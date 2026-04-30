"""Flask test_client tests for the mock reCAPTCHA login app."""

from __future__ import annotations

import pytest

from demos.mock_login_recaptcha.app import (
    DEMO_EMAIL,
    DEMO_PASSWORD,
    DEMO_SITEKEY,
    FAKE_OK_TOKEN,
    create_app,
)


@pytest.fixture
def client():  # type: ignore[no-untyped-def]
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_healthz(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.data == b"ok"


def test_index_redirects_to_login(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (301, 302)
    assert "/login" in resp.headers["Location"]


def test_login_page_renders_g_recaptcha_div(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/login")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'class="g-recaptcha"' in body
    assert DEMO_SITEKEY in body
    assert 'name="g-recaptcha-response"' in body


def test_login_no_callback_mode_omits_callback(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/login?mode=no-callback")
    body = resp.get_data(as_text=True)
    assert "onRecaptchaSuccess" not in body


def test_login_ok_mode_includes_callback(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/login?mode=ok")
    body = resp.get_data(as_text=True)
    assert "onRecaptchaSuccess" in body


def test_login_post_happy_path(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/login?mode=ok",
        data={
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD,
            "g-recaptcha-response": FAKE_OK_TOKEN,
        },
    )
    assert resp.status_code == 200
    assert b'data-testid="dashboard"' in resp.data


def test_login_post_wrong_token_rejected(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/login?mode=ok",
        data={
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD,
            "g-recaptcha-response": "BOGUS",
        },
    )
    assert resp.status_code == 200
    assert b"captcha verification failed" in resp.data
