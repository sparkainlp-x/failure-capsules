"""Tests for the static Pages builder (scripts/build_site.py)."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("build_site", ROOT / "scripts" / "build_site.py")
build_site = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_site)


class BuildSiteTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.out = Path(self._tmp.name)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(build_site.main([str(self.out)]), 0)
        self.page = (self.out / "index.html").read_text(encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_page_is_self_contained(self) -> None:
        self.assertNotIn("<script", self.page.lower())
        # The only absolute URL is the plain link to the source repository.
        urls = set(re.findall(r'(?:src|href)="(https?://[^"]+)"', self.page))
        self.assertEqual(urls, {"https://github.com/sparkainlp-x/failure-capsules"})
        self.assertIn("Content-Security-Policy", self.page)

    def test_every_broken_case_is_rejected_on_the_page(self) -> None:
        self.assertEqual(self.page.count("Rejected, exit code 1"), 5)
        self.assertIn("forbidden raw-measurement/data key", self.page)

    def test_replay_is_labelled_synthetic_and_complete(self) -> None:
        self.assertIn("SYNTHETIC", self.page)
        self.assertEqual(self.page.count("<circle "), 32)
        self.assertIn("prefers-reduced-motion", self.page)

    def test_build_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as other:
            with contextlib.redirect_stdout(io.StringIO()):
                build_site.main([other])
            again = (Path(other) / "index.html").read_text(encoding="utf-8")
        self.assertEqual(self.page, again)


if __name__ == "__main__":
    unittest.main()
