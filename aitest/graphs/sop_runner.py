"""Re-export from alice_engine.workflow.sop_runner — 保持向后兼容。

Deprecated: 直接从 alice_engine.workflow.sop_runner import SOPRunner。
"""
import warnings as _warnings
_warnings.warn(
    "aitest.graphs.sop_runner re-export is deprecated, use alice_engine.workflow.sop_runner directly",
    DeprecationWarning,
    stacklevel=2,
)
from alice_engine.workflow.sop_runner import SOPRunner  # noqa: F401
