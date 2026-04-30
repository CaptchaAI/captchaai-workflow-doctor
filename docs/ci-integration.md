# CI integration

Doctor is designed to run inside a CI job and either fail the build or
publish a report you can attach as an artifact.

## Recommended invocation

```bash
captchaai-doctor run \
  --profile profiles/checkout-flow.yaml \
  --artifact-dir run-artifacts/ \
  --ci \
  --fail-on workflow
```

What that does:

- `--ci` switches output to a single `key=value` line that's easy to
  grep / parse.
- `--fail-on workflow` exits non-zero on `failure` (any non-`ok` root
  cause).
- `--artifact-dir` puts `report.json`, `report.html`, and screenshots
  in one directory you can upload via your CI's artifact action.
- `--no-html` is available if you only want the JSON.

## Exit codes (`§10.6` of the plan)

| Code | Meaning |
|---|---|
| `0` | Run completed and passed `--fail-on`. |
| `1` | Run completed but `--fail-on` matched the result. |
| `2` | Profile loading / config / usage error. |

## `--fail-on` modes

| Value | Fails on |
|---|---|
| `none` | Nothing (always exit 0 on a successful run). |
| `workflow` | Anything other than `root_cause=ok`. |
| `error` | Only `status=error` (i.e. infrastructure / unexpected exception). |

## GitHub Actions example

```yaml
- name: Doctor
  env:
    CAPTCHAAI_API_KEY: ${{ secrets.CAPTCHAAI_API_KEY }}
  run: |
    captchaai-doctor run \
      --profile profiles/checkout-flow.yaml \
      --artifact-dir run-artifacts/ \
      --ci --fail-on workflow

- name: Upload report
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: doctor-report
    path: run-artifacts/
```

## Validating reports against the schema

Every report is a strict subset of `report.REPORT_JSON_SCHEMA`
(Draft 2020-12). Export the schema for your downstream tooling:

```bash
captchaai-doctor schema --output schemas/report.json
```

Then validate in any CI step:

```python
import json
from jsonschema import Draft202012Validator

schema = json.load(open("schemas/report.json"))
report = json.load(open("run-artifacts/report.json"))
Draft202012Validator(schema).validate(report)
```

## Smoke-only mode (no real solve)

If you don't want to spend on real solves in CI, use `--mock-captchaai`
plus the bundled demo apps:

```bash
captchaai-doctor demo turnstile
captchaai-doctor demo recaptcha-v2
```

Both spin up an isolated Flask app, drive it through the full
pipeline with the fake CaptchaAI client, and produce a real
`report.json` + `report.html`. This is exactly what
`.github/workflows/demo-smoke.yml` runs on every PR.
