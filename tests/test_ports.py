"""Tests for the port prober. Requires the local lab to be running."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "recon-engine"))

from scope import ScopeGuard
from ledger import RequestLedger
from net import SafeRequester
from ports import probe_ports

ROOT = Path(__file__).resolve().parent.parent
SCOPE = ROOT / "lab-runtime" / "scope.csv"


class PortProbeTests(unittest.TestCase):
    def setUp(self):
        self.guard = ScopeGuard(SCOPE)
        ledger = RequestLedger(Path(tempfile.mkdtemp()) / "ledger.csv")
        self.req = SafeRequester(self.guard, ledger)
        # read the authorized ports straight from the guard
        self.in_ports = sorted(self.guard.allowed_ports)

    def test_decoy_is_refused_not_scanned(self):
        # even when asked to scan the decoy, it must come back 'refused'
        findings = probe_ports(self.req, "127.0.0.1", [26465])
        self.assertEqual(findings[0]["state"], "refused")

    def test_authorized_ports_are_probed(self):
        findings = probe_ports(self.req, "127.0.0.1", self.in_ports)
        states = {f["port"]: f["state"] for f in findings}
        # every authorized port should be probed (open if lab running, closed if not)
        for port in self.in_ports:
            self.assertIn(states[port], {"open", "closed"})
            self.assertNotEqual(states[port], "refused")


if __name__ == "__main__":
    unittest.main()
