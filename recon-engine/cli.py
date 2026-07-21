"""Command-line entry point for the recon engine.

Usage:
  recon-engine --target 127.0.0.1 --scope lab-runtime/scope.csv --output run/ --rate 25

Writes run.json (versions, timing, arguments, exit status) alongside the raw,
normalized, ledger, errors, and notes output produced by the discovery engine.
"""

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from engine import run_discovery


def main(argv=None):
    parser = argparse.ArgumentParser(prog="recon-engine",
                                     description="Scope-safe loopback recon engine (discovery only).")
    parser.add_argument("--target", required=True, help="target host, e.g. 127.0.0.1")
    parser.add_argument("--scope", required=True, help="path to scope.csv")
    parser.add_argument("--output", required=True, help="output directory")
    parser.add_argument("--rate", type=int, default=25, help="max requests per second")
    args = parser.parse_args(argv)

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    exit_status = 0
    summary = None
    try:
        summary = run_discovery(args.target, args.scope, args.output, rate=args.rate)
    except Exception as exc:  # any unexpected failure -> nonzero exit, recorded
        exit_status = 1
        summary = {"error": str(exc)}

    run_meta = {
        "tool": "recon-engine",
        "schema_version": "1.0",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "arguments": {"target": args.target, "scope": args.scope,
                      "output": args.output, "rate": args.rate},
        "recorded_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "exit_status": exit_status,
        "summary": summary,
    }
    (out / "run.json").write_text(json.dumps(run_meta, indent=2, sort_keys=True) + "\n",
                                  encoding="utf-8")

    print(json.dumps(summary, indent=2))
    return exit_status


if __name__ == "__main__":
    sys.exit(main())
