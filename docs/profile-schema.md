# Profile schema

A profile is a YAML file describing a CAPTCHA-solving workflow to diagnose. The complete schema is enforced by Pydantic v2 models in [captchaai_doctor/schemas.py](../captchaai_doctor/schemas.py).

## Top-level keys

| Key | Required | Type | Notes |
|---|---|---|---|
| `name` | yes | string | `[a-zA-Z0-9._-]+`, max 120 chars |
| `captcha_type` | yes | enum | `turnstile` \| `recaptcha_v2` |
| `target` | yes | object | see below |
| `browser` | no | object | sensible defaults |
| `captchaai` | no | object | endpoints + polling |
| `detection` | no | object | selectors + callback candidates |
| `actions` | no | object | `before_solve` + `after_token` lists |
| `success` | yes | object | at least one of `any_selector` / `url_contains` |
| `failure` | no | object | `any_text` and/or `any_selector` |

## `target`

```yaml
target:
  url: "https://staging.example.com/login"
  allowed_domains:
    - "staging.example.com"
```

The host of `target.url` MUST appear in `allowed_domains`. This guards against accidentally running the doctor against the wrong site.

## `browser`

```yaml
browser:
  engine: chromium      # chromium | firefox | webkit
  headless: true
  timeout_ms: 60000     # 1000..600000
  record_trace: false
  screenshots: true
```

## `captchaai`

```yaml
captchaai:
  submit_endpoint: "https://ocr.captchaai.com/in.php"
  result_endpoint: "https://ocr.captchaai.com/res.php"
  polling_interval_seconds: 5    # 0 < x <= 60
  max_wait_seconds: 120          # 10..600
```

Endpoints default to the CaptchaAI 2captcha-compatible URLs.

## `detection`

```yaml
detection:
  sitekey_selector: "[data-sitekey]"
  response_field_selector: "textarea[name='cf-turnstile-response']"
  callback_candidates:
    - "onTurnstileSuccess"
```

All selectors are validated as parseable CSS at load time.

## `actions`

`before_solve` and `after_token` are ordered lists of action objects. Each action has a `type`:

| Type | Fields |
|---|---|
| `fill` | `selector`, exactly one of `value` or `value_env` |
| `click` | `selector` |
| `wait` | `milliseconds` (0..120000) |
| `inject_token` | `selector` |
| `invoke_callback_if_detected` | (no fields) |

```yaml
actions:
  before_solve:
    - type: fill
      selector: "input[name='email']"
      value_env: "QA_EMAIL"          # NAME of an env var, never the value itself
  after_token:
    - type: inject_token
      selector: "textarea[name='cf-turnstile-response']"
    - type: invoke_callback_if_detected
    - type: click
      selector: "button[type='submit']"
```

## `success` and `failure`

```yaml
success:
  any_selector:
    - "[data-testid='dashboard']"
  url_contains:
    - "/dashboard"

failure:
  any_text:
    - "captcha verification failed"
  any_selector:
    - ".error-banner"
```

`success` MUST declare at least one condition. `failure` is optional but recommended for unambiguous classification.

## Secrets policy

Profiles MUST NOT contain API keys, passwords, tokens, or session cookies.

The loader scans every string value for secret-shaped patterns (long hex strings, long opaque tokens) and rejects any that match. Use `value_env: NAME` for `fill` actions, and set `NAME` in your environment.

## CLI

```bash
captchaai-doctor validate-profile profiles/local-demo-login-turnstile.yaml
```

Exit codes:

- `0` — profile is valid
- `2` — profile is invalid (message printed to stderr)
