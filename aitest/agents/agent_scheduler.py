"""
Agent Scheduler — 前置条件检测 + 自动触发

功能:
  1. 检测模块当前 SOP Phase
  2. 判断下一步应触发哪个 Agent
  3. 自动/手动模式切换
  4. 模块状态机管理

状态机:
  [未纳管] → Project Agent → [已索引]
  [已索引] → Requirement Agent → [已建模]
  [已建模] → Test Design Agent → [已设计]
  [已设计] → Automation Agent → [已自动化]
  [已自动化] → Execution Agent → [执行中]
  [执行中] → Report / Bug Analysis → [已闭环/待修复]

用法:
  python -m aitest.agents.agent_scheduler check --module=tank        # 检查前置条件
  python -m aitest.agents.agent_scheduler next --module=tank         # 推荐下一步 Agent
  python -m aitest.agents.agent_scheduler auto --module=tank         # 自动推进到下一步
"""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from governance.validators.sop_validator import (
    validate_module_context,
    validate_page_bundle,
    validate_sop_state,
)

# ── 路径配置 ──────────────────────────────────────────────────────────
from aitest.platform.paths import get_workstudy, get_test_project_root, get_context_modules, get_governance_dir
WORKSTUDY = get_workstudy()
GOVERNANCE = get_governance_dir()
CONTEXT_MODULES = get_context_modules()

# ── Agent 前置条件定义 ────────────────────────────────────────────────

@dataclass
class AgentTrigger:
    """Agent 触发条件定义。"""
    agent: str
    phase: str
    preconditions: dict[str, str]  # key=文件路径模式, value=检查方式(exists/not_exists/non_empty)
    postconditions: dict[str, str]  # 完成后应存在的文件
    next_agent_on_success: str = ""
    next_agent_on_failure: str = ""
    can_skip: bool = False  # 是否可跳过


# 前置条件定义（路径相对于模块目录）
AGENT_TRIGGERS: list[AgentTrigger] = [
    AgentTrigger(
        agent="project-agent",
        phase="Phase 0",
        preconditions={"../MODULE_INDEX.md": "non_empty"},
        postconditions={"../MODULE_INDEX.md": "non_empty"},
        next_agent_on_success="requirement-agent",
        can_skip=True,
    ),
    AgentTrigger(
        agent="requirement-agent",
        phase="Phase 0.5~0.8",
        preconditions={"MODULE_CONTEXT.md": "not_exists"},
        postconditions={"MODULE_CONTEXT.md": "non_empty"},
        next_agent_on_success="test-design-agent",
        can_skip=False,
    ),
    AgentTrigger(
        agent="test-design-agent",
        phase="Phase 1~2.5",
        preconditions={"MODULE_CONTEXT.md": "non_empty"},
        postconditions={
            "pages/*/PAGE_CONTEXT.md": "all_non_empty",
            "pages/*/TEST_CASES.md": "all_non_empty",
        },
        next_agent_on_success="automation-agent",
        can_skip=False,
    ),
    AgentTrigger(
        agent="automation-agent",
        phase="Phase 3~4",
        preconditions={
            "pages/*/TEST_CASES.md": "all_non_empty",
        },
        postconditions={
            "pages/*/TECH_ANALYSIS.md": "all_non_empty",
            "pages/*/AUTO_STRATEGY.md": "all_non_empty",
        },
        next_agent_on_success="execution-agent",
        can_skip=False,
    ),
    AgentTrigger(
        agent="execution-agent",
        phase="Phase 4.5~7",
        preconditions={
            "pages/*/AUTO_STRATEGY.md": "all_non_empty",
        },
        postconditions={},
        next_agent_on_success="report-agent",
        next_agent_on_failure="bug-analysis-agent",
        can_skip=False,
    ),
    AgentTrigger(
        agent="report-agent",
        phase="Phase 8~9",
        preconditions={},
        postconditions={},
        next_agent_on_success="knowledge-agent",
    ),
    AgentTrigger(
        agent="bug-analysis-agent",
        phase="Phase 4.5~6",
        preconditions={},
        postconditions={},
        next_agent_on_success="knowledge-agent",
    ),
    AgentTrigger(
        agent="knowledge-agent",
        phase="Phase 9 (事件驱动)",
        preconditions={},
        postconditions={},
    ),
]


# ══════════════════════════════════════════════════════════════════════════
#  前置条件检测
# ══════════════════════════════════════════════════════════════════════════

def _resolve_path(module_dir: Path, pattern: str) -> list[Path]:
    """解析路径模式（支持 * 通配符和 ../ 相对路径）。"""
    if "/" in pattern:
        pattern = pattern.replace("/", os.sep)
    if pattern.startswith(".."):
        return [module_dir.parent / pattern[3:]]
    return list(module_dir.glob(pattern))


def check_preconditions(module_name: str, agent: str = None) -> dict:
    """检查模块的前置条件满足情况。

    返回: {
        "module": str,
        "current_agent": str (当前应触发的 Agent),
        "agents": [{"agent": str, "preconditions_met": bool, "details": [...]}]
    }
    """
    module_dir = CONTEXT_MODULES / module_name
    agents_status = []
    current_agent = None
    sop_state = validate_sop_state(module_name)
    module_context_check = validate_module_context(module_name)
    page_bundle_basic = validate_page_bundle(module_name)
    page_bundle_tech = validate_page_bundle(module_name, require_tech=True)

    for trigger in AGENT_TRIGGERS:
        if agent and trigger.agent != agent:
            continue

        details = []
        all_met = True

        for pattern, check_type in trigger.preconditions.items():
            paths = _resolve_path(module_dir, pattern)
            met = False

            if check_type == "exists":
                met = any(p.exists() for p in paths)
            elif check_type == "not_exists":
                met = not any(p.exists() for p in paths)
            elif check_type == "non_empty":
                met = any(p.exists() and p.stat().st_size > 0 for p in paths)
            elif check_type == "all_exists":
                met = bool(paths) and all(p.exists() for p in paths)
            elif check_type == "all_non_empty":
                met = bool(paths) and all(p.exists() and p.stat().st_size > 0 for p in paths)

            details.append({
                "pattern": pattern,
                "check": check_type,
                "met": met,
                "matched_files": [str(p) for p in paths if p.exists()],
            })

            if not met:
                all_met = False

        # 检查 postconditions — 如果 postconditions 都满足，跳过此 agent
        post_all_met = True
        if trigger.postconditions:
            for pattern, check_type in trigger.postconditions.items():
                paths = _resolve_path(module_dir, pattern)
                if check_type == "exists":
                    met = any(p.exists() for p in paths)
                elif check_type == "not_exists":
                    met = not any(p.exists() for p in paths)
                elif check_type == "non_empty":
                    met = any(p.exists() and p.stat().st_size > 0 for p in paths)
                elif check_type == "all_exists":
                    met = bool(paths) and all(p.exists() for p in paths)
                elif check_type == "all_non_empty":
                    met = bool(paths) and all(p.exists() and p.stat().st_size > 0 for p in paths)
                else:
                    met = any(p.exists() for p in paths)

                if not met:
                    post_all_met = False
                    break

        agent_status = {
            "agent": trigger.agent,
            "phase": trigger.phase,
            "preconditions_met": all_met,
            "postconditions_met": post_all_met,
            "already_done": post_all_met,
            "can_skip": trigger.can_skip,
            "details": details,
        }

        if trigger.agent == "requirement-agent":
            agent_status["validator"] = module_context_check.__dict__
            if not module_context_check.ok:
                agent_status["preconditions_met"] = False
                agent_status["postconditions_met"] = False
                agent_status["already_done"] = False

        if trigger.agent == "test-design-agent":
            agent_status["validator"] = page_bundle_basic.__dict__
            if not page_bundle_basic.ok:
                agent_status["preconditions_met"] = False
                agent_status["postconditions_met"] = False
                agent_status["already_done"] = False

        if trigger.agent == "automation-agent":
            agent_status["validator"] = page_bundle_tech.__dict__
            if not page_bundle_tech.ok:
                agent_status["preconditions_met"] = False
                agent_status["postconditions_met"] = False
                agent_status["already_done"] = False

        if trigger.agent == "execution-agent":
            agent_status["validator"] = sop_state.__dict__
            if not sop_state.ok:
                agent_status["preconditions_met"] = False
                agent_status["postconditions_met"] = False
                agent_status["already_done"] = False
        agents_status.append(agent_status)

        # 第一个未完成的 Agent 为 current
        if not post_all_met and current_agent is None:
            current_agent = trigger.agent

    return {
        "module": module_name,
        "current_agent": current_agent or "knowledge-agent",
        "validators": {
            "sop_state": sop_state.__dict__,
            "module_context": module_context_check.__dict__,
            "page_bundle_basic": page_bundle_basic.__dict__,
            "page_bundle_tech": page_bundle_tech.__dict__,
        },
        "agents": agents_status,
    }


def recommend_next_agent(module_name: str) -> dict:
    """推荐下一步应触发的 Agent。

    返回: {"agent": str, "reason": str, "skippable": bool, "suggested_skill": str}
    """
    status = check_preconditions(module_name)

    for agent_info in status["agents"]:
        if not agent_info["already_done"]:
            if agent_info["preconditions_met"]:
                return {
                    "agent": agent_info["agent"],
                    "phase": agent_info["phase"],
                    "reason": f"前置条件已满足，可以启动",
                    "skippable": agent_info["can_skip"],
                }
            else:
                # 找到阻止的原因
                blockers = [d for d in agent_info["details"] if not d["met"]]
                return {
                    "agent": agent_info["agent"],
                    "phase": agent_info["phase"],
                    "reason": f"前置条件不满足 ({len(blockers)} 项未通过)",
                    "blockers": blockers,
                }

    # 所有 Agent 已完成
    return {
        "agent": "knowledge-agent",
        "phase": "Phase 9",
        "reason": "所有前置阶段已完成，建议沉淀知识或结束周期",
    }


def auto_advance(module_name: str, auto_trigger: bool = False) -> dict:
    """自动推进模块到下一 Agent。

    返回: {"action": "trigger"|"blocked"|"complete", "agent": str, ...}
    """
    status = check_preconditions(module_name)
    recommendation = recommend_next_agent(module_name)

    if all(a["already_done"] for a in status["agents"]):
        # B-4: Emit CycleEnd event when all phases complete
        try:
            from aitest.governance.event_bus import emit
            emit("CycleEnd", module=module_name, stats="all_phases_complete")
        except Exception as e:
            from aitest.infra.error_logger import log_error
            log_error("agent_scheduler.auto_advance", "emit_cycle_end", e, {"module": module_name})

        return {
            "action": "complete",
            "module": module_name,
            "message": f"模块 {module_name} 已完成所有 SOP Phase",
            "recommendation": "运行知识沉淀或进入下一个模块",
        }

    if not recommendation.get("blockers"):
        agent = recommendation["agent"]
        # 检查是否可自动触发
        trigger = next((t for t in AGENT_TRIGGERS if t.agent == agent), None)

        if auto_trigger and trigger and trigger.can_skip:
            return {
                "action": "skip",
                "agent": agent,
                "reason": f"{agent} 标记为可跳过，自动跳转到下一 Agent",
            }

        return {
            "action": "trigger",
            "agent": agent,
            "phase": recommendation["phase"],
            "reason": recommendation["reason"],
            "suggested_command": f"/{agent.replace('-agent', '-agent')}",
        }

    return {
        "action": "blocked",
        "agent": recommendation["agent"],
        "reason": recommendation["reason"],
        "blockers": recommendation.get("blockers", []),
        "validators": status.get("validators", {}),
    }


# ══════════════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python agent_scheduler.py check|next|auto [--module=<name>]")
        print("\nAvailable modules:")
        if CONTEXT_MODULES.exists():
            for mod_dir in sorted(CONTEXT_MODULES.iterdir()):
                if mod_dir.is_dir():
                    mc = "✅" if (mod_dir / "MODULE_CONTEXT.md").exists() else "❌"
                    print(f"  {mc} {mod_dir.name}")
        sys.exit(0)

    cmd = sys.argv[1]
    module = "tank"
    auto = False
    for arg in sys.argv[2:]:
        if arg.startswith("--module="):
            module = arg.split("=", 1)[1]
        elif arg == "--auto":
            auto = True

    if cmd == "check":
        result = check_preconditions(module)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif cmd == "next":
        result = recommend_next_agent(module)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif cmd == "auto":
        result = auto_advance(module, auto_trigger=auto)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:
        print(f"Unknown command: {cmd}")
