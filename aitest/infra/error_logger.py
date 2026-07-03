# Re-export — 原文件已搬到 runtime/error_handling.py
# Deprecated: 直接从 aitest.runtime.error_handling import
import warnings as _warnings
_warnings.warn(
    "aitest.infra.error_logger is deprecated, use aitest.runtime.error_handling directly",
    DeprecationWarning,
    stacklevel=2,
)
from aitest.runtime.error_handling import log_error, list_recent, get_summary, cleanup_old  # noqa: F401
