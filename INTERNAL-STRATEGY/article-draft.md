# Why your CaptchaAI token works in curl but your page rejects it

*Draft — `INTERNAL-STRATEGY/article-draft.md`. Author: TBD. Audience:
automation developers, scraping engineers, agency integrators
integrating the CaptchaAI API for the first time.*

---

You wired up your first integration. The HTTP call to CaptchaAI returns
a `200`, the JSON has a `request` field, you forward that token to your
form, and… the page still says "please complete the captcha." You try
again. Same thing. You suspect the solver. You're almost certainly
wrong.

In our integration support inbox, **>80% of "the solver doesn't work"
tickets are not about the solver**. They're about one of four things
the integration is doing wrong with a token that *is* in fact valid.
This article walks through each of them, then gives you a runnable tool
that diagnoses the failure for you in 5 seconds.

## The four constraints every CAPTCHA token has to satisfy

### 1. The (sitekey, page URL) pair must match exactly

When you submit to CaptchaAI you tell it two things: the public
`sitekey` and the `pageurl`. The token the solver computes is *only*
valid when redeemed against that exact pair, because Cloudflare /
Google's `siteverify` will recompute and check both.

The most common bug: passing `https://example.com/` when the widget
actually lives on `https://example.com/login`. The solver returns a
token, but Cloudflare's verification checks the page URL the token was
issued for, sees it doesn't match the page that submitted the form,
and fails the request.

**Fix**: pass the canonical page URL the widget *actually loads on*,
not the homepage and not a redirect target.

### 2. Tokens expire in ~120 seconds

Both Turnstile and reCAPTCHA tokens are single-use and short-lived. If
your code:

- queues tokens for batch submission
- pauses at a debugger
- retries the form after a long wait
- does any other thing that lets >2 minutes elapse between
  `submit_*` and the form POST

…you'll get a "valid-looking" token that fails verification because
the issuer's server has already invalidated it.

**Fix**: measure end-to-end latency. Doctor's report includes
`duration_seconds` for exactly this reason.

### 3. The token must be present in the right field at submit time

Both widgets inject a hidden response field next to themselves:

| Widget | Field |
|---|---|
| Cloudflare Turnstile | `cf-turnstile-response` |
| Google reCAPTCHA v2 | `g-recaptcha-response` |

If you submit the form before the token is in that field — or if you
write to the wrong field — the server-side handler sees an empty
g-recaptcha-response and rejects the request.

**Fix**: write the token in via JS, dispatch `input` and `change`
events so any framework listeners react, and *then* submit.

### 4. Some integrations require a JS callback to fire

Plenty of widgets are configured `data-callback="onSuccess"` and the
submit button is JS-disabled until that callback fires. Just writing
into the response field doesn't invoke the callback. You have to call
the named function with the token as the argument.

**Fix**: detect the callback name from the widget's HTML
(`data-callback="..."`), then call `window.<name>(token)`.

## All four are easy to get wrong silently

The killer feature of these failures is they all "look like the solver
is broken." The HTTP call succeeded, the token came back, you wrote
it into the form. Why does it still fail?

Until now the answer was: read network traces, write print statements,
swear at the JS console.

## Doctor: one command, labeled root cause

[CaptchaAI Workflow Doctor](https://github.com/CaptchaAI/captchaai-workflow-doctor)
is a CLI that runs the full workflow end to end against a real
Chromium browser and prints exactly which of the four (and eight
other) things broke:

```bash
$ captchaai-doctor run --profile profiles/checkout.yaml --ci
status=failure root_cause=callback_not_invoked duration=4.71s ...
```

Or in the HTML report:

> **Recommendation**: None of the configured callback candidates are
> defined on the page when injection runs. Inspect the widget's
> `data-callback` attribute and add that function name to
> `detection.callback_candidates` in your profile.

There are 12 root-cause classes (full list:
[failure-taxonomy.md](https://github.com/CaptchaAI/captchaai-workflow-doctor/blob/main/docs/failure-taxonomy.md))
covering everything from `captchaai_balance` (top up) to
`sitekey_not_found` (the doctor will also tell you which widget kind it
*did* find on the page) to `verification_failed` (the token went
through but server-side rejected it).

## Try it in 60 seconds, no API key required

```bash
git clone https://github.com/CaptchaAI/captchaai-workflow-doctor
cd captchaai-workflow-doctor
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
python -m playwright install chromium

captchaai-doctor demo turnstile         # spins up a local mock + drives it
captchaai-doctor demo recaptcha-v2
```

Look at `run-artifacts/demo-turnstile/report.html`. That's what doctor
gives you for any profile you point it at.

## Real-API evidence

Doctor itself is tested against the production CaptchaAI API. The
real-solve test (`tests/test_live_solve.py`, double-gated behind
`DOCTOR_ALLOW_REAL_API=1` + `DOCTOR_ALLOW_REAL_SOLVE=1`) consumes a
solve from Google's documented test sitekey on every release and
asserts the token is real. The result log is in
[`docs/real-e2e-evidence.md`](https://github.com/CaptchaAI/captchaai-workflow-doctor/blob/main/docs/real-e2e-evidence.md).

## Try it on your own integration

```bash
cp profiles/turnstile-generic.yaml profiles/my-flow.yaml
$EDITOR profiles/my-flow.yaml         # set target.url, sitekey, etc.
captchaai-doctor validate-profile profiles/my-flow.yaml
captchaai-doctor run --profile profiles/my-flow.yaml \
  --api-key $CAPTCHAAI_API_KEY \
  --artifact-dir run-artifacts/
open run-artifacts/report.html
```

Five seconds later you'll know what to fix.

---

*Doctor is Apache-2.0 licensed and lives at
[github.com/CaptchaAI/captchaai-workflow-doctor](https://github.com/CaptchaAI/captchaai-workflow-doctor).
PRs welcome — see [CONTRIBUTING.md](https://github.com/CaptchaAI/captchaai-workflow-doctor/blob/main/CONTRIBUTING.md).*
