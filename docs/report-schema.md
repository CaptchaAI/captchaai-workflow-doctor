# Report schema

The JSON report (`report.json`) conforms to a strict Draft 2020-12
JSON Schema with `additionalProperties: false`. Use it to validate
downstream tooling.

## Get the schema

```bash
captchaai-doctor schema                          # to stdout
captchaai-doctor schema --output schema.json    # to a file
```

Or in Python:

```python
from captchaai_doctor.report import REPORT_JSON_SCHEMA
```

## Top-level fields

| Field | Type | Notes |
|---|---|---|
| `profile_name` | string | From the profile's `name`. |
| `captcha_type` | enum | `"turnstile"` or `"recaptcha_v2"`. |
| `target_url` | URI | The page the workflow ran against. |
| `started_at` / `ended_at` | ISO-8601 string | UTC. |
| `duration_seconds` | number ≥ 0 | Wall-clock. |
| `status` | enum | `"success"`, `"failure"`, `"error"`. |
| `root_cause` | string | One of the values in [`failure-taxonomy.md`](failure-taxonomy.md). |
| `recommendation` | string | Human-readable one-liner; same as the HTML report. |
| `detail` | string \| null | Free-form additional context. |
| `captcha_id_redacted` | string \| null | First 4 chars of the captcha ID + `****`. |
| `poll_attempts` | int ≥ 0 | How many times we hit `res.php`. |
| `poll_seconds` | number ≥ 0 | Cumulative time in `poll_until_ready`. |
| `sitekey_found` | string \| null | The sitekey we read off the page. |
| `screenshots` | array<string> | Filenames relative to the artifact dir. |
| `action_steps` | array<object> | Per-step record (see below). |

## `action_steps[]`

| Field | Type | Notes |
|---|---|---|
| `type` | string | `"fill"`, `"click"`, `"wait"`, `"inject_token"`, `"invoke_callback_if_detected"`, etc. |
| `selector` | string \| null | CSS selector (null for steps that don't take one). |
| `succeeded` | bool | Did the step run without raising? |
| `detail` | string \| null | Free-form. |

## Stability

The schema's `$id` is
`https://captchaai.com/schemas/captchaai-doctor-report-1.json`. Breaking
changes will bump the suffix to `-2`.
