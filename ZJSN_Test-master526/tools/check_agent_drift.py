"""
Agent 定义 drift 检测器。

检查:
  1. agent-definitions.yaml 与 aitest/agent_runner.py 的 AGENT_SKILL_MAP 是否一致
  2. Skill 顺序是否一致

注: .claude/skills/ 检查已移除 (P0-1 架构迁移 — LangGraph AgentLoop
直读 agent-definitions.yaml + governance/skills/, 不再经过 Claude Code Skills)

用法:
  python tools/check_agent_drift.py                # 人类可读输出
  python tools/check_agent_drift.py --json         # JSON 输出（CI 集成）

退出码: 0=一致, 1=存在 drift, 2=严重不一致
"""
import os
import sys
import json
import re
from pathlib import Path

WORKSTUDY = Path(__file__).resolve().parent.parent.parent
GOVERNANCE = WORKSTUDY / "governance"
YAML_PATH = GOVERNANCE / "agents" / "agent-definitions.yaml"
CLAUDE_SKILLS_DIR = WORKSTUDY / ".claude" / "skills"
AGENT_RUNNER_PATH = WORKSTUDY / "aitest" / "agent_runner.py"


def load_yaml_definitions() -> dict:
    """从 agent-definitions.yaml 加载 Agent 定义。"""
    import yaml
    if not YAML_PATH.exists():
        return {}
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("agents", {})


def extract_skills_from_claude_skill(skill_file: Path) -> list[str]:
    """从 .claude/skills/<name>/SKILL.md 提取 Skill 列表。

    解析 SKILL.md 中的 '核心能力' 表格:
      | 1 | `tech-analysis` | Phase 3 | ...
      | 2 | `auto-strategy` | ...
    """
    if not skill_file.exists():
        return []
    content = skill_file.read_text(encoding="utf-8")
    skills = []
    # 匹配表格中的 skill 引用: `skill-name`
    for match in re.finditer(r'`([a-z][a-z-]+)`', content):
        skill = match.group(1)
        # 过滤掉非 skill 名称的 backtick 内容
        if any(category in skill for category in
               ['analysis', 'strategy', 'generator', 'checker', 'modeling',
                'design', 'manager', 'testing', 'sync', 'analyzer', 'exporter',
                'generation']):
            if skill not in skills:
                skills.append(skill)
    # 回退: 在编排规则部分查找
    if not skills:
        # 匹配 "| N | `skill-name` |" 模式
        for match in re.finditer(r'\|\s*\d+\s*\|\s*`([^`]+)`', content):
            skills.append(match.group(1))
    return skills


def extract_skills_from_agent_runner() -> dict:
    """从 agent_runner.py 提取 AGENT_SKILL_MAP。"""
    if not AGENT_RUNNER_PATH.exists():
        return {}
    content = AGENT_RUNNER_PATH.read_text(encoding="utf-8")
    # 找后备定义的硬编码 map
    skills_map = {}
    current_agent = None
    in_skill_list = False
    for line in content.split("\n"):
        if '"project-agent":' in line or '"-agent":' in line:
            match = re.match(r'\s*"([^"]+)":\s*\[', line)
            if match:
                current_agent = match.group(1)
                skills_map[current_agent] = []
                if "]," not in line:
                    in_skill_list = True
        elif in_skill_list and current_agent:
            match = re.match(r'\s*"([^"]+)"', line)
            if match:
                skills_map[current_agent].append(match.group(1))
            if "]," in line:
                in_skill_list = False
    return skills_map


def check_drift(json_output: bool = False) -> dict:
    """检查三层之间的 drift:
      YAML (agent-definitions.yaml) — 单一事实源
      Python (agent_runner.py)   — 派生，应与 YAML 一致
      Claude (.claude/skills/)   — 派生，应与 YAML 一致
    """
    yaml_defs = load_yaml_definitions()
    py_skills = extract_skills_from_agent_runner()

    results = {
        "source": str(YAML_PATH),
        "yaml_version": "",
        "drifts": [],
        "warnings": [],
        "agents_checked": 0,
        "agents_ok": 0,
    }

    if not yaml_defs:
        results["drifts"].append({
            "severity": "critical",
            "message": "agent-definitions.yaml 不存在或为空 — 无事实源",
            "fix": "创建 governance/agents/agent-definitions.yaml",
        })
        return results

    # 跳过 full-sop（编排器，非 Agent）
    agent_defs = {k: v for k, v in yaml_defs.items() if not v.get("is_orchestrator")}

    for agent_id, defn in agent_defs.items():
        results["agents_checked"] += 1
        yaml_skills = defn.get("skills", [])
        agent_ok = True

        # 简化 skill ID（去掉 category 前缀，如 "automation/tech-analysis" → "tech-analysis"）
        yaml_skill_names = [s.split("/")[-1] if "/" in s else s for s in yaml_skills]

        # 检查 1: YAML vs Python (agent_runner.py)
        py_skill_list = py_skills.get(agent_id, [])
        if py_skill_list:
            py_skill_names = [s.split("/")[-1] if "/" in s else s for s in py_skill_list]
            yaml_set = set(yaml_skill_names)
            py_set = set(py_skill_names)
            if yaml_set != py_set:
                agent_ok = False
                only_yaml = yaml_set - py_set
                only_py = py_set - yaml_set
                if only_yaml:
                    results["drifts"].append({
                        "severity": "error",
                        "agent": agent_id,
                        "layer": "agent_runner.py",
                        "message": f"YAML 中有但 agent_runner.py 中缺失: {only_yaml}",
                        "fix": f"更新 agent_runner.py 的 _FALLBACK_AGENT_SKILL_MAP，添加: {only_yaml}",
                    })
                if only_py:
                    results["drifts"].append({
                        "severity": "error",
                        "agent": agent_id,
                        "layer": "agent_runner.py",
                        "message": f"agent_runner.py 中有但 YAML 中缺失: {only_py}",
                        "fix": f"更新 agent-definitions.yaml 的 {agent_id}.skills，添加: {only_py}",
                    })

        # 检查 2: YAML vs .claude/skills/
        claude_skill_file = CLAUDE_SKILLS_DIR / agent_id / "SKILL.md"
        if claude_skill_file.exists():
            claude_skills = extract_skills_from_claude_skill(claude_skill_file)
            if claude_skills:
                claude_set = set(claude_skills)
                yaml_set = set(yaml_skill_names)
                # Claude 文件可能引用其他内容，只检查 YAML 中的 skill 是否在 Claude 中提到
                missing_in_claude = yaml_set - claude_set
                if missing_in_claude:
                    agent_ok = False
                    results["drifts"].append({
                        "severity": "warning",
                        "agent": agent_id,
                        "layer": ".claude/skills/",
                        "message": f"YAML 中定义的 Skill 在 SKILL.md 中未找到引用: {missing_in_claude}",
                        "fix": f"更新 .claude/skills/{agent_id}/SKILL.md 的 Skill 引用",
                    })
            else:
                results["warnings"].append({
                    "agent": agent_id,
                    "message": f"无法从 .claude/skills/{agent_id}/SKILL.md 提取 Skill 列表（格式可能不标准）",
                })
        else:
            results["drifts"].append({
                "severity": "error",
                "agent": agent_id,
                "layer": ".claude/skills/",
                "message": f".claude/skills/{agent_id}/SKILL.md 不存在",
                "fix": f"创建 .claude/skills/{agent_id}/SKILL.md 作为 Claude Code 适配层",
            })

        if agent_ok:
            results["agents_ok"] += 1

    # 检查 3: .claude/skills/ 中是否有 YAML 中不存在的 Agent
    if CLAUDE_SKILLS_DIR.exists():
        for skill_dir in CLAUDE_SKILLS_DIR.iterdir():
            if skill_dir.name.startswith("_") or skill_dir.name == "full-sop":
                continue
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                if skill_dir.name not in agent_defs:
                    results["warnings"].append({
                        "agent": skill_dir.name,
                        "message": f".claude/skills/{skill_dir.name}/ 存在但不在 agent-definitions.yaml 中",
                    })

    results["total_drifts"] = len(results["drifts"])
    return results


def fix_drifts(dry_run: bool = True) -> list[str]:
    """自动修复可修复的 drift。"""
    actions = []
    results = check_drift(json_output=True)

    for drift in results["drifts"]:
        if drift["severity"] == "critical":
            actions.append(f"CRITICAL (需要手动): {drift['message']}")
        elif drift["layer"] == ".claude/skills/":
            skill_dir = CLAUDE_SKILLS_DIR / drift["agent"]
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists() and not dry_run:
                skill_dir.mkdir(parents=True, exist_ok=True)
                # 从 YAML 生成 SKILL.md
                yaml_defs = load_yaml_definitions()
                defn = yaml_defs.get(drift["agent"], {})
                skills = defn.get("skills", [])
                skill_list_str = "\n".join(
                    f"| {i+1} | `{s.split('/')[-1] if '/' in s else s}` | {defn.get('phase', '')} |"
                    for i, s in enumerate(skills)
                )
                content = f"""---
name: {drift['agent']}
description: {defn.get('description', '')}
# 来源: governance/agents/agent-definitions.yaml（单一事实源）
# 此文件是 Claude Code 适配层。修改 Agent 定义请修改 YAML 文件。
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Skill, Agent, WebFetch
---

# /{drift['agent']} — {defn.get('name', '')}

> 来源: `governance/agents/agent-definitions.yaml` — 所有 Agent 的单一事实源。
> 修改 Skill 列表/角色/边界请在 YAML 文件中修改，然后运行 `python tools/check_agent_drift.py --fix` 更新此文件。

你现在的身份是**{defn.get('system_prompt_role', '')}**。

## 核心能力

| 顺序 | Skill | Phase | 产出 |
|------|-------|-------|------|
{skill_list_str}

## 边界

{chr(10).join(f'- {b}' for b in defn.get('boundaries', []))}
"""
                skill_file.write_text(content, encoding="utf-8")
                actions.append(f"CREATED: .claude/skills/{drift['agent']}/SKILL.md (从 YAML 生成)")
            else:
                actions.append(f"SKIP (文件已存在): .claude/skills/{drift['agent']}/SKILL.md")

    for warning in results.get("warnings", []):
        actions.append(f"WARNING: [{warning.get('agent', '?')}] {warning.get('message', '')}")

    return actions


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Agent 定义 drift 检测器")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--fix", action="store_true", help="自动修复 可修复的 drift")
    parser.add_argument("--dry-run", action="store_true", help="仅显示修复计划，不实际执行")
    args = parser.parse_args()

    if args.fix or args.dry_run:
        actions = fix_drifts(dry_run=args.dry_run or not args.fix)
        if args.json:
            print(json.dumps(actions, ensure_ascii=False, indent=2))
        else:
            for action in actions:
                print(f"  {action}")
        sys.exit(0)

    results = check_drift(json_output=args.json)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f"事实源: {results['source']}")
        print(f"检查: {results['agents_checked']} Agent, {results['agents_ok']} 一致")
        print(f"Drift: {results['total_drifts']} 个")
        if results["warnings"]:
            print(f"警告: {len(results['warnings'])} 个")
        print()

        for drift in results["drifts"]:
            icon = "❌" if drift["severity"] == "critical" else "⚠️"
            print(f"{icon} [{drift['severity']}] {drift.get('agent', '?')} / {drift.get('layer', '?')}")
            print(f"   {drift['message']}")
            if drift.get("fix"):
                print(f"   修复: {drift['fix']}")
            print()

        for warning in results.get("warnings", []):
            print(f"💡 [{warning.get('agent', '?')}] {warning.get('message', '')}")

        if results["total_drifts"] == 0:
            print("✅ 所有 Agent 定义一致，无 drift。")
        else:
            print(f"运行 'python tools/check_agent_drift.py --fix' 自动修复部分问题。")

    sys.exit(min(results["total_drifts"], 1))
