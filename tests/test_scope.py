"""Tests for the scope guard. Run with: python3 -m unittest tests.test_scope"""

import sys
import unittest
from pathlib import Path

# make the recon-engine folder importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "recon-engine"))

from scope import ScopeGuard


class ScopeGuardTests(unittest.TestCase):
    def setUp(self):
        # runs before each test; builds a fresh guard from the real scope file
        scope_path = Path(__file__).resolve().parent.parent / "lab-runtime" / "scope.csv"
        self.guard = ScopeGuard(scope_path)

    def test_in_ports_are_allowed(self):
        self.assertTrue(self.guard.is_allowed("127.0.0.1", 18098))
        self.assertTrue(self.guard.is_allowed("127.0.0.1", 23319))

    def test_decoy_is_denied(self):
        # the OUT decoy must never be allowed
        self.assertFalse(self.guard.is_allowed("127.0.0.1", 26465))

    def test_unknown_port_is_denied(self):
        # deny-by-default: a port never marked IN is rejected
        self.assertFalse(self.guard.is_allowed("127.0.0.1", 9999))

    def test_non_loopback_is_denied(self):
        # the 0.0.0.0/0 OUT rule: nothing off-loopback is allowed
        self.assertFalse(self.guard.is_allowed("192.0.2.5", 18098))


if __name__ == "__main__":
    unittest.main()
