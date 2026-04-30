"""Live API smoke test (Option B).

Skipped unless ``DOCTOR_ALLOW_REAL_API=1`` is set in the environment AND
``CAPTCHAAI_API_KEY`` is provided. Hits ONLY the cheapest endpoint
(``getbalance``) so this stays cheap-and-deterministic — it confirms the
endpoint hostname + the API key shape, no solve consumed.

The full real-solve E2E lives under ``tests/e2e/`` and is exercised by
``scripts/run-real-e2e.sh`` on the test server in Phase 5.
"""

from __future__ import annotations

import os

import pytest

from captchaai_doctor.captchaai_client import CaptchaAIClient

LIVE_ENABLED = os.environ.get("DOCTOR_ALLOW_REAL_API") == "1"
API_KEY = os.environ.get("CAPTCHAAI_API_KEY", "")

pytestmark = pytest.mark.skipif(
    not (LIVE_ENABLED and API_KEY),
    reason="set DOCTOR_ALLOW_REAL_API=1 and CAPTCHAAI_API_KEY to run live smoke",
)


def test_live_get_balance_returns_a_float() -> None:
    """Confirms the endpoint + API key are wired correctly. Cheapest possible call."""
    with CaptchaAIClient(api_key=API_KEY) as client:
        balance = client.get_balance()
    assert isinstance(balance, float)
    assert balance >= 0.0  # threading-mode accounts may report 0; that's fine
