"""Scope guard: decides whether a destination is authorized before any socket opens."""

import csv


def load_scope(path):
    """Read scope.csv and return (in_rules, out_rules) as two lists of assets."""
    in_rules = []
    out_rules = []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            asset = row["asset"]
            decision = row["scope"].strip().upper()
            if decision == "IN":
                in_rules.append(asset)
            elif decision == "OUT":
                out_rules.append(asset)
    return in_rules, out_rules


class ScopeGuard:
    """Holds the parsed scope and decides if a destination is authorized."""

    LOOPBACK = "127.0.0.1"

    def __init__(self, scope_path):
        in_rules, out_rules = load_scope(scope_path)
        self.allowed_ports = set()
        for asset in in_rules:
            host, _, port = asset.partition(":")
            if host == self.LOOPBACK and port.isdigit():
                self.allowed_ports.add(int(port))

    def is_allowed(self, host, port):
        """Return True only if this exact host+port is explicitly authorized."""
        if host != self.LOOPBACK:
            return False
        return int(port) in self.allowed_ports
    