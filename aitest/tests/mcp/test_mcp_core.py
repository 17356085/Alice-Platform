"""Tests for mcp/ — error_taxonomy + rate_limit.

Tests: ErrorCode enum, MCPError.to_dict(), error_response, success_response,
ToolPermission, check_rate_limit, rate limit enforcement.
No real MCP server needed.
"""
import time
import pytest

from aitest.mcp.error_taxonomy import (
    ErrorCode, MCPError, error_response, success_response,
)
from aitest.mcp.rate_limit import (
    ToolPermission, check_rate_limit, TOOL_PERMISSIONS,
    RATE_LIMITS, RATE_WINDOW_SECONDS, _rate_limit_state,
)


# ══════════════════════════════════════════════════════════════════════════
#  ErrorCode
# ══════════════════════════════════════════════════════════════════════════


class TestErrorCode:
    def test_all_codes_are_unique(self):
        values = [e.value for e in ErrorCode]
        assert len(values) == len(set(values))

    def test_has_standard_codes(self):
        assert ErrorCode.TOOL_NOT_FOUND.value == "TOOL_NOT_FOUND"
        assert ErrorCode.INVALID_PARAMS.value == "INVALID_PARAMS"
        assert ErrorCode.PERMISSION_DENIED.value == "PERMISSION_DENIED"


# ══════════════════════════════════════════════════════════════════════════
#  MCPError
# ══════════════════════════════════════════════════════════════════════════


class TestMCPError:
    def test_to_dict_basic(self):
        err = MCPError(
            code=ErrorCode.TOOL_NOT_FOUND,
            message="Tool 'xyz' not found",
        )
        d = err.to_dict()
        assert d["status"] == "error"
        assert d["error"]["code"] == "TOOL_NOT_FOUND"
        assert d["error"]["message"] == "Tool 'xyz' not found"
        assert d["error"]["retryable"] is False

    def test_to_dict_with_details(self):
        err = MCPError(
            code=ErrorCode.INVALID_PARAMS,
            message="Missing required field",
            suggestion="Provide 'module' parameter",
            retryable=True,
            details={"missing": ["module"]},
        )
        d = err.to_dict()
        assert d["error"]["retryable"] is True
        assert d["error"]["suggestion"] == "Provide 'module' parameter"
        assert d["error"]["details"]["missing"] == ["module"]

    def test_defaults(self):
        err = MCPError(code=ErrorCode.INTERNAL_ERROR, message="boom")
        assert err.suggestion == ""
        assert err.retryable is False
        assert err.details == {}


# ══════════════════════════════════════════════════════════════════════════
#  error_response + success_response
# ══════════════════════════════════════════════════════════════════════════


class TestResponseHelpers:
    def test_error_response_returns_dict(self):
        result = error_response(ErrorCode.EXECUTION_FAILED, "Test failed",
                                suggestion="Check logs", retryable=False)
        assert result["status"] == "error"
        assert result["error"]["code"] == "EXECUTION_FAILED"

    def test_success_response(self):
        result = success_response({"items": [1, 2, 3]})
        assert result["status"] == "ok"
        assert result["items"] == [1, 2, 3]

    def test_success_response_preserves_existing_status(self):
        result = success_response({"status": "partial", "data": []})
        assert result["status"] == "partial"


# ══════════════════════════════════════════════════════════════════════════
#  ToolPermission
# ══════════════════════════════════════════════════════════════════════════


class TestToolPermission:
    def test_three_levels(self):
        assert ToolPermission.READ.value == "read"
        assert ToolPermission.WRITE.value == "write"
        assert ToolPermission.EXECUTE.value == "execute"

    def test_rate_limits_hierarchy(self):
        """EXECUTE should be most restricted, READ most permissive."""
        assert RATE_LIMITS[ToolPermission.EXECUTE] < RATE_LIMITS[ToolPermission.WRITE]
        assert RATE_LIMITS[ToolPermission.WRITE] < RATE_LIMITS[ToolPermission.READ]

    def test_known_tools_have_permissions(self):
        """All registered tools should have a permission level."""
        for tool_name in TOOL_PERMISSIONS:
            assert TOOL_PERMISSIONS[tool_name] in ToolPermission


# ══════════════════════════════════════════════════════════════════════════
#  check_rate_limit
# ══════════════════════════════════════════════════════════════════════════


class TestCheckRateLimit:
    def test_first_call_allowed(self):
        # Clear state for test isolation
        _rate_limit_state.clear()
        allowed, msg = check_rate_limit("check_code_quality")
        assert allowed is True
        assert msg == ""

    def test_unknown_tool_defaults_to_read(self):
        _rate_limit_state.clear()
        allowed, _ = check_rate_limit("nonexistent_tool_xyz")
        assert allowed is True

    def test_rate_limited_after_exhausting(self):
        _rate_limit_state.clear()
        tool = "check_code_quality"  # READ → 30 calls/60s
        limit = RATE_LIMITS[ToolPermission.READ]

        # Exhaust the limit
        for _ in range(limit):
            allowed, _ = check_rate_limit(tool)
            assert allowed is True

        # Next call should be rate limited
        allowed, msg = check_rate_limit(tool)
        assert allowed is False
        assert "limit" in msg.lower() or "rate" in msg.lower()

    def test_execute_is_more_restricted(self):
        _rate_limit_state.clear()
        tool = "run_pytest"  # EXECUTE → 5 calls/60s
        limit = RATE_LIMITS[ToolPermission.EXECUTE]

        for _ in range(limit):
            assert check_rate_limit(tool)[0] is True
        assert check_rate_limit(tool)[0] is False

    def test_different_tools_independent(self):
        _rate_limit_state.clear()
        # Exhaust one tool
        for _ in range(RATE_LIMITS[ToolPermission.READ]):
            check_rate_limit("check_code_quality")
        # Different tool should still be allowed
        allowed, _ = check_rate_limit("get_module_status")
        assert allowed is True

    def test_window_expires(self):
        _rate_limit_state.clear()
        tool = "check_code_quality"
        # Artificially age timestamps past the window
        old_time = time.time() - RATE_WINDOW_SECONDS - 10
        _rate_limit_state[tool] = [old_time] * RATE_LIMITS[ToolPermission.READ]

        # Window expired → should be allowed
        allowed, _ = check_rate_limit(tool)
        assert allowed is True
        # Old entries should be cleaned up
        assert len(_rate_limit_state[tool]) <= 1  # Only the new call's timestamp
