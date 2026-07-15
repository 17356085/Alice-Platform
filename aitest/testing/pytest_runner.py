"""Pytest execution runner — 运行 pytest 测试并返回结构化结果.

Author: AITest Platform
Created: 2026-07-14
Related: 循环依赖拆分 Step 1
"""

import re
import time
import subprocess
from pathlib import Path
from typing import Optional, Callable


# 默认的任务管理器（无操作）
class _NoOpTaskHandle:
    """无操作的任务句柄（当 cancellation 模块不可用时使用）."""
    task_id = "noop"
    def is_cancelled(self):
        return False

_default_register_task = lambda name: _NoOpTaskHandle()
_default_deregister_task = lambda task_id: None


def run_pytest(
    module: str = "",
    marker: str = "",
    parallel: int = 1,
    test_file: str = "",
    timeout: int = 300,
    register_task: Optional[Callable] = None,
    deregister_task: Optional[Callable] = None,
) -> dict:
    """P0-1: 运行 pytest 测试并返回结构化结果。
    P2-4: 支持通过 cancel_task Tool 中途取消。

    Args:
        module: 测试模块名称
        marker: pytest marker 过滤
        parallel: 并行度
        test_file: 指定测试文件
        timeout: 超时时间（秒）
        register_task: 任务注册函数（可选，用于支持取消）
        deregister_task: 任务注销函数（可选，用于支持取消）

    Returns:
        {
            "exit_code": int,
            "status": "pass" | "fail",
            "total": int,
            "passed": int,
            "failed": int,
            "error": int,
            "skipped": int,
            "duration_seconds": float,
            "summary": str,
            "command": str,
            "module": str,
            "marker": str,
            "failure_output": str (if failed),
            "suggestion": str (if failed),
        }
    """
    # 延迟导入以避免循环
    from aitest.runtime.paths import get_test_project_root

    # 使用提供的任务管理器，或默认无操作版本
    if register_task is None:
        register_task = _default_register_task
    if deregister_task is None:
        deregister_task = _default_deregister_task

    zjsn = get_test_project_root()
    if not zjsn:
        return {
            "status": "error",
            "error_code": "PRECONDITION_FAILED",
            "error": "No test project configured",
            "suggestion": "使用 aitest project set --id=<project> 设置活跃项目。",
        }

    script_dir = zjsn / "script" / module if module else zjsn / "script"
    allure_dir = zjsn / "allure-results"

    if not script_dir.exists():
        return {
            "status": "error",
            "error_code": "FILE_NOT_FOUND",
            "error": f"Test directory not found: script/{module}/",
            "suggestion": f"Module '{module}' 尚未创建测试脚本。使用 run_sop module={module} 从零开始。",
        }

    test_files = list(script_dir.glob("test_*.py"))
    if not test_files:
        return {
            "status": "error",
            "error_code": "PRECONDITION_FAILED",
            "error": f"No test_*.py found in script/{module}/",
            "suggestion": f"Module '{module}' 尚无测试脚本。使用 run_automation_agent module={module} 先生成代码。",
        }

    if test_file:
        import os
        target = str(script_dir / test_file) if not os.path.isabs(test_file) else test_file
        if not os.path.exists(target):
            return {
                "status": "error",
                "error_code": "INVALID_PARAMS",
                "error": f"Test file not found: {test_file}",
                "suggestion": f"可用的测试文件: {[f.name for f in sorted(test_files)]}",
            }
    else:
        target = str(script_dir)

    cmd = ["pytest", target, "-v", "--tb=short", f"--alluredir={allure_dir}"]
    if marker:
        cmd.extend(["-m", marker])
    if parallel and parallel > 1:
        cmd.extend(["-n", str(parallel), "--dist=loadfile"])
    elif marker == "destructive":
        cmd.append("-q")

    # 注册任务以支持取消
    task_handle = register_task("run_pytest")
    start_time = time.time()
    stdout = ""
    stderr = ""

    try:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            cwd=str(zjsn), encoding='utf-8', errors='replace'
        )
        stdout_chunks = []
        stderr_chunks = []

        while process.poll() is None:
            if task_handle.is_cancelled():
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                deregister_task(task_handle.task_id)
                return {
                    "status": "cancelled",
                    "error_code": "EXECUTION_FAILED",
                    "error": "pytest execution cancelled by user request",
                    "suggestion": f"任务 {task_handle.task_id} 已被取消。",
                    "retryable": True,
                    "cancelled_task_id": task_handle.task_id,
                    "partial_stdout": "".join(stdout_chunks)[-500:],
                }
            if time.time() - start_time > timeout:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                deregister_task(task_handle.task_id)
                return {
                    "status": "timeout",
                    "error_code": "EXECUTION_TIMEOUT",
                    "error": f"pytest execution timed out after {timeout}s",
                    "suggestion": "建议减小测试范围或增加 timeout 参数。",
                    "retryable": True,
                    "timeout_seconds": timeout,
                }

            try:
                out_chunk = process.stdout.read(4096) if process.stdout else ""
                err_chunk = process.stderr.read(4096) if process.stderr else ""
                if out_chunk:
                    stdout_chunks.append(out_chunk)
                if err_chunk:
                    stderr_chunks.append(err_chunk)
            except Exception:
                pass
            time.sleep(min(1.0, 0.5))

        # 读取剩余输出
        try:
            remaining_stdout, remaining_stderr = process.communicate(timeout=5)
            if remaining_stdout:
                stdout_chunks.append(remaining_stdout)
            if remaining_stderr:
                stderr_chunks.append(remaining_stderr)
        except Exception:
            pass

        stdout = "".join(stdout_chunks)
        stderr = "".join(stderr_chunks)
        exit_code = process.returncode
        deregister_task(task_handle.task_id)

    except Exception as e:
        deregister_task(task_handle.task_id)
        return {
            "status": "error",
            "error_code": "INTERNAL_ERROR",
            "error": f"pytest process error: {str(e)}",
            "suggestion": "检查 pytest 环境和 Python 路径。",
            "retryable": False,
        }

    duration = round(time.time() - start_time, 2)

    # 解析 pytest 输出
    summary_line = ""
    for line in stdout.split("\n"):
        if "passed" in line or "failed" in line or "error" in line:
            summary_line = line.strip()
            break

    # 提取失败详情
    failure_lines = []
    in_failure = False
    for line in stdout.split("\n"):
        if line.startswith("FAILED") or line.startswith("ERROR"):
            in_failure = True
        if in_failure:
            failure_lines.append(line)
            if line.strip().startswith("_") and "ERROR" not in line:
                in_failure = False
    failure_output = "\n".join(failure_lines[-50:]) if failure_lines else stderr[-1000:]

    # 统计解析
    passed = failed = error = skipped = 0
    try:
        passed = int(re.search(r"(\d+)\s*passed", summary_line).group(1)) if "passed" in summary_line else 0
        failed = int(re.search(r"(\d+)\s*failed", summary_line).group(1)) if "failed" in summary_line else 0
        error = int(re.search(r"(\d+)\s*error", summary_line).group(1)) if "error" in summary_line else 0
        skipped = int(re.search(r"(\d+)\s*skipped", summary_line).group(1)) if "skipped" in summary_line else 0
    except (ValueError, AttributeError):
        pass

    total = passed + failed + error + skipped

    response_data = {
        "exit_code": exit_code,
        "total": total, "passed": passed, "failed": failed, "error": error, "skipped": skipped,
        "duration_seconds": duration,
        "summary": summary_line or "No summary line found",
        "command": " ".join(cmd),
        "module": module, "marker": marker,
    }

    if exit_code != 0:
        response_data["status"] = "fail"
        response_data["failure_output"] = failure_output[:3000]
        response_data["suggestion"] = (
            f"{failed} failed, {error} errors. "
            f"建议: ① 检查 failure_output ② 使用 rag_search_known_issues 搜索已知问题 ③ 使用 bug-analysis-agent 自动分析"
        )
    else:
        response_data["status"] = "pass"

    return response_data
