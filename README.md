# CaptchaAI Workflow Doctor

> Status: **Beta** — `v0.2.0` released (multi-CAPTCHA: Turnstile, reCAPTCHA v2/v3, Cloudflare Challenge). See [CHANGELOG.md](CHANGELOG.md), [ROADMAP.md](ROADMAP.md), and [PROGRESS.md](PROGRESS.md).

A diagnostic CLI for debugging CAPTCHA-solving workflows from CaptchaAI
API request to browser acceptance. Run one command, get a labeled
root cause and a one-line fix.

```text
$ captchaai-doctor run --profile profiles/checkout.yaml --ci --fail-on workflow
status=failure root_cause=callback_not_invoked duration=4.71s report=run-artifacts/report.json html=run-artifacts/report.html
```

## What it does

When the solver returns a token but your page still rejects the
workflow, doctor walks the full pipeline against a real Chromium
browser — submit → poll → inject → invoke callback → submit → verify —
and tells you *exactly* where it broke. See
[docs/failure-taxonomy.md](docs/failure-taxonomy.md) for the 12
possible root causes.

Every run produces:

- `report.json` (validates against [the published JSON Schema](docs/report-schema.md))
- `report.html` (single self-contained file with screenshots)
- a Playwright trace and per-step screenshots

## Responsible use

Doctor is for systems you own, operate, or are explicitly authorized to
test. It is not for bypassing third-party CAPTCHAs. See
[docs/responsible-use.md](docs/responsible-use.md).

## Quickstart (10 minutes from a fresh checkout)

```bash
git clone https://github.com/CaptchaAI/captchaai-workflow-doctor.git
cd captchaai-workflow-doctor
python -m venv .venv
. .venv/bin/activate                    # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m playwright install chromium
captchaai-doctor --help
```

### Run the bundled demos (no API key required)

```bash
captchaai-doctor demo turnstile
captchaai-doctor demo turnstile-invisible
captchaai-doctor demo recaptcha-v2
captchaai-doctor demo recaptcha-v3
captchaai-doctor demo cloudflare-challenge
```

Each spins up a local Flask app, drives it through the full pipeline
with the fake CaptchaAI client, and writes
`run-artifacts/demo-*/report.{json,html}`.

### Run against your own profile + the real CaptchaAI API

```bash
export CAPTCHAAI_API_KEY=...   # see .env.example
captchaai-doctor run \
  --profile profiles/turnstile-generic.yaml \
  --artifact-dir run-artifacts/ \
  --ci --fail-on workflow
```

## Documentation

- [Overview](docs/overview.md)
- [Profile schema](docs/profile-schema.md) — write your own profile
- [Failure taxonomy](docs/failure-taxonomy.md) — what each `root_cause` means
- [Token lifecycle](docs/token-lifecycle.md) — the four constraints
- [Report schema](docs/report-schema.md) — JSON shape + how to validate
- [CI integration](docs/ci-integration.md) — wiring into your pipeline
- [Architecture](docs/architecture.md) — module map
- [Troubleshooting](docs/troubleshooting.md) — common gotchas
- [Real-API evidence log](docs/real-e2e-evidence.md)

## Supported CAPTCHA types

| Type                  | Submit method (CaptchaAI)            | Demo command                                  |
| --------------------- | ------------------------------------ | --------------------------------------------- |
| Cloudflare Turnstile  | `turnstile`                          | `demo turnstile` / `demo turnstile-invisible` |
| reCAPTCHA v2          | `userrecaptcha`                      | `demo recaptcha-v2`                           |
| reCAPTCHA v3          | `userrecaptcha` (v3, action+score)   | `demo recaptcha-v3`                           |
| Cloudflare Challenge  | `cloudflare_challenge` (proxy req'd) | `demo cloudflare-challenge`                   |

See [docs/profile-schema.md](docs/profile-schema.md) for the per-type
profile fields. Cloudflare Challenge requires a `proxy:` block because
the `cf_clearance` cookie is bound to the egress IP that solved it.

## CLI

```text
captchaai-doctor run                       # run a profile end-to-end
captchaai-doctor demo turnstile            # bundled Turnstile mock + driver
captchaai-doctor demo turnstile-invisible
captchaai-doctor demo recaptcha-v2
captchaai-doctor demo recaptcha-v3
captchaai-doctor demo cloudflare-challenge
captchaai-doctor validate-profile <path>
captchaai-doctor schema [--output path]
```

Exit codes follow [docs/ci-integration.md](docs/ci-integration.md):
`0` ok · `1` workflow failure (with `--fail-on`) · `2` profile/usage error.

## Sample reports

`sample-reports/` contains ten fixtures rendered by
`scripts/regenerate_sample_reports.py`:

- `success` — happy path (Turnstile)
- `verification-failed`
- `callback-not-invoked`
- `sitekey-not-found`
- `captchaai-balance`
- `turnstile-invisible-success`
- `recaptcha-v3-success`
- `recaptcha-v3-action-missing`
- `cloudflare-challenge-success`
- `cloudflare-proxy-misconfigured`

Open any `.html` to see what doctor produces in the wild.

## Status & contributing

See [PROGRESS.md](PROGRESS.md) for the per-phase checklist,
[ROADMAP.md](ROADMAP.md) for what's on deck, and
[CONTRIBUTING.md](CONTRIBUTING.md) for the dev workflow.

## Support

- [SUPPORT.md](SUPPORT.md) — how to ask questions and report bugs.
- [docs/sending-a-support-report.md](docs/sending-a-support-report.md)
  — the redact-and-attach checklist for sending a `report.json`.
- Account / billing / API-key questions go to
  **`support@captchaai.com`** (not this repo).

## Known limitations

- **Cloudflare Challenge needs a residential proxy.** Cloudflare
  binds the `cf_clearance` cookie to the egress IP that solved it,
  so the doctor's CF Challenge profile requires a `proxy:` block.
- **Headed mode (`--headed`) needs a local display.** On headless
  CI runners, run without `--headed` and use the trace viewer for
  step-through debugging.
- **CAPTCHA tokens expire in ~120 seconds.** Workflows that pause
  at a debugger or batch tokens for later submission will see
  `token_expired_before_submit`. See
  [docs/token-lifecycle.md](docs/token-lifecycle.md).

## License

- Source: **Apache-2.0** — see [LICENSE](LICENSE).
- Attribution: see [NOTICE](NOTICE). Projects derived from or
  substantially built on this repo are kindly asked to mention
  **`captchaai.com`** in their README. (This is a request, not an
  additional license condition.)
