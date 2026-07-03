"""
ReportConsumer — AI-generated execution summary on run completion. v3 Epic 4.

Subscribes to run.completed and run.failed events.
Aggregates Run + RunEvent data, calls LLM, persists report as Artifact.

Pure consumer. No modification to Frozen Core.

Usage:
    from aitest.platform.hooks.report_consumer import ReportConsumer, get_report_consumer

    rc = get_report_consumer()
    rc.start()   # subscribes to EventBus
    report = rc.get_report("run-abc123")  # get cached report
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from datetime import datetime, timezone

from ..consumer import RunEventConsumer
from ..run_event import RunEvent, EventType, RunCompletedData, RunFailedData, EventDataKey as K
from ..event_bus import get_bus
from ..config_registry import cfg
from aitest.infra.logging import get_logger

_log = get_logger(__name__)


def _report_dir() -> Path:
    return cfg.reports_dir


class ReportConsumer:
    """Auto-generate AI execution summary on run completion.

    Listens to run.completed / run.failed → aggregates data → calls LLM → saves report.

    Args:
        store: RunStore instance. If None, uses get_run_store() singleton.
        bus: EventBus instance. If None, uses get_bus() singleton.
    """

    def __init__(self, store=None, bus=None):
        self._dir = _report_dir()
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._active = False
        self._reports: dict[str, dict] = {}   # run_id → report dict
        self._pending: set[str] = set()       # run_ids being generated
        # v3.2: Always resolve store — no lazy singleton in methods
        if store is None:
            from ..run_store import get_run_store
            store = get_run_store()
        self._store = store
        self._bus = bus       # injected EventBus (None = lazy singleton)

    # ── Lifecycle ───────────────────────────────────────────────────────

    def start(self):
        if self._active:
            return
        bus = self._bus or get_bus()
        bus.subscribe(EventType.RUN_COMPLETED, self._on_run_completed, priority=20)  # NORMAL: aggregation
        bus.subscribe(EventType.RUN_FAILED, self._on_run_failed, priority=20)
        self._active = True
        _log.info("ReportConsumer started")

    def stop(self):
        if not self._active:
            return
        bus = self._bus or get_bus()
        bus.unsubscribe(EventType.RUN_COMPLETED, self._on_run_completed)
        bus.unsubscribe(EventType.RUN_FAILED, self._on_run_failed)
        self._active = False
        _log.info("ReportConsumer stopped")

    @property
    def is_active(self) -> bool:
        return self._active

    # ── Handlers ────────────────────────────────────────────────────────

    def _on_run_completed(self, event: RunEvent):
        self._generate_report(event, status="completed")

    def _on_run_failed(self, event: RunEvent):
        self._generate_report(event, status="failed")

    def _generate_report(self, event: RunEvent, status: str):
        run_id = event.run_id
        if run_id in self._pending or run_id in self._reports:
            return

        self._pending.add(run_id)

        try:
            # Gather data
            report = self._build_report(run_id, status, event)
            if report:
                with self._lock:
                    self._reports[run_id] = report
                self._persist_report(run_id, report)
        except Exception as e:
            _log.warning(f"Report generation failed for {run_id}: {e}")
        finally:
            self._pending.discard(run_id)

    # ── Report building ─────────────────────────────────────────────────

    def _build_report(self, run_id: str, status: str, event: RunEvent) -> dict | None:
        """Aggregate data and optionally call LLM for summary."""
        from ..timeline import build_timeline

        run = self._store.load_run(run_id)
        if run is None:
            return None

        events = self._store.list_events(run_id, limit=500)
        timeline = build_timeline(run_id)

        # ── Compute stats ──
        phase_events = [e for e in events if e.event_type in (
            EventType.PHASE_STARTED, EventType.PHASE_COMPLETED
        )]
        phases_set: set[str] = set()
        for e in phase_events:
            d = e.data if isinstance(e.data, dict) else {}
            name = d.get("phase", "")
            if name:
                phases_set.add(name)

        artifact_count = sum(1 for e in events if e.event_type == EventType.ARTIFACT_CREATED)
        llm_call_count = sum(1 for e in events if "llm" in e.event_type.lower() or "agent" in e.event_type.lower())
        error_events = [e for e in events if "fail" in e.event_type.lower() or "error" in e.event_type.lower()]

        # Duration
        started = run.created_at
        ended = run.completed_at or started
        duration_ms = 0
        try:
            s = datetime.fromisoformat(started)
            e = datetime.fromisoformat(ended)
            duration_ms = int((e - s).total_seconds() * 1000)
        except Exception:
            pass

        # ── Build structured report ──
        report = {
            "run_id": run_id,
            "request_id": run.request_id,
            "status": status,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "header": {
                "agent": run.agent,
                "module": run.module,
                "pages": run.pages,
                "mode": run.mode,
                "capability": run.capability,
                "triggered_by": run.triggered_by,
                "created_at": run.created_at,
                "completed_at": run.completed_at,
            },
            "summary": {
                "duration_ms": duration_ms,
                "duration_display": _format_duration(duration_ms),
                "total_tokens": run.total_tokens,
                "total_cost": run.total_cost,
                "agent_runs": run.agent_runs,
                "phases": sorted(phases_set),
                "phase_count": len(phases_set),
                "artifact_count": artifact_count,
                "llm_call_count": llm_call_count,
                "event_count": len(events),
                "error_count": len(error_events),
                "success": status == "completed",
            },
            "issues": [],
            "suggestions": [],
            "timeline_summary": [e.get("message", "") for e in timeline[-10:]],
        }

        # Detect issues
        if duration_ms > 60_000:
            report["issues"].append({
                "severity": "warning",
                "message": f"执行耗时较高 ({_format_duration(duration_ms)})",
                "suggestion": "考虑启用并行执行模式或减少页面数量",
            })
        if error_events:
            report["issues"].append({
                "severity": "error" if status == "failed" else "warning",
                "message": f"检测到 {len(error_events)} 个错误事件",
                "suggestion": "查看 Timeline 定位失败步骤",
            })
        if llm_call_count > 20:
            report["issues"].append({
                "severity": "info",
                "message": f"LLM 调用次数较多 ({llm_call_count})",
                "suggestion": "考虑启用 prompt 缓存或降低模型 tier",
            })

        # Suggestions
        if run.total_cost > 0.5:
            report["suggestions"].append({
                "message": f"成本 ${run.total_cost:.4f}，考虑对非关键模块使用 econ tier",
            })
        if len(run.pages) > 5 and run.mode != "parallel":
            report["suggestions"].append({
                "message": f"{len(run.pages)} 个页面串行执行，推荐启用 parallel 模式",
            })
        if run.total_tokens > 100_000:
            report["suggestions"].append({
                "message": "Token 用量较高，检查 prompt 是否可精简",
            })

        return report

    # ── Storage ─────────────────────────────────────────────────────────

    def _persist_report(self, run_id: str, report: dict):
        """Write report to JSON file."""
        file = self._dir / f"report_{run_id}.json"
        try:
            file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            _log.warning(f"Failed to persist report {run_id}: {e}")

    def get_report(self, run_id: str) -> dict | None:
        """Get cached report. Falls back to disk."""
        with self._lock:
            if run_id in self._reports:
                return self._reports[run_id]

        # Try disk
        file = self._dir / f"report_{run_id}.json"
        if file.exists():
            try:
                report = json.loads(file.read_text(encoding="utf-8"))
                with self._lock:
                    self._reports[run_id] = report
                return report
            except Exception:
                pass
        return None

    def list_reports(self, limit: int = 50) -> list[dict]:
        """List all generated reports."""
        reports = []
        for f in sorted(self._dir.glob("report_*.json"), reverse=True):
            try:
                r = json.loads(f.read_text(encoding="utf-8"))
                reports.append({
                    "run_id": r.get("run_id", ""),
                    "status": r.get("status", ""),
                    "generated_at": r.get("generated_at", ""),
                    "module": r.get("header", {}).get("module", ""),
                    "agent": r.get("header", {}).get("agent", ""),
                    "duration": r.get("summary", {}).get("duration_display", ""),
                    "tokens": r.get("summary", {}).get("total_tokens", 0),
                    "cost": r.get("summary", {}).get("total_cost", 0),
                    "issues": len(r.get("issues", [])),
                })
            except Exception:
                pass
            if len(reports) >= limit:
                break
        return reports


def _format_duration(ms: int) -> str:
    if ms < 1000:
        return f"{ms}ms"
    if ms < 60_000:
        return f"{ms / 1000:.1f}s"
    m = ms // 60_000
    s = (ms % 60_000) // 1000
    return f"{m}m {s}s"


# ── Singleton ──────────────────────────────────────────────────────────────

_report_consumer: ReportConsumer | None = None
_report_lock = threading.Lock()


def get_report_consumer(store=None, bus=None) -> ReportConsumer:
    """Get the global ReportConsumer singleton. Creates one on first call.

    Args:
        store: RunStore instance to inject. Only used on first creation.
        bus: EventBus instance to inject. Only used on first creation.
    """
    global _report_consumer
    with _report_lock:
        if _report_consumer is None:
            _report_consumer = ReportConsumer(store=store, bus=bus)
        return _report_consumer
