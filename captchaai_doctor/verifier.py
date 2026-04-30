"""Post-injection verification helpers.

After the injector has written the token (and optionally invoked the
page's callback) we want to confirm the page actually accepted the
update *before* we click "Submit". A common cause of false-positive
"submitted but rejected" reports is the response field reverting to
its prior value because the page's own JS rewrote it.

These helpers are deliberately small and read-only — the runner uses
them to record evidence in the report.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

log = logging.getLogger(__name__)


def field_has_value(page: Page, selector: str, expected: str) -> bool:
    """Return ``True`` if ``el.value`` at ``selector`` equals ``expected``.

    Reads the live DOM ``value`` (not the static HTML attribute) via
    ``eval_on_selector`` so it works for hidden fields too.
    """
    if not selector or expected is None:
        return False
    try:
        actual = page.eval_on_selector(selector, "(el) => el.value")
    except Exception as exc:  # pragma: no cover - defensive
        log.warning("verify field_has_value: read failed for %r: %s", selector, exc)
        return False
    return bool(actual == expected)


def callback_marker_present(page: Page, marker_var: str) -> bool:
    """Return ``True`` if ``window[marker_var]`` is truthy.

    A common pattern: a test page sets ``window.__captcha_invoked = true``
    inside its callback, so we can prove the callback actually ran
    rather than just being defined.
    """
    if not marker_var:
        return False
    try:
        result = page.evaluate(f"() => Boolean(window[{marker_var!r}])")
    except Exception as exc:  # pragma: no cover - defensive
        log.warning("verify callback_marker_present failed: %s", exc)
        return False
    return bool(result)


__all__ = ["callback_marker_present", "field_has_value"]
