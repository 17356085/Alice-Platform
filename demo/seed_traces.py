"""Seed trace data for demo — generates 3 realistic runs in trace_log.jsonl."""
import json
import uuid
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TRACE_DIR = Path(__file__).resolve().parent.parent / "governance" / ".traces"
TRACE_LOG = TRACE_DIR / "trace_log.jsonl"

# Cost model
PRICING = {
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-opus-4-8": (15.0, 75.0),
    "claude-haiku-4-5": (0.8, 4.0),
    "deepseek-v4": (0.27, 1.10),
}

def calc_cost(model, tin, tout):
    inp, outp = PRICING.get(model, (0, 0))
    return round((tin / 1_000_000 * inp) + (tout / 1_000_000 * outp), 6)

def make_event(ts, run_id, agent, etype, skill, provider, model, tin, tout, latency,
               status="success", prompt="", response="", error="", meta=None):
    eid = f"{etype[:4]}-{uuid.uuid4().hex[:12]}"
    cost = calc_cost(model, tin, tout)
    return {
        "event_id": eid,
        "event_type": etype,
        "timestamp": ts.isoformat(),
        "run_id": run_id,
        "agent_name": agent,
        "skill_id": skill,
        "provider": provider,
        "model": model,
        "latency_ms": latency,
        "token_input": tin,
        "token_output": tout,
        "token_cost_estimate": cost,
        "status": status,
        "prompt_preview": (prompt or "")[:200].replace("\n", " "),
        "response_preview": (response or "")[:500].replace("\n", " "),
        "error_message": (error or "")[:300],
        "metadata": meta or {},
    }

# ── Run 1: Successful equipment SOP (8 steps, ~2min) ──
run1_id = "sop-equipment-240620-001"
t1 = datetime(2026, 6, 20, 14, 30, 0)
r1_events = [
    make_event(t1, run1_id, "automation-agent", "skill_execution",
               "automation/tech-analysis", "claude", "claude-sonnet-4-6",
               3500, 1200, 8200, "success",
               "Analyze equipment module page structure for Element Plus components...",
               "## 技术分析报告\n- el-table: 4 instances, el-dialog: 2 instances, el-cascader: 1 instance\n- Teleport targets: dialog, cascader dropdown\n- Loading mask: detected on search operations\n- 无 iframe, 无 Shadow DOM。"),
    make_event(t1 + timedelta(seconds=9), run1_id, "automation-agent", "llm_call",
               "automation/tech-analysis", "claude", "claude-sonnet-4-6",
               3500, 1200, 8100, "success",
               meta={"temperature": 0.3, "finish_reason": "stop"}),
    make_event(t1 + timedelta(seconds=18), run1_id, "automation-agent", "skill_execution",
               "automation/page-analysis", "claude", "claude-sonnet-4-6",
               2800, 1800, 12400, "success",
               "Analyze UnitManagePage DOM structure and generate locators...",
               "## Page Object\n```python\nclass UnitManagePage(BasePage):\n    TABLE = (By.CSS_SELECTOR, '.el-table')\n    SEARCH_INPUT = (By.CSS_SELECTOR, '.el-input__inner[placeholder*=\"单位\"]')\n    ADD_BTN = (By.XPATH, '//button[.//span[text()=\"新增\"]]')\n```\n\n定位器全部使用 CSS 优先策略。"),
    make_event(t1 + timedelta(seconds=35), run1_id, "automation-agent", "agent_decision",
               "automation/auto-strategy", "claude", "claude-opus-4-8",
               4500, 900, 5300, "success",
               "Decide automation strategy: which locators to use, what waits to apply...",
               "## AUTO_STRATEGY\n- P0: smoke test (页面加载, 搜索, CRUD 入口)\n- P1: CRUD flow (创建→验证→编辑→删除)\n- P2: boundary & error states\n\n定位策略: CSS优先 (el-table, el-input), XPath回退 (按钮文本)\n等待策略: wait_vue_stable() → 检查 el-loading-mask → 元素可见\nTeleport处理: dialog内元素定位到body层"),
    make_event(t1 + timedelta(seconds=42), run1_id, "automation-agent", "skill_execution",
               "automation/test-code-gen", "claude", "claude-sonnet-4-6",
               5200, 3200, 18500, "success",
               "Generate pytest test code for equipment/unit-management page...",
               "## 生成代码\n```python\nclass TestUnitManageCRUD:\n    def test_create_unit(self, page):\n        page.navigate()\n        page.click_add()\n        page.fill_form({'name': 'test_unit', 'code': 'TU001'})\n        page.submit()\n        assert page.has_toast('成功')\n    \n    def test_search_unit(self, page):\n        page.navigate()\n        page.search('TU001')\n        assert page.table_has_row('TU001')\n```"),
    make_event(t1 + timedelta(seconds=62), run1_id, "execution-agent", "skill_execution",
               "execution/test-run", "claude", "claude-haiku-4-5",
               800, 400, 45200, "success",
               "pytest script/equipment/test_unit_manage.py -v --reruns 2",
               "test_create_unit PASSED [20%]\ntest_search_unit PASSED [40%]\ntest_update_unit PASSED [60%]\ntest_delete_unit PASSED [80%]\ntest_search_pagination PASSED [100%]\n\n5 passed in 45.20s"),
    make_event(t1 + timedelta(seconds=108), run1_id, "report-agent", "skill_execution",
               "reporting/report-generator", "claude", "claude-haiku-4-5",
               1200, 2400, 3800, "success",
               "Generate KPI Excel report for equipment module...",
               "## 测试报告\n- 模块: equipment\n- 页面: 4\n- 用例: 28 passed / 0 failed / 2 skipped\n- 通过率: 100%\n- 总耗时: 2m18s\n- 报告路径: governance/kpi/reports/equipment/测试报告-equipment.xlsx"),
    make_event(t1 + timedelta(seconds=115), run1_id, "knowledge-agent", "milestone",
               "", "claude", "claude-sonnet-4-6",
               500, 200, 1200, "success",
               "SOP cycle complete: equipment module Phase 1-9 done.",
               "CycleEnd event emitted. StateAuditor: 0 drifts. SOPAuditor: 0 violations.\nRAG updated: 4 new documents indexed.\nKPI recorded."),
]

# ── Run 2: Bug analysis run with errors + safety flag ──
run2_id = "sop-warehouse-240621-002"
t2 = datetime(2026, 6, 21, 10, 15, 0)
r2_events = [
    make_event(t2, run2_id, "execution-agent", "skill_execution",
               "execution/test-run", "claude", "claude-haiku-4-5",
               600, 300, 38200, "success",
               "pytest script/warehouse/test_hazard_item.py -v",
               "test_create_hazard PASSED [25%]\ntest_search_hazard FAILED [50%]\ntest_update_hazard FAILED [75%]\ntest_delete_hazard PASSED [100%]\n\n2 passed, 2 failed in 38.20s"),
    make_event(t2 + timedelta(seconds=39), run2_id, "bug-analysis-agent", "skill_execution",
               "bug-analysis/failure-classify", "claude", "claude-sonnet-4-6",
               3800, 1500, 6200, "error",
               prompt="Classify test_search_hazard failure from allure-results...",
               response="## 故障分类\n- 类型: ElementNotInteractableException\n- 根因: el-cascader 下拉选项通过 Teleport 渲染到 body，定位器未穿透\n- 匹配已知问题: EP-001 (Teleport 定位)\n- 严重度: high\n- 建议: 在 BasePage 添加 cascader_select 方法",
               error="ElementNotInteractableException: el-cascader option not reachable"),
    make_event(t2 + timedelta(seconds=47), run2_id, "bug-analysis-agent", "llm_call",
               "bug-analysis/rag-match", "claude", "claude-sonnet-4-6",
               1200, 600, 1400, "success",
               meta={"matched_issue": "EP-001", "similarity": 0.89, "collection": "known_issues"}),
    make_event(t2 + timedelta(seconds=50), run2_id, "bug-analysis-agent", "skill_execution",
               "bug-analysis/bug-report", "claude", "claude-opus-4-8",
               2500, 1800, 9400, "success",
               "Generate bug report with fix recommendation...",
               "## Bug Report: EP-012\n- 页面: warehouse/hazard-item\n- 组件: el-cascader\n- 症状: 级联选择器下拉选项无法点击\n- 根因: Teleport 渲染到 body，PO 定位器在组件树内查找\n- 修复: BasePage.cascader_select() 方法，定位到 body > .el-cascader__dropdown\n- Tag: v0.5.1-hotfix"),
    make_event(t2 + timedelta(seconds=61), run2_id, "knowledge-agent", "skill_execution",
               "knowledge/bug-index", "claude", "claude-haiku-4-5",
               800, 400, 1500, "success",
               "Index EP-012 into known_issues RAG collection...",
               "RAG indexed: known_issues/EP-012 (Teleport + cascader)"),
    # Safety flag: sensitive info detected in response
    make_event(t2 + timedelta(seconds=64), run2_id, "knowledge-agent", "skill_execution",
               "knowledge/context-sync", "deepseek", "deepseek-v4",
               600, 800, 2100, "partial",
               response="Updated MODULE_CONTEXT.md with connection string jdbc:mysql://192.168.1.100:3306/testdb?user=admin&password=secret123",
               meta={"safety_flags": ["SENSITIVE_LEAK: 内网 IP 地址", "SENSITIVE_LEAK: 密码明文"]}),
]

# ── Run 3: Dev SOP run (architecture phase) ──
run3_id = "dev-sop-tank-monitor-240622-003"
t3 = datetime(2026, 6, 22, 9, 0, 0)
r3_events = [
    make_event(t3, run3_id, "pm-agent", "skill_execution",
               "pm/project-init", "claude", "claude-opus-4-8",
               4200, 1800, 11300, "success",
               "Initialize tank-monitor module: requirements, tech stack, milestones...",
               "## Project Init\n- Module: tank-monitor\n- Stack: React 18 + TypeScript + ECharts\n- Repository: git@gitlab:cimc/tank-monitor.git\n- Sprint: 2 weeks\n- Team: 1 FE + 1 BE"),
    make_event(t3 + timedelta(seconds=13), run3_id, "pm-agent", "agent_decision",
               "pm/plan-review", "claude", "claude-opus-4-8",
               2200, 600, 3900, "success",
               "Review project plan and approve milestone schedule...",
               "Plan approved. 3 milestones: M1 (data model), M2 (API layer), M3 (UI + integration)."),
    make_event(t3 + timedelta(seconds=18), run3_id, "req-agent", "skill_execution",
               "requirement/business-analysis", "claude", "claude-sonnet-4-6",
               3800, 2400, 15200, "success",
               "Analyze tank monitoring business requirements: real-time data, alert thresholds, historical trends...",
               "## 需求分析\n1. 实时监控: WebSocket 推送, <500ms 延迟\n2. 阈值告警: 三级 (黄色预警/橙色警戒/红色报警)\n3. 历史趋势: 7天/30天/90天 可选\n4. 导出: Excel + PDF"),
    make_event(t3 + timedelta(seconds=35), run3_id, "arch-agent", "skill_execution",
               "architecture/system-design", "claude", "claude-opus-4-8",
               5600, 3200, 18400, "success",
               "Design tank-monitor architecture: component tree, data flow, API contracts...",
               "## 架构设计\n```\n┌─ TankMonitorApp ──────────────────────┐\n│  ├─ DashboardLayout                  │\n│  │   ├─ RealTimeGauge (WebSocket)    │\n│  │   ├─ AlertPanel (SSE)             │\n│  │   └─ TrendChart (ECharts)         │\n│  ├─ DataService (React Query)        │\n│  └─ AlertEngine (Web Worker)         │\n└──────────────────────────────────────┘\n```\n\nAPI: REST + WS /api/tank/v2/..."),
    make_event(t3 + timedelta(seconds=55), run3_id, "arch-agent", "agent_decision",
               "architecture/review-approval", "claude", "claude-opus-4-8",
               1800, 500, 2800, "success",
               meta={"confirmed": True, "interaction_type": "confirm"}),
]

# Combine and write
all_events = r1_events + r2_events + r3_events

TRACE_DIR.mkdir(parents=True, exist_ok=True)
with open(TRACE_LOG, "w", encoding="utf-8") as f:
    for evt in all_events:
        f.write(json.dumps(evt, ensure_ascii=False) + "\n")

total_cost = sum(e["token_cost_estimate"] for e in all_events)
total_tokens = sum(e["token_input"] + e["token_output"] for e in all_events)
print(f"Seeded {len(all_events)} trace events across 3 runs.")
print(f"  Run 1 ({run1_id}): {len(r1_events)} events — equipment SOP (success)")
print(f"  Run 2 ({run2_id}): {len(r2_events)} events — warehouse bug analysis (with errors + safety flags)")
print(f"  Run 3 ({run3_id}): {len(r3_events)} events — dev SOP architecture (success)")
print(f"  Total tokens: {total_tokens:,} | Est. cost: ${total_cost:.4f}")
print(f"  Written to: {TRACE_LOG}")
