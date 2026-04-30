# CaptchaAI Workflow Doctor

> Status: **pre-alpha** — under active development. Do not use yet.

A diagnostic tool for debugging CAPTCHA-solving workflows from CaptchaAI API request to browser acceptance.

## What it solves

When a CAPTCHA solver returns a token but the page still rejects the workflow, the failure can be in many places: wrong sitekey, wrong page URL, token injected into the wrong field, callback not triggered, token expired, session mismatch, and more. CaptchaAI Workflow Doctor runs the full workflow against an authorized profile and tells you *exactly* where it broke.

## Responsible Use

CaptchaAI Workflow Doctor is designed for developers testing CAPTCHA-solving integrations in systems they own, operate, or are authorized to test.

Do not use this project for unauthorized access, spam, credential attacks, account farming, or activity that violates a website's terms or applicable law.

## Quickstart

> Phase 0 ships only the CLI skeleton. Real workflow runs land in Phase 3.

```bash
git clone https://github.com/CaptchaAI/captchaai-workflow-doctor.git
cd captchaai-workflow-doctor
python -m venv .venv
. .venv/bin/activate          # on Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
captchaai-doctor --help
```

## Project status

See [PROGRESS.md](PROGRESS.md) for a per-phase checklist of what's done and what's pending.

## License

Apache-2.0 — see [LICENSE](LICENSE).
