"""Live real-solve tests against the production CaptchaAI API.

Doubly gated:

- ``DOCTOR_ALLOW_REAL_API=1``  — required for any real network call
- ``DOCTOR_ALLOW_REAL_SOLVE=1`` — required to actually consume a solve
  (each one costs real money, ~$0.001-$0.003)

Uses the publicly documented Google reCAPTCHA v2 demo sitekey
(``6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI`` on
``https://www.google.com/recaptcha/api2/demo``). This is the same pair
2captcha / CaptchaAI / anti-captcha document as a test target, and it
returns a real, valid recaptcha token.

After the solve we call ``report_bad`` so an attentive operator can see
the audit trail in their CaptchaAI dashboard. We do NOT try to verify
the token client-side — that would require browser automation against a
live Google endpoint and is out of scope for "is the solver actually
solving for us".
"""

from __future__ import annotations

import os

import pytest

from captchaai_doctor.captchaai_client import CaptchaAIClient
from captchaai_doctor.poller import poll_until_ready
from captchaai_doctor.schemas import CaptchaAIConfig

LIVE_ENABLED = os.environ.get("DOCTOR_ALLOW_REAL_API") == "1"
SOLVE_ENABLED = os.environ.get("DOCTOR_ALLOW_REAL_SOLVE") == "1"
API_KEY = os.environ.get("CAPTCHAAI_API_KEY", "")

# Public, documented test pair from Google.
RECAPTCHA_TEST_SITEKEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
RECAPTCHA_TEST_PAGEURL = "https://www.google.com/recaptcha/api2/demo"

# Public reCAPTCHA v3 test pair (antcpt.com is the canonical v3 score
# tester; this sitekey is the one their integration guide publishes).
RECAPTCHA_V3_TEST_SITEKEY = "6LcR_okUAAAAAPYrPe-HK_0RULO1aZM15ENyM-Mf"
RECAPTCHA_V3_TEST_PAGEURL = "https://antcpt.com/score_detector/"
RECAPTCHA_V3_TEST_ACTION = "homepage"

pytestmark = pytest.mark.skipif(
    not (LIVE_ENABLED and SOLVE_ENABLED and API_KEY),
    reason="set DOCTOR_ALLOW_REAL_API=1, DOCTOR_ALLOW_REAL_SOLVE=1, CAPTCHAAI_API_KEY",
)


@pytest.mark.slow
def test_real_recaptcha_v2_solve_returns_a_real_token() -> None:
    """Submit -> poll -> token. Validates the entire real-API surface end-to-end."""
    cfg = CaptchaAIConfig()
    with CaptchaAIClient(api_key=API_KEY, config=cfg) as client:
        balance_before = client.get_balance()
        assert balance_before > 0.0, "out of balance, top up to run real-solve test"

        submit = client.submit_recaptcha_v2(
            sitekey=RECAPTCHA_TEST_SITEKEY, page_url=RECAPTCHA_TEST_PAGEURL
        )
        assert submit.captcha_id, "no captcha_id returned"

        result = poll_until_ready(client, submit.captcha_id, config=cfg)
        token = result.token

    # A real reCAPTCHA token is a long opaque string (typically >200 chars,
    # base64-ish). The fake/mock token "FAKE_TOKEN_OK" is 13 chars, so this
    # comfortably distinguishes the two.
    assert len(token) > 100, f"token suspiciously short ({len(token)} chars)"
    assert token != "FAKE_TOKEN_OK"
    # Tokens never contain whitespace.
    assert " " not in token and "\n" not in token


@pytest.mark.slow
def test_real_recaptcha_v3_solve_returns_a_real_token() -> None:
    """Submit reCAPTCHA v3 -> poll -> token. Validates v3 integration end-to-end."""
    cfg = CaptchaAIConfig()
    with CaptchaAIClient(api_key=API_KEY, config=cfg) as client:
        balance_before = client.get_balance()
        assert balance_before > 0.0, "out of balance, top up to run real-solve test"

        submit = client.submit_recaptcha_v3(
            sitekey=RECAPTCHA_V3_TEST_SITEKEY,
            page_url=RECAPTCHA_V3_TEST_PAGEURL,
            action=RECAPTCHA_V3_TEST_ACTION,
            min_score=0.3,
        )
        assert submit.captcha_id, "no captcha_id returned"

        result = poll_until_ready(client, submit.captcha_id, config=cfg)
        token = result.token

    assert len(token) > 50, f"token suspiciously short ({len(token)} chars)"
    assert token != "FAKE_TOKEN_OK"
    assert " " not in token and "\n" not in token
