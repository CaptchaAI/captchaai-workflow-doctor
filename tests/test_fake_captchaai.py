"""Tests for the FakeCaptchaAIClient."""

from __future__ import annotations

import pytest

from captchaai_doctor.captchaai_client import CaptchaAINotReadyError
from captchaai_doctor.fake_captchaai import FAKE_OK_TOKEN, FakeCaptchaAIClient


def test_submit_assigns_increasing_ids() -> None:
    c = FakeCaptchaAIClient()
    a = c.submit_turnstile(sitekey="x", page_url="https://e.test")
    b = c.submit_turnstile(sitekey="x", page_url="https://e.test")
    assert a.captcha_id != b.captcha_id
    assert len(a.captcha_id) >= 7  # so log redaction kicks in


def test_get_result_returns_token_immediately() -> None:
    c = FakeCaptchaAIClient()
    sub = c.submit_recaptcha_v2(sitekey="x", page_url="https://e.test")
    poll = c.get_result(sub.captcha_id)
    assert poll.token == FAKE_OK_TOKEN
    assert sub.captcha_id in c.polled


def test_not_ready_count_is_consumed() -> None:
    c = FakeCaptchaAIClient(not_ready_count=2)
    sub = c.submit_turnstile(sitekey="x", page_url="https://e.test")
    with pytest.raises(CaptchaAINotReadyError):
        c.get_result(sub.captcha_id)
    with pytest.raises(CaptchaAINotReadyError):
        c.get_result(sub.captcha_id)
    poll = c.get_result(sub.captcha_id)
    assert poll.token == FAKE_OK_TOKEN


def test_get_balance_default() -> None:
    assert FakeCaptchaAIClient().get_balance() == pytest.approx(100.0)


def test_report_bad_records() -> None:
    c = FakeCaptchaAIClient()
    c.report_bad("0001234")
    assert c.reported_bad == ["0001234"]


def test_context_manager_works() -> None:
    with FakeCaptchaAIClient() as c:
        assert c.get_balance() > 0
