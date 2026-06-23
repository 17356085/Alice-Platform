"""Secure subprocess wrapper — 带安全校验的 subprocess.run()。

Week 1 Day 4: 替代直接 subprocess.run() 调用。

用法:
    from aitest.infra.secure_subprocess import secure_run
    result = secure_run(["python", "script.py", "--force"])
"""
import subprocess
import logging
from pathlib import Path
from typing import Optional

from aitest.infra.security import SecurityHook, SecurityError

logger = logging.getLogger(__name__)

# 模块级单例
_security_hook: Optional[SecurityHook] = None


def get_security_hook() -> SecurityHook:
    """获取 SecurityHook 单例。延迟初始化。"""
    global _security_hook
    if _security_hook is None:
        from aitest.platform.paths import get_workstudy
        project_root = get_workstudy()
        _security_hook = SecurityHook(project_root=project_root)
    return _security_hook


def secure_run(
    args: list[str],
    check: bool = True,
    cwd: str = None,
    timeout: int = None,
    capture_output: bool = True,
    text: bool = True,
    encoding: str = "utf-8",
    errors: str = "replace",
    **kwargs,
) -> subprocess.CompletedProcess:
    """带安全校验的 subprocess.run()。

    参数与 subprocess.run() 基本一致。额外的安全校验在 subprocess 调用前执行。

    Raises:
        SecurityError: 安全校验失败
        subprocess.CalledProcessError: check=True 且进程返回非零
        subprocess.TimeoutExpired: timeout 超时

    Example:
        result = secure_run(["python", str(scan_script), "--force"])
        result = secure_run(["pytest", "-v", "test_page.py"], cwd=str(test_dir), timeout=300)
    """
    hook = get_security_hook()

    # 安全校验
    allowed, reason = hook.before_subprocess(args, cwd=cwd)
    if not allowed:
        logger.error(f"Security blocked command: {reason} | args={args}")
        raise SecurityError(f"Command blocked by security policy: {reason}")

    # 执行
    logger.debug(f"secure_run: {' '.join(str(a) for a in args)}")
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
    cwd: str = None,
    **kwargs,
) -> subprocess.Popen:
    """带安全校验的 subprocess.Popen()。"""
    hook = get_security_hook()

    allowed, reason = hook.before_subprocess(args, cwd=cwd)
    if not allowed:
        logger.error(f"Security blocked command: {reason} | args={args}")
        raise SecurityError(f"Command blocked by security policy: {reason}")

    logger.debug(f"secure_popen: {' '.join(str(a) for a in args)}")
    return subprocess.Popen(args, cwd=cwd, **kwargs)
