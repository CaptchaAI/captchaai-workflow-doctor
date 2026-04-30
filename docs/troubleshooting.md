# Troubleshooting

If the doctor itself misbehaves, here are the most common gotchas.

## "sitekey_not_found" but I can see the widget

The configured `detection.sitekey_selector` didn't match. Two common
causes:

1. The widget renders inside an iframe. Doctor only looks at the top
   frame by default. Use the iframe's source URL as a separate profile,
   or wait for the widget to be hoisted into the main DOM.
2. The widget loads after `domcontentloaded`. Add a `wait` action with
   a selector that's only present when the widget is ready.

The error detail will tell you if a *different* widget kind was
detected on the page (e.g. the profile says Turnstile but reCAPTCHA was
present). Update `detection.sitekey_selector` accordingly.

## "callback_not_invoked"

The site uses a callback name we don't have in
`detection.callback_candidates`. Open the page, search the JS source
for `data-callback=` and `'callback':`, and add the name to the
candidate list.

## Token is delivered but verification still fails

See [`token-lifecycle.md`](token-lifecycle.md). The four typical
culprits are: wrong page URL, stale token (>2min), token missing from
the form submission, server-side `siteverify` mismatch.

## Real-solve test costs / behavior

`tests/test_live_solve.py` is double-gated and uses Google's documented
test sitekey, which is not billed by CaptchaAI. To test against your
own paid sitekey, set the env vars and update the test locally — be
aware each solve consumes balance.

## Logs include `***REDACTED***` everywhere

Working as intended. The `redaction` filter is installed on the root
logger. If you need to inspect raw values during local development,
disable it temporarily:

```python
import logging
from captchaai_doctor.redaction import RedactingFilter

for h in logging.getLogger().handlers:
    h.filters = [f for f in h.filters if not isinstance(f, RedactingFilter)]
```

Never disable redaction in CI.

## Playwright can't find a browser

```
playwright._impl._errors.Error: Executable doesn't exist at .../chromium-...
```

Run:

```bash
python -m playwright install chromium
```

CI does this automatically in `demo-smoke.yml`.

## Demo command picks a busy port

`captchaai-doctor demo` auto-picks a free port and verifies it owns the
running Flask app via `/healthz` before driving it. If you see
`PortOwnershipError`, another process (a previous Flask, a port-conflicting
service) responded on `/healthz` with content we don't recognize. Kill
the squatter or pick a different `--port`.

## CI mypy fails on a brand-new dep

`mypy.ini` strict-checks `captchaai_doctor/`. Add stubs (`types-foo`)
to `pyproject.toml [project.optional-dependencies] dev` rather than
relaxing strictness.
