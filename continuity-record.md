# Portfolio Continuity Record — Stage 5 to Stage 6

This project produced reusable components intended to carry forward.

## Reusable components handed forward

- **Scope guard** (`recon-engine/scope.py`): deny-by-default authorization from a
  scope file; enforces host/port scope before any network activity. Reusable for
  any future engagement by supplying a different scope file.
- **Request ledger** (`recon-engine/ledger.py`): append-only, written before each
  request; the basis for reconciliation and budget accounting.
- **Safe requester** (`recon-engine/net.py`): the single gate that fuses scope and
  ledger so no request bypasses enforcement.
- **Runtime identifier / normalization model** (`recon-engine/normalize.py`):
  one versioned record schema with deterministic, order-independent hashing.
- **Checkpoint/resume** (`recon-engine/checkpoint.py`): staged, atomic checkpointing
  for interruptible long-running assessments.
- **Parser adapters** (`recon-engine/adapters.py`): XML/JSON/line parsing into the
  shared schema with safe, specific errors.

## Interfaces to preserve for Stage 6

- CLI contract: `--target --scope --output --rate`, writing `run.json`, `raw/`,
  `normalized/`, `errors.jsonl`.
- Normalized record schema: `schemas/normalized-record.schema.json` (version 1.0).
- Determinism guarantee: result hash excludes volatile fields.

## Cleanup behavior

`make clean` removes generated run state (checkpoint, temp files, caches) so a
clean-state rebuild is reproducible. The lab runtime and evidence are preserved.
