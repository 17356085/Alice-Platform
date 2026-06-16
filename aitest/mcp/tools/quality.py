"""Tool: check_code_quality — 8 条代码红线扫描。"""
import json
import subprocess

from aitest.mcp.config import CODE_QUALITY_SCRIPT, ZJSN_TEST
from aitest.mcp.error_taxonomy import ErrorCode, error_response


def run_code_quality_check(target: str = "", staged: bool = False) -> dict:
    """运行代码质量扫描器，返回结构化结果。"""
    if not CODE_QUALITY_SCRIPT.exists():
        return error_response(
            ErrorCode.FILE_NOT_FOUND,
            f"Tool not found: {CODE_QUALITY_SCRIPT}",
            "代码质量检查脚本缺失。",
        )

    cmd = ["python", str(CODE_QUALITY_SCRIPT), "--json"]
    if staged:
        cmd.append("--staged")
    if target:
        cmd.append(target)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                                cwd=str(ZJSN_TEST), encoding='utf-8', errors='replace')
        if result.returncode == 0:
            data = json.loads(result.stdout) if result.stdout.strip() else {"status": "pass", "violations": []}
            data["status"] = "pass"
        else:
            data = json.loads(result.stdout) if result.stdout.strip() else {"status": "fail", "stderr": result.stderr}
            data["status"] = "fail"
        data["exit_code"] = result.returncode
        return data
    except json.JSONDecodeError:
        return error_response(ErrorCode.INTERNAL_ERROR, "Failed to parse code quality output as JSON",
                              f"stdout: {result.stdout[:200]}\nstderr: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        return error_response(ErrorCode.EXECUTION_TIMEOUT, "Code quality check timed out after 60s",
                              "指定 target 参数缩小检查范围。", retryable=True)
    except Exception as e:
        return error_response(ErrorCode.INTERNAL_ERROR, str(e), "请检查 Python 环境和工具依赖。")
