"""Synchronous httpx client for the CaptchaAI 2captcha-compatible API.

Endpoints (defaults, overridable via :class:`~captchaai_doctor.schemas.CaptchaAIConfig`):

- ``in.php``  — submit a CAPTCHA challenge (returns captcha_id)
- ``res.php`` — poll for a result, get balance, report bad token

All requests use ``json=1`` so responses are uniform JSON of shape::

    {"status": 0|1, "request": "<value>", "error_text": "..."}

API key, captcha_id, and token are never logged in plaintext — see
:mod:`captchaai_doctor.redaction`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Final

import httpx

from captchaai_doctor.schemas import CaptchaAIConfig, Profile

log = logging.getLogger(__name__)

# Polling status codes returned by 2captcha-style res.php
_NOT_READY: Final[str] = "CAPCHA_NOT_READY"  # canonical 2captcha spelling
_NOT_READY_ALT: Final[str] = "CAPTCHA_NOT_READY"  # defensive alt

# Subset of error codes we map to specific exception types.
# Anything else falls under generic CaptchaAIServerError.
_RECOVERABLE_ERRORS: Final[frozenset[str]] = frozenset(
    {
        "ERROR_NO_SLOT_AVAILABLE",  # all worker threads busy — retry
    }
)
_AUTH_ERRORS: Final[frozenset[str]] = frozenset(
    {
        "ERROR_WRONG_USER_KEY",
        "ERROR_KEY_DOES_NOT_EXIST",
    }
)
_BALANCE_ERRORS: Final[frozenset[str]] = frozenset({"ERROR_ZERO_BALANCE"})
_PAGE_ERRORS: Final[frozenset[str]] = frozenset(
    {
        "ERROR_PAGEURL",
        "ERROR_GOOGLEKEY",
        "ERROR_BAD_TOKEN_OR_PAGEURL",
        "ERROR_DOMAIN_NOT_ALLOWED",
    }
)
_UNSOLVABLE_ERRORS: Final[frozenset[str]] = frozenset(
    {
        "ERROR_CAPTCHA_UNSOLVABLE",
    }
)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class CaptchaAIError(Exception):
    """Base class for all CaptchaAI client errors."""


class CaptchaAITransportError(CaptchaAIError):
    """Network / HTTP transport failure (DNS, refused, 5xx, etc.)."""


class CaptchaAIServerError(CaptchaAIError):
    """API returned ``status: 0`` with an error code."""

    def __init__(self, code: str, message: str | None = None) -> None:
        # Always include the code in the printable message so tests / log
        # consumers can match on it without reaching for ``.code``.
        if message:
            super().__init__(f"{code}: {message}")
        else:
            super().__init__(code)
        self.code = code


class CaptchaAIAuthError(CaptchaAIServerError):
    """Bad / missing API key."""


class CaptchaAIBalanceError(CaptchaAIServerError):
    """Out of balance."""


class CaptchaAIPageError(CaptchaAIServerError):
    """Page URL / sitekey / domain rejected by the solver."""


class CaptchaAIUnsolvableError(CaptchaAIServerError):
    """Workers tried but could not solve."""


class CaptchaAINotReadyError(CaptchaAIError):
    """The challenge is still being solved — caller should wait + retry."""


def _classify_error(code: str, message: str | None = None) -> CaptchaAIServerError:
    if code in _AUTH_ERRORS:
        return CaptchaAIAuthError(code, message)
    if code in _BALANCE_ERRORS:
        return CaptchaAIBalanceError(code, message)
    if code in _PAGE_ERRORS:
        return CaptchaAIPageError(code, message)
    if code in _UNSOLVABLE_ERRORS:
        return CaptchaAIUnsolvableError(code, message)
    return CaptchaAIServerError(code, message)


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SubmitResult:
    captcha_id: str


@dataclass(frozen=True)
class PollResult:
    token: str
    raw: dict[str, Any]


class CaptchaAIClient:
    """Thin sync wrapper around the 2captcha-compatible HTTP API.

    Usage::

        client = CaptchaAIClient(api_key="...", config=profile.captchaai)
        captcha_id = client.submit_turnstile(sitekey, page_url).captcha_id
        token = client.get_result(captcha_id).token
    """

    def __init__(
        self,
        api_key: str,
        *,
        config: CaptchaAIConfig | None = None,
        http_client: httpx.Client | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("api_key is required")
        self._api_key = api_key.strip()
        self._config = config or CaptchaAIConfig()
        self._owns_client = http_client is None
        self._http = http_client or httpx.Client(timeout=timeout_seconds)

    # ---- lifecycle ------------------------------------------------------

    def close(self) -> None:
        if self._owns_client:
            self._http.close()

    def __enter__(self) -> CaptchaAIClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ---- public API -----------------------------------------------------

    def get_balance(self) -> float:
        """Return account balance in account currency. Cheapest call to verify auth+endpoint."""
        data = self._get(action="getbalance")
        try:
            return float(data["request"])
        except (KeyError, TypeError, ValueError) as exc:
            raise CaptchaAIServerError(
                "BAD_BALANCE_RESPONSE", f"unexpected balance payload: {data!r}"
            ) from exc

    def submit_turnstile(
        self, *, sitekey: str, page_url: str, action: str | None = None
    ) -> SubmitResult:
        """Submit a Cloudflare Turnstile challenge."""
        params: dict[str, str] = {
            "method": "turnstile",
            "sitekey": sitekey,
            "pageurl": page_url,
        }
        if action:
            params["action"] = action
        return self._submit(params)

    def submit_recaptcha_v2(self, *, sitekey: str, page_url: str) -> SubmitResult:
        """Submit a reCAPTCHA v2 challenge."""
        return self._submit(
            {
                "method": "userrecaptcha",
                "googlekey": sitekey,
                "pageurl": page_url,
            }
        )

    def get_result(self, captcha_id: str) -> PollResult:
        """Fetch one poll cycle. Raises :class:`CaptchaAINotReadyError` if not ready."""
        data = self._get(action="get", id=captcha_id)
        token = data.get("request")
        if not isinstance(token, str) or not token:
            raise CaptchaAIServerError(
                "BAD_RESULT_RESPONSE", f"unexpected result payload: {data!r}"
            )
        return PollResult(token=token, raw=data)

    def report_bad(self, captcha_id: str) -> None:
        """Report a token that the target page rejected. No exception on best-effort."""
        try:
            self._get(action="reportbad", id=captcha_id)
        except CaptchaAIError:  # pragma: no cover — best effort
            log.debug("report_bad failed for captcha_id=%s", captcha_id)

    # ---- internals ------------------------------------------------------

    def _submit(self, params: dict[str, str]) -> SubmitResult:
        body = {"key": self._api_key, "json": "1", **params}
        url = str(self._config.submit_endpoint)
        log.debug("POST %s params=%s", url, {k: v for k, v in body.items() if k != "key"})
        try:
            resp = self._http.post(url, data=body)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise CaptchaAITransportError(f"submit transport error: {exc}") from exc
        data = self._parse_json(resp)
        # CaptchaAI returns the captcha id as either a string or an integer
        # (production API returns ints for `userrecaptcha`, strings for some
        # other methods). Coerce to string so downstream code is uniform.
        raw_id = data.get("request")
        if isinstance(raw_id, int) and raw_id > 0:
            captcha_id = str(raw_id)
        elif isinstance(raw_id, str) and raw_id:
            captcha_id = raw_id
        else:
            raise CaptchaAIServerError("BAD_SUBMIT_RESPONSE", f"unexpected payload: {data!r}")
        return SubmitResult(captcha_id=captcha_id)

    def _get(self, **params: str) -> dict[str, Any]:
        query = {"key": self._api_key, "json": "1", **params}
        url = str(self._config.result_endpoint)
        log.debug("GET %s params=%s", url, {k: v for k, v in query.items() if k != "key"})
        try:
            resp = self._http.get(url, params=query)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise CaptchaAITransportError(f"transport error: {exc}") from exc
        return self._parse_json(resp)

    def _parse_json(self, resp: httpx.Response) -> dict[str, Any]:
        try:
            data = resp.json()
        except ValueError as exc:
            raise CaptchaAIServerError(
                "BAD_JSON", f"non-JSON response: {resp.text[:200]!r}"
            ) from exc
        if not isinstance(data, dict):
            raise CaptchaAIServerError("BAD_JSON", f"non-object response: {data!r}")

        status = data.get("status")
        request = data.get("request")
        # Status semantics: 1 = success, 0 = error or not-ready.
        if status == 1:
            return data
        if status == 0:
            if request in (_NOT_READY, _NOT_READY_ALT):
                raise CaptchaAINotReadyError(_NOT_READY)
            code = request if isinstance(request, str) else "UNKNOWN_ERROR"
            raise _classify_error(code, data.get("error_text"))
        raise CaptchaAIServerError("BAD_STATUS", f"unexpected status field: {data!r}")


# ---------------------------------------------------------------------------
# Convenience factory using a Profile
# ---------------------------------------------------------------------------


def client_for_profile(profile: Profile, api_key: str) -> CaptchaAIClient:
    """Build a client whose endpoints come from ``profile.captchaai``."""
    return CaptchaAIClient(api_key=api_key, config=profile.captchaai)


__all__ = [
    "CaptchaAIAuthError",
    "CaptchaAIBalanceError",
    "CaptchaAIClient",
    "CaptchaAIError",
    "CaptchaAINotReadyError",
    "CaptchaAIPageError",
    "CaptchaAIServerError",
    "CaptchaAITransportError",
    "CaptchaAIUnsolvableError",
    "PollResult",
    "SubmitResult",
    "client_for_profile",
]
