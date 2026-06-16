"""
automation-agent LangGraph SubGraph。

每个页面执行 6 个 Skill 节点链:
  tech-analysis → auto-strategy → page-object-generator → test-script-generator
  → conftest-generator → code-consistency-checker (mechanical)

对内包含 Perceive→Plan→Act→Observe 循环。
"""

import re
from pathlib import Path
from typing import Literal

from langgraph.graph import StateGraph, END

from aitest.graphs.state import (
    SOPState,
    GateResult,
    GateLevel,
    SkillObservation,
)

WORKSTUDY = Path(__file__).resolve().parent.parent.parent
ZJSN_TEST = WORKSTUDY / "ZJSN_Test-master526"
GOVERNANCE = WORKSTUDY / "governance"
CONTEXT_MODULES = GOVERNANCE / "context" / "projects" / "web-automation" / "modules"

# automation-agent 的 Skill 链
AUTOMATION_SKILLS = [
    "automation/tech-analysis",
    "automation/auto-strategy",
    "automation/page-object-generator",
    "automation/test-script-generator",
    "automation/conftest-generator",
    "automation/code-consistency-checker",
]

# Skill → 产出文件映射
SKILL_OUTPUT_MAP = {
    "automation/tech-analysis": "{module_dir}/pages/{page}/TECH_ANALYSIS.md",
    "automation/auto-strategy": "{module_dir}/pages/{page}/AUTO_STRATEGY.md",
    "automation/page-object-generator": "ZJSN_Test-master526/page/{module}_page/{PageName}Page.py",
    "automation/test-script-generator": "ZJSN_Test-master526/script/{module}/test_{page_underscore}.py",
    "automation/conftest-generator": "ZJSN_Test-master526/script/{module}/conftest.py",
}

# 8 条代码红线（用于 observe + mechanical check）
CODE_REDLINE_CHECKS = [
    ("继承 BasePage", r"class \w+\(BasePage\):", True),
    ("绝对 XPath", r"//\*\[@id=", False),
    ("time.sleep 硬等待", r"time\.sleep\(", False),
    ("print 调试", r"^[^#]*\bprint\(", False),
    ("手动 URL 硬编码", r'get\("https?://', False),
]


# ══════════════════════════════════════════════════════════════════════════
#  Helper
# ══════════════════════════════════════════════════════════════════════════

def _get_current_page(state: dict) -> str:
    """从 state 获取当前处理的 page slug。"""
    pages = state.get("pages", [])
    idx = state.get("current_page_index", 0)
    if pages and idx < len(pages):
        return pages[idx]
    return ""


def _slug_to_page_name(slug: str) -> str:
    """alarm-config → AlarmConfig"""
    return "".join(part.capitalize() for part in slug.replace("-", " ").split())


def _slug_to_underscore(slug: str) -> str:
    """alarm-config → alarm_config"""
    return slug.replace("-", "_")


def _resolve_path(pattern: str, module: str, page: str) -> Path:
    """将带有变量的路径模式解析为绝对路径。"""
    resolved = pattern
    resolved = resolved.replace("{module_dir}", str(CONTEXT_MODULES / module))
    resolved = resolved.replace("{module}", module)
    resolved = resolved.replace("{page}", page)
    resolved = resolved.replace("{PageName}", _slug_to_page_name(page))
    resolved = resolved.replace("{page_underscore}", _slug_to_underscore(page))
    if resolved.startswith("ZJSN_Test-master526"):
        resolved = str(WORKSTUDY / resolved)
    return Path(resolved)


# ══════════════════════════════════════════════════════════════════════════
#  节点函数
# ══════════════════════════════════════════════════════════════════════════

def automation_entry(state: SOPState) -> dict:
    """入口：初始化当前页面的 skill 迭代器。"""
    page = _get_current_page(state)
    return {
        "current_skill": "",
        "current_phase": "Automation",
    }


def perceive_node(state: SOPState) -> dict:
    """
    感知：检查当前页面的已有产物（幂等跳过）。
    """
    page = _get_current_page(state)
    module = state["module"]

    existing = []
    for skill_id, pattern in SKILL_OUTPUT_MAP.items():
        path = _resolve_path(pattern, module, page)
        if path.exists() and path.stat().st_size > 0:
            existing.append(skill_id)

    return {
        "agent_outputs": {
            **state.get("agent_outputs", {}),
            "automation_existing_skills": existing,
        },
    }


def plan_node(state: SOPState) -> dict:
    """
    规划：决定下一个要执行的 Skill。

    - 已完成（existing）→ 跳过
    - 正常推进 → 下一个
    - 全部完成 → 空字符串
    """
    existing = state.get("agent_outputs", {}).get("automation_existing_skills", [])
    completed = state.get("completed_skills", [])
    failed = state.get("failed_skills", {})

    for skill_id in AUTOMATION_SKILLS:
        if skill_id in existing or skill_id in completed:
            continue
        if skill_id in failed and state.get("retry_counts", {}).get(skill_id, 0) >= 3:
            continue  # 超过最大重试，跳过
        return {"current_skill": skill_id}

    return {"current_skill": ""}  # 全部完成


def act_node(state: SOPState) -> dict:
    """
    执行：调用 run_skill() 或运行机械化检查。
    """
    skill_id = state.get("current_skill", "")
    if not skill_id:
        return {}

    module = state["module"]
    page = _get_current_page(state)
    provider = state.get("provider", "claude")

    # ── 机械化检查：code-consistency-checker ──
    if skill_id == "automation/code-consistency-checker":
        return _act_mechanical_check(module, page)

    # ── LLM Skill 调用 ──
    from aitest.agent_runner import run_skill

    response = run_skill(
        skill_id=skill_id,
        user_input=f"模块: {module}, 页面: {page}",
        provider=provider,
        context_vars={"module": module, "page": page},
    )

    if response.finish_reason == "error":
        return {
            "agent_outputs": {
                **state.get("agent_outputs", {}),
                f"skill_{skill_id.replace('/', '_')}": {"error": response.content[:300]},
            },
        }

    # 保存产出到文件
    saved_path = _save_skill_output(skill_id, response.content, module, page)

    return {
        "agent_outputs": {
            **state.get("agent_outputs", {}),
            f"skill_{skill_id.replace('/', '_')}": {
                "content_preview": response.content[:500],
                "token_usage": response.token_usage,
                "finish_reason": response.finish_reason,
                "saved_path": saved_path,
            },
        },
    }


def _act_mechanical_check(module: str, page: str) -> dict:
    """机械化代码合规检查（不调 LLM）。"""
    po_path = _resolve_path(
        "ZJSN_Test-master526/page/{module}_page/{PageName}Page.py", module, page
    )
    test_path = _resolve_path(
        "ZJSN_Test-master526/script/{module}/test_{page_underscore}.py", module, page
    )

    issues = []
    for fpath in [po_path, test_path]:
        if not fpath.exists():
            continue
        content = fpath.read_text(encoding="utf-8")
        is_po = "Page.py" in fpath.name

        for label, pattern, should_find in CODE_REDLINE_CHECKS:
            if "BasePage" in label and not is_po:
                continue
            found = bool(re.search(pattern, content, re.MULTILINE))
            if found != should_find:
                if should_find:
                    issues.append(f"{fpath.name}: 缺少 {label}")
                else:
                    for match in re.finditer(pattern, content, re.MULTILINE):
                        line_no = content[:match.start()].count("\n") + 1
                        matched_text = match.group().strip()[:60]
                        if "print" in label and "def " in matched_text:
                            continue
                        issues.append(f"{fpath.name}:{line_no}: {label} (禁止模式: {matched_text})")

    summary_lines = []
    if issues:
        summary_lines.append(f"Code consistency check found {len(issues)} issues:")
        summary_lines.extend(f"  - {i}" for i in issues)
    else:
        summary_lines.append("Code consistency check passed.")

    return {
        "agent_outputs": {
            "code_consistency_result": {
                "passed": len(issues) == 0,
                "issues": issues,
                "summary": "\n".join(summary_lines),
            },
        },
    }


def _save_skill_output(skill_id: str, content: str, module: str, page: str) -> str:
    """将 LLM 输出保存到文件。"""
    pattern = SKILL_OUTPUT_MAP.get(skill_id)
    if not pattern:
        return ""

    path = _resolve_path(pattern, module, page)

    # .py 文件：从 markdown code block 提取
    if path.suffix == ".py":
        extracted = _extract_code_block(content, "python") or _extract_code_block(content, "py")
        if not extracted:
            extracted = content
    else:
        extracted = content

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(extracted, encoding="utf-8")
    return str(path)


def _extract_code_block(text: str, language: str = "python") -> str:
    """从 markdown 中提取代码块。"""
    pattern = rf'```{language}\s*\n(.*?)```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r'```\s*\n(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def observe_node(state: SOPState) -> dict:
    """
    观察：验证 Skill 产出质量。

    检查：
      - 文件存在性
      - 代码红线 (只对 page-object-generator 和 test-script-generator)
    """
    skill_id = state.get("current_skill", "")
    module = state["module"]
    page = _get_current_page(state)

    obs = {
        "skill_id": skill_id,
        "status": "pass",
        "artifacts_found": [],
        "artifacts_missing": [],
        "quality_issues": [],
        "summary": "",
        "suggestion": "continue",
        "token_usage": {},
    }

    # 机械化检查的结果提取
    if skill_id == "automation/code-consistency-checker":
        result = state.get("agent_outputs", {}).get("code_consistency_result", {})
        if result.get("passed"):
            obs["status"] = "pass"
            obs["summary"] = "Code consistency check passed."
        else:
            obs["status"] = "fail"
            obs["quality_issues"] = result.get("issues", [])
            obs["summary"] = result.get("summary", "")
            obs["suggestion"] = "continue"  # 确定性检查，重试不会改变结果
        return {"skill_observations": [obs]}

    # 文件产出检查
    pattern = SKILL_OUTPUT_MAP.get(skill_id)
    if pattern:
        path = _resolve_path(pattern, module, page)
        if path.exists() and path.stat().st_size > 0:
            obs["artifacts_found"].append(str(path))
        else:
            obs["artifacts_missing"].append(str(path))
            obs["status"] = "fail"
            obs["suggestion"] = "retry"
            obs["summary"] = f"Missing output: {path.name}"

    # 代码红线检查（仅 page-object-generator 和 test-script-generator）
    if skill_id in ("automation/page-object-generator", "automation/test-script-generator"):
        pattern = SKILL_OUTPUT_MAP.get(skill_id)
        if pattern:
            path = _resolve_path(pattern, module, page)
            if path.exists():
                file_content = path.read_text(encoding="utf-8")
                is_po = "Page.py" in path.name

                for label, check_pattern, should_find in CODE_REDLINE_CHECKS:
                    if "BasePage" in label and not is_po:
                        continue
                    found = bool(re.search(check_pattern, file_content, re.MULTILINE))
                    if found != should_find:
                        obs["quality_issues"].append(
                            f"{label}: {'应包含' if should_find else '禁止'} {check_pattern}"
                        )
                        if should_find:
                            obs["status"] = "fail"
                            obs["suggestion"] = "retry"

    if obs["status"] == "pass" and not obs["artifacts_found"] and not obs["artifacts_missing"]:
        obs["summary"] = "Skill executed (no file output expected)"

    return {"skill_observations": [obs]}


def skill_router(state: SOPState) -> Literal["continue", "retry", "gate_check"]:
    """根据当前 Skill 的观察结果决定下一步。"""
    skill_id = state.get("current_skill", "")
    if not skill_id:
        return "gate_check"

    observations = state.get("skill_observations", [])
    if not observations:
        return "continue"

    last_obs = observations[-1]
    if isinstance(last_obs, dict):
        suggestion = last_obs.get("suggestion", "continue")
    else:
        suggestion = getattr(last_obs, "suggestion", "continue")

    if suggestion == "retry":
        retries = state.get("retry_counts", {}).get(skill_id, 0)
        if retries < 3:
            return "retry"
    if suggestion in ("continue", "skip"):
        return "continue"
    return "gate_check"


def update_node(state: SOPState) -> dict:
    """
    更新：根据观察结果更新 skill 完成/失败状态。
    """
    skill_id = state.get("current_skill", "")
    observations = state.get("skill_observations", [])

    updates: dict = {
        "completed_skills": [],
        "failed_skills": dict(state.get("failed_skills", {})),
        "retry_counts": dict(state.get("retry_counts", {})),
    }

    if observations and skill_id:
        last_obs = observations[-1]
        if isinstance(last_obs, dict):
            status = last_obs.get("status", "")
        else:
            status = getattr(last_obs, "status", "")

        if status == "pass":
            updates["completed_skills"] = [skill_id]
            updates["failed_skills"].pop(skill_id, None)
            updates["retry_counts"].pop(skill_id, None)
        elif status in ("fail", "partial"):
            updates["failed_skills"][skill_id] = last_obs.get("summary", "") if isinstance(last_obs, dict) else last_obs.summary
            updates["retry_counts"][skill_id] = updates["retry_counts"].get(skill_id, 0) + 1

    return updates


def automation_review(state: SOPState) -> dict:
    """
    对抗性代码审查：LLM 以资深自动化工程师身份批判 PageObject + 测试脚本。

    检查维度:
      - 定位器稳定性（是否依赖动态 ID/脆弱XPath?）
      - 等待策略是否正确（有无遗漏等待？）
      - 测试断言是否充分（只检查 toaster？忘了验证数据？）

    严重问题 → interrupt() 挂起等待人工确认。
    """
    module = state["module"]
    page = _get_current_page(state)
    provider = state.get("provider", "claude")

    po_path = _resolve_path(
        "ZJSN_Test-master526/page/{module}_page/{PageName}Page.py", module, page
    )
    test_path = _resolve_path(
        "ZJSN_Test-master526/script/{module}/test_{page_underscore}.py", module, page
    )

    po_code = po_path.read_text(encoding="utf-8")[:2000] if po_path.exists() else "(缺失)"
    test_code = test_path.read_text(encoding="utf-8")[:2000] if test_path.exists() else "(缺失)"

    from aitest.agent_runner import run_skill
    import json, re

    review_input = f"""你是资深UI自动化工程师，请**批判**以下自动化代码：

模块: {module}, 页面: {page}

## PageObject ({po_path.name})
```python
{po_code}
```

## 测试脚本 ({test_path.name})
```python
{test_code}
```

## 审查要求
1. 定位器是否稳定？（避免 //*[@id=...] 绝对路径、动态class名、无意义的索引）
2. 是否缺少等待？（点击后无等待即断言、弹窗未等待关闭）
3. 断言是否充分？（只检查 toast 提示？遗漏了数据验证？）
4. 判断: PASS / WARN（建议改进但可跑）/ FAIL（有严重问题）

输出 JSON:
{{"severity": "PASS"|"WARN"|"FAIL",
 "issues": ["问题1", "问题2"],
 "risky_locators": ["不稳定的定位器"],
 "suggestion": "一句话建议"}}"""

    response = run_skill(
        skill_id="automation/code-consistency-checker",
        user_input=review_input,
        provider=provider,
        context_vars={"module": module, "page": page},
    )

    review_result = {"severity": "WARN", "issues": [], "suggestion": ""}
    try:
        json_match = re.search(r'\{[^{}]*"severity"[^{}]*\}', response.content, re.DOTALL)
        if json_match:
            review_result = json.loads(json_match.group())
    except Exception:
        review_result = {"severity": "WARN", "issues": ["审查解析失败"], "suggestion": response.content[:200]}

    severity = review_result.get("severity", "WARN")
    if severity == "FAIL":
        from langgraph.types import interrupt
        interrupt({
            "type": "automation_review",
            "module": module,
            "page": page,
            "severity": "FAIL",
            "issues": review_result.get("issues", [])[:5],
            "suggestion": review_result.get("suggestion", ""),
            "options": ["continue_anyway", "regenerate"],
        })

    # 将审查结果也记录下来供后续参考
    result_path = CONTEXT_MODULES / module / "pages" / page / "CODE_REVIEW.md"
    review_md = f"# Code Review — {module}/{page}\n\n"
    review_md += f"**Severity**: {severity}\n\n"
    review_md += "## Issues\n" + "\n".join(f"- {i}" for i in review_result.get("issues", []))
    review_md += f"\n\n## Suggestion\n{review_result.get('suggestion', '')}"
    try:
        result_path.write_text(review_md, encoding="utf-8")
    except Exception:
        pass

    return {
        "agent_outputs": {
            **state.get("agent_outputs", {}),
            "auto_review": {
                "passed": severity != "FAIL",
                "severity": severity,
                "issues": review_result.get("issues", [])[:5],
                "suggestion": review_result.get("suggestion", ""),
                "report_path": str(result_path),
            },
        },
    }


def automation_gate_check(state: SOPState) -> dict:
    """
    L2 门禁：验证当前页面的自动化产物完整性。
    """
    module = state["module"]
    page = _get_current_page(state)

    page_dir = CONTEXT_MODULES / module / "pages" / page
    required_files = [
        (page_dir / "TECH_ANALYSIS.md", "TECH_ANALYSIS.md"),
        (page_dir / "AUTO_STRATEGY.md", "AUTO_STRATEGY.md"),
    ]
    # 检查 ZJSN 代码文件
    po_file = ZJSN_TEST / "page" / f"{module}_page" / f"{_slug_to_page_name(page)}Page.py"
    test_file = ZJSN_TEST / "script" / module / f"test_{_slug_to_underscore(page)}.py"
    required_files.extend([
        (po_file, f"PageObject: {po_file.name}"),
        (test_file, f"TestScript: {test_file.name}"),
    ])

    missing = []
    for fpath, label in required_files:
        if not fpath.exists() or fpath.stat().st_size == 0:
            missing.append(label)

    ok = len(missing) == 0
    result = GateResult(
        level=GateLevel.L2_AGENT,
        phase="Automation",
        ok=ok,
        message=f"Automation gate for {module}/{page}: {'PASS' if ok else 'FAIL'}",
        details={"missing_files": missing, "module": module, "page": page},
    )

    return {"gate_results": [result.to_dict()]}


def automation_exit(state: SOPState) -> dict:
    """
    出口：标记当前页面完成，更新 page 迭代器。
    当所有页面处理完毕时，标记 Automation phase 完成。
    """
    page = _get_current_page(state)
    idx = state.get("current_page_index", 0)
    pages = state.get("pages", [])
    next_idx = idx + 1

    updates: dict = {
        "current_page_index": next_idx,
        "completed_skills": [],
        "current_skill": "",
    }

    # 所有页面处理完毕 → 标记 phase 完成
    if next_idx >= len(pages):
        updates["completed_phases"] = ["Automation"]
        updates["current_page_index"] = 0

    return updates


# ══════════════════════════════════════════════════════════════════════════
#  图构建
# ══════════════════════════════════════════════════════════════════════════

def build_automation_subgraph() -> StateGraph:
    """
    构建 automation-agent SubGraph。

    图结构:
      entry → perceive → plan → act → observe → update → skill_router
                                                          ├── continue → plan
                                                          ├── retry → plan (with adjustments)
                                                          └── gate_check → exit
    """
    builder = StateGraph(SOPState)

    builder.add_node("entry", automation_entry)
    builder.add_node("perceive", perceive_node)
    builder.add_node("plan", plan_node)
    builder.add_node("act", act_node)
    builder.add_node("observe", observe_node)
    builder.add_node("update", update_node)
    builder.add_node("gate_check", automation_gate_check)
    builder.add_node("review", automation_review)
    builder.add_node("exit", automation_exit)

    builder.set_entry_point("entry")
    builder.add_edge("entry", "perceive")
    builder.add_edge("perceive", "plan")
    builder.add_edge("plan", "act")
    builder.add_edge("act", "observe")
    builder.add_edge("observe", "update")
    builder.add_conditional_edges("update", skill_router, {
        "continue": "plan",
        "retry": "plan",
        "gate_check": "gate_check",
    })
    builder.add_edge("gate_check", "review")
    builder.add_edge("review", "exit")
    builder.add_edge("exit", END)

    return builder
