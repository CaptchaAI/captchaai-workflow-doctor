# Responsible use

CaptchaAI Workflow Doctor is a debugging tool for CAPTCHA-solving
integrations on systems you own, operate, or are explicitly authorized
to test.

## What this is for

- Verifying your own staging / QA / production CAPTCHA flow works end
  to end.
- Diagnosing why a token returned by CaptchaAI is being rejected by
  *your* page or *your* server.
- Reproducing CAPTCHA integration bugs in CI.
- Building re-usable per-client diagnostic profiles (agency / integrator
  use case).

## What this is NOT for

- Bypassing CAPTCHAs on third-party sites without authorization.
- Credential-stuffing, scraping, ticket-buying, account-creation farms,
  or any activity that violates a site's terms of service or
  applicable law.
- "Beating" Cloudflare, Google, hCaptcha, or any other vendor — doctor
  drives the *legitimate* solver flow, not an evasion path.

## Profile-based design enforces this

The public repo ships:

- Local mock demos (`demos/mock_login_turnstile`,
  `demos/mock_login_recaptcha`).
- *Generic* profiles describing the shape of common widgets, not a
  specific third-party site.

Site-specific profiles are intentionally *not* shipped. If you need
one, you author it privately for a system you own or are authorized to
test.

## Things doctor will not do

- Doctor will not fetch or operate on a profile that points at a
  domain you didn't explicitly load — the profile path is required and
  must be on disk.
- Doctor never logs the API key, captcha ID, or solved token in
  plaintext (see `redaction.py`).
- The real-solve test (`test_live_solve.py`) is double-gated and uses
  Google's documented test sitekey by default.

## If you use this in a way the project author wouldn't approve of

That's on you. The license (Apache-2.0) doesn't excuse abuse and
neither do we.
