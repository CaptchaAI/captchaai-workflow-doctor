# Changelog

All notable changes to **captchaai-workflow-doctor** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
  (managed + invisible) all confirmed against `ocr.captchaai.com`.
  Cloudflare Challenge is partially verified — the method name +
  parameter contract are accepted live, but a full solve requires a
  real residential proxy (Cloudflare binds the cookie to the worker's
  egress IP); deferred until a proxy is plumbed in.
- hCaptcha was probed and **not** offered by CaptchaAI; the slot was
  taken by Cloudflare Challenge.

## [0.1.0] — 2026-04-29

Initial public-ready release: walking-skeleton runner for Cloudflare
Turnstile + reCAPTCHA v2 with profile validation, redaction, fake
client for offline demos, mock Flask targets, sample reports, and a
green CI matrix (lint/type/test on 3.11 + 3.12, demo-smoke, and
secrets-scan).

[0.2.0]: https://github.com/CaptchaAI/captchaai-workflow-doctor/releases/tag/v0.2.0
[0.1.0]: https://github.com/CaptchaAI/captchaai-workflow-doctor/releases/tag/v0.1.0
