"""
P0-2: 结构化错误码 (Error Taxonomy)
MCP Tool 错误分类 — 帮助 LLM 理解错误性质并做出正确决策。
"""
import enum
from dataclasses import dataclass, field


class ErrorCode(enum.Enum):
    """MCP Tool 错误分类。"""
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    INVALID_PARAMS = "INVALID_PARAMS"
    PRECONDITION_FAILED = "PRECONDITION_FAILED"
    EXECUTION_TIMEOUT = "EXECUTION_TIMEOUT"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"


@dataclass
class MCPError:
    """结构化错误响应。包含可操作建议供 LLM 直接展示。"""
    code: ErrorCode
    message: str
    suggestion: str = ""
    retryable: bool = False
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {
            "status": "error",
            "error": {
                "code": self.code.value,
                "message": self.message,
                "suggestion": self.suggestion,
                "retryable": self.retryable,
            }
        }
        if self.details:
            d["error"]["details"] = self.details
        return d


def error_response(code: ErrorCode, message: str, suggestion: str = "",
                   retryable: bool = False, **details) -> dict:
    """快捷构造结构化错误响应。"""
    return MCPError(code=code, message=message, suggestion=suggestion,
                    retryable=retryable, details=details).to_dict()


def success_response(data: dict) -> dict:
    """统一成功响应包装。"""
    data["status"] = data.get("status", "ok")
    return data
