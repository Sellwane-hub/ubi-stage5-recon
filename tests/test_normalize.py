"""Tests for normalization: determinism, dedup, and the published DEDUPE fixtures."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "recon-engine"))

from normalize import make_record, normalize, result_hash

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = json.loads((ROOT / "parser-fixtures.json").read_text(encoding="utf-8"))["fixtures"]


def make(target, port, protocol, service, observed_at):
    return make_record(target, port, protocol, service, "test", "raw/x", 0.9, "", observed_at)


class DeterminismTests(unittest.TestCase):
    def test_hash_ignores_timestamp_and_order(self):
        a = make("127.0.0.1", 18098, "tcp", "http", "2026-01-01T00:00:00Z")
        b = make("127.0.0.1", 23319, "tcp", "signal", "2026-01-01T00:00:01Z")
        a2 = make("127.0.0.1", 18098, "tcp", "http", "2026-07-21T14:00:00Z")
        b2 = make("127.0.0.1", 23319, "tcp", "signal", "2026-07-21T14:00:05Z")
        self.assertEqual(result_hash([a, b]), result_hash([b2, a2]))

    def test_dedupe_collapses_identical(self):
        a = make("127.0.0.1", 443, "tcp", "https", "t")
        self.assertEqual(len(normalize([a, a])), 1)


class DedupeFixtureTests(unittest.TestCase):
    def test_published_dedupe_fixtures(self):
        cases = [f for f in FIXTURES if f.get("kind") == "records"]
        self.assertTrue(cases)
        for fx in cases:
            with self.subTest(fixture=fx["id"]):
                # each input_id looks like "host:443:tcp" -> treat as identity
                records = []
                for i, ident in enumerate(fx["input_ids"]):
                    host, port, proto = ident.split(":")
                    records.append(make(host, int(port), proto, "svc", f"t{i}"))
                self.assertEqual(len(normalize(records)), fx["expected_count"])


if __name__ == "__main__":
    unittest.main()
