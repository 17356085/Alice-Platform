"""
SOPGraph — 顶层 LangGraph 编排器。

替换 full-sop.workflow.js + workflow_engine.py 的编排逻辑。

图结构:
  START → entry → preflight → cond_route ─┬→ project_agent ─→ cond_route
                                          ├→ requirement_agent ─→ cond_route
                                          ├→ test_design_agent ─→ cond_route
                                          ├→ automation_agent ─→ cond_route
                                          ├→ execution_agent ─→ cond_route
                                          ├→ bug_analysis_agent ─→ cond_route
                                          ├→ report_agent ─→ cond_route
                                          ├→ knowledge_agent ─→ cond_route
                                          └→ exit → END

用法:
  from aitest.graphs.sop_graph import build_sop_graph
  from aitest.graphs.checkpoint import get_checkpointer
  from aitest.graphs.state import create_initial_state

  graph = build_sop_graph()
  compiled = graph.compile(checkpointer=get_checkpointer())
  result = compiled.invoke(
      create_initial_state("equipment", ["alarm-config", "camera", "key-param", "maintenance"]),
      {"configurable": {"thread_id": "my-run"}}
  )
"""

import json
import time
from pathlib import Path
from typing import Optional

from langgraph.graph import StateGraph, END
from langgraph.types import interrupt  # P1-3 HITL: automation strategy + test case approval

from aitest.graphs.state import (
    SOPState,
    SOPMode,
    PhaseName,
    AgentName,
    GateResult,
    GateLevel,
    CANONICAL_PHASES,
    MODE_SKIP_MAP,
    AGENT_PHASE_MAP,
    get_module_dir,
    get_page_dir,
)
from aitest.graphs.nodes import make_agent_loop_node

# ── 路径配置 ──────────────────────────────────────────────────────────
from aitest.platform.paths import get_workstudy, get_test_project_root, get_context_modules, get_governance_dir, get_project_dir
WORKSTUDY = get_workstudy()
GOVERNANCE = get_governance_dir()
CONTEXT_MODULES = get_context_modules()
ARTIFACTS_DIR = GOVERNANCE / "artifacts"


# ── P1-5: Preflight 结果缓存 ──
_preflight_cache: dict[str, dict] = {}
# P1 可观测性: preflight 缓存命中/总计计数器
_preflight_cache_hits: int = 0
_preflight_cache_total: int = 0
# ★ #8: 缓存失效 — 基于文件 mtime 的 TTL
_preflight_cache_mtimes: dict[str, float] = {}


# ══════════════════════════════════════════════════════════════════════════
#  节点函数
# ══════════════════════════════════════════════════════════════════════════

def _get_max_mtime(module: str) -> float:
    """★ #8: 获取模块关键目录的最新 mtime，用于 preflight 缓存失效。

    扫描:
      - PROJECT_CONTEXT.md
      - MODULE_CONTEXT.md
      - pages/*/ 下所有文件
      - ZJSN_Test-master526/page/<module>_page/ 下的 .py 文件
      - ZJSN_Test-master526/script/<module>/ 下的 .py 文件
    """
    max_mtime = 0.0
    dirs_to_check = [
        get_module_dir(module),
        get_project_dir(),
    ]
    zjsn = get_test_project_root()
    code_dirs = [
        zjsn / "page" / f"{module}_page",
        zjsn / "script" / module,
    ] if zjsn else []

    for d in dirs_to_check + code_dirs:
        if not d.exists():
            continue
        try:
            for fpath in d.rglob("*"):
                if fpath.is_file() and not fpath.name.startswith("."):
                    try:
                        mtime = fpath.stat().st_mtime
                        if mtime > max_mtime:
                            max_mtime = mtime
                    except OSError:
                        pass
        except OSError:
            pass

    return max_mtime


def entry_node(state: SOPState) -> dict:
    """
    入口节点：初始化运行时状态。

    - 计算 skip_phases（基于 mode）
    - 设置 run_id（如果未提供）
    - 处理 status 模式：直接跳到 exit
    """
    mode = state.get("mode", "full")
    skip_phases = list(MODE_SKIP_MAP.get(mode, []))

    updates: dict = {
        "skip_phases": skip_phases,
        "current_phase": "Preflight",
        "status": "running",
    }

    # Status 模式：跳过所有 phase，直接标记完成
    if mode == "status":
        updates["current_phase"] = "Preflight"
        # 将在 preflight 后直接 exit

    # Resume 模式：从 artifact 扫描结果恢复
    if mode == "resume":
        # skip_phases 保持为空 — 由 preflight 决定哪些已完成
        pass

    return updates


def preflight_node(state: SOPState) -> dict:
    """
    起飞前检查节点：扫描现有产物，确定哪些 Phase 已完成。

    对应 full-sop.workflow.js 的 Preflight phase。

    检查内容:
      1. PROJECT_CONTEXT.md 是否存在
      2. MODULE_INDEX.md 中是否列出了此模块
      3. 模块目录是否存在 (MODULE_CONTEXT.md)
      4. 每个页面：PAGE_CONTEXT.md / TEST_CASES.md / TECH_ANALYSIS.md 是否存在
      5. SOP_STATUS_<module>.json 是否存在（resume 模式）
    """
    module = state.get("module", "")
    mode = state.get("mode", "full")
    pages = list(state.get("pages", []))

    # ★ P1-5: Preflight result cache — 非 resume 模式复用已扫描结果
    global _preflight_cache_total, _preflight_cache_hits, _preflight_cache_mtimes
    cache_key = f"{module}:{mode}:{':'.join(sorted(pages))}"
    _preflight_cache_total += 1  # P1 可观测性
    if mode != "resume" and cache_key in _preflight_cache:
        # ★ #8: mtime 失效检查 — 扫描关键目录，有更新则失效
        cached_mtime = _preflight_cache_mtimes.get(cache_key, 0.0)
        current_mtime = _get_max_mtime(module)
        if current_mtime <= cached_mtime:
            _preflight_cache_hits += 1  # P1 可观测性
            return _preflight_cache[cache_key]
        else:
            # 缓存过期 — 清理并重新扫描
            del _preflight_cache[cache_key]
            _preflight_cache_mtimes.pop(cache_key, None)

    completed_phases: list[PhaseName] = []
    artifact_map: dict = {}

    # ── 检查 PROJECT_CONTEXT ──
    project_context = get_project_dir() / "PROJECT_CONTEXT.md"
    if project_context.exists():
        artifact_map["Project Init"] = [str(project_context)]

    # ── 检查 MODULE_CONTEXT ──
    module_context = get_module_dir(module) / "MODULE_CONTEXT.md"
    if module_context.exists() and module_context.stat().st_size > 0:
        if mode != "from-requirement":  # from-requirement 只跳过 Project Init
            pass  # 存在不代表 Project Init 完成，只是 prereq

    # ── 检查 Requirement phase 产物 ──
    requirement_artifact = get_module_dir(module) / "MODULE_CONTEXT.md"
    if requirement_artifact.exists() and requirement_artifact.stat().st_size > 0:
        # MODULE_CONTEXT.md 存在 → Requirement phase 至少部分完成
        pass

    # ── 检查 SOP_STATUS（resume 模式 + 所有模式均可受益）──
    status_file = ARTIFACTS_DIR / f"SOP_STATUS_{module}.json"

    # ★ #5: Resume 时优先从 LangGraph checkpoint 恢复（完整 State，支持时间旅行）
    # JSON 作为 fallback（checkpoint 不可用时）
    checkpoint_loaded = False
    if mode == "resume":
        run_id = state.get("run_id", "")
        if run_id:
            try:
                from aitest.graphs.checkpoint import get_checkpointer
                cp = get_checkpointer()
                # 尝试从 checkpoint 恢复最近的状态
                saved = cp.get_tuple({"configurable": {"thread_id": run_id}})
                if saved and saved.checkpoint:
                    cp_state = saved.checkpoint.get("channel_values", {})
                    cp_completed = cp_state.get("completed_phases", [])
                    if cp_completed:
                        completed_phases = [p for p in cp_completed if p in CANONICAL_PHASES]
                        checkpoint_loaded = True
            except Exception:
                pass  # checkpoint 不可用，fallback 到 JSON

    if not checkpoint_loaded and status_file.exists():
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                status_data = json.load(f)
            saved_completed = status_data.get("completed_phases", [])

            # ★ U2修复: 旧格式 Phase 名称 → 规范名称映射
            _LEGACY_PHASE_MAP = {
                "Phase 0 (Project Init)": "Project Init",
                "Phase 0.5 (Module Modeling": "Requirement",
                "Phase 0.8": "Requirement",
                "Phase 1 (Page Analysis": "Test Design",
                "Phase 1.5 (Risk Modeling": "Test Design",
                "Phase 2 (Test Design": "Test Design",
                "Phase 2.5 (Test Cases": "Test Design",
                "Phase 3 (Tech Analysis": "Automation",
                "Phase 3.5 (Auto Strategy": "Automation",
                "Phase 3-4 (Automation": "Automation",
                "Phase 4 (Code Generation": "Automation",
                "Phase 4.5": "Bug Analysis",
                "Phase 4.5-7": "Execute & Debug",
                "Phase 5": "Bug Analysis",
                "Phase 6": "Test Design",
                "Phase 7": "Bug Analysis",
                "Phase 8": "Report",
                "Phase 9": "Knowledge",
            }
            # 也兼容 sop_validator.py 旧规范名称
            _LEGACY_PHASE_MAP.update({
                "Module Modeling": "Requirement",
                "Execution": "Execute & Debug",
            })

            resolved = []
            for p in saved_completed:
                # 先尝试规范名称
                if p in CANONICAL_PHASES:
                    resolved.append(p)
                # 再尝试旧格式映射（前缀匹配，因为旧格式可能包含长描述）
                elif p in _LEGACY_PHASE_MAP:
                    mapped = _LEGACY_PHASE_MAP[p]
                    if mapped not in resolved:
                        resolved.append(mapped)
                else:
                    # 前缀模糊匹配（如 "Phase 0.5 (Module Modeling — MODULE_CONTEXT.md v2.0)"）
                    matched = False
                    for legacy_prefix, canonical in _LEGACY_PHASE_MAP.items():
                        if p.startswith(legacy_prefix):
                            if canonical not in resolved:
                                resolved.append(canonical)
                            matched = True
                            break
                    if not matched:
                        # 最后的尝试：检查是否包含已知规范名称
                        for cp in CANONICAL_PHASES:
                            if cp in p and cp not in resolved:
                                resolved.append(cp)
                                matched = True
                                break
            completed_phases = resolved
        except (json.JSONDecodeError, KeyError):
            pass

    # ── 发现页面 ──
    if not pages:
        # 自动发现模块下的所有页面
        pages_dir = get_module_dir(module) / "pages"
        if pages_dir.exists():
            discovered = [
                d.name for d in pages_dir.iterdir()
                if d.is_dir() and not d.name.startswith(".") and not d.name.startswith("_")
            ]
            pages = discovered

    # ── 检查每个页面的产物 ──
    per_page_results = []
    for page_slug in pages:
        page_dir = get_page_dir(module, page_slug)
        page_info = {
            "page_slug": page_slug,
            "has_page_context": (page_dir / "PAGE_CONTEXT.md").exists(),
            "has_test_cases": (page_dir / "TEST_CASES.md").exists(),
            "has_test_design": (page_dir / "TEST_DESIGN.md").exists(),
            "has_risk_model": (page_dir / "RISK_MODEL.md").exists(),
            "has_tech_analysis": (page_dir / "TECH_ANALYSIS.md").exists(),
            "has_auto_strategy": (page_dir / "AUTO_STRATEGY.md").exists(),
            # PAGE_INTERFACE.yaml — 可选精简索引。不影响 Phase 判定。
            "has_page_interface": (page_dir / "PAGE_INTERFACE.yaml").exists(),
        }

        page_artifacts = []
        for key, path_suffix in [
            ("PAGE_CONTEXT.md", "PAGE_CONTEXT.md"),
            ("TEST_CASES.md", "TEST_CASES.md"),
            ("TECH_ANALYSIS.md", "TECH_ANALYSIS.md"),
            ("AUTO_STRATEGY.md", "AUTO_STRATEGY.md"),
        ]:
            fpath = page_dir / path_suffix
            if fpath.exists():
                page_artifacts.append(str(fpath))

        page_info["artifacts"] = page_artifacts
        per_page_results.append(page_info)

        # 将 artifacts 添加到总 map
        artifact_map.setdefault(page_slug, []).extend(page_artifacts)

    # ── 自动模式检测：根据产物完整度推荐最优 mode ──
    has_project = project_context.exists()
    has_module = module_context.exists() and module_context.stat().st_size > 0
    has_page_context = any(p["has_page_context"] for p in per_page_results) if per_page_results else False
    has_test_cases = any(p["has_test_cases"] for p in per_page_results) if per_page_results else False
    has_tech = any(p["has_tech_analysis"] for p in per_page_results) if per_page_results else False

    # 检查代码是否存在
    zjsn = get_test_project_root()
    has_code = False
    if zjsn:
        po_dir = zjsn / "page" / f"{module}_page"
        test_dir = zjsn / "script" / module
        has_code = po_dir.exists() and test_dir.exists() and \
            any(po_dir.glob("*Page.py")) and any(test_dir.glob("test_*.py"))

    # 检查 allure 是否有失败
    allure_results = zjsn / "allure-results" if zjsn else None
    has_failures = False
    if allure_results and allure_results.exists():
        try:
            for f in allure_results.glob("*-result.json"):
                content = f.read_text(encoding="utf-8")
                if '"status":"failed"' in content or '"status":"broken"' in content:
                    has_failures = True
                    break
        except Exception as e:
            from aitest.infra.error_logger import log_error
            log_error("sop_graph.preflight", "allure_scan", e, {"module": module})

    # 推荐模式 — 默认走完整流水线，只有显式 status 才跳过
    if not has_project:
        recommended_mode = "full"
        mode_reason = "PROJECT_CONTEXT 缺失，建议从头开始"
    elif not has_module:
        recommended_mode = "full"
        mode_reason = "MODULE_CONTEXT 缺失，建议从头开始"
    elif not has_page_context:
        recommended_mode = "from-test-design"
        mode_reason = "缺少页面分析，建议从测试设计阶段开始"
    elif not has_code:
        recommended_mode = "from-automation"
        mode_reason = "测试设计已完成但无代码，建议从自动化阶段开始"
    elif has_failures:
        recommended_mode = "from-automation"
        mode_reason = "代码已存在但 allure 有失败记录，建议重新执行+修复"
    else:
        # 代码存在且测试通过 → 仍然走 from-automation（会进入 Execute & Debug）
        # status 模式仅由用户显式指定，preflight 不自动推荐
        recommended_mode = "from-automation"
        mode_reason = "所有产物完整，建议从自动化阶段开始（包含测试执行）"

    # ── 判断已完成的 Phase（基于产物）──
    if all(p["has_page_context"] for p in per_page_results) and per_page_results:
        pass

    # 基于 data 决定项目初始化的完成状态
    if project_context.exists() and module_context.exists():
        if "Project Init" not in completed_phases and mode == "resume":
            completed_phases.append("Project Init")

    # 如果用户没指定 mode（或用了不合理的 mode），自动采用推荐
    user_mode = state.get("mode", "full")
    auto_mode = user_mode
    if user_mode == "full" and recommended_mode != "full":
        # 用户可能不知道可以用更快的方式 — 在 agent_outputs 里提示
        pass

    result = {
        "pages": pages,
        "per_page_results": per_page_results,
        "artifact_map": artifact_map,
        "completed_phases": completed_phases,
        "current_page_index": 0,
        "current_phase": "Preflight",
        "agent_outputs": {
            **state.get("agent_outputs", {}),
            "preflight_auto_detect": {
                "recommended_mode": recommended_mode,
                "reason": mode_reason,
                "has_project": has_project,
                "has_module": has_module,
                "has_page_context": has_page_context,
                "has_test_cases": has_test_cases,
                "has_tech_analysis": has_tech,
                "has_code": has_code,
                "has_failures": has_failures,
                "hint": f"建议使用 --mode={recommended_mode} 跳过不必要的阶段" if recommended_mode != user_mode else "当前 mode 已是最优",
            },
        },
    }

    # ★ P1-5: 缓存 preflight 结果（含 mtime 用于 #8 TTL）
    _preflight_cache[cache_key] = result
    _preflight_cache_mtimes[cache_key] = _get_max_mtime(module)

    return result


def exit_node(state: SOPState) -> dict:
    """
    出口节点：写入最终状态，发射 CycleEnd 事件。

    - 写入 SOP_STATUS_<module>.json
    - 发射 CycleEnd 事件到 EventBus
    """
    module = state.get("module", "")
    completed = state.get("completed_phases", [])
    failed = state.get("failed_phases", [])
    fatal = state.get("fatal_error")

    # 确定最终状态
    if fatal:
        final_status = "failed"
        termination = f"fatal_error: {fatal}"
    elif failed:
        final_status = "completed_with_issues"
        termination = f"completed_with_issues: {len(failed)} phases failed"
    else:
        final_status = "completed"
        termination = "all_phases_completed"

    # 写入 SOP_STATUS JSON
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    status_file = ARTIFACTS_DIR / f"SOP_STATUS_{module}.json"
    status_payload = {
        "module": module,
        "status": final_status,
        "completed_phases": completed,
        "failed_phases": failed,
        "pages_processed": state.get("pages", []),
        "per_page_results": [
            {"page_slug": r.get("page_slug", r.get("page", "?")),
             "status": r.get("status", "?"),
             "artifacts": r.get("artifacts", [])}
            for r in state.get("per_page_results", [])
        ],
        "agent_summary": {
            name: {"success": a.get("success", False),
                   "skills_completed": len(a.get("completed_skills", [])),
                   "termination": a.get("termination_reason", "")}
            for name, a in state.get("agent_outputs", {}).items()
            if isinstance(a, dict)
        },
        "run_id": state.get("run_id", ""),
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "engine": "langgraph",
    }
    try:
        with open(status_file, "w", encoding="utf-8") as f:
            json.dump(status_payload, f, ensure_ascii=False, indent=2)
    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("sop_graph.exit", "write_status_json", e, {"module": module, "file": str(status_file)})

    # 发射 CycleEnd 事件
    try:
        from aitest.audit_engine.event_bus import emit
        emit("CycleEnd", module=module, status=final_status, engine="langgraph")
    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("sop_graph.exit", "emit_cycle_end", e, {"module": module, "status": final_status})

    # P0-2: 在 CycleEnd 后自动运行 State Auditor (全量 S/C/Q/T Check)
    try:
        from aitest.audit_engine.state_auditor import StateAuditor
        auditor = StateAuditor()
        audit_report = auditor.audit(module, auto_repair=False)
        if audit_report["drift_count"] > 0:
            # 发现漂移 → 发射 StateDrift 事件
            from aitest.audit_engine.event_bus import emit as _emit2
            try:
                _emit2("StateDrift",
                       module=module,
                       run_id=state.get("run_id", ""),
                       drift_count=audit_report["drift_count"],
                       error_count=audit_report["error_count"],
                       warning_count=audit_report["warning_count"],
                       overall_status=audit_report["overall_status"])
            except Exception as e:
                from aitest.infra.error_logger import log_error
                log_error("sop_graph.exit", "emit_StateDrift", e, {"module": module})
    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("sop_graph.exit", "state_auditor", e, {"module": module})

    # P1-2: SOP Auditor — 全量 6 维检查 (P0-FIX 2026-06-15: 从 3 维扩展到 6 维)
    try:
        from aitest.audit_engine.sop_auditor import SOPAuditor
        sop_auditor = SOPAuditor()
        sop_report = sop_auditor.audit(module, days=1)  # 默认全部 6 维: p/s/g/h/b/l
        if sop_report["total_violations"] > 0:
            from aitest.audit_engine.event_bus import emit as _emit3
            try:
                _emit3("SOPViolation",
                       module=module,
                       run_id=state.get("run_id", ""),
                       violation_type="cycle_end_audit",
                       detail=f"SOP 审计发现 {sop_report['total_violations']} 个违规")
            except Exception as e2:
                from aitest.infra.error_logger import log_error
                log_error("sop_graph.exit", "emit_SOPViolation", e2, {"module": module})
    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("sop_graph.exit", "sop_auditor", e, {"module": module})

    return {
        "status": final_status,
        "current_phase": "Complete",
        "fatal_error": fatal if final_status == "failed" else None,
    }


# ══════════════════════════════════════════════════════════════════════════
#  P1-3 HITL 扩展节点: 自动化策略审批 + 测试用例审批
# ══════════════════════════════════════════════════════════════════════════

def _get_current_page(state: SOPState) -> str:
    """获取当前正在处理的页面 slug。"""
    pages = state.get("pages", [])
    idx = state.get("current_page_index", 0)
    return pages[idx] if idx < len(pages) else ""


def _load_p0_modules() -> list:
    """从 environments.yaml 加载 P0 模块白名单。"""
    import yaml
    env_path = GOVERNANCE / "context" / "environments.yaml"
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

# BSC 评分阈值
BSC_PASS_THRESHOLD = 60       # 最低通过分
BSC_HITL_THRESHOLD = 40       # 低于此分强制 HITL
BSC_MAX_RETRY_ROUNDS = 2      # 最多打回重做轮次


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
    bs_dimensions = {
        "业务目标": ["业务目标", "Business Goal", "核心业务目标"],
        "角色": ["角色", "Role", "角色与旅程"],
        "流程": ["流程", "Workflow", "业务流程", "Happy Path", "Alternative Path"],
        "业务规则": ["业务规则", "Business Rule", "状态流转", "触发规则", "计算规则"],
        "数据流": ["数据流", "Data Flow", "数据来源", "数据消费"],
        "风险映射": ["风险", "场景映射", "Risk-to-Scenario", "关联风险"],
    }
    for keywords in bs_dimensions.values():
        if any(kw.lower() in bs_content.lower() for kw in keywords):
            score += 8
        elif any(kw.lower() in td_content.lower() for kw in keywords):
            score += 4

    # 第 9 维检测
    bs_dim9_markers = [
        "业务场景验证", "业务场景", "端到端业务流程", "角色协作",
        "BS-", "跨页面", "数据流完整性", "状态机验证",
    ]
    bs_dim9_hits = sum(1 for m in bs_dim9_markers if m.lower() in td_content.lower())
    if bs_dim9_hits >= 3:
        score += 8
    elif bs_dim9_hits >= 1:
        score += 4

    # Layer 3: 用例质量标记 (20分)
    bs_id_count = len(_re.findall(r'BS-\w+-\d{3}', tc_content))
    if bs_id_count >= 5:
        score += 10
    elif bs_id_count >= 1:
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
        from aitest.audit_engine.event_bus import emit
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

def data_sanitization_node(state: SOPState) -> dict:
    """
    执行 scan_and_clean.py --force 清理测试残留数据。

    对应 test-data-policy.md 兜底策略: 测试执行后离线扫描，确保不留脏数据。
    SOP 位置: Bug Analysis → Data Sanitization → Report

    产出:
      - agent_outputs["data-sanitization"] = {residual_count, cleaned_count, threshold_exceeded}
      - gate_results 追加门禁结果
    """
    import subprocess
    import re

    module = state.get("module", "")
    scan_script = ZJSN_TEST / "tools" / "cleanup" / "scan_and_clean.py"

    updates: dict = {
        "agent_outputs": {**state.get("agent_outputs", {})},
        "gate_results": list(state.get("gate_results", [])),
        "completed_phases": ["Data Sanitization"],
    }

    if not scan_script.exists():
        updates["agent_outputs"]["data-sanitization"] = {
            "residual_count": 0, "cleaned_count": 0,
            "threshold_exceeded": False,
            "warning": f"scan_and_clean.py 不存在: {scan_script}",
        }
        return updates

    try:
        # ★ v1.0: 使用 secure_run 替代裸 subprocess.run (安全校验)
        from aitest.infra.secure_subprocess import secure_run
        result = secure_run(
            ["python", str(scan_script), "--force"],
            capture_output=True, text=True, timeout=120,
            cwd=str(ZJSN_TEST),
            check=False,  # 不抛异常，手动检查返回码
        )
        stdout = result.stdout + result.stderr

        # 解析输出: "总计: N 条残留数据" / "共清理 N 条数据" / "未发现残留"
        residual_match = re.search(r"总计:\s*(\d+)\s*条残留数据", stdout)
        cleaned_match = re.search(r"共清理\s*(\d+)\s*条数据", stdout)
        no_residual = "未发现残留" in stdout

        residual_count = int(residual_match.group(1)) if residual_match else 0
        cleaned_count = int(cleaned_match.group(1)) if cleaned_match else 0
        threshold = 50  # max_residual_allowed
        threshold_exceeded = residual_count > threshold

        sanitization_result = {
            "residual_count": residual_count,
            "cleaned_count": cleaned_count,
            "threshold_exceeded": threshold_exceeded,
            "no_residual": no_residual,
            "script_ok": result.returncode == 0,
        }
        updates["agent_outputs"]["data-sanitization"] = sanitization_result

        # 门禁: PASS = 无残留或已全部清理
        gate_ok = residual_count == 0 or (cleaned_count >= residual_count)
        updates["gate_results"].append(GateResult(
            level=GateLevel.L2_AGENT,
            phase="Data Sanitization",
            ok=gate_ok,
            message=(
                f"Data Sanitization: {'PASS' if gate_ok else 'WARN'} "
                f"(residual={residual_count}, cleaned={cleaned_count})"
            ),
            details=sanitization_result,
        ).to_dict())

        if threshold_exceeded:
            from aitest.infra.error_logger import log_error
            log_error(
                "sop_graph.data_sanitization", "threshold_exceeded",
                Exception(f"残留数据 {residual_count} 超过阈值 {threshold}"),
                {"module": module, "residual_count": residual_count},
            )

    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("sop_graph.data_sanitization", "script_error", e, {"module": module})
        updates["agent_outputs"]["data-sanitization"] = {
            "residual_count": 0, "cleaned_count": 0,
            "threshold_exceeded": False, "error": str(e)[:200],
        }

    return updates


# ══════════════════════════════════════════════════════════════════════════
#  页面迭代节点
# ══════════════════════════════════════════════════════════════════════════

def page_advance_node(state: SOPState) -> dict:
    """Automation 完成后推进页面索引，支持跨页迭代。
    若 force_retry_phase 已设置 → 当前页面产物缺失，不推进页码。"""
    if state.get("force_retry_phase"):
        return {}  # 重试中 — 不推进页码
    pages = state.get("pages", [])
    idx = state.get("current_page_index", 0)
    next_idx = min(idx + 1, len(pages))
    return {"current_page_index": next_idx}


def _route_after_page_advance(state: SOPState) -> str:
    """页面推进后：有下页→回 test_design_agent 重新走测试设计+自动化，无→继续下一个 Phase。
    若 force_retry_phase 已设置 → 优先送回到重试目标节点。"""
    force_retry = state.get("force_retry_phase")
    if force_retry:
        node_name = PHASE_TO_NODE.get(force_retry)
        if node_name:
            return node_name
    pages = state.get("pages", [])
    idx = state.get("current_page_index", 0)
    if idx < len(pages):
        return "test_design_agent"
    return route_next_phase(state)


# ══════════════════════════════════════════════════════════════════════════
#  条件路由函数
# ══════════════════════════════════════════════════════════════════════════

# Phase → Agent 节点名映射
PHASE_TO_NODE: dict[PhaseName, str] = {
    "Project Init": "project_agent",
    "Requirement": "requirement_agent",
    "Test Design": "test_design_agent",
    "Automation": "automation_agent_pre",   # P1-3 HITL: 入口为 pre，内部经 approval → post
    "Execute & Debug": "execution_agent",
    "Bug Analysis": "bug_analysis_agent",
    "Data Sanitization": "data_sanitization_agent",
    "Report": "report_agent",
    "Knowledge": "knowledge_agent",
}

# 所有可能的 agent 节点名（含 HITL 中断节点 + 清理节点 + 质量门禁）
ALL_AGENT_NODES = list(PHASE_TO_NODE.values()) + [
    "automation_agent_post",
]
# ★ 这些节点有自定义边，不在通用循环中添加条件边
_CUSTOM_EDGE_NODES = {
    "automation_agent_pre",
    "automation_strategy_approval",
    "automation_agent_post",
    "testcase_approval",
    "testcase_quality_gate",
    "test_design_agent",
    "page_advance",
}


def route_next_phase(state: SOPState) -> str:
    """
    条件边函数：根据 completed_phases + skip_phases + 执行结果 决定下一个节点。

    返回下一个要执行的节点名。
    如果全部完成或有 fatal_error，返回 "exit"。

    特殊规则:
      - Bug Analysis: 仅当 execution_failed=True 时才触发
      - 🆕 QA Loop (TLO): Bug Analysis 后用 QALoop 分类决定 auto-fix vs escalate
      - Status 模式: preflight 后直接退出
      - P1-3 HITL: Automation phase 内部分段路由 (pre → approval → post)
      - P1-3 HITL: Test Design 完成后 → testcase_approval (仅 P0 模块)
    """
    # 致命错误 → 直接退出
    if state.get("fatal_error"):
        return "exit"

    # Status 模式 → preflight 后直接退出
    if state.get("mode") == "status":
        return "exit"

    # 质量门禁强制重试：force_retry_phase 不为 None 时优先路由
    force_retry = state.get("force_retry_phase")
    if force_retry:
        node_name = PHASE_TO_NODE.get(force_retry)
        if node_name:
            return node_name

    completed = set(state.get("completed_phases", []))
    skipped = set(state.get("skip_phases", []))

    # 检查执行是否失败（决定是否触发 Bug Analysis）
    # P2-4: 优先检查 AgentResult.execution_failed, 回退到旧格式
    agent_outputs = state.get("agent_outputs", {})
    execution_failed = agent_outputs.get("execution_failed", False)
    if not execution_failed:
        exec_result = agent_outputs.get("execution-agent", {})
        if isinstance(exec_result, dict):
            # P2-4 AgentResult 格式优先
            execution_failed = exec_result.get("execution_failed", False) or not exec_result.get("success", True)

    # 🆕 TLO QA Loop: Bug Analysis 后检查是否应继续修复循环
    if "Bug Analysis" in completed:
        qa_rounds = state.get("qa_loop_rounds", 0)
        qa_max = state.get("qa_loop_max_rounds", 3)
        qa_should_escalate = state.get("qa_should_escalate", False)

        if qa_should_escalate:
            # 不可自动修复 → 跳过后续修复, 直接去 Report
            skipped.add("Bug Analysis")
            state["qa_loop_status"] = "escalated"
            _emit_qa_loop_event(state, "escalated")

        elif qa_rounds < qa_max and execution_failed:
            # 还有重试额度 → 路由到 Automation 修复
            state["qa_loop_rounds"] = qa_rounds + 1
            _emit_qa_loop_event(state, f"retry_round_{qa_rounds + 1}")
            auto_node = PHASE_TO_NODE.get("Automation")
            if auto_node:
                return auto_node
        else:
            # 轮数耗尽 或 无失败 → 结束 QA Loop
            state["qa_loop_status"] = "passed" if not execution_failed else "max_rounds"
            _emit_qa_loop_event(state, state["qa_loop_status"])

    for phase in CANONICAL_PHASES:
        if phase in completed or phase in skipped:
            continue

        # Bug Analysis 条件触发：仅执行失败时运行
        if phase == "Bug Analysis" and not execution_failed:
            continue  # 跳过 — 自动进入下一个 phase (Report)

        # 🆕 TLO QA Loop: 进入 Bug Analysis 前初始化 QA Loop 状态
        if phase == "Bug Analysis":
            if "Bug Analysis" not in state.get("qa_loop_phases_seen", []):
                state["qa_loop_rounds"] = 0
                state["qa_loop_max_rounds"] = state.get("qa_loop_max_rounds", 3)
                state["qa_should_escalate"] = False
                seen = state.get("qa_loop_phases_seen", [])
                seen.append("Bug Analysis")
                state["qa_loop_phases_seen"] = seen

        # P1-3 HITL: Test Design → 先检查 P0 测试用例审批
        if phase == "Automation":
            # 检查是否需要测试用例审批（P0 模块 + 未审批）
            p0_modules = _load_p0_modules()
            if state["module"] in p0_modules and not state.get("test_cases_approved"):
                return "testcase_approval"

        node_name = PHASE_TO_NODE.get(phase)
        if node_name:
            return node_name

    # 所有 phase 处理完毕
    return "exit"


def _emit_qa_loop_event(state: SOPState, action: str):
    """Emit QA Loop lifecycle event to EventBus (JSONL)."""
    try:
        import json
        from datetime import datetime
        from pathlib import Path

        event = {
            "event_type": f"qa_loop.{action}",
            "timestamp": datetime.now().isoformat(),
            "run_id": state.get("run_id", ""),
            "module": state.get("module", ""),
            "agent": "qa-loop",
            "round": state.get("qa_loop_rounds", 0),
            "max_rounds": state.get("qa_loop_max_rounds", 3),
            "status": action,
        }
        events_dir = Path(__file__).resolve().parent.parent.parent / "governance" / ".events"
        events_dir.mkdir(parents=True, exist_ok=True)
        with open(events_dir / "qa_loop.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass  # EventBus failure is non-blocking


# ══════════════════════════════════════════════════════════════════════════
#  图构建
# ══════════════════════════════════════════════════════════════════════════

def build_sop_graph() -> StateGraph:
    """
    构建完整的 SOP 编排图。

    所有 Agent 节点使用 make_agent_loop_node (AgentLoop 作为 Skill 链的唯一执行引擎)。
    execution/report/knowledge 使用 LangGraph 子图。
    bug-analysis 保留 HITL interrupt + 自动循环修复。

    返回:
        未编译的 StateGraph（调用者负责 compile + checkpointer）
    """
    builder = StateGraph(SOPState)

    # ── 添加节点 ──
    builder.add_node("entry", entry_node)
    builder.add_node("preflight", preflight_node)

    # ── P0-1 架构统一: AgentLoop 作为 Skill 链的唯一执行引擎 ──
    # project / requirement / test-design → make_agent_loop_node (完整链)
    builder.add_node("project_agent", make_agent_loop_node("project-agent"))
    builder.add_node("requirement_agent", make_agent_loop_node("requirement-agent"))
    builder.add_node("test_design_agent", make_agent_loop_node("test-design-agent"))

    # P1-3 HITL: automation-agent 拆分为 pre/approval/post 三段
    # pre:  tech-analysis + auto-strategy
    # approval: HITL interrupt（人工审批 AUTO_STRATEGY.md）
    # post: page-object-generator + test-script-generator + code-consistency-checker
    builder.add_node("automation_agent_pre", make_agent_loop_node(
        "automation-agent",
        skill_subset=["automation/tech-analysis", "automation/auto-strategy"],
    ))
    builder.add_node("automation_strategy_approval", automation_strategy_approval_node)
    builder.add_node("automation_agent_post", make_agent_loop_node(
        "automation-agent",
        skill_subset=[
            "automation/page-object-generator",
            "automation/test-script-generator",
            "automation/code-consistency-checker",
        ],
        use_context_agent=True,  # ContextAgent: 只看本页 context，省 70%+ token
    ))

    # P1-3 HITL: P0 模块测试用例审批节点
    builder.add_node("testcase_approval", testcase_approval_node)

    # P2-5: 业务覆盖质量门禁 (L3 Validator)
    builder.add_node("testcase_quality_gate", testcase_quality_gate_node)

    # ★ 页面迭代节点：automation_agent_post 完成后推进 current_page_index
    builder.add_node("page_advance", page_advance_node)

    # execution / report / knowledge → 保留 execution_graph
    from aitest.graphs.execution_graph import (
        build_execution_subgraph,
        build_report_subgraph,
        build_knowledge_subgraph,
    )
    builder.add_node("execution_agent", build_execution_subgraph().compile())
    builder.add_node("report_agent", build_report_subgraph().compile())
    builder.add_node("knowledge_agent", build_knowledge_subgraph().compile())

    # bug-analysis → 保留（HITL interrupt + 自动循环修复，无法用 AgentLoop 替代）
    from aitest.graphs.bug_analysis_graph import build_bug_analysis_compiled
    builder.add_node("bug_analysis_agent", build_bug_analysis_compiled())

    # data-sanitization → 清理节点（离线扫描残留数据，不调用 LLM）
    builder.add_node("data_sanitization_agent", data_sanitization_node)

    builder.add_node("exit", exit_node)

    # ── 添加边 ──
    builder.set_entry_point("entry")
    builder.add_edge("entry", "preflight")

    # 条件路由映射
    all_routable_nodes = list(ALL_AGENT_NODES) + list(_CUSTOM_EDGE_NODES) + ["page_advance"]
    route_map = {name: name for name in all_routable_nodes}
    route_map["exit"] = "exit"

    # preflight → 条件路由
    builder.add_conditional_edges("preflight", route_next_phase, route_map)

    # 每个 Agent 完成后 → 条件路由（跳过有自定义边的节点）
    for node_name in ALL_AGENT_NODES:
        if node_name not in _CUSTOM_EDGE_NODES:
            builder.add_conditional_edges(node_name, route_next_phase, route_map)

    # ── P1-3 HITL: 定制边覆盖（后添加 → 优先）──
    # automation-agent 内部管线: pre → approval → post
    builder.add_edge("automation_agent_pre", "automation_strategy_approval")
    builder.add_conditional_edges(
        "automation_strategy_approval",
        lambda s: "automation_agent_post" if s.get("auto_strategy_approved") else "exit",
        {"automation_agent_post": "automation_agent_post", "exit": "exit"},
    )

    # testcase_approval → automation_agent_pre（审批通过）/ exit（拒绝）
    builder.add_conditional_edges(
        "testcase_approval",
        lambda s: "automation_agent_pre" if s.get("test_cases_approved") else "exit",
        {"automation_agent_pre": "automation_agent_pre", "exit": "exit"},
    )

    # ★ 页面迭代路由: automation_agent_post → page_advance → next page or next phase
    builder.add_edge("automation_agent_post", "page_advance")
    builder.add_conditional_edges(
        "page_advance",
        _route_after_page_advance,
        {**route_map, "automation_agent_pre": "automation_agent_pre"},
    )

    # ── P2-5 业务覆盖质量门禁路由 ──
    # test_design_agent → testcase_quality_gate（优先于通用条件的定制边）
    builder.add_edge("test_design_agent", "testcase_quality_gate")
    # quality_gate → automation_agent_pre（有页面未处理）/ route_next_phase（通过）/ test_design_agent（打回重做）
    def _route_quality_gate(state):
        if not state.get("test_cases_approved") or state.get("force_retry_phase") == "Test Design":
            return "test_design_agent"
        # 如果还有页面未自动化，直接进 automation_agent_pre（跳过 phase 检查）
        pages = state.get("pages", [])
        idx = state.get("current_page_index", 0)
        if idx < len(pages):
            return "automation_agent_pre"
        return route_next_phase(state)
    builder.add_conditional_edges(
        "testcase_quality_gate",
        _route_quality_gate,
        {**route_map, "test_design_agent": "test_design_agent", "automation_agent_pre": "automation_agent_pre"},
    )

    # exit → END
    builder.add_edge("exit", END)

    return builder


def build_compiled_graph(checkpointer=None):
    """
    构建并编译完整的 SOP 图（便捷函数）。

    参数:
        checkpointer: SqliteSaver 实例（默认：创建新的）

    返回:
        编译后的 CompiledGraph
    """
    if checkpointer is None:
        from aitest.graphs.checkpoint import get_checkpointer
        checkpointer = get_checkpointer()

    builder = build_sop_graph()
    return builder.compile(checkpointer=checkpointer)


# ══════════════════════════════════════════════════════════════════════════
#  ★ v2.0: Complexity Routing — 自适应 SOP 流水线
# ══════════════════════════════════════════════════════════════════════════

def resolve_sop_pipeline(module: str, pages: list[str] = None,
                         discovery_data: dict = None) -> dict:
    """根据页面复杂度推荐 SOP 流水线。

    用法:
        result = resolve_sop_pipeline("equipment", ["alarm-config"])
        # → {"tier": "standard", "pipeline": ["requirement-agent", ...], "estimated_tokens": 100000}

    三档:
      - SIMPLE:   2 agent (automation + execution) → ~15K tokens/page
      - STANDARD: 5 agent → ~100K tokens/page
      - COMPLEX:  8 agent (完整) → ~130K tokens/page
    """
    from aitest.platform.complexity import complexity_assess
    from aitest.platform.complexity.factors import ComplexityTier

    pages = pages or []
    result = {"module": module, "pages": {}, "overall_tier": "standard"}

    for page_slug in pages:
        # 尝试读取 discovery 数据
        page_data = {}
        page_dir = get_page_dir(module, page_slug)
        discovery_file = page_dir / ".discovery" / "pages.json" if page_dir else None
        if discovery_file and discovery_file.exists():
            try:
                import json
                with open(discovery_file) as f:
                    all_pages = json.load(f)
                page_data = _find_page_data(all_pages, page_slug)
            except Exception:
                pass

        assessment = complexity_assess(page_data, page_title=page_slug)
        result["pages"][page_slug] = assessment

    # 整体复杂度 = max(各页面复杂度)
    tiers = [p["tier"] for p in result["pages"].values()]
    if "complex" in tiers:
        result["overall_tier"] = "complex"
    elif "standard" in tiers:
        result["overall_tier"] = "standard"
    else:
        result["overall_tier"] = "simple"

    # 汇总 pipeline
    from aitest.platform.complexity.factors import pipeline_for_tier
    all_tiers = set(tiers)
    if len(all_tiers) == 1:
        tier = ComplexityTier(list(all_tiers)[0])
    elif "complex" in all_tiers:
        tier = ComplexityTier.COMPLEX
    elif "standard" in all_tiers:
        tier = ComplexityTier.STANDARD
    else:
        tier = ComplexityTier.SIMPLE

    result["pipeline"] = pipeline_for_tier(tier)
    result["estimated_tokens_per_page"] = {
        "simple": 15000, "standard": 100000, "complex": 130000,
    }[tier.value]

    return result


def _find_page_data(all_pages: list, page_slug: str) -> dict:
    """从 pages.json 中找到指定 page 的数据。"""
    for p in all_pages:
        name = p.get("slug", p.get("name", p.get("title", "")))
        if page_slug in name or name in page_slug:
            return p
    return all_pages[0] if all_pages else {}
