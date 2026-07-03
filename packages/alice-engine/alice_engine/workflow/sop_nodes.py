"""SOP Nodes — node functions for the SOP graph.

Extracted from sop_graph.py for single-responsibility.
"""

import json
import logging
import time
from pathlib import Path

from langgraph.types import interrupt

from alice_engine.workflow.state import (
    SOPState, PhaseName, CANONICAL_PHASES, MODE_SKIP_MAP,
    get_module_dir, get_page_dir, get_test_project_root, get_behavior_pack,
)
from alice_engine.workflow.sop_preflight import _preflight_cache

logger = logging.getLogger(__name__)

WORKSTUDY = Path(".")


def _get_artifacts_dir() -> Path:
    """获取 artifacts 目录 — 通过 behavior pack 解析。"""
    pack = get_behavior_pack()
    if pack and pack.artifacts_dir:
        return pack.artifacts_dir
    return WORKSTUDY / "artifacts"


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
    cache_key = f"{module}:{mode}:{':'.join(sorted(pages))}"
    if mode != "resume":
        cached = _preflight_cache.get(cache_key, module)
        if cached is not None:
            return cached

    completed_phases: list[PhaseName] = []
    artifact_map: dict = {}

    # ── 检查 PROJECT_CONTEXT ──
    project_context = WORKSTUDY / "PROJECT_CONTEXT.md"
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
    artifacts_dir = _get_artifacts_dir()
    status_file = artifacts_dir / f"SOP_STATUS_{module}.json"

    # ★ #5: Resume 时优先从 LangGraph checkpoint 恢复（完整 State，支持时间旅行）
    # JSON 作为 fallback（checkpoint 不可用时）
    checkpoint_loaded = False
    if mode == "resume":
        run_id = state.get("run_id", "")
        if run_id:
            try:
                from alice_engine.runtime.checkpoint import CheckpointManager; get_checkpointer = lambda: CheckpointManager(".").get_checkpointer()
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
            import logging; _log_error = logging.getLogger(__name__).error
            _log_error("sop_graph.preflight", "allure_scan", e, {"module": module})

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
    _preflight_cache.put(cache_key, result, module)

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
    artifacts_dir = _get_artifacts_dir()
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    status_file = artifacts_dir / f"SOP_STATUS_{module}.json"
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
        import logging; _log_error = logging.getLogger(__name__).error
        _log_error("sop_graph.exit", "write_status_json", e, {"module": module, "file": str(status_file)})

    # 发射 CycleEnd 事件
    try:
        emit("CycleEnd", module=module, status=final_status, engine="langgraph")
    except Exception as e:
        import logging; _log_error = logging.getLogger(__name__).error
        _log_error("sop_graph.exit", "emit_cycle_end", e, {"module": module, "status": final_status})

    # P0-2: 在 CycleEnd 后自动运行 State Auditor (全量 S/C/Q/T Check)
    try:
        pass  # StateAuditor removed
        auditor = StateAuditor()
        audit_report = auditor.audit(module, auto_repair=False)
        if audit_report["drift_count"] > 0:
            # 发现漂移 → 发射 StateDrift 事件
            try:
                emit("StateDrift",
                       module=module,
                       run_id=state.get("run_id", ""),
                       drift_count=audit_report["drift_count"],
                       error_count=audit_report["error_count"],
                       warning_count=audit_report["warning_count"],
                       overall_status=audit_report["overall_status"])
            except Exception as e:
                import logging; _log_error = logging.getLogger(__name__).error
                _log_error("sop_graph.exit", "emit_StateDrift", e, {"module": module})
    except Exception as e:
        import logging; _log_error = logging.getLogger(__name__).error
        _log_error("sop_graph.exit", "state_auditor", e, {"module": module})

    # P1-2: SOP Auditor — 全量 6 维检查 (P0-FIX 2026-06-15: 从 3 维扩展到 6 维)
    try:
        pass  # SOPAuditor removed
        sop_auditor = SOPAuditor()
        sop_report = sop_auditor.audit(module, days=1)  # 默认全部 6 维: p/s/g/h/b/l
        if sop_report["total_violations"] > 0:
            try:
                emit("SOPViolation",
                       module=module,
                       run_id=state.get("run_id", ""),
                       violation_type="cycle_end_audit",
                       detail=f"SOP 审计发现 {sop_report['total_violations']} 个违规")
            except Exception as e2:
                import logging; _log_error = logging.getLogger(__name__).error
                _log_error("sop_graph.exit", "emit_SOPViolation", e2, {"module": module})
    except Exception as e:
        import logging; _log_error = logging.getLogger(__name__).error
        _log_error("sop_graph.exit", "sop_auditor", e, {"module": module})

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
    zjsn_test = get_test_project_root()
    scan_script = (zjsn_test / "tools" / "cleanup" / "scan_and_clean.py") if zjsn_test else None

    updates: dict = {
        "agent_outputs": {**state.get("agent_outputs", {})},
        "gate_results": list(state.get("gate_results", [])),
        "completed_phases": ["Data Sanitization"],
    }

    if not scan_script or not scan_script.exists():
        updates["agent_outputs"]["data-sanitization"] = {
            "residual_count": 0, "cleaned_count": 0,
            "threshold_exceeded": False,
            "warning": f"scan_and_clean.py 不存在: {scan_script}",
        }
        return updates

    try:
        # ★ v1.0: 使用 secure_run 替代裸 subprocess.run (安全校验)
        pass  # secure_run removed
        result = secure_run(
            ["python", str(scan_script), "--force"],
            capture_output=True, text=True, timeout=120,
            cwd=str(zjsn_test),
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
            import logging; _log_error = logging.getLogger(__name__).error
            _log_error(
                "sop_graph.data_sanitization", "threshold_exceeded",
                Exception(f"残留数据 {residual_count} 超过阈值 {threshold}"),
                {"module": module, "residual_count": residual_count},
            )

    except Exception as e:
        import logging; _log_error = logging.getLogger(__name__).error
        _log_error("sop_graph.data_sanitization", "script_error", e, {"module": module})
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
    "bug_analysis_agent",       # H5: goes to qa_loop_decision, not route_next_phase
}


