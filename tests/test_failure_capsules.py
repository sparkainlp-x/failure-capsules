import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from failure_capsules import generate_replay, main, validate_capsule  # noqa: E402


class CapsuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "examples" / "example_capsule.json").open(encoding="utf-8") as handle:
            cls.example = json.load(handle)

    def test_example_capsule_is_valid(self):
        self.assertEqual(validate_capsule(self.example), [])

    def test_replay_is_deterministic_for_same_seed_and_recipe(self):
        recipe = self.example["replay"]["recipe"]
        first = generate_replay(self.example["replay"]["seed"], **recipe)
        second = generate_replay(self.example["replay"]["seed"], **recipe)
        self.assertEqual(first, second)
        self.assertEqual(len(first), recipe["points"])

    def test_replay_changes_with_seed(self):
        self.assertNotEqual(generate_replay(11), generate_replay(12))

    def test_required_fields_are_enforced(self):
        capsule = json.loads(json.dumps(self.example))
        del capsule["event_class"]
        self.assertTrue(any("event_class is required" in error for error in validate_capsule(capsule)))

    def test_forbidden_raw_measurement_keys_are_rejected_recursively(self):
        capsule = json.loads(json.dumps(self.example))
        capsule["coarse_features"]["Raw_Measurements"] = "should-not-be-here"
        capsule["coarse_features"]["raw_samples"] = [1.0, 2.0]
        errors = validate_capsule(capsule)
        self.assertTrue(any("forbidden raw-measurement/data key" in error for error in errors))
        self.assertGreaterEqual(
            sum("forbidden raw-measurement/data key" in error for error in errors), 2
        )

    def test_malformed_schema_and_non_categorical_features_are_rejected(self):
        capsule = json.loads(json.dumps(self.example))
        capsule["timestamp_policy"]["policy"] = "nearest-ish"
        capsule["coarse_features"]["peak_level_bucket"] = 123.4
        errors = validate_capsule(capsule)
        self.assertTrue(any("timestamp_policy.policy must be" in error for error in errors))
        self.assertTrue(any("coarse_features.peak_level_bucket" in error for error in errors))

    def test_non_string_timestamp_policy_is_rejected_without_crashing(self):
        capsule = json.loads(json.dumps(self.example))
        capsule["timestamp_policy"]["policy"] = ["not", "a", "policy"]
        errors = validate_capsule(capsule)
        self.assertTrue(any("timestamp_policy.policy must be" in error for error in errors))

    def test_unknown_schema_fields_are_rejected(self):
        capsule = json.loads(json.dumps(self.example))
        capsule["unreviewed_extension"] = "unexpected"
        self.assertTrue(any("is not allowed by schema" in error for error in validate_capsule(capsule)))

    def test_malformed_json_shape_is_rejected(self):
        self.assertTrue(validate_capsule(["not", "an", "object"]))

    # --- Fix 5: oversized integers are rejected instead of crashing ---
    def test_huge_integer_recipe_value_is_rejected_without_crashing(self):
        capsule = json.loads(json.dumps(self.example))
        capsule["replay"]["recipe"]["baseline"] = 10**400
        errors = validate_capsule(capsule)
        self.assertTrue(any("replay.recipe.baseline" in error for error in errors))

    def test_huge_integer_relative_timestamp_is_rejected_without_crashing(self):
        capsule = json.loads(json.dumps(self.example))
        capsule["timestamp_policy"] = {"policy": "relative_offset_seconds", "value": 10**400}
        errors = validate_capsule(capsule)
        self.assertTrue(any("timestamp_policy.value" in error for error in errors))

    def test_generate_replay_rejects_huge_integer(self):
        with self.assertRaises(ValueError):
            generate_replay(1, drift_per_step=10**400)

    # --- Fix 6: unreadable files are reported, not tracebacks ---
    def _run_cli(self, *argv):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = main(list(argv))
        return code, err.getvalue()

    def test_non_utf8_file_is_reported_as_unreadable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_bytes(b"\xff\xfe\x00")
            code, err = self._run_cli("validate", str(path))
        self.assertEqual(code, 2)
        self.assertIn("Could not read capsule", err)

    def test_deeply_nested_json_is_reported_as_unreadable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deep.json"
            path.write_text("[" * 100_000, encoding="utf-8")
            code, err = self._run_cli("validate", str(path))
        self.assertEqual(code, 2)
        self.assertIn("Could not read capsule", err)

    # --- Fix 7: recipe magnitudes are bounded so replay stays finite ---
    def test_recipe_magnitude_is_bounded(self):
        capsule = json.loads(json.dumps(self.example))
        capsule["replay"]["recipe"]["baseline"] = 1e308
        capsule["replay"]["recipe"]["drift_per_step"] = 1e308
        errors = validate_capsule(capsule)
        self.assertTrue(any("replay.recipe.baseline must have magnitude" in error for error in errors))
        self.assertTrue(any("replay.recipe.drift_per_step must have magnitude" in error for error in errors))

    def test_generate_replay_rejects_overflowing_recipe(self):
        with self.assertRaises(ValueError):
            generate_replay(1, points=3, baseline=1e308, drift_start=0, drift_per_step=1e308)

    def test_max_bounds_replay_is_finite(self):
        values = generate_replay(1, points=10_000, baseline=1e9, noise_stddev=1e9, drift_start=0, drift_per_step=1e9)
        self.assertTrue(all(abs(v) != float("inf") and v == v for v in values))

    # --- Fix 8: coarse_features keys and number-list values are limited ---
    def test_long_coarse_feature_key_is_rejected(self):
        capsule = json.loads(json.dumps(self.example))
        capsule["coarse_features"]["x" * 5000] = "low"
        errors = validate_capsule(capsule)
        self.assertTrue(any("coarse_features key" in error and "at most" in error for error in errors))

    def test_too_many_coarse_features_are_rejected(self):
        capsule = json.loads(json.dumps(self.example))
        capsule["coarse_features"] = {f"bucket_{i}": "low" for i in range(33)}
        errors = validate_capsule(capsule)
        self.assertTrue(any("at most 32 entries" in error for error in errors))

    def test_numeric_list_feature_value_is_rejected(self):
        for smuggled in ("1.2,3.4,5.6", "101.23; 102.5; 99.8", "1e3 2e3"):
            capsule = json.loads(json.dumps(self.example))
            capsule["coarse_features"]["sensor_value_list"] = smuggled
            errors = validate_capsule(capsule)
            self.assertTrue(any("looks like a list of numbers" in error for error in errors), smuggled)

    def test_categorical_range_labels_are_still_allowed(self):
        capsule = json.loads(json.dumps(self.example))
        capsule["coarse_features"]["duration_bucket"] = "10-20 minutes"
        capsule["coarse_features"]["level_bucket"] = "50"
        self.assertEqual(validate_capsule(capsule), [])

    # --- Fix 9: consistent exit codes (0 valid, 1 invalid, 2 unreadable) ---
    def test_validate_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good.json"
            good.write_text(json.dumps(self.example), encoding="utf-8")
            bad = Path(tmp) / "bad.json"
            invalid = json.loads(json.dumps(self.example))
            del invalid["event_class"]
            bad.write_text(json.dumps(invalid), encoding="utf-8")
            self.assertEqual(self._run_cli("validate", str(good))[0], 0)
            self.assertEqual(self._run_cli("validate", str(bad))[0], 1)
            self.assertEqual(self._run_cli("validate", str(Path(tmp) / "missing.json"))[0], 2)

    def test_demo_exits_zero_with_checked_in_example(self):
        self.assertEqual(self._run_cli("demo")[0], 0)


if __name__ == "__main__":
    unittest.main()
