"""Tests for the mock Turnstile login Flask app (no browser involved)."""

from __future__ import annotations

import pytest

from demos.mock_login_turnstile.app import (
    DEMO_EMAIL,
    DEMO_PASSWORD,
    DEMO_SITEKEY,
    FAKE_OK_TOKEN,
    create_app,
)


@pytest.fixture
def client():  # type: ignore[no-untyped-def]
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_login_page_renders_form_and_sitekey(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/login")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert DEMO_SITEKEY in body
    assert "cf-turnstile-response" in body
    assert 'name="email"' in body


def test_login_succeeds_with_correct_token_and_creds(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/login",
        data={
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD,
            "cf-turnstile-response": FAKE_OK_TOKEN,
        },
    )
    assert resp.status_code == 200
    assert b'data-testid="dashboard"' in resp.data


def test_login_rejects_wrong_token(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/login",
        data={
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD,
            "cf-turnstile-response": "BAD",
        },
    )
    assert resp.status_code == 200
    assert b"captcha verification failed" in resp.data


def test_wrong_token_mode_rejects_even_correct_token(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/login?mode=wrong-token",
        data={
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD,
            "cf-turnstile-response": FAKE_OK_TOKEN,
        },
    )
    assert b"captcha verification failed" in resp.data


def test_no_callback_mode_omits_window_callback(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/login?mode=no-callback")
    body = resp.data.decode()
    assert "window.onTurnstileSuccess" not in body


def test_healthz(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.data == b"ok"


def test_invisible_widget_renders_data_size_and_execute_shim(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/login?widget=invisible")
    body = resp.data.decode()
    assert 'data-size="invisible"' in body
    assert "window.turnstile = {" in body
    assert "execute" in body


def test_managed_widget_omits_invisible_attrs(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/login")
    body = resp.data.decode()
    assert 'data-size="invisible"' not in body
    assert "window.turnstile = {" not in body


def test_invisible_widget_full_login_succeeds(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/login?widget=invisible",
        data={
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD,
            "cf-turnstile-response": FAKE_OK_TOKEN,
        },
    )
    assert resp.status_code == 200
    assert b'data-testid="dashboard"' in resp.data
