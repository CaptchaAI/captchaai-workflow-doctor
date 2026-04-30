"""Pydantic v2 schemas for workflow profiles.

A profile fully describes a CAPTCHA-solving workflow to diagnose:
- target page
- browser engine + recording options
- CaptchaAI endpoints + polling parameters
- detection selectors / callback candidates
- ordered actions to take before solving and after token receipt
- success / failure conditions

Profiles must NEVER contain secrets. Use environment variables (`value_env`).
"""

from __future__ import annotations

import re
from typing import Annotated, Literal
from urllib.parse import urlparse

import cssselect
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

SUPPORTED_CAPTCHA_TYPES: tuple[str, ...] = (
    "turnstile",
    "recaptcha_v2",
    "recaptcha_v3",
    "cloudflare_challenge",
)

# Pattern that catches anything that LOOKS like an API key, hex token,
# session cookie, or password literal. Used by the secret scanner in config.py.
_SECRET_LIKE_PATTERN = re.compile(
    r"""
    (?:
      \b[a-fA-F0-9]{30,}\b           # long hex strings (api keys, hashes)
      |
      \b[A-Za-z0-9_\-]{40,}\b        # long opaque tokens (jwt-ish)
    )
    """,
    re.VERBOSE,
)


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------


def _is_valid_css_selector(selector: str) -> bool:
    """Return True if the string parses as a CSS selector."""
    try:
        cssselect.parse(selector)
    except cssselect.SelectorError:
        return False
    return True


# ----------------------------------------------------------------------------
# Sub-models
# ----------------------------------------------------------------------------


class StrictModel(BaseModel):
    """Base for all profile models: forbid unknown keys, freeze after build."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class Target(StrictModel):
    url: HttpUrl
    allowed_domains: list[str] = Field(min_length=1)

    @field_validator("allowed_domains")
    @classmethod
    def _domains_lowercase(cls, v: list[str]) -> list[str]:
        return [d.lower().strip() for d in v if d.strip()]

    @model_validator(mode="after")
    def _target_host_allowed(self) -> Target:
        host = urlparse(str(self.url)).hostname
        if host is None or host.lower() not in self.allowed_domains:
            raise ValueError(
                f"target.url host '{host}' must appear in target.allowed_domains "
                f"({self.allowed_domains})"
            )
        return self


class Browser(StrictModel):
    engine: Literal["chromium", "firefox", "webkit"] = "chromium"
    headless: bool = True
    timeout_ms: Annotated[int, Field(ge=1000, le=600_000)] = 60_000
    record_trace: bool = False
    screenshots: bool = True


class CaptchaAIConfig(StrictModel):
    submit_endpoint: HttpUrl = Field(
        default_factory=lambda: HttpUrl("https://ocr.captchaai.com/in.php")
    )
    result_endpoint: HttpUrl = Field(
        default_factory=lambda: HttpUrl("https://ocr.captchaai.com/res.php")
    )
    polling_interval_seconds: Annotated[float, Field(gt=0.0, le=60.0)] = 5.0
    max_wait_seconds: Annotated[int, Field(ge=10, le=600)] = 120


class Detection(StrictModel):
    sitekey_selector: str | None = None
    response_field_selector: str | None = None
    callback_candidates: list[str] = Field(default_factory=list)
    # reCAPTCHA v3 only: action name + advisory minimum score.
    # `action` is sent to CaptchaAI so the worker reproduces the same
    # action context the page would use; `min_score` is informational
    # (the solver ignores it but it appears in the report).
    action: str | None = None
    min_score: Annotated[float, Field(ge=0.0, le=1.0)] | None = None
    # Cloudflare Turnstile only: declares which widget rendering mode
    # the page uses. Has no runtime effect on the doctor's solving
    # path (the token is fetched from CaptchaAI either way) but is
    # surfaced in the report and used by the detector to confirm the
    # profile matches the live page.
    turnstile_mode: Literal["managed", "non-interactive", "invisible"] | None = None

    @field_validator("sitekey_selector", "response_field_selector")
    @classmethod
    def _selector_parseable(cls, v: str | None) -> str | None:
        if v is not None and not _is_valid_css_selector(v):
            raise ValueError(f"not a valid CSS selector: {v!r}")
        return v


# --- Actions (discriminated union) ------------------------------------------


class FillAction(StrictModel):
    type: Literal["fill"]
    selector: str
    value: str | None = None
    value_env: str | None = None

    @field_validator("selector")
    @classmethod
    def _selector_ok(cls, v: str) -> str:
        if not _is_valid_css_selector(v):
            raise ValueError(f"not a valid CSS selector: {v!r}")
        return v

    @model_validator(mode="after")
    def _exactly_one_value_source(self) -> FillAction:
        if (self.value is None) == (self.value_env is None):
            raise ValueError("fill action requires exactly one of `value` or `value_env`")
        return self


class ClickAction(StrictModel):
    type: Literal["click"]
    selector: str

    @field_validator("selector")
    @classmethod
    def _selector_ok(cls, v: str) -> str:
        if not _is_valid_css_selector(v):
            raise ValueError(f"not a valid CSS selector: {v!r}")
        return v


class WaitAction(StrictModel):
    type: Literal["wait"]
    milliseconds: Annotated[int, Field(ge=0, le=120_000)]


class InjectTokenAction(StrictModel):
    type: Literal["inject_token"]
    selector: str

    @field_validator("selector")
    @classmethod
    def _selector_ok(cls, v: str) -> str:
        if not _is_valid_css_selector(v):
            raise ValueError(f"not a valid CSS selector: {v!r}")
        return v


class InvokeCallbackIfDetectedAction(StrictModel):
    type: Literal["invoke_callback_if_detected"]


class ApplyClearanceCookieAction(StrictModel):
    """Apply the ``cf_clearance`` cookie returned by Cloudflare Challenge.

    Reads the structured token returned by
    ``CaptchaAIClient.submit_cloudflare_challenge`` (a JSON object with
    ``cookies`` + ``userAgent``), sets the cookie on the browser context,
    and updates the page's User-Agent so the cleared session matches the
    fingerprint Cloudflare validated.
    """

    type: Literal["apply_clearance_cookie"]


Action = Annotated[
    FillAction
    | ClickAction
    | WaitAction
    | InjectTokenAction
    | InvokeCallbackIfDetectedAction
    | ApplyClearanceCookieAction,
    Field(discriminator="type"),
]


class Actions(StrictModel):
    before_solve: list[Action] = Field(default_factory=list)
    after_token: list[Action] = Field(default_factory=list)


class Success(StrictModel):
    any_selector: list[str] = Field(default_factory=list)
    url_contains: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _at_least_one_condition(self) -> Success:
        if not self.any_selector and not self.url_contains:
            raise ValueError(
                "success must declare at least one of `any_selector` or `url_contains`"
            )
        return self

    @field_validator("any_selector")
    @classmethod
    def _selectors_ok(cls, v: list[str]) -> list[str]:
        for s in v:
            if not _is_valid_css_selector(s):
                raise ValueError(f"not a valid CSS selector: {s!r}")
        return v


class Failure(StrictModel):
    any_text: list[str] = Field(default_factory=list)
    any_selector: list[str] = Field(default_factory=list)

    @field_validator("any_selector")
    @classmethod
    def _selectors_ok(cls, v: list[str]) -> list[str]:
        for s in v:
            if not _is_valid_css_selector(s):
                raise ValueError(f"not a valid CSS selector: {s!r}")
        return v


class Proxy(StrictModel):
    """Outbound proxy used by both the CaptchaAI worker and the browser.

    Required when ``captcha_type=cloudflare_challenge`` because the
    ``cf_clearance`` cookie is bound to the IP that solved the
    challenge — replaying it from a different egress will be rejected.

    Credentials live ONLY in env vars; the YAML carries the variable
    NAMES, never the secret. The runtime resolves them on use.
    """

    type: Literal["HTTP", "HTTPS", "SOCKS4", "SOCKS5"]
    host: Annotated[str, Field(min_length=1, max_length=255)]
    port: Annotated[int, Field(ge=1, le=65535)]
    username_env: str | None = None
    password_env: str | None = None

    @model_validator(mode="after")
    def _both_or_neither_creds(self) -> Proxy:
        if (self.username_env is None) != (self.password_env is None):
            raise ValueError(
                "proxy.username_env and proxy.password_env must both be set or both omitted"
            )
        return self


# ----------------------------------------------------------------------------
# Top-level profile
# ----------------------------------------------------------------------------


class Profile(StrictModel):
    name: Annotated[str, Field(min_length=1, max_length=120, pattern=r"^[a-zA-Z0-9._\-]+$")]
    captcha_type: Literal["turnstile", "recaptcha_v2", "recaptcha_v3", "cloudflare_challenge"]
    target: Target
    browser: Browser = Field(default_factory=Browser)
    captchaai: CaptchaAIConfig = Field(default_factory=CaptchaAIConfig)
    detection: Detection = Field(default_factory=Detection)
    actions: Actions = Field(default_factory=Actions)
    success: Success
    failure: Failure = Field(default_factory=Failure)
    proxy: Proxy | None = None

    @model_validator(mode="after")
    def _proxy_required_for_cloudflare(self) -> Profile:
        if self.captcha_type == "cloudflare_challenge" and self.proxy is None:
            raise ValueError(
                "captcha_type=cloudflare_challenge requires a `proxy` block: "
                "the CaptchaAI worker must clear the challenge through the same "
                "network egress your browser will replay the cookie from"
            )
        return self


__all__ = [
    "SUPPORTED_CAPTCHA_TYPES",
    "_SECRET_LIKE_PATTERN",
    "Action",
    "Actions",
    "ApplyClearanceCookieAction",
    "Browser",
    "CaptchaAIConfig",
    "ClickAction",
    "Detection",
    "Failure",
    "FillAction",
    "InjectTokenAction",
    "InvokeCallbackIfDetectedAction",
    "Profile",
    "Proxy",
    "StrictModel",
    "Success",
    "Target",
    "WaitAction",
]
