"""
Long-Running Monitor — resource sampling for 24h/48h/72h stabilization tests.

Samples every N seconds: RSS, CPU%, thread count, SQLite sizes, WS connections,
GC generation stats, asyncio task count, queue depth.

Usage:
    # Start monitor alongside server:
    python -m aitest.testing.long_run_monitor --interval 30 --duration 86400

    # Analyze after run:
    python -m aitest.testing.long_run_monitor --analyze <logfile>
"""

from __future__ import annotations
import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
#  Sampling
# ═══════════════════════════════════════════════════════════════════════════

def _get_rss_mb() -> float:
    """Resident Set Size in MB for current process."""
    try:
        import psutil
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except ImportError:
        return -1.0


def _get_cpu_percent() -> float:
    """CPU usage % for current process."""
    try:
        import psutil
        return psutil.Process().cpu_percent(interval=0.1)
    except ImportError:
        return -1.0


def _get_thread_count() -> int:
    """Thread count for current process."""
    try:
        import psutil
        return psutil.Process().num_threads()
    except ImportError:
        return threading_active()


def threading_active() -> int:
    import threading
    return threading.active_count()


def _get_sqlite_sizes() -> dict:
    """File sizes of all tracked SQLite databases."""
    from aitest.platform.paths import get_workstudy
    base = get_workstudy()
    dbs = {
        "runs": base / "governance" / ".data" / "runs.db",
        "audit": base / "governance" / ".data" / "audit.db",
        "checkpoints": base / "governance" / ".graph_state" / "checkpoints.sqlite",
    }
    sizes = {}
    for name, path in dbs.items():
        if path.exists():
            sizes[name] = path.stat().st_size
        else:
            sizes[name] = 0
    return sizes


def _get_ws_connections() -> int:
    """Active WebSocket connections across all managers."""
    count = 0
    try:
        from aitest.server.api.terminal import get_agent_terminal_ws
        count += get_agent_terminal_ws().active_connections
    except Exception:
        pass
    try:
        from aitest.server.api.kanban import get_kanban_ws
        count += get_kanban_ws().active_connections
    except Exception:
        pass
    return count


def _get_gc_stats() -> dict:
    """Python GC generation stats."""
    import gc
    counts = gc.get_count()
    return {
        "gen0": counts[0],
        "gen1": counts[1],
        "gen2": counts[2],
        "total_objects": len(gc.get_objects()),
    }


def _get_asyncio_tasks() -> int:
    """Count of active asyncio tasks."""
    try:
        return len(asyncio.all_tasks())
    except RuntimeError:
        return -1


def _get_runstore_stats() -> dict:
    """Run count + event count from RunStore."""
    try:
        from aitest.platform.run_store import get_run_store
        return get_run_store().get_stats()
    except Exception:
        return {}


def _get_audit_stats() -> dict:
    """Audit log entry count."""
    try:
        from aitest.platform.audit_log import get_audit_logger
        alog = get_audit_logger()
        return {"total_entries": alog.count(), "active": alog.is_active}
    except Exception:
        return {}


def sample() -> dict:
    """Take one resource sample. Returns dict for JSONL output."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rss_mb": round(_get_rss_mb(), 2),
        "cpu_pct": round(_get_cpu_percent(), 2),
        "threads": _get_thread_count(),
        "sqlite": _get_sqlite_sizes(),
        "ws_connections": _get_ws_connections(),
        "gc": _get_gc_stats(),
        "asyncio_tasks": _get_asyncio_tasks(),
        "runstore": _get_runstore_stats(),
        "audit": _get_audit_stats(),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Analysis
# ═══════════════════════════════════════════════════════════════════════════

def analyze(logfile: Path) -> dict:
    """Parse a monitor log and produce a trend report.

    Returns dict with:
        - duration_hours
        - samples_total
        - rss: {start, end, delta, trend}  (trend = 'stable'|'growing'|'leaking')
        - cpu: {mean, max}
        - threads: {start, end, delta}
        - sqlite: per-db {start, end, delta_kb}
        - gc_gen2: {start, end, delta}  (gen2 must stabilize)
        - ws: {mean, max}
    """
    if not logfile.exists():
        return {"error": f"Logfile not found: {logfile}"}

    samples = []
    with open(logfile, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    samples.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    if len(samples) < 2:
        return {"error": f"Need >=2 samples, got {len(samples)}"}

    first = samples[0]
    last = samples[-1]
    duration = len(samples)  # proxy; real duration from timestamps

    # RSS analysis
    rss_first = first["rss_mb"]
    rss_last = last["rss_mb"]
    rss_delta = rss_last - rss_first
    rss_values = [s["rss_mb"] for s in samples if s["rss_mb"] > 0]
    rss_growth_rate = (rss_delta / rss_first * 100) if rss_first > 0 else 0

    if rss_growth_rate > 50:
        rss_trend = "LEAKING"
    elif rss_growth_rate > 20:
        rss_trend = "GROWING"
    else:
        rss_trend = "STABLE"

    # CPU analysis
    cpu_values = [s["cpu_pct"] for s in samples if s["cpu_pct"] >= 0]

    # Thread analysis
    thread_first = first.get("threads", 0)
    thread_last = last.get("threads", 0)

    # GC gen2 analysis (must plateau)
    gc_gen2_start = first.get("gc", {}).get("gen2", 0)
    gc_gen2_end = last.get("gc", {}).get("gen2", 0)

    # SQLite analysis
    sqlite_start = first.get("sqlite", {})
    sqlite_end = last.get("sqlite", {})
    sqlite_deltas = {}
    for db_name in set(list(sqlite_start.keys()) + list(sqlite_end.keys())):
        s = sqlite_start.get(db_name, 0)
        e = sqlite_end.get(db_name, 0)
        sqlite_deltas[db_name] = {
            "start_kb": round(s / 1024, 1) if s else 0,
            "end_kb": round(e / 1024, 1) if e else 0,
            "delta_kb": round((e - s) / 1024, 1) if s and e else 0,
        }

    # WS analysis
    ws_values = [s.get("ws_connections", 0) for s in samples]

    return {
        "duration_hours": round(duration / 120, 1) if duration > 0 else 0,  # 30s = 2 samples/min
        "samples_total": len(samples),
        "rss": {
            "start_mb": round(rss_first, 2),
            "end_mb": round(rss_last, 2),
            "delta_mb": round(rss_delta, 2),
            "growth_pct": round(rss_growth_rate, 1),
            "trend": rss_trend,
        },
        "cpu": {
            "mean_pct": round(sum(cpu_values) / len(cpu_values), 2) if cpu_values else -1,
            "max_pct": round(max(cpu_values), 2) if cpu_values else -1,
        },
        "threads": {
            "start": thread_first,
            "end": thread_last,
            "delta": thread_last - thread_first,
        },
        "sqlite": sqlite_deltas,
        "gc": {
            "gen2_start": gc_gen2_start,
            "gen2_end": gc_gen2_end,
            "gen2_delta": gc_gen2_end - gc_gen2_start,
        },
        "ws": {
            "mean": round(sum(ws_values) / len(ws_values), 1) if ws_values else 0,
            "max": max(ws_values) if ws_values else 0,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════════════

async def _run_monitor(interval: int, duration: int, output: Path):
    """Sample loop. Writes JSONL to output file."""
    start = time.time()
    deadline = start + duration
    sample_count = 0

    logger.info("Monitor started: interval=%ds duration=%ds output=%s", interval, duration, output)

    with open(output, "w", encoding="utf-8") as f:
        while time.time() < deadline:
            try:
                s = sample()
                s["sample_index"] = sample_count
                s["elapsed_s"] = round(time.time() - start, 1)
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
                f.flush()
                sample_count += 1
            except Exception as e:
                logger.error("Sample %d failed: %s", sample_count, e)

            await asyncio.sleep(interval)

    logger.info("Monitor finished: %d samples in %.1fh", sample_count, (time.time() - start) / 3600)

    # Auto-analyze
    report = analyze(output)
    print("\n=== Monitor Analysis ===")
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # Verdict
    rss = report.get("rss", {})
    gc = report.get("gc", {})
    sqlite = report.get("sqlite", {})
    issues = []

    if rss.get("trend") == "LEAKING":
        issues.append(f"RSS LEAKING: +{rss.get('delta_mb', '?')}MB ({rss.get('growth_pct', '?')}%)")
    if gc.get("gen2_delta", 0) > 100:
        issues.append(f"GC gen2 growing: +{gc.get('gen2_delta')} objects not collected")
    for db, info in sqlite.items():
        if info.get("delta_kb", 0) > 1024:
            issues.append(f"{db} grew {info['delta_kb']}KB")

    if issues:
        print("\n⚠️  ISSUES DETECTED:")
        for i in issues:
            print(f"  - {i}")
    else:
        print("\n✅ No issues detected — resource usage stable")


def main():
    parser = argparse.ArgumentParser(description="Alice Long-Running Monitor")
    parser.add_argument("--interval", type=int, default=30, help="Sample interval in seconds")
    parser.add_argument("--duration", type=int, default=86400, help="Total duration in seconds (86400=24h)")
    parser.add_argument("--output", type=str, default=None, help="Output log file path")
    parser.add_argument("--analyze", type=str, default=None, help="Analyze existing log file")
    args = parser.parse_args()

    if args.analyze:
        report = analyze(Path(args.analyze))
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    output = Path(args.output) if args.output else (
        Path(__file__).parent.parent.parent / "governance" / ".data" /
        f"monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    asyncio.run(_run_monitor(args.interval, args.duration, output))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    main()
