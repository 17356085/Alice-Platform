"""
aitest — AI 自动化测试平台统一 CLI

用法:
  aitest sop run --module=<name> [--pages=...] [--provider=...]  完整 SOP 流水线（⭐ 主入口）
  aitest sop resume --run-id=<id>              断点续跑
  aitest sop status [--run-id=<id>]            查看 SOP 状态
  aitest agent run <name> --module=<m>         单 Agent 执行
  aitest skill run <id> --input=<text>         单 Skill 执行
  aitest check [--module=<name>]               代码质量检查
  aitest status [--module=<name>]              项目/模块状态
  aitest run <module> [--smoke|--all]          执行 pytest 测试
  aitest report summary|progress|excel         生成报告
  aitest rag search <query>                    RAG 检索
  aitest dashboard                              平台总览面板
  aitest server start                           启动 API 服务

  完整命令: aitest graph | workflow | bus | bug | errors | trace | eval | ab | regression
"""
import os
import sys
import json
import subprocess
import time
import argparse
from pathlib import Path

from aitest.platform.paths import get_workstudy, get_test_project_root, get_governance_dir, get_project_dir
from aitest.audit_engine.event_bus import emit, list_pending, list_all, process_pending, EVENT_DIR

WORKSTUDY = get_workstudy()
GOVERNANCE = get_governance_dir()


def _zjsn():
    """Resolve test project root lazily. Returns None if not configured."""
    import os
    root = get_test_project_root()
    if root:
        return root
    # No fallback — project must be configured
    return None


def cmd_project_register(args):
    """Register a project with the platform."""
    import yaml
    project_path = Path(args.path).resolve()
    if not project_path.exists():
        print(f"ERROR: Path does not exist: {project_path}")
        return 1

    # Check for .tlo/project.yaml
    tlo_yaml = project_path / ".tlo" / "project.yaml"
    if tlo_yaml.exists():
        config = yaml.safe_load(tlo_yaml.read_text(encoding="utf-8"))
        project_id = config.get("project", {}).get("id", args.id or project_path.name)
    else:
        project_id = args.id or project_path.name
        # Create .tlo/project.yaml from template
        tlo_dir = project_path / ".tlo"
        tlo_dir.mkdir(parents=True, exist_ok=True)
        for subdir in ["knowledge/modules", "context", "runtime/sop-status", "cache/discovery", "artifacts"]:
            (tlo_dir / subdir).mkdir(parents=True, exist_ok=True)
        tlo_yaml.write_text(
            f"# {project_id} — TLO Project Configuration\n"
            f"project:\n"
            f"  id: \"{project_id}\"\n"
            f"  name: \"{project_id}\"\n"
            f"test_project:\n"
            f"  type: \"pytest-selenium\"\n"
            f"  code_path: \"{project_path.relative_to(WORKSTUDY.parent) if WORKSTUDY.parent in project_path.parents else project_path}\"\n",
            encoding="utf-8"
        )
        print(f"Created .tlo/project.yaml for {project_id}")

    # Update project-index.yaml
    index_path = GOVERNANCE / "context" / "project-index.yaml"
    try:
        index = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
    except Exception:
        index = {"projects": []}

    projects = index.get("projects", [])
    existing = [p for p in projects if p.get("id") == project_id]
    if existing:
        existing[0]["path"] = str(project_path)
        print(f"Updated existing project: {project_id}")
    else:
        projects.append({
            "id": project_id,
            "name": project_id,
            "path": str(project_path),
            "tlo_dir": ".tlo/",
            "status": "active",
        })
        print(f"Registered new project: {project_id}")

    # Set as active
    from aitest.platform.context import set_active_project
    set_active_project(project_id)

    index_path.write_text(yaml.dump(index, allow_unicode=True, default_flow_style=False), encoding="utf-8")
    print(f"Active project: {project_id}")
    print(f"Path: {project_path}")
    return 0


def cmd_check(args):
    """代码质量检查 + 一致性校验。"""
    # P2-2: 一致性校验
    if args.consistency:
        sys.path.insert(0, str(WORKSTUDY))
        from aitest.testing.consistency_checker import run_all_checks
        results = run_all_checks()
        all_ok = all(r.ok for r in results)
        issues = sum(len(r.details) for r in results)

        if args.json_output:
            import json as _json
            output = {
                "status": "pass" if all_ok else "fail",
                "checks": [
                    {"name": r.check, "ok": r.ok, "message": r.message, "details": r.details}
                    for r in results
                ],
                "summary": f"{sum(1 for r in results if r.ok)}/{len(results)} checks passed, {issues} issues",
            }
            print(_json.dumps(output, ensure_ascii=False, indent=2))
        else:
            width = 60
            print()
            print("=" * width)
            print("  Consistency Check — P2-2")
            print("=" * width)
            for r in results:
                icon = "OK" if r.ok else "FAIL"
                print(f"\n  [{icon}] {r.check}")
                print(f"       {r.message}")
                for d in r.details[:5]:
                    print(f"         - {d}")
            print(f"\n  Summary: {sum(1 for r in results if r.ok)}/{len(results)} passed, {issues} issues")
            print("=" * width)
            print()
        return

    # 代码质量检查
    tool = _zjsn() / "tools" / "check_code_quality.py"
    cmd = ["python", str(tool)]
    if args.staged:
        cmd.append("--staged")
    if args.json_output:
        cmd.append("--json")
    if args.module:
        page_dir = _zjsn() / "page" / f"{args.module}_page"
        if page_dir.exists():
            cmd.append(str(page_dir))
        else:
            print(f"Warning: page/{args.module}_page not found, scanning all")
    subprocess.run(cmd, cwd=str(_zjsn()))


def cmd_status(args):
    """项目/模块状态。"""
    sys.path.insert(0, str(WORKSTUDY))
    from aitest.agents.agent_scheduler import recommend_next_agent, check_preconditions
    from aitest.knowledge.rag_engine import get_chroma_client

    module = args.module or "tank"

    print(f"\n{'='*60}")
    print(f"  AI Test Platform — Status")
    print(f"{'='*60}\n")

    # Agent scheduler
    rec = recommend_next_agent(module)
    print(f"[Module: {module}]")
    print(f"  Next Agent:  {rec['agent']} ({rec['phase']})")
    print(f"  Reason:      {rec['reason']}")
    if rec.get('blockers'):
        for b in rec['blockers']:
            print(f"  Blocker:     {b['pattern']} ({b['check']})")

    # RAG status
    try:
        client = get_chroma_client()
        colls = client.list_collections()
        total = sum(c.count() for c in colls)
        print(f"\n[RAG] {len(colls)} collections, {total} docs")
        for c in colls:
            print(f"  {c.name}: {c.count()} docs")
    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("cli.cmd_status", "rag_status", e)
        print(f"\n[RAG] Not connected")

    # Graph runs (LangGraph checkpoint)
    try:
        from aitest.graphs.checkpoint import list_runs as list_graph_runs
        runs = list_graph_runs(limit=5)
        print(f"\n[Graph Runs] {len(runs)} run(s)")
        for r in runs:
            print(f"  {r['run_id']} ({r.get('updated_at', '?')})")
    except Exception:
        pass

    print()


def cmd_sync(args):
    """会话上下文同步。"""
    module = args.module
    if not module:
        print("Error: --module is required for sync")
        return

    template_path = GOVERNANCE / "templates" / "current-task.template.md"
    task_path = get_project_dir() / "modules" / module / "CURRENT_TASK.md"

    if args.start:
        if task_path.exists():
            print(f"Reading CURRENT_TASK.md for {module}...")
            with open(task_path, "r", encoding="utf-8") as f:
                print(f.read()[:2000])
        else:
            print(f"No CURRENT_TASK.md found for {module}.")
            print(f"Template: {template_path}")
            print("Create one with: aitest sync --module={module} --end")

    elif args.end:
        task_path.parent.mkdir(parents=True, exist_ok=True)
        # Generate from template
        template = open(template_path, "r", encoding="utf-8").read() if template_path.exists() else ""
        date_str = time.strftime("%Y-%m-%d")
        content = template.replace("{{date}}", date_str)
        content = content.replace("{{module_name}}", module)
        content = content.replace("{{agent_name}}", "aitest CLI")
        with open(task_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"CURRENT_TASK.md created: {task_path}")
        print("Please fill in the details before committing.")


def cmd_run(args):
    """执行测试。"""
    module = args.module
    script_dir = _zjsn() / "script" / module
    if not script_dir.exists():
        print(f"Error: script/{module}/ not found")
        return

    cmd = ["pytest", str(script_dir), "-v", f"--alluredir={_zjsn()}/allure-results"]
    if args.smoke:
        cmd.extend(["-m", "smoke"])
    if args.parallel:
        cmd.extend(["-n", "3", "--dist=loadfile"])
    if args.destructive:
        cmd.extend(["-m", "destructive", "-q"])

    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(_zjsn()))


def cmd_report(args):
    """生成报告。"""
    mode = args.mode
    module = args.module or ""

    if mode == "summary":
        print(f"Generating test summary report for {module or 'all modules'}...")
        print("→ Use report-agent: /report-agent")
        print("→ Or: aitest rag search 'test summary template' project_context")

    elif mode == "progress":
        print(f"Generating progress report...")
        print("→ Use report-agent: /report-agent")
        print("→ Or: aitest agent check --module={module or 'tank'}")

    elif mode == "excel":
        print(f"Generating Excel report for {module or 'all modules'}...")
        excel_tool = _zjsn() / "tools" / "report" / "generate_excel.py"
        if excel_tool.exists():
            subprocess.run(["python", str(excel_tool)], cwd=str(_zjsn()))
        else:
            print("Excel generation tool not found. Using excel-exporter Skill via /report-agent")


def cmd_agent(args):
    """Agent 调度 + 执行。"""
    sys.path.insert(0, str(WORKSTUDY))
    from aitest.agents.agent_scheduler import check_preconditions, recommend_next_agent, auto_advance

    module = args.module or "tank"

    if args.action == "run":
        # ── agent run: 执行 Agent（使用 agent_runner）──
        from aitest.agents.agent_runner import run_agent, list_agents

        agent_name = args.agent_name
        provider = args.provider or "claude"

        # 兼容不带 -agent 后缀的输入
        if not agent_name.endswith("-agent"):
            agent_name = f"{agent_name}-agent"

        valid_agents = [a for a in list_agents() if a.endswith("-agent") and not a.startswith(("project", "requirement"))]
        if agent_name not in list_agents():
            print(f"Unknown agent: '{agent_name}'")
            print(f"Available: {', '.join(valid_agents)}")
            return

        print(f"Agent: {agent_name}")
        print(f"Module: {module}")
        if args.page:
            print(f"Page: {args.page}")
        print(f"Provider: {provider}")
        print()

        result = run_agent(
            agent_name=agent_name,
            provider=provider,
            module=module,
            page=args.page,
            verbose=True,
        )

        print(f"\nDone: {result['skills_executed']} skills, "
              f"{result['total_tokens']['input']}+{result['total_tokens']['output']} tokens, "
              f"{result['total_elapsed']}s")

    elif args.action == "check":
        result = check_preconditions(module)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.action == "next":
        rec = recommend_next_agent(module)
        print(f"\nModule: {module}")
        print(f"Next Agent: {rec['agent']} ({rec['phase']})")
        print(f"Reason: {rec['reason']}")
        if rec.get('blockers'):
            print("Blockers:")
            for b in rec['blockers']:
                print(f"  - {b['pattern']} ({b['check']})")

    elif args.action == "auto":
        result = auto_advance(module, auto_trigger=args.force)
        print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_skill(args):
    """执行单个 Skill。"""
    sys.path.insert(0, str(WORKSTUDY))
    from aitest.agents.agent_runner import run_skill
    from aitest.llm.skill_loader import list_skills, list_categories

    if args.action == "list":
        # ── skill list: 列出可用 Skill ──
        if args.category:
            skills = list_skills(args.category)
            print(f"\nCategory: {args.category} ({len(skills)} skills)")
        else:
            skills = []
            for cat in list_categories():
                cat_skills = list_skills(cat)
                skills.extend(cat_skills)
                print(f"  {cat}: {len(cat_skills)} skills")
            print(f"\nTotal: {len(skills)} active skills in {len(list_categories())} categories")

        if args.category:
            for s in skills:
                print(f"  {s['id']}")

    elif args.action == "run":
        # ── skill run: 执行 Skill ──
        skill_id = args.skill_id
        user_input = args.input
        provider = args.provider or "claude"

        if not user_input:
            print("Error: --input/-i is required for skill run")
            print("Example: aitest skill run test-design/page-analysis --input '分析 equipment/alarm-config' --provider claude")
            return

        print(f"Skill: {skill_id}")
        print(f"Provider: {provider}")
        print(f"Input: {user_input[:100]}{'...' if len(user_input) > 100 else ''}")
        print()

        response = run_skill(
            skill_id=skill_id,
            user_input=user_input,
            provider=provider,
            context_vars={
                "module": args.module or "",
                "page": args.page or "",
            },
        )

        if response.finish_reason == "error":
            print(f"Error: {response.content[:200]}")
        else:
            print(f"Model: {response.model}")
            print(f"Tokens: {response.token_usage}")
            print(f"\n--- Response ---\n{response.content[:2000]}")
            if len(response.content) > 2000:
                print(f"\n[... 共 {len(response.content)} 字符，已截断 ...]")

    elif args.action == "promote":
        # P0-ACTIVATION (2026-06-15): Skill 版本推广 — 闭合 Prompt Versioning 链路
        skill_id = args.skill_id
        new_version = args.version
        provider = args.provider or "claude"

        if not new_version:
            print("Error: --version/-v is required for skill promote")
            print("Example: aitest skill promote test-design/page-analysis --version 1.1")
            return

        from aitest.testing.regression import promote_skill_version
        print(f"Promoting {skill_id} -> v{new_version}...")
        result = promote_skill_version(skill_id, new_version, provider=provider)

        if result.get("promoted"):
            print(f"  Promoted: {result['old_version']} -> {result['new_version']}")
            gate = result.get("gate_result", {})
            print(f"  Gate: {gate.get('cases_passed', 0)}/{gate.get('cases_total', 0)} passed")
            print(f"  Event: PromptChanged emitted")
        else:
            print(f"  BLOCKED: {result.get('error', 'regression detected')}")
            gate = result.get("gate_result", {})
            if gate:
                print(f"  Gate: {gate.get('cases_failed', 0)}/{gate.get('cases_total', 0)} failed")
                for f in gate.get("failures", []):
                    print(f"    - {f.get('case_id', '?')}: {f.get('reason', 'degraded')}")
                print(f"  Event: EvalRegressed emitted")

    else:
        print(f"Unknown action: {args.action}. Use: list | run | promote")


def cmd_workflow(args):
    """工作流引擎 — LangGraph SOP Graph。

    旧版 workflow_engine.py 已于 2026-07 移除。
    使用 `aitest graph run --module=<m>` 替代。
    """
    sys.path.insert(0, str(WORKSTUDY))
    print("Legacy workflow engine removed. Use LangGraph SOP Graph:")
    print("  aitest graph run --module=<m> [--pages=<p1,p2>] [--mode=full]")
    print()

    if args.action == "list":
        print("Available workflows (governance/workflows/):")
        for wf in sorted((GOVERNANCE / "workflows").glob("*.yaml")):
            print(f"  {wf.stem}")
        print()
        print("To run: aitest graph run --module=<m>")
    elif args.action in ("run", "resume", "status"):
        print(f"Action '{args.action}' no longer supported via workflow_engine.")
        print("Use:")
        print("  aitest graph run     --module=<m>")
        print("  aitest graph resume  --run-id=<id>")
        print("  aitest graph status  [--run-id=<id>]")


def cmd_rag(args):
    """RAG 检索和索引管理。"""
    sys.path.insert(0, str(WORKSTUDY))

    if args.action == "search":
        from aitest.knowledge.rag_engine import search_known_issues, search_context
        query = " ".join(args.query)
        coll = args.collection or "known_issues"

        if coll == "known_issues":
            results = search_known_issues(query, n_results=args.n or 5)
        else:
            results = search_context(query, coll, n_results=args.n or 5)

        print(f"\nSearch: '{query}' in {coll}")
        print(f"Results: {len(results)}\n")
        for i, r in enumerate(results):
            print(f"{i+1}. [{r['id']}] dist={r.get('distance', 'N/A')}")
            meta = r.get('metadata', {})
            if meta.get('title'):
                print(f"   Title: {meta['title'][:80]}")
            if meta.get('module'):
                print(f"   Module: {meta['module']}, Page: {meta.get('page', 'N/A')}")
            doc = r.get('document', '')[:200]
            print(f"   {doc}")
            print()

    elif args.action == "index":
        from aitest.knowledge.rag_engine import index_all
        print("Rebuilding RAG indices...")
        results = index_all()
        for name, count in results.items():
            print(f"  {name}: {count} docs")
        print("Done.")

    elif args.action == "status":
        from aitest.knowledge.rag_engine import get_chroma_client
        client = get_chroma_client()
        colls = client.list_collections()
        total = sum(c.count() for c in colls)
        print(f"\nRAG Status: {len(colls)} collections, {total} total documents\n")
        for c in colls:
            print(f"  {c.name}: {c.count()} docs | {c.metadata.get('description', '')}")


def cmd_bus(args):
    """事件总线。"""
    sys.path.insert(0, str(WORKSTUDY))

    if args.action == "emit":
        if not args.event_type:
            print("Usage: aitest bus emit <EventType> [key=value ...]")
            return
        data = {}
        for kv in args.data or []:
            if "=" in kv:
                k, v = kv.split("=", 1)
                data[k] = v
        evt = emit(args.event_type, **data)
        print(f"Emitted: {evt.id} ({evt.type})")

    elif args.action == "listen":
        pending = list_pending()
        print(f"Pending events: {len(pending)}")
        for evt in pending:
            print(f"  [{evt.type}] {evt.id} — {evt.data}")

    elif args.action == "process":
        results = process_pending()
        print(f"Processed: {len(results)} events")
        for r in results:
            print(f"  [{r['type']}] → {r['action']}")



# Additional CLI commands extracted to submodules (P1 split, 2026-06-27)
from aitest.infra.cli.dashboard_cmds import cmd_dashboard
from aitest.infra.cli.debug_cmds import cmd_trace, cmd_errors, cmd_bug
from aitest.infra.cli.eval_cmds import cmd_ab, cmd_eval, cmd_regression, cmd_testcase
# Graph commands extracted to aitest/infra/cli/graph_cmds.py (P3-8 God Module split)
from aitest.infra.cli.graph_cmds import cmd_graph, cmd_graph_dev


# ══════════════════════════════════════════════════════════════════════════
#  DX Commands: inspect, event (v2.6)
# ══════════════════════════════════════════════════════════════════════════

def cmd_inspect(args):
    """Run Inspector — detailed view of any Run."""
    from aitest.platform.run_store import get_run_store
    from aitest.platform.timeline import build_timeline, timeline_summary

    rs = get_run_store()

    if args.run_id:
        run = rs.load_run(args.run_id)
        if run is None:
            print(f"Run '{args.run_id}' not found")
            return 1

        events = rs.list_events(args.run_id) if args.events else []
        timeline = build_timeline(args.run_id) if args.events else None

        if args.json:
            result = {"run": run.to_dict(), "events": [e.to_dict() for e in events]}
            if timeline:
                result["timeline"] = timeline
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0

        print(f"\n{'='*60}")
        print(f"  Run Inspector")
        print(f"{'='*60}")
        print(f"  Run ID:      {run.run_id}")
        print(f"  Request ID:  {run.request_id}")
        print(f"  Status:      {run.status}")
        print(f"  Agent:       {run.agent}")
        print(f"  Module:      {run.module}")
        print(f"  Pages:       {', '.join(run.pages) if run.pages else '—'}")
        print(f"  Created:     {run.created_at[:19] if run.created_at else '—'}")
        print(f"  Completed:   {run.completed_at[:19] if run.completed_at else '—'}")
        print(f"  Tokens:      {run.total_tokens:,}")
        print(f"  Cost:        ${run.total_cost:.4f}")
        print(f"  Error:       {run.error_message or '—'}")
        print(f"{'─'*60}")

        if events:
            print(f"  Events ({len(events)}):")
            for e in events:
                ts = e.timestamp[:19] if e.timestamp else ''
                print(f"    [{ts}] {e.event_type}")
            print(f"{'─'*60}")

        if timeline:
            summary = timeline_summary(args.run_id)
            if summary:
                print(f"  Timeline Summary:")
                for k, v in summary.items():
                    print(f"    {k}: {v}")
        print()
    else:
        # List recent runs
        runs = rs.list_runs(limit=args.limit)
        if not runs:
            print("No runs found.")
            return 0

        print(f"\n  Recent Runs ({len(runs)}):")
        print(f"  {'Run ID':<38} {'Status':<12} {'Agent':<22} {'Module':<20}")
        print(f"  {'─'*90}")
        for r in runs:
            rid = r.run_id[:36]
            print(f"  {rid:<38} {r.status:<12} {r.agent:<22} {r.module:<20}")
        print()


def cmd_event(args):
    """Event Inspector — browse/filter/tail events."""
    from aitest.audit_engine.event_bus import list_all, EVENT_DIR, cleanup_old_events
    from aitest.platform.run_store import get_run_store

    if args.action == "types":
        rs = get_run_store()
        all_events = rs.list_events(limit=1000)
        from collections import Counter
        type_counts = Counter(e.event_type for e in all_events)
        print(f"\n  Event Types ({len(type_counts)}):")
        for t, c in type_counts.most_common(20):
            print(f"    {t:<30} {c:>6}")
        print()

    elif args.action == "tail":
        print(f"  Watching events (Ctrl+C to stop)...")
        print(f"  Events dir: {EVENT_DIR}")
        try:
            seen = set()
            while True:
                events = list_all(limit=args.limit)
                for evt in events:
                    if evt.id not in seen:
                        seen.add(evt.id)
                        ts = evt.timestamp[:19] if hasattr(evt, 'timestamp') and evt.timestamp else ''
                        print(f"  [{ts}] {evt.type}")
                time.sleep(2)
        except KeyboardInterrupt:
            print("\n  Stopped.")

    else:  # list
        if args.json:
            events = list_all(limit=args.limit)
            result = []
            for e in events:
                d = {"id": e.id, "type": e.type, "timestamp": e.timestamp,
                     "processed": e.processed}
                if hasattr(e, 'data'):
                    d["data"] = str(e.data)[:200]
                result.append(d)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0

        # Filter by type or run_id from platform RunStore
        rs = get_run_store()
        events = rs.list_events(limit=args.limit or 20)

        if args.type:
            events = [e for e in events if e.event_type == args.type]
        if args.run_id:
            events = [e for e in events if e.run_id == args.run_id]

        print(f"\n  Recent Events ({len(events)}):")
        for e in events:
            ts = e.timestamp[:19] if e.timestamp else ''
            print(f"  [{ts}] {e.event_type:<30} run={e.run_id[:20]}...")


def main():
    # Windows GBK 终端兼容：强制 UTF-8 输出
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="AI Test Platform CLI")
    sub = parser.add_subparsers(dest="command")

    # ── check ──
    p_check = sub.add_parser("check", help="代码质量检查 + 一致性校验")
    p_check.add_argument("--module", help="模块名")
    p_check.add_argument("--staged", action="store_true", help="仅检查 stage 区")
    p_check.add_argument("--json", dest="json_output", action="store_true", help="JSON 输出")
    p_check.add_argument("--consistency", action="store_true", help="P2-2: 运行跨层一致性校验")

    # ── status ──
    p_status = sub.add_parser("status", help="项目/模块状态")
    p_status.add_argument("--module", help="模块名")

    # ── sync ──
    p_sync = sub.add_parser("sync", help="会话同步")
    p_sync.add_argument("--module", required=True, help="模块名")
    p_sync.add_argument("--start", action="store_true", help="读取 CURRENT_TASK")
    p_sync.add_argument("--end", action="store_true", help="写入 CURRENT_TASK")

    # ── run ──
    p_run = sub.add_parser("run", help="执行测试")
    p_run.add_argument("module", help="模块名")
    p_run.add_argument("--smoke", action="store_true", help="仅冒烟用例")
    p_run.add_argument("--parallel", action="store_true", help="并行执行")
    p_run.add_argument("--destructive", action="store_true", help="破坏性用例")

    # ── report ──
    p_report = sub.add_parser("report", help="生成报告")
    p_report.add_argument("mode", choices=["summary", "progress", "excel"])
    p_report.add_argument("--module", help="模块名")

    # ── agent ──
    p_agent = sub.add_parser("agent", help="Agent 调度与执行")
    p_agent.add_argument("action", choices=["run", "check", "next", "auto"],
                         help="run:执行Agent | check:检查前置条件 | next:推荐下一步 | auto:自动推进")
    p_agent.add_argument("agent_name", nargs="?", help="Agent 名称（run 模式必填，如 automation-agent）")
    p_agent.add_argument("--module", help="模块名")
    p_agent.add_argument("--page", help="页面名（页面级 Agent 必填）")
    p_agent.add_argument("--provider", "-p", default="claude",
                         choices=["claude", "openai", "ollama"],
                         help="LLM Provider（默认 claude）")
    p_agent.add_argument("--force", action="store_true", help="强制执行（auto 模式）")

    # ── skill ──
    p_skill = sub.add_parser("skill", help="Skill 执行")
    p_skill.add_argument("action", choices=["run", "list", "promote"],
                         help="run:执行Skill | list:列出可用Skill | promote:推广新版本")
    p_skill.add_argument("skill_id", nargs="?", help="Skill ID（run/promote 模式必填，如 test-design/page-analysis）")
    p_skill.add_argument("--input", "-i", help="用户输入/任务描述（run 模式必填）")
    p_skill.add_argument("--version", "-v", help="目标版本号（promote 模式必填，如 1.1）")
    p_skill.add_argument("--provider", "-p", default="claude",
                         choices=["claude", "openai", "ollama"],
                         help="LLM Provider（默认 claude）")
    p_skill.add_argument("--module", help="模块名（上下文注入用）")
    p_skill.add_argument("--page", help="页面名（上下文注入用）")
    p_skill.add_argument("--category", "-c", help="按分类筛选（list 模式）")

    # ── workflow ──
    p_wf = sub.add_parser("workflow", help="工作流引擎")
    p_wf.add_argument("action", choices=["run", "resume", "status"])
    p_wf.add_argument("workflow_id", nargs="?", help="工作流 ID")
    p_wf.add_argument("--module", help="模块名")
    p_wf.add_argument("--run-id", help="运行 ID（resume/status）")

    # ── rag ──
    p_rag = sub.add_parser("rag", help="RAG 检索")
    p_rag.add_argument("action", choices=["search", "index", "status"])
    p_rag.add_argument("query", nargs="*", help="搜索查询")
    p_rag.add_argument("--collection", "-c", help="集合名 (known_issues/tech_analysis/page_context/page_objects)")
    p_rag.add_argument("-n", type=int, default=5, help="返回数量")

    # ── bus ──
    p_bus = sub.add_parser("bus", help="事件总线")
    p_bus.add_argument("action", choices=["emit", "listen", "process"])
    p_bus.add_argument("event_type", nargs="?", help="事件类型（emit）")
    p_bus.add_argument("data", nargs="*", help="事件数据 key=value")

    # ── bug ──
    p_bug = sub.add_parser("bug", help="Bug 历史库")
    p_bug.add_argument("action", choices=["add", "list", "trends"])
    p_bug.add_argument("--module", help="模块名")
    p_bug.add_argument("--page", help="页面名")
    p_bug.add_argument("--error-type", help="异常类型")
    p_bug.add_argument("--root-cause", help="根因")
    p_bug.add_argument("--severity", choices=["high", "medium", "low"])
    p_bug.add_argument("--status", help="状态筛选")
    p_bug.add_argument("--matched-issue", help="关联已知问题 ID")
    p_bug.add_argument("--limit", type=int, default=20)

    # ── sop（用户友好别名，与 graph 完全等价）──
    p_sop = sub.add_parser("sop", help="完整 SOP 流水线（⭐ 推荐主入口）")
    p_sop.add_argument("action", choices=["run", "resume", "status", "list", "cleanup"],
                        help="run:执行完整SOP | resume:断点续跑 | status:查看状态 | list:列出runs | cleanup:清理")
    p_sop.add_argument("--module", "-m", help="模块名（run 模式必填）")
    p_sop.add_argument("--pages", help="页面列表，逗号分隔（如 alarm-config,unit-management）")
    p_sop.add_argument("--mode", default="full",
                        choices=["full", "resume", "status", "from-requirement", "from-test-design", "from-automation"],
                        help="运行模式（默认 full）")
    p_sop.add_argument("--provider", "-p", default="claude",
                        choices=["claude", "openai", "ollama"],
                        help="LLM Provider（默认 claude；DeepSeek 用户用 claude + ANTHROPIC_BASE_URL 环境变量）")
    p_sop.add_argument("--run-id", help="运行 ID（resume/status/cleanup 模式）")
    p_sop.add_argument("--limit", type=int, default=20, help="列出数量（list 模式）")
    p_sop.add_argument("--non-interactive", action="store_true",
                       help="非交互模式：自动通过 HITL 审批，输出 JSON 结果（Claude Code 集成用）")

    # ── graph（LangGraph 底层命令，与 sop 等价）──
    p_graph = sub.add_parser("graph", help="LangGraph 编排引擎（等价于 sop）")
    p_graph.add_argument("action", choices=["run", "resume", "status", "list", "cleanup"],
                        help="run:执行SOP编排 | resume:断点续跑 | status:查看状态 | list:列出runs | cleanup:清理")
    p_graph.add_argument("--module", "-m", help="模块名（run 模式必填）")
    p_graph.add_argument("--pages", help="页面列表，逗号分隔（如 alarm-config,unit-management）")
    p_graph.add_argument("--mode", default="full",
                        choices=["full", "resume", "status", "from-requirement", "from-test-design", "from-automation"],
                        help="运行模式（默认 full）")
    p_graph.add_argument("--provider", "-p", default="claude",
                        choices=["claude", "openai", "ollama"],
                        help="LLM Provider（默认 claude；DeepSeek 用户用 claude + ANTHROPIC_BASE_URL 环境变量）")
    p_graph.add_argument("--run-id", help="运行 ID（resume/status/cleanup 模式）")
    p_graph.add_argument("--limit", type=int, default=20, help="列出数量（list 模式）")
    p_graph.add_argument("--non-interactive", action="store_true",
                       help="非交互模式：自动通过 HITL 审批，输出 JSON 结果（Claude Code 集成用）")

    # ── sop-dev (Dev SOP 用户友好别名) ──
    p_sop_dev = sub.add_parser("sop-dev", help="开发 SOP 流水线 (9 Agent / 10 Phase)")
    p_sop_dev.add_argument("action", choices=["run", "resume", "status", "list"],
                          help="run:执行DevSOP | resume:断点续跑 | status:查看状态 | list:列出runs")
    p_sop_dev.add_argument("--module", "-m", help="模块名（run 模式必填）")
    p_sop_dev.add_argument("--mode", default="full",
                          choices=["full", "resume", "status", "from-architecture", "from-frontend", "from-backend", "review-only"],
                          help="运行模式（默认 full）")
    p_sop_dev.add_argument("--provider", "-p", default="claude",
                          choices=["claude", "openai", "ollama"],
                          help="LLM Provider（默认 claude）")
    p_sop_dev.add_argument("--run-id", help="运行 ID（resume/status 模式）")
    p_sop_dev.add_argument("--limit", type=int, default=20, help="列出数量（list 模式）")
    p_sop_dev.add_argument("--non-interactive", action="store_true",
                          help="非交互模式：自动通过 HITL 审批")

    # ── graph-dev (LangGraph 底层命令，与 sop-dev 等价) ──
    p_graph_dev = sub.add_parser("graph-dev", help="Dev LangGraph 编排引擎（等价于 sop-dev）")
    p_graph_dev.add_argument("action", choices=["run", "resume", "status", "list"],
                            help="run:执行DevSOP编排 | resume:断点续跑 | status:查看状态 | list:列出runs")
    p_graph_dev.add_argument("--module", "-m", help="模块名（run 模式必填）")
    p_graph_dev.add_argument("--pages", help="页面列表，逗号分隔（可选，默认自动发现）")
    p_graph_dev.add_argument("--mode", default="full",
                            choices=["full", "resume", "status", "from-architecture", "from-frontend", "from-backend", "review-only"],
                            help="运行模式（默认 full）")
    p_graph_dev.add_argument("--provider", "-p", default="claude",
                            choices=["claude", "openai", "ollama", "deepseek"],
                            help="LLM Provider（默认 claude）")
    p_graph_dev.add_argument("--run-id", help="运行 ID（resume/status 模式）")
    p_graph_dev.add_argument("--limit", type=int, default=20, help="列出数量（list 模式）")
    p_graph_dev.add_argument("--non-interactive", action="store_true",
                            help="非交互模式：自动通过 HITL 审批")

    # ── dashboard ──
    p_dash = sub.add_parser("dashboard", help="平台总览面板")

    # ── server ──
    p_server = sub.add_parser("server", help="服务管理")
    p_server.add_argument("action", choices=["start", "task", "queue", "cleanup"],
                          help="start:启动服务 | task:查询任务 | queue:队列统计 | cleanup:清理旧任务")
    p_server.add_argument("task_id", nargs="?", help="任务 ID（task 模式）")
    p_server.add_argument("--host", default="0.0.0.0", help="绑定地址（start 模式）")
    p_server.add_argument("--port", type=int, default=8000, help="端口（start 模式）")
    p_server.add_argument("--reload", action="store_true", help="热重载（start 模式，开发用）")
    p_server.add_argument("--hours", type=int, default=24, help="清理 N 小时前的记录（cleanup 模式）")

    # ── project register ──
    p_proj = sub.add_parser("project", help="项目管理")
    p_proj.add_argument("action", choices=["register", "list", "set"],
                        help="register:注册项目 | list:列出项目 | set:设置活跃项目")
    p_proj.add_argument("--id", help="项目 ID")
    p_proj.add_argument("--path", help="项目根目录路径")

    # ── errors ──
    p_errors = sub.add_parser("errors", help="错误日志 (P0-2: 结构化错误追踪)")
    p_errors.add_argument("action", choices=["recent", "summary", "clean"],
                         help="recent:最近错误 | summary:按组件汇总 | clean:清理旧记录")
    p_errors.add_argument("--component", "-c", help="按组件筛选（recent/summary）")
    p_errors.add_argument("--severity", "-s", choices=["debug", "info", "warning", "error", "critical"],
                         help="按严重级别筛选（recent）")
    p_errors.add_argument("--limit", "-n", type=int, default=20, help="返回条数（recent）")
    p_errors.add_argument("--days", "-d", type=int, default=7, help="汇总/清理的天数范围（summary/clean）")

    # ── trace ──
    p_trace = sub.add_parser("trace", help="追踪事件查询 (P1-1: 全链路追踪)")
    p_trace.add_argument("action", choices=["list", "summary", "stats", "board", "advise", "clean"],
                         help="list:查询事件 | summary:运行摘要 | clean:清理旧记录")
    p_trace.add_argument("--run-id", help="按运行 ID 筛选")
    p_trace.add_argument("--type", dest="type", choices=["llm_call", "skill_execution", "agent_decision", "milestone"],
                         help="按事件类型筛选")
    p_trace.add_argument("--skill", help="按 Skill ID 筛选（支持子串匹配）")
    p_trace.add_argument("--limit", "-n", type=int, default=20, help="返回条数（list）")
    p_trace.add_argument("--days", "-d", type=int, default=7, help="清理 N 天前的记录（clean）")

    # ── eval ──
    p_eval = sub.add_parser("eval", help="评估运行器 (P1-2: Skill 评估框架)")
    p_eval.add_argument("action", choices=["run", "agent", "summary"],
                        help="run:执行Skill评估 | agent:执行Agent评估 | summary:聚合摘要")
    p_eval.add_argument("target", nargs="?", help="Skill ID 或 Agent 名称")
    p_eval.add_argument("--input", "-i", help="用户输入/任务描述（run 模式必填）")
    p_eval.add_argument("--criteria", "-c", help="评估标准 JSON 字符串 (run 模式)")
    p_eval.add_argument("--provider", "-p", default="claude", choices=["claude", "openai", "ollama"],
                        help="LLM Provider（默认 claude）")
    p_eval.add_argument("--module", "-m", help="模块名（agent 模式）")
    p_eval.add_argument("--page", help="页面名（agent 模式）")
    p_eval.add_argument("--skill", "-s", help="按 Skill ID 筛选（summary 模式）")
    p_eval.add_argument("--run-id", help="按运行 ID 筛选（summary 模式）")

    # ── ab ──
    p_ab = sub.add_parser("ab", help="A/B 测试 (P1-3: Prompt 变体对比)")
    p_ab.add_argument("action", choices=["list", "compare", "batch"],
                      help="list:列出变体 | compare:单用例对比 | batch:批量对比")
    p_ab.add_argument("skill_id", nargs="?", help="Skill ID")
    p_ab.add_argument("--a", help="变体 A ID (compare/batch)")
    p_ab.add_argument("--b", help="变体 B ID (compare/batch)")
    p_ab.add_argument("--input", "-i", help="测试输入 (compare)")
    p_ab.add_argument("--criteria", "-c", help="评估标准 JSON (compare)")
    p_ab.add_argument("--cases", help="测试用例 YAML 文件 (batch)")
    p_ab.add_argument("--provider", "-p", default="claude", choices=["claude", "openai", "ollama"],
                      help="LLM Provider（默认 claude）")

    # ── regression ──
    p_reg = sub.add_parser("regression", help="回归测试 (P1-4: Golden Test 基线)")
    p_reg.add_argument("action", choices=["run", "list", "capture"],
                       help="run:执行回归测试 | list:列出用例 | capture:捕获基线")
    p_reg.add_argument("target", nargs="?", help="Case ID（capture 模式必填）")
    p_reg.add_argument("--tag", "-t", help="按 tag 筛选（run 模式，如 smoke/critical）")
    p_reg.add_argument("--skill", "-s", help="按 Skill ID 筛选（run/list 模式）")
    p_reg.add_argument("--provider", "-p", default="claude", choices=["claude", "openai", "ollama"],
                       help="LLM Provider（默认 claude）")

    # ── kpi (L4) ──
    p_kpi = sub.add_parser("kpi", help="治理KPI (L4: 指标仪表板)")
    p_kpi.add_argument("action", choices=["summary", "audit-all", "export"],
                       help="summary:KPI总览 | audit-all:一次性审计全部模块 | export:导出Excel报表")
    p_kpi.add_argument("--days", "-d", type=int, default=30, help="回溯天数")
    p_kpi.add_argument("--modules", "-m", help="模块列表，逗号分隔 (audit-all)")
    p_kpi.add_argument("--json", action="store_true", help="JSON输出")

    # ── inspect (Run Inspector) ──
    p_inspect = sub.add_parser("inspect", help="Run Inspector — 查看 Run 详情")
    p_inspect.add_argument("run_id", nargs="?", help="Run ID (省略则列出最近)")
    p_inspect.add_argument("--events", "-e", action="store_true", help="显示事件时间线")
    p_inspect.add_argument("--json", action="store_true", help="JSON 格式输出")
    p_inspect.add_argument("--limit", "-n", type=int, default=10, help="列出最近 N 个 run")

    # ── event (Event Inspector) ──
    p_event = sub.add_parser("event", help="Event Inspector — 查看平台事件")
    p_event.add_argument("action", nargs="?", default="list", choices=["list", "tail", "types"],
                         help="list:最近事件 | tail:实时跟踪 | types:事件类型统计")
    p_event.add_argument("--limit", "-n", type=int, default=20, help="显示数量")
    p_event.add_argument("--type", "-t", help="过滤事件类型")
    p_event.add_argument("--run-id", help="过滤 Run ID")
    p_event.add_argument("--json", action="store_true", help="JSON 输出")

    # ── testcase (测试用例导出) ──
    p_tc = sub.add_parser("testcase", help="测试用例Excel导出")
    p_tc.add_argument("module", help="模块名 (如 sales)")
    p_tc.add_argument("page", help="页面名 (如 customer)")
    p_tc.add_argument("--output", "-o", help="输出路径 (.xlsx)")

    args = parser.parse_args()

    if args.command == "check":
        cmd_check(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "sync":
        cmd_sync(args)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "report":
        cmd_report(args)
    elif args.command == "agent":
        cmd_agent(args)
    elif args.command == "skill":
        cmd_skill(args)
    elif args.command == "workflow":
        cmd_workflow(args)
    elif args.command == "rag":
        cmd_rag(args)
    elif args.command == "bus":
        cmd_bus(args)
    elif args.command == "bug":
        cmd_bug(args)
    elif args.command == "server":
        cmd_server(args)
    elif args.command == "project":
        if args.action == "register":
            if not args.path:
                print("ERROR: --path is required for project register")
                return 1
            return cmd_project_register(args)
        elif args.action == "list":
            import yaml
            index_path = GOVERNANCE / "context" / "project-index.yaml"
            if index_path.exists():
                index = yaml.safe_load(index_path.read_text(encoding="utf-8"))
                print(f"{'ID':<25} {'Path'}")
                print("-" * 60)
                for p in index.get("projects", []):
                    print(f"{p['id']:<25} {p.get('path', '?')}")
            else:
                print("No projects registered.")
            return 0
        elif args.action == "set":
            from aitest.platform.context import set_active_project
            if args.id:
                set_active_project(args.id)
                print(f"Active project set to: {args.id}")
            else:
                from aitest.platform.context import get_active_project_id
                print(f"Active project: {get_active_project_id()}")
            return 0
    elif args.command == "errors":
        cmd_errors(args)
    elif args.command == "trace":
        cmd_trace(args)
    elif args.command == "eval":
        cmd_eval(args)
    elif args.command == "ab":
        cmd_ab(args)
    elif args.command == "regression":
        cmd_regression(args)
    elif args.command == "testcase":
        cmd_testcase(args)
    elif args.command == "kpi":
        cmd_kpi(args)
    elif args.command == "sop":
        cmd_graph(args)  # sop 是 graph 的用户友好别名
    elif args.command == "graph":
        cmd_graph(args)
    elif args.command == "sop-dev":
        cmd_graph_dev(args)  # sop-dev 是 graph-dev 的用户友好别名
    elif args.command == "graph-dev":
        cmd_graph_dev(args)
    elif args.command == "dashboard":
        cmd_dashboard(args)
    elif args.command == "inspect":
        cmd_inspect(args)
    elif args.command == "event":
        cmd_event(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
