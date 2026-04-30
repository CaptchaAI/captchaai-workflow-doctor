"""End-to-end workflow runner.

Single entry point :func:`run_workflow` that:

1. launches a browser per the profile,
2. navigates to ``profile.target.url``,
3. runs the ``actions.before_solve`` steps,
4. detects the sitekey,
5. submits the challenge to CaptchaAI (real or mocked),
6. polls until a token is returned,
7. runs the ``actions.after_token`` steps (which inject the token and
   typically click Submit),
8. checks ``success`` / ``failure`` conditions, captures screenshots,
9. returns a :class:`RunResult` for the report writer.

The runner is intentionally deterministic: all timing knobs come from
the profile, all I/O is wrapped, and the same :class:`RunResult` shape
is produced whether we used the real client or the fake one.
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Protocol

from captchaai_doctor.browser import (
    ActionStep,
    BrowserActionError,
    BrowserSession,
    launch_browser,
)
from captchaai_doctor.captchaai_client import (
    CaptchaAIError,
    CaptchaAINotReadyError,
    PollResult,
    SubmitResult,
)
from captchaai_doctor.poller import PollOutcome, PollTimeout, poll_until_ready
from captchaai_doctor.redaction import install_global_redaction
from captchaai_doctor.schemas import Profile

if TYPE_CHECKING:  # pragma: no cover
    pass

log = logging.getLogger(__name__)

RunStatus = Literal["success", "failure", "error"]
RootCause = Literal[
    "ok",
    "captchaai_unreachable",
    "captchaai_auth",
    "captchaai_balance",
    "captchaai_unsolvable",
    "captchaai_page_rejected",
    "poll_timeout",
    "sitekey_not_found",
    "browser_action_failed",
    "callback_not_invoked",
    "verification_failed",
    "recaptcha_v3_action_missing",
    "unknown",
]


# ---------------------------------------------------------------------------
# Protocol for the CAPTCHA client (so runner accepts both real + fake)
# ---------------------------------------------------------------------------


class _CaptchaClientProtocol(Protocol):  # pragma: no cover - structural
    def submit_turnstile(self, *, sitekey: str, page_url: str) -> SubmitResult: ...
    def submit_recaptcha_v2(self, *, sitekey: str, page_url: str) -> SubmitResult: ...
    def submit_recaptcha_v3(
        self,
        *,
        sitekey: str,
        page_url: str,
        action: str,
        min_score: float = 0.3,
    ) -> SubmitResult: ...
    def get_result(self, captcha_id: str) -> PollResult: ...
    def get_balance(self) -> float: ...
    def report_bad(self, captcha_id: str) -> None: ...


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class RunResult:
    profile_name: str
    captcha_type: str
    target_url: str
    started_at: str
    ended_at: str
    duration_seconds: float
    status: RunStatus
    root_cause: RootCause
    detail: str | None = None
    captcha_id_redacted: str | None = None
    poll_attempts: int = 0
    poll_seconds: float = 0.0
    sitekey_found: str | None = None
    screenshots: list[str] = field(default_factory=list)
    action_steps: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def _utcnow_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _redact_id(captcha_id: str | None) -> str | None:
    if not captcha_id:
        return None
    if len(captcha_id) <= 4:
        return "****"
    return f"{captcha_id[:4]}****"


def _submit_for(client: _CaptchaClientProtocol, profile: Profile, sitekey: str) -> SubmitResult:
    page_url = str(profile.target.url)
    if profile.captcha_type == "turnstile":
        return client.submit_turnstile(sitekey=sitekey, page_url=page_url)
    if profile.captcha_type == "recaptcha_v2":
        return client.submit_recaptcha_v2(sitekey=sitekey, page_url=page_url)
    if profile.captcha_type == "recaptcha_v3":
        action = profile.detection.action
        if not action:
            raise _ProfileMisconfigured(
                "recaptcha_v3 requires detection.action in the profile (the action name "
                "the page passes to grecaptcha.execute)"
            )
        min_score = profile.detection.min_score if profile.detection.min_score is not None else 0.3
        return client.submit_recaptcha_v3(
            sitekey=sitekey, page_url=page_url, action=action, min_score=min_score
        )
    raise ValueError(f"unsupported captcha_type: {profile.captcha_type}")  # pragma: no cover


class _ProfileMisconfigured(RuntimeError):
    """Raised when the profile lacks fields required for the chosen captcha_type."""


def _classify_captchaai_error(exc: CaptchaAIError) -> RootCause:
    from captchaai_doctor.captchaai_client import (
        CaptchaAIAuthError,
        CaptchaAIBalanceError,
        CaptchaAIPageError,
        CaptchaAITransportError,
        CaptchaAIUnsolvableError,
    )

    if isinstance(exc, CaptchaAIAuthError):
        return "captchaai_auth"
    if isinstance(exc, CaptchaAIBalanceError):
        return "captchaai_balance"
    if isinstance(exc, CaptchaAIPageError):
        return "captchaai_page_rejected"
    if isinstance(exc, CaptchaAIUnsolvableError):
        return "captchaai_unsolvable"
    if isinstance(exc, CaptchaAITransportError):
        return "captchaai_unreachable"
    return "unknown"


def _classify_browser_error(exc: BrowserActionError) -> RootCause:
    msg = str(exc).lower()
    if "callback" in msg:
        return "callback_not_invoked"
    return "browser_action_failed"


def _check_success(session: BrowserSession, profile: Profile) -> tuple[bool, str | None]:
    page = session.page
    for sel in profile.success.any_selector:
        try:
            if page.query_selector(sel) is not None:
                return True, f"matched success selector {sel!r}"
        except Exception:  # pragma: no cover - defensive
            continue
    current_url = page.url
    for needle in profile.success.url_contains:
        if needle in current_url:
            return True, f"url contains {needle!r}"
    return False, None


def _check_failure(session: BrowserSession, profile: Profile) -> str | None:
    page = session.page
    for sel in profile.failure.any_selector:
        try:
            if page.query_selector(sel) is not None:
                return f"matched failure selector {sel!r}"
        except Exception:  # pragma: no cover
            continue
    if profile.failure.any_text:
        try:
            body_text = (page.inner_text("body") or "").lower()
        except Exception:  # pragma: no cover
            body_text = ""
        for needle in profile.failure.any_text:
            if needle.lower() in body_text:
                return f"failure text matched: {needle!r}"
    return None


def run_workflow(
    profile: Profile,
    *,
    client: _CaptchaClientProtocol,
    artifact_dir: str | Path,
    headed: bool = False,
) -> RunResult:
    """Drive the full workflow described by ``profile`` once."""
    install_global_redaction()
    artifacts = Path(artifact_dir)
    artifacts.mkdir(parents=True, exist_ok=True)

    started_at = _utcnow_iso()
    t0 = time.monotonic()

    captcha_id: str | None = None
    poll_outcome: PollOutcome | None = None
    sitekey: str | None = None
    screenshots: list[str] = []
    action_steps: list[ActionStep] = []

    def finalize(status: RunStatus, root_cause: RootCause, detail: str | None) -> RunResult:
        return RunResult(
            profile_name=profile.name,
            captcha_type=profile.captcha_type,
            target_url=str(profile.target.url),
            started_at=started_at,
            ended_at=_utcnow_iso(),
            duration_seconds=round(time.monotonic() - t0, 3),
            status=status,
            root_cause=root_cause,
            detail=detail,
            captcha_id_redacted=_redact_id(captcha_id),
            poll_attempts=poll_outcome.attempts if poll_outcome else 0,
            poll_seconds=round(poll_outcome.elapsed_seconds, 3) if poll_outcome else 0.0,
            sitekey_found=sitekey,
            screenshots=screenshots,
            action_steps=[asdict(s) for s in action_steps],
        )

    try:
        with launch_browser(profile.browser, headed_override=headed or None) as session:
            log.info("navigating to %s", profile.target.url)
            session.page.goto(str(profile.target.url), timeout=profile.browser.timeout_ms)

            if profile.actions.before_solve:
                try:
                    action_steps.extend(
                        session.run_actions(
                            list(profile.actions.before_solve), detection=profile.detection
                        )
                    )
                except BrowserActionError as exc:
                    return finalize("failure", _classify_browser_error(exc), str(exc))

            sitekey = session.read_sitekey(profile.detection)
            if sitekey is None:
                # Run the heuristic scan so the report can tell the user
                # *what* widget (if any) was actually on the page when their
                # configured selector missed.
                from captchaai_doctor.detector import detect_widget

                detected = detect_widget(session.page)
                screenshots.append(session.screenshot(str(artifacts / "01-no-sitekey.png")) or "")
                if detected is not None:
                    sitekey_detail = (
                        f"no sitekey at selector {profile.detection.sitekey_selector!r} "
                        f"(but the page does expose a {detected.kind!r} widget at "
                        f"{detected.selector_matched!r}; update detection.sitekey_selector)"
                    )
                else:
                    sitekey_detail = (
                        f"no sitekey at selector {profile.detection.sitekey_selector!r} "
                        "(no Turnstile/reCAPTCHA widget detected on the page either)"
                    )
                return finalize("failure", "sitekey_not_found", sitekey_detail)

            log.info("submitting %s challenge", profile.captcha_type)
            try:
                submit = _submit_for(client, profile, sitekey)
                captcha_id = submit.captcha_id
                poll_outcome = poll_until_ready(
                    client,  # type: ignore[arg-type]
                    captcha_id,
                    config=profile.captchaai,
                )
            except _ProfileMisconfigured as exc:
                return finalize("failure", "recaptcha_v3_action_missing", str(exc))
            except PollTimeout as exc:
                return finalize("failure", "poll_timeout", str(exc))
            except CaptchaAINotReadyError:  # pragma: no cover - poller catches this
                return finalize("failure", "poll_timeout", "still not ready at deadline")
            except CaptchaAIError as exc:
                return finalize("failure", _classify_captchaai_error(exc), str(exc))

            token = poll_outcome.token

            if profile.actions.after_token:
                try:
                    action_steps.extend(
                        session.run_actions(
                            list(profile.actions.after_token),
                            token=token,
                            detection=profile.detection,
                        )
                    )
                except BrowserActionError as exc:
                    screenshots.append(
                        session.screenshot(str(artifacts / "02-after-token-failure.png")) or ""
                    )
                    return finalize("failure", _classify_browser_error(exc), str(exc))

            ok, detail = _check_success(session, profile)
            screenshots.append(session.screenshot(str(artifacts / "03-final.png")) or "")
            if ok:
                return finalize("success", "ok", detail)

            failure_detail = _check_failure(session, profile)
            return finalize(
                "failure",
                "verification_failed",
                failure_detail or "neither success nor failure markers were observed",
            )
    except Exception as exc:  # pragma: no cover - last resort
        log.exception("unhandled error in run_workflow")
        return finalize("error", "unknown", f"{type(exc).__name__}: {exc}")


__all__ = ["RootCause", "RunResult", "RunStatus", "run_workflow"]
