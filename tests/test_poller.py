"""Tests for `captchaai_doctor.poller.poll_until_ready` (deterministic, no real time)."""

from __future__ import annotations

import httpx
import pytest
import respx

from captchaai_doctor.captchaai_client import (
    CaptchaAIAuthError,
    CaptchaAIClient,
)
from captchaai_doctor.poller import PollTimeout, poll_until_ready
from captchaai_doctor.schemas import CaptchaAIConfig

RESULT_URL = "https://ocr.captchaai.com/res.php"


class FakeClock:
    """Monotonic clock that only advances when the fake `sleep` is called."""

    def __init__(self) -> None:
        self.t = 0.0

    def now(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.t += seconds


@pytest.fixture
def cfg() -> CaptchaAIConfig:
    # Tight bounds so tests are obvious.
    return CaptchaAIConfig(polling_interval_seconds=2.0, max_wait_seconds=20)


@pytest.fixture
def client() -> CaptchaAIClient:
    return CaptchaAIClient(api_key="x" * 32, config=CaptchaAIConfig())


@respx.mock
def test_poll_returns_on_first_ready(cfg: CaptchaAIConfig, client: CaptchaAIClient) -> None:
    respx.get(RESULT_URL).respond(json={"status": 1, "request": "TOKEN_OK"})
    clock = FakeClock()
    out = poll_until_ready(client, "1234", config=cfg, sleep=clock.sleep, clock=clock.now)
    assert out.token == "TOKEN_OK"
    assert out.attempts == 1
    assert out.elapsed_seconds == pytest.approx(2.0)


@respx.mock
def test_poll_waits_through_not_ready(cfg: CaptchaAIConfig, client: CaptchaAIClient) -> None:
    responses = [
        httpx.Response(200, json={"status": 0, "request": "CAPCHA_NOT_READY"}),
        httpx.Response(200, json={"status": 0, "request": "CAPCHA_NOT_READY"}),
        httpx.Response(200, json={"status": 1, "request": "TOKEN_FINAL"}),
    ]
    respx.get(RESULT_URL).mock(side_effect=responses)
    clock = FakeClock()
    out = poll_until_ready(client, "1234", config=cfg, sleep=clock.sleep, clock=clock.now)
    assert out.token == "TOKEN_FINAL"
    assert out.attempts == 3
    assert out.elapsed_seconds == pytest.approx(6.0)


@respx.mock
def test_poll_timeout_raises(cfg: CaptchaAIConfig, client: CaptchaAIClient) -> None:
    respx.get(RESULT_URL).respond(json={"status": 0, "request": "CAPCHA_NOT_READY"})
    clock = FakeClock()
    with pytest.raises(PollTimeout) as exc:
        poll_until_ready(client, "1234567890", config=cfg, sleep=clock.sleep, clock=clock.now)
    assert exc.value.captcha_id == "1234567890"
    # Captcha id should be redacted in the message itself.
    assert "1234567890" not in str(exc.value)
    assert exc.value.attempts >= cfg.max_wait_seconds // int(cfg.polling_interval_seconds) - 1


@respx.mock
def test_poll_no_slot_available_backs_off_and_retries(
    cfg: CaptchaAIConfig, client: CaptchaAIClient
) -> None:
    responses = [
        httpx.Response(200, json={"status": 0, "request": "ERROR_NO_SLOT_AVAILABLE"}),
        httpx.Response(200, json={"status": 1, "request": "TOKEN_OK"}),
    ]
    respx.get(RESULT_URL).mock(side_effect=responses)
    clock = FakeClock()
    out = poll_until_ready(client, "1234", config=cfg, sleep=clock.sleep, clock=clock.now)
    assert out.token == "TOKEN_OK"
    # 1 normal sleep + 1 backoff + 1 normal sleep == 3 * 2.0
    assert out.elapsed_seconds == pytest.approx(6.0)


@respx.mock
def test_poll_propagates_auth_error_immediately(
    cfg: CaptchaAIConfig, client: CaptchaAIClient
) -> None:
    respx.get(RESULT_URL).respond(json={"status": 0, "request": "ERROR_WRONG_USER_KEY"})
    clock = FakeClock()
    with pytest.raises(CaptchaAIAuthError):
        poll_until_ready(client, "1234", config=cfg, sleep=clock.sleep, clock=clock.now)


@respx.mock
def test_poll_attempts_capped_by_max_wait(cfg: CaptchaAIConfig, client: CaptchaAIClient) -> None:
    respx.get(RESULT_URL).respond(json={"status": 0, "request": "CAPCHA_NOT_READY"})
    clock = FakeClock()
    with pytest.raises(PollTimeout) as exc:
        poll_until_ready(client, "1234", config=cfg, sleep=clock.sleep, clock=clock.now)
    # Sleeps of 2s up to 20s deadline -> 10 attempts max.
    assert exc.value.attempts <= 10
    assert exc.value.waited_seconds == pytest.approx(20.0)
