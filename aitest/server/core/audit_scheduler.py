"""Background audit scheduler — periodic full audit + review trigger.
Extracted from main.py lifespan (P0-2 split, 2026-06-25).
"""
from __future__ import annotations
import asyncio


async def audit_scheduler_loop(log, audit_interval: int, stop_event: asyncio.Event):
    """Periodic full audit: state + SOP + cost + safety. Triggers review if needed."""
    await asyncio.sleep(60)  # Let server fully initialize
    iteration = 0
    from aitest.audit_engine.scheduled_audit import run_all_audits, discover_modules

    while not stop_event.is_set():
        iteration += 1
        started = asyncio.get_event_loop().time()
        log.info("scheduled_audit_start", iteration=iteration)

        try:
            modules = discover_modules()
            results = await asyncio.to_thread(run_all_audits, modules)

            state_drifts = sum(
                r.get("drift_count", 0)
                for r in results["state_audits"].values()
            )
            sop_violations = sum(
                r.get("violations", 0)
                for r in results["sop_audits"].values()
            )
            cost_info = results.get("cost_audit", {})
            duration = asyncio.get_event_loop().time() - started
            log.info("scheduled_audit_done", iteration=iteration,
                     state_drifts=state_drifts, sop_violations=sop_violations,
                     cost=round(cost_info.get('total_cost', 0), 4),
                     duration_s=round(duration, 1))

            # Check if review trigger needed
            try:
                from aitest.audit_engine.review_trigger import check_and_enqueue, format_queue_summary
                tasks = check_and_enqueue()
                if tasks:
                    summary = format_queue_summary()
                    log.info("review_trigger_enqueued", count=len(tasks), summary=summary)
            except Exception as re:
                log.warning("review_trigger_failed", error=str(re))

        except Exception as e:
            log.error("scheduled_audit_error", iteration=iteration, error=str(e))

        # Wait for next interval (or stop signal)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=audit_interval)
        except asyncio.TimeoutError:
            pass

    log.info("audit_scheduler_stopped", iterations=iteration)
