"""Polling loop on top of :class:`~captchaai_doctor.captchaai_client.CaptchaAIClient`.

Strategy:
- wait ``polling_interval_seconds`` between polls (no early first poll —
  CaptchaAI rarely solves in <5 s, so a leading sleep saves a wasted GET)
- back off mildly on ``ERROR_NO_SLOT_AVAILABLE`` (transient capacity)
- give up at ``max_wait_seconds`` with :class:`PollTimeout`

Returns a :class:`PollOutcome` with timing metadata for the report.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass

from captchaai_doctor.captchaai_client import (
    CaptchaAIClient,
    CaptchaAINotReadyError,
    CaptchaAIServerError,
    PollResult,
)
from captchaai_doctor.schemas import CaptchaAIConfig

log = logging.getLogger(__name__)

# Cap on the back-off bonus when the server is temporarily out of capacity.
_NO_SLOT_BACKOFF_CAP_S: float = 30.0


class PollTimeout(Exception):
    """Polling exceeded ``max_wait_seconds`` without a final result."""

    def __init__(self, captcha_id: str, waited_seconds: float, attempts: int) -> None:
        super().__init__(
            f"poll timeout for captcha_id={captcha_id[:4]}**** after "
            f"{waited_seconds:.1f}s ({attempts} attempts)"
        )
        self.captcha_id = captcha_id
        self.waited_seconds = waited_seconds
        self.attempts = attempts


@dataclass(frozen=True)
class PollOutcome:
    token: str
    captcha_id: str
    attempts: int
    elapsed_seconds: float


def _now() -> float:
    return time.monotonic()


def poll_until_ready(
    client: CaptchaAIClient,
    captcha_id: str,
    *,
    config: CaptchaAIConfig,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = _now,
) -> PollOutcome:
    """Poll until a token is ready, the deadline expires, or a hard error fires.

    Hard errors (auth, balance, page, unsolvable) propagate immediately —
    polling cannot recover from them.
    """
    interval = float(config.polling_interval_seconds)
    deadline = clock() + float(config.max_wait_seconds)
    attempts = 0
    started = clock()

    while True:
        # Sleep BEFORE the first poll: results are never instant.
        remaining = deadline - clock()
        if remaining <= 0:
            raise PollTimeout(captcha_id, clock() - started, attempts)
        sleep(min(interval, remaining))

        attempts += 1
        try:
            result: PollResult = client.get_result(captcha_id)
        except CaptchaAINotReadyError:
            log.debug("captcha_id=%s****: not ready (attempt %d)", captcha_id[:4], attempts)
            continue
        except CaptchaAIServerError as exc:
            if exc.code == "ERROR_NO_SLOT_AVAILABLE":
                # Transient — wait a touch longer before resuming normal cadence.
                bonus = min(interval, _NO_SLOT_BACKOFF_CAP_S)
                log.warning("no slot available; backing off %.1fs", bonus)
                sleep(bonus)
                continue
            raise

        return PollOutcome(
            token=result.token,
            captcha_id=captcha_id,
            attempts=attempts,
            elapsed_seconds=clock() - started,
        )


__all__ = ["PollOutcome", "PollTimeout", "poll_until_ready"]
