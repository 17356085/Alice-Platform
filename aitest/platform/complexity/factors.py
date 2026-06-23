"""Complexity Factors — 页面复杂度评分因子。

参考 Aperant spec-orchestrator.ts 的快速路径启发式。
适配 AITest 测试领域：字段数/组件类型/交互复杂度/数据复杂度/风险因子。
"""
from dataclasses import dataclass, field
from enum import Enum


class ComplexityTier(str, Enum):
    SIMPLE = "simple"
    STANDARD = "standard"
    COMPLEX = "complex"


@dataclass
class PageComplexityProfile:
    tier: ComplexityTier = ComplexityTier.STANDARD
    score: float = 0.0

    # 页面特征
    field_count: int = 0
    button_count: int = 0
    table_column_count: int = 0

    # 组件特征
    has_dialog: bool = False
    has_wizard: bool = False
    has_file_upload: bool = False
    has_workflow: bool = False
    has_rich_editor: bool = False
    has_tree: bool = False
    has_chart: bool = False

    # 交互复杂度
    has_search_filter: bool = False
    has_batch_operation: bool = False
    has_data_import_export: bool = False
    has_tab_panel: bool = False

    # 数据复杂度
    has_cascading: bool = False
    has_dynamic_form: bool = False
    has_cross_page_validation: bool = False

    # 风险因子
    involves_money: bool = False
    involves_approval: bool = False
    is_critical_path: bool = False


# ── 评分规则 ─────────────────────────────────────────────────────────

COMPLEXITY_RULES = {
    # 基础分 (每个字段/列/按钮加分)
    "field_count":        lambda v: min(v, 50),
    "table_column_count": lambda v: min(v * 1.5, 30),
    "button_count":       lambda v: min(v * 0.5, 10),

    # 组件加分
    "has_dialog":              10,
    "has_wizard":              20,
    "has_file_upload":         15,
    "has_workflow":            20,
    "has_rich_editor":         10,
    "has_tree":                10,
    "has_chart":                5,

    # 交互加分
    "has_search_filter":        5,
    "has_batch_operation":     10,
    "has_data_import_export":  10,
    "has_tab_panel":            5,

    # 数据加分
    "has_cascading":           15,
    "has_dynamic_form":        20,
    "has_cross_page_validation": 25,

    # 风险加分
    "involves_money":          20,
    "involves_approval":       15,
    "is_critical_path":        25,
}

SIMPLE_THRESHOLD = 20    # ≤20 → SIMPLE
COMPLEX_THRESHOLD = 60   # ≥60 → COMPLEX


# ── Pipeline 定义 ────────────────────────────────────────────────────

SIMPLE_PIPELINE = [
    "automation-agent",     # 直接生成 PO + 测试脚本
    "execution-agent",      # 运行 + 报告
]
# 省 88% token

STANDARD_PIPELINE = [
    "requirement-agent",
    "test-design-agent",
    "automation-agent",
    "execution-agent",
    "report-agent",
]
# 省 23% token

COMPLEX_PIPELINE = [
    "project-agent",
    "requirement-agent",
    "test-design-agent",
    "automation-agent",
    "execution-agent",
    "bug-analysis-agent",
    "report-agent",
    "knowledge-agent",
]
# 完整 8 Agent


def pipeline_for_tier(tier: ComplexityTier) -> list[str]:
    return {
        ComplexityTier.SIMPLE: SIMPLE_PIPELINE,
        ComplexityTier.STANDARD: STANDARD_PIPELINE,
        ComplexityTier.COMPLEX: COMPLEX_PIPELINE,
    }[tier]


def score_to_tier(score: float) -> ComplexityTier:
    if score <= SIMPLE_THRESHOLD:
        return ComplexityTier.SIMPLE
    if score >= COMPLEX_THRESHOLD:
        return ComplexityTier.COMPLEX
    return ComplexityTier.STANDARD
