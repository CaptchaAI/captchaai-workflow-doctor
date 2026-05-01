# Roadmap

What's next for **CaptchaAI Workflow Doctor**. Items move from
*Considering* → *On deck* → *Recently shipped* as they land. Dates
are not promised — this is a public direction document, not a
contract.

For the per-release detail see [CHANGELOG.md](CHANGELOG.md).

---

## Recently shipped

- **`v0.2.0`** — Multi-CAPTCHA support: Cloudflare Turnstile (managed
  + invisible), reCAPTCHA v2, reCAPTCHA v3, and Cloudflare Challenge.
  Sample reports, demos, and live-solve coverage for the
  Turnstile/reCAPTCHA paths.
- **`v0.1.0`** — Walking-skeleton runner for Turnstile + reCAPTCHA v2:
  profile validation, redaction, fake client for offline demos,
  Flask mock targets, JSON + HTML reports, CI mode.

## On deck

- **Cloudflare Challenge live-solve coverage** — wire residential
  proxy support so the existing CF Challenge code path can be
  end-to-end live-tested. Cloudflare binds the `cf_clearance` cookie
  to the egress IP, so this needs a stable residential proxy on the
  worker side; the doctor side is already wired (`Proxy` schema +
  `ApplyClearanceCookieAction`).
- **Profile cookbook** (`docs/cookbook/`) — a small set of worked,
  anonymized real-world profiles (login, checkout, contact form,
  multi-step) showing how to translate a real workflow into YAML.
- **Headed-mode trace viewer helper** — a small CLI command to open
  the most recent run's Playwright trace without remembering the
  Playwright trace-viewer invocation.
- **Expanded sample reports** — one per root cause in
  `docs/failure-taxonomy.md`, so you can see what each failure looks
  like before you hit it.

## Considering

- **Node SDK parity** — a TypeScript package mirroring the Python
  CLI / runner / report contract. Only after Python adoption is
  firmly established and the schema is stable.
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
