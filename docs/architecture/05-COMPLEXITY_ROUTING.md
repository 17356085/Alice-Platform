# Complexity Routing — 自适应 SOP 流水线路由

> 参考: Aperant `orchestration/spec-orchestrator.ts` — 三档复杂度路由 + 快速路径启发式
>       + `config/agent-configs.ts` — 声明式 Agent 配置
> 适配: AITest 页面测试场景 — SIMPLE/STANDARD/COMPLEX 三档 + 页面特征启发式
> 状态: v1.0-draft | 优先级: P1

## 1. 问题

### 1.1 当前状态

所有页面走完全相同的 8-Agent SOP 流水线：

```
无论页面复杂度如何:
  Preflight → Project → Requirement → Test Design → Automation
  → Execution → Bug Analysis → Report → Knowledge
```

结果：
- 简单列表页（3 字段，无弹窗，无搜索）走完整 SOP → 浪费 80% token
- 复杂向导页（30+ 字段，多步骤，文件上传，审批流）也只走一次 → 质量不足

### 1.2 Aperant 的复杂度评估

```typescript
// Aperant spec-orchestrator.ts — 快速路径启发式
if (taskDescription.length < 30 && matchesSimplePattern(taskDescription)) {
  return "SIMPLE";  // 跳过 LLM 评估，直接走简版 pipeline
}
// 否则走 AI 评估: SIMPLE / STANDARD / COMPLEX
```

## 2. 设计

### 2.1 页面复杂度因子

```python
# platform/complexity/factors.py

from dataclasses import dataclass, field
from enum import Enum


class ComplexityTier(str, Enum):
    """复杂度档次。"""
    SIMPLE = "simple"        # ~30% 的页面
    STANDARD = "standard"    # ~50% 的页面
    COMPLEX = "complex"      # ~20% 的页面


@dataclass
class PageComplexityProfile:
    """页面复杂度画像。"""
    tier: ComplexityTier = ComplexityTier.STANDARD
    score: float = 0.0                  # 0-100 复杂度评分

    # 页面特征
    field_count: int = 0                # 表单字段数
    button_count: int = 0               # 操作按钮数
    table_column_count: int = 0         # 表格列数

    # 组件特征
    has_dialog: bool = False            # 是否有弹窗
    has_wizard: bool = False            # 是否有向导/步骤条
    has_file_upload: bool = False       # 是否有文件上传
    has_workflow: bool = False          # 是否有审批流
    has_rich_editor: bool = False       # 是否有富文本编辑器
    has_tree: bool = False              # 是否有组织/分类树
    has_chart: bool = False             # 是否有图表

    # 交互复杂度
    has_search_filter: bool = False     # 是否有搜索/筛选
    has_batch_operation: bool = False   # 是否有批量操作
    has_data_import_export: bool = False  # 是否有导入/导出
    has_tab_panel: bool = False         # 是否有 Tab 切换

    # 数据复杂度
    has_cascading: bool = False         # 是否有级联选择
    has_dynamic_form: bool = False      # 是否有动态表单（字段随选择变化）
    has_cross_page_validation: bool = False  # 是否涉及跨页面数据校验

    # 风险因子
    involves_money: bool = False        # 是否涉及金额
    involves_approval: bool = False     # 是否涉及审批
    is_critical_path: bool = False      # 是否在关键路径上


# ══════════════════════════════════════════════════════════════════════════
#  评分规则
# ══════════════════════════════════════════════════════════════════════════

COMPLEXITY_RULES = {
    # 基础分 (每个字段/列/按钮加 1 分)
    "field_count":        lambda v: min(v, 50),
    "table_column_count": lambda v: min(v * 1.5, 30),
    "button_count":       lambda v: min(v * 0.5, 10),

    # 组件加分
    "has_dialog":             10,
    "has_wizard":             20,
    "has_file_upload":        15,
    "has_workflow":           20,
    "has_rich_editor":        10,
    "has_tree":               10,
    "has_chart":              5,

    # 交互加分
    "has_search_filter":      5,
    "has_batch_operation":    10,
    "has_data_import_export": 10,
    "has_tab_panel":          5,

    # 数据加分
    "has_cascading":          15,
    "has_dynamic_form":       20,
    "has_cross_page_validation": 25,

    # 风险加分
    "involves_money":         20,
    "involves_approval":      15,
    "is_critical_path":       25,
}

# 阈值
SIMPLE_THRESHOLD = 20      # ≤20 → SIMPLE
COMPLEX_THRESHOLD = 60     # ≥60 → COMPLEX
                          # 20-60 → STANDARD
```

### 2.2 快速路径启发式 (跳过大模型评估)

参考 Aperant spec-orchestrator 的快速路径：

```python
# platform/complexity/classifier.py

class ComplexityClassifier:
    """页面复杂度分类器。

    两阶段:
      1. 快速路径 (启发式规则，<1ms)
      2. LLM 评估 (仅 STANDARD 档不确定时，~2s)

    参考: Aperant spec-orchestrator.ts 的快速路径 + AI complexity_assessor
    """

    def classify(self, discovery_data: dict) -> PageComplexityProfile:
        """分类页面复杂度。

        Args:
            discovery_data: BrowserUse 发现阶段产出的 pages.json 条目
                {
                    "url": "...",
                    "page_type": "form",
                    "fields": [...],
                    "components": ["el-table", "el-dialog", ...],
                    "interactions": ["search", "batch-delete"],
                    ...
                }
        """
        # Phase 1: 启发式规则
        profile = self._heuristic_classify(discovery_data)

        # Phase 2: 如果边界不明显，用 LLM 辅助判断
        if 15 < profile.score < 70:
            profile = self._llm_refine(discovery_data, profile)

        return profile

    def _heuristic_classify(self, data: dict) -> PageComplexityProfile:
        """基于启发式规则的快速分类。"""
        profile = PageComplexityProfile()

        # 提取特征
        profile.field_count = len(data.get("fields", data.get("form_fields", [])))
        profile.table_column_count = len(data.get("table_columns", []))
        profile.button_count = len(data.get("buttons", []))

        components = data.get("components", [])
        component_names = " ".join(components).lower()
        profile.has_dialog = "dialog" in component_names or "modal" in component_names
        profile.has_wizard = "steps" in component_names or "wizard" in component_names
        profile.has_file_upload = "upload" in component_names
        profile.has_workflow = "workflow" in component_names or "timeline" in component_names
        profile.has_tree = "tree" in component_names
        profile.has_tab_panel = "tabs" in component_names

        interactions = data.get("interactions", [])
        interaction_names = " ".join(interactions).lower()
        profile.has_search_filter = "search" in interaction_names or "filter" in interaction_names
        profile.has_batch_operation = "batch" in interaction_names
        profile.has_data_import_export = "import" in interaction_names or "export" in interaction_names

        # 计算评分
        score = 0.0
        for rule_key, rule_fn in COMPLEXITY_RULES.items():
            value = getattr(profile, rule_key, None)
            if value is None:
                continue
            if isinstance(value, bool) and value:
                score += rule_fn  # 固定加分
            elif isinstance(value, (int, float)) and value > 0:
                score += rule_fn(value) if callable(rule_fn) else rule_fn

        profile.score = score
        profile.tier = self._score_to_tier(score)

        return profile

    def _score_to_tier(self, score: float) -> ComplexityTier:
        if score <= SIMPLE_THRESHOLD:
            return ComplexityTier.SIMPLE
        if score >= COMPLEX_THRESHOLD:
            return ComplexityTier.COMPLEX
        return ComplexityTier.STANDARD

    def _llm_refine(self, data: dict, heuristic: PageComplexityProfile) -> PageComplexityProfile:
        """LLM 辅助判断（边界不明时）。

        用便宜模型 (DeepSeek) 做一次快速评估，成本约 $0.001。
        """
        prompt = (
            f"Classify this web page into SIMPLE / STANDARD / COMPLEX for automated testing:\n\n"
            f"Page data:\n"
            f"  Fields: {heuristic.field_count}\n"
            f"  Table columns: {heuristic.table_column_count}\n"
            f"  Components: {heuristic._component_summary(data)}\n"
            f"  Heuristic score: {heuristic.score:.0f}/100\n"
            f"  Heuristic tier: {heuristic.tier.value}\n\n"
            f"Reply with only one word: SIMPLE, STANDARD, or COMPLEX."
        )

        try:
            from aitest.llm.provider import get_provider
            llm = get_provider("deepseek")
            response = llm.complete(
                "You are a test automation complexity assessor. "
                "Classify web pages for automated testing. Reply with exactly one word.",
                prompt,
                max_tokens=10,
                temperature=0.1,
            )
            tier_str = response.content.strip().upper()
            if tier_str in ("SIMPLE", "STANDARD", "COMPLEX"):
                heuristic.tier = ComplexityTier(tier_str.lower())
        except Exception:
            pass  # LLM 评估失败 → 保持启发式结果

        return heuristic
```

### 2.3 三档 SOP 流水线

```python
# platform/complexity/pipelines.py

# ── SIMPLE: 2 个 Agent ──
SIMPLE_PIPELINE = [
    "automation-agent",    # 直接生成 PO + 测试脚本
    "execution-agent",     # 运行 + 报告
]
# Token 估算: ~5K + ~10K = ~15K (vs 完整 130K，省 88%)

# ── STANDARD: 5 个 Agent ──
STANDARD_PIPELINE = [
    "requirement-agent",   # 需求分析
    "test-design-agent",   # 测试设计
    "automation-agent",    # 自动化代码生成
    "execution-agent",     # 执行
    "report-agent",        # 报告
]
# Token 估算: ~15K + ~20K + ~30K + ~25K + ~10K = ~100K (省 23%)

# ── COMPLEX: 8 个 Agent (完整) ──
COMPLEX_PIPELINE = [
    "project-agent",       # 项目初始化 + 上下文同步
    "requirement-agent",   # 需求分析
    "test-design-agent",   # 测试设计 + 风险评估
    "automation-agent",    # 自动化代码生成 + 一致性检查
    "execution-agent",     # 执行 + Allure 分析
    "bug-analysis-agent",  # Bug 分析 (最多 3 轮 QA loop)
    "report-agent",        # 报告生成
    "knowledge-agent",     # 知识库更新
]
# Token 估算: 完整 ~130K

# ── 每档可选阶段 (HITL 触发) ──
QUALITY_GATES = {
    ComplexityTier.SIMPLE: [],           # 无质量门
    ComplexityTier.STANDARD: ["execution"],  # 执行后检查通过率
    ComplexityTier.COMPLEX: ["test_design", "execution"],  # 两个门
}
```

### 2.4 集成到 SOP Graph

```python
# aitest/graphs/sop_graph.py — 改造后的入口

def build_sop_graph():
    graph = StateGraph(SOPState)

    # ★ 新入口: 复杂度评估
    graph.add_node("complexity_assess", complexity_assess_node)
    graph.add_node("preflight", preflight_node)

    # SIMPLE pipeline
    graph.add_node("simple_automation", make_agent_loop_node("automation-agent"))
    graph.add_node("simple_execution", make_agent_loop_node("execution-agent"))

    # STANDARD pipeline
    graph.add_node("requirement_agent", make_agent_loop_node("requirement-agent"))
    graph.add_node("test_design_agent", make_agent_loop_node("test-design-agent"))
    graph.add_node("automation_agent", make_agent_loop_node("automation-agent"))
    graph.add_node("execution_agent", make_agent_loop_node("execution-agent"))
    graph.add_node("report_agent", make_agent_loop_node("report-agent"))

    # COMPLEX pipeline (额外)
    graph.add_node("project_agent", make_agent_loop_node("project-agent"))
    graph.add_node("bug_analysis_agent", make_agent_loop_node("bug-analysis-agent"))
    graph.add_node("knowledge_agent", make_agent_loop_node("knowledge-agent"))

    # 路由
    graph.set_entry_point("complexity_assess")
    graph.add_conditional_edges(
        "complexity_assess",
        route_by_complexity,
        {
            "simple": "simple_automation",
            "standard": "preflight",
            "complex": "project_agent",
        }
    )

    # SIMPLE: 2 步直通
    graph.add_edge("simple_automation", "simple_execution")
    graph.add_edge("simple_execution", END)

    # STANDARD: preflight → requirement → test_design → automation → execution → report
    graph.add_edge("preflight", "requirement_agent")
    graph.add_edge("requirement_agent", "test_design_agent")
    graph.add_edge("test_design_agent", "automation_agent")
    graph.add_edge("automation_agent", "execution_agent")
    graph.add_edge("execution_agent", "report_agent")
    graph.add_edge("report_agent", END)

    # COMPLEX: 完整 8 Agent (当前流程)
    graph.add_edge("project_agent", "requirement_agent")
    # ... (完整流程，同现有图)
    graph.add_edge("knowledge_agent", END)

    return graph


def complexity_assess_node(state: SOPState) -> dict:
    """复杂度评估节点。

    从 discovery 数据读取页面特征 → 分类 → 写入 state。
    """
    page_url = state.get("page_url", "")
    discovery_dir = get_page_dir(state["module"], state["current_page"]) / ".discovery"
    pages_json = discovery_dir / "pages.json"

    if pages_json.exists():
        import json
        with open(pages_json) as f:
            page_data = json.load(f)
        # 找到当前页面
        page_info = _find_page(page_data, state["current_page"])
    else:
        page_info = {}

    classifier = ComplexityClassifier()
    profile = classifier.classify(page_info)

    return {
        "complexity_tier": profile.tier.value,
        "complexity_score": profile.score,
        "complexity_profile": profile,
        "selected_pipeline": _pipeline_for_tier(profile.tier),
        "estimated_tokens": _estimate_tokens(profile.tier),
    }


def route_by_complexity(state: SOPState) -> str:
    """根据复杂度路由到不同 pipeline。"""
    tier = state.get("complexity_tier", "standard")

    # SIMPLE: 跳过 preflight → 直接走简版 pipeline
    if tier == "simple":
        return "simple"

    # STANDARD/COMPLEX: 先走 preflight
    if tier == "complex":
        return "complex"

    return "standard"
```

## 4. 预期收益

| 指标 | 当前 (全量 8 Agent) | 改造后 (自适应) | 节省 |
|------|--------------------|-----------------|------|
| 简单页面 Token | ~130K | ~15K | **88%** |
| 标准页面 Token | ~130K | ~100K | **23%** |
| 复杂页面 Token | ~130K | ~130K | 0% |
| 假设 30%S+50%ST+20%C 混合 | ~130K × 100 = 13M | ~15K×30 + 100K×50 + 130K×20 = 8.05M | **38%** |

## 5. 快速路径触发条件（自动识别，无需 LLM）

```python
# 这些页面特征可以直接判断复杂度，不需要调 LLM

IMMEDIATE_SIMPLE_PATTERNS = [
    # 页面标题包含
    "详情", "查看", "Detail", "View",
    # 页面类型
    "list", "detail",
    # 特征组合
    ("no_form", "no_dialog", "table_only"),  # 纯列表页
]

IMMEDIATE_COMPLEX_PATTERNS = [
    # 页面标题包含
    "审批", "工作流", "配置向导", "Approval", "Workflow",
    # 特征组合
    ("has_wizard",),
    ("has_workflow",),
    ("has_dynamic_form",),
    ("field_count > 30",),
    ("has_file_upload", "has_cascading"),
]
```

## 6. 参考来源

| 特性 | 参考 |
|------|------|
| 快速路径启发式 (<30字+关键词) | Aperant `spec-orchestrator.ts` — SIMPLE 自动判定 |
| 三档复杂度 (SIMPLE/STANDARD/COMPLEX) | Aperant `spec-orchestrator.ts` — COMPLEXITY 三档 |
| LLM 辅助评估 | Aperant `complexity_assessor.md` prompt + `ComplexityAssessmentOutputSchema` |
| 声明式 Pipeline 配置 | Aperant `config/agent-configs.ts` — 声明式 Agent 定义 |
| 页面特征因子 | AITest 现有 `discovery/` — BrowserUse 页面观察数据 |
