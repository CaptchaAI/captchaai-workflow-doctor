<!--
Thanks for the patch. Tick every box before requesting review.
-->

## What

<!-- One-paragraph summary. Link to issue / plan section if relevant. -->

## Why

<!-- The user-visible reason this change exists. -->

## Verification

- [ ] `ruff check .` clean
- [ ] `mypy` clean (strict, on `captchaai_doctor/`)
- [ ] `pytest -m "not e2e"` green
- [ ] `pytest -m e2e` green (real Chromium)
- [ ] Manual `captchaai-doctor` smoke against the relevant demo, where applicable
- [ ] No secret committed; `.secrets/` was not touched
- [ ] `PROGRESS.md` updated if this closes a checkbox
- [ ] `docs/real-e2e-evidence.md` appended if this consumed real CaptchaAI balance

## Notes for the reviewer

<!-- Anything tricky / surprising / out of scope. -->
