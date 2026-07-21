"""Tests for the signal-service parser."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "recon-engine"))

from scope import ScopeGuard
from ledger import RequestLedger
from net import SafeRequester
from signal_probe import discover_signal, parse_kv

ROOT = Path(__file__).resolve().parent.parent
SCOPE = ROOT / "lab-runtime" / "scope.csv"


class ParseKvTests(unittest.TestCase):
    def test_parses_spaced_and_unspaced(self):
        self.assertEqual(parse_kv("a=1; b=2"), {"a": "1", "b": "2"})
        self.assertEqual(parse_kv("a=1;b=2"), {"a": "1", "b": "2"})
        self.assertEqual(parse_kv("a = 1 ; b = 2"), {"a": "1", "b": "2"})

    def test_ignores_parts_without_equals(self):
        self.assertEqual(parse_kv("hello; a=1"), {"a": "1"})


class SignalDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.guard = ScopeGuard(SCOPE)
        ledger = RequestLedger(Path(tempfile.mkdtemp()) / "ledger.csv")
        self.req = SafeRequester(self.guard, ledger)
        self.port = sorted(self.guard.allowed_ports)[1]  # signal port (higher of the two)

    def test_discovers_commands_and_route(self):
        result = discover_signal(self.req, "127.0.0.1", self.port)
        # CAPS must advertise ROUTE, and ROUTE must yield a vhost + key
        self.assertIn("ROUTE", result["commands"])
        self.assertIsNotNone(result["vhost"])
        self.assertIsNotNone(result["route_key"])


if __name__ == "__main__":
    unittest.main()
