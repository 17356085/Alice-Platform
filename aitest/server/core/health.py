"""Health check endpoint — component status aggregation.
Extracted from main.py (P0-2 split, 2026-06-25).
"""
from __future__ import annotations


async def get_health_response() -> dict:
    """Aggregate health status across all platform components."""
    from aitest.infra.task_queue import get_queue
    from aitest.infra.error_logger import get_summary as error_summary

    components: dict = {}
    overall = "healthy"

    # Task Queue
    try:
        queue = get_queue()
        components["task_queue"] = {"status": "ok", "stats": queue.count_by_status()}
    except Exception as e:
        components["task_queue"] = {"status": "error", "error": str(e)[:100]}
        overall = "degraded"

    # RAG / ChromaDB
    try:
        from aitest.knowledge.rag_engine import get_chroma_client
        client = get_chroma_client()
        colls = client.list_collections()
        components["rag"] = {"status": "connected", "collections": len(colls),
                             "total_docs": sum(c.count() for c in colls),
                             "names": [c.name for c in colls]}
    except Exception as e:
        components["rag"] = {"status": "disconnected", "error": str(e)[:100]}
        overall = "degraded"

    # Known Issues
    try:
        from aitest.knowledge.rag_engine import _known_issues_mtime, KNOWN_ISSUES
        yaml_mtime = KNOWN_ISSUES.stat().st_mtime if KNOWN_ISSUES.exists() else 0
        components["known_issues"] = {
            "status": "synced" if _known_issues_mtime >= yaml_mtime else "stale",
            "yaml_mtime": yaml_mtime, "index_mtime": _known_issues_mtime,
        }
    except Exception as e:
        components["known_issues"] = {"status": "error", "error": str(e)[:100]}

    # Error Log
    try:
        summary = error_summary(days=1)
        components["error_log"] = {"status": "ok", "recent_24h": summary["total"],
                                   "by_severity": summary.get("by_severity", {})}
    except Exception as e:
        components["error_log"] = {"status": "error", "error": str(e)[:100]}

    # Checkpoint DB
    try:
        from aitest.graphs.checkpoint import DB_PATH, list_runs
        components["checkpoint_db"] = {
            "status": "connected" if DB_PATH.exists() else "empty",
            "path": str(DB_PATH), "recent_runs": len(list_runs(limit=5)),
        }
    except Exception as e:
        components["checkpoint_db"] = {"status": "error", "error": str(e)[:100]}

    # LLM Provider
    try:
        from aitest.config import config
        provider = config.resolve_llm_provider()
        components["llm"] = {"status": "ok", "resolved_provider": provider}
        from aitest.llm.circuit_breaker import get_all_metrics
        cb_metrics = get_all_metrics()
        if cb_metrics:
            open_breakers = [m for m in cb_metrics if m["state"] == "open"]
            components["llm"]["circuit_breakers"] = {
                "total": len(cb_metrics), "open": len(open_breakers),
                "details": {m["name"]: m["state"] for m in cb_metrics},
            }
    except Exception as e:
        components["llm"] = {"status": "error", "error": str(e)[:100]}
        if overall == "healthy":
            overall = "degraded"

    # Session DB
    try:
        from aitest.server.session_store import engine
        components["session_db"] = {"status": "connected"}
    except Exception as e:
        components["session_db"] = {"status": "error", "error": str(e)[:100]}

    # Tenants
    try:
        from aitest.platform.tenant import get_tenant_manager
        tenants = get_tenant_manager().list_tenants()
        components["tenants"] = {"status": "ok", "count": len(tenants), "ids": tenants}
    except Exception as e:
        components["tenants"] = {"status": "error", "error": str(e)[:100]}

    # Cache
    try:
        from aitest.infra.cache_layer import cache
        components["cache"] = {"status": "ok", "total_saved_tokens": cache.all_saved_tokens(),
                               "stores": cache.stats()}
    except Exception as e:
        components["cache"] = {"status": "error", "error": str(e)[:100]}

    # Worker Pool
    try:
        from aitest.infra.worker_pool import get_worker_pool
        stats = get_worker_pool().stats()
        components["worker_pool"] = {
            "status": "ok", "max_workers": stats.max_workers,
            "active": stats.active_tasks, "queued": stats.queued_tasks,
            "completed": stats.completed_tasks, "failed": stats.failed_tasks,
            "per_tenant": stats.per_tenant,
        }
    except Exception as e:
        components["worker_pool"] = {"status": "error", "error": str(e)[:100]}

    # Platform Consumers
    try:
        from aitest.platform.audit_log import get_audit_logger
        from aitest.platform.metrics_consumer import get_metrics_consumer
        from aitest.platform.quota_usage import get_quota_usage
        from aitest.platform.billing_hook import get_billing_hook
        from aitest.platform.event_bus import get_bus
        from aitest.platform.run_store import get_run_store
        from aitest.server.api.terminal import get_agent_terminal_ws

        bus = get_bus()
        store = get_run_store()
        tws = get_agent_terminal_ws()
        components["platform"] = {
            "status": "ok", "event_bus_subscribers": bus.subscriber_count,
            "runs_in_store": store.count_runs(),
            "consumers": {
                "audit_logger": get_audit_logger().is_active,
                "metrics_consumer": get_metrics_consumer().is_active,
                "quota_usage": get_quota_usage().is_active,
                "billing_hook": get_billing_hook().is_active,
            },
            "agent_terminal": tws.stats,
        }
        if not all(components["platform"]["consumers"].values()):
            components["platform"]["status"] = "degraded"
            if overall == "healthy":
                overall = "degraded"
    except Exception as e:
        components["platform"] = {"status": "error", "error": str(e)[:100]}
        if overall == "healthy":
            overall = "degraded"

    # Lifecycle
    try:
        from aitest.platform.lifecycle import get_registry
        lr_stats = get_registry().stats()
        components["lifecycle"] = {
            "status": "ok", "alive_objects": lr_stats["alive"],
            "total_disposed": lr_stats["total_disposed"],
            "expired_pending": lr_stats["expired_pending"],
            "by_owner": lr_stats["by_owner"],
        }
    except Exception as e:
        components["lifecycle"] = {"status": "error", "error": str(e)[:100]}

    return {"status": overall, "components": components}
