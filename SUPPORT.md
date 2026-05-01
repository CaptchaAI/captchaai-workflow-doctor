# Support

How to get help with **CaptchaAI Workflow Doctor**.

## Three lanes

### 1. Bug or unexpected behavior in the doctor itself

Open a [GitHub issue](https://github.com/CaptchaAI/captchaai-workflow-doctor/issues/new/choose)
using the **Bug report** template.

Please attach:

- Your `report.json` (after redacting any secrets — see below).
- Your profile YAML (after removing any private selectors / URLs you
  don't want to share publicly).
- The exact CLI command you ran.
- Doctor version (`captchaai-doctor --version`), OS, Python version.

### 2. "How do I…?" usage questions

Open a [GitHub issue](https://github.com/CaptchaAI/captchaai-workflow-doctor/issues/new/choose)
using the **Support question** template, or start a thread in the
[Discussions](https://github.com/CaptchaAI/captchaai-workflow-doctor/discussions)
tab if your repo has discussions enabled.

Before opening a question, please skim:

- [Quickstart](README.md#quickstart-10-minutes-from-a-fresh-checkout)
- [docs/profile-schema.md](docs/profile-schema.md)
- [docs/failure-taxonomy.md](docs/failure-taxonomy.md)
- [docs/troubleshooting.md](docs/troubleshooting.md)

### 3. Account / billing / API key issues

These are not doctor issues — please contact CaptchaAI support
directly at **`support@captchaai.com`** or via your account dashboard
at [captchaai.com](https://captchaai.com).

If you suspect the issue is on the CaptchaAI side, the doctor's JSON
report (with a labeled `root_cause` and the redacted captcha_id) is
the fastest thing to attach. See
[docs/sending-a-support-report.md](docs/sending-a-support-report.md)
for the redaction + send checklist.

---

## Redact before you send

The doctor redacts API keys, captcha ids, and tokens from logs and
the rendered report by default. Before you attach a report to a
public issue, do a final pass:

```bash
grep -E "(api[_-]?key|token|captcha[_-]?id)" report.json
```

Any matches should already be `****`-redacted. If you find a real
secret, delete the report file and re-run with the latest version
(`pip install -U captchaai-workflow-doctor`).

## Security issues

See [SECURITY.md](SECURITY.md). Please do not open public issues for
security reports.
