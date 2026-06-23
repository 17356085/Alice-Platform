"""
Knowledge Auto-Extractor — 每次执行后自动提取知识到 ChromaDB。

借鉴 Aperant Graphiti 语义记忆概念，但复用现有 ChromaDB (5 collections, 1,115 docs)。
Aperant: 跨会话语义图谱记忆
TLO:     ChromaDB + 元数据关联 + 跨模块模式匹配

提取维度:
  1. 定位器模式 — 新发现的 Element Plus 组件定位方式
  2. 失败模式 — 新的失败原因 + 修复策略
  3. 修复策略 — 成功的修复 → known-issues.yaml 自动更新
  4. 跨模块关联 — 同模式问题在其他模块的适用性

用法:
    from aitest.knowledge.knowledge_extractor import KnowledgeExtractor

    extractor = KnowledgeExtractor()
    extractor.extract_from_execution(
        module="equipment",
        trace_events=events,
        execution_results=results,
    )
"""

from __future__ import annotations

import json
import re
import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

_WORKSTUDY = Path(__file__).resolve().parent.parent.parent


@dataclass
class ExtractedPattern:
    """从一次执行中提取的知识模式。"""
    pattern_type: str          # locator | failure | fix | correlation
    module: str
    page: str = ""
    summary: str = ""
    detail: str = ""
    source_run_id: str = ""
    confidence: float = 0.5
    cross_module_applicable: list[str] = field(default_factory=list)
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())


class KnowledgeExtractor:
    """
    自动知识提取器。

    在每次 SOP 执行后运行，从 trace 事件和测试结果中提取:
      - 定位器模式 → page_objects collection
      - 失败模式 → known_issues collection
      - 修复策略 → known_issues collection
      - 跨模块关联 → tech_analysis collection

    ChromaDB collections:
      page_objects:     103 docs — Element Plus 组件定位器
      known_issues:      24 docs — 已知问题 + 修复方案
      tech_analysis:    401 docs — 技术分析报告
      page_context:     581 docs — 页面上下文
      project_context:    6 docs — 项目上下文
    """

    def __init__(self, auto_index: bool = True):
        self.auto_index = auto_index
        self._extracted: list[ExtractedPattern] = []

    def extract_from_execution(
        self,
        module: str,
        trace_events: list[dict] = None,
        execution_results: dict = None,
        run_id: str = "",
    ) -> list[ExtractedPattern]:
        """
        从一次完整执行中提取知识。

        Args:
            module: 模块名
            trace_events: trace_log.jsonl 中该 run 的全部事件
            execution_results: pytest 执行结果
            run_id: run ID
        """
        patterns = []

        # 1. 提取新的定位器模式
        locator_patterns = self._extract_locator_patterns(trace_events or [], module)
        patterns.extend(locator_patterns)

        # 2. 提取失败模式 + 修复策略
        failure_patterns = self._extract_failure_patterns(trace_events or [], execution_results or {}, module)
        patterns.extend(failure_patterns)

        # 3. 跨模块关联
        for p in locator_patterns + failure_patterns:
            p.cross_module_applicable = self._find_cross_module(p)
            if p.cross_module_applicable:
                p.pattern_type = "correlation"

        # 4. 去重 + 存储
        new_patterns = self._deduplicate(patterns)
        self._extracted = new_patterns

        if self.auto_index and new_patterns:
            self._index_to_chromadb(new_patterns)

        return new_patterns

    # ── Extraction ──

    def _extract_locator_patterns(self, events: list[dict], module: str) -> list[ExtractedPattern]:
        """从成功执行的 automation 事件中提取定位器模式。"""
        patterns = []
        locator_re = re.compile(
            r'(?:By\.|find_element.*?)(?:CSS_SELECTOR|XPATH|ID|CLASS_NAME|NAME|TAG_NAME)[\s\("]*["\']([^"\']+)["\']',
            re.IGNORECASE
        )

        for e in events:
            if e.get("event_type") != "skill_execution":
                continue
            skill = e.get("skill_id", "")
            if "automation" not in skill:
                continue
            if e.get("status") != "success":
                continue

            # Extract from prompt preview (what the agent was asked)
            prompt = e.get("prompt_preview", "")
            response = e.get("response_preview", "")

            # Find new locators in the response
            found = locator_re.findall(response)
            for locator in found:
                if len(locator) > 5 and not locator.startswith("//"):  # skip trivial xpath
                    # Check if this is a new pattern (not already in page_objects)
                    if self._is_new_locator(locator, module):
                        patterns.append(ExtractedPattern(
                            pattern_type="locator",
                            module=module,
                            page=e.get("metadata", {}).get("page", ""),
                            summary=f"Locator pattern: {locator[:80]}",
                            detail=f"Used in {skill} for {module}",
                            source_run_id=e.get("run_id", ""),
                            confidence=0.8,
                        ))

        return patterns

    def _extract_failure_patterns(
        self, events: list[dict], results: dict, module: str
    ) -> list[ExtractedPattern]:
        """从失败的执行事件中提取失败模式 + 修复策略。"""
        patterns = []

        # Find failures
        failed_events = [e for e in events if e.get("status") != "success"]
        success_after_fix = [
            e for e in events
            if e.get("status") == "success"
            and any(f.get("test_id") in e.get("prompt_preview", "") for f in failed_events)
        ]

        for e in failed_events:
            error_msg = e.get("error_message", "")
            if not error_msg:
                continue

            # Classify failure type
            failure_type = self._classify_error(error_msg)
            summary = f"[{failure_type}] {error_msg[:120]}"

            # Check for fix
            fix = ""
            for se in success_after_fix:
                if se.get("skill_id", "").startswith("automation"):
                    fix = se.get("response_preview", "")[:300]

            patterns.append(ExtractedPattern(
                pattern_type="failure",
                module=module,
                summary=summary,
                detail=f"Fix: {fix}" if fix else f"Error: {error_msg[:300]}",
                source_run_id=e.get("run_id", ""),
                confidence=0.7,
            ))

            # If fix exists, also add as fix pattern
            if fix:
                patterns.append(ExtractedPattern(
                    pattern_type="fix",
                    module=module,
                    summary=f"Fix for {failure_type}: {fix[:120]}",
                    detail=fix,
                    source_run_id=e.get("run_id", ""),
                    confidence=0.85,
                ))

        return patterns

    def _classify_error(self, error_msg: str) -> str:
        """快速分类错误类型。"""
        msg = error_msg.lower()
        if any(kw in msg for kw in ["nosuchelement", "no such element", "unable to locate"]):
            return "StaleLocator"
        if any(kw in msg for kw in ["timeout", "timed out"]):
            return "Timeout"
        if any(kw in msg for kw in ["assertion", "assert", "expected"]):
            return "Assertion"
        if any(kw in msg for kw in ["connection refused", "503", "502"]):
            return "ServiceDown"
        return "Unknown"

    def _is_new_locator(self, locator: str, module: str) -> bool:
        """检查定位器是否已在 ChromaDB 中。"""
        try:
            from aitest.knowledge.rag_engine import search_context
            hits = search_context(locator, collection_name="page_objects", n_results=3)
            # Check if any existing doc contains this exact locator
            for h in hits:
                if locator in h.get("document", ""):
                    return False  # already known
        except Exception:
            pass
        return True  # new pattern

    # ── Cross-module correlation ──

    def _find_cross_module(self, pattern: ExtractedPattern) -> list[str]:
        """查找同模式在其他模块的适用性。"""
        applicable = []
        try:
            from aitest.knowledge.rag_engine import search_context
            # Search tech_analysis for similar patterns
            hits = search_context(
                pattern.summary,
                collection_name="tech_analysis",
                n_results=5,
            )
            for h in hits:
                other_mod = h.get("metadata", {}).get("module", "")
                if other_mod and other_mod != pattern.module and other_mod not in applicable:
                    applicable.append(other_mod)

            # Also search page_context for similar UI patterns
            hits2 = search_context(
                pattern.summary,
                collection_name="page_context",
                n_results=3,
            )
            for h in hits2:
                other_mod = h.get("metadata", {}).get("module", "")
                if other_mod and other_mod != pattern.module and other_mod not in applicable:
                    applicable.append(other_mod)
        except Exception:
            pass
        return applicable[:5]

    # ── Deduplication ──

    def _deduplicate(self, patterns: list[ExtractedPattern]) -> list[ExtractedPattern]:
        """去重：相同模块+相同类型的相似 pattern 只保留一个。"""
        seen = set()
        unique = []
        for p in patterns:
            key = hashlib.md5(
                f"{p.pattern_type}:{p.module}:{p.summary[:100]}".encode()
            ).hexdigest()
            if key not in seen:
                seen.add(key)
                unique.append(p)
        return unique

    # ── Indexing ──

    def _index_to_chromadb(self, patterns: list[ExtractedPattern]):
        """将提取的 pattern 写入 ChromaDB 对应 collection。"""
        try:
            from aitest.knowledge.rag_engine import get_chroma_client
            client = get_chroma_client()

            # Group by collection target
            by_collection = defaultdict(list)
            for p in patterns:
                if p.pattern_type == "locator":
                    by_collection["page_objects"].append(p)
                elif p.pattern_type in ("failure", "fix"):
                    by_collection["known_issues"].append(p)
                elif p.pattern_type == "correlation":
                    by_collection["tech_analysis"].append(p)

            for coll_name, items in by_collection.items():
                try:
                    collection = client.get_collection(coll_name)
                    ids = [f"auto-{p.extracted_at}-{hashlib.md5(p.summary.encode()).hexdigest()[:8]}"
                           for p in items]
                    documents = [f"{p.pattern_type}: {p.summary}\n\n{p.detail}\nCross-module: {p.cross_module_applicable}"
                                 for p in items]
                    metadatas = [{
                        "module": p.module,
                        "pattern_type": p.pattern_type,
                        "confidence": p.confidence,
                        "extracted_at": p.extracted_at,
                        "source": "knowledge_extractor",
                    } for p in items]
                    collection.add(ids=ids, documents=documents, metadatas=metadatas)
                    print(f"[KnowledgeExtractor] Indexed {len(items)} pattern(s) → {coll_name}")
                except Exception as e:
                    print(f"[KnowledgeExtractor] Index error ({coll_name}): {e}")

        except Exception as e:
            print(f"[KnowledgeExtractor] ChromaDB unavailable: {e}")

    # ── Reporting ──

    @property
    def summary(self) -> dict:
        return {
            "total_extracted": len(self._extracted),
            "by_type": {
                t: len([p for p in self._extracted if p.pattern_type == t])
                for t in set(p.pattern_type for p in self._extracted)
            },
            "cross_module": len([p for p in self._extracted if p.cross_module_applicable]),
            "extracted_at": datetime.now().isoformat(),
        }


# ── Convenience ──

def auto_extract(
    module: str,
    trace_events: list[dict] = None,
    execution_results: dict = None,
    run_id: str = "",
) -> dict:
    """便捷函数 — 从执行结果自动提取知识。"""
    extractor = KnowledgeExtractor(auto_index=True)
    extractor.extract_from_execution(module, trace_events, execution_results, run_id)
    print(f"[KnowledgeExtractor] {extractor.summary}")
    return extractor.summary
