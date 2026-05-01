# Sending a support report

When something doesn't work, the fastest way to get help is to attach
the `report.json` produced by the failing run. This page is the
checklist for doing that safely.

## 1. Run the doctor against your profile

```bash
captchaai-doctor run \
  --profile profiles/my-flow.yaml \
  --artifact-dir run-artifacts/ \
  --ci --fail-on workflow
```

This produces:

- `run-artifacts/report.json` — structured root-cause + timeline
- `run-artifacts/report.html` — same data, human-readable
- `run-artifacts/screenshots/` — per-step screenshots
- `run-artifacts/trace.zip` — Playwright trace (if enabled)

## 2. Redact

The doctor redacts API keys, captcha ids, and tokens by default. Do
a final pass before you share anything:

```bash
grep -E "(api[_-]?key|token|captcha[_-]?id)" run-artifacts/report.json
```

Any matches should already be `****`-redacted. If you find a real
secret, delete the report file, upgrade
(`pip install -U captchaai-workflow-doctor`), and re-run.

If you're attaching the trace too, open it locally first
(`playwright show-trace run-artifacts/trace.zip`) and confirm no
sensitive page state leaks into screenshots.

## 3. Attach

### For doctor bugs / usage questions

Open a GitHub issue using the
[Bug report](https://github.com/CaptchaAI/captchaai-workflow-doctor/issues/new?template=bug_report.yml)
or
[Support question](https://github.com/CaptchaAI/captchaai-workflow-doctor/issues/new?template=support_question.yml)
template and attach `report.json` (and the redacted profile YAML if
relevant).

### For CaptchaAI account / billing / API-key issues

Email `support@captchaai.com` with the redacted `report.json`
attached. The labeled `root_cause` and timeline let support skip the
"is it the solver or the integration?" diagnosis step entirely.

## What support sees

A redacted report looks like this:

```json
{
  "schema_version": "1.0",
  "status": "failure",
  "root_cause": "callback_not_invoked",
  "captcha": { "type": "turnstile", "sitekey_redacted": "0x4AAAA****" },
  "captchaai": { "captcha_id_redacted": "7382****", "solve_time_ms": 18200 },
  "browser": {
    "token_field_found": true,
    "token_injected": true,
    "callback_detected": true,
    "callback_invoked": false,
    "failure_text": "captcha verification failed"
  },
  "recommendation": "Inspect the page for the Turnstile callback…"
}
```

That's everything support needs and nothing they don't.
