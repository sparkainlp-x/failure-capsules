# Contributing

Changes must keep the capsule schema fail-closed: unknown fields are rejected, replay values
stay synthetic and finite, and invalid input produces validation errors (never a traceback).
Changing the schema requires bumping `SCHEMA_VERSION` and updating `examples/`, the README
and the tests together.

- For anything larger than a typo, open an issue first so we can agree on scope.
- Keep pull requests focused (one topic each). `main` changes land through pull requests,
  squash-merged, with CI passing on Python 3.10-3.13.
- Run `python -m unittest discover -s tests -v` before opening a pull request. Changes to
  validation or replay behavior need both an accepting and a rejecting test case.
- Standard library only; do not add runtime dependencies without discussion.

## Claim hygiene (fail-closed)

Tag every number as **SYNTHETIC**, **REPORTED** (measured on named public data, with seed,
configuration, environment and command), **TARGET** or **UNRUN**. Replay output is always
SYNTHETIC. Do not describe the validator as anonymization, de-identification, certified
privacy, or a safety or medical system, and do not add claims of production readiness,
revenue, peer review or hardware results.

## Privacy

Never commit real incident data, sensor measurements, device or user identifiers,
credentials, personal email addresses or phone numbers. Use your GitHub noreply address as
commit author.

## Licensing

Contributions are accepted under the repository's MIT license. By submitting a pull request
you confirm that you have the right to contribute the code or text. All participation is
covered by the [Code of Conduct](CODE_OF_CONDUCT.md).
