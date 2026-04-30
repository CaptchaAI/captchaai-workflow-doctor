# Failure taxonomy

Every run produces exactly one `root_cause`. The classifier picks the
*most actionable* cause when multiple signals overlap (e.g. an auth
error short-circuits all subsequent stages).

| `root_cause` | When it fires | Likely fix |
|---|---|---|
| `ok` | Verification matched the success selector / no failure text observed. | — |
| `captchaai_unreachable` | Network/DNS/TLS error talking to CaptchaAI (`CaptchaAITransportError`). | Check egress, proxy, firewall, status page. |
| `captchaai_auth` | API rejected the key (`ERROR_WRONG_USER_KEY`, `ERROR_KEY_DOES_NOT_EXIST`). | Rotate / re-issue the key. |
| `captchaai_balance` | API reports out of balance / no slot (`ERROR_ZERO_BALANCE`, `ERROR_NO_SLOT_AVAILABLE`). | Top up; or use threading mode. |
| `captchaai_unsolvable` | Workers tried and gave up (`ERROR_CAPTCHA_UNSOLVABLE`). | Verify sitekey + page URL pair; retry; check that the widget actually loads. |
| `captchaai_page_rejected` | API rejected the submission (`ERROR_PAGEURL`, `ERROR_GOOGLEKEY`, `ERROR_BAD_TOKEN_OR_PAGEURL`, `ERROR_DOMAIN_NOT_ALLOWED`). | Use the canonical page URL the widget loads on; confirm the sitekey matches the live HTML. |
| `poll_timeout` | Polling exceeded `solving.poll_timeout_seconds`. | Raise the timeout, or the solver is overloaded. |
| `sitekey_not_found` | The configured `detection.sitekey_selector` didn't match anything. The detector adds a hint if it spotted a different widget on the page. | Update the selector; the widget may have moved or be inside an iframe. |
| `browser_action_failed` | A `before_solve` or `after_token` action errored (selector miss, timeout, navigation crash). | Inspect the screenshots + action timeline in the HTML report. |
| `callback_not_invoked` | None of `detection.callback_candidates` were defined on the page when we tried to invoke them. | Check the actual JS — the callback name may have been renamed/minified, or the widget loaded async. |
| `verification_failed` | Form submitted but the page showed the failure text / didn't show the success selector. | Wrong success/failure pattern in the profile, or the token was rejected by the server. |
| `unknown` | Catch-all (defensive). | Look at the report's `detail` field; file an issue with the screenshots. |

## How the classifier prioritizes

In rough order, from most-fundamental to most-derived:

1. CaptchaAI errors (auth → balance → unreachable → page → unsolvable → timeout).
2. Detection errors (sitekey not found).
3. Browser action errors (any action raised).
4. Injection / callback errors.
5. Verification (success selector / failure text).

This means a `captchaai_balance` failure will *not* be downgraded to
`verification_failed` even if the form happens to render an error banner.

## Recommendation field

Each `root_cause` maps to a one-line recommendation in
`captchaai_doctor.classifier.RECOMMENDATIONS`. The recommendation is
included verbatim in the JSON report (`recommendation` field) and
rendered prominently in the HTML report.
