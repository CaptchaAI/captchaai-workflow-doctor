"""Flask test_client tests for the mock reCAPTCHA-v3 contact app."""

from __future__ import annotations

import pytest

from demos.mock_form_recaptcha_v3.app import (
    DEMO_ACTION,
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


def test_index_redirects_to_contact(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (301, 302)
    assert "/contact" in resp.headers["Location"]


def test_contact_page_renders_v3_script(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/contact")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert f"render={DEMO_SITEKEY}" in body
    assert 'name="g-recaptcha-response"' in body
    assert DEMO_ACTION in body


def test_contact_post_happy_path(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/contact?mode=ok",
        data={
            "name": "Alice",
            "message": "hi",
            "g-recaptcha-response": FAKE_OK_TOKEN,
            "action": DEMO_ACTION,
        },
    )
    assert resp.status_code == 200
    assert b'data-testid="thanks"' in resp.data


def test_contact_post_wrong_token_rejected(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/contact?mode=ok",
        data={
            "name": "Alice",
            "message": "hi",
            "g-recaptcha-response": "BOGUS",
            "action": DEMO_ACTION,
        },
    )
    assert resp.status_code == 200
    assert b"captcha verification failed" in resp.data
