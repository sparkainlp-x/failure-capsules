# Failure Capsules

Failure Capsules is a compact, offline Python prototype for turning an incident into a
bug report with a deterministic synthetic replay, without including original sensor
measurements. A capsule records software and configuration versions, a timestamp policy,
broad device/channel-group categories, an event class, categorical coarse features, a
seeded synthetic replay recipe, expected and observed behavior, and a checklist.

## Run it

Requires Python 3.10 or newer; uses only the Python standard library. From this directory:

```
python3 failure_capsules.py demo
python3 failure_capsules.py validate examples/example_capsule.json
python3 -m unittest discover -s tests -v
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

## Project layout

```
failure_capsules.py
examples/example_capsule.json
tests/test_failure_capsules.py
```

## License

MIT, see `LICENSE`.
