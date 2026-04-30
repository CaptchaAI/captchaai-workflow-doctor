"""Tests for the detector module against a real (Playwright) DOM.

We use ``data:`` URLs so no Flask server is needed. Marked ``e2e`` only
because Chromium has to be installed; runtime is well under a second
per test.
"""

from __future__ import annotations

import base64
from collections.abc import Iterator

import pytest

pytestmark = [pytest.mark.e2e]

pw_sync = pytest.importorskip("playwright.sync_api")

from captchaai_doctor.detector import (  # noqa: E402
    detect_callback,
    detect_widget,
    read_sitekey,
)
from captchaai_doctor.schemas import Detection  # noqa: E402


def _data_url(html: str) -> str:
    encoded = base64.b64encode(html.encode("utf-8")).decode("ascii")
    return f"data:text/html;base64,{encoded}"


@pytest.fixture(scope="module")
def page() -> Iterator[object]:
    with pw_sync.sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        try:
            yield page
        finally:
            context.close()
            browser.close()


def test_read_sitekey_finds_data_sitekey(page: object) -> None:
    page.goto(_data_url('<div data-sitekey="ABC123"></div>'))  # type: ignore[attr-defined]
    detection = Detection(
        sitekey_selector="[data-sitekey]",
        response_field_selector="textarea",
        callback_candidates=[],
    )
    assert read_sitekey(page, detection) == "ABC123"  # type: ignore[arg-type]


def test_read_sitekey_returns_none_when_missing(page: object) -> None:
    page.goto(_data_url("<p>nothing</p>"))  # type: ignore[attr-defined]
    detection = Detection(
        sitekey_selector="[data-sitekey]",
        response_field_selector="textarea",
        callback_candidates=[],
    )
    assert read_sitekey(page, detection) is None  # type: ignore[arg-type]


def test_detect_widget_classifies_turnstile(page: object) -> None:
    html = '<div class="cf-turnstile" data-sitekey="0xABC"></div>'
    page.goto(_data_url(html))  # type: ignore[attr-defined]
    widget = detect_widget(page)  # type: ignore[arg-type]
    assert widget is not None
    assert widget.kind == "turnstile"
    assert widget.sitekey == "0xABC"
    assert widget.turnstile_mode is None


def test_detect_widget_classifies_turnstile_invisible(page: object) -> None:
    html = '<div class="cf-turnstile" data-sitekey="0xINV" data-size="invisible"></div>'
    page.goto(_data_url(html))  # type: ignore[attr-defined]
    widget = detect_widget(page)  # type: ignore[arg-type]
    assert widget is not None
    assert widget.kind == "turnstile"
    assert widget.sitekey == "0xINV"
    assert widget.turnstile_mode == "invisible"


def test_detect_widget_classifies_turnstile_managed(page: object) -> None:
    html = '<div class="cf-turnstile" data-sitekey="0xMNG" data-size="normal"></div>'
    page.goto(_data_url(html))  # type: ignore[attr-defined]
    widget = detect_widget(page)  # type: ignore[arg-type]
    assert widget is not None
    assert widget.turnstile_mode == "managed"


def test_detect_widget_classifies_recaptcha(page: object) -> None:
    html = '<div class="g-recaptcha" data-sitekey="6Lc-XYZ"></div>'
    page.goto(_data_url(html))  # type: ignore[attr-defined]
    widget = detect_widget(page)  # type: ignore[arg-type]
    assert widget is not None
    assert widget.kind == "recaptcha_v2"
    assert widget.sitekey == "6Lc-XYZ"


def test_detect_widget_classifies_recaptcha_v3(page: object) -> None:
    html = (
        "<html><body>"
        '<script src="https://www.google.com/recaptcha/api.js?render=6LcV3KEY"></script>'
        "</body></html>"
    )
    page.goto(_data_url(html))  # type: ignore[attr-defined]
    widget = detect_widget(page)  # type: ignore[arg-type]
    assert widget is not None
    assert widget.kind == "recaptcha_v3"
    assert widget.sitekey == "6LcV3KEY"


def test_read_sitekey_extracts_v3_render_query(page: object) -> None:
    html = (
        "<html><body>"
        '<script src="https://www.google.com/recaptcha/api.js?render=6LcRENDERED"></script>'
        "</body></html>"
    )
    page.goto(_data_url(html))  # type: ignore[attr-defined]
    detection = Detection(
        sitekey_selector="script[src*='recaptcha'][src*='render=']",
        response_field_selector="input[name='g-recaptcha-response']",
        callback_candidates=[],
    )
    assert read_sitekey(page, detection) == "6LcRENDERED"  # type: ignore[arg-type]


def test_detect_widget_unknown_for_generic(page: object) -> None:
    html = '<div data-sitekey="generic"></div>'
    page.goto(_data_url(html))  # type: ignore[attr-defined]
    widget = detect_widget(page)  # type: ignore[arg-type]
    assert widget is not None
    assert widget.kind == "unknown"


def test_detect_widget_returns_none_when_no_widget(page: object) -> None:
    page.goto(_data_url("<p>hello</p>"))  # type: ignore[attr-defined]
    assert detect_widget(page) is None  # type: ignore[arg-type]


def test_detect_callback_finds_first_present(page: object) -> None:
    html = """
        <html><body>
        <script>window.onTurnstileSuccess = function() {};</script>
        </body></html>
    """
    page.goto(_data_url(html))  # type: ignore[attr-defined]
    name = detect_callback(page, ["onRecaptchaSuccess", "onTurnstileSuccess"])  # type: ignore[arg-type]
    assert name == "onTurnstileSuccess"


def test_detect_callback_none_when_missing(page: object) -> None:
    page.goto(_data_url("<p></p>"))  # type: ignore[attr-defined]
    assert detect_callback(page, ["onTurnstileSuccess"]) is None  # type: ignore[arg-type]


def test_detect_callback_empty_candidates(page: object) -> None:
    page.goto(_data_url("<p></p>"))  # type: ignore[attr-defined]
    assert detect_callback(page, []) is None  # type: ignore[arg-type]
