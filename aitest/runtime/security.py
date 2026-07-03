"""Re-export from alice_engine.runtime.security — 保持向后兼容。

Deprecated: 直接从 alice_engine.runtime.security import。
"""
import warnings as _warnings
_warnings.warn(
    "aitest.runtime.security re-export is deprecated, use alice_engine.runtime.security directly",
    DeprecationWarning,
    stacklevel=2,
)
from alice_engine.runtime.security import (  # noqa: F401
    BLOCKED_COMMANDS,
    CONTEXT_BLOCKED_PATTERNS,
    BashValidator,
    SecurityHook,
    PromptInjectionGuard,
    secure_run,
)
