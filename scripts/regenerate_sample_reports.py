"""Regenerate the sample reports under ``sample-reports/``.

These reports are checked in so users can preview what a successful and
each failure-mode run looks like without having to run the doctor
themselves. They are also a fast smoke for the report writers.

Usage::

    python scripts/regenerate_sample_reports.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from captchaai_doctor.report import write_html_report, write_json_report  # noqa: E402
from captchaai_doctor.runner import RunResult  # noqa: E402

OUT = REPO_ROOT / "sample-reports"


def _base(**overrides: object) -> RunResult:
    base: dict[str, object] = dict(
        profile_name="local-demo-login-turnstile",
        captcha_type="turnstile",
        target_url="http://127.0.0.1:8765/login",
        started_at="2026-04-30T21:00:00Z",
        ended_at="2026-04-30T21:00:08Z",
        duration_seconds=8.123,
        status="success",
        root_cause="ok",
        detail=None,
        captcha_id_redacted="A1B2****",
        poll_attempts=2,
        poll_seconds=4.0,
        sitekey_found="0xMOCK_SITEKEY_DEMO",
        screenshots=["03-final.png"],
        action_steps=[
            {
                "type": "fill",
                "selector": "input[name='email']",
                "succeeded": True,
                "detail": None,
            },
            {
                "type": "fill",
                "selector": "input[name='password']",
                "succeeded": True,
                "detail": None,
            },
            {
                "type": "inject_token",
                "selector": "textarea[name='cf-turnstile-response']",
                "succeeded": True,
                "detail": None,
            },
            {
                "type": "invoke_callback_if_detected",
                "selector": None,
                "succeeded": True,
                "detail": None,
            },
            {"type": "wait", "selector": None, "succeeded": True, "detail": None},
            {
                "type": "click",
                "selector": "button[type='submit']",
                "succeeded": True,
                "detail": None,
            },
        ],
    )
    base.update(overrides)
    return RunResult(**base)  # type: ignore[arg-type]


SAMPLES: dict[str, RunResult] = {
    "success": _base(),
    "verification-failed": _base(
        status="failure",
        root_cause="verification_failed",
        detail="failure text matched: 'captcha verification failed'",
        action_steps=_base().action_steps,
    ),
    "callback-not-invoked": _base(
        status="failure",
        root_cause="callback_not_invoked",
        detail=(
            "none of the callback candidates were defined on the page: "
            "['onTurnstileSuccess', 'turnstileCallback']"
        ),
        action_steps=[
            *_base().action_steps[:3],
            {
                "type": "invoke_callback_if_detected",
                "selector": None,
                "succeeded": False,
                "detail": "none of the callback candidates were defined on the page",
            },
        ],
    ),
    "sitekey-not-found": _base(
        status="failure",
        root_cause="sitekey_not_found",
        detail=(
            "no sitekey at selector '[data-sitekey]' "
            "(but the page does expose a 'recaptcha_v2' widget at "
            "'div.g-recaptcha[data-sitekey]'; update detection.sitekey_selector)"
        ),
        sitekey_found=None,
        action_steps=_base().action_steps[:2],
        screenshots=["01-no-sitekey.png"],
    ),
    "captchaai-balance": _base(
        status="failure",
        root_cause="captchaai_balance",
        detail="Account balance too low (code: ERROR_NO_SLOT_AVAILABLE)",
        captcha_id_redacted=None,
        poll_attempts=0,
        poll_seconds=0.0,
        action_steps=_base().action_steps[:2],
        screenshots=[],
    ),
    "recaptcha-v3-success": _base(
        profile_name="local-demo-form-recaptcha-v3",
        captcha_type="recaptcha_v3",
        target_url="http://127.0.0.1:8768/contact",
        sitekey_found="6LcMOCK_RECAPTCHA_V3_SITEKEY_DEMO",
        action_steps=[
            {
                "type": "fill",
                "selector": "input[name='name']",
                "succeeded": True,
                "detail": None,
            },
            {
                "type": "fill",
                "selector": "textarea[name='message']",
                "succeeded": True,
                "detail": None,
            },
            {
                "type": "inject_token",
                "selector": "input[name='g-recaptcha-response']",
                "succeeded": True,
                "detail": None,
            },
            {"type": "wait", "selector": None, "succeeded": True, "detail": None},
            {
                "type": "click",
                "selector": "button[type='submit']",
                "succeeded": True,
                "detail": None,
            },
        ],
    ),
    "recaptcha-v3-action-missing": _base(
        profile_name="local-demo-form-recaptcha-v3",
        captcha_type="recaptcha_v3",
        target_url="http://127.0.0.1:8768/contact",
        status="failure",
        root_cause="recaptcha_v3_action_missing",
        detail=(
            "recaptcha_v3 requires detection.action in the profile (the action name "
            "the page passes to grecaptcha.execute)"
        ),
        sitekey_found="6LcMOCK_RECAPTCHA_V3_SITEKEY_DEMO",
        captcha_id_redacted=None,
        poll_attempts=0,
        poll_seconds=0.0,
        action_steps=[
            {
                "type": "fill",
                "selector": "input[name='name']",
                "succeeded": True,
                "detail": None,
            },
            {
                "type": "fill",
                "selector": "textarea[name='message']",
                "succeeded": True,
                "detail": None,
            },
        ],
        screenshots=["01-detected.png"],
    ),
}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, result in SAMPLES.items():
        write_json_report(result, OUT / f"{name}.json")
        write_html_report(result, OUT / f"{name}.html")
        print(f"  wrote {name}.json + {name}.html")
    print(f"regenerated {len(SAMPLES)} sample reports under {OUT}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
