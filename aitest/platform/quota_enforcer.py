"""Workspace quota checks without embedding pricing policy."""

from __future__ import annotations


class QuotaExceededError(PermissionError):
    pass


def check_workspace_quota(
    *,
    quotas: dict,
    usage: dict,
    requested_runs: int = 1,
    requested_tokens: int = 0,
    requested_storage_bytes: int = 0,
) -> None:
    limits = {
        "max_runs_per_day": (usage.get("run_count", 0), requested_runs, "runs"),
        "max_tokens_per_run": (usage.get("token_usage", 0), requested_tokens, "tokens"),
        "max_storage_mb": (usage.get("storage_bytes", 0), requested_storage_bytes, "storage_bytes"),
    }
    for key, (current, requested, label) in limits.items():
        limit = quotas.get(key)
        if limit is None:
            continue
        effective_limit = limit * 1024 * 1024 if key == "max_storage_mb" else limit
        if current + requested > effective_limit:
            raise QuotaExceededError(
                f"Workspace quota exceeded: {label} {current + requested} > {effective_limit}"
            )
