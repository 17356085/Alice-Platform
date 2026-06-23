"""Tools: run_pytest + run_sop (LangGraph orchestrator)。"""
import os
import re
import json
import time
import subprocess
import traceback as _traceback

from aitest.mcp.config import CONTEXT_MODULES
from aitest.mcp.error_taxonomy import ErrorCode, error_response
from aitest.mcp.cancellation import register_task, deregister_task
from aitest.mcp.tools.status import get_module_status
from aitest.platform.paths import get_test_project_root


def run_pytest(module: str = "", marker: str = "", parallel: int = 1,
               test_file: str = "", timeout: int = 300) -> dict:
    """P0-1: 运行 pytest 测试并返回结构化结果。
    P2-4: 支持通过 cancel_task Tool 中途取消。"""
    zjsn = get_test_project_root()
    if not zjsn:
        return error_response(
            ErrorCode.PRECONDITION_FAILED,
            "No test project configured",
            "使用 aitest project set --id=<project> 设置活跃项目。",
        )
    script_dir = zjsn / "script" / module if module else zjsn / "script"
    allure_dir = zjsn / "allure-results"

    if not script_dir.exists():
        return error_response(
            ErrorCode.FILE_NOT_FOUND,
            f"Test directory not found: script/{module}/",
            f"Module '{module}' 尚未创建测试脚本。使用 run_sop module={module} 从零开始。",
        )

    test_files = list(script_dir.glob("test_*.py"))
    if not test_files:
        return error_response(
            ErrorCode.PRECONDITION_FAILED,
            f"No test_*.py found in script/{module}/",
            f"Module '{module}' 尚无测试脚本。使用 run_automation_agent module={module} 先生成代码。",
        )

    if test_file:
        target = str(script_dir / test_file) if not os.path.isabs(test_file) else test_file
        if not os.path.exists(target):
            return error_response(
                ErrorCode.INVALID_PARAMS,
                f"Test file not found: {test_file}",
                f"可用的测试文件: {[f.name for f in sorted(test_files)]}",
            )
    else:
        target = str(script_dir)

    cmd = ["pytest", target, "-v", "--tb=short", f"--alluredir={allure_dir}"]
    if marker:
        cmd.extend(["-m", marker])
    if parallel and parallel > 1:
        cmd.extend(["-n", str(parallel), "--dist=loadfile"])
    elif marker == "destructive":
        cmd.append("-q")

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
                return error_response(
                    ErrorCode.EXECUTION_FAILED,
                    "pytest execution cancelled by user request",
                    f"任务 {task_handle.task_id} 已被取消。",
                    retryable=True,
                    cancelled_task_id=task_handle.task_id,
                    partial_stdout="".join(stdout_chunks)[-500:],
                )
            if time.time() - start_time > timeout:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                deregister_task(task_handle.task_id)
                return error_response(
                    ErrorCode.EXECUTION_TIMEOUT,
                    f"pytest execution timed out after {timeout}s",
                    "建议减小测试范围或增加 timeout 参数。",
                    retryable=True, timeout_seconds=timeout,
                )

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
        return error_response(ErrorCode.INTERNAL_ERROR, f"pytest process error: {str(e)}",
                              "检查 pytest 环境和 Python 路径。", retryable=False)

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


def run_sop_handler(arguments: dict) -> dict:
    """统一 SOP 编排 — LangGraph 引擎。P2-4: 支持取消。"""
    module = arguments.get("module", "")
    mode = arguments.get("mode", "full")
    pages_str = arguments.get("pages", "")
    provider = arguments.get("provider", "claude")
    pages = [p.strip() for p in pages_str.split(",") if p.strip()] if pages_str else []

    if mode == "status":
        result = get_module_status(module)
        result["mode"] = "status"
        return result

    task_handle = register_task("run_sop")

    try:
        from aitest.graphs.state import create_initial_state
        from aitest.graphs.checkpoint import get_checkpointer
        from aitest.graphs.sop_graph import build_sop_graph

        initial_state = create_initial_state(module=module, pages=pages, mode=mode, provider=provider)
        checkpointer = get_checkpointer()
        graph = build_sop_graph()
        compiled = graph.compile(checkpointer=checkpointer)
        thread = {"configurable": {"thread_id": initial_state["run_id"]}}

        events = []
        from langgraph.types import Command
        state_stream = initial_state
        for event in compiled.stream(state_stream, thread, stream_mode="updates"):
            if task_handle.is_cancelled():
                deregister_task(task_handle.task_id)
                return error_response(
                    ErrorCode.EXECUTION_FAILED,
                    f"run_sop cancelled (task {task_handle.task_id})",
                    f"SOP 已中断于 {events[-1]['phase'] if events else 'initial'} 阶段。使用 run_sop mode=resume 续跑。",
                    retryable=True,
                    cancelled_task_id=task_handle.task_id,
                    completed_phases_before_cancel=[e.get("phase") for e in events],
                )
            if "__interrupt__" in event:
                state_stream = Command(resume="approve")
                continue
            for node_name, update in event.items():
                if isinstance(update, dict):
                    events.append({"node": node_name, "phase": update.get("current_phase", ""),
                                   "completed": update.get("completed_phases", [])})

        deregister_task(task_handle.task_id)
        final = compiled.get_state(thread)
        return {
            "status": final.values.get("status", "completed") if final and final.values else "completed",
            "module": module, "mode": mode, "engine": "langgraph",
            "run_id": initial_state["run_id"], "events": events[-10:],
            "completed_phases": final.values.get("completed_phases", []) if final and final.values else [],
        }
    except Exception as e:
        deregister_task(task_handle.task_id)
        tb = _traceback.format_exc()[-500:]
        return error_response(
            ErrorCode.EXECUTION_FAILED, f"run_sop failed: {str(e)}",
            f"检查模块 '{module}' 的前置文档是否完整。可使用 get_module_status module_name={module} 诊断。",
            retryable=True, module=module, mode=mode, traceback=tb,
        )
