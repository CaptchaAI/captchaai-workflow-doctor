# Architecture

CaptchaAI Workflow Doctor is a single-process Python CLI. Each invocation
runs a workflow defined by a YAML *profile*, drives a real Chromium
browser via Playwright, talks to the CaptchaAI API for the actual solve,
and emits machine- and human-readable reports.

```text
┌────────────┐   load    ┌──────────────┐    submit/poll    ┌──────────────┐
│  Profile   │─────────▶ │ run_workflow │ ────────────────▶ │ CaptchaAI API│
│ (YAML)     │           │              │ ◀──────────────── │              │
└────────────┘           └──────┬───────┘   token / errors  └──────────────┘
                                │
                       open + drive (Playwright)
                                ▼
                        ┌──────────────┐
                        │   Browser    │
                        │  (Chromium)  │
                        └──────┬───────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
        screenshots                    inject token + invoke
        + trace                        callback + verify
                               │
                               ▼
                       ┌──────────────┐
                       │  RunResult   │
                       └──────┬───────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ JSON + HTML      │
                    │ report           │
                    └──────────────────┘
```

## Modules

| Module | Responsibility |
|---|---|
| `captchaai_doctor.schemas` | Pydantic v2 models for `Profile`, `Action`, `RunResult`. Strict, frozen. |
| `captchaai_doctor.config` | `load_profile(path)` → validated `Profile`. |
| `captchaai_doctor.captchaai_client` | Synchronous `httpx` client for the 2captcha-compatible API. Typed error hierarchy (`CaptchaAITransportError`, `CaptchaAIAuthError`, `CaptchaAIBalanceError`, `CaptchaAIPageError`, `CaptchaAIUnsolvableError`, `CaptchaAINotReadyError`). |
| `captchaai_doctor.poller` | `poll_until_ready` with deterministic backoff + injectable clock/sleep for tests. |
| `captchaai_doctor.fake_captchaai` | Drop-in fake client for offline runs (`--mock-captchaai`). |
| `captchaai_doctor.browser` | `launch_browser` + `run_actions` (fill/click/wait/inject/invoke). |
| `captchaai_doctor.detector` | Sitekey reader + heuristic widget detection (Turnstile / reCAPTCHA v2). Discovers callback names. |
| `captchaai_doctor.injector` | Writes the token into the response field (bypasses the hidden attribute) and dispatches `input` + `change` events; invokes the JS callback. |
| `captchaai_doctor.verifier` | Post-injection checks: field has expected value; callback marker present. |
| `captchaai_doctor.classifier` | Maps a `RootCause` to a one-line recommendation. |
| `captchaai_doctor.runner` | Orchestrates the full pipeline; produces a `RunResult`. |
| `captchaai_doctor.report` | `write_json_report`, `write_html_report`, `REPORT_JSON_SCHEMA`, `write_schema`. |
| `captchaai_doctor.redaction` | Logging filter that scrubs API keys, captcha IDs, and tokens. Installed globally by the CLI. |
| `captchaai_doctor.cli` | `click` entry point. Subcommands: `run`, `validate-profile`, `schema`, `demo turnstile`, `demo recaptcha-v2`. |

## Pipeline (per `run_workflow`)

1. **Load** the profile.
2. **Launch** Chromium (headless by default; `--headed` for debugging).
3. **Navigate** to `target.url`.
4. **before_solve** action steps (fill credentials, etc.).
5. **Read sitekey** at `detection.sitekey_selector`. If missing, run
   `detect_widget` to suggest the right selector and stop.
6. **Submit** to CaptchaAI (`submit_turnstile` or `submit_recaptcha_v2`).
7. **Poll** with bounded backoff until token / unsolvable / timeout.
8. **Inject** the token into `detection.response_field_selector`.
9. **Invoke callback** (one of `detection.callback_candidates`) if defined.
10. **after_token** action steps (e.g., click submit).
11. **Verify** success via `verification.success_selector` /
    `verification.failure_text`.
12. **Classify** the outcome to a single `RootCause`.
13. **Write** `report.json` + `report.html` + screenshots.

## Failure taxonomy

The classifier reports exactly one `root_cause` per run, drawn from a
fixed enum. See [`failure-taxonomy.md`](failure-taxonomy.md) for the
full list and what each means.

## Reproducibility & tests

- Pure functions take an injectable clock + sleep so the poller can
  be exhaustively unit-tested.
- The fake CaptchaAI client mirrors the real client's contract,
  enabling fully offline e2e via `--mock-captchaai`.
- Real-API tests are gated behind `DOCTOR_ALLOW_REAL_API=1`
  (cheap: `get_balance` only) and `DOCTOR_ALLOW_REAL_SOLVE=1`
  (consumes balance).
