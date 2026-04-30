"""Failure classifier — full implementation lands in Phase 5.

This module exists today as a thin recommendation map so the report
writer can already include "what to do next" text alongside each
:class:`~captchaai_doctor.runner.RootCause`. Phase 5 will add
confidence scoring, evidence aggregation, and unknown-failure
heuristics.
"""

from __future__ import annotations

# Imports must work without any runtime dependency on the runner module
# (which imports playwright); RootCause is a Literal alias so the
# annotation below uses ``str`` to stay loose.

RECOMMENDATIONS: dict[str, str] = {
    "ok": "Workflow succeeded. No action required.",
    "captchaai_unreachable": (
        "Could not reach api.captchaai.com. Check the network/firewall and CAPTCHAAI_BASE_URL."
    ),
    "captchaai_auth": "CaptchaAI rejected the API key. Rotate the key and retry.",
    "captchaai_balance": "Account balance is too low. Top up at https://captchaai.com.",
    "captchaai_unsolvable": (
        "CaptchaAI could not solve this challenge. Verify the sitekey is correct for the page URL."
    ),
    "captchaai_page_rejected": (
        "The page URL was rejected by CaptchaAI. Confirm the URL is reachable and matches the "
        "domain registered with the sitekey."
    ),
    "poll_timeout": (
        "Polling timed out before a token was returned. Increase poll_timeout_seconds or check "
        "CaptchaAI status page."
    ),
    "sitekey_not_found": (
        "No sitekey was found at the configured selector. Open the page in a browser, inspect "
        "the captcha widget, and update detection.sitekey_selector."
    ),
    "browser_action_failed": (
        "A pre/post action failed in the browser. Check action_steps in the report for the "
        "exact selector that did not match."
    ),
    "callback_not_invoked": (
        "None of the JS callback candidates were defined on the page when we tried to invoke "
        "them. Update detection.callback_candidates with the real callback name from the page."
    ),
    "verification_failed": (
        "The token was injected but the server still rejected the submission. Confirm the "
        "response field name and that the form's POST includes it."
    ),
    "recaptcha_v3_action_missing": (
        "Profile uses captcha_type=recaptcha_v3 but detection.action is empty. Set it to the "
        "exact action name the page passes to grecaptcha.execute (e.g. 'login', 'submit')."
    ),
    "unknown": "An unexpected error occurred. See `detail` in the report for the raw exception.",
}


def recommendation_for(root_cause: str) -> str:
    """Return a one-line human recommendation for ``root_cause``."""
    return RECOMMENDATIONS.get(root_cause, RECOMMENDATIONS["unknown"])


__all__ = ["RECOMMENDATIONS", "recommendation_for"]
