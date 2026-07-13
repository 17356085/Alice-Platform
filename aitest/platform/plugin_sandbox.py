"""Process-isolated runner for plugins that expose a sandbox command contract.

The runner deliberately does not execute arbitrary shell strings. A plugin
must expose ``sandbox_entrypoint`` in its manifest as ``module:function``;
the child process receives JSON payloads over stdin and returns JSON results.
"""

from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import ctypes
from dataclasses import dataclass
from pathlib import Path


class PluginSandboxError(RuntimeError):
    pass


@dataclass(frozen=True)
class SandboxPolicy:
    timeout_seconds: float = 30.0
    max_payload_bytes: int = 1_048_576
    max_memory_mb: int = 2048
    max_cpu_seconds: int = 300
    strict_resource_limits: bool = False
    network_access: bool = False
    filesystem_root: Path | None = None
    isolation_command: tuple[str, ...] = ()
    strict_os_isolation: bool = False


class PluginSandbox:
    def __init__(self, plugin_path: Path, entrypoint: str, policy: SandboxPolicy | None = None):
        self.plugin_path = Path(plugin_path).resolve()
        self.entrypoint = entrypoint
        self.policy = policy or SandboxPolicy()
        self._process: subprocess.Popen[str] | None = None
        self._job_handle = None

    def start(self) -> dict:
        if self._process and self._process.poll() is None:
            return {"status": "running"}
        if not self.plugin_path.is_dir() or ":" not in self.entrypoint:
            raise PluginSandboxError("Sandbox requires a plugin directory and module:function entrypoint")
        # Keep Windows runtime variables required by CPython, but do not pass
        # common platform credentials into the child process.
        env = {
            key: value
            for key, value in os.environ.items()
            if not any(marker in key.upper() for marker in ("API_KEY", "TOKEN", "PASSWORD", "SECRET"))
        }
        env.update({"PYTHONIOENCODING": "utf-8", "PYTHONPATH": str(self.plugin_path.parent)})
        command = [sys.executable, "-m", "aitest.platform.plugin_sandbox_worker", self.entrypoint]
        if self.policy.strict_os_isolation and not self.policy.isolation_command:
            raise PluginSandboxError("Strict OS isolation requires a configured isolation_command")
        if self.policy.isolation_command:
            command = [*self.policy.isolation_command, *command]
        env.update({
            "AITEST_PLUGIN_NETWORK_ACCESS": "1" if self.policy.network_access else "0",
            "AITEST_PLUGIN_FILESYSTEM_ROOT": str(self.policy.filesystem_root or self.plugin_path),
        })
        self._process = subprocess.Popen(
            command,
            cwd=str(self.plugin_path),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
            preexec_fn=self._posix_limits if os.name != "nt" else None,
        )
        self._apply_windows_limits()
        response = self._request({"op": "ping"})
        if response.get("status") != "ready":
            self.stop()
            raise PluginSandboxError(response.get("error", "Sandbox failed to start"))
        return response

    def invoke(self, payload: dict) -> dict:
        if len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) > self.policy.max_payload_bytes:
            raise PluginSandboxError("Sandbox payload exceeds configured limit")
        if not self._process or self._process.poll() is not None:
            self.start()
        return self._request({"op": "invoke", "payload": payload})

    def call_provider(self, provider: str, method: str, payload: dict | None = None) -> dict:
        """Invoke a provider method through the child-process RPC contract."""
        if not provider or not method:
            raise PluginSandboxError("Provider RPC requires provider and method")
        if not self._process or self._process.poll() is not None:
            self.start()
        return self._request({"op": "provider_call", "provider": provider, "method": method, "payload": payload or {}})

    def stop(self) -> None:
        if not self._process:
            return
        try:
            if self._process.poll() is None:
                self._process.stdin.write(json.dumps({"op": "stop"}) + "\n")
                self._process.stdin.flush()
                self._process.wait(timeout=2)
        except Exception:
            self._process.kill()
            self._process.wait(timeout=2)
        finally:
            self._close_job()
            self._process = None

    def _request(self, message: dict) -> dict:
        if not self._process or not self._process.stdin or not self._process.stdout:
            raise PluginSandboxError("Sandbox process is not running")
        try:
            self._process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
            self._process.stdin.flush()
            result_queue: queue.Queue[str] = queue.Queue(maxsize=1)
            reader = threading.Thread(
                target=lambda: result_queue.put(self._process.stdout.readline()), daemon=True
            )
            reader.start()
            line = result_queue.get(timeout=self.policy.timeout_seconds)
        except queue.Empty as exc:
            self.stop()
            raise PluginSandboxError("Sandbox request timed out") from exc
        except Exception as exc:
            raise PluginSandboxError(f"Sandbox communication failed: {exc}") from exc
        if not line:
            error = self._process.stderr.read() if self._process.stderr else ""
            raise PluginSandboxError(error.strip() or "Sandbox process exited")
        try:
            response = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PluginSandboxError("Sandbox returned invalid JSON") from exc
        if response.get("status") == "error":
            raise PluginSandboxError(response.get("error", "Sandbox invocation failed"))
        return response

    def _posix_limits(self):
        try:
            import resource
            resource.setrlimit(resource.RLIMIT_AS, (self.policy.max_memory_mb * 1024 * 1024,) * 2)
            resource.setrlimit(resource.RLIMIT_CPU, (self.policy.max_cpu_seconds, self.policy.max_cpu_seconds))
        except Exception:
            if self.policy.strict_resource_limits:
                raise

    def _apply_windows_limits(self):
        if os.name != "nt" or not self._process:
            return
        try:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.CreateJobObjectW(None, None)
            if not handle:
                raise OSError("CreateJobObjectW failed")
            self._job_handle = handle

            class BasicLimit(ctypes.Structure):
                _fields_ = [
                    ("PerProcessUserTime", ctypes.c_longlong), ("PerJobUserTime", ctypes.c_longlong),
                    ("LimitFlags", ctypes.c_uint32), ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", ctypes.c_uint32),
                    ("Affinity", ctypes.c_size_t), ("PriorityClass", ctypes.c_uint32),
                    ("SchedulingClass", ctypes.c_uint32),
                ]

            class ExtendedLimit(ctypes.Structure):
                _fields_ = [
                    ("BasicLimitInformation", BasicLimit),
                    ("IoInfo", ctypes.c_byte * 48),
                    ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t),
                ]

            limits = ExtendedLimit()
            limits.BasicLimitInformation.LimitFlags = 0x00000100 | 0x00000002  # kill-on-close + process time
            limits.BasicLimitInformation.PerProcessUserTime = self.policy.max_cpu_seconds * 10_000_000
            limits.ProcessMemoryLimit = self.policy.max_memory_mb * 1024 * 1024
            limits.BasicLimitInformation.LimitFlags |= 0x00000100
            if not kernel32.SetInformationJobObject(handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
                raise OSError("SetInformationJobObject failed")
            if not kernel32.AssignProcessToJobObject(handle, ctypes.c_void_p(self._process._handle)):
                raise OSError("AssignProcessToJobObject failed")
        except Exception:
            self._close_job()
            if self.policy.strict_resource_limits:
                self.stop()
                raise PluginSandboxError("Unable to apply Windows sandbox resource limits")

    def _close_job(self):
        if self._job_handle:
            try:
                ctypes.windll.kernel32.CloseHandle(self._job_handle)
            except Exception:
                pass
            self._job_handle = None
