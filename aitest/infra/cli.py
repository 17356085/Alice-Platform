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

WORKSTUDY = get_workstudy()
GOVERNANCE = get_governance_dir()


def _zjsn():
    """Resolve test project root lazily. Returns fallback if not configured."""
    import os
    root = get_test_project_root()
    if root:
        return root
    # Fallback: look for ZJSN_Test in the WORKSTUDY parent directory
    return WORKSTUDY / "ZJSN_Test-master526"


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

    # Workflow runs
    from aitest.workflow_engine import RUNS_DIR
    if RUNS_DIR.exists():
        runs = sorted(RUNS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        print(f"\n[Workflows] {len(runs)} run(s)")
        for r in runs[:5]:
            print(f"  {r.stem} ({time.strftime('%m-%d %H:%M', time.localtime(r.stat().st_mtime))})")

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
    """工作流引擎。"""
    sys.path.insert(0, str(WORKSTUDY))
    from aitest.workflow_engine import WorkflowDef, topological_sort, WorkflowRunner, RUNS_DIR

    if args.action == "run":
        wf_path = GOVERNANCE / "workflows" / f"{args.workflow_id}.yaml"
        if not wf_path.exists():
            print(f"Workflow not found: {wf_path}")
            print("Available:")
            for wf in sorted((GOVERNANCE / "workflows").glob("*.yaml")):
                print(f"  {wf.stem}")
            return

        wf = WorkflowDef.from_yaml(wf_path)
        params = {}
        if args.module:
            params["module"] = args.module
        runner = WorkflowRunner(wf, params)
        state = runner.start()
        print(f"Workflow started: {state.run_id}")
        levels = topological_sort(wf.steps)
        for i, level in enumerate(levels):
            print(f"  Level {i}: {[s.id for s in level]}")
        ready = runner.get_next_steps()
        print(f"Ready: {[s.id for s in ready]}")

    elif args.action == "resume":
        if not args.run_id:
            runs = sorted(RUNS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if runs:
                args.run_id = runs[0].stem
                print(f"Resuming latest run: {args.run_id}")
            else:
                print("No runs to resume")
                return

        wf_id = args.run_id.rsplit("-", 1)[0]
        wf_path = GOVERNANCE / "workflows" / f"{wf_id}.yaml"
        if wf_path.exists():
            wf = WorkflowDef.from_yaml(wf_path)
            runner = WorkflowRunner(wf)
            runner.resume(args.run_id)
            progress = runner.progress()
            print(json.dumps(progress, ensure_ascii=False, indent=2))
        else:
            print(f"Cannot find workflow for run {args.run_id}")

    elif args.action == "status":
        if args.run_id:
            path = RUNS_DIR / f"{args.run_id}.json"
            if path.exists():
                with open(path, "r") as f:
                    print(json.dumps(json.load(f), ensure_ascii=False, indent=2))
            else:
                print(f"No run: {args.run_id}")
        else:
            if RUNS_DIR.exists():
                runs = sorted(RUNS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
                for r in runs[:10]:
                    print(f"  {r.stem}")


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
    from aitest.governance.event_bus import emit, list_pending, list_all, process_pending

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


def cmd_dashboard(args):
    """平台总览面板。"""
    sys.path.insert(0, str(WORKSTUDY))
    CONTEXT_MODULES = get_project_dir() / "modules"

    width = 70
    print()
    print("=" * width)
    print("  AI Test Platform — Dashboard")
    print("=" * width)

    # ── 1. 模块 SOP 状态 ──
    print(f"\n{'─' * width}")
    print("  Modules")
    print(f"{'─' * width}")

    from aitest.agents.agent_scheduler import AGENT_TRIGGERS
    from aitest.knowledge.rag_engine import get_chroma_client

    if (CONTEXT_MODULES).exists():
        print(f"  {'Module':<20} {'Phase':<12} {'Pages':<8} {'Code':<10}")
        print(f"  {'-'*18}   {'-'*10}   {'-'*6}   {'-'*8}")

        for mod_dir in sorted(CONTEXT_MODULES.iterdir()):
            if not mod_dir.is_dir():
                continue
            mod = mod_dir.name
            mc = (mod_dir / "MODULE_CONTEXT.md").exists()
            pages_dir = mod_dir / "pages"
            page_count = len([p for p in pages_dir.iterdir() if p.is_dir()]) if pages_dir.exists() else 0

            # 判断当前 Phase
            from aitest.agents.agent_scheduler import recommend_next_agent
            try:
                rec = recommend_next_agent(mod)
                phase = rec.get("phase", "?")
            except Exception as e:
                from aitest.infra.error_logger import log_error
                log_error("cli.cmd_dashboard", "recommend_agent", e, {"module": mod})
                phase = "?"

            # 代码状态
            zjsn = _zjsn()
            page_code = zjsn / "page" / f"{mod}_page"
            script_code = zjsn / "script" / mod
            code_icon = ""
            if page_code.exists() and script_code.exists():
                code_icon = "[OK]"
            elif page_code.exists() or script_code.exists():
                code_icon = "[!!]"
            else:
                code_icon = " -"

            mc_icon = "[OK]" if mc else "[XX]"
            print(f"  {mc_icon} {mod:<18} {phase:<12} {page_count:<8} {code_icon}")

    # ── 2. 任务队列 ──
    print(f"\n{'─' * width}")
    print("  Task Queue")
    print(f"{'─' * width}")

    from aitest.infra.task_queue import get_queue
    queue = get_queue()
    counts = queue.count_by_status()
    total = sum(counts.values())
    print(f"  Queued: {counts.get('queued', 0)} | Running: {counts.get('running', 0)} | "
          f"Completed: {counts.get('completed', 0)} | Failed: {counts.get('failed', 0)}")

    pending = queue.list_tasks(status="queued", limit=3)
    running = queue.list_tasks(status="running", limit=3)
    if pending:
        print(f"  Pending: {', '.join(t['agent'].replace('-agent','') for t in pending)}")
    if running:
        print(f"  Running: {', '.join(t['agent'].replace('-agent','') for t in running)}")

    # ── 3. RAG 知识库 ──
    print(f"\n{'─' * width}")
    print("  RAG Knowledge Base")
    print(f"{'─' * width}")

    try:
        client = get_chroma_client()
        colls = client.list_collections()
        total_docs = sum(c.count() for c in colls)
        print(f"  Collections: {len(colls)} | Documents: {total_docs}")
        for c in colls:
            print(f"    {c.name:<25} {c.count():>4} docs  {c.metadata.get('description', '')[:30]}")
    except Exception as e:
        print(f"  Status: Disconnected ({str(e)[:50]})")

    # ── 4. Event Bus ──
    print(f"\n{'─' * width}")
    print("  Event Bus")
    print(f"{'─' * width}")

    from aitest.governance.event_bus import list_pending, EVENT_DIR
    pending_events = list_pending()
    print(f"  Pending events: {len(pending_events)}")
    for evt in pending_events[:5]:
        print(f"    [{evt.type}] {evt.id} — {str(evt.data)[:60]}")

    # ── 5. Bug 历史 ──
    print(f"\n{'─' * width}")
    print("  Bug History")
    print(f"{'─' * width}")

    try:
        from aitest.testing.bug_history import list_bugs as list_bugs_fn, BUG_DB
        bugs = list_bugs_fn(limit=10)
        open_bugs = [b for b in bugs if b.get("status") == "open"]
        print(f"  Total: {len(bugs)} | Open: {len(open_bugs)}")
        if open_bugs:
            for b in open_bugs[:3]:
                print(f"    [{b.get('severity', '?')}] {b.get('module', '')}/{b.get('page', '')} — {b.get('error_type', '')[:40]}")
    except Exception as e:
        print(f"  Status: Unavailable ({str(e)[:50]})")

    # ── 6. Skill 能力分布 ──
    print(f"\n{'─' * width}")
    print("  Skills")
    print(f"{'─' * width}")

    from aitest.llm.skill_registry import get_skill_stats
    stats = get_skill_stats()
    print(f"  mechanical: {stats.get('mechanical', 0)} | low: {stats.get('low', 0)} | "
          f"medium: {stats.get('medium', 0)} | high: {stats.get('high', 0)}")

    from aitest.llm.provider import list_providers
    print(f"  LLM Providers: {', '.join(list_providers())}")

    print()
    print("=" * width)
    print("  aitest server start     — 启动 API 服务")
    print("  aitest agent run <name> --module=<m> — 执行 Agent")
    print("  aitest server queue     — 任务队列详情")
    print("=" * width)
    print()


def _run_preflight_gate(module: str, mode: str, pages: list[str]) -> None:
    """U9: SOP 门禁前置检查 — 在编排启动前验证前置条件。"""
    try:
        import subprocess
        zjsn = _zjsn()
        script = zjsn / "tools" / "check_sop_gate.py"
        if not script.exists():
            return  # 门禁脚本不存在，静默跳过

        # 根据 mode 确定最关键的 agent 进行检查
        mode_to_agent = {
            "full": "project-agent",
            "from-requirement": "requirement-agent",
            "from-test-design": "test-design-agent",
            "from-automation": "automation-agent",
        }
        agent = mode_to_agent.get(mode, "project-agent")

        result = subprocess.run(
            ["python", str(script), "--module", module, "--agent", agent, "--json"],
            capture_output=True, text=True, timeout=30,
            cwd=str(zjsn),
        )
        if result.returncode != 0 and result.stdout:
            import json as _json
            try:
                data = _json.loads(result.stdout)
                if data.get("blocked"):
                    print(f"  [GATE BLOCKED] {data.get('summary', '')}")
                    print(f"  [RECOMMEND]    {data.get('recommendation', '')}")
                    # 不阻塞执行 — warning only (P1 阶段)
            except Exception:
                pass
    except Exception:
        pass  # 门禁检查失败不阻塞编排


def cmd_graph(args):
    """LangGraph 编排引擎。"""
    sys.path.insert(0, str(WORKSTUDY))
    from aitest.graphs.state import create_initial_state, MODE_SKIP_MAP
    from aitest.graphs.checkpoint import get_checkpointer, list_runs as graph_list_runs, get_latest_state
    from aitest.graphs.sop_graph import build_sop_graph

    if args.action == "run":
        # ── graph run: 执行 SOP 编排 ──
        module = args.module
        pages = args.pages.split(",") if args.pages else []
        mode = args.mode or "full"
        provider = args.provider or "claude"

        if not module:
            print("Error: --module is required")
            return

        print(f"LangGraph SOP Engine")
        print(f"  Module:   {module}")
        print(f"  Pages:    {pages or '(auto-discover)'}")
        print(f"  Mode:     {mode}")
        print(f"  Provider: {provider}")
        print()

        # ★ U9: Gate 检查前置 — 在编排启动前验证前置条件
        if mode != "status":
            _run_preflight_gate(module, mode, pages)

        # 构建初始状态
        initial_state = create_initial_state(
            module=module,
            pages=pages,
            mode=mode,
            provider=provider,
        )

        # 编译图
        checkpointer = get_checkpointer()
        graph = build_sop_graph()
        compiled = graph.compile(checkpointer=checkpointer)

        thread = {"configurable": {"thread_id": initial_state["run_id"]}}
        non_interactive = getattr(args, 'non_interactive', False)

        if not non_interactive:
            print(f"Run ID: {initial_state['run_id']}")
            print(f"Skip phases: {initial_state['skip_phases']}")
            print("-" * 60)

        # 流式执行（含 HITL interrupt 处理）
        from langgraph.types import Command

        hitl_log = []  # 记录 HITL 决策（non-interactive 用）
        try:
            for event in compiled.stream(initial_state, thread, stream_mode="updates"):
                # ── HITL interrupt 处理 ──
                if "__interrupt__" in event:
                    interrupt_data = event["__interrupt__"]
                    for item in interrupt_data:
                        payload = getattr(item, 'value', None) or item
                        if isinstance(payload, dict):
                            itype = payload.get('type', 'Approval Required')
                            if non_interactive:
                                # ★ 非交互模式：自动选第一个选项（approve/force_continue 等）
                                opts = payload.get('options', ['approve'])
                                answer = opts[0] if opts else "approve"
                                hitl_log.append({
                                    "type": itype,
                                    "decision": f"auto_{answer}",
                                    "reason": "non-interactive mode",
                                    "details": str(payload.get('hint', ''))[:200],
                                })
                            else:
                                print()
                                print(f"  [HITL] {itype}")
                                print(f"  Cycle:  {payload.get('cycle', '?')}")
                                print(f"  Fix:    {payload.get('fix_summary', '')[:200]}")
                                print(f"  Options: {payload.get('options', ['approve', 'reject'])}")
                                answer = input("  > approve/reject/skip: ").strip().lower()
                            # Resume
                            for resume_event in compiled.stream(
                                Command(resume=answer), thread, stream_mode="updates"
                            ):
                                for rn, ru in resume_event.items():
                                    if rn == "__interrupt__":
                                        continue
                                    completed = ru.get("completed_phases", []) if isinstance(ru, dict) else []
                                    if completed and not non_interactive:
                                        print(f"  [{rn}] {completed}")
                        else:
                            if not non_interactive:
                                print(f"  [HITL] Interrupt (raw): {str(payload)[:200]}")
                    continue

                # ── 正常事件处理 ──
                for node_name, update in event.items():
                    if non_interactive:
                        continue  # 非交互模式不打印进度

                    phase = update.get("current_phase", "") if isinstance(update, dict) else ""
                    status = update.get("status", "") if isinstance(update, dict) else ""

                    if node_name == "entry":
                        print(f"  [entry]     Mode={mode}, Skip={initial_state['skip_phases']}")
                    elif node_name == "preflight":
                        pages_found = update.get("pages", []) if isinstance(update, dict) else []
                        completed = update.get("completed_phases", []) if isinstance(update, dict) else []
                        print(f"  [preflight] Pages: {pages_found}")
                        if completed:
                            print(f"              Completed: {completed}")
                    elif node_name == "exit":
                        final_status = update.get("status", "?") if isinstance(update, dict) else "?"
                        print(f"  [exit]      Status: {final_status}")
                    elif node_name.endswith("_agent"):
                        completed_phases = update.get("completed_phases", []) if isinstance(update, dict) else []
                        failed_phases = update.get("failed_phases", []) if isinstance(update, dict) else []
                        fatal = update.get("fatal_error") if isinstance(update, dict) else None
                        if completed_phases:
                            print(f"  [{node_name}] Completed: {completed_phases}")
                        if failed_phases:
                            print(f"  [{node_name}] Failed: {failed_phases}")
                        if fatal:
                            print(f"  [{node_name}] FATAL: {fatal}")
                    else:
                        if phase:
                            print(f"  [{node_name}] Phase={phase}")

            # 获取最终状态
            final = compiled.get_state(thread)
            if final and final.values:
                fv = final.values
                if non_interactive:
                    # ★ 输出结构化 JSON（Claude Code 可直接解析）
                    result = {
                        "status": fv.get("status", "?"),
                        "module": fv.get("module", module),
                        "run_id": initial_state["run_id"],
                        "completed_phases": fv.get("completed_phases", []),
                        "failed_phases": fv.get("failed_phases", []),
                        "pages_processed": fv.get("pages", []),
                        "fatal_error": fv.get("fatal_error"),
                        "hitl_decisions": hitl_log,
                        "engine": "langgraph",
                    }
                    import json as _json
                    print(_json.dumps(result, ensure_ascii=False, indent=2))
                else:
                    print("-" * 60)
                    print(f"Final: {fv.get('status', '?')}")
                    print(f"  Completed phases: {fv.get('completed_phases', [])}")
                    print(f"  Failed phases: {fv.get('failed_phases', [])}")
                    if fv.get("fatal_error"):
                        print(f"  Fatal error: {fv['fatal_error']}")

        except KeyboardInterrupt:
            print("\n  Interrupted. Run state saved. Resume with:")
            print(f"  aitest graph resume --run-id={initial_state['run_id']}")
        except Exception as e:
            print(f"\n  Error: {e}")
            import traceback
            traceback.print_exc()

    elif args.action == "resume":
        # ── graph resume: 断点续跑 ──
        run_id = args.run_id
        if not run_id:
            runs = graph_list_runs()
            if runs:
                run_id = runs[0]["run_id"]
                print(f"Resuming latest run: {run_id}")
            else:
                print("No runs to resume")
                return

        checkpointer = get_checkpointer()
        graph = build_sop_graph()
        compiled = graph.compile(checkpointer=checkpointer)

        thread = {"configurable": {"thread_id": run_id}}
        current = compiled.get_state(thread)

        if not current or not current.values:
            print(f"No state found for run: {run_id}")
            return

        state = current.values
        print(f"Resuming: {run_id}")
        print(f"  Module: {state.get('module', '?')}")
        print(f"  Status: {state.get('status', '?')}")
        print(f"  Completed: {state.get('completed_phases', [])}")
        print(f"  Current phase: {state.get('current_phase', '?')}")
        print("-" * 60)

        non_interactive = getattr(args, 'non_interactive', False)
        hitl_log = []
        try:
            from langgraph.types import Command

            for event in compiled.stream(None, thread, stream_mode="updates"):
                # ── HITL interrupt ──
                if "__interrupt__" in event:
                    for item in event["__interrupt__"]:
                        payload = getattr(item, 'value', None) or item
                        if isinstance(payload, dict):
                            itype = payload.get('type', 'Approval')
                            if non_interactive:
                                # ★ 非交互模式：自动选第一个选项
                                opts = payload.get('options', ['approve'])
                                answer = opts[0] if opts else "approve"
                                hitl_log.append({
                                    "type": itype,
                                    "decision": f"auto_{answer}",
                                    "reason": "non-interactive mode",
                                    "details": str(payload.get('hint', ''))[:200],
                                })
                            else:
                                print(f"\n  [HITL] {itype}")
                                print(f"  Fix: {payload.get('fix_summary', '')[:200]}")
                                answer = input("  > approve/reject/skip: ").strip().lower()
                            for resume_event in compiled.stream(
                                Command(resume=answer), thread, stream_mode="updates"
                            ):
                                for rn, ru in resume_event.items():
                                    if rn == "__interrupt__":
                                        continue
                                    completed = ru.get("completed_phases", []) if isinstance(ru, dict) else []
                                    if completed and not non_interactive:
                                        print(f"  [{rn}] {completed}")
                    continue

                for node_name, update in event.items():
                    if non_interactive:
                        continue
                    if node_name == "exit":
                        print(f"  [exit] Status: {update.get('status', '?') if isinstance(update, dict) else '?'}")
                    else:
                        completed = update.get("completed_phases", []) if isinstance(update, dict) else []
                        if completed:
                            print(f"  [{node_name}] Completed: {completed}")

            # Output final result
            final = compiled.get_state(thread)
            if final and final.values:
                fv = final.values
                if non_interactive:
                    import json as _json
                    result = {
                        "status": fv.get("status", "?"),
                        "module": fv.get("module", state.get('module', '?')),
                        "run_id": run_id,
                        "completed_phases": fv.get("completed_phases", []),
                        "failed_phases": fv.get("failed_phases", []),
                        "pages_processed": fv.get("pages", []),
                        "fatal_error": fv.get("fatal_error"),
                        "hitl_decisions": hitl_log,
                        "engine": "langgraph",
                    }
                    print(_json.dumps(result, ensure_ascii=False, indent=2))
        except KeyboardInterrupt:
            print(f"\n  Interrupted. Resume again with:")
            print(f"  aitest graph resume --run-id={run_id}")

    elif args.action == "status":
        # ── graph status: 查看运行状态 ──
        run_id = args.run_id
        if run_id:
            state = get_latest_state(run_id)
            if state:
                print(f"Run: {run_id}")
                print(f"  Module: {state.get('module', '?')}")
                print(f"  Status: {state.get('status', '?')}")
                print(f"  Mode: {state.get('mode', '?')}")
                print(f"  Completed phases: {state.get('completed_phases', [])}")
                print(f"  Failed phases: {state.get('failed_phases', [])}")
                print(f"  Current phase: {state.get('current_phase', '?')}")
                print(f"  Pages: {state.get('pages', [])}")
            else:
                print(f"No state found for run: {run_id}")
        else:
            runs = graph_list_runs()
            if runs:
                print(f"Recent runs ({len(runs)}):")
                for r in runs:
                    print(f"  {r['run_id']}  ({r.get('updated_at', '?')})")
            else:
                print("No runs found.")

    elif args.action == "list":
        # ── graph list: 列出所有 runs ──
        runs = graph_list_runs(limit=args.limit or 20)
        if runs:
            print(f"Runs ({len(runs)}):")
            for r in runs:
                print(f"  {r['run_id']}  ({r.get('updated_at', '?')})")
        else:
            print("No runs found.")

    elif args.action == "cleanup":
        # ── graph cleanup: 清理旧 runs ──
        from aitest.graphs.checkpoint import cleanup_run
        run_id = args.run_id
        if run_id:
            ok = cleanup_run(run_id)
            print(f"Cleanup {run_id}: {'OK' if ok else 'Failed'}")
        else:
            print("Usage: aitest graph cleanup --run-id=<id>")


def cmd_graph_dev(args):
    """Dev SOP LangGraph 编排引擎 — 9 Agent 开发流水线。"""
    sys.path.insert(0, str(WORKSTUDY))
    from aitest.graphs_dev.state_dev import create_initial_state_dev, DEV_MODE_SKIP_MAP
    from aitest.graphs_dev.sop_graph_dev import build_compiled_dev_graph
    from aitest.graphs.checkpoint import get_checkpointer, list_runs as graph_list_runs, get_latest_state

    if args.action == "run":
        module = args.module
        mode = args.mode or "full"
        provider = args.provider or "claude"

        if not module:
            print("Error: --module is required")
            return

        print(f"DevSOP LangGraph Engine (9 Agent / 10 Phase)")
        print(f"  Module:   {module}")
        print(f"  Mode:     {mode}")
        print(f"  Provider: {provider}")
        print()

        initial_state = create_initial_state_dev(
            module=module, mode=mode, provider=provider,
        )

        checkpointer = get_checkpointer()
        compiled = build_compiled_dev_graph(checkpointer=checkpointer)
        thread = {"configurable": {"thread_id": initial_state["run_id"]}}
        non_interactive = getattr(args, 'non_interactive', False)

        if not non_interactive:
            print(f"Run ID: {initial_state['run_id']}")
            print(f"Phases: {[p for p in ['Plan','Requirements','Architecture','Component Design','Frontend Impl','Backend Impl','Code Review','Dev Test','Debug & Fix','Build'] if p not in initial_state['skip_phases']]}")
            print("-" * 60)

        hitl_log = []
        try:
            from langgraph.types import Command

            for event in compiled.stream(initial_state, thread, stream_mode="updates"):
                if "__interrupt__" in event:
                    for item in event["__interrupt__"]:
                        payload = getattr(item, 'value', None) or item
                        if isinstance(payload, dict):
                            itype = payload.get('type', 'Approval Required')
                            if non_interactive:
                                opts = payload.get('options', ['approve'])
                                answer = opts[0] if opts else "approve"
                                hitl_log.append({"type": itype, "decision": f"auto_{answer}", "reason": "non-interactive"})
                            else:
                                print(f"\n  [HITL] {itype}")
                                print(f"  Options: {payload.get('options', ['approve', 'reject'])}")
                                answer = input("  > approve/reject/skip: ").strip().lower()
                            for resume_event in compiled.stream(Command(resume=answer), thread, stream_mode="updates"):
                                for rn, ru in resume_event.items():
                                    if rn == "__interrupt__":
                                        continue
                                    completed = ru.get("completed_phases", []) if isinstance(ru, dict) else []
                                    if completed and not non_interactive:
                                        print(f"  [{rn}] {completed}")
                    continue

                for node_name, update in event.items():
                    if non_interactive:
                        continue
                    phase = update.get("current_phase", "") if isinstance(update, dict) else ""
                    completed = update.get("completed_phases", []) if isinstance(update, dict) else []
                    if node_name == "entry":
                        print(f"  [entry]     Mode={mode}")
                    elif node_name == "exit":
                        print(f"  [exit]      Status: {update.get('status', '?') if isinstance(update, dict) else '?'}")
                    elif completed:
                        print(f"  [{node_name}] Completed: {completed}")
                    elif phase:
                        print(f"  [{node_name}] Phase={phase}")

            final = compiled.get_state(thread)
            if final and final.values:
                fv = final.values
                if non_interactive:
                    import json as _json
                    result = {
                        "status": fv.get("status", "?"),
                        "module": fv.get("module", module),
                        "run_id": initial_state["run_id"],
                        "completed_phases": fv.get("completed_phases", []),
                        "failed_phases": fv.get("failed_phases", []),
                        "fatal_error": fv.get("fatal_error"),
                        "hitl_decisions": hitl_log,
                        "engine": "langgraph-dev",
                    }
                    print(_json.dumps(result, ensure_ascii=False, indent=2))
                else:
                    print("-" * 60)
                    print(f"Final: {fv.get('status', '?')}")
                    print(f"  Completed phases: {fv.get('completed_phases', [])}")
                    print(f"  Failed phases: {fv.get('failed_phases', [])}")

        except KeyboardInterrupt:
            print(f"\n  Interrupted. Resume with:")
            print(f"  aitest sop-dev resume --run-id={initial_state['run_id']}")
        except Exception as e:
            print(f"\n  Error: {e}")
            import traceback
            traceback.print_exc()

    elif args.action == "resume":
        run_id = args.run_id
        if not run_id:
            runs = graph_list_runs()
            if runs:
                run_id = runs[0]["run_id"]
                print(f"Resuming latest run: {run_id}")
            else:
                print("No runs to resume")
                return

        checkpointer = get_checkpointer()
        compiled = build_compiled_dev_graph(checkpointer=checkpointer)
        thread = {"configurable": {"thread_id": run_id}}
        current = compiled.get_state(thread)

        if not current or not current.values:
            print(f"No state found for run: {run_id}")
            return

        state = current.values
        print(f"Resuming: {run_id}")
        print(f"  Module: {state.get('module', '?')}")
        print(f"  Status: {state.get('status', '?')}")
        print(f"  Completed: {state.get('completed_phases', [])}")
        print("-" * 60)

        non_interactive = getattr(args, 'non_interactive', False)
        try:
            from langgraph.types import Command
            for event in compiled.stream(None, thread, stream_mode="updates"):
                if "__interrupt__" in event:
                    for item in event["__interrupt__"]:
                        payload = getattr(item, 'value', None) or item
                        if isinstance(payload, dict):
                            if non_interactive:
                                opts = payload.get('options', ['approve'])
                                answer = opts[0] if opts else "approve"
                            else:
                                print(f"\n  [HITL] {payload.get('type', 'Approval')}")
                                answer = input("  > approve/reject/skip: ").strip().lower()
                            for resume_event in compiled.stream(Command(resume=answer), thread, stream_mode="updates"):
                                for rn, ru in resume_event.items():
                                    if rn == "__interrupt__":
                                        continue
                                    completed = ru.get("completed_phases", []) if isinstance(ru, dict) else []
                                    if completed and not non_interactive:
                                        print(f"  [{rn}] {completed}")
                    continue
                for node_name, update in event.items():
                    if non_interactive:
                        continue
                    if node_name == "exit":
                        print(f"  [exit] Status: {update.get('status', '?') if isinstance(update, dict) else '?'}")
                    else:
                        completed = update.get("completed_phases", []) if isinstance(update, dict) else []
                        if completed:
                            print(f"  [{node_name}] Completed: {completed}")

            final = compiled.get_state(thread)
            if final and final.values and non_interactive:
                import json as _json
                fv = final.values
                result = {
                    "status": fv.get("status", "?"),
                    "module": fv.get("module", state.get('module', '?')),
                    "run_id": run_id,
                    "completed_phases": fv.get("completed_phases", []),
                    "failed_phases": fv.get("failed_phases", []),
                    "fatal_error": fv.get("fatal_error"),
                    "engine": "langgraph-dev",
                }
                print(_json.dumps(result, ensure_ascii=False, indent=2))
        except KeyboardInterrupt:
            print(f"\n  Interrupted. Resume again with:")
            print(f"  aitest sop-dev resume --run-id={run_id}")

    elif args.action == "status":
        run_id = args.run_id
        if run_id:
            state = get_latest_state(run_id)
            if state:
                print(f"Run: {run_id}")
                print(f"  Module: {state.get('module', '?')}")
                print(f"  Status: {state.get('status', '?')}")
                print(f"  Completed phases: {state.get('completed_phases', [])}")
                print(f"  Failed phases: {state.get('failed_phases', [])}")
            else:
                print(f"No state found for run: {run_id}")
        else:
            runs = graph_list_runs()
            if runs:
                print(f"Recent runs ({len(runs)}):")
                for r in runs:
                    print(f"  {r['run_id']}  ({r.get('updated_at', '?')})")
            else:
                print("No runs found.")

    elif args.action == "list":
        runs = graph_list_runs(limit=args.limit or 20)
        if runs:
            print(f"Runs ({len(runs)}):")
            for r in runs:
                print(f"  {r['run_id']}  ({r.get('updated_at', '?')})")
        else:
            print("No runs found.")


def cmd_errors(args):
    """错误日志查看与清理 (P0-2)。"""
    sys.path.insert(0, str(WORKSTUDY))
    from aitest.infra.error_logger import list_recent, get_summary, cleanup_old

    if args.action == "recent":
        entries = list_recent(
            limit=args.limit or 20,
            severity=args.severity,
            component=args.component,
        )
        if not entries:
            print("No errors recorded.")
            return

        print(f"\nRecent errors ({len(entries)}):")
        print(f"{'─'*70}")
        for entry in entries:
            ts = entry.get("timestamp", "?")[:19]
            comp = entry.get("component", "?")
            op = entry.get("operation", "?")
            err_type = entry.get("error_type", "?")
            msg = entry.get("error_message", "")[:80]
            sev = entry.get("severity", "?")
            sev_icon = {"error": "[E]", "critical": "[!!]", "warning": "[W]", "info": "[I]", "debug": "[D]"}.get(sev, "[?]")
            print(f"  {sev_icon} {ts} | {comp}.{op}: {err_type}: {msg}")
        print()

    elif args.action == "summary":
        summary = get_summary(days=args.days or 7)
        print(f"\nError Summary (since {summary.get('since', '?')[:10]}):")
        print(f"  Total: {summary['total']}")
        print(f"\n  By Component:")
        for comp, count in summary.get("by_component", {}).items():
            bar = "█" * min(count, 40)
            print(f"    {comp:<40} {count:>4} {bar}")
        print(f"\n  By Severity:")
        for sev, count in summary.get("by_severity", {}).items():
            print(f"    {sev:<10} {count}")
        print()

    elif args.action == "clean":
        deleted = cleanup_old(days=args.days or 7)
        print(f"Cleaned up {deleted} old error entries (older than {args.days or 7} days).")


def cmd_server(args):
    """服务管理。"""
    if args.action == "start":
        import uvicorn
        # 先加载 .env 再导入 app，确保 provider.py 在 uvicorn 进程中有正确的环境变量
        from dotenv import load_dotenv
        from pathlib import Path
        _env = Path.cwd() / ".env"
        if _env.exists():
            load_dotenv(_env)
        print("Starting AITest Platform server on http://0.0.0.0:8000")
        print("API docs: http://localhost:8000/docs")
        print("Chat UI:  http://localhost:8000/chat")
        uvicorn.run(
            "aitest.server.main:app",
            host=args.host or "0.0.0.0",
            port=args.port or 8000,
            reload=args.reload,
        )

    elif args.action == "task":
        task_id = args.task_id
        if not task_id:
            print("Usage: aitest server task <task_id>")
            return

        from aitest.infra.task_queue import get_queue
        queue = get_queue()
        task = queue.get(task_id)

        if not task:
            print(f"Task not found: {task_id}")
            return

        print(f"Task: {task['id']}")
        print(f"Agent: {task['agent']}")
        print(f"Module: {task['module']}/{task['page']}")
        print(f"Status: {task['status']}")
        print(f"Provider: {task['provider']}")

        if task["status"] == "completed":
            result = task.get("result", {})
            print(f"Skills: {result.get('skills_executed', 'N/A')}")
            print(f"Tokens: {result.get('total_tokens', {})}")
            print(f"Elapsed: {result.get('total_elapsed', 'N/A')}s")
        elif task["status"] == "failed":
            print(f"Error: {task.get('error_msg', 'Unknown')}")

    elif args.action == "queue":
        from aitest.infra.task_queue import get_queue
        queue = get_queue()
        counts = queue.count_by_status()
        print("Task Queue Stats:")
        for status, count in counts.items():
            print(f"  {status}: {count}")

        recent = queue.list_tasks(limit=10)
        if recent:
            print(f"\nRecent tasks ({len(recent)}):")
            for t in recent:
                status_icon = {"queued": "[..]", "running": "[>>]", "completed": "[OK]", "failed": "[XX]"}.get(t["status"], "[??]")
                print(f"  {status_icon} {t['id'][:18]} | {t['agent']:25s} | {t['module']}/{t['page']}")

    elif args.action == "cleanup":
        from aitest.infra.task_queue import get_queue
        queue = get_queue()
        deleted = queue.cleanup(older_than_hours=args.hours or 24)
        print(f"Cleaned up {deleted} old tasks")


def cmd_bug(args):
    """Bug 历史库。"""
    sys.path.insert(0, str(WORKSTUDY))
    from aitest.testing.bug_history import (
        add_bug, list_bugs, get_trends, BUG_DB
    )

    if args.action == "add":
        bug_id = add_bug(
            module=args.module or "",
            page=args.page or "",
            error_type=args.error_type or "",
            root_cause=args.root_cause or "",
            severity=args.severity or "medium",
            status="open",
            matched_issue=args.matched_issue or "",
        )
        print(f"Bug added: {bug_id}")

    elif args.action == "list":
        bugs = list_bugs(
            module=args.module,
            severity=args.severity,
            status=args.status,
            limit=args.limit or 20,
        )
        print(f"\nBug History ({len(bugs)} records):\n")
        for b in bugs:
            print(f"  [{b['id']}] {b['date']} | {b['module']}/{b['page']}")
            print(f"    {b['error_type']} → {b['root_cause'][:60]}")
            print(f"    severity={b['severity']} status={b['status']} matched={b.get('matched_issue', 'N/A')}")
            print()

    elif args.action == "trends":
        trends = get_trends(args.module)
        print(f"\nBug Trends{f' for {args.module}' if args.module else ''}:\n")
        for t in trends:
            print(f"  {t['period']}: {t['total']} bugs (open={t['open']}, fixed={t['fixed']})")


def cmd_testcase(args):
    """测试用例 Excel 导出。"""
    sys.path.insert(0, str(WORKSTUDY))
    from aitest.testing.testcase_exporter import export_testcases_to_excel
    path = export_testcases_to_excel(args.module, args.page, args.output)
    print(f"Exported: {path}")


def cmd_kpi(args):
    """L4: Governance KPI 仪表板"""
    sys.path.insert(0, str(WORKSTUDY))
    from aitest.governance.governance_kpi import run_kpi_summary
    from aitest.governance.scheduled_audit import run_all_audits, discover_modules

    if args.action == "summary":
        run_kpi_summary(days=args.days or 30, json_output=args.json)
    elif args.action == "audit-all":
        modules = args.modules.split(",") if args.modules else discover_modules()
        print(f"Auditing {len(modules)} modules...")
        results = run_all_audits(modules)
        if args.json:
            import json
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            state_drifts = sum(r.get("drift_count", 0) for r in results["state_audits"].values())
            sop_v = sum(r.get("violations", 0) for r in results["sop_audits"].values())
            print(f"\n{len(modules)} modules: {state_drifts} drifts, {sop_v} SOP violations")
    elif args.action == "export":
        from aitest.governance.governance_kpi import export_to_excel
        path = export_to_excel(days=args.days or 30)
        print(f"Exported: {path}")
    else:
        print("Usage: aitest kpi summary|audit-all|export [--days=30] [--modules=m1,m2] [--json]")


def cmd_regression(args):
    """回归测试运行器 (P1-4)"""
    sys.path.insert(0, str(WORKSTUDY))
    from aitest.testing.regression import RegressionRunner

    if args.action == "list":
        runner = RegressionRunner()
        cases = runner.list_cases(skill_id=args.skill or None)
        if not cases:
            print("No regression test cases found.")
            print(f"Test cases are defined in: governance/tests/regression/test_cases.yaml")
            return

        print(f"\n{'='*65}")
        print(f"  Regression Test Cases — {len(cases)} total")
        print(f"{'='*65}")
        for c in cases:
            tags = ", ".join(c["tags"])
            baseline_icon = "📄" if c["has_baseline"] else "❌"
            print(f"\n  [{c['id']}] {baseline_icon}")
            print(f"    skill:  {c['skill_id']}")
            print(f"    desc:   {c['description']}")
            print(f"    tags:   {tags}")

    elif args.action == "run":
        runner = RegressionRunner(provider=args.provider)
        results = runner.run_all(
            tag=args.tag or None,
            skill_id=args.skill or None,
        )

        summary = runner.summary()
        print(f"\n{'='*60}")
        print(f"  Regression Results")
        print(f"{'='*60}")
        print(f"  Total:   {summary['total']}")
        print(f"  Passed:  {summary['passed']}")
        print(f"  Failed:  {summary['failed']}")
        print(f"  Rate:    {summary['pass_rate']:.0%}")
        print(f"  Avg Score: {summary['avg_score']:.2f}")

        if summary.get("deviations"):
            print(f"\n  Failures:")
            for d in summary["deviations"]:
                print(f"    [{d['case_id']}]")
                for dev in d["deviations"][-5:]:
                    print(f"      - {dev}")

        if summary.get("by_skill"):
            print(f"\n  By Skill:")
            for sid, stats in summary["by_skill"].items():
                pr = f"{stats['passed']}/{stats['total']}"
                print(f"    {sid}: {pr}")

    elif args.action == "capture":
        if not args.target:
            print("Error: Case ID is required for capture")
            print("Usage: aitest regression capture <case_id>")
            return

        runner = RegressionRunner(provider=args.provider)
        try:
            path = runner.capture_baseline(args.target)
            print(f"Baseline captured: {path}")
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Capture failed: {e}")


def cmd_ab(args):
    """A/B 测试运行器 (P1-3)"""
    sys.path.insert(0, str(WORKSTUDY))
    from aitest.llm.skill_loader import list_variants

    if args.action == "list":
        skill_id = args.skill_id or None
        variants = list_variants(skill_id)
        if not variants:
            print(f"No variants found{f' for {skill_id}' if skill_id else ''}.")
            print("Variants are registered in governance/skills/skill-registry.yaml")
            return

        print(f"\n{'='*60}")
        print(f"  Prompt Variants{f' — {skill_id}' if skill_id else ''}")
        print(f"{'='*60}")
        for v in variants:
            tags = ", ".join(v.tags) if v.tags else "none"
            print(f"\n  [{v.variant_id}] v{v.version}")
            print(f"    skill:  {v.skill_id}")
            print(f"    tags:   {tags}")
            print(f"    desc:   {v.description}")

    elif args.action == "compare":
        if not args.skill_id:
            print("Error: Skill ID is required")
            return
        if not args.a or not args.b:
            print("Error: --a and --b (variant IDs) are required")
            return
        if not args.input:
            print("Error: --input is required")
            return

        criteria = {}
        if args.criteria:
            try:
                criteria = json.loads(args.criteria)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid criteria JSON: {e}")
                return

        from aitest.agents.ab_test import ABTestRunner
        runner = ABTestRunner(provider=args.provider)
        result = runner.compare(
            skill_id=args.skill_id,
            variant_a=args.a,
            variant_b=args.b,
            test_input=args.input,
            criteria=criteria,
        )

        print(f"\n{'='*60}")
        print(f"  A/B Test — {result.skill_id}")
        print(f"{'='*60}")
        print(f"  A: {result.variant_a}  vs  B: {result.variant_b}")
        print(f"  Winner:      {result.winner}")
        print(f"  Score diff:  {result.score_diff:+.3f}  (A={result.run_a.get('score',0):.2f} B={result.run_b.get('score',0):.2f})")
        print(f"  Cost diff:   ${result.cost_diff:+.6f}")
        print(f"  Latency diff: {result.latency_diff_ms:+d}ms")
        if result.run_a.get("errors"):
            print(f"\n  A errors:")
            for e in result.run_a["errors"][-5:]:
                print(f"    - {e}")
        if result.run_b.get("errors"):
            print(f"\n  B errors:")
            for e in result.run_b["errors"][-5:]:
                print(f"    - {e}")

    elif args.action == "batch":
        if not args.skill_id:
            print("Error: Skill ID is required")
            return
        if not args.a or not args.b:
            print("Error: --a and --b (variant IDs) are required")
            return
        if not args.cases:
            print("Error: --cases <yaml-file> is required for batch mode")
            return

        from aitest.agents.ab_test import ABTestRunner
        runner = ABTestRunner(provider=args.provider)
        cases = runner.load_cases_from_yaml(args.cases)
        results = runner.batch_compare(
            skill_id=args.skill_id,
            variant_a=args.a,
            variant_b=args.b,
            test_cases=cases,
        )

        summary = runner.summary()
        print(f"\n{'='*60}")
        print(f"  A/B Batch — {args.skill_id} ({len(results)} cases)")
        print(f"{'='*60}")
        for i, r in enumerate(results):
            print(f"  [{i+1}] {r.winner} | score={r.score_diff:+.3f} | cost=${r.cost_diff:+.6f}")
        print(f"\n  Summary: {summary['recommendation']}")


def cmd_eval(args):
    """Skill 评估运行器 (P1-2)"""
    sys.path.insert(0, str(WORKSTUDY))
    from aitest.testing.evaluator import EvalRunner

    if args.action == "run":
        if not args.target:
            print("Error: Skill ID is required for eval run")
            print("Usage: aitest eval run <skill_id> --input=<text> [--criteria=<json>]")
            return
        if not args.input:
            print("Error: --input is required for eval run")
            return

        criteria = {}
        if args.criteria:
            try:
                criteria = json.loads(args.criteria)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid criteria JSON: {e}")
                return

        runner = EvalRunner(provider=args.provider)
        result = runner.run(args.target, args.input, criteria)

        print(f"\n{'='*60}")
        print(f"  Eval Run — {result.skill_id}")
        print(f"{'='*60}")
        icon = "PASS" if result.passed else "FAIL"
        print(f"  Status:     {icon}  (score={result.score:.2f})")
        print(f"  Latency:    {result.latency_ms}ms")
        if result.token_usage:
            print(f"  Tokens:     {result.token_usage.get('input',0)} in / {result.token_usage.get('output',0)} out")
        print(f"  Errors:     {len(result.errors)}")
        for e in result.errors[-8:]:
            print(f"    - {e}")
        print(f"  Output:     {result.actual_output[:200]}...")

    elif args.action == "agent":
        if not args.target:
            print("Error: Agent name is required for eval agent")
            print("Usage: aitest eval agent <agent_name> --module=<m> [--page=<p>]")
            return

        runner = EvalRunner(provider=args.provider)
        result = runner.run_agent(
            agent_name=args.target,
            module=args.module or "",
            page=args.page or "",
        )

        print(f"\n{'='*60}")
        print(f"  Agent Eval — {result['agent_name']}")
        print(f"{'='*60}")
        icon = "PASS" if result["success"] else "FAIL"
        print(f"  Status:     {icon}  ({result['termination_reason']})")
        print(f"  Completed:  {result['completed_skills']}")
        print(f"  Failed:     {result['failed_skills']}")
        print(f"  Total latency: {result['total_latency_ms']}ms")
        print(f"  Total tokens:  {result['total_tokens']}")
        print(f"\n  Skill details:")
        for sr in result["skill_results"]:
            sicon = "✅" if sr["status"] == "pass" else "❌"
            print(f"    {sicon} {sr['skill_id']}: {sr['status']} ({len(sr['quality_issues'])} issues)")

    elif args.action == "summary":
        runner = EvalRunner()
        metrics = runner.metric_from_traces(
            skill_id=args.skill,
            run_id=args.run_id,
        )

        if not metrics:
            print("No evaluation metrics found. Run 'aitest eval run' first, or check trace data.")
            return

        print(f"\n{'='*65}")
        print(f"  Eval Summary — {'all skills' if not args.skill else args.skill}")
        print(f"{'='*65}")
        for m in metrics:
            sr = f"{m.success_rate:.0%}"
            print(f"\n  {m.skill_id}")
            print(f"    runs={m.total_runs}  success={sr}  avg_lat={m.avg_latency_ms}ms  cost=${m.avg_cost_per_run:.4f}/run")
            print(f"    tokens/run={m.tokens_per_run}  (ok={m.success_count} fail={m.failure_count})")


def cmd_trace(args):
    """追踪事件查询 (P1-1 + P0/P1 可观测性)"""
    sys.path.insert(0, str(WORKSTUDY))
    from aitest.infra.trace import query_trace_events, get_trace_summary, cleanup_old_traces, get_run_stats, get_cost_leaderboard

    if args.action == "list":
        events = query_trace_events(
            run_id=args.run_id,
            event_type=args.type,
            skill_id=args.skill,
            limit=args.limit,
        )
        if not events:
            print("No trace events found.")
            return

        print(f"\n{'='*70}")
        print(f"  Trace Events — {len(events)} found")
        print(f"{'='*70}")
        for e in events:
            icon = "✅" if e.get("status") == "success" else "❌"
            cost = e.get("token_cost_estimate", 0)
            cost_str = f" ${cost:.4f}" if cost > 0 else " free"
            print(f"\n  {icon} [{e.get('event_type','?')}] {e.get('skill_id','') or e.get('agent_name','')}")
            print(f"     ts={e.get('timestamp','?')} | provider={e.get('provider','?')} | model={e.get('model','?')}")
            print(f"     latency={e.get('latency_ms',0)}ms | tokens(in={e.get('token_input',0)} out={e.get('token_output',0)}){cost_str}")
            preview = e.get("response_preview", "")
            if preview:
                print(f"     preview: {preview[:120]}...")

    elif args.action == "summary":
        if not args.run_id:
            print("Error: --run-id is required for summary")
            return
        summary = get_trace_summary(args.run_id)
        print(f"\n{'='*60}")
        print(f"  Trace Summary — {args.run_id}")
        print(f"{'='*60}")
        print(f"  Total events:    {summary['total_events']}")
        print(f"  Total cost:      ${summary['total_cost']:.4f}")
        print(f"  Total latency:   {summary['total_latency_ms']}ms ({summary['total_latency_ms']/1000:.1f}s)")
        print(f"  Total tokens:    {summary['total_tokens_input']} in / {summary['total_tokens_output']} out")
        print(f"  Models:          {', '.join(summary['models_seen']) if summary['models_seen'] else 'N/A'}")
        print(f"\n  By event type:")
        for etype, count in sorted(summary.get("by_type", {}).items()):
            print(f"    {etype}: {count}")
        print(f"\n  By skill:")
        for sid, stats in sorted(summary.get("by_skill", {}).items()):
            sr = stats.get("success_rate", 0)
            avg_lat = stats.get("avg_latency_ms", 0)
            print(f"    {sid}: {stats['count']} calls, {sr:.0%} success, avg {avg_lat}ms")

    elif args.action == "stats":
        # ★ P0: 单次运行的完整 Token/调用/成本统计
        if not args.run_id:
            print("Error: --run-id is required for stats")
            return
        stats = get_run_stats(args.run_id)
        if "error" in stats:
            print(f"Error: {stats['error']}")
            return

        print(f"\n{'='*60}")
        print(f"  Run Stats — {args.run_id}")
        print(f"{'='*60}")
        print(f"  LLM calls:       {stats['total_llm_calls']}")
        print(f"  Agent decisions: {stats['agent_decision_calls']}")
        print(f"  Skill execs:     {stats['skill_executions']}")
        print(f"  Total tokens:    {stats['total_tokens_in']:,} in / {stats['total_tokens_out']:,} out ({stats['total_tokens']:,} total)")
        print(f"  Total cost:      ${stats['total_cost']:.4f}")
        print(f"  Total latency:   {stats['total_latency_ms']}ms ({stats['total_latency_ms']/1000:.1f}s)")
        print(f"  Models:          {', '.join(stats['models_seen']) if stats['models_seen'] else 'N/A'}")

        if stats.get("by_agent"):
            print(f"\n  By Agent:")
            for agent, a in stats["by_agent"].items():
                print(f"    {agent}: {a['calls']} calls, {a['tokens_in']:,} in, ${a['cost']:.4f}")

        if stats.get("by_skill"):
            print(f"\n  By Skill:")
            for sid, s in stats["by_skill"].items():
                print(f"    {sid}: {s['calls']} calls, {s['tokens_in']:,} in / {s['tokens_out']:,} out, ${s['cost']:.4f}")

    elif args.action == "board":
        # ★ P1: Agent 成本排行榜
        days = getattr(args, 'days', 7)
        limit = getattr(args, 'limit', 10)
        leaderboard = get_cost_leaderboard(days=days, limit=limit)
        if not leaderboard:
            print(f"No trace events found in the last {days} day(s).")
            return

        print(f"\n{'='*70}")
        print(f"  Agent Cost Leaderboard (last {days} days)")
        print(f"{'='*70}")
        print(f"  {'Rank':<5} {'Agent':<25} {'Calls':<8} {'Tokens In':<12} {'Cost':<10}")
        print(f"  {'-'*4} {'-'*25} {'-'*8} {'-'*12} {'-'*10}")
        for i, entry in enumerate(leaderboard, 1):
            print(f"  {i:<5} {entry['agent']:<25} {entry['calls']:<8} {entry['tokens_in']:>10,}  ${entry['cost']:>8.4f}")

    elif args.action == "advise":
        # ★ P2: 自动成本优化建议
        days = getattr(args, 'days', 7)
        from aitest.cost_advisor import analyze_trace_data
        suggestions = analyze_trace_data(days=days)
        if not suggestions:
            print(f"No optimization suggestions found (last {days} days).")
            return

        severity_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        print(f"\n{'='*70}")
        print(f"  Cost Optimization Suggestions (last {days} days)")
        print(f"{'='*70}")
        for s in suggestions:
            icon = severity_icons.get(s["severity"], "⚪")
            sev = s["severity"].upper()
            rule = s["rule"]
            print(f"\n{icon} {sev} | {rule}")
            print(f"  {s['finding']}")
            print(f"  → {s['suggestion']}")

    elif args.action == "clean":
        deleted = cleanup_old_traces(days=args.days)
        print(f"Cleaned {deleted} trace events older than {args.days} day(s).")


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
    p_graph_dev.add_argument("--mode", default="full",
                            choices=["full", "resume", "status", "from-architecture", "from-frontend", "from-backend", "review-only"],
                            help="运行模式（默认 full）")
    p_graph_dev.add_argument("--provider", "-p", default="claude",
                            choices=["claude", "openai", "ollama"],
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
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
