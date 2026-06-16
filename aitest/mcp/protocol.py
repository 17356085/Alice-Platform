"""
MCP Protocol handlers: list_tools + call_tool (with audit + rate-limit wrapping)。
"""
import os
import json
import time
import datetime as _dt
import subprocess

from mcp.types import Tool, TextContent

from aitest.mcp.tools import TOOL_REGISTRY, TOOL_ALIASES
from aitest.mcp.error_taxonomy import ErrorCode, error_response
from aitest.mcp.audit import AuditRecord, write_audit_log
from aitest.mcp.rate_limit import check_rate_limit, RATE_WINDOW_SECONDS


def build_list_tools_handler():
    """返回 list_tools 处理器。"""
    async def handler() -> list[Tool]:
        seen = set()
        tools = []
        for tdef in TOOL_REGISTRY.values():
            if tdef.name in seen:
                continue
            seen.add(tdef.name)
            tools.append(Tool(name=tdef.name, description=tdef.description,
                            inputSchema=tdef.schema))
        return tools
    return handler


def _safe_json_dumps(obj, **kwargs) -> str:
    """安全的 JSON 序列化——处理 datetime/date 等非标准类型。"""
    return json.dumps(obj, ensure_ascii=False, default=str, **kwargs)


def build_call_tool_handler():
    """返回 call_tool 处理器（含审计日志 + 速率限制）。"""
    async def handler(name: str, arguments: dict) -> list[TextContent]:
        t_start = time.time()

        # 向后兼容别名
        resolved = TOOL_ALIASES.get(name, name)

        # P2-2: 速率限制检查
        allowed, rate_msg = check_rate_limit(resolved)
        if not allowed:
            result = error_response(ErrorCode.PERMISSION_DENIED, rate_msg,
                                    f"等待 {RATE_WINDOW_SECONDS}s 后重试。", retryable=True)
            write_audit_log(AuditRecord(
                timestamp=_dt.datetime.now().isoformat(), tool_name=resolved,
                arguments=arguments, duration_ms=0, status="error",
                error_code=ErrorCode.PERMISSION_DENIED.value,
                result_summary="Rate limited", caller_pid=os.getpid(),
            ))
            return [TextContent(type="text", text=_safe_json_dumps(result))]

        tdef = TOOL_REGISTRY.get(resolved)
        if not tdef:
            result = error_response(ErrorCode.TOOL_NOT_FOUND, f"Unknown tool: {name}",
                                    f"可用 Tools: {sorted(TOOL_REGISTRY.keys())}", retryable=False)
            write_audit_log(AuditRecord(
                timestamp=_dt.datetime.now().isoformat(), tool_name=name,
                arguments=arguments, duration_ms=(time.time() - t_start) * 1000,
                status="error", error_code=ErrorCode.TOOL_NOT_FOUND.value,
                result_summary=f"Unknown tool: {name}", caller_pid=os.getpid(),
            ))
            return [TextContent(type="text", text=_safe_json_dumps(result))]

        try:
            result = tdef.handler(arguments)
            err_code = result.get("error", {}).get("code", "") if isinstance(result, dict) else ""
            # 审计日志：json.dumps 可能因结果含非可序列化对象而失败，独立 try/except 不污染 Tool 结果
            try:
                summary = _safe_json_dumps(result)[:200]
            except Exception:
                summary = str(result)[:200]
            write_audit_log(AuditRecord(
                timestamp=_dt.datetime.now().isoformat(), tool_name=resolved,
                arguments=arguments, duration_ms=(time.time() - t_start) * 1000,
                status="ok" if result.get("status") != "error" else "error",
                error_code=err_code,
                result_summary=summary,
                caller_pid=os.getpid(),
            ))
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            result = error_response(ErrorCode.INVALID_PARAMS, str(e),
                                    "检查参数类型和必填字段是否符合 Tool schema。",
                                    retryable=False, param_error=str(e))
            write_audit_log(AuditRecord(
                timestamp=_dt.datetime.now().isoformat(), tool_name=resolved,
                arguments=arguments, duration_ms=(time.time() - t_start) * 1000,
                status="error", error_code=ErrorCode.INVALID_PARAMS.value,
                result_summary=str(e)[:200], caller_pid=os.getpid(),
            ))
        except subprocess.TimeoutExpired as e:
            result = error_response(ErrorCode.EXECUTION_TIMEOUT, str(e),
                                    "建议增加 timeout 参数或缩小处理范围。", retryable=True)
            write_audit_log(AuditRecord(
                timestamp=_dt.datetime.now().isoformat(), tool_name=resolved,
                arguments=arguments, duration_ms=(time.time() - t_start) * 1000,
                status="error", error_code=ErrorCode.EXECUTION_TIMEOUT.value,
                result_summary=str(e)[:200], caller_pid=os.getpid(),
            ))
        except Exception as e:
            result = error_response(ErrorCode.INTERNAL_ERROR, f"{type(e).__name__}: {str(e)}",
                                    "请联系管理员查看 mcp_server 日志。", retryable=False,
                                    exception_type=type(e).__name__)
            write_audit_log(AuditRecord(
                timestamp=_dt.datetime.now().isoformat(), tool_name=resolved,
                arguments=arguments, duration_ms=(time.time() - t_start) * 1000,
                status="error", error_code=ErrorCode.INTERNAL_ERROR.value,
                result_summary=f"{type(e).__name__}: {str(e)[:150]}",
                caller_pid=os.getpid(),
            ))

        return [TextContent(type="text", text=_safe_json_dumps(result, indent=2))]
    return handler
