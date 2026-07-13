"""Workspace quota enforcement tests."""

import pytest

from aitest.platform.quota_enforcer import QuotaExceededError, check_workspace_quota


def test_quota_allows_usage_within_limits():
    check_workspace_quota(
        quotas={"max_runs_per_day": 5, "max_tokens_per_run": 1000, "max_storage_mb": 10},
        usage={"run_count": 2, "token_usage": 100, "storage_bytes": 1024},
        requested_tokens=500,
    )


def test_quota_rejects_run_limit():
    with pytest.raises(QuotaExceededError, match="runs"):
        check_workspace_quota(
            quotas={"max_runs_per_day": 1},
            usage={"run_count": 1},
        )


def test_quota_converts_storage_mb():
    with pytest.raises(QuotaExceededError, match="storage_bytes"):
        check_workspace_quota(
            quotas={"max_storage_mb": 1},
            usage={"storage_bytes": 1024 * 1024},
            requested_storage_bytes=1,
        )
