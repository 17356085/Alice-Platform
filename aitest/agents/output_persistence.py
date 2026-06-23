"""Skill output persistence — SKILL_OUTPUT_MAP, file saving, event emission.

Extracted from agent_runner.py (W01 refactor, 2026-06-17).
~120 lines extracted from AgentLoop._save_skill_output.
"""

import re
import time
from pathlib import Path

from aitest.llm.provider import LLMResponse

# ── Paths ────────────────────────────────────────────────────────────────
from aitest.platform.paths import get_workstudy, get_test_project_root, get_context_modules
WORKSTUDY = get_workstudy()
CONTEXT_MODULES = get_context_modules()


def _slug_to_page_name(slug: str) -> str:
    """kebab-case → PascalCase conversion for page class names."""
    if not slug:
        return ""
    return "".join(part.capitalize() for part in slug.split("-"))


def _page_slug_to_underscore(slug: str) -> str:
    """kebab-case → snake_case."""
    return slug.replace("-", "_") if slug else ""


def build_skill_output_map(module: str, page: str) -> dict:
    """Build skill_id → (file_path, file_type) mapping for a module/page."""
    page_name = _slug_to_page_name(page)
    page_underscore = _page_slug_to_underscore(page)
    zjsn = get_test_project_root()

    po_path = zjsn / "page" / f"{module}_page" / f"{page_name}Page.py" if zjsn else None
    test_path = zjsn / "script" / module / f"test_{page_underscore}.py" if zjsn else None
    conftest_path = zjsn / "script" / module / "conftest.py" if zjsn else None

    # Build output map — automation entries depend on test project availability
    output_map = {
        # ── Requirement phase ──
        "requirements/module-modeling": (
            CONTEXT_MODULES / module / "MODULE_CONTEXT.md", "md"
        ),
        "requirements/requirement-analysis": [
            (CONTEXT_MODULES / module / "pages" / page / "PAGE_CONTEXT.md", "md"),
            (CONTEXT_MODULES / module / "pages" / page / "PAGE_INTERFACE.yaml", "yaml"),
        ],
        # ── Test Design phase ──
        "test-design/page-analysis": [
            (CONTEXT_MODULES / module / "pages" / page / "PAGE_CONTEXT.md", "md"),
            (CONTEXT_MODULES / module / "pages" / page / "PAGE_INTERFACE.yaml", "yaml"),
        ],
        "test-design/risk-modeling": (
            CONTEXT_MODULES / module / "pages" / page / "RISK_MODEL.md", "md"
        ),
        "test-design/testcase-design": (
            CONTEXT_MODULES / module / "pages" / page / "TEST_CASES.md", "md"
        ),
        "test-design/test-design-synthesizer": (
            CONTEXT_MODULES / module / "pages" / page / "TEST_DESIGN.md", "md"
        ),
        # ── Automation phase ──
        "automation/tech-analysis": (
            CONTEXT_MODULES / module / "pages" / page / "TECH_ANALYSIS.md", "md"
        ),
        "automation/auto-strategy": (
            CONTEXT_MODULES / module / "pages" / page / "AUTO_STRATEGY.md", "md"
        ),
    }
    if po_path:
        output_map["automation/page-object-generator"] = (po_path, "py")
    if test_path:
        items = [(test_path, "py")]
        if conftest_path:
            items.append((conftest_path, "py"))
        output_map["automation/test-script-generator"] = items
    return output_map


def extract_code_block(text: str, language: str = "python") -> str:
    """Extract code block from markdown."""
    pattern = rf'```{language}\s*\n(.*?)```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r'```\s*\n(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def extract_yaml_block(text: str) -> str:
    """Extract YAML code block from markdown."""
    pattern = r'```yaml\s*\n(.*?)```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r'```\s*\n(.*?)```', text, re.DOTALL)
    if match:
        content = match.group(1).strip()
        if content.startswith("interface:") or content.startswith("meta:") or content.startswith("elements:"):
            return content
    return ""


def save_skill_output(skill_id: str, content: str, module: str, page: str,
                      agent_name: str, logger=None) -> str:
    """Save LLM output to target file(s). Returns primary saved path or ''.

    Args:
        skill_id: e.g. 'automation/tech-analysis'
        content: raw LLM response content
        module: module name
        page: page slug
        agent_name: for event emission
        logger: optional callable(msg) for logging

    Returns:
        Primary saved file path or empty string.
    """
    output_map = build_skill_output_map(module, page)
    target = output_map.get(skill_id)
    if not target:
        return ""

    targets = target if isinstance(target, list) else [target]
    saved_paths = []

    for file_path, file_type in targets:
        if file_type == "py":
            extracted = extract_code_block(content, "python")
            if not extracted:
                extracted = extract_code_block(content, "py")
            if not extracted:
                extracted = content
        else:
            extracted = content

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(extracted, encoding="utf-8")
        if logger:
            logger(f"  Saved: {file_path}")
        saved_paths.append(str(file_path))

    # Emit ContextUpdated events
    if saved_paths:
        try:
            from aitest.audit_engine.event_bus import emit
            gov_files = [p for p in saved_paths if "governance/context" in str(p).replace("\\", "/")]
            code_files = [p for p in saved_paths if p not in gov_files]
            if gov_files:
                emit("ContextUpdated",
                     file=str(gov_files[0]),
                     changes=f"Agent {agent_name} updated {len(gov_files)} governance context file(s)",
                     content_hash=str(hash(frozenset(gov_files))))
            if code_files:
                emit("ContextUpdated",
                     file=str(code_files[0]),
                     changes=f"Agent {agent_name} generated {len(code_files)} code file(s)",
                     content_hash=str(hash(frozenset(code_files))))
        except Exception:
            pass  # Best-effort event emission

    return saved_paths[0] if saved_paths else ""


def persist_consistency_report(module: str, page: str, lines: list[str], issues: list[str]) -> None:
    """Write mechanical consistency check report to artifacts/code-review/."""
    try:
        report_dir = WORKSTUDY / "governance" / "artifacts" / "code-review" / module / page
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "consistency-check.md"
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        report_content = f"# Code Consistency Check — {module}/{page}\n\n"
        report_content += f"**Time**: {timestamp}\n**Module**: {module}\n**Page**: {page}\n"
        report_content += f"**Issues**: {len(issues)}\n\n"
        for line in lines:
            report_content += f"{line}\n"
        report_path.write_text(report_content, encoding="utf-8")
    except Exception:
        pass


def persist_review_report(module: str, page: str, content: str) -> None:
    """Write LLM review report to artifacts/code-review/."""
    try:
        report_dir = WORKSTUDY / "governance" / "artifacts" / "code-review" / module / page
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "llm-review.md"
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        report_content = f"# LLM Code Review — {module}/{page}\n\n"
        report_content += f"**Time**: {timestamp}\n**Module**: {module}\n**Page**: {page}\n\n"
        report_content += content
        report_path.write_text(report_content, encoding="utf-8")
    except Exception:
        pass
