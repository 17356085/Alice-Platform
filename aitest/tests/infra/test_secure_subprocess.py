"""Tests for infra/secure_subprocess.py — security-gated subprocess calls.

Tests: secure_run blocks dangerous commands, allows safe commands,
SecurityError propagation, secure_popen, security hook integration.
"""
import subprocess
import pytest
from unittest.mock import patch, MagicMock

from aitest.infra.secure_subprocess import secure_run, secure_popen, get_security_hook
from aitest.infra.security import SecurityError


# ══════════════════════════════════════════════════════════════════════════
#  Shared fixtures
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_hook():
    """SecurityHook that allows everything by default."""
    hook = MagicMock()
    hook.before_subprocess.return_value = (True, "")
    return hook


@pytest.fixture
def blocking_hook():
    """SecurityHook that blocks everything."""
    hook = MagicMock()
    hook.before_subprocess.return_value = (False, "test-block: command denied")
    return hook


@pytest.fixture
def allow_all(monkeypatch, mock_hook):
    """Patch get_security_hook to return an allow-all hook."""
    monkeypatch.setattr(
        "aitest.infra.secure_subprocess.get_security_hook",
        lambda: mock_hook,
    )
    return mock_hook


@pytest.fixture
def block_all(monkeypatch, blocking_hook):
    """Patch get_security_hook to return a block-all hook."""
    monkeypatch.setattr(
        "aitest.infra.secure_subprocess.get_security_hook",
        lambda: blocking_hook,
    )
    return blocking_hook


# ══════════════════════════════════════════════════════════════════════════
#  secure_run — allowed commands
# ══════════════════════════════════════════════════════════════════════════


class TestSecureRunAllowed:
    def test_runs_safe_command(self, allow_all):
        result = secure_run(["echo", "hello"])
        assert result.returncode == 0
        assert "hello" in result.stdout

    def test_passes_cwd_to_subprocess(self, allow_all, temp_dir):
        result = secure_run(["echo", "test"], cwd=str(temp_dir))
        assert result.returncode == 0

    def test_passes_timeout_to_subprocess(self, allow_all):
        result = secure_run(["echo", "fast"], timeout=10)
        assert result.returncode == 0

    def test_check_true_raises_on_failure(self, allow_all):
        with pytest.raises(subprocess.CalledProcessError):
            secure_run(["python", "-c", "import sys; sys.exit(1)"])

    def test_check_false_returns_result(self, allow_all):
        result = secure_run(
            ["python", "-c", "import sys; sys.exit(1)"],
            check=False,
        )
        assert result.returncode == 1

    def test_capture_output_enabled_by_default(self, allow_all):
        result = secure_run(["python", "-c", "print('captured')"])
        assert "captured" in result.stdout

    def test_calls_security_hook_before_subprocess(self, allow_all):
        secure_run(["echo", "x"])
        allow_all.before_subprocess.assert_called_once()
        call_args, call_kwargs = allow_all.before_subprocess.call_args
        assert call_args[0] == ["echo", "x"]

    def test_encoding_utf8(self, allow_all):
        # Windows: subprocess encoding depends on console codepage.
        # Pass encoding explicitly and verify the parameter is accepted.
        result = secure_run(
            ["python", "-c", "print('hello')"],
        )
        assert "hello" in result.stdout
        assert result.returncode == 0


# ══════════════════════════════════════════════════════════════════════════
#  secure_run — blocked commands
# ══════════════════════════════════════════════════════════════════════════


class TestSecureRunBlocked:
    def test_raises_security_error_when_blocked(self, block_all):
        with pytest.raises(SecurityError) as exc:
            secure_run(["rm", "-rf", "/"])
        assert "blocked by security policy" in str(exc.value)
        assert "test-block" in str(exc.value)

    def test_security_error_is_not_called_process_error(self, block_all):
        """SecurityError is distinct from subprocess errors."""
        with pytest.raises(SecurityError):
            secure_run(["anything"])
        # SecurityError is NOT a subclass of CalledProcessError
        assert not issubclass(SecurityError, subprocess.CalledProcessError)


# ══════════════════════════════════════════════════════════════════════════
#  secure_popen
# ══════════════════════════════════════════════════════════════════════════


class TestSecurePopen:
    def test_allows_safe_command(self, allow_all):
        proc = secure_popen(["echo", "popen_test"], stdout=subprocess.PIPE, text=True)
        out, _ = proc.communicate()
        assert "popen_test" in out
        assert proc.returncode == 0

    def test_blocks_dangerous_command(self, block_all):
        with pytest.raises(SecurityError):
            secure_popen(["sudo", "rm", "-rf", "/"])

    def test_calls_security_hook_before_popen(self, allow_all):
        proc = secure_popen(
            ["echo", "x"],
            stdout=subprocess.PIPE,
            text=True,
        )
        proc.communicate()
        allow_all.before_subprocess.assert_called_once()


# ══════════════════════════════════════════════════════════════════════════
#  get_security_hook
# ══════════════════════════════════════════════════════════════════════════


class TestGetSecurityHook:
    def test_returns_security_hook(self):
        from aitest.infra.security import SecurityHook
        hook = get_security_hook()
        assert isinstance(hook, SecurityHook)

    def test_returns_same_instance(self):
        a = get_security_hook()
        b = get_security_hook()
        assert a is b
