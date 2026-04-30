"""End-to-end runner test for the reCAPTCHA-v2 mock app.

Mirrors :mod:`tests.test_runner_e2e` but against the reCAPTCHA flow, so
both code paths in the runner / detector / injector are exercised by CI.
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

pytest.importorskip("playwright.sync_api")

from captchaai_doctor.config import load_profile  # noqa: E402
from captchaai_doctor.fake_captchaai import FakeCaptchaAIClient  # noqa: E402
from captchaai_doctor.runner import run_workflow  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
PROFILE_PATH = REPO_ROOT / "profiles" / "local-demo-login-recaptcha.yaml"


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
    port = _free_port()
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "flask",
            "--app",
            "demos.mock_login_recaptcha.app",
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
        assert _wait_for("127.0.0.1", port), "mock recaptcha app did not start"
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


def test_recaptcha_runner_happy_path(mock_app: tuple[str, int], tmp_path: Path) -> None:
    host, port = mock_app
    os.environ["QA_EMAIL"] = "demo@example.com"
    os.environ["QA_PASSWORD"] = "demo-pass"

    profile = _profile_with_url(f"http://{host}:{port}/login")
    client = FakeCaptchaAIClient()
    result = run_workflow(profile, client=client, artifact_dir=tmp_path)

    assert result.status == "success", f"detail={result.detail!r}"
    assert result.root_cause == "ok"
    assert result.sitekey_found is not None
    assert len(client.submitted) == 1
    assert client.submitted[0]["method"] == "userrecaptcha"


def test_recaptcha_runner_detects_wrong_token(mock_app: tuple[str, int], tmp_path: Path) -> None:
    host, port = mock_app
    os.environ["QA_EMAIL"] = "demo@example.com"
    os.environ["QA_PASSWORD"] = "demo-pass"

    profile = _profile_with_url(f"http://{host}:{port}/login?mode=wrong-token")
    result = run_workflow(profile, client=FakeCaptchaAIClient(), artifact_dir=tmp_path)

    assert result.status == "failure"
    assert result.root_cause == "verification_failed"


def test_recaptcha_runner_detects_missing_callback(
    mock_app: tuple[str, int], tmp_path: Path
) -> None:
    host, port = mock_app
    os.environ["QA_EMAIL"] = "demo@example.com"
    os.environ["QA_PASSWORD"] = "demo-pass"

    profile = _profile_with_url(f"http://{host}:{port}/login?mode=no-callback")
    result = run_workflow(profile, client=FakeCaptchaAIClient(), artifact_dir=tmp_path)

    assert result.status == "failure"
    assert result.root_cause == "callback_not_invoked"
