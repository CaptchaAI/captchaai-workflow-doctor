"""Mocked HTTP tests for the CaptchaAI client (no real network)."""

from __future__ import annotations

import logging

import httpx
import pytest
import respx

from captchaai_doctor.captchaai_client import (
    CaptchaAIAuthError,
    CaptchaAIBalanceError,
    CaptchaAIClient,
    CaptchaAINotReadyError,
    CaptchaAIPageError,
    CaptchaAIServerError,
    CaptchaAITransportError,
    CaptchaAIUnsolvableError,
)
from captchaai_doctor.redaction import install_global_redaction
from captchaai_doctor.schemas import CaptchaAIConfig

API_KEY = "deadbeefcafebabe1234567890abcdef"  # synthetic 32-char hex
SUBMIT_URL = "https://ocr.captchaai.com/in.php"
RESULT_URL = "https://ocr.captchaai.com/res.php"


@pytest.fixture
def client() -> CaptchaAIClient:
    return CaptchaAIClient(api_key=API_KEY, config=CaptchaAIConfig())


def test_api_key_required() -> None:
    with pytest.raises(ValueError, match="api_key"):
        CaptchaAIClient(api_key="")


@respx.mock
def test_get_balance_ok(client: CaptchaAIClient) -> None:
    respx.get(RESULT_URL).respond(json={"status": 1, "request": "12.345"})
    assert client.get_balance() == pytest.approx(12.345)


@respx.mock
def test_get_balance_bad_payload(client: CaptchaAIClient) -> None:
    respx.get(RESULT_URL).respond(json={"status": 1, "request": "not a number"})
    with pytest.raises(CaptchaAIServerError, match="BAD_BALANCE_RESPONSE"):
        client.get_balance()


@respx.mock
def test_submit_turnstile_ok(client: CaptchaAIClient) -> None:
    respx.post(SUBMIT_URL).respond(json={"status": 1, "request": "1234567890"})
    result = client.submit_turnstile(sitekey="0x4AAAA", page_url="https://x.test/login")
    assert result.captcha_id == "1234567890"


@respx.mock
def test_submit_recaptcha_v2_ok(client: CaptchaAIClient) -> None:
    respx.post(SUBMIT_URL).respond(json={"status": 1, "request": "9999"})
    assert (
        client.submit_recaptcha_v2(sitekey="6Lc...", page_url="https://x.test").captcha_id == "9999"
    )


@respx.mock
def test_submit_recaptcha_v3_sends_version_and_action(client: CaptchaAIClient) -> None:
    route = respx.post(SUBMIT_URL).respond(json={"status": 1, "request": "5550000"})
    result = client.submit_recaptcha_v3(
        sitekey="6Lc-V3", page_url="https://x.test/page", action="login", min_score=0.5
    )
    assert result.captcha_id == "5550000"
    body = route.calls.last.request.content.decode()
    assert "method=userrecaptcha" in body
    assert "version=v3" in body
    assert "action=login" in body
    assert "min_score=0.5" in body


def test_submit_recaptcha_v3_requires_action(client: CaptchaAIClient) -> None:
    with pytest.raises(ValueError, match="action"):
        client.submit_recaptcha_v3(sitekey="6Lc-V3", page_url="https://x.test", action="")


def test_submit_recaptcha_v3_validates_min_score(client: CaptchaAIClient) -> None:
    with pytest.raises(ValueError, match="min_score"):
        client.submit_recaptcha_v3(
            sitekey="6Lc-V3", page_url="https://x.test", action="login", min_score=1.5
        )


@respx.mock
def test_submit_accepts_integer_captcha_id(client: CaptchaAIClient) -> None:
    """Production CaptchaAI returns captcha_id as an int for userrecaptcha."""
    respx.post(SUBMIT_URL).respond(json={"status": 1, "request": 3397637370})
    result = client.submit_recaptcha_v2(sitekey="6Lc...", page_url="https://x.test")
    assert result.captcha_id == "3397637370"


@respx.mock
def test_get_result_ok(client: CaptchaAIClient) -> None:
    respx.get(RESULT_URL).respond(json={"status": 1, "request": "TOKEN_TOKEN_TOKEN_xyz"})
    result = client.get_result("1234567890")
    assert result.token == "TOKEN_TOKEN_TOKEN_xyz"


@respx.mock
def test_get_result_not_ready_raises(client: CaptchaAIClient) -> None:
    respx.get(RESULT_URL).respond(json={"status": 0, "request": "CAPCHA_NOT_READY"})
    with pytest.raises(CaptchaAINotReadyError):
        client.get_result("1234567890")


@pytest.mark.parametrize(
    "code,expected",
    [
        ("ERROR_WRONG_USER_KEY", CaptchaAIAuthError),
        ("ERROR_KEY_DOES_NOT_EXIST", CaptchaAIAuthError),
        ("ERROR_ZERO_BALANCE", CaptchaAIBalanceError),
        ("ERROR_PAGEURL", CaptchaAIPageError),
        ("ERROR_GOOGLEKEY", CaptchaAIPageError),
        ("ERROR_BAD_TOKEN_OR_PAGEURL", CaptchaAIPageError),
        ("ERROR_DOMAIN_NOT_ALLOWED", CaptchaAIPageError),
        ("ERROR_CAPTCHA_UNSOLVABLE", CaptchaAIUnsolvableError),
        ("ERROR_SOMETHING_NEW", CaptchaAIServerError),
    ],
)
@respx.mock
def test_error_codes_map_to_typed_exceptions(
    client: CaptchaAIClient, code: str, expected: type[Exception]
) -> None:
    respx.get(RESULT_URL).respond(json={"status": 0, "request": code})
    with pytest.raises(expected) as exc_info:
        client.get_result("1234567890")
    if isinstance(exc_info.value, CaptchaAIServerError):
        assert exc_info.value.code == code


@respx.mock
def test_submit_propagates_auth_error(client: CaptchaAIClient) -> None:
    respx.post(SUBMIT_URL).respond(json={"status": 0, "request": "ERROR_WRONG_USER_KEY"})
    with pytest.raises(CaptchaAIAuthError):
        client.submit_turnstile(sitekey="x", page_url="https://x.test")


@respx.mock
def test_transport_5xx_raises_transport_error(client: CaptchaAIClient) -> None:
    respx.get(RESULT_URL).respond(status_code=503, text="upstream down")
    with pytest.raises(CaptchaAITransportError):
        client.get_balance()


@respx.mock
def test_transport_connect_failure_raises_transport_error(client: CaptchaAIClient) -> None:
    respx.get(RESULT_URL).mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(CaptchaAITransportError):
        client.get_balance()


@respx.mock
def test_non_json_response_classified(client: CaptchaAIClient) -> None:
    respx.get(RESULT_URL).respond(text="OK|tokenstring")
    with pytest.raises(CaptchaAIServerError, match="BAD_JSON"):
        client.get_balance()


@respx.mock
def test_logs_redact_api_key(client: CaptchaAIClient, caplog) -> None:
    flt = install_global_redaction()
    caplog.handler.addFilter(flt)
    respx.get(RESULT_URL).respond(json={"status": 1, "request": "10.0"})
    with caplog.at_level(logging.DEBUG, logger="captchaai_doctor.captchaai_client"):
        client.get_balance()
    combined = " ".join(rec.getMessage() for rec in caplog.records)
    assert API_KEY not in combined, f"API key leaked into logs: {combined!r}"


@respx.mock
def test_context_manager_closes(client: CaptchaAIClient) -> None:
    # Just exercise __enter__/__exit__ — no assertion beyond not-raising.
    respx.get(RESULT_URL).respond(json={"status": 1, "request": "1"})
    with CaptchaAIClient(api_key=API_KEY) as c:
        c.get_balance()


@respx.mock
def test_submit_cloudflare_challenge_sends_proxy_params(client: CaptchaAIClient) -> None:
    route = respx.post(SUBMIT_URL).respond(json={"status": 1, "request": "7777"})
    result = client.submit_cloudflare_challenge(
        page_url="https://x.test/p",
        user_agent="Mozilla/5.0 ... Chrome/124.0.0.0",
        proxy_host="10.0.0.1",
        proxy_port=8080,
        proxy_type="HTTP",
        proxy_username="u",
        proxy_password="p",
    )
    assert result.captcha_id == "7777"
    body = route.calls.last.request.content.decode()
    assert "method=cloudflare_challenge" in body
    assert "proxytype=HTTP" in body
    assert "u%3Ap%4010.0.0.1%3A8080" in body  # urlencoded user:pass@host:port


def test_submit_cloudflare_challenge_validates_args(client: CaptchaAIClient) -> None:
    with pytest.raises(ValueError, match="user_agent"):
        client.submit_cloudflare_challenge(
            page_url="https://x.test",
            user_agent="  ",
            proxy_host="h",
            proxy_port=8080,
            proxy_type="HTTP",
        )
    with pytest.raises(ValueError, match="proxy_port"):
        client.submit_cloudflare_challenge(
            page_url="https://x.test",
            user_agent="ua",
            proxy_host="h",
            proxy_port=99999,
            proxy_type="HTTP",
        )
    with pytest.raises(ValueError, match="proxy_type"):
        client.submit_cloudflare_challenge(
            page_url="https://x.test",
            user_agent="ua",
            proxy_host="h",
            proxy_port=8080,
            proxy_type="FTP",
        )
    with pytest.raises(ValueError, match="both"):
        client.submit_cloudflare_challenge(
            page_url="https://x.test",
            user_agent="ua",
            proxy_host="h",
            proxy_port=8080,
            proxy_type="HTTP",
            proxy_username="u",
        )
