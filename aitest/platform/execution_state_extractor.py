"""State extraction utilities for execution results.

This module handles extracting structured data from execution states
and finalizing run objects.

Extracted from execution_service.py to improve modularity.
"""

from __future__ import annotations

from typing import Any

from alice_engine.contracts import ExecutionContext, ExecutionResult
from alice_engine.runtime_contracts import RuntimeArtifactRecord

from .config_registry import cfg
from .run import Run
from .run_event import EventDataKey as K


class ExecutionStateExtractor:
    """Utilities for extracting data from execution states."""

    @staticmethod
    def extract_value(state: Any, key: str, default: Any = None) -> Any:
        """Extract a value from state (ExecutionResult, dict, or object)."""
        if isinstance(state, ExecutionResult):
            return getattr(state, key, default)
        if isinstance(state, dict):
            return state.get(key, default)
        return getattr(state, key, default)

    @staticmethod
    def extract_list(state: Any, key: str) -> list[str]:
        """Extract a list value from state."""
        value = ExecutionStateExtractor.extract_value(state, key, [])
        return list(value) if isinstance(value, (list, tuple, set)) else []

    @staticmethod
    def extract_artifacts(state: Any) -> list[str]:
        """Extract artifacts list from state."""
        if isinstance(state, ExecutionResult):
            return [str(v) for v in state.artifacts]
        value = ExecutionStateExtractor.extract_value(state, "artifacts", [])
        if isinstance(value, list):
            return [str(v) for v in value]
        return []

    @staticmethod
    def extract_runtime_artifacts(state: Any, run_id: str, module: str) -> list[RuntimeArtifactRecord]:
        """Extract artifacts as RuntimeArtifactRecord list."""
        artifact_paths = ExecutionStateExtractor.extract_artifacts(state)
        return [
            RuntimeArtifactRecord(path=path, run_id=run_id, module=module)
            for path in artifact_paths
        ]

    @staticmethod
    def version_payload(ctx: ExecutionContext) -> dict[str, Any]:
        """Build version payload from execution context."""
        metadata = ctx.metadata if isinstance(ctx.metadata, dict) else {}
        return {
            K.POLICY_VERSION: metadata.get(K.POLICY_VERSION, cfg.governance_policy_version),
            K.GOVERNANCE_VERSION: metadata.get(K.GOVERNANCE_VERSION, cfg.governance_policy_version),
            K.CONFIG_VERSION: metadata.get(K.CONFIG_VERSION, cfg.governance_policy_version),
            K.GOVERNANCE_PACK_ROOT: metadata.get(K.GOVERNANCE_PACK_ROOT, ""),
        }

    @staticmethod
    def version_payload_from_run(run: Run) -> dict[str, Any]:
        """Build version payload from run object."""
        metadata = getattr(run, "runtime_context", {})
        if not isinstance(metadata, dict):
            metadata = {}
        return {
            K.POLICY_VERSION: metadata.get(K.POLICY_VERSION, cfg.governance_policy_version),
            K.GOVERNANCE_VERSION: metadata.get(K.GOVERNANCE_VERSION, cfg.governance_policy_version),
            K.CONFIG_VERSION: metadata.get(K.CONFIG_VERSION, cfg.governance_policy_version),
            K.GOVERNANCE_PACK_ROOT: metadata.get(K.GOVERNANCE_PACK_ROOT, ""),
        }

    @staticmethod
    def finalize_run_from_state(run: Run, state: Any) -> None:
        """Finalize run object from execution state.

        Updates run status (completed/failed/cancelled/timed_out) based on state.
        """
        if isinstance(state, ExecutionResult):
            # Modern ExecutionResult path
            setattr(run, "runtime_context", state.metadata.get("runtime_context", {}))
            setattr(run, "replay_session_id", state.metadata.get("replay_session_id", ""))

            if state.status == "cancelled":
                run.total_tokens = state.total_tokens
                run.total_cost = state.total_cost
                run.agent_runs = state.agent_runs
                run.artifacts = list(state.artifacts)
                run.cancel()
                return

            if state.status in {"failed", "timed_out"} or state.failed_phases:
                run.total_tokens = state.total_tokens
                run.total_cost = state.total_cost
                run.agent_runs = state.agent_runs
                run.artifacts = list(state.artifacts)
                if state.status == "timed_out":
                    run.timed_out()
                else:
                    run.fail(state.error_message or "execution_failed")
                return

            run.complete(
                total_tokens=state.total_tokens,
                total_cost=state.total_cost,
                agent_runs=state.agent_runs,
                artifacts=list(state.artifacts),
            )
            return

        # Legacy dict/object path
        extract = ExecutionStateExtractor.extract_value
        total_tokens = int(extract(state, "total_tokens", 0) or 0)
        total_cost = float(
            extract(
                state,
                "estimated_cost",
                extract(state, "total_cost", 0.0),
            )
            or 0.0
        )
        agent_runs = int(
            extract(
                state,
                "step",
                len(extract(state, "agent_outputs", {}) or {}),
            )
            or 0
        )
        artifacts = ExecutionStateExtractor.extract_artifacts(state)
        failed_phases = ExecutionStateExtractor.extract_list(state, "failed_phases")
        termination_reason = str(extract(state, "termination_reason", "") or "")
        success = extract(state, "success", None)
        status_hint = str(extract(state, "status", "") or "").lower()

        setattr(run, "runtime_context", extract(state, "memory", {}).get("runtime_context", {}))
        setattr(run, "replay_session_id", extract(state, "memory", {}).get("replay_session_id", ""))

        if status_hint == "cancelled" or termination_reason == "cancelled":
            run.total_tokens = total_tokens
            run.total_cost = total_cost
            run.agent_runs = agent_runs
            run.artifacts = artifacts
            run.cancel()
            return

        if status_hint == "timed_out" or termination_reason == "timed_out":
            run.total_tokens = total_tokens
            run.total_cost = total_cost
            run.agent_runs = agent_runs
            run.artifacts = artifacts
            run.timed_out()
            return

        if failed_phases or (success is False and termination_reason not in ("max_steps", "")):
            run.total_tokens = total_tokens
            run.total_cost = total_cost
            run.agent_runs = agent_runs
            run.artifacts = artifacts
            error_msg = str(extract(state, "error_message", "") or "")
            run.fail(error_msg or termination_reason or "execution_failed")
            return

        run.complete(
            total_tokens=total_tokens,
            total_cost=total_cost,
            agent_runs=agent_runs,
            artifacts=artifacts,
        )
