# Roadmap

What's next for **CaptchaAI Workflow Doctor**. Items move from
*Considering* → *On deck* → *Recently shipped* as they land. Dates
are not promised — this is a public direction document, not a
contract.

For the per-release detail see [CHANGELOG.md](CHANGELOG.md).

---

## Recently shipped

- **`v0.2.1`** — Trust/packaging polish: NOTICE attribution,
  ROADMAP/SUPPORT docs, GitHub issue templates, README hero image,
  live launch article link, Phase 10–15 epic issues.
- **`v0.2.0`** — Multi-CAPTCHA support: Cloudflare Turnstile (managed
  + invisible), reCAPTCHA v2, reCAPTCHA v3, and Cloudflare Challenge.
  Sample reports, demos, and live-solve coverage for the
  Turnstile/reCAPTCHA paths.
- **`v0.1.0`** — Walking-skeleton runner for Turnstile + reCAPTCHA v2:
  profile validation, redaction, fake client for offline demos,
  Flask mock targets, JSON + HTML reports, CI mode.

## On deck

- **Cloudflare Challenge live-solve coverage** ([#21](https://github.com/CaptchaAI/captchaai-workflow-doctor/issues/21))
  — wire residential proxy support so the existing CF Challenge
  code path can be end-to-end live-tested. Cloudflare binds the
  `cf_clearance` cookie to the egress IP, so this needs a stable
  residential proxy on the worker side; the doctor side is already
  wired (`Proxy` schema + `ApplyClearanceCookieAction`).
- **Failure taxonomy expansion** ([#22](https://github.com/CaptchaAI/captchaai-workflow-doctor/issues/22))
  — surface 7 additional `root_cause` classes (`pageurl_mismatch`,
  `wrong_frame`, `submitted_before_injection`,
  `iframe_blocked`, `widget_loaded_but_no_sitekey`,
  `multi_widget_ambiguity`, `success_then_revert`) with detection
  hooks, sample reports, and recommendation strings.
- **Profile cookbook + scaffolder** ([#23](https://github.com/CaptchaAI/captchaai-workflow-doctor/issues/23))
  — `cookbook/` of curated anonymized profiles plus
  `doctor scaffold --from cookbook:<id>` and an interactive
  `doctor init` wizard.
- **Report intelligence** ([#24](https://github.com/CaptchaAI/captchaai-workflow-doctor/issues/24))
  — `report.diff`, `report.aggregate`, interactive HTML timeline,
  Slack/webhook output, Prometheus exporter.
- **Headed-mode trace viewer helper** — a small CLI command to open
  the most recent run's Playwright trace without remembering the
  Playwright trace-viewer invocation.

## Considering

- **Node SDK parity** ([#25](https://github.com/CaptchaAI/captchaai-workflow-doctor/issues/25))
  — a TypeScript package mirroring the Python CLI / runner / report
  contract. Only after Python adoption is firmly established and the
  schema is stable.
- **Headed observability + VS Code extension** ([#26](https://github.com/CaptchaAI/captchaai-workflow-doctor/issues/26))
  — `--pause-on-failure`, live TUI, profile YAML language server.
- **Additional widget heuristics** — broader coverage of the long
  tail of CAPTCHA widget shapes seen in the wild (custom
  integrations, SPA-loaded widgets, shadow-DOM hosted widgets).
- **Hosted demo** — a public sandbox where users can paste a profile
  and see the report shape without installing locally.
- **`report_bad` workflow integration** — let the doctor distinguish
  a likely solver-side issue from a likely integration-side issue
  and (with an explicit flag) call CaptchaAI's `reportbad` endpoint.

---

## Want something on this list?

Open an issue with the **feature_request** template. The more
specific the integration scenario, the easier it is to scope.
