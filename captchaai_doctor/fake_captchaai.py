"""In-process fake CaptchaAI client for demos and tests.

Implements the same surface as :class:`captchaai_doctor.captchaai_client.CaptchaAIClient`
but does not touch the network. Always returns the well-known token
``FAKE_TOKEN_OK`` (matches what the demo Flask apps accept).

This is what ``captchaai-doctor run --mock-captchaai`` and the demo
commands inject so the walking skeleton can be exercised end-to-end on
any CI runner with zero credentials and zero spend.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from captchaai_doctor.captchaai_client import (
    CaptchaAINotReadyError,
    PollResult,
    SubmitResult,
)

#: Token that the mock Flask apps in :mod:`demos` accept as valid.
FAKE_OK_TOKEN: Final[str] = "FAKE_TOKEN_OK"


@dataclass
class FakeCaptchaAIClient:
    """A drop-in replacement for ``CaptchaAIClient`` with no network I/O.

    Configurable knobs:

    - ``balance``         — value returned by :meth:`get_balance`.
    - ``token``           — value returned by :meth:`get_result`.
    - ``not_ready_count`` — how many times :meth:`get_result` should raise
                            :class:`CaptchaAINotReadyError` before returning
                            the token. Useful for exercising the poll loop.
    """

    balance: float = 100.0
    token: str = FAKE_OK_TOKEN
    not_ready_count: int = 0

    # Recorded call history so tests can assert against it.
    submitted: list[dict[str, str]] = field(default_factory=list)
    polled: list[str] = field(default_factory=list)
    reported_bad: list[str] = field(default_factory=list)

    _next_id: int = 1
    _remaining_not_ready: int | None = None

    # ---- shape parity with CaptchaAIClient -------------------------------

    def __enter__(self) -> FakeCaptchaAIClient:
        return self

    def __exit__(self, *exc: object) -> None:  # pragma: no cover - trivial
        return None

    def close(self) -> None:  # pragma: no cover - trivial
        return None

    def get_balance(self) -> float:
        return float(self.balance)

    def submit_turnstile(
        self, *, sitekey: str, page_url: str, action: str | None = None
    ) -> SubmitResult:
        return self._submit({"method": "turnstile", "sitekey": sitekey, "pageurl": page_url})

    def submit_recaptcha_v2(self, *, sitekey: str, page_url: str) -> SubmitResult:
        return self._submit({"method": "userrecaptcha", "googlekey": sitekey, "pageurl": page_url})

    def get_result(self, captcha_id: str) -> PollResult:
        self.polled.append(captcha_id)
        if self._remaining_not_ready is None:
            self._remaining_not_ready = max(0, int(self.not_ready_count))
        if self._remaining_not_ready > 0:
            self._remaining_not_ready -= 1
            raise CaptchaAINotReadyError("CAPCHA_NOT_READY")
        return PollResult(token=self.token, raw={"status": 1, "request": self.token})

    def report_bad(self, captcha_id: str) -> None:
        self.reported_bad.append(captcha_id)

    # ---- helpers ---------------------------------------------------------

    def _submit(self, params: dict[str, str]) -> SubmitResult:
        self.submitted.append(params)
        captcha_id = str(self._next_id).zfill(7)  # always >= 7 digits so redaction kicks in
        self._next_id += 1
        return SubmitResult(captcha_id=captcha_id)


def make_fake_client(
    *, not_ready_count: int = 0, token: str = FAKE_OK_TOKEN
) -> FakeCaptchaAIClient:
    """Convenience factory used by the runner when ``--mock-captchaai`` is set."""
    return FakeCaptchaAIClient(token=token, not_ready_count=not_ready_count)


__all__ = [
    "FAKE_OK_TOKEN",
    "FakeCaptchaAIClient",
    "make_fake_client",
]
