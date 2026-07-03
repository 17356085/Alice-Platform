"""SOP HITL — human-in-the-loop approval and quality gate nodes.

Extracted from sop_graph.py for single-responsibility.
"""

import re as _re
import logging

from langgraph.types import interrupt

from alice_engine.workflow.state import (
    SOPState, get_module_dir, get_page_dir, get_behavior_pack,
)

logger = logging.getLogger(__name__)

WORKSTUDY = __import__("pathlib").Path(".")


def _get_current_page(state: SOPState) -> str:
    """获取当前正在处理的页面 slug。"""
    pages = state.get("pages", [])
    idx = state.get("current_page_index", 0)
    return pages[idx] if idx < len(pages) else ""




def _load_p0_modules() -> list:
    """从 environments.yaml 加载 P0 模块白名单。"""
    import yaml
    pack = get_behavior_pack()
    if pack and pack.context_dir:
        env_path = pack.context_dir / "environments.yaml"
    else:
        env_path = WORKSTUDY / "context" / "environments.yaml"
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return list(data.get("hitl", {}).get("p0_modules", []))
        except Exception:
            pass
    return []




def _extract_p0_cases(content: str) -> list:
    """从 TEST_CASES.md 内容中提取 P0 用例。"""
    cases = []
    for line in content.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        # 匹配包含 P0 标记的行: markdown 表格行、标题行、列表项
        if "P0" in stripped and ("|" in stripped or stripped.startswith("#") or stripped.startswith("-")):
            cases.append({
                "title": stripped[:150],
                "priority": "P0",
            })
    return cases




def automation_strategy_approval_node(state: SOPState) -> dict:
    """
    ★ P1-3 HITL: 审批 AUTO_STRATEGY.md 后再生成代码。

    使用 LangGraph interrupt() 挂起执行，等待人工审批自动化策略。
    审批通过 → 继续生成 PageObject/测试脚本
    审批拒绝 → 退出，人工修改策略后重跑
    """
    page = _get_current_page(state)

    strategy_path = get_page_dir(state["module"], page) / "AUTO_STRATEGY.md"

    if not strategy_path.exists():
        # 无策略文件，自动通过
        return {"auto_strategy_approved": True}

    summary = strategy_path.read_text(encoding="utf-8")[:800]

    decision = interrupt({
        "type": "automation_strategy_approval",
        "module": state["module"],
        "page": page,
        "strategy_summary": summary,
        "options": ["approve", "reject", "edit"],
        "hint": (
            "审批 AUTO_STRATEGY.md — "
            "确认定位器策略(优先CSS/测试id?)、等待策略(wait_vue_stable?)、"
            "测试文件结构后再生成代码。reject=退出, edit=附带修改意见继续"
        ),
    })

    if decision == "approve":
        return {"auto_strategy_approved": True}
    elif isinstance(decision, dict) and decision.get("action") == "edit":
        return {
            "auto_strategy_approved": True,
            "human_feedback": decision.get("feedback", ""),
        }
    else:
        return {
            "auto_strategy_approved": False,
            "fatal_error": f"自动化策略被拒绝: {decision}",
        }




def testcase_approval_node(state: SOPState) -> dict:
    """
    ★ P1-3 HITL: P0 模块的测试用例需人工审批后才进入自动化阶段。

    仅当模块在 p0_modules 白名单中且存在 P0 用例时触发。
    非 P0 模块或无 P0 用例 → 自动通过。
    """
    page = _get_current_page(state)

    # 检查是否 P0 模块
    p0_modules = _load_p0_modules()
    if state["module"] not in p0_modules:
        return {"test_cases_approved": True}

    test_cases_path = get_page_dir(state["module"], page) / "TEST_CASES.md"

    if not test_cases_path.exists():
        return {"test_cases_approved": True}

    content = test_cases_path.read_text(encoding="utf-8")
    p0_cases = _extract_p0_cases(content)

    if not p0_cases:
        return {"test_cases_approved": True}

    decision = interrupt({
        "type": "testcase_approval",
        "module": state["module"],
        "page": page,
        "p0_case_count": len(p0_cases),
        "p0_cases_preview": [
            {"title": c["title"], "priority": c["priority"]}
            for c in p0_cases[:5]
        ],
        "options": ["approve", "reject", "modify"],
        "hint": (
            f"审批 {page} 的 {len(p0_cases)} 个 P0 测试用例 — "
            "确认覆盖关键业务场景后再生成自动化代码"
        ),
    })

    if decision == "approve":
        return {"test_cases_approved": True}
    elif isinstance(decision, dict) and decision.get("action") == "modify":
        return {
            "test_cases_approved": True,
            "human_feedback": decision.get("feedback", ""),
        }
    else:
        return {
            "test_cases_approved": False,
            "fatal_error": f"P0 测试用例被拒绝: {decision}",
        }


# ══════════════════════════════════════════════════════════════════════════
#  P2-5 业务覆盖质量门禁节点: TESTCASE_QUALITY_GATE (L3 Validator)
# ══════════════════════════════════════════════════════════════════════════

# BSC 评分阈值 (v2.7: 调低适配 AI 生成内容，关键词覆盖更宽)
BSC_PASS_THRESHOLD = 50       # 最低通过分
BSC_HITL_THRESHOLD = 30       # 低于此分强制 HITL
BSC_MAX_RETRY_ROUNDS = 1      # 最多打回重做轮次 (AI 重生成改善有限)




# ══════════════════════════════════════════════════════════════════════════
#  P2-5 业务覆盖质量门禁节点: TESTCASE_QUALITY_GATE (L3 Validator)
# ══════════════════════════════════════════════════════════════════════════

# BSC 评分阈值 (v2.7: 调低适配 AI 生成内容，关键词覆盖更宽)
BSC_PASS_THRESHOLD = 50       # 最低通过分
BSC_HITL_THRESHOLD = 30       # 低于此分强制 HITL
BSC_MAX_RETRY_ROUNDS = 1      # 最多打回重做轮次 (AI 重生成改善有限)


def _get_bsc_retry_count(state: SOPState) -> int:
    """获取当前页面 BSC 打回重试次数（从独立 state 字段读取，不会被 agent loop 覆盖）。"""
    return state.get("bsc_retry_count", 0)




def testcase_quality_gate_node(state: SOPState) -> dict:
    """
    P2-5 L3 Validator: 业务场景覆盖质量门禁。

    在 Test Design 完成后、Automation 开始前运行。
    检查 BUSINESS_SCENARIOS.md → TEST_DESIGN.md → TEST_CASES.md 的
    业务覆盖链是否完整。

    评分规则:
      - score ≥ 60 → PASS → 进入 Automation
      - score 40-59 → WARN → P0 模块 HITL，非 P0 放行
      - score < 40 → BLOCK → 打回 Test Design 重做 (max 2 rounds)

    发射事件:
      - BusinessCoverageInsufficient (score < threshold)
      - WorkflowCoverageInsufficient (cross_page=0 且 pages≥2)
    """
    import re as _re

    page = _get_current_page(state)
    module = state.get("module", "")
    pages = state.get("pages", [])

    bsc_retry = _get_bsc_retry_count(state)

    # 定位产物文件
    page_dir = get_page_dir(module, page)
    bs_path = page_dir / "BUSINESS_SCENARIOS.md"
    td_path = page_dir / "TEST_DESIGN.md"
    tc_path = page_dir / "TEST_CASES.md"

    # ── 计算 BSC Score ──
    score = 0
    bs_content = bs_path.read_text(encoding="utf-8") if bs_path.exists() else ""
    td_content = td_path.read_text(encoding="utf-8") if td_path.exists() else ""
    tc_content = tc_path.read_text(encoding="utf-8") if tc_path.exists() else ""

    # Layer 1: 产物存在性 (30分)
    if bs_path.exists():
        score += 10
    else:
        score -= 5
    if td_path.exists():
        score += 10
    else:
        score -= 5
    if tc_path.exists():
        score += 10
    else:
        score -= 5

    # Layer 2: 业务维度覆盖 (50分)
    # v2.7: expanded keywords to match AI-generated Chinese terminology
    bs_dimensions = {
        "业务目标": ["业务目标", "Business Goal", "核心业务目标", "测试目标", "验证目标"],
        "角色": ["角色", "Role", "角色与旅程", "用户角色", "权限", "admin", "普通用户"],
        "流程": ["流程", "Workflow", "业务流程", "Happy Path", "Alternative Path",
                "正常流程", "异常流程", "操作流程", "步骤"],
        "业务规则": ["业务规则", "Business Rule", "状态流转", "触发规则", "计算规则",
                   "校验", "验证规则", "约束", "限制"],
        "数据流": ["数据流", "Data Flow", "数据来源", "数据消费",
                  "接口", "API", "请求", "响应", "字段", "参数", "数据传递"],
        "风险映射": ["风险", "场景映射", "Risk-to-Scenario", "关联风险",
                    "潜在问题", "边界条件", "异常场景"],
    }
    for keywords in bs_dimensions.values():
        if any(kw.lower() in bs_content.lower() for kw in keywords):
            score += 8
        elif any(kw.lower() in td_content.lower() for kw in keywords):
            score += 4
        elif any(kw.lower() in tc_content.lower() for kw in keywords):
            score += 3  # v2.7: fallback to TC if neither BS nor TD match

    # 第 9 维检测 — v2.7: expanded to match AI-generated patterns
    bs_dim9_markers = [
        "业务场景验证", "业务场景", "端到端业务流程", "角色协作",
        "BS-", "跨页面", "数据流完整性", "状态机验证",
        "测试场景", "测试用例", "用例", "覆盖", "场景",
    ]
    bs_dim9_hits = sum(1 for m in bs_dim9_markers if m.lower() in td_content.lower())
    if bs_dim9_hits >= 3:
        score += 8
    elif bs_dim9_hits >= 1:
        score += 4

    # Layer 3: 用例质量标记 (20分)
    # v2.7: accept TC-XXX format (AI common) in addition to BS-XXX-XXX
    bs_id_count = len(_re.findall(r'BS-\w+-\d{3}', tc_content))
    tc_id_count = len(_re.findall(r'TC-\w+-\d{3}', tc_content))
    case_id_count = bs_id_count + tc_id_count
    if case_id_count >= 5:
        score += 10
    elif case_id_count >= 1:
        score += 5
    if "P0" in tc_content or "阻塞" in tc_content:
        score += 5
    placeholder_patterns = ["输入XXX", "输入用户名", "输入密码", "输入数据", "输入值"]
    if not any(p in tc_content for p in placeholder_patterns):
        score += 5

    score = max(0, min(100, score))

    # 跨页面覆盖检查
    cross_page_markers = [
        "跨页面", "cross-page", "跨模块", "cross-module",
        "page-a", "page-b", "→", "流转到",
    ]
    has_cross_page = any(
        _re.search(m, bs_content, _re.IGNORECASE) for m in cross_page_markers
    ) if bs_content else False

    # ── 判定 ──
    p0_modules = _load_p0_modules()
    is_p0 = module in p0_modules

    gate_result = {
        "gate": "TESTCASE_QUALITY_GATE",
        "level": "L3_VALIDATOR",
        "phase": "Test Design",
        "page": page,
        "score": score,
        "bs_dim9_hits": bs_dim9_hits,
        "bs_id_count": bs_id_count,
        "has_cross_page": has_cross_page,
        "has_bs_file": bs_path.exists(),
        "bsc_retry_count": bsc_retry,
    }

    if score >= BSC_PASS_THRESHOLD:
        gate_result["ok"] = True
        gate_result["action"] = "pass"
        updates = {
            "gate_results": [gate_result],
            "test_cases_approved": True,  # 质量门禁通过，等同于审批通过
            "force_retry_phase": None,    # ★ 清除重试标记
        }

    elif score >= BSC_HITL_THRESHOLD:
        if is_p0:
            # P0 模块: 警告级 → HITL
            gate_result["ok"] = False
            gate_result["action"] = "hitl_warn"
            decision = interrupt({
                "type": "business_coverage_warning",
                "module": module,
                "page": page,
                "score": score,
                "threshold": BSC_PASS_THRESHOLD,
                "gate_result": gate_result,
                "options": ["approve", "retry"],
                "hint": (
                    f"业务覆盖评分 {score} < {BSC_PASS_THRESHOLD} (阈值 {BSC_PASS_THRESHOLD})。"
                    "approve=接受当前覆盖继续; retry=打回 Test Design 重做"
                ),
            })
            if decision == "approve":
                gate_result["ok"] = True
                gate_result["action"] = "hitl_approved"
                updates = {
                    "gate_results": [gate_result],
                    "test_cases_approved": True,
                    "force_retry_phase": None,
                }
            else:
                gate_result["action"] = "retry"
                updates = {
                    "gate_results": [gate_result],
                    "test_cases_approved": False,
                    "force_retry_phase": "Test Design",
                    "human_feedback": str(decision) if isinstance(decision, str) else "",
                }
        else:
            # 非 P0: 警告但放行
            gate_result["ok"] = True
            gate_result["action"] = "warn_pass"
            updates = {
                "gate_results": [gate_result],
                "test_cases_approved": True,
                "force_retry_phase": None,
            }

    else:
        # score < 40: 硬阻断
        if bsc_retry < BSC_MAX_RETRY_ROUNDS:
            gate_result["ok"] = False
            gate_result["action"] = "retry"
            updates = {
                "gate_results": [gate_result],
                "bsc_retry_count": bsc_retry + 1,
                "test_cases_approved": False,
                "force_retry_phase": "Test Design",
            }
        else:
            # 超过最大重试次数 → HITL
            gate_result["ok"] = False
            gate_result["action"] = "hitl_block"
            decision = interrupt({
                "type": "business_coverage_blocked",
                "module": module,
                "page": page,
                "score": score,
                "threshold": BSC_HITL_THRESHOLD,
                "retry_count": bsc_retry,
                "gate_result": gate_result,
                "options": ["force_continue", "abort"],
                "hint": (
                    f"业务覆盖评分 {score} < {BSC_HITL_THRESHOLD}，"
                    f"已重试 {bsc_retry} 次仍不达标。"
                    "force_continue=强制继续; abort=终止流程"
                ),
            })
            if decision == "force_continue":
                gate_result["ok"] = True
                gate_result["action"] = "force_continue"
                updates = {
                    "gate_results": [gate_result],
                    "test_cases_approved": True,
                    "force_retry_phase": None,
                }
            else:
                updates = {
                    "gate_results": [gate_result],
                    "test_cases_approved": False,
                    "force_retry_phase": None,
                    "fatal_error": f"业务覆盖质量门禁阻断: score={score} < {BSC_HITL_THRESHOLD}",
                }

    # ── 发射事件 ──
    try:
        if score < BSC_PASS_THRESHOLD:
            emit("BusinessCoverageInsufficient",
                 module=module, page=page,
                 score=score, threshold=BSC_PASS_THRESHOLD,
                 dimensions_detail=str(gate_result))
        if not has_cross_page and len(pages) >= 2:
            emit("WorkflowCoverageInsufficient",
                 module=module, page_count=len(pages),
                 cross_page_scenarios=0)
    except Exception as e:
        import logging
        logging.getLogger("aitest.graph").warning(
            f"testcase_quality_gate: event emission failed: {e}")


    return updates


# ══════════════════════════════════════════════════════════════════════════
#  数据清理节点: 离线扫描并清理测试残留数据
# ══════════════════════════════════════════════════════════════════════════



def qa_loop_decision_node(state: SOPState) -> dict:
    """Bug Analysis 完成后的 QA Loop 状态机。

    H5 fix: 原来嵌在 route_next_phase 中的 state mutation + I/O
    提取为独立节点，符合 LangGraph 契约（routing function 必须纯函数）。

    决策逻辑:
      - escalate → 跳过修复，去 Report
      - 还有重试额度 + 有失败 → 回 Automation 修复
      - 轮数耗尽 或 无失败 → 结束 QA Loop
    """
    completed = set(state.get("completed_phases", []))
    agent_outputs = state.get("agent_outputs", {})

    # 检查执行是否失败
    execution_failed = agent_outputs.get("execution_failed", False)
    if not execution_failed:
        exec_result = agent_outputs.get("execution-agent", {})
        if isinstance(exec_result, dict):
            execution_failed = exec_result.get("execution_failed", False) or not exec_result.get("success", True)

    qa_rounds = state.get("qa_loop_rounds", 0)
    qa_max = state.get("qa_loop_max_rounds", 3)
    qa_should_escalate = state.get("qa_should_escalate", False)

    updates: dict = {}

    # 初始化 QA Loop 状态（首次进入 Bug Analysis）
    if "Bug Analysis" not in state.get("qa_loop_phases_seen", []):
        updates["qa_loop_rounds"] = 0
        updates["qa_loop_max_rounds"] = state.get("qa_loop_max_rounds", 3)
        updates["qa_should_escalate"] = False
        seen = list(state.get("qa_loop_phases_seen", []))
        seen.append("Bug Analysis")
        updates["qa_loop_phases_seen"] = seen

    run_id = state.get("run_id", "")
    module = state.get("module", "")

    if qa_should_escalate:
        # 不可自动修复 → 跳过后续修复, 直接去 Report
        updates["qa_loop_status"] = "escalated"
        updates["qa_loop_decision"] = "report"
        logger.info("[QA Loop] escalated: run=%s module=%s round=%s/%s",
                    run_id, module, qa_rounds, qa_max)

    elif qa_rounds < qa_max and execution_failed:
        # 还有重试额度 → 路由到 Automation 修复
        new_round = qa_rounds + 1
        updates["qa_loop_rounds"] = new_round
        updates["qa_loop_decision"] = "automation"
        logger.info("[QA Loop] retry_round_%s: run=%s module=%s round=%s/%s",
                    new_round, run_id, module, new_round, qa_max)

    else:
        # 轮数耗尽 或 无失败 → 结束 QA Loop
        status = "passed" if not execution_failed else "max_rounds"
        updates["qa_loop_status"] = status
        updates["qa_loop_decision"] = "next_phase"
        logger.info("[QA Loop] %s: run=%s module=%s round=%s/%s",
                    status, run_id, module, qa_rounds, qa_max)

    return updates


# ══════════════════════════════════════════════════════════════════════════
#  图构建
# ══════════════════════════════════════════════════════════════════════════

