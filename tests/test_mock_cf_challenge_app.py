"""Unit tests for the mock Cloudflare-challenge demo app."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from demos.mock_cloudflare_challenge.app import (
    EXPECTED_USER_AGENT_FRAGMENT,
    FAKE_OK_CLEARANCE,
    create_app,
)


@pytest.fixture
def client() -> Iterator[object]:  # type: ignore[misc]
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as c:
        yield c


def test_protected_without_cookie_serves_interstitial(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/protected", headers={"User-Agent": "anything"})
    assert resp.status_code == 403
    assert b"Just a moment" in resp.data
    assert b'data-testid="cf-interstitial"' in resp.data
    assert resp.headers["X-Mock-Cf-Cookie-Match"] == "0"


def test_protected_with_cookie_but_wrong_ua_serves_interstitial(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get(
        "/protected",
        headers={"User-Agent": "curl/8.0"},
        # Flask test client cookie set
    )
    client.set_cookie("cf_clearance", FAKE_OK_CLEARANCE, domain="localhost")
    resp = client.get("/protected", headers={"User-Agent": "curl/8.0"})
    assert resp.status_code == 403
    assert resp.headers["X-Mock-Cf-Cookie-Match"] == "1"
    assert resp.headers["X-Mock-Cf-Ua-Match"] == "0"


def test_protected_with_cookie_and_ua_passes(client) -> None:  # type: ignore[no-untyped-def]
    client.set_cookie("cf_clearance", FAKE_OK_CLEARANCE, domain="localhost")
    ua = f"Mozilla/5.0 ... {EXPECTED_USER_AGENT_FRAGMENT}.0.0.0 Safari/537.36"
    resp = client.get("/protected", headers={"User-Agent": ua})
    assert resp.status_code == 200
    assert b'data-testid="protected"' in resp.data


def test_wrong_cookie_mode_always_rejects(client) -> None:  # type: ignore[no-untyped-def]
    client.set_cookie("cf_clearance", FAKE_OK_CLEARANCE, domain="localhost")
    ua = f"Mozilla/5.0 ... {EXPECTED_USER_AGENT_FRAGMENT}.0.0.0 Safari/537.36"
    resp = client.get("/protected?mode=wrong-cookie", headers={"User-Agent": ua})
    assert resp.status_code == 403


def test_healthz(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.data == b"ok"
