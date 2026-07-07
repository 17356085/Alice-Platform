"""Performance baseline snapshot and hotspot detection.

Phase 6.3 anchors a repeatable baseline for the hottest platform paths:
runtime, provider, knowledge, and memory.

This module deliberately stays lightweight:
  - snapshot current operational metrics
  - collect trace / knowledge / memory state
  - flag hotspots with clear, actionable thresholds
  - optionally persist snapshots for later comparison
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aitest.platform.paths import get_workstudy


BASELINE_DIR = get_workstudy() / "governance" / "kpi" / "timeseries"
BASELINE_FILE = BASELINE_DIR / "performance_baselines.jsonl"


@dataclass
class PerformanceHotspot:
    category: str
    severity: str
    name: str
    metric: str
    suggestion: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "severity": self.severity,
            "name": self.name,
            "metric": self.metric,
            "suggestion": self.suggestion,
        }


@dataclass
class PerformanceBaselineSnapshot:
    ts: str
    runtime: dict[str, Any] = field(default_factory=dict)
    provider: dict[str, Any] = field(default_factory=dict)
    knowledge: dict[str, Any] = field(default_factory=dict)
    memory: dict[str, Any] = field(default_factory=dict)
    worker: dict[str, Any] = field(default_factory=dict)
    hotspots: list[PerformanceHotspot] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ts": self.ts,
            "runtime": self.runtime,
            "provider": self.provider,
            "knowledge": self.knowledge,
            "memory": self.memory,
            "worker": self.worker,
            "hotspots": [item.to_dict() for item in self.hotspots],
        }


class PerformanceBaselineService:
    """Capture baseline state and derive first-order bottlenecks."""

    SLOW_AGENT_P95_S = 30
    LOW_WORKFLOW_RATE = 0.8
    LOW_MEMORY_DOCS = 5

    def capture(
        self,
        *,
        namespace: str = "web-automation",
        run_id: str = "",
        persist: bool = True,
    ) -> PerformanceBaselineSnapshot:
        runtime = self._capture_runtime()
        provider = self._capture_provider(run_id)
        knowledge = self._capture_knowledge(namespace)
        memory = self._capture_memory()
        worker = self._capture_worker()

        snapshot = PerformanceBaselineSnapshot(
            ts=datetime.now(timezone.utc).isoformat(),
            runtime=runtime,
            provider=provider,
            knowledge=knowledge,
            memory=memory,
            worker=worker,
        )
        snapshot.hotspots = self._detect_hotspots(snapshot)

        if persist:
            self._persist(snapshot)

        return snapshot

    def _capture_runtime(self) -> dict[str, Any]:
        try:
            from aitest.platform.operational_metrics import get_collector

            return get_collector().snapshot()
        except Exception as exc:
            return {"error": str(exc)[:200]}

    def _capture_provider(self, run_id: str) -> dict[str, Any]:
        try:
            from aitest.infra.trace import get_trace_summary

            return get_trace_summary(run_id=run_id or None)
        except Exception as exc:
            return {"error": str(exc)[:200]}

    def _capture_knowledge(self, namespace: str) -> dict[str, Any]:
        try:
            from aitest.platform.knowledge import get_knowledge

            store = get_knowledge(namespace=namespace)
            return {
                "namespace": namespace,
                "available": store.available(),
                "collections": store.collection_stats(),
            }
        except Exception as exc:
            return {"namespace": namespace, "available": False, "error": str(exc)[:200]}

    def _capture_memory(self) -> dict[str, Any]:
        try:
            from aitest.platform.testing_memory_store import TestingMemoryStore

            store = TestingMemoryStore()
            return {
                "available": store.available(),
                "collections": store.stats(),
            }
        except Exception as exc:
            return {"available": False, "error": str(exc)[:200]}

    def _capture_worker(self) -> dict[str, Any]:
        try:
            from aitest.platform.execution_worker import get_execution_worker

            return get_execution_worker().stats().__dict__
        except Exception as exc:
            return {"error": str(exc)[:200]}

    def _detect_hotspots(self, snapshot: PerformanceBaselineSnapshot) -> list[PerformanceHotspot]:
        hotspots: list[PerformanceHotspot] = []

        runtime = snapshot.runtime or {}
        for agent, data in runtime.get("agent_latency_p95", {}).items():
            if not isinstance(data, dict):
                continue
            if float(data.get("p95", 0) or 0) >= self.SLOW_AGENT_P95_S:
                hotspots.append(
                    PerformanceHotspot(
                        category="runtime",
                        severity="warning",
                        name=agent,
                        metric=f"p95={data.get('p95', 0)}s",
                        suggestion="优先检查该 agent 的模型调用、上下文长度和缓存命中率。",
                    )
                )

        for module, data in runtime.get("workflow", {}).items():
            if not isinstance(data, dict):
                continue
            rate = float(data.get("rate", 1) or 0)
            if data.get("total", 0) and rate < self.LOW_WORKFLOW_RATE:
                hotspots.append(
                    PerformanceHotspot(
                        category="runtime",
                        severity="warning",
                        name=module,
                        metric=f"success_rate={round(rate * 100)}%",
                        suggestion="优先拆解失败路径，确认是否是 locator、tool 或 knowledge 退化。",
                    )
                )

        provider = snapshot.provider or {}
        if provider.get("total_latency_ms", 0) and provider.get("total_latency_ms", 0) > 30000:
            hotspots.append(
                PerformanceHotspot(
                    category="provider",
                    severity="info",
                    name="trace_latency",
                    metric=f"total_latency_ms={provider.get('total_latency_ms', 0)}",
                    suggestion="评估 provider fallback / retry / context 压缩策略。",
                )
            )

        knowledge = snapshot.knowledge or {}
        collections = knowledge.get("collections", {}) if isinstance(knowledge, dict) else {}
        for name, count in collections.items():
            if isinstance(count, int) and count == 0:
                hotspots.append(
                    PerformanceHotspot(
                        category="knowledge",
                        severity="info",
                        name=name,
                        metric="docs=0",
                        suggestion="检查该 collection 是否尚未初始化，或该项目尚未形成知识沉淀。",
                    )
                )

        memory = snapshot.memory or {}
        mem_collections = memory.get("collections", {}) if isinstance(memory, dict) else {}
        if isinstance(mem_collections, dict):
            total_docs = mem_collections.get("total", 0)
            if isinstance(total_docs, int) and total_docs < self.LOW_MEMORY_DOCS:
                hotspots.append(
                    PerformanceHotspot(
                        category="memory",
                        severity="info",
                        name="testing_memory",
                        metric=f"docs={total_docs}",
                        suggestion="补充高频失败模式与 locator history，避免每次都从零学习。",
                    )
                )

        worker = snapshot.worker or {}
        if worker.get("throttled", 0):
            hotspots.append(
                PerformanceHotspot(
                    category="runtime",
                    severity="warning",
                    name="execution_worker",
                    metric=f"throttled={worker.get('throttled', 0)}",
                    suggestion="检查 tenant capacity 配置与 worker 并发上限。",
                )
            )
        if worker.get("retried", 0):
            hotspots.append(
                PerformanceHotspot(
                    category="runtime",
                    severity="info",
                    name="execution_worker",
                    metric=f"retried={worker.get('retried', 0)}",
                    suggestion="继续观察重试分布，避免 retry 风暴放大底层抖动。",
                )
            )

        return hotspots[:20]

    def _persist(self, snapshot: PerformanceBaselineSnapshot) -> None:
        try:
            BASELINE_DIR.mkdir(parents=True, exist_ok=True)
            with open(BASELINE_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(snapshot.to_dict(), ensure_ascii=False, default=str) + "\n")
        except Exception:
            pass


_service: PerformanceBaselineService | None = None


def get_performance_baseline_service() -> PerformanceBaselineService:
    global _service
    if _service is None:
        _service = PerformanceBaselineService()
    return _service
