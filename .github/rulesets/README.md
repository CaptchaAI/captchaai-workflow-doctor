# Branch protection for `main`

This repo ships a ready-to-apply ruleset at
[.github/rulesets/protect-main.json](protect-main.json).

It enforces the following on the default branch:

- All changes must arrive via pull request.
- The PR must be up to date with `main` (`strict` status checks).
- Required green status checks:
  - `lint-type-test (3.11)`
  - `lint-type-test (3.12)`
  - `demo-smoke`
  - `secrets-scan`
- Linear history (no merge commits from outside the PR flow).
- No force-push on `main`.
- No deletion of `main`.
- All review threads must be resolved before merge.

## Apply

Both the **branch protection** API and the **rulesets** API require either a
public repository or a paid plan (GitHub Pro / Team / Enterprise) on private
repositories. While this repo is private and on the free plan, GitHub returns
HTTP 403 ("Upgrade to GitHub Pro or make this repository public to enable this
feature.") on `PUT /repos/{owner}/{repo}/branches/{branch}/protection` and on
`POST /repos/{owner}/{repo}/rulesets`.

Once the repository is public (or upgraded), apply the ruleset with:

```powershell
gh api -X POST repos/CaptchaAI/captchaai-workflow-doctor/rulesets `
  --input .github/rulesets/protect-main.json
```

To verify it took:

```powershell
gh api repos/CaptchaAI/captchaai-workflow-doctor/rulesets
git push --dry-run --force origin main   # must be rejected
```
