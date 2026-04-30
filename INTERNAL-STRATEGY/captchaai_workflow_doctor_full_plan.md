# CaptchaAI Workflow Doctor — Full Execution Plan

## 0. Executive Summary

Build **CaptchaAI Workflow Doctor**: a runnable diagnostic helper repo that helps developers understand why a CAPTCHA-solving workflow fails even when the solver API returns a token.

This is not just another article and not just a small API wrapper.

It is a practical debugging system that follows the full workflow:

1. Open the target page or local demo.
2. Detect CAPTCHA type and page parameters.
3. Submit the challenge to CaptchaAI.
4. Poll until a token/answer is ready.
5. Inject the token/answer into the browser/page state.
6. Trigger callbacks when required.
7. Submit the form or workflow step.
8. Verify success/failure.
9. Classify the root cause.
10. Produce a report with fixes.

The public repo should be **generic and profile-based**, not website-specific. It should ship local demos and generic profiles. Clients can create private profiles for their own authorized staging, QA, or production workflows.

---

## 1. Strategic Goal

### 1.1 Business goal

The project should support three CaptchaAI outcomes:

- **Drive API adoption** by reducing time-to-first-successful-solve.
- **Reduce support load** by giving users self-service diagnostics.
- **Build technical authority** by producing a hard, useful, runnable asset competitors are unlikely to match.

### 1.2 Content goal

Create a flagship article plus example repo that answers a high-intent developer pain:

> “CaptchaAI gave me a token, but my page still rejects the CAPTCHA. What is wrong?”

The answer should not be theoretical. The article should point to a runnable tool that gives the developer a diagnosis.

### 1.3 Product goal

The repo should be useful enough that a developer can run:

```bash
captchaai-doctor run \
  --profile profiles/my-flow.yaml \
  --api-key $CAPTCHAAI_API_KEY \
  --output reports/my-flow.html
```

And get:

- HTML report
- JSON report
- browser screenshots
- trace file
- root-cause classification
- recommended fix

---

## 2. ICP Focus

## 2.1 Primary ICP: Automation Developer

### Why this ICP matters

Automation developers are the most direct users of CaptchaAI API. They need:

- working code
- clear request/response handling
- polling logic
- browser integration
- debugging help
- repeatable examples

### Their main pain

They often believe the CAPTCHA solver failed, but the real problem may be:

- wrong page URL
- wrong sitekey
- token injected into the wrong field
- callback not triggered
- token expired before form submission
- browser state did not update
- session/proxy mismatch
- bad retry loop
- bad timeout settings

### What they get from this repo

A diagnostic tool that tells them where the workflow fails.

---

## 2.2 Secondary ICP: Scraping Engineer

### Why this ICP matters

Scraping engineers manage more complex environments:

- proxies
- browser sessions
- retries
- rate limits
- worker queues
- challenge loops
- distributed systems
- anti-blocking workflows

### Their main pain

They do not only need a solve token. They need to know whether the solve token is accepted by the browser workflow under realistic network/session conditions.

### What they get from this repo

A workflow-level debug system that can be used during integration, QA, and CI.

---

## 2.3 Tertiary ICP: Agency / Integrator

### Why this ICP matters

Agencies and integrators need reusable assets for clients.

### Their main pain

They repeatedly solve the same integration/debugging problems for different clients.

### What they get from this repo

A reusable profile-based framework where each client gets a private profile, but the core repo remains the same.

---

## 3. Core Product Decision

## 3.1 Generic or website-specific?

Use a **generic core + profile-based configuration**.

Do not build one public repo per website.

### Correct model

```text
captchaai-workflow-doctor/
  profiles/
    recaptcha-v2-generic.yaml
    turnstile-generic.yaml
    local-demo-login.yaml
```

A client can privately add:

```text
profiles/client-staging-login.yaml
profiles/client-checkout-flow.yaml
profiles/client-internal-form.yaml
```

### Why this is best

- One reusable public repo.
- Safe public positioning.
- Clients can adapt it to their own authorized flows.
- No risky public tutorials for specific third-party websites.
- Easier maintenance.
- Easier to integrate into CI.

---

## 4. Safe Positioning

## 4.1 Use this positioning

> Debug your CAPTCHA-solving integration from API request to browser success.

Or:

> Find why your CAPTCHA solve fails after token delivery.

Or:

> A workflow diagnostic tool for authorized CAPTCHA integration testing.

## 4.2 Avoid this positioning

Do not say:

- bypass CAPTCHA
- undetectable automation
- beat Cloudflare
- solve any website
- anti-detect browser workflow
- mass account creation
- evade detection

## 4.3 Public repo disclaimer

Use this in the README:

```md
## Responsible Use

CaptchaAI Workflow Doctor is designed for developers testing CAPTCHA-solving integrations in systems they own, operate, or are authorized to test.

Do not use this project for unauthorized access, spam, credential attacks, account farming, or activity that violates a website’s terms or applicable law.
```

---

## 5. What We Will Produce

## 5.1 Public GitHub repo

Recommended name:

```text
captchaai-workflow-doctor
```

Alternative names:

```text
captchaai-integration-doctor
captchaai-token-debugger
captchaai-browser-workflow-doctor
```

Best name:

```text
captchaai-workflow-doctor
```

Because it covers more than token debugging.

---

## 5.2 Flagship article

Recommended title:

```text
Why CAPTCHA Tokens Work in the API but Fail in the Browser: A Practical Debugging System
```

Alternative SEO titles:

```text
CAPTCHA Token Injection Fails? Debug the Full Solver-to-Browser Workflow
```

```text
How to Debug CAPTCHA Solving Workflows After Token Delivery
```

Recommended final:

```text
Why CAPTCHA Tokens Work in the API but Fail in the Browser
```

Subtitle:

```text
Use CaptchaAI Workflow Doctor to diagnose sitekey, page URL, polling, token injection, callback, timeout, and browser-state failures.
```

---

## 5.3 Example pack

Public examples repo path:

```text
CaptchaAI-Examples/articles/captchaai-workflow-doctor/
```

Example pack should include:

```text
README.md
python/
nodejs/
docker/
profiles/
sample-reports/
```

---

## 5.4 Blog visuals

Required visuals:

1. Hero image
2. Workflow architecture diagram
3. Failure taxonomy decision tree
4. Example report screenshot
5. Token lifecycle timeline

Recommended file names:

```text
assets/images/captchaai-workflow-doctor-hero.png
assets/images/captchaai-workflow-doctor-architecture.png
assets/images/captchaai-workflow-doctor-failure-tree.png
assets/images/captchaai-workflow-doctor-token-lifecycle.png
```

---

## 6. User Story

## 6.1 Main user story

As an automation developer, I want to run a diagnostic tool against my authorized CAPTCHA workflow so that I can know whether the failure is caused by API parameters, polling, token lifecycle, browser injection, callback execution, session state, or form validation.

## 6.2 Example real-world story

A client has a staging login page protected by Cloudflare Turnstile.

They use Playwright for QA automation.

CaptchaAI returns a token, but the page still says:

```text
captcha verification failed
```

The client runs:

```bash
captchaai-doctor run \
  --profile profiles/staging-login.yaml \
  --output reports/staging-login.html
```

The tool returns:

```text
Root cause: callback_not_triggered
Confidence: 91%

Explanation:
CaptchaAI returned a token and the token was inserted into the expected field.
However, the page did not execute the expected Turnstile callback before form submission.

Recommended fix:
Invoke the detected callback after token injection and wait for the page’s challenge-complete state before clicking submit.
```

This turns a vague support issue into a specific engineering fix.

---

## 7. Repo Structure

Recommended repository structure:

```text
captchaai-workflow-doctor/
  README.md
  LICENSE
  CONTRIBUTING.md
  SECURITY.md
  CODE_OF_CONDUCT.md
  .gitignore
  .env.example
  docker-compose.yml

  docs/
    overview.md
    responsible-use.md
    failure-taxonomy.md
    token-lifecycle.md
    profile-schema.md
    report-schema.md
    ci-integration.md
    troubleshooting.md
    architecture.md

  profiles/
    recaptcha-v2-generic.yaml
    turnstile-generic.yaml
    local-demo-login-turnstile.yaml
    local-demo-form-recaptcha-v2.yaml

  demos/
    mock-login-turnstile/
      package.json
      src/
      public/
      README.md
    mock-form-recaptcha-v2/
      package.json
      src/
      public/
      README.md

  packages/
    python/
      pyproject.toml
      captchaai_doctor/
        __init__.py
        cli.py
        config.py
        captchaai_client.py
        poller.py
        browser.py
        detector.py
        injector.py
        verifier.py
        classifier.py
        report.py
        redaction.py
        schemas.py
      tests/

    node/
      package.json
      tsconfig.json
      src/
        cli.ts
        config.ts
        captchaaiClient.ts
        poller.ts
        browserDoctor.ts
        detector.ts
        injector.ts
        verifier.ts
        classifier.ts
        report.ts
        redaction.ts
        schemas.ts
      tests/

  reports/
    .gitkeep

  sample-reports/
    success-turnstile.json
    failure-callback-not-triggered.json
    failure-token-expired.json
    failure-wrong-sitekey.json

  scripts/
    run-local-demo.sh
    validate-profile.py
    generate-report-fixtures.py

  .github/
    workflows/
      test.yml
      lint.yml
      demo-smoke.yml
```

---

## 8. Feature Scope

## 8.1 Version 1 must include

### CLI

Required commands:

```bash
captchaai-doctor --help
captchaai-doctor validate-profile --profile profiles/example.yaml
captchaai-doctor run --profile profiles/example.yaml
captchaai-doctor demo turnstile
captchaai-doctor demo recaptcha-v2
```

### CaptchaAI API client

Must support:

- submit endpoint
- result endpoint
- API key via env var or flag
- polling
- timeout
- retry
- JSON and plain response handling if needed
- safe logging with API key redaction

### Browser runner

Must support:

- Playwright Chromium
- headless mode
- headed mode for debugging
- screenshots
- trace recording
- selector-based actions
- success/failure detection

### CAPTCHA detection

Must support:

- Cloudflare Turnstile generic detection
- reCAPTCHA v2 generic detection

### Token injection

Must support:

- Turnstile response field injection
- reCAPTCHA v2 textarea injection
- optional callback invocation
- wait conditions after injection

### Failure classification

Must support at minimum:

- `profile_config_invalid`
- `captcha_not_detected`
- `sitekey_missing`
- `pageurl_invalid`
- `captchaai_submit_failed`
- `captchaai_poll_timeout`
- `captchaai_returned_error`
- `token_received`
- `token_injection_failed`
- `callback_not_found`
- `callback_not_triggered`
- `token_expired_before_submit`
- `form_submit_failed`
- `success_condition_not_met`
- `challenge_loop_detected`
- `proxy_session_mismatch_possible`
- `unknown_failure`

### Reports

Must generate:

- JSON report
- HTML report
- screenshot folder
- trace archive if enabled

---

## 8.2 Version 1 should not include

Do not include in v1:

- automated solving for a list of public target websites
- anti-detect browser integration
- proxy marketplace integrations
- multi-account workflows
- scraping templates for specific sites
- stealth plugin recommendations
- huge dashboard complexity
- browser extension
- hosted SaaS dashboard

Keep v1 focused and shippable.

---

## 9. Profile Schema

## 9.1 Example profile

```yaml
name: acme-staging-login
captcha_type: turnstile

target:
  url: "https://staging.example.com/login"
  allowed_domains:
    - "staging.example.com"

browser:
  engine: chromium
  headless: true
  timeout_ms: 60000
  record_trace: true
  screenshots: true

captchaai:
  submit_endpoint: "https://ocr.captchaai.com/in.php"
  result_endpoint: "https://ocr.captchaai.com/res.php"
  polling_interval_seconds: 5
  max_wait_seconds: 120

detection:
  sitekey_selector: "[data-sitekey]"
  response_field_selector: "textarea[name='cf-turnstile-response']"
  callback_candidates:
    - "onTurnstileSuccess"
    - "turnstileCallback"

actions:
  before_solve:
    - type: fill
      selector: "input[name='email']"
      value_env: "QA_EMAIL"
    - type: fill
      selector: "input[name='password']"
      value_env: "QA_PASSWORD"

  after_token:
    - type: inject_token
      selector: "textarea[name='cf-turnstile-response']"
    - type: invoke_callback_if_detected
    - type: wait
      milliseconds: 1500
    - type: click
      selector: "button[type='submit']"

success:
  any_selector:
    - "[data-testid='dashboard']"
    - ".account-home"
  url_contains:
    - "/dashboard"

failure:
  any_text:
    - "captcha verification failed"
    - "challenge failed"
    - "please try again"
```

---

## 9.2 Profile rules

The tool must validate:

- `name` exists
- `captcha_type` is supported
- `target.url` exists
- `target.allowed_domains` contains the target host
- `captchaai.submit_endpoint` is valid
- `captchaai.result_endpoint` is valid
- `polling_interval_seconds` is reasonable
- `max_wait_seconds` is reasonable
- success/failure conditions are not empty
- selectors are syntactically plausible
- no API key is stored directly in the YAML profile

If profile validation fails, the tool should stop before opening the browser.

---

## 10. CLI Design

## 10.1 Basic usage

```bash
captchaai-doctor run \
  --profile profiles/local-demo-login-turnstile.yaml \
  --api-key $CAPTCHAAI_API_KEY
```

## 10.2 Output path

```bash
captchaai-doctor run \
  --profile profiles/local-demo-login-turnstile.yaml \
  --output reports/local-demo-login.html
```

## 10.3 Headed browser mode

```bash
captchaai-doctor run \
  --profile profiles/local-demo-login-turnstile.yaml \
  --headed
```

## 10.4 JSON-only report

```bash
captchaai-doctor run \
  --profile profiles/local-demo-login-turnstile.yaml \
  --json reports/local-demo-login.json
```

## 10.5 CI mode

```bash
captchaai-doctor run \
  --profile profiles/staging-login.yaml \
  --ci \
  --fail-on callback_not_triggered,token_expired_before_submit
```

## 10.6 Exit codes

```text
0 = workflow success
1 = workflow failed
2 = profile/config error
3 = CaptchaAI API error
4 = browser/runtime error
5 = unsupported CAPTCHA type
```

---

## 11. Diagnostic Report Schema

## 11.1 JSON report example

```json
{
  "schema_version": "1.0",
  "run_id": "2026-04-30T12-45-00Z-acme-staging-login",
  "profile_name": "acme-staging-login",
  "status": "failed",
  "root_cause": "callback_not_triggered",
  "confidence": 0.91,
  "captcha": {
    "type": "turnstile",
    "sitekey_detected": true,
    "sitekey_redacted": "0x4AAAA...abcd",
    "pageurl": "https://staging.example.com/login"
  },
  "captchaai": {
    "submit_ok": true,
    "captcha_id_redacted": "7382****",
    "poll_ok": true,
    "solve_time_ms": 18200,
    "token_received": true,
    "token_age_at_injection_ms": 320
  },
  "browser": {
    "token_field_found": true,
    "token_injected": true,
    "callback_detected": true,
    "callback_invoked": false,
    "form_submitted": true,
    "success_condition_met": false,
    "failure_condition_met": true,
    "failure_text": "captcha verification failed"
  },
  "recommended_fix": {
    "summary": "The token was received and injected, but the page callback was not triggered.",
    "actions": [
      "Inspect the page for the Turnstile callback function.",
      "Invoke the callback after token injection.",
      "Wait for a challenge-complete state before submitting the form."
    ]
  },
  "artifacts": {
    "html_report": "reports/acme-staging-login.html",
    "json_report": "reports/acme-staging-login.json",
    "trace": "reports/acme-staging-login-trace.zip",
    "screenshots": [
      "reports/screenshots/01-page-loaded.png",
      "reports/screenshots/02-captcha-detected.png",
      "reports/screenshots/03-token-injected.png",
      "reports/screenshots/04-submit-failed.png"
    ]
  }
}
```

---

## 12. Failure Taxonomy

## 12.1 Configuration failures

### `profile_config_invalid`

The YAML profile is invalid or incomplete.

Recommended fix:

- run `captchaai-doctor validate-profile`
- check required fields
- remove secrets from profile
- confirm allowed domain

### `target_domain_not_allowed`

The target URL host is not listed in `allowed_domains`.

Recommended fix:

- add the target host to `allowed_domains`
- verify the URL is correct
- avoid accidentally running against the wrong domain

---

## 12.2 Detection failures

### `captcha_not_detected`

The browser page loaded, but no supported CAPTCHA widget was detected.

Recommended fix:

- verify the CAPTCHA appears in the tested state
- run headed mode
- check if login/form steps before CAPTCHA are required
- add selectors to the profile

### `sitekey_missing`

The CAPTCHA appears present, but no sitekey was extracted.

Recommended fix:

- inspect DOM
- provide `sitekey_selector`
- pass the sitekey explicitly if authorized and stable

---

## 12.3 CaptchaAI API failures

### `captchaai_submit_failed`

The submit request failed.

Recommended fix:

- verify API key
- verify required parameters
- check endpoint
- check method/type field
- inspect redacted request payload

### `captchaai_poll_timeout`

The tool submitted the challenge, but polling did not return a ready token in time.

Recommended fix:

- increase `max_wait_seconds`
- check challenge type
- check balance/API status
- retry later
- add backoff

### `captchaai_returned_error`

CaptchaAI returned an error response.

Recommended fix:

- map the error code to docs
- verify parameters
- check account/balance
- check challenge type support

---

## 12.4 Token lifecycle failures

### `token_expired_before_submit`

The token was received but too much time passed before form submission.

Recommended fix:

- solve later in the workflow
- reduce browser actions after token receipt
- submit immediately after injection
- avoid queue delays

### `token_reuse_detected`

A token appears to have been reused.

Recommended fix:

- never reuse tokens
- bind each token to a single browser attempt
- solve again per attempt

---

## 12.5 Browser integration failures

### `token_injection_failed`

The tool could not write the token into the expected field.

Recommended fix:

- verify response field selector
- run headed mode
- check iframe boundaries
- check whether the widget renders late

### `callback_not_found`

The page probably expects callback execution, but no callback was found.

Recommended fix:

- inspect widget configuration
- add callback candidates to profile
- check JavaScript globals
- use browser trace

### `callback_not_triggered`

The token was injected, but the expected callback did not run.

Recommended fix:

- invoke the callback explicitly
- wait for page state change
- verify callback name

### `success_condition_not_met`

The token was submitted, but the success condition did not appear.

Recommended fix:

- check success selector
- inspect server response
- check application-specific validation
- inspect screenshots and trace

### `challenge_loop_detected`

The page returned to a challenge state after submission.

Recommended fix:

- check page URL
- check session continuity
- check proxy/session consistency
- check token age
- verify that the CAPTCHA type and sitekey are correct

---

## 13. Architecture

## 13.1 High-level flow

```text
Profile YAML
    |
    v
Profile Validator
    |
    v
Browser Runner
    |
    v
CAPTCHA Detector
    |
    v
CaptchaAI Client
    |
    v
Polling Manager
    |
    v
Token Injector
    |
    v
Callback Handler
    |
    v
Form Submitter
    |
    v
Success/Failure Verifier
    |
    v
Failure Classifier
    |
    v
HTML/JSON Report Generator
```

---

## 13.2 Python components

```text
captchaai_doctor/
  config.py
    load_profile()
    validate_profile()

  captchaai_client.py
    submit_challenge()
    poll_result()

  poller.py
    poll_until_ready()
    calculate_backoff()

  browser.py
    launch_browser()
    run_actions()
    capture_screenshot()
    record_trace()

  detector.py
    detect_captcha_type()
    extract_sitekey()
    detect_response_field()
    detect_callback_candidates()

  injector.py
    inject_token()
    invoke_callback()
    verify_token_present()

  verifier.py
    check_success_conditions()
    check_failure_conditions()

  classifier.py
    classify_failure()
    calculate_confidence()

  report.py
    write_json_report()
    write_html_report()

  redaction.py
    redact_api_key()
    redact_token()
    redact_captcha_id()
```

---

## 14. Local Demo Design

## 14.1 Why local demos matter

The public repo should not depend on third-party target sites.

Local demos allow:

- safe article screenshots
- repeatable CI tests
- failure-mode simulation
- client understanding without legal risk

---

## 14.2 Demo 1: Turnstile-like login

Path:

```text
demos/mock-login-turnstile/
```

Features:

- login form
- CAPTCHA-like widget placeholder
- hidden response field
- callback function
- success page
- configurable failure mode

Modes:

```bash
DEMO_FAILURE_MODE=none
DEMO_FAILURE_MODE=callback_required
DEMO_FAILURE_MODE=token_expired
DEMO_FAILURE_MODE=wrong_field
```

---

## 14.3 Demo 2: reCAPTCHA-like form

Path:

```text
demos/mock-form-recaptcha-v2/
```

Features:

- form page
- `g-recaptcha-response` textarea
- submit button
- server-side validation mock
- success/failure text

Modes:

```bash
DEMO_FAILURE_MODE=none
DEMO_FAILURE_MODE=missing_token
DEMO_FAILURE_MODE=expired_token
DEMO_FAILURE_MODE=reused_token
```

---

## 15. MVP Build Plan

## 15.1 Phase 1 — Spec and repo skeleton

Duration: 2-3 days

Tasks:

- create repo
- write README
- write responsible use policy
- create profile schema
- create report schema
- create failure taxonomy doc
- create Python package skeleton
- create Node package skeleton
- add Docker Compose
- add CI lint/test workflow

Deliverables:

- repo skeleton
- docs
- empty CLI command
- profile validation command

Acceptance criteria:

- `captchaai-doctor --help` works
- `captchaai-doctor validate-profile profiles/local-demo-login-turnstile.yaml` works
- CI runs

---

## 15.2 Phase 2 — CaptchaAI API client

Duration: 3-4 days

Tasks:

- implement submit request
- implement polling
- implement timeout
- implement structured errors
- implement redacted logs
- write tests with mocked HTTP responses
- document supported parameters

Deliverables:

- Python client
- Node client
- tests
- sample JSON responses

Acceptance criteria:

- successful mocked solve flow passes
- timeout case classified
- API key never appears in logs
- request/response examples documented

---

## 15.3 Phase 3 — Browser runner and local demos

Duration: 5-7 days

Tasks:

- implement Playwright browser runner
- implement local Turnstile-like demo
- implement local reCAPTCHA-like demo
- implement profile-driven actions
- implement screenshots
- implement trace recording

Deliverables:

- local demos
- browser runner
- sample profile
- screenshots

Acceptance criteria:

- `captchaai-doctor demo turnstile` starts local demo
- tool can open page
- tool can fill form
- tool can capture screenshots
- tool can detect simulated widget

---

## 15.4 Phase 4 — Detection and injection

Duration: 5-7 days

Tasks:

- detect Turnstile-like fields
- detect reCAPTCHA-like fields
- extract sitekey
- inject token
- verify field value after injection
- detect callback candidates
- invoke callback if configured
- wait for post-injection state

Deliverables:

- detector module
- injector module
- test profiles
- failure fixtures

Acceptance criteria:

- token injection succeeds in success demo
- callback failure is detected in failure demo
- wrong selector returns clear error
- screenshot shows before/after state

---

## 15.5 Phase 5 — Failure classifier

Duration: 4-5 days

Tasks:

- define classification priority
- implement root cause selection
- implement confidence scoring
- map every failed step to recommendations
- create sample reports for each failure type

Deliverables:

- classifier
- recommendation map
- sample reports

Acceptance criteria:

- each local failure mode maps to expected root cause
- report includes explanation and fix
- unknown failures still include useful timeline

---

## 15.6 Phase 6 — HTML/JSON reports

Duration: 4-5 days

Tasks:

- write JSON report
- write HTML report
- include timeline
- include screenshots
- include root cause
- include recommended fix
- include redacted raw request/response summary
- include environment info

Deliverables:

- report generator
- HTML template
- sample reports

Acceptance criteria:

- report opens locally
- report is readable by non-expert developer
- secrets are redacted
- screenshots are linked
- JSON follows schema

---

## 15.7 Phase 7 — CI mode

Duration: 2-3 days

Tasks:

- add `--ci`
- add `--fail-on`
- implement exit codes
- create GitHub Actions example
- document CI usage

Deliverables:

- CI mode
- GitHub Actions example
- CI docs

Acceptance criteria:

- successful demo exits 0
- failure demo exits 1
- config failure exits 2
- GitHub Actions example runs

---

## 15.8 Phase 8 — Article and example pack

Duration: 4-7 days

Tasks:

- write flagship article
- include code snippets
- include screenshots
- include architecture diagram
- include failure taxonomy table
- add example pack under public examples repo
- validate content
- validate examples
- prepare publishing package

Deliverables:

- article markdown
- public example pack
- image assets
- HTML-ready article

Acceptance criteria:

- article has clear ICP
- article has one dominant search intent
- article includes working commands
- article links to repo
- example pack is runnable
- no unsafe framing

---

## 16. MVP Timeline

Recommended hard but realistic timeline:

```text
Week 1:
  - final spec
  - repo skeleton
  - profile schema
  - report schema
  - API client

Week 2:
  - browser runner
  - local demos
  - detection
  - injection

Week 3:
  - failure classifier
  - reports
  - CI mode
  - tests

Week 4:
  - docs
  - article
  - example pack
  - images
  - validation
  - publishing prep
```

If team capacity is strong, MVP can ship in 3 weeks. If quality is more important, use 4 weeks.

---

## 17. Team Roles

## 17.1 Technical lead

Responsibilities:

- architecture
- profile schema
- failure taxonomy
- code review
- safety review

## 17.2 Python engineer

Responsibilities:

- Python CLI
- CaptchaAI client
- profile validator
- report generator
- tests

## 17.3 Node/Playwright engineer

Responsibilities:

- browser runner
- demos
- token injection
- callback handling
- trace/screenshot capture

## 17.4 Content strategist

Responsibilities:

- article brief
- article draft
- screenshots
- SEO title/meta
- internal linking
- CTA

## 17.5 QA engineer

Responsibilities:

- demo scenarios
- failure fixtures
- cross-platform testing
- CI workflow
- report validation

---

## 18. Task Breakdown

## 18.1 Epic A: Repository foundation

Tasks:

- Create repo.
- Add README.
- Add responsible-use policy.
- Add license.
- Add contribution guide.
- Add security policy.
- Add `.env.example`.
- Add Docker Compose.
- Add docs folder.
- Add package skeletons.
- Add CI workflows.

Definition of done:

- repo can be cloned
- dependencies can be installed
- help command works
- tests run in CI

---

## 18.2 Epic B: Profile system

Tasks:

- Define YAML schema.
- Implement loader.
- Implement validator.
- Add allowed domain check.
- Add secret detection.
- Add example profiles.
- Add profile docs.

Definition of done:

- valid profiles pass
- invalid profiles fail with actionable messages
- no secret is accepted in profile
- examples are documented

---

## 18.3 Epic C: CaptchaAI client

Tasks:

- Implement submit request.
- Implement result polling.
- Implement timeout.
- Implement error mapping.
- Implement redaction.
- Add tests.
- Add examples.

Definition of done:

- client returns structured result
- errors are classified
- polling respects max wait
- logs are safe

---

## 18.4 Epic D: Browser workflow runner

Tasks:

- Launch Chromium.
- Load target URL.
- Run before-solve actions.
- Detect CAPTCHA.
- Capture screenshots.
- Record trace.
- Run after-token actions.
- Verify result.

Definition of done:

- browser workflow runs from profile
- screenshots are saved
- traces are saved when enabled
- failures are structured

---

## 18.5 Epic E: Detection and injection

Tasks:

- Detect reCAPTCHA v2.
- Detect Turnstile.
- Extract sitekey.
- Find response field.
- Inject token.
- Verify injection.
- Detect callback candidates.
- Invoke callback.

Definition of done:

- local demos pass success mode
- each broken mode produces correct failure
- injection is visible in screenshots/report

---

## 18.6 Epic F: Classifier and recommendations

Tasks:

- Create root-cause classifier.
- Create confidence scoring.
- Create recommendation map.
- Create failure docs.
- Create sample reports.

Definition of done:

- every known failure has a clear recommendation
- report explains likely cause
- developer can act on the fix

---

## 18.7 Epic G: Reports

Tasks:

- Implement JSON report.
- Implement HTML report.
- Add screenshots.
- Add timeline.
- Add root cause.
- Add fix section.
- Add redaction verification.

Definition of done:

- HTML report is readable
- JSON report follows schema
- secrets are not present
- report includes artifacts

---

## 18.8 Epic H: Documentation and article

Tasks:

- Write README quickstart.
- Write profile guide.
- Write troubleshooting docs.
- Write CI guide.
- Write flagship article.
- Create images.
- Prepare example pack.

Definition of done:

- new developer can run demo in under 10 minutes
- article gives full context
- example pack is complete
- content passes validation

---

## 19. README Outline

Use this README structure:

```md
# CaptchaAI Workflow Doctor

A diagnostic tool for debugging CAPTCHA-solving workflows from CaptchaAI API request to browser acceptance.

## What it solves

## Responsible use

## Quickstart

## Run the local demo

## Run against your authorized workflow

## Profile configuration

## Understanding reports

## Failure types

## CI integration

## Supported CAPTCHA types

## Roadmap

## Contributing

## Security
```

---

## 20. Flagship Article Outline

## Title

```text
Why CAPTCHA Tokens Work in the API but Fail in the Browser
```

## Search promise

```text
Learn how to debug the full CAPTCHA-solving workflow after token delivery, including sitekey, page URL, polling, token injection, callback execution, token timing, and browser success verification.
```

## Sections

### 1. The real problem: token received, workflow failed

Explain that a solver token is only one part of the workflow.

### 2. The two halves of CAPTCHA solving

- API solve
- Browser/application acceptance

### 3. Common failure points

Table:

| Failure | Symptom | Likely fix |
|---|---|---|
| wrong sitekey | API returns error or rejected token | extract correct widget sitekey |
| wrong page URL | token rejected | use exact page URL |
| token expired | form fails after delay | solve later, submit faster |
| callback not triggered | token exists but page still pending | invoke callback |
| wrong field | token not seen by page | use correct response selector |
| session mismatch | challenge loop | keep browser/session consistent |

### 4. Introducing CaptchaAI Workflow Doctor

Explain repo.

### 5. Install and run demo

Include commands.

### 6. Create your profile

Show YAML example.

### 7. Read the report

Show JSON/HTML report excerpt.

### 8. Fix example: callback not triggered

Show before/after code.

### 9. Add it to CI

Show GitHub Actions snippet.

### 10. Conclusion and CTA

CTA:

```text
Get your CaptchaAI API key and use Workflow Doctor to validate your integration before shipping.
```

---

## 21. Example GitHub Actions Workflow

```yaml
name: CAPTCHA Workflow Doctor

on:
  workflow_dispatch:
  schedule:
    - cron: "0 3 * * *"

jobs:
  captcha-workflow-check:
    runs-on: ubuntu-latest

    env:
      CAPTCHAAI_API_KEY: ${{ secrets.CAPTCHAAI_API_KEY }}
      QA_EMAIL: ${{ secrets.QA_EMAIL }}
      QA_PASSWORD: ${{ secrets.QA_PASSWORD }}

    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        run: |
          pip install captchaai-workflow-doctor
          playwright install chromium

      - name: Run CAPTCHA workflow doctor
        run: |
          captchaai-doctor run \
            --profile profiles/staging-login.yaml \
            --ci \
            --output reports/staging-login.html

      - name: Upload diagnostic report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: captcha-workflow-report
          path: reports/
```

---

## 22. Example Client Outcome

## 22.1 Before using the repo

Client says:

```text
CaptchaAI does not work on our login page.
```

Support has to ask:

- What sitekey did you use?
- What page URL did you use?
- Did you receive a token?
- Did you inject it?
- Did you trigger the callback?
- How long did you wait?
- Did you reuse the token?
- Did the browser submit after injection?
- What error did the page show?

This is slow and unclear.

## 22.2 After using the repo

Client sends:

```text
Root cause: callback_not_triggered
Report: reports/staging-login.html
Trace: reports/staging-login-trace.zip
```

Support can immediately answer:

```text
CaptchaAI returned the token successfully. Your browser workflow injected the token but did not invoke the page callback. Add callback invocation and wait for the page state to update before submitting.
```

This is much better.

---

## 23. Strong Differentiators

This project is stronger than generic CAPTCHA articles because it provides:

1. Full workflow diagnosis, not just API code.
2. Runnable local demos.
3. Real failure taxonomy.
4. HTML/JSON reports.
5. Screenshots and browser traces.
6. CI integration.
7. Safe profile-based configuration.
8. Reusable support artifact.
9. Article + repo + example pack.
10. Practical debugging for real developers.

---

## 24. Risk Management

## 24.1 Safety risk

Risk:

- Users may try to use the tool for unauthorized third-party workflows.

Mitigation:

- Responsible-use policy.

---

## 24.2 Technical risk

Risk:

- Real CAPTCHA providers change browser behavior.

Mitigation:

- Make detection configurable.
- Keep generic profiles simple.
- Avoid overpromising.
- Maintain failure taxonomy.
- Add versioned report schema.

---

## 24.3 Support risk

Risk:

- Users expect the tool to magically solve every page.

Mitigation:

- Position as diagnostic tool, not universal solver.
- Report confidence scores.
- Clearly label unknown failures.
- Provide trace/screenshots for manual debugging.

---

## 24.4 Scope risk

Risk:

- Team overbuilds dashboard/SaaS too early.

Mitigation:

- v1 is CLI-first.
- HTML report is static.
- No hosted dashboard.
- No browser extension.
- No site-specific public flows.

---

## 25. MVP Acceptance Criteria

The MVP is complete when:

- A user can clone the repo.
- A user can run a local demo.
- A user can validate a profile.
- A user can run the doctor with a profile.
- The tool can submit to CaptchaAI.
- The tool can poll for a result.
- The tool can inject a token into a browser flow.
- The tool can verify success/failure.
- The tool can classify at least 8 root causes.
- The tool can generate JSON and HTML reports.
- The tool can run in CI mode.
- README explains safe usage.
- Article explains the full workflow.
- Example pack is runnable.
- No secrets appear in logs or reports.
- No unsafe public site-specific examples are included.

---

## 26. Suggested First Sprint Backlog

## Day 1

- Create repo.
- Add README skeleton.
- Add responsible-use section.
- Add docs/failure-taxonomy.md.
- Add docs/profile-schema.md.
- Add Python package skeleton.
- Add CLI `--help`.

## Day 2

- Implement profile loader.
- Implement profile validator.
- Add sample profiles.
- Add tests for invalid profiles.
- Add `.env.example`.

## Day 3

- Implement CaptchaAI submit client.
- Implement polling client.
- Mock successful result.
- Mock timeout.
- Mock API error.

## Day 4

- Add Playwright browser runner.
- Open local/static demo page.
- Take screenshot.
- Save trace.

## Day 5

- Add local Turnstile-like demo.
- Add token injection simulation.
- Add first JSON report.

End of first sprint goal:

```text
captchaai-doctor run --profile profiles/local-demo-login-turnstile.yaml
```

Should produce:

```text
reports/local-demo-login-turnstile.json
reports/screenshots/01-page-loaded.png
```

---

## 27. Suggested Final Deliverable Package

When complete, publish a package like this:

```text
Public article:
  /why-captcha-tokens-work-api-fail-browser

Public repo:
  github.com/CaptchaAI/captchaai-workflow-doctor

Public examples:
  github.com/CaptchaAI/CaptchaAI-Examples/articles/captchaai-workflow-doctor

Assets:
  hero image
  architecture diagram
  failure taxonomy diagram
  sample report screenshot

Support internal:
  support macro using report root causes
  troubleshooting checklist
  issue template for clients
```

---

## 28. Support Macro Template

Support can ask clients:

```md
Please run CaptchaAI Workflow Doctor against your authorized test workflow and send us:

1. The JSON report
2. The HTML report
3. The trace zip if available
4. The profile YAML with secrets removed

Command:

```bash
captchaai-doctor run \
  --profile profiles/your-flow.yaml \
  --output reports/your-flow.html
```

The report will help us see whether the issue is API submission, polling, token lifecycle, browser injection, callback execution, or page validation.
```

---

## 29. Issue Template

```md
## Workflow Doctor Report

- Tool version:
- CAPTCHA type:
- Root cause:
- Confidence:
- CaptchaAI submit status:
- Poll status:
- Token received:
- Token injected:
- Callback triggered:
- Success condition met:

## Attachments

- JSON report:
- HTML report:
- Trace:
- Screenshots:

## Notes

What did you expect to happen?

What happened instead?
```

---

## 30. Final Recommendation

Build this as a **generic profile-based diagnostic repo**.

Do not build one public repo per website.

Do not publish specific third-party site profiles.

Start with:

1. Turnstile local demo.
2. reCAPTCHA v2 local demo.
3. Python CLI.
4. Node.js example.
5. JSON/HTML reports.
6. Failure taxonomy.
7. CI mode.
8. Flagship article.

The value is not that the repo solves one CAPTCHA once.

The value is that it gives developers and support teams a repeatable way to answer:

> Where exactly did the CAPTCHA workflow fail?

That is the real gap.

