"""
P2-3: Tool 执行审计日志
每次 Tool 调用记录到 governance/audit/tool-calls.jsonl。
写入失败静默降级，不中断 Tool 执行。
"""
import json
import os
from dataclasses import dataclass

from aitest.mcp.config import AUDIT_DIR, AUDIT_LOG_FILE


@dataclass
class AuditRecord:
    """单次 Tool 调用的审计记录。"""
    timestamp: str
    tool_name: str
    arguments: dict
    duration_ms: float
    status: str              # "ok" | "error"
    error_code: str          # ErrorCode value 或空字符串
    result_summary: str      # 结果摘要（截断至 200 字符）
    caller_pid: int

    def to_jsonl(self) -> str:
        return json.dumps({
            "ts": self.timestamp,
            "tool": self.tool_name,
            "args": {k: (v[:100] if isinstance(v, str) else v) for k, v in (self.arguments or {}).items()},
            "dur_ms": round(self.duration_ms, 1),
            "status": self.status,
            "err": self.error_code,
            "summary": self.result_summary[:200],
            "pid": self.caller_pid,
        }, ensure_ascii=False)


def write_audit_log(record: AuditRecord) -> None:
    """追加审计记录到 JSONL 文件。自动创建目录，静默失败不中断 Tool 执行。"""
    try:
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(record.to_jsonl() + "\n")
    except Exception:
        pass  # 审计日志写入失败不影响 Tool 执行


def audit_log_filename() -> str:
    """返回当前审计日志文件路径。"""
    return str(AUDIT_LOG_FILE)
