"""Complexity Classifier — 页面复杂度分类器。

两阶段:
  1. 快速路径: 启发式规则 (<1ms)
  2. LLM 辅助: 边界不明时用 DeepSeek 评估 (~2s)

参考 Aperant spec-orchestrator.ts 的快速路径 + AI complexity_assessor。
"""
import json
import logging
from pathlib import Path
from typing import Optional

from aitest.platform.complexity.factors import (
    PageComplexityProfile, ComplexityTier, COMPLEXITY_RULES,
    SIMPLE_THRESHOLD, COMPLEX_THRESHOLD, score_to_tier, pipeline_for_tier,
)

logger = logging.getLogger(__name__)


# ── 快速路径模式 ────────────────────────────────────────────────────

IMMEDIATE_SIMPLE_PAGE_TITLES = [
    "详情", "查看", "Detail", "View", "列表",
]

IMMEDIATE_COMPLEX_PAGE_TITLES = [
    "审批", "工作流", "配置向导", "Approval", "Workflow", "向导",
]


class ComplexityClassifier:
    """页面复杂度分类器。

    用法:
        classifier = ComplexityClassifier()
        profile = classifier.classify(discovery_data)
        pipeline = pipeline_for_tier(profile.tier)
    """

    def classify(self, discovery_data: dict = None, page_title: str = "") -> PageComplexityProfile:
        """分类页面复杂度。

        Args:
            discovery_data: BrowserUse 发现数据 (pages.json 条目)
            page_title: 页面标题 (fallback)
        """
        discovery_data = discovery_data or {}

        # Phase 1: 快速路径 — 标题关键词直接判定
        quick = self._quick_classify(page_title, discovery_data)
        if quick is not None:
            return quick

        # Phase 2: 启发式规则评分
        profile = self._heuristic_classify(discovery_data)

        # Phase 3: 边界不明时 LLM 辅助
        if 15 < profile.score < 70:
            profile = self._llm_refine(discovery_data, profile, page_title)

        return profile

    def _quick_classify(self, page_title: str, data: dict) -> Optional[PageComplexityProfile]:
        """快速路径：标题关键词直接判定。"""
        title = page_title or data.get("title", data.get("page_title", ""))
        title_lower = title.lower()

        for kw in IMMEDIATE_SIMPLE_PAGE_TITLES:
            if kw.lower() in title_lower:
                profile = PageComplexityProfile(tier=ComplexityTier.SIMPLE, score=10)
                profile.tier = ComplexityTier.SIMPLE
                return profile

        components = " ".join(str(data.get("components", data.get("ui_components", [])))).lower()
        if any(kw.lower() in f"{title_lower} {components}" for kw in IMMEDIATE_COMPLEX_PAGE_TITLES):
            profile = PageComplexityProfile(tier=ComplexityTier.COMPLEX, score=70)
            profile.has_workflow = True
            return profile

        return None

    def _heuristic_classify(self, data: dict) -> PageComplexityProfile:
        """基于启发式规则的评分分类。"""
        profile = PageComplexityProfile()

        # 提取特征
        profile.field_count = len(data.get("fields", data.get("form_fields", [])))
        profile.table_column_count = len(data.get("table_columns", []))
        profile.button_count = len(data.get("buttons", data.get("actions", [])))

        # 组件检测
        components = " ".join(str(data.get("components", data.get("ui_components", [])))).lower()
        interactions = " ".join(str(data.get("interactions", []))).lower()
        page_type = str(data.get("page_type", data.get("type", ""))).lower()

        profile.has_dialog = any(c in components for c in ["dialog", "modal", "drawer"])
        profile.has_wizard = any(c in components for c in ["steps", "wizard"]) or "wizard" in page_type
        profile.has_file_upload = "upload" in components
        profile.has_workflow = "workflow" in components or "timeline" in components
        profile.has_tree = "tree" in components
        profile.has_tab_panel = "tabs" in components or "tab" in components
        profile.has_search_filter = any(c in interactions for c in ["search", "filter", "query"])
        profile.has_batch_operation = "batch" in interactions
        profile.has_data_import_export = any(c in interactions for c in ["import", "export"])
        profile.has_cascading = "cascader" in components or "cascading" in str(data)
        profile.has_dynamic_form = "dynamic" in str(data).lower()

        # 计算评分
        score = 0.0
        for rule_key, rule_fn in COMPLEXITY_RULES.items():
            value = getattr(profile, rule_key, None)
            if value is None:
                continue
            if isinstance(value, bool):
                if value:
                    score += rule_fn
            elif isinstance(value, (int, float)) and value > 0:
                score += rule_fn(value) if callable(rule_fn) else rule_fn

        profile.score = min(score, 100)
        profile.tier = score_to_tier(profile.score)
        return profile

    def _llm_refine(self, data: dict, heuristic: PageComplexityProfile, page_title: str = "") -> PageComplexityProfile:
        """LLM 辅助判断（边界不明时）。用 DeepSeek 做快速评估。"""
        prompt = (
            f"Classify this web page complexity for automated testing. Reply with ONE word only.\n\n"
            f"Page title: {page_title}\n"
            f"Fields: {heuristic.field_count}\n"
            f"Table columns: {heuristic.table_column_count}\n"
            f"Components: {self._component_summary(data)}\n"
            f"Heuristic score: {heuristic.score:.0f}/100 (thresholds: ≤{SIMPLE_THRESHOLD}=SIMPLE, ≥{COMPLEX_THRESHOLD}=COMPLEX)\n"
            f"Heuristic tier: {heuristic.tier.value}\n\n"
            f"Reply: SIMPLE, STANDARD, or COMPLEX"
        )

        try:
            from aitest.llm.provider import get_provider
            llm = get_provider("deepseek")
            response = llm.complete(
                "You are a test automation complexity assessor. Reply with exactly one word.",
                prompt, max_tokens=10, temperature=0.1,
            )
            tier_str = response.content.strip().upper()
            for tier in ComplexityTier:
                if tier.value.upper() in tier_str:
                    heuristic.tier = tier
                    break
        except Exception:
            pass

        return heuristic

    @staticmethod
    def _component_summary(data: dict) -> str:
        comps = data.get("components", data.get("ui_components", []))
        if isinstance(comps, list):
            return ", ".join(comps)[:200]
        return str(comps)[:200]
