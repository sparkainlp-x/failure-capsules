# Security Policy

**Please do not open a public issue for security problems.**

## Reporting a vulnerability

Use GitHub **private vulnerability reporting**: open the repository's **Security** tab and click
**Report a vulnerability**. The report is visible only to the maintainer until an advisory is
published.

This repository is currently private. GitHub offers private vulnerability reporting only on
public repositories, so while it stays private the form is not available. Collaborators with
access should report privately to the repository owner (@sparkainlp-x) through GitHub instead
of opening an issue. Once the repository is public, the Security tab form is the only
supported channel. No email address or phone number is used for security reports.

Please include the affected file(s) and commit or tag, a minimal reproduction, and the
security impact as you understand it. Avoid publishing exploit details until a fix and
disclosure timeline have been agreed. We aim to acknowledge reports within 7 days (TARGET).

## Scope

Failure Capsules is a standard-library research prototype. Invalid input is rejected by
design (fail closed): the validator returns errors, `generate_replay` raises `ValueError`, and
the CLI exits `1` (invalid) or `2` (unreadable) instead of crashing. In scope:

- a capsule that should be invalid but is silently accepted, including forbidden raw-data
  keys that pass, or an unhandled exception/traceback on crafted input;
- non-finite or unbounded replay output from a recipe that passes validation;
- CI workflow issues (unsafe triggers, secret exposure).

Out of scope: sensitive content in free text or disguised keys (the validator is a format
guard, not a privacy scanner; see README), findings that need a compromised developer
machine, and upstream issues in GitHub Actions.

## Supported versions

Only the current `main` branch and the latest release receive fixes.
