"""Health check endpoint — component status aggregation.
Extracted from main.py (P0-2 split, 2026-06-25).
"""
from __future__ import annotations


async def get_health_response(app_state=None) -> dict:
    """Aggregate health status across all platform components.

    Args:
        app_state: Optional FastAPI app.state for DI. Falls back to singletons.
    """
    components: dict = {}
    overall = "healthy"
    pending_tasks = 0  # P4: aggregate pending tasks from task_queue + worker_pool

    # Task Queue (P4: pending_tasks + dual backend detection)
    try:
        from aitest.infra.queue_factory import get_backend, get_queue
        backend = get_backend()
        queue = get_queue()

        if backend == "redis":
            stats = queue.stats()  # RQ returns extended stats
            pending = stats.get("pending", 0)
            pending_tasks += pending
            components["task_queue"] = {
                "status": "ok" if queue.is_available else "disconnected",
                "backend": "redis",
                "redis_version": stats.get("redis_version", "?"),
                "stats": {k: v for k, v in stats.items()
                         if k not in ("backend", "redis_version", "queue_name")},
                "pending": pending,
            }
        else:
            stats = queue.count_by_status()
            pending = stats.get("pending", 0)
            pending_tasks += pending
            components["task_queue"] = {
                "status": "ok", "backend": "sqlite",
                "stats": stats, "pending": pending,
            }
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
        from aitest.infra.error_logger import get_summary as error_summary
        summary = error_summary(days=1)
        components["error_log"] = {"status": "ok", "recent_24h": summary["total"],
                                   "by_severity": summary.get("by_severity", {})}
    except Exception as e:
        components["error_log"] = {"status": "error", "error": str(e)[:100]}

    # Redis: Cache
    try:
        from aitest.infra.redis_cache import redis_cache
        components["redis_cache"] = redis_cache.stats()
    except Exception as e:
        components["redis_cache"] = {"status": "error", "error": str(e)[:100]}

    # Redis: Session Store
    try:
        from aitest.server.redis_session_store import redis_session_store
        components["redis_session"] = redis_session_store.stats()
    except Exception as e:
        components["redis_session"] = {"status": "error", "error": str(e)[:100]}

    # Redis: PubSub
    try:
        from aitest.infra.redis_pubsub import pubsub_stats
        components["redis_pubsub"] = pubsub_stats()
    except Exception as e:
        components["redis_pubsub"] = {"status": "error", "error": str(e)[:100]}

    # Redis: Rate Limiter
    try:
        from aitest.infra.redis_utils import redis_limiter
        components["redis_ratelimit"] = redis_limiter.stats()
    except Exception as e:
        components["redis_ratelimit"] = {"status": "error", "error": str(e)[:100]}

    # Redis: Vector Search
    try:
        from aitest.knowledge.redis_vector import redis_vector_client
        components["redis_vector"] = redis_vector_client.stats()
    except Exception as e:
        components["redis_vector"] = {"status": "error", "error": str(e)[:100]}

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
        from alice_engine.runtime.core.circuit_breaker import get_all_metrics
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

    # Worker Pool (P4: oldest_active_s + timed_out)
    try:
        from aitest.infra.worker_pool import get_worker_pool
        stats = get_worker_pool().stats()
        pending_tasks += stats.queued_tasks  # P4: worker pool queued = pending
        components["worker_pool"] = {
            "status": "ok", "max_workers": stats.max_workers,
            "active": stats.active_tasks, "queued": stats.queued_tasks,
            "completed": stats.completed_tasks, "failed": stats.failed_tasks,
            "timed_out": stats.timed_out_tasks,
            "oldest_active_s": stats.oldest_active_s,
            "per_tenant": stats.per_tenant,
        }
    except Exception as e:
        components["worker_pool"] = {"status": "error", "error": str(e)[:100]}

    # Execution Worker (v5.4: control plane / execution plane separation)
    try:
        from aitest.platform.execution_worker import get_execution_worker
        worker = get_execution_worker()
        wstats = worker.stats()
        queued_requests = 0
        try:
            from aitest.platform.run_store import get_run_store
            queued_requests = len(get_run_store().list_requests(status="queued", limit=1000))
            pending_tasks += queued_requests
        except Exception:
            pass
        components["execution_worker"] = {
            "status": "ok" if wstats.running else "idle",
            "worker_id": wstats.worker_id,
            "running": wstats.running,
            "claimed": wstats.claimed,
            "completed": wstats.completed,
            "failed": wstats.failed,
            "retried": getattr(wstats, "retried", 0),
            "throttled": getattr(wstats, "throttled", 0),
            "last_claimed_request_id": wstats.last_claimed_request_id,
            "last_error": wstats.last_error,
            "queued_requests": queued_requests,
        }
    except Exception as e:
        components["execution_worker"] = {"status": "error", "error": str(e)[:100]}

    # Platform Consumers — v3.2: DI via app_state, fallback to singletons
    try:
        from aitest.platform.audit_log import get_audit_logger
        from aitest.platform.hooks.metrics_consumer import get_metrics_consumer
        from aitest.platform.hooks.quota_usage import get_quota_usage
        from aitest.platform.hooks.billing_hook import get_billing_hook
        from aitest.platform.event_bus import get_bus
        from aitest.platform.run_store import get_run_store
        from aitest.server.api.terminal import get_agent_terminal_ws

        # DI: prefer app_state instances
        bus = getattr(app_state, 'event_bus', None) or get_bus()
        store = getattr(app_state, 'run_store', None) or get_run_store()
        audit = getattr(app_state, 'audit_logger', None) or get_audit_logger()
        metrics = getattr(app_state, 'metrics_consumer', None) or get_metrics_consumer()
        quota = getattr(app_state, 'quota_usage', None) or get_quota_usage()
        billing = getattr(app_state, 'billing_hook', None) or get_billing_hook()
        tws = get_agent_terminal_ws()
        components["platform"] = {
            "status": "ok", "event_bus_subscribers": bus.subscriber_count,
            "runs_in_store": store.count_runs(),
            "consumers": {
                "audit_logger": audit.is_active,
                "metrics_consumer": metrics.is_active,
                "quota_usage": quota.is_active,
                "billing_hook": billing.is_active,
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

    # Ecosystem control plane — projects, discovery strategies, compatibility
    try:
        from aitest.platform.ecosystem import collect_ecosystem_snapshot
        ecosystem = collect_ecosystem_snapshot()
        components["ecosystem"] = ecosystem
        if ecosystem.get("status") != "healthy" and overall == "healthy":
            overall = "degraded"
    except Exception as e:
        components["ecosystem"] = {"status": "error", "error": str(e)[:100]}
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

    return {"status": overall, "pending_tasks": pending_tasks, "components": components}
