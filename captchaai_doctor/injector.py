"""Token injection helpers.

The injector is responsible for the *write* side of the workflow:
putting the solved CAPTCHA token into the page in the way the page's
own JavaScript expects to find it.

Two operations are supported, mirroring how real captcha widgets
deliver their token:

1. :func:`inject_token` writes the token into a hidden response field
   (``cf-turnstile-response`` for Turnstile, ``g-recaptcha-response``
   for reCAPTCHA v2). Most server-side validators read this field
   directly from the form POST.
2. :func:`invoke_callback` calls the page's JS callback (e.g.
   ``onTurnstileSuccess(token)``) which is what the real widget would
   do. Many SPAs only progress when the callback runs, so we have to
   simulate it.

Both operations log redacted progress information.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

log = logging.getLogger(__name__)


class InjectionError(RuntimeError):
    """Raised when token injection or callback invocation cannot complete."""


@dataclass(frozen=True)
class CallbackInvocation:
    """Outcome of a single :func:`invoke_callback` call."""

    invoked: bool
    callback_name: str | None
    error: str | None = None


def inject_token(page: Page, response_field_selector: str, token: str) -> None:
    """Set ``token`` on the hidden response field at ``response_field_selector``.

    Uses ``eval_on_selector`` (rather than ``locator.fill``) so we can
    write to fields that are intentionally hidden — both Turnstile and
    reCAPTCHA mark their response field ``hidden`` / ``display:none``,
    and Playwright's ``fill`` refuses to touch hidden elements.

    After setting ``el.value`` we dispatch ``input`` and ``change``
    events so any framework that listens for them (React/Vue/Angular)
    notices the update.
    """
    if not token:
        raise InjectionError("inject_token called without a token")
    if not response_field_selector:
        raise InjectionError("inject_token called without a selector")
    try:
        page.eval_on_selector(
            response_field_selector,
            "(el, value) => {"
            "  el.value = value;"
            "  el.dispatchEvent(new Event('input', {bubbles: true}));"
            "  el.dispatchEvent(new Event('change', {bubbles: true}));"
            "}",
            token,
        )
    except Exception as exc:
        raise InjectionError(f"inject_token failed for {response_field_selector!r}: {exc}") from exc
    log.debug("injected token (len=%d) into %s", len(token), response_field_selector)


def invoke_callback(page: Page, candidates: list[str], token: str) -> CallbackInvocation:
    """Call the first ``window[name]`` from ``candidates`` that is a function.

    Returns a :class:`CallbackInvocation`:

    - ``invoked=True``  — at least one candidate was a function and ran cleanly.
    - ``invoked=False`` — none of the candidates were defined.
    - ``error != None`` — a candidate ran but threw inside the page.
    """
    if not candidates:
        return CallbackInvocation(invoked=False, callback_name=None)
    script = """
        ({candidates, token}) => {
            for (const name of candidates) {
                const fn = window[name];
                if (typeof fn === 'function') {
                    try { fn(token); } catch (e) {
                        return {ok: false, name, error: String(e)};
                    }
                    return {ok: true, name, error: null};
                }
            }
            return {ok: false, name: null, error: null};
        }
    """
    try:
        result = page.evaluate(script, {"candidates": candidates, "token": token})
    except Exception as exc:
        raise InjectionError(f"invoke_callback failed: {exc}") from exc
    if not isinstance(result, dict):  # pragma: no cover - defensive
        raise InjectionError(f"invoke_callback returned unexpected payload: {result!r}")
    if result.get("ok"):
        log.debug("invoked callback %s", result.get("name"))
        return CallbackInvocation(invoked=True, callback_name=result.get("name"))
    if result.get("error"):
        return CallbackInvocation(
            invoked=False, callback_name=result.get("name"), error=result.get("error")
        )
    return CallbackInvocation(invoked=False, callback_name=None)


__all__ = [
    "CallbackInvocation",
    "InjectionError",
    "inject_token",
    "invoke_callback",
]
