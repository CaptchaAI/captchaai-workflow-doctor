# Token lifecycle

The token returned by CaptchaAI is short-lived and single-use. Most
"the token is valid but my page rejected it" problems are caused by
breaking one of the four constraints below.

## 1. Token is bound to a (sitekey, page URL) pair

When you call `submit_turnstile` or `submit_recaptcha_v2`, you tell
CaptchaAI:

- `sitekey` — the public site key from the widget's HTML
- `pageurl` — the page where that widget renders

The solver computes a token that is only valid for **that exact pair**,
as Cloudflare/Google's verification will check both.

Common mistakes:

- Using `https://example.com/` when the widget is on
  `https://example.com/login`. Use the **canonical URL the widget
  actually loads on**, not the homepage.
- Using a sitekey scraped from a different environment (staging vs.
  prod often have different keys).
- Trailing-slash mismatch — try with and without.

## 2. Token expires fast

Both Cloudflare Turnstile and Google reCAPTCHA tokens expire in
**~120 seconds** from issue. If you:

- batch tokens
- queue a token while polling another captcha
- pause the workflow at a breakpoint
- retry after a long wait

… the token will silently fail validation. Doctor measures the
end-to-end time and includes it in the report so you can spot this.

## 3. Token must be present in the right field at submit time

The widget injects a hidden response field next to the challenge:

| Type | Field name |
|---|---|
| Turnstile | `cf-turnstile-response` |
| reCAPTCHA v2 | `g-recaptcha-response` |

You must write the token into that field *before* submitting the form.
Doctor's `injector` writes the value via `eval_on_selector` (so hidden
fields work) and dispatches both `input` and `change` events so any
React/Vue listeners notice.

## 4. The widget's JS callback may need to fire

Some integrations gate the submit button on a JS callback the widget
invokes when it has a token (e.g. `data-callback="onTurnstileSuccess"`).
Just writing into the response field does not invoke that callback.

Doctor's `injector.invoke_callback` calls the named function with the
token as the argument. The list of names to try is configurable per
profile (`detection.callback_candidates`).

## 5. Server-side verification is what you're really debugging

If steps 1-4 are all correct and the page still rejects the workflow,
the token reached your server but server-side `siteverify` rejected it.
That's almost always one of:

- Your server is using a **different secret key** than the sitekey was
  issued for.
- Your server passed a **stale or wrong remoteip**.
- The token was reused (already redeemed).
- Network/clock skew >>5 seconds.

Doctor cannot see your server, but the report's screenshot and the
verifier output usually tells you which side rejected the token.
