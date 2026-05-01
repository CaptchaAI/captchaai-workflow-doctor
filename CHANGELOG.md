# Changelog

All notable changes to **captchaai-workflow-doctor** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] — 2026-05-01

### Added

- `NOTICE` file with a soft attribution request asking downstream
  projects to mention `captchaai.com`. Apache-2.0 license unchanged.
- `ROADMAP.md` and `SUPPORT.md` at the repo root.
- `docs/sending-a-support-report.md` walks users through producing a
  redacted report for support tickets.
- `scripts/capture-report-screenshot.py` — a Playwright @2× helper to
  produce report screenshots for docs and the launch article.
- README hero image and a link to the live launch article
  (*Why CAPTCHA Tokens Work in the API but Fail in the Browser*).
- GitHub issue templates (bug, feature, support) + contact-link config.

### Changed

- README status label is now **Beta** (was "stable"); `pyproject.toml`
  classifier is now `Development Status :: 4 - Beta`. Honest given the
  one-minor-release track record and the residential-proxy gap on the
  Cloudflare Challenge live-solve path (tracked in `ROADMAP.md`).
- Phase-internal phrasing in `CHANGELOG.md`, `PROGRESS.md`, and
  `docs/real-e2e-evidence.md` rewritten to neutral scope language so
  the public surface no longer reads as a release post-mortem.
- `pyproject.toml` wheel build now `force-include`s `NOTICE` at
  `captchaai_doctor/NOTICE`; sdist `include` lists `NOTICE`,
  `ROADMAP.md`, and `SUPPORT.md` explicitly.

### Notes

- No runtime behavior changes. Pure trust / packaging / docs release.
  Safe to upgrade from `0.2.0` with no profile or CLI changes.

## [0.2.0] — 2026-05-01

### Added — multi-CAPTCHA-type expansion

- **reCAPTCHA v3** end-to-end (PR #12). New `captcha_type=recaptcha_v3`,
  `submit_recaptcha_v3` (passes `version=v3`, `action`, `min_score`),
  detector heuristic for the `?render=SITEKEY` script-tag shape, mock
  contact form (port 8768), profile, CLI demo, and live-solve coverage
  against the antcpt public test sitekey.
- **Cloudflare Turnstile invisible mode** end-to-end (PR #13). Detector
  reads `data-size="invisible"`; profile + CLI demo + mock variant.
- **Cloudflare Challenge** end-to-end (PR #14). New
  `captcha_type=cloudflare_challenge`, `submit_cloudflare_challenge`
  with the verified `proxy`/`proxytype` parameter contract, new `Proxy`
  schema model (required when `captcha_type=cloudflare_challenge` —
  the `cf_clearance` cookie is bound to the egress IP that solved it),
  new `ApplyClearanceCookieAction` that parses the JSON clearance,
  sets the cookie via `BrowserContext.add_cookies`, replays the
  matching User-Agent via `Page.set_extra_http_headers`, and reloads.
  Detector heuristic for the "Just a moment..." interstitial. Mock app
  (port 8769), profile, CLI demo, sample reports.
- **New root cause** `cloudflare_proxy_misconfigured` for missing
  proxy credential env vars; classifier recommendation included.

### Repo / process

- **CODEOWNERS** + **PR template** (PR #10).
- Ready-to-apply **branch-protection ruleset** under
  `.github/rulesets/protect-main.json` (PR #11). Application is gated
  on the repo flipping public.

### Notes

- Live-solve verification: reCAPTCHA v2, reCAPTCHA v3, and Turnstile
  (managed + invisible) are all confirmed against `ocr.captchaai.com`.
- Cloudflare Challenge ships with the verified submit contract and
  the `cf_clearance` cookie / User-Agent replay path. Full live-solve
  coverage requires a real residential proxy on the worker side
  (Cloudflare binds the clearance cookie to the egress IP that solved
  it); residential-proxy plumbing is on the roadmap and will land in
  a follow-up release. See [`ROADMAP.md`](ROADMAP.md).
- v0.2 supported types: Turnstile (managed + invisible), reCAPTCHA
  v2, reCAPTCHA v3, and Cloudflare Challenge. Additional types may
  be added in future minor releases.

## [0.1.0] — 2026-04-29

Initial public-ready release: walking-skeleton runner for Cloudflare
Turnstile + reCAPTCHA v2 with profile validation, redaction, fake
client for offline demos, mock Flask targets, sample reports, and a
green CI matrix (lint/type/test on 3.11 + 3.12, demo-smoke, and
secrets-scan).

[0.2.0]: https://github.com/CaptchaAI/captchaai-workflow-doctor/releases/tag/v0.2.0
[0.1.0]: https://github.com/CaptchaAI/captchaai-workflow-doctor/releases/tag/v0.1.0
