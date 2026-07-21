"""Runs the remaining published fixtures: SCOPE, DNS wildcard, RESUME, FAILURE."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "recon-engine"))

from rules import (
    scope_cidr, scope_hostname, scope_port,
    dns_wildcard, next_step, tool_failure_decision,
)

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = json.loads((ROOT / "parser-fixtures.json").read_text(encoding="utf-8"))["fixtures"]


class ScopeFixtureTests(unittest.TestCase):
    def test_scope_fixtures(self):
        for fx in FIXTURES:
            kind = fx.get("kind")
            if kind == "cidr":
                got = scope_cidr(fx["scope"], fx["candidate"])
            elif kind == "hostname":
                got = scope_hostname(fx["scope"], fx["candidate"])
            elif kind == "port":
                got = scope_port(fx["scope"], fx["candidate"])
            else:
                continue
            with self.subTest(fixture=fx["id"]):
                self.assertEqual(got, fx["expected"])


class DnsWildcardFixtureTests(unittest.TestCase):
    def test_dns_fixtures(self):
        for fx in FIXTURES:
            if fx.get("kind") == "dns":
                with self.subTest(fixture=fx["id"]):
                    got = dns_wildcard(fx["random_responses"], fx["candidate_response"])
                    self.assertEqual(got, fx["expected"])


class ResumeFixtureTests(unittest.TestCase):
    def test_resume_fixtures(self):
        for fx in FIXTURES:
            if fx.get("kind") == "checkpoint":
                with self.subTest(fixture=fx["id"]):
                    got = next_step(fx["completed"], fx["pending"])
                    self.assertEqual(got, fx["expected_next"])


class FailureFixtureTests(unittest.TestCase):
    def test_failure_fixtures(self):
        for fx in FIXTURES:
            if fx.get("kind") == "tool_exit":
                with self.subTest(fixture=fx["id"]):
                    got = tool_failure_decision(fx["exit_code"], fx["fallback_available"])
                    self.assertEqual(got, fx["expected"])


if __name__ == "__main__":
    unittest.main()
