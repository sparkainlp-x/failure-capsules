# Changelog

All notable changes to this project. Evidence tags follow the README (SYNTHETIC / REPORTED / TARGET / UNRUN).

## Unreleased

### Added
- Governance and security files: `SECURITY.md` (GitHub private vulnerability reporting; no email or phone), `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1), `.github/CODEOWNERS`, issue and pull request templates, `.github/dependabot.yml` (GitHub Actions updates), `.zenodo.json` (community `spark-ai-nlp`), `CHANGELOG.md`.
- README sections: What it is / What it is NOT, Evidence tags, Security.

## 0.1.0 — 2026-09-29

### Added
- Initial import of the prototype: `failure_capsules.py`, the SYNTHETIC seed-417 example capsule, 9 unit tests.

### Fixed
- Oversized integers (> 2**53) are validation errors instead of `OverflowError`.
- The CLI reports unreadable files (not UTF-8, malformed or excessively nested JSON) with exit code 2 instead of a traceback.
- `baseline`, `noise_stddev` and `drift_per_step` are bounded to |x| <= 1e9; replay output is always finite.
- `coarse_features`: at most 32 entries, keys at most 80 characters, number-list values rejected (heuristic).
- Consistent exit codes: 0 valid, 1 invalid, 2 unreadable.

### Changed
- README converted from PDF; replay described as deterministic on CPython 3.x. MIT license, CITATION.cff, CI on Python 3.10-3.13. Tests: 23 (SYNTHETIC).
