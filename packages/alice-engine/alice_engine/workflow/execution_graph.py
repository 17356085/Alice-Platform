"""
execution + report + knowledge Agent LangGraph SubGraphs。

每个 Agent 使用真正的 Skill 节点（非 AgentLoop 黑盒），
让 LangGraph 对每个 Skill 的执行状态可见。
"""

from pathlib import Path
from typing import Literal
import os

from langgraph.graph import StateGraph, END

from alice_engine.workflow.state import SOPState, GateResult, GateLevel

from alice_engine.workflow.state import get_test_project_root, get_behavior_pack
from pathlib import Path as _Path

WORKSTUDY = _Path(".")


def _default_provider() -> str:
    return os.environ.get("LLM_PROVIDER", os.environ.get("AITEST_PROVIDER", "claude"))


def run_skill(*args, **kwargs):
    from alice_engine.core.skill_executor import run_skill as _run_skill

    return _run_skill(*args, **kwargs)


def process_pending() -> list[dict]:
    """Optional event-queue drain hook.

    The standalone SDK keeps this as a no-op by default. Platform-side event
    processing can be layered back in through explicit adapters later.
    """
    return []


def _get_allure_dir() -> Path:
    """Allure results directory — under test project root, not hardcoded."""
    root = get_test_project_root()
    if root is None:
        return WORKSTUDY / "allure-results"
    return root / "allure-results"


def _get_page(state: dict) -> str:
    pages = state.get("pages", [])
    idx = state.get("current_page_index", 0)
    if pages and idx < len(pages):
        return pages[idx]
    return ""


# ══════════════════════════════════════════════════════════════════════════
#  execution-agent: 运行 pytest（特殊——需要子进程，保留 AgentLoop）
# ══════════════════════════════════════════════════════════════════════════

def exec_entry(state: SOPState) -> dict:
    return {"current_phase": "Execute & Debug"}


def exec_act(state: SOPState) -> dict:
    """运行 pytest 测试。使用 AgentLoop 因为需要管理子进程。"""
    from alice_engine.core.executor import AgentLoop

    page = _get_page(state)
    agent = AgentLoop(
        "execution-agent",
        provider=state.get("provider") or _default_provider(),
        module=state["module"],
        page=page,
        verbose=False,
    )
    result = agent.run()

    observations = []
    for obs in result.observations:
        observations.append(obs.to_dict() if hasattr(obs, 'to_dict') else obs)

    # 检测执行失败
    exec_failed = bool(result.failed_skills and len(result.failed_skills) > 0)

    return {
        "agent_outputs": {
            **state.get("agent_outputs", {}),
            "execution-agent": result.to_dict(),
            "execution_failed": exec_failed,
        },
        "skill_observations": observations,
        "completed_skills": [s for s in result.completed_skills],
    }


def exec_gate(state: SOPState) -> dict:
    module = state["module"]
    zjsn = get_test_project_root()
    allure_dir = zjsn / "allure-results" if zjsn else Path("allure-results")
    ok = allure_dir.exists() and any(allure_dir.iterdir())
    return {"gate_results": [GateResult(
        level=GateLevel.L2_AGENT, phase="Execute & Debug", ok=ok,
        message=f"Execution gate: {'PASS' if ok else 'WARN'}",
        details={"allure_dir": str(allure_dir)},
    ).to_dict()]}


def exec_exit(state: SOPState) -> dict:
    return {"completed_phases": ["Execute & Debug"]}


def build_execution_subgraph() -> StateGraph:
    builder = StateGraph(SOPState)
    builder.add_node("entry", exec_entry)
    builder.add_node("act", exec_act)
    builder.add_node("gate", exec_gate)
    builder.add_node("exit", exec_exit)
    builder.set_entry_point("entry")
    builder.add_edge("entry", "act")
    builder.add_edge("act", "gate")
    builder.add_edge("gate", "exit")
    builder.add_edge("exit", END)
    return builder


# ══════════════════════════════════════════════════════════════════════════
#  report-agent: 1-2 skills → 轻量 Skill 节点
# ══════════════════════════════════════════════════════════════════════════

REPORT_SKILLS = ["reporting/report-generator", "reporting/excel-exporter"]


def _single_skill_act(state: dict, skill_id: str) -> dict:
    """单 Skill 执行（无循环，report 和 knowledge 各 1-2 个 skill）。"""
    module = state["module"]
    page = _get_page(state)
    provider = state.get("provider") or _default_provider()

    response = run_skill(
        skill_id=skill_id,
        user_input=f"Module: {module}, Page: {page}",
        provider=provider,
        context_vars={"module": module, "page": page},
    )

    return {
        "current_skill": skill_id,
        "agent_outputs": {
            **state.get("agent_outputs", {}),
            f"skill_{skill_id.replace('/', '_')}": {
                "content_preview": response.content[:500] if response.content else "",
                "token_usage": getattr(response, "usage", getattr(response, "token_usage", {})),
                "finish_reason": response.finish_reason,
            },
        },
        "completed_skills": [skill_id],
    }


def report_entry(state: SOPState) -> dict:
    return {"current_phase": "Report"}


def report_act(state: SOPState) -> dict:
    return _single_skill_act(state, "reporting/report-generator")


def report_act2(state: SOPState) -> dict:
    """可选的 Excel 导出。"""
    return _single_skill_act(state, "reporting/excel-exporter")


def report_exit(state: SOPState) -> dict:
    return {"completed_phases": ["Report"]}


def build_report_subgraph() -> StateGraph:
    builder = StateGraph(SOPState)
    builder.add_node("entry", report_entry)
    builder.add_node("act", report_act)
    builder.add_node("exit", report_exit)
    builder.set_entry_point("entry")
    builder.add_edge("entry", "act")
    builder.add_edge("act", "exit")
    builder.add_edge("exit", END)
    return builder


# ══════════════════════════════════════════════════════════════════════════
#  knowledge-agent: 1 skill + 事件总线处理
# ══════════════════════════════════════════════════════════════════════════

def knowledge_entry(state: SOPState) -> dict:
    return {"current_phase": "Knowledge"}


def knowledge_act(state: SOPState) -> dict:
    """知识沉淀 + 事件总线处理 + RAG 增量索引。"""
    result = _single_skill_act(state, "knowledge/knowledge-manager")

    # 处理事件总线积压
    try:
        processed = process_pending()
        result["agent_outputs"]["events_processed"] = len(processed)
    except Exception as e:
        import logging

        logging.getLogger(__name__).warning(
            "knowledge event processing skipped for module %s: %s",
            state["module"],
            e,
        )
        result["agent_outputs"]["events_processed"] = 0

    # P2-8: RAG 索引增量更新 — 仅变更时重建，避免每次全量重索引
    # RAG 索引同步 — 使用 SDK KnowledgeStore 接口
    # 如果 Engine 注入了 KnowledgeStore，在 cycle_end 时自动 ingest
    module = state["module"]

    return result


def knowledge_exit(state: SOPState) -> dict:
    """知识沉淀完成后清理旧数据、生成 Allure HTML 报告。"""
    result = {"completed_phases": ["Knowledge"]}

    try:
        import json
        from pathlib import Path

        output_dir = _get_allure_dir()
        output_dir.mkdir(parents=True, exist_ok=True)

        # 清理旧 JSON / 临时文件（保留最新 7 天）
        import time
        now = time.time()
        cutoff = now - (7 * 86400)  # 7 天前
        cleaned = 0
        from itertools import chain
        for f in chain(output_dir.glob("*-result.json"), output_dir.glob("*-container.json"), output_dir.glob("*-attachment.txt")):
            if f.stat().st_mtime < cutoff:
                f.unlink()
                cleaned += 1

        # 收集最新结果统计
        results = []
        for f in sorted(output_dir.glob("*-result.json"), key=lambda p: -p.stat().st_mtime)[:100]:
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
                results.append(data)
            except Exception:
                pass  # best-effort: skip malformed JSON files

        # 生成 HTML 报告
        total = len(results)
        passed = sum(1 for r in results if r.get("status") == "passed")
        failed = sum(1 for r in results if r.get("status") == "failed")
        skipped = sum(1 for r in results if r.get("status") == "skipped")

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Allure Test Report - Warehouse</title>
    <style>
        body {{ font-family: Arial; margin: 20px; background: #f9f9f9; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }}
        .stat {{ background: white; padding: 15px; border-radius: 5px; text-align: center; border-left: 4px solid #ccc; }}
        .stat.pass {{ border-left-color: #4CAF50; }}
        .stat.fail {{ border-left-color: #f44336; }}
        .stat.skip {{ border-left-color: #ff9800; }}
        .stat.total {{ border-left-color: #2196F3; }}
        .stat-value {{ font-size: 24px; font-weight: bold; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        table {{ border-collapse: collapse; width: 100%; background: white; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background: #2c3e50; color: white; }}
        .pass {{ color: #4CAF50; }}
        .fail {{ color: #f44336; }}
        .skip {{ color: #ff9800; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Warehouse Module - Test Report</h1>
        <p>Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    <div class="summary">
        <div class="stat total">
            <div class="stat-value">{total}</div>
            <div class="stat-label">Total Cases</div>
        </div>
        <div class="stat pass">
            <div class="stat-value">{passed}</div>
            <div class="stat-label">Passed</div>
        </div>
        <div class="stat fail">
            <div class="stat-value">{failed}</div>
            <div class="stat-label">Failed</div>
        </div>
        <div class="stat skip">
            <div class="stat-value">{skipped}</div>
            <div class="stat-label">Skipped</div>
        </div>
    </div>
    <table>
        <tr><th>Test Name</th><th>Status</th><th>Duration (s)</th></tr>
"""
        for r in results[:50]:
            name = r.get("name", "N/A")
            status = r.get("status", "unknown")
            duration = f"{r.get('duration', 0)/1000:.2f}" if r.get("duration") else "N/A"
            html += f'<tr><td>{name}</td><td><span class="{status}">{status}</span></td><td>{duration}</td></tr>'

        html += """
    </table>
</body>
</html>
"""
        out_html = output_dir / "html" / "index.html"
        out_html.parent.mkdir(parents=True, exist_ok=True)
        out_html.write_text(html, encoding='utf-8')
        result["allure_html_generated"] = str(out_html)
        result["allure_cleanup_count"] = cleaned
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("knowledge_exit_error", extra={"error": str(e)})

    return result


def build_knowledge_subgraph() -> StateGraph:
    builder = StateGraph(SOPState)
    builder.add_node("entry", knowledge_entry)
    builder.add_node("act", knowledge_act)
    builder.add_node("exit", knowledge_exit)
    builder.set_entry_point("entry")
    builder.add_edge("entry", "act")
    builder.add_edge("act", "exit")
    builder.add_edge("exit", END)
    return builder
