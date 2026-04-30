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


## reCAPTCHA v3 — live solve verified (Phase 7a)

- Date: 2026-04-30
- Test pair: `sitekey=6LcR_okUAAAAAPYrPe-HK_0RULO1aZM15ENyM-Mf` on `https://antcpt.com/score_detector/`, `action=homepage`, `min_score=0.3`
- Endpoint: `https://ocr.captchaai.com/in.php` with `method=userrecaptcha&version=v3&action=homepage&min_score=0.3`
- Result: real ~80-character token returned in ~5s
- Test: `pytest tests/test_live_solve.py::test_real_recaptcha_v3_solve_returns_a_real_token`
- Status: PASSED (gated on `DOCTOR_ALLOW_REAL_API=1` + `DOCTOR_ALLOW_REAL_SOLVE=1`)

## hCaptcha — NOT supported by CaptchaAI (decision record)

- Probed `https://ocr.captchaai.com/in.php` with `method=hcaptcha` against multiple sitekey/pageurl combos; every response was `{"status":0,"request":"ERROR_SERVER_ERROR"}`.
- Cross-checked with docs.captchaai.com supported list: hCaptcha is absent (Normal Captcha, BLS, reCAPTCHA v2/v3, Turnstile, Cloudflare Challenge, Geetest V3 are listed).
- Decision: dropped hCaptcha from the v0.2 scope; replaced with **Cloudflare Challenge** in Phase 7c.
