"""End-to-end runner test for the Cloudflare-challenge mock app."""

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
from captchaai_doctor.fake_captchaai import (  # noqa: E402
    FakeCaptchaAIClient,
    fake_cf_clearance_payload,
)
from captchaai_doctor.runner import run_workflow  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
PROFILE_PATH = REPO_ROOT / "profiles" / "local-demo-cloudflare-challenge.yaml"


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
            "demos.mock_cloudflare_challenge.app",
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
        assert _wait_for("127.0.0.1", port), "mock cf-challenge app did not start"
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


def test_cf_challenge_runner_happy_path(mock_app: tuple[str, int], tmp_path: Path) -> None:
    host, port = mock_app
    profile = _profile_with_url(f"http://{host}:{port}/protected")
    client = FakeCaptchaAIClient(token=fake_cf_clearance_payload())
    result = run_workflow(profile, client=client, artifact_dir=tmp_path)

    assert result.status == "success", f"detail={result.detail!r}"
    assert result.root_cause == "ok"
    # Skipped sitekey detection \u2014 this is a clearance-cookie flow.
    assert result.sitekey_found is None
    assert len(client.submitted) == 1
    submitted = client.submitted[0]
    assert submitted["method"] == "cloudflare_challenge"
    assert submitted["pageurl"].endswith("/protected")
    assert submitted["proxytype"] == "HTTP"
    assert "127.0.0.1:18080" in submitted["proxy"]


def test_cf_challenge_runner_rejects_wrong_cookie(
    mock_app: tuple[str, int], tmp_path: Path
) -> None:
    """If the worker's cookie is rejected, the runner reports verification_failed."""
    host, port = mock_app
    profile = _profile_with_url(f"http://{host}:{port}/protected?mode=wrong-cookie")
    client = FakeCaptchaAIClient(token=fake_cf_clearance_payload())
    result = run_workflow(profile, client=client, artifact_dir=tmp_path)

    assert result.status == "failure"
    assert result.root_cause == "verification_failed"


def test_cf_challenge_runner_misconfigured_proxy_credentials(
    mock_app: tuple[str, int], tmp_path: Path
) -> None:
    """Proxy creds that reference an unset env var must surface as misconfig."""
    host, port = mock_app
    profile = _profile_with_url(f"http://{host}:{port}/protected")
    new_proxy = profile.proxy.model_copy(  # type: ignore[union-attr]
        update={
            "username_env": "DOCTOR_TEST_NONEXISTENT_USER_ABCXYZ",
            "password_env": "DOCTOR_TEST_NONEXISTENT_PASS_ABCXYZ",
        }
    )
    profile = profile.model_copy(update={"proxy": new_proxy})
    # Make sure those env vars are absent so the test is hermetic.
    for var in ("DOCTOR_TEST_NONEXISTENT_USER_ABCXYZ", "DOCTOR_TEST_NONEXISTENT_PASS_ABCXYZ"):
        os.environ.pop(var, None)

    client = FakeCaptchaAIClient(token=fake_cf_clearance_payload())
    result = run_workflow(profile, client=client, artifact_dir=tmp_path)

    assert result.status == "failure"
    assert result.root_cause == "cloudflare_proxy_misconfigured"


def test_cf_challenge_runner_rejects_bad_token_payload(
    mock_app: tuple[str, int], tmp_path: Path
) -> None:
    """A non-JSON 'token' from the solver must surface as a browser action failure."""
    host, port = mock_app
    profile = _profile_with_url(f"http://{host}:{port}/protected")
    client = FakeCaptchaAIClient(token="this is not json")
    result = run_workflow(profile, client=client, artifact_dir=tmp_path)

    assert result.status == "failure"
    assert result.root_cause == "browser_action_failed"
    assert result.detail is not None
    assert "JSON" in result.detail or "json" in result.detail
