# Changelog

All notable changes to this project. Evidence tags follow the README (SYNTHETIC / REPORTED / TARGET / UNRUN).

## 0.1.0 (unreleased; date set when tagged)

First public release candidate. All numbers are SYNTHETIC.

### Added
- Static GitHub Pages demo (`scripts/build_site.py`, `.github/workflows/pages.yml`): the example capsule, its SYNTHETIC replay as an inline SVG, and five deliberately broken capsules with the validator's own messages. No JavaScript, no external requests. 4 builder tests.
- README sections: Quickstart, Limitations, How to cite.
- Governance and security files: `SECURITY.md` (GitHub private vulnerability reporting; no email or phone), `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1), `.github/CODEOWNERS`, issue and pull request templates, `.github/dependabot.yml` (GitHub Actions updates), `.zenodo.json` (community `spark-ai-nlp`), `CHANGELOG.md`.
- README sections: What it is / What it is NOT, Evidence tags, Security.
- Initial import of the prototype: `failure_capsules.py`, the SYNTHETIC seed-417 example capsule, unit tests.

### Changed
- Copyright line names Jean-François Brisson, Spark AI NLP (licence stays MIT).
- CITATION.cff and .zenodo.json: full affiliation (Spark AI NLP, Fredericton, New Brunswick, Canada), version 0.1.0, Pages link.
- CI runs on every branch with warnings as errors and builds the Pages demo. Tests: 27 (SYNTHETIC).
- README converted from PDF; replay described as deterministic on CPython 3.x.

### Fixed
- Oversized integers (> 2**53) are validation errors instead of `OverflowError`.
- The CLI reports unreadable files (not UTF-8, malformed or excessively nested JSON) with exit code 2 instead of a traceback.
- `baseline`, `noise_stddev` and `drift_per_step` are bounded to |x| <= 1e9; replay output is always finite.
- `coarse_features`: at most 32 entries, keys at most 80 characters, number-list values rejected (heuristic).
- Consistent exit codes: 0 valid, 1 invalid, 2 unreadable.
