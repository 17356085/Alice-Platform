# Dependency Governance Baseline

> Phase 8 / PH8-PR-8.1  
> Last refreshed: 2026-07-15

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

- First-level nodes: `51`
- First-level edges: `166`
- Multi-node SCC count: `3`
- Largest SCC size: `6`

Reviewed SCC sets:

1. `aitest.adapters`, `aitest.audit_engine`, `aitest.llm`, `aitest.mcp`, `aitest.platform`, `aitest.testing`
2. `alice_engine.core`, `alice_engine.workflow`
3. `alice_engine.engine`, `alice_engine.extension`

## Hard Gates

- `packages/alice-engine/alice_engine/**` must not statically import `aitest`.
- `packages/alice-engine/alice_engine/**` must not dynamically import `aitest`
  via `import_module(...)` or `__import__(...)`.
- New first-level SCCs are blocked.
- Existing SCC count must not grow above the reviewed baseline.
- Existing largest SCC size must not grow above the reviewed baseline.

The 2026-07-15 audit reports `51` nodes and `166` edges after moving the
runtime contract into `aitest.runtime.base`, registering page execution and
capability adapters from the platform composition root, and retaining
`aitest.platform.runtime` as a compatibility facade. Discovery persistence now
uses an injected artifact-store port, so `aitest.discovery` no longer imports
the platform context. It reports exactly `3` SCCs with a largest size of `6`,
and no `alice_engine -> aitest` boundary violation. The edge count is a
reviewed snapshot of the current package inventory; the governing regression
is that SCC count and size do not grow. These are intentionally small
dependency seams, not a broad architecture rewrite.

## Allowed Compatibility Layers

- `aitest.platform.sdk_ports` may adapt platform services into
  `alice_engine.platform_ports`.
- `alice_engine.platform_bridge` may read explicit platform ports, but it may not
  import `aitest.*`.
- Platform facades such as `ExecutionService` and `EngineFactory` may depend on
  `alice_engine`, because the dependency direction is Platform -> SDK.

## Completed Seams

- `aitest.platform.governance_bridge` receives the adapter event bus through
  `register_governance_source()` from the server composition root.
- Codegen capability providers receive `run_skill` through
  `register_skill_runner()` or an execution context instead of importing
  `aitest.agents`.
- `aitest.config` owns configuration; `aitest.runtime.config` is a compatibility
  re-export, so the runtime layer no longer points back through the config
  compatibility shell.
- `aitest.runtime.context` receives Artifact/Knowledge/BrowserRuntime factories
  from `aitest.platform` at initialization instead of importing platform
  implementations.
- `aitest.runtime.base` owns the runtime contract and explicit page-executor /
  capability-factory ports; `aitest.platform.runtime` is the composition root
  that registers platform implementations and preserves the public import path.
- `aitest.discovery.base` owns the discovery artifact persistence port;
  `aitest.platform` registers `ArtifactStore` at composition time, while
  discovery retains a legacy filesystem fallback for standalone use.

## Pending Reduction Targets

- Break the `alice_engine.core <-> alice_engine.workflow` SCC during the
  AgentLoop boundary reduction work in `PH8-PR-8.3`.
- Remove the `alice_engine.engine <-> alice_engine.extension` SCC after the
  extension contract is simplified or inverted.
- Shrink the remaining `aitest.*` SCC incrementally; do not attempt a single
  wide-scope rewrite. The runtime, infrastructure, knowledge, and graph
  packages are now outside the largest cluster; next targets are the remaining
  `aitest.adapters` / `audit_engine` / `llm` / `mcp` / `platform` /
  `testing` links.

## How To Refresh

When a reviewed PR intentionally reduces the baseline:

```powershell
python tools/check_dependency_graph.py --write-baseline
python tools/check_dependency_graph.py
```

Refresh this document in the same PR with the new counts and SCC list.
