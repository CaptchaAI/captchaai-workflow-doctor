"""CAPTCHA widget / sitekey / callback detection helpers.

Pure helpers that operate on a live Playwright :class:`~playwright.sync_api.Page`.
The runner uses these to read DOM state without mutating it; the
injector mutates it.

Two layers:

- *profile-driven*: read the explicit selectors from
  :class:`captchaai_doctor.schemas.Detection`. This is what we always
  do today.
- *heuristic*: when no profile selector is given (or the profile
  selector misses), :func:`detect_widget` scans for common Turnstile
  and reCAPTCHA markers and returns a :class:`DetectedWidget` so the
  user can be told *what* the page actually looks like.

Heuristic detection is intentionally conservative: false positives are
worse than false negatives because the user trusts our root cause.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from playwright.sync_api import Page

    from captchaai_doctor.schemas import Detection

log = logging.getLogger(__name__)

CaptchaKind = Literal["turnstile", "recaptcha_v2", "recaptcha_v3", "unknown"]

# (selector, attribute that holds the sitekey, kind)
_HEURISTIC_RULES: list[tuple[str, str, CaptchaKind]] = [
    # Cloudflare Turnstile
    ("div.cf-turnstile[data-sitekey]", "data-sitekey", "turnstile"),
    ("[data-sitekey].cf-turnstile", "data-sitekey", "turnstile"),
    ("#cf-turnstile[data-sitekey]", "data-sitekey", "turnstile"),
    # Google reCAPTCHA v2
    ("div.g-recaptcha[data-sitekey]", "data-sitekey", "recaptcha_v2"),
    (".g-recaptcha[data-sitekey]", "data-sitekey", "recaptcha_v2"),
    # Generic catch-all (must be last)
    ("[data-sitekey]", "data-sitekey", "unknown"),
]

# reCAPTCHA v3 has no widget div — only a script tag with `?render=SITEKEY`.
_RECAPTCHA_V3_SCRIPT_SELECTOR = "script[src*='recaptcha'][src*='render=']"
_RENDER_QUERY_RE = re.compile(r"[?&]render=([^&]+)")

# Default callback names to probe per kind, in priority order.
DEFAULT_CALLBACK_CANDIDATES: dict[CaptchaKind, list[str]] = {
    "turnstile": ["onTurnstileSuccess", "turnstileCallback", "onloadTurnstileCallback"],
    "recaptcha_v2": ["onRecaptchaSuccess", "recaptchaCallback", "onloadRecaptchaCallback"],
    # v3 has no callback in the page; the doctor uses grecaptcha.execute().
    "recaptcha_v3": [],
    "unknown": [],
}

# Default response field selector per kind.
DEFAULT_RESPONSE_FIELD: dict[CaptchaKind, str] = {
    "turnstile": "textarea[name='cf-turnstile-response']",
    "recaptcha_v2": "textarea[name='g-recaptcha-response']",
    # v3 stores its token in a hidden input named after the action,
    # but the canonical default field is g-recaptcha-response.
    "recaptcha_v3": "input[name='g-recaptcha-response']",
    "unknown": "",
}


@dataclass(frozen=True)
class DetectedWidget:
    """The result of a heuristic widget scan."""

    kind: CaptchaKind
    sitekey: str
    selector_matched: str
    sitekey_attribute: str
    # Turnstile only: "managed" | "non-interactive" | "invisible".
    # Read from the widget element's `data-size` attribute when present.
    # ``None`` for non-Turnstile kinds or when the page omits data-size.
    turnstile_mode: str | None = None


def read_sitekey(page: Page, detection: Detection) -> str | None:
    """Read the sitekey from the profile-supplied selector.

    Looks at ``data-sitekey``, ``data-sitekey-id``, and ``value`` attrs;
    additionally extracts the sitekey from a ``?render=SITEKEY`` query
    string in ``src`` (the reCAPTCHA v3 integration shape).
    """
    selector = detection.sitekey_selector
    if not selector:
        return None
    try:
        handle = page.query_selector(selector)
    except Exception as exc:  # pragma: no cover - defensive
        log.warning("sitekey read failed for %r: %s", selector, exc)
        return None
    if handle is None:
        return None
    for attr in ("data-sitekey", "data-sitekey-id", "value"):
        value = handle.get_attribute(attr)
        if value:
            return value
    src = handle.get_attribute("src")
    if src:
        match = _RENDER_QUERY_RE.search(src)
        if match:
            return match.group(1)
    return None


def detect_widget(page: Page) -> DetectedWidget | None:
    """Heuristically classify the captcha widget on the current page."""
    for selector, attr, kind in _HEURISTIC_RULES:
        try:
            handle = page.query_selector(selector)
        except Exception:  # pragma: no cover - defensive
            continue
        if handle is None:
            continue
        sitekey = handle.get_attribute(attr)
        if not sitekey:
            continue
        turnstile_mode: str | None = None
        if kind == "turnstile":
            size = handle.get_attribute("data-size")
            if size in ("invisible", "compact", "normal", "flexible"):
                turnstile_mode = "invisible" if size == "invisible" else "managed"
        return DetectedWidget(
            kind=kind,
            sitekey=sitekey,
            selector_matched=selector,
            sitekey_attribute=attr,
            turnstile_mode=turnstile_mode,
        )
    # Fall back to reCAPTCHA v3 (no widget div, only a script tag).
    try:
        handle = page.query_selector(_RECAPTCHA_V3_SCRIPT_SELECTOR)
    except Exception:  # pragma: no cover - defensive
        handle = None
    if handle is not None:
        src = handle.get_attribute("src") or ""
        match = _RENDER_QUERY_RE.search(src)
        if match:
            return DetectedWidget(
                kind="recaptcha_v3",
                sitekey=match.group(1),
                selector_matched=_RECAPTCHA_V3_SCRIPT_SELECTOR,
                sitekey_attribute="src?render=",
            )
    return None


def detect_callback(page: Page, candidates: list[str]) -> str | None:
    """Return the name of the first callback present on ``window``.

    A *present* callback is any ``window[name]`` whose ``typeof`` is
    ``"function"``. This is the contract used by both Turnstile and
    reCAPTCHA-v2: the page declares a global callback that receives
    the token.
    """
    if not candidates:
        return None
    script = """
        (names) => {
            for (const name of names) {
                if (typeof window[name] === 'function') return name;
            }
            return null;
        }
    """
    try:
        result = page.evaluate(script, candidates)
    except Exception as exc:  # pragma: no cover - defensive
        log.warning("callback probe failed: %s", exc)
        return None
    return result if isinstance(result, str) else None


__all__ = [
    "DEFAULT_CALLBACK_CANDIDATES",
    "DEFAULT_RESPONSE_FIELD",
    "CaptchaKind",
    "DetectedWidget",
    "detect_callback",
    "detect_widget",
    "read_sitekey",
]
