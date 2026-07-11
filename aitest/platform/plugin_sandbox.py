"""Process-isolated runner for plugins that expose a sandbox command contract.

The runner deliberately does not execute arbitrary shell strings. A plugin
must expose ``sandbox_entrypoint`` in its manifest as ``module:function``;
the child process receives JSON payloads over stdin and returns JSON results.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


class PluginSandboxError(RuntimeError):
    pass


@dataclass(frozen=True)
class SandboxPolicy:
    timeout_seconds: float = 30.0
    max_payload_bytes: int = 1_048_576


class PluginSandbox:
    def __init__(self, plugin_path: Path, entrypoint: str, policy: SandboxPolicy | None = None):
        self.plugin_path = Path(plugin_path).resolve()
        self.entrypoint = entrypoint
        self.policy = policy or SandboxPolicy()
        self._process: subprocess.Popen[str] | None = None

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
        self._process = subprocess.Popen(
            [sys.executable, "-m", "aitest.platform.plugin_sandbox_worker", self.entrypoint],
            cwd=str(self.plugin_path),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env=env,
        )
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
            self._process = None

    def _request(self, message: dict) -> dict:
        if not self._process or not self._process.stdin or not self._process.stdout:
            raise PluginSandboxError("Sandbox process is not running")
        try:
            self._process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
            self._process.stdin.flush()
            line = self._process.stdout.readline()
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
