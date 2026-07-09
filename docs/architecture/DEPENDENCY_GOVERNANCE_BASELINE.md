# Dependency Governance Baseline

> Phase 8 / PH8-PR-8.1  
> Last refreshed: 2026-07-08

## Goal

Phase 8 does not try to remove every historical cycle in one PR. The first step
is to freeze a reviewed baseline for first-level package dependencies, keep the
`alice_engine -> aitest` boundary hard-blocked, and stop SCC growth while later
PRs reduce the historical clusters.

## Checked Artifacts

- Script: [tools/check_dependency_graph.py](/D:/Desktop/Alice/tools/check_dependency_graph.py)
- Baseline JSON: [dependency_graph_baseline.json](/D:/Desktop/Alice/docs/architecture/dependency_graph_baseline.json)
- Regression test: [test_dependency_graph_guard.py](/D:/Desktop/Alice/packages/alice-engine/tests/test_dependency_graph_guard.py)

## Current Baseline

- First-level nodes: `48`
- First-level edges: `152`
- Multi-node SCC count: `3`
- Largest SCC size: `17`

Reviewed SCC sets:

1. `aitest.adapters`, `aitest.agents`, `aitest.audit_engine`, `aitest.bu_adapter`, `aitest.config`, `aitest.discovery`, `aitest.engine`, `aitest.graphs`, `aitest.graphs_dev`, `aitest.infra`, `aitest.integrations`, `aitest.knowledge`, `aitest.llm`, `aitest.mcp`, `aitest.platform`, `aitest.runtime`, `aitest.testing`
2. `alice_engine.core`, `alice_engine.workflow`
3. `alice_engine.engine`, `alice_engine.extension`

## Hard Gates

- `packages/alice-engine/alice_engine/**` must not statically import `aitest`.
- `packages/alice-engine/alice_engine/**` must not dynamically import `aitest`
  via `import_module(...)` or `__import__(...)`.
- New first-level SCCs are blocked.
- Existing SCC count must not grow above the reviewed baseline.
- Existing largest SCC size must not grow above the reviewed baseline.

## Allowed Compatibility Layers

- `aitest.platform.sdk_ports` may adapt platform services into
  `alice_engine.platform_ports`.
- `alice_engine.platform_bridge` may read explicit platform ports, but it may not
  import `aitest.*`.
- Platform facades such as `ExecutionService` and `EngineFactory` may depend on
  `alice_engine`, because the dependency direction is Platform -> SDK.

## Pending Reduction Targets

- Break the `alice_engine.core <-> alice_engine.workflow` SCC during the
  AgentLoop boundary reduction work in `PH8-PR-8.3`.
- Remove the `alice_engine.engine <-> alice_engine.extension` SCC after the
  extension contract is simplified or inverted.
- Shrink the large `aitest.*` SCC incrementally; do not attempt a single
  wide-scope rewrite. Prioritize `aitest.platform`, `aitest.runtime`,
  `aitest.graphs`, and `aitest.infra` seams.

## How To Refresh

When a reviewed PR intentionally reduces the baseline:

```powershell
python tools/check_dependency_graph.py --write-baseline
python tools/check_dependency_graph.py
```

Refresh this document in the same PR with the new counts and SCC list.
