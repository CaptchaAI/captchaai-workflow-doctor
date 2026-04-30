"""Tests for the injector module against a real (Playwright) DOM."""

from __future__ import annotations

import base64
from collections.abc import Iterator

import pytest

pytestmark = [pytest.mark.e2e]

pw_sync = pytest.importorskip("playwright.sync_api")

from captchaai_doctor.injector import (  # noqa: E402
    InjectionError,
    inject_token,
    invoke_callback,
)
from captchaai_doctor.verifier import callback_marker_present, field_has_value  # noqa: E402


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


def test_inject_token_writes_value_to_hidden_field(page: object) -> None:
    page.goto(_data_url('<textarea name="x" hidden></textarea>'))  # type: ignore[attr-defined]
    inject_token(page, "textarea[name='x']", "TKN-123")  # type: ignore[arg-type]
    assert field_has_value(page, "textarea[name='x']", "TKN-123")  # type: ignore[arg-type]


def test_inject_token_dispatches_input_event(page: object) -> None:
    """A framework listening for 'input' should see our update."""
    html = """
        <textarea name="x" hidden></textarea>
        <script>
          window.__events = [];
          var el = document.querySelector('textarea[name="x"]');
          el.addEventListener('input', function() { window.__events.push('input'); });
          el.addEventListener('change', function() { window.__events.push('change'); });
        </script>
    """
    page.goto(_data_url(html))  # type: ignore[attr-defined]
    inject_token(page, "textarea[name='x']", "TKN")  # type: ignore[arg-type]
    events = page.evaluate("() => window.__events")  # type: ignore[attr-defined]
    assert "input" in events
    assert "change" in events


def test_inject_token_raises_on_missing_token(page: object) -> None:
    with pytest.raises(InjectionError, match="without a token"):
        inject_token(page, "textarea[name='x']", "")  # type: ignore[arg-type]


def test_inject_token_raises_when_selector_misses(page: object) -> None:
    page.goto(_data_url("<p>nothing</p>"))  # type: ignore[attr-defined]
    with pytest.raises(InjectionError):
        inject_token(page, "textarea[name='nope']", "TKN")  # type: ignore[arg-type]


def test_invoke_callback_runs_first_present(page: object) -> None:
    html = """
        <script>
          window.__captured = null;
          window.onTurnstileSuccess = function (t) {
              window.__captured = t;
              window.__captcha_invoked = true;
          };
        </script>
    """
    page.goto(_data_url(html))  # type: ignore[attr-defined]
    outcome = invoke_callback(
        page,  # type: ignore[arg-type]
        ["recaptchaCallback", "onTurnstileSuccess"],
        "TKN-XYZ",
    )
    assert outcome.invoked is True
    assert outcome.callback_name == "onTurnstileSuccess"
    assert page.evaluate("() => window.__captured") == "TKN-XYZ"  # type: ignore[attr-defined]
    assert callback_marker_present(page, "__captcha_invoked")  # type: ignore[arg-type]


def test_invoke_callback_reports_missing(page: object) -> None:
    page.goto(_data_url("<p></p>"))  # type: ignore[attr-defined]
    outcome = invoke_callback(page, ["nope1", "nope2"], "TKN")  # type: ignore[arg-type]
    assert outcome.invoked is False
    assert outcome.callback_name is None
    assert outcome.error is None


def test_invoke_callback_propagates_callback_throw(page: object) -> None:
    html = """
        <script>
          window.bad = function () { throw new Error('boom'); };
        </script>
    """
    page.goto(_data_url(html))  # type: ignore[attr-defined]
    outcome = invoke_callback(page, ["bad"], "TKN")  # type: ignore[arg-type]
    assert outcome.invoked is False
    assert outcome.callback_name == "bad"
    assert outcome.error is not None
    assert "boom" in outcome.error
