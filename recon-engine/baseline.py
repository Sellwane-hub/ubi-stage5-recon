"""Wildcard baselining: decide whether a vhost response is genuine content or
just the target's wildcard (catch-all) noise.

A response that matches the established baseline (same status, size, and body
hash) is wildcard noise and is SUPPRESSED. A response that differs in any of
those is genuine and is RETAINED. This lets the engine confirm the real vhost
without being fooled by the catch-all page, and without hiding a real vhost.
"""

import hashlib


def body_hash(body):
    """Return a short stable hash of a response body (bytes or str)."""
    if isinstance(body, str):
        body = body.encode("utf-8")
    return hashlib.sha256(body).hexdigest()[:12]


def response_signature(status, body):
    """Build a comparable signature from a response: (status, length, hash)."""
    if isinstance(body, str):
        length = len(body.encode("utf-8"))
    else:
        length = len(body)
    return {"status": status, "bytes": length, "body_hash": body_hash(body)}


def classify(baseline, candidate):
    """Compare a candidate signature to the baseline.

    Returns 'suppress' if the candidate matches the baseline (wildcard noise),
    or 'retain' if it differs (genuine content).
    """
    same = (
        baseline["status"] == candidate["status"]
        and baseline["bytes"] == candidate["bytes"]
        and baseline["body_hash"] == candidate["body_hash"]
    )
    return "suppress" if same else "retain"
