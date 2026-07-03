"""Background sweep loops — lifecycle + ownership + rate cleanup.
Extracted from main.py lifespan (P0-2 split, 2026-06-25).
"""
from __future__ import annotations
import asyncio
import time


async def lifecycle_sweep_loop(log, lifecycle_registry, memory_guard, ownership_checker, task_guard,
                               audit_logger=None, run_store=None):
    """Unified sweep: lifecycle TTL + session stores + ownership scan + memory guard.

    Args:
        audit_logger: AuditLogger instance. If None, uses get_audit_logger() singleton.
        run_store: RunStore instance. If None, uses get_run_store() singleton.
    """
    await asyncio.sleep(30)  # Let server stabilize before first sweep
    while True:
        await asyncio.sleep(60)
        actions: list[str] = []

        # 1. Lifecycle TTL sweep
        try:
            count = lifecycle_registry.sweep()
            if count:
                actions.append(f"lifecycle_sweep:{count}")
        except Exception:
            pass

        # 2. Chat session cleanup
        try:
            from aitest.server.api.chat import _cleanup_old_sessions
            cleaned = _cleanup_old_sessions()
            if cleaned:
                actions.append(f"chat_cleanup:{cleaned}")
        except Exception:
            pass

        # 3. Onboarding session cleanup
        try:
            from aitest.onboarding.project_onboarding_agent import cleanup_stale_sessions
            cleaned = cleanup_stale_sessions()
            if cleaned:
                actions.append(f"onboarding_cleanup:{cleaned}")
        except Exception:
            pass

        # 4. OwnershipChecker scan (every 5 cycles)
        try:
            if ownership_checker.scan_count == 0 or ownership_checker.scan_count % 5 == 0:
                result = ownership_checker.scan(max_objects=50)
                violations = result.get("violations", [])
                criticals = [v for v in violations if v.get("max_severity") == "critical"]
                if criticals:
                    actions.append(f"ownership_violations:{len(violations)}(critical:{len(criticals)})")
                    for v in criticals[:3]:
                        ext_refs = [r["location"] for r in v.get("external_refs", [])[:2]]
                        log.warning("ownership_violation",
                            lifecycle_id=v["lifecycle_id"], owner=v["owner"], held_by=ext_refs)
        except Exception:
            pass

        # 5. MemoryGuard enforcement
        try:
            guard_result = memory_guard.check()
            if guard_result.get("level") != "normal":
                actions.append(f"memory:{guard_result['level']}")
                log.warning("memory_guard", **guard_result)
        except Exception:
            pass

        # 6. TaskGuard stats
        task_stats = task_guard.stats
        if task_stats["active"] > 20:
            actions.append(f"active_tasks:{task_stats['active']}")

        # 7. Checkpoint retention cleanup (every 6th cycle = ~6min)
        try:
            if ownership_checker.scan_count % 6 == 0:
                from aitest.graphs.checkpoint import cleanup_old_checkpoints, get_checkpoint_stats
                removed = cleanup_old_checkpoints()
                if removed:
                    actions.append(f"checkpoint_cleanup:{removed}")
                else:
                    stats = get_checkpoint_stats()
                    if stats["size_mb"] > 100:
                        actions.append(f"checkpoint_size:{stats['size_mb']}MB")
        except Exception:
            pass

        # 8. Audit log retention (every 6th cycle = ~6min)
        try:
            if ownership_checker.scan_count % 6 == 0:
                if audit_logger is None:
                    from aitest.platform.audit_log import get_audit_logger
                    audit_logger = get_audit_logger()
                alog = audit_logger
                removed = alog.cleanup_old_entries()
                if removed:
                    actions.append(f"audit_cleanup:{removed}")
        except Exception:
            pass

        # 9. RunStore retention (every 6th cycle = ~6min)
        try:
            if ownership_checker.scan_count % 6 == 0:
                if run_store is None:
                    from aitest.platform.run_store import get_run_store
                    run_store = get_run_store()
                rs = run_store
                removed = rs.cleanup_old_runs()
                if removed:
                    actions.append(f"runstore_cleanup:{removed}")
                else:
                    rs_stats = rs.get_stats()
                    if rs_stats["event_count"] > 10000:
                        actions.append(f"runstore_events:{rs_stats['event_count']}")
        except Exception:
            pass

        # 10. Governance event file cleanup (every 6th cycle)
        try:
            if ownership_checker.scan_count % 6 == 0:
                from aitest.audit_engine.event_bus import cleanup_old_events
                removed = cleanup_old_events()
                if removed:
                    actions.append(f"eventfile_cleanup:{removed}")
        except Exception:
            pass

        if actions:
            log.info("sweep_cycle", actions=", ".join(actions))


async def rate_state_cleanup_loop(rate_state: dict, rate_lock, rate_window: int):
    """Sweep rate_state every 10 minutes to remove IPs with no recent activity."""
    while True:
        await asyncio.sleep(600)
        now = time.time()
        window_start = now - rate_window
        with rate_lock:
            stale_ips = [
                ip for ip, ts_list in rate_state.items()
                if not [t for t in ts_list if t > window_start]
            ]
            for ip in stale_ips:
                rate_state.pop(ip, None)
