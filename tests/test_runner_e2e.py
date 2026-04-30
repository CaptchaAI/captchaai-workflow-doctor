"""End-to-end runner test — boots the mock Flask app + drives a real Chromium.

Marked ``e2e`` and ``slow`` because it spawns a child server and a real
browser. Skipped if Playwright/chromium are not installed.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.slow]

# Skip the whole module if Playwright isn't available (e.g. lint-only jobs).
pytest.importorskip("playwright.sync_api")

from captchaai_doctor.config import load_profile  # noqa: E402
from captchaai_doctor.fake_captchaai import FakeCaptchaAIClient  # noqa: E402
from captchaai_doctor.report import write_json_report  # noqa: E402
from captchaai_doctor.runner import run_workflow  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
PROFILE_PATH = REPO_ROOT / "profiles" / "local-demo-login-turnstile.yaml"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _wait_for(host: str, port: int, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


@pytest.fixture
def mock_app(tmp_path: Path) -> Iterator[tuple[str, int]]:
    """Spawn the mock Flask app on a random free port for the test."""
    port = _free_port()
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "flask",
            "--app",
            "demos.mock_login_turnstile.app",
            "run",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env={**os.environ, "FLASK_DEBUG": "0"},
    )
    try:
        assert _wait_for("127.0.0.1", port), "mock app did not start"
        yield "127.0.0.1", port
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def _profile_with_url(url: str):  # type: ignore[no-untyped-def]
    profile = load_profile(str(PROFILE_PATH))
    return profile.model_copy(update={"target": profile.target.model_copy(update={"url": url})})


def test_runner_happy_path(mock_app: tuple[str, int], tmp_path: Path) -> None:
    host, port = mock_app
    os.environ["QA_EMAIL"] = "demo@example.com"
    os.environ["QA_PASSWORD"] = "demo-pass"

    profile = _profile_with_url(f"http://{host}:{port}/login")
    client = FakeCaptchaAIClient()
    result = run_workflow(profile, client=client, artifact_dir=tmp_path)

    assert result.status == "success", f"detail={result.detail!r}"
    assert result.root_cause == "ok"
    assert result.sitekey_found is not None
    # Submitted exactly one challenge with the discovered sitekey.
    assert len(client.submitted) == 1
    assert client.submitted[0]["method"] == "turnstile"
    # Captcha id is redacted in the report.
    assert result.captcha_id_redacted is not None
    assert "****" in result.captcha_id_redacted

    report_path = tmp_path / "report.json"
    write_json_report(result, report_path)
    assert report_path.exists()
    text = report_path.read_text(encoding="utf-8")
    assert '"status": "success"' in text


def test_runner_detects_wrong_token_mode(mock_app: tuple[str, int], tmp_path: Path) -> None:
    """When the page rejects the token, runner should report verification_failed."""
    host, port = mock_app
    os.environ["QA_EMAIL"] = "demo@example.com"
    os.environ["QA_PASSWORD"] = "demo-pass"

    profile = _profile_with_url(f"http://{host}:{port}/login?mode=wrong-token")
    result = run_workflow(profile, client=FakeCaptchaAIClient(), artifact_dir=tmp_path)

    assert result.status == "failure"
    assert result.root_cause == "verification_failed"
    assert result.detail and "captcha verification failed" in result.detail.lower()


def test_runner_detects_missing_callback(mock_app: tuple[str, int], tmp_path: Path) -> None:
    """The no-callback mode omits the window callback, so invoke step fails."""
    host, port = mock_app
    os.environ["QA_EMAIL"] = "demo@example.com"
    os.environ["QA_PASSWORD"] = "demo-pass"

    profile = _profile_with_url(f"http://{host}:{port}/login?mode=no-callback")
    result = run_workflow(profile, client=FakeCaptchaAIClient(), artifact_dir=tmp_path)

    assert result.status == "failure"
    assert result.root_cause == "callback_not_invoked"
