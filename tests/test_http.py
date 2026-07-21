"""Tests for the HTTP/vhost prober. The parse test needs no network; the live
test requires the local lab running."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "recon-engine"))

from scope import ScopeGuard
from ledger import RequestLedger
from net import SafeRequester
from signal_probe import discover_signal
from http_probe import parse_http_response, probe_http

ROOT = Path(__file__).resolve().parent.parent
SCOPE = ROOT / "lab-runtime" / "scope.csv"


class HttpParseTests(unittest.TestCase):
    def test_parses_status_headers_body(self):
        raw = b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nhello"
        status, headers, body = parse_http_response(raw)
        self.assertEqual(status, 200)
        self.assertEqual(headers["content-type"], "text/plain")
        self.assertEqual(body, "hello")

    def test_handles_401(self):
        raw = b"HTTP/1.1 401 Unauthorized\r\n\r\nauth required"
        status, _, body = parse_http_response(raw)
        self.assertEqual(status, 401)
        self.assertIn("auth", body)


class HttpProbeLiveTests(unittest.TestCase):
    def setUp(self):
        self.guard = ScopeGuard(SCOPE)
        ledger = RequestLedger(Path(tempfile.mkdtemp()) / "ledger.csv")
        self.req = SafeRequester(self.guard, ledger)
        self.ports = sorted(self.guard.allowed_ports)
        self.http_port = self.ports[0]
        self.signal_port = self.ports[1]

    def test_full_chain_confirms_vhost_and_finds_creds(self):
        sig = discover_signal(self.req, "127.0.0.1", self.signal_port)
        http = probe_http(self.req, "127.0.0.1", self.http_port, sig["vhost"])
        # the genuine vhost must differ from the wildcard baseline
        self.assertEqual(http["baseline_class"], "retain")
        # credentials must be discovered behind the real vhost
        self.assertIsNotNone(http["credentials"].get("username"))
        self.assertIsNotNone(http["credentials"].get("password"))


if __name__ == "__main__":
    unittest.main()
