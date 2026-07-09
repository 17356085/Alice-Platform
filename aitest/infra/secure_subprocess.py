"""Compatibility wrappers for security-gated subprocess helpers."""

from __future__ import annotations

import subprocess

from alice_engine.runtime.core.security import (
    SecurityError,
    get_security_hook as _get_security_hook,
)


def get_security_hook():
    """Expose the platform security hook for legacy monkeypatch targets."""
    return _get_security_hook()


def secure_run(
    args: list[str],
    check: bool = True,
    cwd: str | None = None,
    timeout: int | None = None,
    capture_output: bool = True,
    text: bool = True,
    encoding: str = "utf-8",
    errors: str = "replace",
    **kwargs,
) -> subprocess.CompletedProcess:
    """Run a subprocess after consulting the compatibility-layer hook."""
    hook = get_security_hook()
    allowed, reason = hook.before_subprocess(args, cwd=cwd)
    if not allowed:
        raise SecurityError(f"Command blocked by security policy: {reason}")
    return subprocess.run(
        args,
        check=check,
        cwd=cwd,
        timeout=timeout,
        capture_output=capture_output,
        text=text,
        encoding=encoding,
        errors=errors,
        **kwargs,
    )


def secure_popen(
    args: list[str],
    cwd: str | None = None,
    **kwargs,
) -> subprocess.Popen:
    """Open a subprocess after consulting the compatibility-layer hook."""
    hook = get_security_hook()
    allowed, reason = hook.before_subprocess(args, cwd=cwd)
    if not allowed:
        raise SecurityError(f"Command blocked by security policy: {reason}")
    return subprocess.Popen(args, cwd=cwd, **kwargs)
