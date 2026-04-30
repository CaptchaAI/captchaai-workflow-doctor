# Progress

Single source of truth for "what's done vs pending". Updated in the same commit as the work.
Status legend: `[ ]` not started · `[~]` in progress · `[x]` done.

> See `INTERNAL-STRATEGY/captchaai_workflow_doctor_full_plan.md` for the full strategy
> and `/memories/session/plan.md` for the agent execution plan.

---

## Pre-flight (security & repo init)

- [x] Quarantine `creds.txt` → `.secrets/creds.txt`
- [x] `.gitignore` excludes secrets and runtime artifacts
- [x] `.env.example` with placeholder names
- [ ] Initial commit on `main` (skeleton only — no secrets)
- [ ] Push to private `CaptchaAI/captchaai-workflow-doctor`
- [ ] Branch protection on `main` (require PR + CI green, no force-push)
- [ ] Test server: create non-root `doctor` user, install deploy key (host in `.secrets/`)

## Phase 0 — Repo skeleton

- [x] `pyproject.toml` (hatchling, py3.11+, deps locked)
- [x] `ruff.toml`, `mypy.ini`
- [x] Package tree under `captchaai_doctor/` (stubs)
- [x] CLI entry point `captchaai-doctor` with `--help`, `--version`, subcommand stubs
- [x] `tests/` with smoke tests
- [x] `.github/workflows/ci.yml` (lint + type + test + gitleaks)
- [x] `README.md`, `PROGRESS.md`
- [ ] CI green on first push
- [ ] **Checkpoint: user review**

## Phase 1 — Profile system + Pydantic schemas

- [x] `schemas.py` Pydantic v2 models for Profile / Action / Report
- [x] `config.load_profile`, `config.validate_profile`
- [x] `validate-profile` CLI wired to real validator
- [x] `profiles/local-demo-login-turnstile.yaml`
- [x] `profiles/local-demo-form-recaptcha-v2.yaml`
- [x] `profiles/turnstile-generic.yaml`, `profiles/recaptcha-v2-generic.yaml`
- [x] Tests: valid profiles pass; each rule violation fails with actionable message
- [x] Tests: secret-shaped strings in YAML rejected
- [x] `docs/profile-schema.md`
- [ ] **Checkpoint**

## Phase 2 — CaptchaAI client + poller (mocked)

- [x] `captchaai_client` submit + result + balance + report-bad with typed error hierarchy
- [x] `poller.poll_until_ready` with backoff + timeout (deterministic, injectable clock/sleep)
- [x] `redaction.py` + logging filter (api key / captcha id / token)
- [x] Tests for success, NOT_READY→OK, timeout, every documented `ERROR_*`
- [x] Logs greppable for raw secrets → zero matches (asserted by test)
- [x] Live API smoke (Option B) — `tests/test_live_smoke.py` opt-in via `DOCTOR_ALLOW_REAL_API=1`
- [x] `scripts/provision-server.sh` + `scripts/run-real-e2e.sh` skeletons (used in Phase 5)

## Phase 3 — Local Turnstile mock + Playwright runner (walking skeleton)

- [x] `demos/mock_login_turnstile/app.py` (Flask, failure-mode query param)
- [x] `cli demo turnstile` boots Flask subprocess (auto-picks free port; verifies via `/healthz`)
- [x] `browser.launch_browser`, `browser.run_actions` (Playwright sync)
- [x] `cli run --mock-captchaai` produces JSON report + screenshots
- [x] `runner.run_workflow` orchestrates load → navigate → before_solve → submit → poll → after_token → verify
- [x] `report.write_json_report` (HTML deferred to Phase 5)
- [x] `fake_captchaai.FakeCaptchaAIClient` (drop-in replacement, deterministic)
- [x] CI demo-smoke job: full vertical green (`.github/workflows/demo-smoke.yml`)
- [x] Tests: 6 mock-app, 6 fake-client, 3 e2e (real Chromium)

## Phase 4 — Detection, injection, verifier, classifier + reCAPTCHA mock

- [x] `detector.py` (Turnstile + reCAPTCHA v2 + sitekey + callback candidates)
- [x] `injector.py` (token write + callback invoke, dispatches input/change events)
- [x] `verifier.py` (`field_has_value`, `callback_marker_present`)
- [x] `classifier.py` recommendation map (full priority/confidence ladder lands in Phase 5)
- [x] `demos/mock_login_recaptcha/app.py` (mirror of turnstile, modes ok/wrong-token/no-callback)
- [x] `profiles/local-demo-login-recaptcha.yaml`
- [x] CLI `demo recaptcha-v2` command
- [x] Heuristic widget detection used in `sitekey_not_found` reports
- [x] Tests: detector (9), injector+verifier (7), recaptcha mock (7), classifier (3), recaptcha e2e (3)
- [x] All 113 tests green; ruff + mypy --strict clean

## Phase 5 — HTML report + CI mode + real-server E2E

> Test-server connection details live only in `.secrets/` (gitignored).


- [x] `report.write_html_report` (single self-contained HTML, no external assets, XSS-safe)
- [x] `report.write_json_report` validated against published JSON Schema (`report.REPORT_JSON_SCHEMA`, Draft 2020-12)
- [x] `recommendation` field wired into JSON + HTML via `classifier.recommendation_for`
- [x] `captchaai-doctor schema` CLI subcommand exports the JSON Schema
- [x] `--ci`, `--fail-on`, exit codes per plan §10.6 (already wired in Phase 3, tested in Phase 5)
- [x] `--no-html` flag for callers that only want JSON
- [x] `sample-reports/` regenerated from fixtures via `scripts/regenerate_sample_reports.py` (5 samples)
- [x] `scripts/provision-server.sh` (idempotent)
- [x] `scripts/run-real-e2e.sh` gated by `DOCTOR_ALLOW_REAL_API=1` (real-solve tier gated by additional `DOCTOR_ALLOW_REAL_SOLVE=1`)
- [x] First real CaptchaAI solve recorded in `docs/real-e2e-evidence.md` (2026-05-01: real reCAPTCHA token, 36.82s; bug found + fixed)
- [x] `.github/workflows/demo-smoke.yml` (full vertical green; uploads artifacts on failure)
- [x] **Checkpoint**

## Phase 6 — Docs, article, polish, release

- [x] `docs/` filled per plan §7 (overview, responsible-use, failure-taxonomy, token-lifecycle, profile-schema, report-schema, ci-integration, troubleshooting, architecture, real-e2e-evidence)
- [x] README quickstart walkthrough <10 min on fresh VM
- [x] CONTRIBUTING.md
- [x] Flagship article draft → `INTERNAL-STRATEGY/article-draft.md`
- [x] `ruff check`, `mypy --strict`, full `pytest` all green
- [x] All plan §25 acceptance criteria checked
- [x] Tag `v0.1.0`, draft release notes
- [ ] Flip repo public *(USER ACTION)*

---

## Phase 7 — Multi-CAPTCHA support (v0.2)

> **PIVOT note:** hCaptcha was dropped after a live probe of `ocr.captchaai.com/in.php`
> returned `ERROR_SERVER_ERROR` for every method/sitekey combo and the upstream docs
> confirmed it is not on the supported list. Replaced with **Cloudflare Challenge** in 7c.

### 7a — reCAPTCHA v3
- [x] `schemas.CaptchaType` extended with `recaptcha_v3`
- [x] `Detection` model: `action`, `min_score` fields
- [x] `captchaai_client.submit_recaptcha_v3` (method=userrecaptcha + version=v3)
- [x] `detector` rule for `script[src*='recaptcha'][src*='render=']` (extracts sitekey from `?render=`)
- [x] `runner` v3 pipeline branch + `_ProfileMisconfigured` mapping
- [x] New `RootCause` `recaptcha_v3_action_missing` + classifier recommendation
- [x] `demos/mock_form_recaptcha_v3/app.py` (port 8768; modes ok/wrong-token)
- [x] Profiles: `local-demo-form-recaptcha-v3.yaml`, `recaptcha-v3-generic.yaml`
- [x] CLI `demo recaptcha-v3`
- [x] Tests: client / fake / detector / mock app / e2e (3 cases) — green
- [x] **Live solve verified** (antcpt.com pair, real ~80-char token in ~5s) — gated test
- [x] Sample report fixtures (`recaptcha-v3-success`, `recaptcha-v3-action-missing`)
- [x] `report.REPORT_JSON_SCHEMA` enum updated
- [x] `demo-smoke.yml` extended

### 7b — Turnstile invisible
- [x] `detector` rule for `div.cf-turnstile[data-size="invisible"]` (exposed as `DetectedWidget.turnstile_mode`)
- [~] `injector` path via `turnstile.execute(widgetId)` — *deferred: existing `inject_token` + `invoke_callback_if_detected` path already covers invisible mode (the doctor gets the token from CaptchaAI, so it doesn't need to invoke the widget). The mock exposes a `window.turnstile.execute` shim for completeness.*
- [x] `Detection.turnstile_mode` (`managed | non-interactive | invisible`)
- [x] Existing turnstile mock extended with `?widget=invisible` (data-size + execute shim)
- [x] CLI `demo turnstile-invisible` + profile `local-demo-login-turnstile-invisible.yaml`
- [x] Tests: 3 mock-app + 3 detector + 2 e2e — green
- [x] Sample report fixture (`turnstile-invisible-success`)
- [x] `demo-smoke.yml` extended

### 7c — Cloudflare Challenge (replaces hCaptcha)
- [x] Live-probe the exact submit method name on CaptchaAI: confirmed
      `method=cloudflare_challenge` with REQUIRED params
      `pageurl`, `userAgent`, `proxy` (host:port or user:pass@host:port),
      `proxytype` (HTTP/HTTPS/SOCKS4/SOCKS5). Submit accepts; result
      shape is `cf_clearance` cookie + matching User-Agent that must be
      replayed from the same egress IP.
- [x] `schemas`: `captcha_type` literal extended; new `Proxy` model;
      new `ApplyClearanceCookieAction`; cross-field validator forces
      `proxy:` when `captcha_type=cloudflare_challenge`.
- [x] `captchaai_client.submit_cloudflare_challenge` + matching
      `FakeCaptchaAIClient.submit_cloudflare_challenge` +
      `fake_cf_clearance_payload()` helper.
- [x] `runner._submit_for` dispatches CF, resolves proxy creds from env,
      reports new `cloudflare_proxy_misconfigured` root cause when env
      vars are missing.
- [x] `browser._apply_clearance_cookie` parses the JSON token, sets
      `cf_clearance` via `context.add_cookies`, replays the UA via
      `page.set_extra_http_headers`, and reloads the page.
- [x] Detector heuristic for the CF interstitial
      (`script[src*='challenges.cloudflare.com']`, `#cf-challenge-running`,
      etc.); new `cloudflare_challenge` `CaptchaKind`.
- [x] Mock app `demos/mock_cloudflare_challenge` (port 8769) — serves a
      403 interstitial unless cookie + matching UA are presented.
- [x] Profiles: `local-demo-cloudflare-challenge.yaml` +
      `cloudflare-challenge-generic.yaml`.
- [x] CLI: `captchaai-doctor demo cloudflare-challenge`.
- [x] Tests: 5 mock-app + 2 client + 4 e2e + 1 classifier extension — green.
- [x] Sample reports: `cloudflare-challenge-success`,
      `cloudflare-proxy-misconfigured`.
- [x] `demo-smoke.yml` extended.
- [~] Live solve verification: deferred. The CaptchaAI worker requires a
      real residential proxy (the cookie is bound to the egress IP); we
      do not have one allocated to this test account. Method name +
      parameter contract are verified live (submit returns a captcha_id;
      result returns `ERROR_CAPTCHA_UNSOLVABLE` with a fake proxy, which
      is the expected failure mode). Live-solve gate stays off until a
      real proxy is plumbed in.

## Phase 8 — Branch protection on `main`

- [x] `.github/CODEOWNERS` (assigns @bshahin)
- [x] `.github/PULL_REQUEST_TEMPLATE.md` (verification checklist)
- [x] Ready-to-apply ruleset: `.github/rulesets/protect-main.json` (+ README)
- [ ] Apply ruleset *(blocked: GitHub free private repos cannot enable branch protection or rulesets — apply right after the user flips the repo public)*
- [ ] Verify `git push --dry-run --force origin main` is rejected (post-public)

## Release v0.2.0

- [ ] Tag `v0.2.0`
- [ ] GitHub release notes (reCAPTCHA v3 + Turnstile invisible + Cloudflare Challenge + branch protection scaffolding)
