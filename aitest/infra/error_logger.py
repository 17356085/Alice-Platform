"""
Structured Error Logger — P0-2: 替换全项目 30+ 处静默异常。

设计原则:
  - 不改变现有异常处理的控制流（该 continue 的仍然 continue）
  - 将静默的 `except Exception: pass` 替换为 `except Exception: log_error(...)`
  - JSONL 持久化，支持按时间/组件/操作查询
  - 零外部依赖，纯标准库实现

用法:
    from aitest.infra.error_logger import log_error

    # 替换前:
    except Exception:
        pass

    # 替换后:
    except Exception as e:
        log_error("sop_graph.preflight", "allure_scan", e, {"module": module})

CLI:
    aitest errors recent        # 最近 20 条错误
    aitest errors summary       # 按组件汇总
    aitest errors clean         # 清理 7 天前的错误
"""

import json
import logging
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# ── 路径配置 ──────────────────────────────────────────────────────────
WORKSTUDY = Path(__file__).resolve().parent.parent.parent
ERROR_DIR = WORKSTUDY / "governance" / ".errors"
ERROR_LOG = ERROR_DIR / "error_log.jsonl"

# ── 线程安全锁 ──────────────────────────────────────────────────────
_write_lock = threading.Lock()

# ── 标准 logging 兜底 ────────────────────────────────────────────────
_logger = logging.getLogger("aitest.error")


def _ensure_dir() -> None:
    """确保错误日志目录存在。"""
    ERROR_DIR.mkdir(parents=True, exist_ok=True)


def log_error(
    component: str,
    operation: str,
    error: Exception,
    context: dict = None,
    severity: str = "warning",
) -> dict:
    """
    记录结构化错误日志到 JSONL 文件。

    参数:
        component: 组件名 (e.g. "sop_graph.preflight", "rag_engine.search")
        operation: 操作描述 (e.g. "allure_scan", "rag_query", "event_emit")
        error:     异常对象
        context:   附加上下文 (module, page, run_id 等)
        severity:  "debug" | "info" | "warning" | "error" | "critical"

    返回:
        错误条目字典（可用于进一步处理）

    此函数设计为非侵入式 — 调用后不抛出，不改变现有控制流。
    """
    _ensure_dir()

    entry = {
        "timestamp": datetime.now().isoformat(),
        "component": component,
        "operation": operation,
        "error_type": type(error).__name__,
        "error_message": str(error)[:500],
        "severity": severity,
        "context": context or {},
    }

    # 同时输出到标准 logging（方便开发调试）
    log_msg = f"[{component}] {operation}: {type(error).__name__}: {str(error)[:200]}"
    if severity == "error" or severity == "critical":
        _logger.error(log_msg)
    else:
        _logger.warning(log_msg)

    # 线程安全写入 JSONL
    try:
        with _write_lock:
            with open(ERROR_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        # 最后的兜底 — 如果连写日志都失败了，至少输出到 stderr
        import sys
        print(f"[aitest.infra.error_logger FATAL] Cannot write to {ERROR_LOG}: {log_msg}", file=sys.stderr)

    return entry


# ══════════════════════════════════════════════════════════════════════════
#  查询 API
# ══════════════════════════════════════════════════════════════════════════

def list_recent(limit: int = 20, severity: str = None, component: str = None) -> list[dict]:
    """
    列出最近的错误日志。

    参数:
        limit:     返回条数上限
        severity:  按严重级别筛选 (None = 全部)
        component: 按组件筛选 (支持子串匹配, None = 全部)

    返回:
        错误条目列表（最近优先）
    """
    _ensure_dir()
    if not ERROR_LOG.exists():
        return []

    entries = []
    try:
        with open(ERROR_LOG, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if severity and entry.get("severity") != severity:
                        continue
                    if component and component not in entry.get("component", ""):
                        continue
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue
    except Exception:
        return []

    # 最近优先
    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return entries[:limit]


def get_summary(days: int = 7) -> dict:
    """
    获取错误汇总：按组件分组计数。

    返回:
        {
            "total": 42,
            "by_component": {"sop_graph.preflight": 3, "rag_engine.search": 10, ...},
            "by_severity": {"warning": 35, "error": 7},
            "since": "2026-06-06T00:00:00",
        }
    """
    _ensure_dir()
    if not ERROR_LOG.exists():
        return {"total": 0, "by_component": {}, "by_severity": {}, "since": ""}

    cutoff = datetime.now() - timedelta(days=days)
    by_component = {}
    by_severity = {}
    total = 0

    try:
        with open(ERROR_LOG, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    ts = datetime.fromisoformat(entry.get("timestamp", "2000-01-01T00:00:00"))
                    if ts < cutoff:
                        continue
                    total += 1
                    comp = entry.get("component", "unknown")
                    sev = entry.get("severity", "warning")
                    by_component[comp] = by_component.get(comp, 0) + 1
                    by_severity[sev] = by_severity.get(sev, 0) + 1
                except (json.JSONDecodeError, ValueError):
                    continue
    except Exception:
        return {"total": 0, "by_component": {}, "by_severity": {}, "since": str(cutoff)}

    return {
        "total": total,
        "by_component": dict(sorted(by_component.items(), key=lambda x: -x[1])),
        "by_severity": by_severity,
        "since": cutoff.isoformat(),
    }


def cleanup_old(days: int = 7) -> int:
    """
    清理 N 天前的错误日志。

    返回: 删除的条目数
    """
    _ensure_dir()
    if not ERROR_LOG.exists():
        return 0

    cutoff = datetime.now() - timedelta(days=days)
    kept = []
    deleted = 0

    try:
        with open(ERROR_LOG, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    ts = datetime.fromisoformat(entry.get("timestamp", "2000-01-01T00:00:00"))
                    if ts >= cutoff:
                        kept.append(line)
                    else:
                        deleted += 1
                except (json.JSONDecodeError, ValueError):
                    deleted += 1  # 损坏的行也删除

        with open(ERROR_LOG, "w", encoding="utf-8") as f:
            for line in kept:
                f.write(line + "\n")
    except Exception:
        return 0

    return deleted
