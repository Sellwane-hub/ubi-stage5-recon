"""Engine orchestration: runs the full discovery chain and collects raw output,
normalized records, and errors. Discovery only -- it never fetches the flag.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from scope import ScopeGuard
from ledger import RequestLedger
from net import SafeRequester, ScopeViolation
from ports import probe_ports
from signal_probe import discover_signal
from http_probe import probe_http
from normalize import make_record, normalize, result_hash, write_jsonl


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_discovery(target, scope_path, output_dir, rate=25):
    """Run the full discovery chain, writing raw output, normalized records,
    ledger, and errors under output_dir. Returns a summary dict."""
    out = Path(output_dir)
    (out / "raw").mkdir(parents=True, exist_ok=True)
    (out / "normalized").mkdir(parents=True, exist_ok=True)

    started = utc_now()
    guard = ScopeGuard(scope_path)
    ledger = RequestLedger(out / "request-ledger.csv")
    req = SafeRequester(guard, ledger)
    errors = []   # genuine problems (e.g. scope violations)
    notes = []    # expected observations (e.g. a port that isn't the signal service)
    records = []

    def save_raw(tool, name, content):
        d = out / "raw" / tool
        d.mkdir(parents=True, exist_ok=True)
        path = d / name
        path.write_text(content, encoding="utf-8")
        return str(path.relative_to(out))

    in_ports = sorted(guard.allowed_ports)

    # 1. port discovery
    port_findings = probe_ports(req, target, in_ports)
    raw_ports = save_raw("port-probe", "ports.json", json.dumps(port_findings, indent=2))
    for f in port_findings:
        if f["state"] == "open":
            records.append(make_record(
                target, f["port"], f["transport"], "unknown",
                "port-probe", raw_ports, 0.6, "open port", utc_now()))

    open_ports = [f["port"] for f in port_findings if f["state"] == "open"]

    # 2. signal discovery (probe each open port; only one speaks the line protocol)
    vhost = None
    signal_port = None
    for port in open_ports:
        try:
            sig = discover_signal(req, target, port)
            if sig.get("vhost"):
                vhost = sig["vhost"]
                signal_port = port
                raw_sig = save_raw("signal", "signal.json", json.dumps(sig, indent=2))
                records.append(make_record(
                    target, port, "tcp", "signal", "signal-probe", raw_sig,
                    0.9, f"vhost={vhost}; route_key discovered", utc_now(),
                    extra={"vhost": vhost, "commands": sig.get("commands", [])}))
                break
        except ScopeViolation as exc:
            errors.append({"stage": "signal", "port": port, "error": str(exc)})
        except OSError as exc:
            # expected: this open port does not speak the signal protocol
            notes.append({"stage": "signal", "port": port,
                          "observation": "not a signal service", "detail": str(exc)})

    # 3. http/vhost discovery (skip the signal port -- it does not speak HTTP)
    for port in open_ports:
        if vhost is None:
            break
        if port == signal_port:
            continue
        try:
            http = probe_http(req, target, port, vhost)
            if http["baseline_class"] == "retain":
                raw_http = save_raw("http", "http.json", json.dumps(http, indent=2))
                records.append(make_record(
                    target, port, "tcp", "http", "http-probe", raw_http,
                    0.9, f"genuine vhost confirmed ({http['baseline_class']})", utc_now(),
                    extra={"vhost": vhost, "baseline_class": http["baseline_class"],
                           "paths": list(http["paths"].keys()),
                           "credentials_found": bool(http["credentials"].get("username"))}))
            else:
                notes.append({"stage": "http", "port": port,
                              "observation": "response matches wildcard baseline (suppressed)"})
        except ScopeViolation as exc:
            errors.append({"stage": "http", "port": port, "error": str(exc)})
        except OSError as exc:
            notes.append({"stage": "http", "port": port,
                          "observation": "not an http service", "detail": str(exc)})

    # write normalized records, errors, and notes
    normalized = normalize(records)
    write_jsonl(records, out / "normalized" / "assets.jsonl")
    with (out / "errors.jsonl").open("w", encoding="utf-8") as h:
        for e in errors:
            h.write(json.dumps(e, sort_keys=True) + "\n")
    with (out / "notes.jsonl").open("w", encoding="utf-8") as h:
        for n in notes:
            h.write(json.dumps(n, sort_keys=True) + "\n")

    ended = utc_now()
    return {
        "started_at": started,
        "ended_at": ended,
        "target": target,
        "records": len(normalized),
        "result_hash": result_hash(records),
        "request_count": ledger.sequence,
        "errors": len(errors),
        "notes": len(notes),
    }
