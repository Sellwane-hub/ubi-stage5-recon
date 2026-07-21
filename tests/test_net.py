"""Tests for the safe-request layer (scope enforcement gate)."""

import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "recon-engine"))

from scope import ScopeGuard
from ledger import RequestLedger
from net import SafeRequester, ScopeViolation


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.reader(handle))


class SafeRequesterTests(unittest.TestCase):
    def setUp(self):
        scope_path = Path(__file__).resolve().parent.parent / "lab-runtime" / "scope.csv"
        self.guard = ScopeGuard(scope_path)
        self.ledger_path = Path(tempfile.mkdtemp()) / "ledger.csv"
        self.ledger = RequestLedger(self.ledger_path)
        self.req = SafeRequester(self.guard, self.ledger)

    def test_allowed_target_passes_check(self):
        # should not raise
        self.req.check("127.0.0.1", 18098, "http", "/")

    def test_decoy_raises_scope_violation(self):
        with self.assertRaises(ScopeViolation):
            self.req.check("127.0.0.1", 26465, "http", "/")

    def test_denied_attempt_is_logged(self):
        try:
            self.req.check("127.0.0.1", 26465, "http", "/")
        except ScopeViolation:
            pass
        rows = read_rows(self.ledger_path)
        # last row should be the DENIED decoy attempt
        self.assertEqual(rows[-1][2], "127.0.0.1")
        self.assertEqual(rows[-1][3], "26465")
        self.assertEqual(rows[-1][6], "DENIED")


if __name__ == "__main__":
    unittest.main()
