# Runtime Contract Pack

> Phase 8 / PH8-PR-8.2  
> Last refreshed: 2026-07-08

## Goal

Freeze the smallest SDK-neutral contracts that sit under the public execution
kernel and above platform-specific projections.

This layer is intentionally narrower than `Run`, `RunEvent`, billing, webhook,
or SQL storage. The SDK owns the neutral runtime contracts; the platform owns
projection into product/runtime-control concerns.

## Contract Modules

- SDK-neutral pack: [runtime_contracts.py](/D:/Desktop/Alice/packages/alice-engine/alice_engine/runtime_contracts.py)
- Shared execution input/output: [contracts.py](/D:/Desktop/Alice/packages/alice-engine/alice_engine/contracts.py)
- Platform projections: [runtime_contracts.py](/D:/Desktop/Alice/aitest/platform/runtime_contracts.py)

## Frozen Contracts

### Execution Context

- Canonical type: `alice_engine.contracts.ExecutionContext`
- Purpose: normalize API / CLI / chat / SDK caller identity and execution routing
- Platform-only semantics such as queue lease, billing, and webhook delivery stay
  out of this object

### Runtime Event Envelope

- Canonical type: `alice_engine.runtime_contracts.RuntimeEventEnvelope`
- Purpose: neutral event shape emitted from runtime-facing execution semantics
- Carries:
  - request/run identity
  - normalized context reference
  - module/pages/agent/phase/status
  - token/cost/duration counters
  - replay/checkpoint identifiers
  - completed/failed phase summaries
  - artifact references
  - additive metadata

Platform projection:

- `aitest.platform.runtime_contracts.runtime_event_to_run_event(...)`
  maps `RuntimeEventEnvelope` into `RunEvent`
- `RunEvent` remains the platform-facing event stream for audit, billing,
  webhook, metrics, and timeline consumers

### Replay Core

- Canonical types:
  - `RuntimeReplaySessionRecord`
  - `RuntimeReplayStepRecord`
- Purpose: freeze a neutral replay model above SQL tables and below UI/query use
- Platform SQL persistence in `aitest.platform.replay` is now treated as an
  adapter around these stable records

### Checkpoint Snapshot

- Canonical type: `RuntimeCheckpointRecord`
- Purpose: stable resume/checkpoint snapshot above specific stores such as
  LangGraph SQLite or future platform Postgres adapters
- Platform bridge:
  - `aitest.platform.checkpoint.CheckpointSnapshot` remains the live adapter
  - `checkpoint_snapshot_to_record(...)` maps into the frozen contract

### Artifact Record

- Canonical type: `RuntimeArtifactRecord`
- Purpose: freeze artifact references as runtime outputs without forcing the SDK
  to depend on platform lineage storage, SOP status storage, or project layout

## Ownership Boundary

- SDK owns:
  - `ExecutionContext`
  - `ExecutionResult`
  - `RuntimeEventEnvelope`
  - `RuntimeReplaySessionRecord`
  - `RuntimeReplayStepRecord`
  - `RuntimeCheckpointRecord`
  - `RuntimeArtifactRecord`

- Platform owns:
  - `Run`
  - `RunEvent`
  - `ExecutionRequest`
  - billing/audit/webhook projections
  - replay SQL persistence
  - checkpoint store wiring
  - artifact lineage and project-scoped file layout

## Current Projection Rule

The rule for Phase 8 is:

```text
ExecutionResult / runtime state
  -> RuntimeEventEnvelope / Runtime*Record
  -> Platform RunEvent / Replay / Checkpoint / Artifact adapters
```

Platform may enrich contracts additively during projection, but it should not
force the SDK contract pack to absorb billing-, org-, or storage-specific fields.

## Focused Regression Coverage

- SDK contract tests:
  [test_runtime_contract_pack.py](/D:/Desktop/Alice/packages/alice-engine/tests/test_runtime_contract_pack.py)
- Platform projection tests:
  [test_runtime_contract_projection.py](/D:/Desktop/Alice/aitest/tests/platform/test_runtime_contract_projection.py)
