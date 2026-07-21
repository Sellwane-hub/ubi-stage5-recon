"""Normalization: fold all prober outputs into one versioned record schema,
deduplicate deterministically, and compute a stable result hash.

The result hash is computed over the STABLE discovery facts only (target, port,
protocol, service, vhost, classifications) and deliberately EXCLUDES volatile
fields like observed_at and run timestamps. This is what lets an interrupted or
fallback run produce the same result hash as an uninterrupted run: the facts
discovered are identical even though the timing differs.
"""

import hashlib
import json

SCHEMA_VERSION = "1.0"

# fields that are evidence but must NOT influence the deterministic result hash
VOLATILE_FIELDS = ("observed_at",)


def make_record(target, port, protocol, service, source_tool, source_file,
                confidence, notes, observed_at, extra=None):
    """Build one normalized record with all required interface fields."""
    record = {
        "schema_version": SCHEMA_VERSION,
        "observed_at": observed_at,
        "target": target,
        "port": port,
        "protocol": protocol,
        "service": service,
        "source_tool": source_tool,
        "source_file": source_file,
        "confidence": confidence,
        "notes": notes,
    }
    if extra:
        record.update(extra)
    return record


def dedupe_key(record):
    """Deterministic identity of a record: target:port:protocol:service."""
    return f"{record['target']}:{record['port']}:{record['protocol']}:{record['service']}"


def normalize(records):
    """Deduplicate records by identity and return them in a stable sorted order."""
    unique = {}
    for record in records:
        key = dedupe_key(record)
        # first occurrence wins; deterministic because input order is stable
        if key not in unique:
            unique[key] = record
    # sort by the dedupe key so output order never depends on discovery timing
    return [unique[k] for k in sorted(unique)]


def stable_view(records):
    """A canonical, volatile-field-free view of records used for hashing."""
    view = []
    for record in records:
        clean = {k: v for k, v in record.items() if k not in VOLATILE_FIELDS}
        view.append(clean)
    return sorted(view, key=lambda r: dedupe_key(r))


def result_hash(records):
    """Compute a deterministic hash over the stable discovery facts."""
    view = stable_view(records)
    encoded = json.dumps(view, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_jsonl(records, path):
    """Write records one-per-line as JSON (the normalized/assets.jsonl format)."""
    with open(path, "w", encoding="utf-8") as handle:
        for record in normalize(records):
            handle.write(json.dumps(record, sort_keys=True) + "\n")
