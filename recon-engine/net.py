"""Safe-request layer: the single gate every network call passes through.

No prober opens a socket directly. They call open_connection(), which enforces
scope BEFORE any socket is created and records every attempt (allowed or denied)
in the request ledger. This makes 'zero packets to the decoy' a structural
guarantee, not a matter of trusting each prober to remember to check.
"""

import socket


class ScopeViolation(Exception):
    """Raised when a request targets a destination that is not authorized."""


class SafeRequester:
    def __init__(self, guard, ledger, timeout=4.0):
        self.guard = guard
        self.ledger = ledger
        self.timeout = timeout

    def check(self, host, port, protocol, resource):
        """Enforce scope. Record the attempt. Raise if denied. No socket here."""
        if not self.guard.is_allowed(host, port):
            self.ledger.record(host, port, protocol, resource, "DENIED")
            raise ScopeViolation(f"{host}:{port} is out of scope; refused before any packet")
        self.ledger.record(host, port, protocol, resource, "SENT")

    def open_connection(self, host, port, protocol, resource):
        """Check scope first, then open a TCP connection only if authorized."""
        self.check(host, port, protocol, resource)
        return socket.create_connection((host, port), timeout=self.timeout)
