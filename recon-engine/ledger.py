"""Request ledger: an append-only record of every request the engine makes.

Each entry is written BEFORE the request is sent, so an interrupted run never
leaves an unrecorded request. This is the evidence used to prove zero decoy
traffic and that the request budget was respected.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path


def utc_now():
    """Return the current UTC time as an ISO-8601 string ending in Z."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class RequestLedger:
    FIELDS = ("sequence", "sent_at", "host", "port", "protocol", "resource", "result")

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.sequence = 0
        # write the header row once, fresh
        with self.path.open("w", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerow(self.FIELDS)

    def record(self, host, port, protocol, resource, result):
        """Append one request to the ledger and return its sequence number."""
        self.sequence += 1
        row = (self.sequence, utc_now(), host, port, protocol, resource, result)
        with self.path.open("a", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerow(row)
        return self.sequence
