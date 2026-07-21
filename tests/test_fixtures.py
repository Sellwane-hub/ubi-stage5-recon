"""Runs the published parser-fixtures.json cases against the engine's logic.

These are the exact acceptance fixtures the graders use, so passing them here
is direct evidence for the published-suite gate. We start with the wildcard
vhost cases and extend to other fixture kinds as each module is built.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "recon-engine"))

from baseline import classify

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = json.loads((ROOT / "parser-fixtures.json").read_text(encoding="utf-8"))["fixtures"]


def fixtures_of_kind(kind):
    return [f for f in FIXTURES if f.get("kind") == kind]


class WildcardVhostFixtureTests(unittest.TestCase):
    def test_vhost_fixtures(self):
        cases = fixtures_of_kind("vhost")
        self.assertTrue(cases, "expected at least one vhost fixture")
        for fx in cases:
            with self.subTest(fixture=fx["id"]):
                got = classify(fx["baseline"], fx["candidate"])
                self.assertEqual(got, fx["expected"])


if __name__ == "__main__":
    unittest.main()
