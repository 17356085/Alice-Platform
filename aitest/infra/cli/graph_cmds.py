"""CLI graph commands — LangGraph SOP orchestration.

Extracted from infra/cli.py (Architecture Review P3-8 God Module split).
"""

import sys
import subprocess
from aitest.platform.paths import get_workstudy, get_governance_dir, get_test_project_root

WORKSTUDY = get_workstudy()
GOVERNANCE = get_governance_dir()


def _zjsn():
    """Resolve test project root lazily. Returns None if not configured."""
    root = get_test_project_root()
    return root if root else None


def _run_preflight_gate(module: str, mode: str, pages: list[str]) -> None:
    """U9: SOP 门禁前置检查 — 在编排启动前验证前置条件。"""
    try:
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
                if "__interrupt__" in event:
                    for item in event["__interrupt__"]:
                        payload = getattr(item, 'value', None) or item
                        if isinstance(payload, dict):
                            itype = payload.get('type', 'Approval')
                            if non_interactive:
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
        runs = graph_list_runs(limit=args.limit or 20)
        if runs:
            print(f"Runs ({len(runs)}):")
            for r in runs:
                print(f"  {r['run_id']}  ({r.get('updated_at', '?')})")
        else:
            print("No runs found.")

    elif args.action == "cleanup":
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

    if args.action == "run":
        module = args.module
        pages = args.pages.split(",") if args.pages else []
        mode = args.mode or "full"
        provider = args.provider or "claude"

        if not module:
            print("Error: --module is required")
            return

        print(f"Dev SOP LangGraph Engine")
        print(f"  Module:   {module}")
        print(f"  Pages:    {pages or '(auto-discover)'}")
        print(f"  Mode:     {mode}")
        print(f"  Provider: {provider}")
        print()

        initial_state = create_initial_state_dev(
            module=module,
            pages=pages,
            mode=mode,
            provider=provider,
        )

        compiled = build_compiled_dev_graph()
        thread = {"configurable": {"thread_id": initial_state["run_id"]}}
        non_interactive = getattr(args, 'non_interactive', False)

        if not non_interactive:
            print(f"Run ID: {initial_state['run_id']}")
            print("-" * 60)

        from langgraph.types import Command

        try:
            for event in compiled.stream(initial_state, thread, stream_mode="updates"):
                if "__interrupt__" in event:
                    for item in event["__interrupt__"]:
                        payload = getattr(item, 'value', None) or item
                        if isinstance(payload, dict):
                            itype = payload.get('type', 'Approval')
                            if non_interactive:
                                answer = payload.get('options', ['approve'])[0]
                            else:
                                print(f"\n  [HITL] {itype}")
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
                    completed = update.get("completed_phases", []) if isinstance(update, dict) else []
                    if completed:
                        print(f"  [{node_name}] Completed: {completed}")
                    if node_name == "exit":
                        print(f"  [exit] Status: {update.get('status', '?') if isinstance(update, dict) else '?'}")

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
                        "engine": "langgraph-dev",
                    }
                    print(_json.dumps(result, ensure_ascii=False, indent=2))

        except KeyboardInterrupt:
            print(f"\n  Interrupted. Resume with: aitest graph-dev resume --run-id={initial_state['run_id']}")

    elif args.action == "resume":
        from aitest.graphs_dev.sop_graph_dev import get_dev_checkpointer, list_dev_runs

        run_id = args.run_id
        if not run_id:
            runs = list_dev_runs()
            if runs:
                run_id = runs[0]["run_id"]
                print(f"Resuming latest run: {run_id}")
            else:
                print("No runs to resume")
                return

        compiled = build_compiled_dev_graph()
        thread = {"configurable": {"thread_id": run_id}}
        current = compiled.get_state(thread)

        if not current or not current.values:
            print(f"No state found for run: {run_id}")
            return

        state = current.values
        print(f"Resuming: {run_id}")
        print(f"  Module: {state.get('module', '?')}")
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
                                answer = payload.get('options', ['approve'])[0]
                            else:
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
                    completed = update.get("completed_phases", []) if isinstance(update, dict) else []
                    if completed:
                        print(f"  [{node_name}] Completed: {completed}")
        except KeyboardInterrupt:
            print(f"\n  Interrupted. Resume again with: aitest graph-dev resume --run-id={run_id}")

    elif args.action == "status":
        from aitest.graphs_dev.sop_graph_dev import get_dev_checkpointer, list_dev_runs
        run_id = args.run_id
        if run_id:
            state = compiled.get_state(thread)
            if state and state.values:
                sv = state.values
                print(f"Run: {run_id}")
                print(f"  Module: {sv.get('module', '?')}")
                print(f"  Status: {sv.get('status', '?')}")
                print(f"  Completed: {sv.get('completed_phases', [])}")
            else:
                print(f"No state found for run: {run_id}")
        else:
            runs = list_dev_runs()
            if runs:
                print(f"Recent runs ({len(runs)}):")
                for r in runs:
                    print(f"  {r['run_id']}  ({r.get('updated_at', '?')})")
            else:
                print("No runs found.")
