# Recon Engine and Foothold — Stage 5 (EH-A1)

A resumable, scope-safe reconnaissance engine (Python standard library only)
that discovers a loopback lab's hidden service chain, confirms the genuine
virtual host, and produces the evidence used to earn a bounded foothold.

## Requirements

- Python 3.11 or newer (developed and tested on Python 3.13.14).
- No third-party packages, no Docker, no VPN, no cloud, no internet.
- The supplied local lab (`local_lab.py`) running on `127.0.0.1`.

## Quick start

Start the local lab in one terminal (marker comes from the private overlay):

    python3.13 local_lab.py --marker <YOUR-UBI-A5-MARKER> --output lab-runtime

Run the engine in another terminal:

    make run
    # equivalent to:
    # cd recon-engine && python3.13 cli.py --target 127.0.0.1 \
    #     --scope ../lab-runtime/scope.csv --output ../run --rate 25

Run the tests:

    make test

## What the engine does

1. Probes only the authorized loopback ports (scope enforced before every socket).
2. Talks to the line-protocol signal service, learns its commands via CAPS, and
   extracts the virtual host and route key via ROUTE.
3. Re-probes HTTP using the discovered vhost, establishes a wildcard baseline
   with a random hostname, and confirms the genuine vhost by difference.
4. Reads diagnostics behind the real vhost to discover credentials.
5. Normalizes all findings into a deterministic, sorted record set and computes
   a timestamp-independent result hash.

The engine is **discovery only**. It never fetches the flag. The foothold is a
separate, deliberate step (`foothold.py`) that uses the engine's discovered
values to authenticate to `/user.txt` and records a full transcript.

## Scope safety

Every network request passes through a single scope-enforcing gate
(`recon-engine/net.py`) that checks the destination against the generated scope
before any socket is opened, and logs every attempt (SENT or DENIED) to the
request ledger. The out-of-scope decoy therefore receives zero packets; this is
demonstrated in `request-ledger.csv` and corroborated by the lab's own ledger.

## Resumable runs

Each discovery stage (ports, signal, http) is checkpointed after completion
(`recon-engine/checkpoint.py`). An interrupted run reloads the checkpoint,
skips completed stages, and produces the same result hash as an uninterrupted
run, because normalization sorts records by identity before hashing.

## Layout

- `recon-engine/` — the engine modules and CLI
- `tests/` — unittest suite (includes all 20 published fixtures)
- `schemas/` — the versioned normalized-record schema
- `raw-output/` — unedited tool/probe output
- `normalized.json` — the normalized records from the graded run
- `request-ledger.csv` — every request the engine made
- `scope-register.csv` — the IN/OUT scope decisions
- `foothold-evidence.txt` — the foothold transcript and flag
- `evidence-index.csv` — maps each claim to its raw evidence
- `assessment-manifest.json` — machine-readable build/test/run recipe
- `manifest.sha256` — SHA-256 of every submitted artifact
- `continuity-record.md` — what carries forward to Stage 6

## Reproduce from clean

    make clean
    make test
    make run

The result hash in `run/run.json` will match across clean runs on the same lab
profile.
