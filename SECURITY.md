# Security Policy

## Reporting a vulnerability

If you discover a security issue in CaptchaAI Workflow Doctor, please **do not** open a public GitHub issue. Instead, email security@captchaai.com (or the maintainer-provided private channel) with:

- a clear description of the issue
- steps to reproduce
- the affected version / commit
- any suggested mitigation

We will acknowledge receipt within 3 business days and aim to provide a status update within 10 business days.

## Secrets handling

This project must never accept API keys, tokens, passwords, or session cookies inside profile YAML files. Provide secrets via environment variables or a local `.env` file (see `.env.example`). The validator rejects YAML profiles that contain key-shaped strings.

## Scope

CaptchaAI Workflow Doctor is for diagnostic testing of CAPTCHA workflows on systems you own or are authorized to test. See [README.md](README.md#responsible-use).
