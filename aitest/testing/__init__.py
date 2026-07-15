"""Testing execution module — pytest runner and test utilities.

Extracted from mcp.tools.execution to break circular dependency.

Author: AITest Platform
Created: 2026-07-14
Related: 循环依赖拆分 Step 1
"""

from aitest.testing.pytest_runner import run_pytest

__all__ = ["run_pytest"]
