"""Tests for the request ledger."""

import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "recon-engine"))

from ledger import RequestLedger


def read_rows(path):
    """Read all rows from a CSV file, closing it properly."""
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.reader(handle))


class RequestLedgerTests(unittest.TestCase):
    def setUp(self):
        # a throwaway temp file so tests never touch real run data
        self.tmp = Path(tempfile.mkdtemp()) / "ledger.csv"
        self.ledger = RequestLedger(self.tmp)

    def test_header_written_on_init(self):
        rows = read_rows(self.tmp)
        self.assertEqual(rows[0], list(RequestLedger.FIELDS))

    def test_records_increment_sequence(self):
        self.assertEqual(self.ledger.record("127.0.0.1", 18098, "http", "/", 200), 1)
        self.assertEqual(self.ledger.record("127.0.0.1", 23319, "signal", "ROUTE", 200), 2)

    def test_rows_persist_to_disk(self):
        self.ledger.record("127.0.0.1", 18098, "http", "/", 200)
        rows = read_rows(self.tmp)
        # header + 1 data row
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][2], "127.0.0.1")


if __name__ == "__main__":
    unittest.main()
