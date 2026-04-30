# Overview

CaptchaAI Workflow Doctor is a runnable diagnostic for CAPTCHA-solving
integrations. You give it a *profile* (a YAML file describing one
authorized workflow) and a CaptchaAI API key. It runs the workflow end
to end against a real Chromium browser and emits a structured report
saying exactly where the workflow broke — with a one-line recommended
fix.

## Why this exists

Every team that integrates a CAPTCHA solver eventually hits the same
shape of bug:

> "CaptchaAI gave me a token, but my page still rejects the CAPTCHA."

The token is rarely the problem. The actual failure is almost always
one of:

- wrong sitekey or wrong page URL
- token written into the wrong field
- callback not invoked
- token expired before form submit
- server-side `siteverify` mismatch
- session / proxy / origin mismatch

Without a tool, debugging this requires staring at network traces and
guessing. With doctor, you run one command and get a screenshot, an
action timeline, and a labeled root cause.

## Status

- **Phase 5 complete**: HTML + JSON reports, JSON Schema, real-solve
  evidence, CI mode.
- **Phase 6 in progress**: docs, polish, v0.1.0 release.

## Where to start

1. [Quickstart](../README.md#quickstart) — clone, install, run a demo.
2. [Profile schema](profile-schema.md) — write your own profile.
3. [Failure taxonomy](failure-taxonomy.md) — the 12 root-cause classes.
4. [Token lifecycle](token-lifecycle.md) — the four constraints every
   integration must satisfy.
5. [CI integration](ci-integration.md) — how to wire doctor into your
   pipeline.
6. [Architecture](architecture.md) — module layout and request flow.
7. [Troubleshooting](troubleshooting.md) — common gotchas.
8. [Responsible use](responsible-use.md) — what doctor is and isn't for.

## Reports

Every run produces:

- `report.json` — strict JSON conforming to the published Draft 2020-12
  [report schema](../sample-reports/) (export with
  `captchaai-doctor schema`).
- `report.html` — single self-contained file (no remote assets) with
  badge, summary, recommendation, action timeline, and embedded
  screenshots.
- Screenshots and a Playwright trace per workflow step.

See `sample-reports/` in the repo root for examples of every failure
mode.
