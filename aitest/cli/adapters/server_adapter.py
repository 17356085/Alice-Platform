"""Server adapter — 管理 FastAPI 服务进程。

支持前台和后台两种模式:
  - 前台: os.execvp 阻塞终端，Ctrl+C 停止
  - 后台: subprocess.Popen + PID 文件
"""

import os
import sys
import socket
import signal
import subprocess
from pathlib import Path
from typing import Optional

PID_FILE = Path.home() / ".alice" / "server.pid"


def _is_port_in_use(port: int, host: str = "localhost") -> bool:
    """检查端口是否被占用。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex((host, port)) == 0


def _read_pid() -> Optional[int]:
    """读取 PID 文件。"""
    if PID_FILE.exists():
        try:
            return int(PID_FILE.read_text().strip())
        except (ValueError, OSError):
            pass
    return None


def _write_pid(pid: int):
    """写入 PID 文件。"""
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(pid))


def _remove_pid():
    """删除 PID 文件。"""
    if PID_FILE.exists():
        try:
            PID_FILE.unlink()
        except OSError:
            pass


def _is_process_alive(pid: int) -> bool:
    """检查进程是否存活。"""
    try:
        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        else:
            os.kill(pid, 0)
            return True
    except (OSError, ProcessLookupError):
        return False


class ServerAdapter:
    """服务器进程管理。"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port

    def start(self, daemon: bool = False, reload: bool = False) -> dict:
        """启动服务器。

        Args:
            daemon: 后台模式
            reload: 自动重载 (开发用)

        Returns:
            {"pid": int, "host": str, "port": int, "mode": str}
        """
        if _is_port_in_use(self.port, "localhost"):
            raise RuntimeError(f"端口 {self.port} 已被占用")

        cmd = [
            sys.executable, "-m", "uvicorn",
            "aitest.server.main:app",
            "--host", self.host,
            "--port", str(self.port),
        ]
        if reload:
            cmd.append("--reload")

        if daemon:
            # 后台模式
            kwargs = {}
            if sys.platform == "win32":
                kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                kwargs["start_new_session"] = True

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                **kwargs,
            )
            _write_pid(process.pid)
            return {
                "pid": process.pid,
                "host": self.host,
                "port": self.port,
                "mode": "daemon",
            }
        else:
            # 前台模式: 阻塞直到 Ctrl+C
            try:
                subprocess.run(cmd, check=True)
            except KeyboardInterrupt:
                pass
            return {"mode": "foreground"}

    def stop(self) -> dict:
        """停止服务器。

        Returns:
            {"pid": int, "status": str}
        """
        pid = _read_pid()
        if not pid:
            raise RuntimeError("未找到 PID 文件，服务器可能未启动")

        if not _is_process_alive(pid):
            _remove_pid()
            raise RuntimeError(f"进程 {pid} 不存在，已清理 PID 文件")

        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    check=True,
                    capture_output=True,
                )
            else:
                os.kill(pid, signal.SIGTERM)
            _remove_pid()
            return {"pid": pid, "status": "stopped"}
        except (ProcessLookupError, subprocess.CalledProcessError) as e:
            _remove_pid()
            raise RuntimeError(f"停止进程 {pid} 失败: {e}")

    def status(self) -> dict:
        """获取服务器状态。

        Returns:
            {"status": str, "pid": int|None, "port": int, "host": str}
        """
        pid = _read_pid()
        port_in_use = _is_port_in_use(self.port, "localhost")

        if pid and _is_process_alive(pid) and port_in_use:
            return {"status": "running", "pid": pid, "port": self.port, "host": self.host}
        elif pid and not port_in_use:
            # PID 存在但端口未占用: 残留 PID 文件
            _remove_pid()
            return {"status": "stopped", "pid": None, "port": self.port, "host": self.host}
        elif not pid and port_in_use:
            return {"status": "external_process", "pid": None, "port": self.port, "host": self.host}
        else:
            return {"status": "stopped", "pid": None, "port": self.port, "host": self.host}
