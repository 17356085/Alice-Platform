# Re-export — 原文件已搬到 runtime/security.py
# Deprecated: 直接从 alice_engine.runtime.security import
import warnings as _warnings
_warnings.warn(
    "aitest.infra.security is deprecated, use aitest.runtime.security or alice_engine.runtime.security directly",
    DeprecationWarning,
    stacklevel=2,
)
from alice_engine.runtime.core.security import (  # noqa: F401
    BashValidator, SecurityHook, SecurityError, PromptInjectionGuard,
    BLOCKED_COMMANDS, CONTEXT_BLOCKED_PATTERNS, VALIDATORS,
    parse_commands, validate_rm_command, validate_git_command,
    validate_python_command, validate_pip_command, validate_curl_wget,
)
