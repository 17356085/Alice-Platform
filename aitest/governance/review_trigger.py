"""
Review Trigger — 审计后阈值检查，自动排队架构评审。

审计器 emit StateDrift/CostAnomaly/SOPViolation 事件。
此模块检查事件累积是否超过阈值，若超过则排队对应的 review mode。

Usage:
  python -m aitest.governance.review_trigger           # 检查并排队
  python -m aitest.governance.review_trigger --dry-run # 仅报告，不排队
  python -m aitest.governance.review_trigger --list    # 查看当前队列
  python -m aitest.governance.review_trigger --clear   # 清空队列
"""

from __future__ import annotations

import json, os, time
from pathlib import Path
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from typing import Optional

WORKSTUDY = Path(__file__).resolve().parent.parent.parent
REVIEW_QUEUE_DIR = WORKSTUDY / "governance" / ".review_queue"

# ── 阈值配置 ─────────────────────────────────────────────
THRESHOLDS = {
    "StateDrift": {
        "max_drift_count": 3,       # drift 累积 >= 3 → 触发 architecture review
        "max_error_count": 1,       # 任一模块 error >= 1 → 立即触发
        "window_hours": 24,         # 时间窗口
    },
    "CostAnomaly": {
        "max_anomalies": 2,         # 成本异常 >= 2 → 触发 cost review
        "max_cost_delta_pct": 50,   # 单次成本增幅 >= 50% → 立即触发
        "window_hours": 24,
    },
    "SOPViolation": {
        "max_violations": 5,        # SOP 违规 >= 5 → 触发 governance review
        "window_hours": 24,
    },
    # 全局阈值: 任意组合达标 → full review
    "global": {
        "min_review_interval_hours": 72,  # 两次 full review 最小间隔
    },
}

# 事件 → review mode 映射
EVENT_TO_MODE = {
    "StateDrift": "architecture",
    "CostAnomaly": "cost",
    "SOPViolation": "governance",
}


@dataclass
class ReviewTask:
    mode: str                          # full / architecture / cost / governance
    reason: str                        # 触发原因
    triggered_by: list[str] = field(default_factory=list)  # 触发事件类型
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    urgency: str = "normal"            # immediate / normal


def _ensure_queue_dir() -> Path:
    REVIEW_QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    return REVIEW_QUEUE_DIR


def _read_event_log() -> list[dict]:
    """读取 Event Bus 持久化日志（最近 7 天）。"""
    log_file = WORKSTUDY / "governance" / "artifacts" / "events.jsonl"
    if not log_file.exists():
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    events = []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                    ts = evt.get("timestamp", "")
                    if ts:
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        if dt < cutoff:
                            continue
                    events.append(evt)
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        pass
    return events


def _count_recent(events: list[dict], event_type: str, window_hours: int) -> list[dict]:
    """统计时间窗口内的特定事件。"""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    recent = []
    for evt in events:
        if evt.get("type") != event_type:
            continue
        ts = evt.get("timestamp", "")
        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if dt >= cutoff:
                    recent.append(evt)
            except (ValueError, AttributeError):
                continue
    return recent


def _last_full_review() -> Optional[datetime]:
    """检查最近一次 full review 时间。"""
    _ensure_queue_dir()
    completed_file = REVIEW_QUEUE_DIR / "completed.json"
    if not completed_file.exists():
        return None
    try:
        data = json.loads(completed_file.read_text(encoding="utf-8"))
        last = data.get("last_full_review")
        if last:
            return datetime.fromisoformat(last)
    except (json.JSONDecodeError, ValueError, KeyError):
        pass
    return None


def check_and_enqueue(dry_run: bool = False) -> list[ReviewTask]:
    """
    检查事件日志，超阈值则排队评审任务。

    Returns: 本次新排队的 ReviewTask 列表。
    """
    events = _read_event_log()
    tasks: list[ReviewTask] = []

    # ── StateDrift 检查 ──
    drifts = _count_recent(events, "StateDrift", THRESHOLDS["StateDrift"]["window_hours"])
    total_drift = sum(e.get("drift_count", 0) for e in drifts)
    max_error = max((e.get("error_count", 0) for e in drifts), default=0)
    if total_drift >= THRESHOLDS["StateDrift"]["max_drift_count"] or \
       max_error >= THRESHOLDS["StateDrift"]["max_error_count"]:
        tasks.append(ReviewTask(
            mode="architecture",
            reason=f"StateDrift: {total_drift} drifts, {max_error} errors in 24h",
            triggered_by=["StateDrift"],
            urgency="immediate" if max_error >= 1 else "normal",
        ))

    # ── CostAnomaly 检查 ──
    anomalies = _count_recent(events, "CostAnomaly", THRESHOLDS["CostAnomaly"]["window_hours"])
    if len(anomalies) >= THRESHOLDS["CostAnomaly"]["max_anomalies"]:
        tasks.append(ReviewTask(
            mode="cost",
            reason=f"CostAnomaly: {len(anomalies)} anomalies in 24h",
            triggered_by=["CostAnomaly"],
            urgency="normal",
        ))

    # ── SOPViolation 检查 ──
    violations = _count_recent(events, "SOPViolation", THRESHOLDS["SOPViolation"]["window_hours"])
    total_violations = sum(e.get("violations", 0) for e in violations)
    if total_violations >= THRESHOLDS["SOPViolation"]["max_violations"]:
        tasks.append(ReviewTask(
            mode="governance",
            reason=f"SOPViolation: {total_violations} violations in 24h",
            triggered_by=["SOPViolation"],
            urgency="normal",
        ))

    # ── 全局: 多事件触发 → 升级为 full ──
    if len(tasks) >= 2:
        # 检查是否满足最小间隔
        last = _last_full_review()
        min_interval = THRESHOLDS["global"]["min_review_interval_hours"]
        if last is None or \
           (datetime.now(timezone.utc) - last).total_seconds() / 3600 >= min_interval:
            # 合并为 full review
            all_events = list(set(sum((t.triggered_by for t in tasks), [])))
            tasks = [ReviewTask(
                mode="full",
                reason=f"Multiple triggers: {', '.join(all_events)} — escalated to full review",
                triggered_by=all_events,
                urgency="immediate",
            )]

    # ── 写入队列 ──
    if tasks and not dry_run:
        _ensure_queue_dir()
        queue_file = REVIEW_QUEUE_DIR / "pending.json"
        existing = []
        if queue_file.exists():
            try:
                existing = json.loads(queue_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        # 去重：同 mode 不重复排队
        existing_modes = {t.get("mode") for t in existing}
        new_entries = [t.__dict__ for t in tasks if t.mode not in existing_modes]
        if new_entries:
            existing.extend(new_entries)
            queue_file.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"[ReviewTrigger] Enqueued {len(new_entries)} review(s): "
                  f"{', '.join(e['mode'] for e in new_entries)}")

    return tasks


def list_queue() -> list[dict]:
    """列出待处理评审。"""
    _ensure_queue_dir()
    queue_file = REVIEW_QUEUE_DIR / "pending.json"
    if not queue_file.exists():
        return []
    try:
        return json.loads(queue_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def mark_completed(mode: str) -> None:
    """标记某次评审已完成。"""
    _ensure_queue_dir()

    # 从 pending 移除
    queue_file = REVIEW_QUEUE_DIR / "pending.json"
    if queue_file.exists():
        try:
            pending = json.loads(queue_file.read_text(encoding="utf-8"))
            pending = [t for t in pending if t.get("mode") != mode]
            queue_file.write_text(json.dumps(pending, indent=2, ensure_ascii=False), encoding="utf-8")
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    # 记录完成时间
    completed_file = REVIEW_QUEUE_DIR / "completed.json"
    completed = {}
    if completed_file.exists():
        try:
            completed = json.loads(completed_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    if mode == "full":
        completed["last_full_review"] = datetime.now().isoformat()
    completed[f"last_{mode}_review"] = datetime.now().isoformat()
    completed_file.write_text(json.dumps(completed, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[ReviewTrigger] Marked '{mode}' review as completed.")


def clear_queue() -> None:
    """清空所有待处理评审。"""
    _ensure_queue_dir()
    queue_file = REVIEW_QUEUE_DIR / "pending.json"
    if queue_file.exists():
        queue_file.write_text("[]", encoding="utf-8")
        print("[ReviewTrigger] Queue cleared.")


def format_queue_summary() -> str:
    """格式化队列摘要供会话使用。"""
    pending = list_queue()
    if not pending:
        return ""

    lines = ["## ⚠️ Pending Architecture Reviews\n"]
    for task in pending:
        urgency_mark = "🔴" if task.get("urgency") == "immediate" else "🟡"
        mode = task.get("mode", "unknown")
        reason = task.get("reason", "")
        created = task.get("created_at", "")[:16].replace("T", " ")
        lines.append(f"- {urgency_mark} **{mode}** review — {reason} _(queued {created})_")

    lines.append(f"\nRun `/review {pending[0]['mode']}` or say \"execute pending reviews\".\n")
    lines.append(f"Queue file: `governance/.review_queue/pending.json`")
    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if "--dry-run" in sys.argv:
        tasks = check_and_enqueue(dry_run=True)
        if tasks:
            print(f"Would enqueue: {[t.mode for t in tasks]}")
        else:
            print("No reviews needed (thresholds not met).")
    elif "--list" in sys.argv:
        pending = list_queue()
        if pending:
            print(json.dumps(pending, indent=2, ensure_ascii=False))
        else:
            print("Queue empty.")
    elif "--clear" in sys.argv:
        clear_queue()
    else:
        tasks = check_and_enqueue()
        if tasks:
            print(json.dumps([t.__dict__ for t in tasks], indent=2, ensure_ascii=False))
        else:
            print("No thresholds exceeded.")
