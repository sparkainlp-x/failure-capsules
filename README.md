# Failure Capsules

Failure Capsules is a compact, offline Python prototype for turning an incident into a
bug report with a deterministic synthetic replay, without including original sensor
measurements. A capsule records software and configuration versions, a timestamp policy,
broad device/channel-group categories, an event class, categorical coarse features, a
seeded synthetic replay recipe, expected and observed behavior, and a checklist.

Live demo (static, no JavaScript, no network requests):
[sparkainlp-x.github.io/failure-capsules](https://sparkainlp-x.github.io/failure-capsules/).
It shows the example capsule, its SYNTHETIC replay drawn from the recipe, and five
deliberately broken capsules with the validator's own error messages.

## Quickstart

Requires Python 3.10 or newer; uses only the Python standard library. No install step:

```
git clone https://github.com/sparkainlp-x/failure-capsules
cd failure-capsules
python3 failure_capsules.py demo
python3 failure_capsules.py validate examples/example_capsule.json
```

## What it is / What it is NOT

- **Is:** a standard-library format guard for compact incident capsules, plus a seeded
  synthetic replay generator. Research prototype.
- **Is NOT:** an anonymizer, de-identification tool or privacy scanner; a certified safety or
  medical system; a production service. It never reads device or incident storage.

## Evidence tags

Every number in this repository is tagged: **SYNTHETIC** (generated, e.g. replay values,
the example capsule, test fixtures), **REPORTED** (measured on named public data),
**TARGET** (a goal) or **UNRUN** (not executed). Everything here is SYNTHETIC; use on real
incident workflows is UNRUN. Definitions: [sparkainlp-x/.github](https://github.com/sparkainlp-x/.github#evidence-tags).

## Run it

From this directory:

```
python3 failure_capsules.py demo
python3 failure_capsules.py validate examples/example_capsule.json
python3 -W error -m unittest discover -s tests -v
python3 scripts/build_site.py _site      # rebuild the Pages demo into _site/index.html
```

`demo` validates the checked-in example and prints the first eight values from a
synthetic replay. The replay is deterministic on CPython 3.x for the same recipe and seed
(it uses `random.Random` / `gauss`; other Python implementations may produce different
values). Generate a replay in Python with the same recipe and seed:

```python
from failure_capsules import generate_replay

values = generate_replay(
    seed=417,
    points=32,
    baseline=100.0,
    noise_stddev=0.25,
    drift_start=20,
    drift_per_step=1.0,
)
```

Exit codes for both commands: `0` valid, `1` invalid capsule, `2` file could not be read
or parsed (missing, not UTF-8, malformed or excessively nested JSON).

The generated sequence is artificial and is not derived from an incident recording. The CLI
and library do not access the network or upload files; replay generation uses no incident
input, and the validator reads only the capsule JSON explicitly passed to it. The validator
checks required fields, types, allowed schema keys, timestamp-policy consistency, replay-
recipe bounds, and known forbidden raw-data key names. It is a format guard, not a privacy
scanner: it cannot detect sensitive content hidden in ordinary text or disguised under an
unfamiliar key.

## Capsule contents

See `examples/example_capsule.json` for a valid example (all values are synthetic). The
schema is versioned as `1.0`. Timestamp policies are `exact_utc`, `rounded_minute_utc`,
`rounded_hour_utc`, `relative_offset_seconds`, or `omitted`. Coarse feature values must be
categorical strings; the replay recipe contains only parameters for the declared synthetic
generator. Unknown fields are rejected so accidental additions are visible and require a
deliberate schema update.

Limits enforced by the validator:

- integers must have magnitude at most 2**53;
- `baseline`, `noise_stddev` and `drift_per_step` must have magnitude at most 1e9, and
  `points` at most 10,000, so replay values stay finite;
- `coarse_features`: at most 32 entries, keys and values at most 80 characters each, and
  values that look like a list of numbers (for example `"1.2,3.4,5.6"`) are rejected.
  This is a heuristic, not a guarantee.

There is intentionally no incident identifier field. If an identifier is necessary in a separate
workflow, omit it from the shared capsule or replace it with a carefully managed
pseudonym; a pseudonym can still be linkable. Prefer broad categories and coarse buckets.
Review version strings, timestamps, categories, feature labels, and behavior descriptions
before sharing: metadata and coarse features can still be sensitive or identifying, and free
text may reveal people, locations, or operational details.

## Privacy and security boundary

This prototype does not perform certified anonymization, de-identification, signatures,
encryption, access control, or secure uploads. It does not guarantee anonymization,
confidentiality, or safe disclosure. Do not put original samples, waveforms, measurement
arrays, device/user identifiers, credentials, or other sensitive values into a capsule; do not
treat passing validation as proof that a capsule is safe to publish. Keep original incident
data in its separately governed system, if one exists, and share only a manually reviewed
capsule appropriate for its audience.

The `reproducibility_checklist` fields are self-reported booleans; the tool does not verify them.

## Limitations

- It is a format guard, not a privacy scanner, anonymizer or de-identification tool. It
  cannot detect sensitive content in ordinary text or under an unfamiliar key.
- Every number in this repository is SYNTHETIC. Use on real incident workflows is UNRUN,
  and no privacy, detection or performance metric is claimed.
- Replay determinism is stated for CPython 3.x only; other implementations may differ.
- The reproducibility checklist is self-reported and not verified by the tool.
- There are no signatures, encryption or access control; a valid capsule is not proof
  that it is safe to share.

## Project layout

```
failure_capsules.py              validator, replay generator and CLI (stdlib only)
examples/example_capsule.json    SYNTHETIC example capsule (seed 417)
scripts/build_site.py            builds the static Pages demo
tests/                           unit tests (unittest)
```

## Security

Please do not open public issues for vulnerabilities; see [SECURITY.md](SECURITY.md)
(GitHub private vulnerability reporting, no email or phone).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md).

## How to cite

See [CITATION.cff](CITATION.cff). A Zenodo DOI will be listed here after the first release:
`10.5281/zenodo.XXXXXXX` (placeholder).

> Brisson, J.-F. (2026). *Failure Capsules: offline incident capsules with a deterministic
> synthetic replay* (Version 0.1.0) [Computer software]. Spark AI NLP, Fredericton, New
> Brunswick, Canada. https://github.com/sparkainlp-x/failure-capsules

## License

Copyright (c) 2026 Jean-François Brisson, Spark AI NLP.

Released under the MIT License; see [LICENSE](LICENSE).
