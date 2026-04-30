# Real CaptchaAI E2E evidence

This file records each successful real-API run on the test server. It is
appended-to (never overwritten) so we have a permanent audit trail that
the endpoint and API key are working.

Format: ISO timestamp · phase · operation · result.

| When (UTC) | Phase | Operation | Result |
|---|---|---|---|
| 2026-04-29 | Phase 2 | `pytest tests/test_live_smoke.py` (`get_balance`) | PASSED — endpoint + API key confirmed, balance returned as float |
| 2026-05-01 | Phase 5 | `pytest tests/test_live_solve.py` (real reCAPTCHA v2 solve via `submit_recaptcha_v2` + `poll_until_ready`) | PASSED in 36.82s — real opaque token (>100 chars) returned for sitekey `6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI` on `https://www.google.com/recaptcha/api2/demo`. Balance unchanged ($10.00 before/after) — Google's documented test pair is not billed. **Found and fixed a real bug**: production CaptchaAI returns `request` as an integer for `userrecaptcha`; `_submit` now coerces int→str (regression test `test_submit_accepts_integer_captcha_id`). |

## How to add new evidence

Run the live-solve test on the test server (or your dev box) with both
gates enabled:

```bash
DOCTOR_ALLOW_REAL_API=1 \
DOCTOR_ALLOW_REAL_SOLVE=1 \
CAPTCHAAI_API_KEY=... \
pytest tests/test_live_solve.py -v
```

Then append a row above with the result. **Do NOT** ever paste the API
key, captcha id, or full token into this file — only the test summary.
