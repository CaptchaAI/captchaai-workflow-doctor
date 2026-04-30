# Real CaptchaAI E2E evidence

This file records each successful real-API run on the test server. It is
appended-to (never overwritten) so we have a permanent audit trail that
the endpoint and API key are working.

Format: ISO timestamp · phase · operation · result.

| When (UTC) | Phase | Operation | Result |
|---|---|---|---|
| (auto-generated below) |  |  |  |
| (first row) | Phase 2 | `pytest tests/test_live_smoke.py` (`get_balance`) | PASSED — endpoint + API key confirmed working from dev workstation |

To add an entry, run `scripts/run-real-e2e.sh` on the test server with
`DOCTOR_ALLOW_REAL_API=1`, then append a row above with the test output.
