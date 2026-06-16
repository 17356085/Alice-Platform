"""
Workflow Engine — ⚠️ DEPRECATED (P1-1, 2026-06-13)

已被 LangGraph 引擎 (aitest/graphs/sop_graph.py) 全面替代。
保留 30 天缓冲期至 2026-07-13，届时删除。

迁移指引:
  旧: python -m aitest.workflow_engine run <wf-id> --module=<m>
  新: aitest graph run --module=<m>

  旧: python -m aitest.workflow_engine resume <run-id>
  新: aitest graph resume --run-id=<run-id>

  旧: python -m aitest.workflow_engine status [--run-id=<id>]
  新: aitest graph status [--run-id=<id>]

原功能:
  1. YAML DAG 定义解析 + 拓扑排序
  2. 顺序/并行步骤执行
  3. 断点续跑（checkpoint JSON）
  4. 状态报告

原用法:
  python -m aitest.workflow_engine run module-onboarding --module=tank
  python -m aitest.workflow_engine resume module-onboarding --run-id=xxx
  python -m aitest.workflow_engine status [--run-id=xxx]
"""
import os
import json
import time
from pathlib import Path
from typing import Optional, Any
from collections import deque
from dataclasses import dataclass, field

import yaml

from governance.validators.sop_validator import validate_file_set

# ── 路径配置 ──────────────────────────────────────────────────────────
WORKSTUDY = Path(__file__).resolve().parent.parent
WORKFLOW_DIR = WORKSTUDY / "governance" / "workflows"
CHECKPOINT_DIR = WORKSTUDY / "governance" / ".workflow_state"
RUNS_DIR = CHECKPOINT_DIR / "runs"


@dataclass
class WorkflowStep:
    """工作流步骤定义。"""
    id: str
    name: str
    agent: str = ""
    skill: str = ""
    phase: str = ""
    description: str = ""
    depends_on: list[str] = field(default_factory=list)
    inputs: dict = field(default_factory=dict)
    outputs: list[str] = field(default_factory=list)
    condition: str = ""          # Python expression for conditional execution
    auto_trigger: bool = False   # 是否自动触发（不需人工确认）
    artifact_pattern: str = ""   # 产出文件 glob pattern

    @classmethod
    def from_dict(cls, d: dict) -> "WorkflowStep":
        return cls(
            id=d.get("id", ""),
            name=d.get("name", ""),
            agent=d.get("agent", ""),
            skill=d.get("skill", ""),
            phase=d.get("phase", ""),
            description=d.get("description", ""),
            depends_on=d.get("depends_on", []),
            inputs=d.get("inputs", {}),
            outputs=d.get("outputs", []),
            condition=d.get("condition", ""),
            auto_trigger=d.get("auto_trigger", False),
            artifact_pattern=d.get("artifact_pattern", ""),
        )


@dataclass
class WorkflowDef:
    """工作流定义。"""
    id: str
    name: str
    description: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    on_failure: str = "pause"  # pause | skip | abort

    @classmethod
    def from_yaml(cls, path) -> "WorkflowDef":
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        steps = [WorkflowStep.from_dict(s) for s in data.get("steps", [])]
        return cls(
            id=data.get("id", path.stem),
            name=data.get("name", path.stem),
            description=data.get("description", ""),
            steps=steps,
            on_failure=data.get("on_failure", "pause"),
        )


@dataclass
class StepState:
    """步骤执行状态。"""
    step_id: str
    status: str = "pending"          # pending | running | completed | failed | skipped
    started_at: float = 0.0
    completed_at: float = 0.0
    output_summary: str = ""
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "output_summary": self.output_summary,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "StepState":
        return cls(**d)


@dataclass
class RunState:
    """运行状态 — 持久化到 checkpoint JSON。"""
    run_id: str
    workflow_id: str
    params: dict = field(default_factory=dict)
    steps: dict[str, StepState] = field(default_factory=dict)  # step_id → state
    current_step: str = ""
    status: str = "running"  # running | completed | failed | paused
    created_at: float = 0.0
    updated_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "params": self.params,
            "steps": {k: v.to_dict() for k, v in self.steps.items()},
            "current_step": self.current_step,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RunState":
        steps = {k: StepState.from_dict(v) for k, v in d.get("steps", {}).items()}
        return cls(
            run_id=d["run_id"],
            workflow_id=d["workflow_id"],
            params=d.get("params", {}),
            steps=steps,
            current_step=d.get("current_step", ""),
            status=d.get("status", "running"),
            created_at=d.get("created_at", 0.0),
            updated_at=d.get("updated_at", 0.0),
        )


# ══════════════════════════════════════════════════════════════════════════
#  DAG 分析
# ══════════════════════════════════════════════════════════════════════════

def topological_sort(steps: list[WorkflowStep]) -> list[list[WorkflowStep]]:
    """拓扑排序，返回可并行执行的步骤组列表。

    返回: [[step_a, step_b], [step_c], [step_d, step_e]] — 每组内的步骤可并行执行。
    """
    step_map = {s.id: s for s in steps}
    in_degree = {s.id: len(s.depends_on) for s in steps}
    dependents = {s.id: [] for s in steps}

    for s in steps:
        for dep_id in s.depends_on:
            if dep_id in dependents:
                dependents[dep_id].append(s.id)

    # BFS — 每个层级包含所有入度为0的步骤
    queue = deque([sid for sid, deg in in_degree.items() if deg == 0])
    levels = []

    while queue:
        level = []
        for _ in range(len(queue)):
            sid = queue.popleft()
            if sid in step_map:
                level.append(step_map[sid])
            for dep in dependents.get(sid, []):
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)
        if level:
            levels.append(level)

    # 检测循环依赖
    remaining = [s for s in steps if in_degree[s.id] > 0]
    if remaining:
        raise ValueError(f"Circular dependency detected: {[r.id for r in remaining]}")

    return levels


def get_ready_steps(steps: list[WorkflowStep], completed: set[str]) -> list[WorkflowStep]:
    """获取所有依赖已满足的步骤。"""
    ready = []
    for s in steps:
        if s.id not in completed and all(d in completed for d in s.depends_on):
            # 检查 condition
            if s.condition:
                try:
                    if not eval(s.condition, {"completed": completed}):
                        continue
                except Exception as e:
                    from aitest.error_logger import log_error
                    log_error("workflow_engine.get_ready_steps", "eval_condition", e, {"condition": s.condition, "step": s.id})
            ready.append(s)
    return ready


# ══════════════════════════════════════════════════════════════════════════
#  执行引擎
# ══════════════════════════════════════════════════════════════════════════

class WorkflowRunner:
    """工作流执行器 — 管理单次运行的完整生命周期。"""

    def __init__(self, workflow: WorkflowDef, params: dict = None):
        self.workflow = workflow
        self.params = params or {}
        self.run_id = f"{workflow.id}-{int(time.time())}"
        self.run_state: Optional[RunState] = None

    def start(self) -> RunState:
        """初始化运行状态。"""
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        now = time.time()
        self.run_state = RunState(
            run_id=self.run_id,
            workflow_id=self.workflow.id,
            params=self.params,
            steps={s.id: StepState(step_id=s.id) for s in self.workflow.steps},
            created_at=now,
            updated_at=now,
        )
        self._save_checkpoint()
        return self.run_state

    def resume(self, run_id: str) -> RunState:
        """从 checkpoint 恢复。"""
        self.run_id = run_id
        path = RUNS_DIR / f"{run_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            self.run_state = RunState.from_dict(json.load(f))
        return self.run_state

    def get_next_steps(self) -> list[WorkflowStep]:
        """获取下一步可执行的步骤。"""
        if not self.run_state:
            return []
        completed = {sid for sid, st in self.run_state.steps.items()
                     if st.status in ("completed", "skipped")}
        all_steps = {s.id: s for s in self.workflow.steps}
        ready = get_ready_steps(list(all_steps.values()), completed)
        # 排除已运行中的
        ready = [s for s in ready
                 if self.run_state.steps[s.id].status not in ("running", "failed")]
        return ready

    def mark_step_running(self, step_id: str) -> None:
        """标记步骤开始执行。"""
        if self.run_state and step_id in self.run_state.steps:
            st = self.run_state.steps[step_id]
            st.status = "running"
            st.started_at = time.time()
            self.run_state.current_step = step_id
            self.run_state.updated_at = time.time()
            self._save_checkpoint()

    def mark_step_completed(self, step_id: str, summary: str = "") -> None:
        """标记步骤完成。"""
        if self.run_state and step_id in self.run_state.steps:
            step = next((s for s in self.workflow.steps if s.id == step_id), None)
            if step and step.artifact_pattern:
                pattern = self._render_template(step.artifact_pattern)
                rendered = self._glob_paths(pattern)
                gate = validate_file_set(rendered, require_non_empty=True)
                if not gate.ok:
                    raise ValueError(
                        f"Cannot complete step {step_id}: {gate.message} ({gate.details})"
                    )
            st = self.run_state.steps[step_id]
            st.status = "completed"
            st.completed_at = time.time()
            st.output_summary = summary
            self.run_state.updated_at = time.time()
            self._save_checkpoint()

    def mark_step_failed(self, step_id: str, error: str) -> None:
        """标记步骤失败。"""
        if self.run_state and step_id in self.run_state.steps:
            st = self.run_state.steps[step_id]
            st.status = "failed"
            st.error = error
            self.run_state.status = "failed" if self.workflow.on_failure == "abort" else "paused"
            self.run_state.updated_at = time.time()
            self._save_checkpoint()

    def execute_step(self, step_id: str) -> dict:
        """
        执行一个步骤——调用 AgentLoop 真正运行 Agent。

        这是 workflow_engine 和 agent_runner 的桥接点。
        只有当 step 定义了 agent 字段时才执行 Agent；否则仅标记完成。
        """
        step = next((s for s in self.workflow.steps if s.id == step_id), None)
        if not step:
            raise ValueError(f"Step not found: {step_id}")

        # 渲染 agent name
        agent_name = self._render_template(step.agent) if step.agent else ""
        module = self.params.get("module", "")
        page = self.params.get("page", "")

        if not agent_name:
            # 无 Agent 的步骤（纯检查步骤），直接标记完成
            self.mark_step_completed(step_id, "No agent required")
            return {"step": step_id, "status": "completed", "note": "no agent"}

        # 调用 AgentLoop 执行
        try:
            from aitest.agent_runner import AgentLoop
            agent = AgentLoop(
                agent_name,
                module=module,
                page=page,
                verbose=False,
            )
            state = agent.run()
            result = {
                "step": step_id,
                "agent": agent_name,
                "status": "completed" if state.success else "completed_with_issues",
                "success": state.success,
                "steps": state.step,
                "completed_skills": state.completed_skills,
                "failed_skills": state.failed_skills,
                "termination_reason": state.termination_reason,
            }
            if state.success:
                self.mark_step_completed(step_id, state.termination_reason)
            else:
                self.mark_step_completed(
                    step_id,
                    f"Partial: {len(state.completed_skills)}/{len(state.completed_skills) + len(state.failed_skills)} skills passed"
                )
            return result
        except Exception as e:
            self.mark_step_failed(step_id, str(e))
            return {"step": step_id, "status": "failed", "error": str(e)}

    def execute_ready_steps(self) -> list[dict]:
        """执行所有就绪的步骤（调用 AgentLoop）。"""
        ready = self.get_next_steps()
        if not ready:
            return []
        results = []
        for step in ready:
            self.mark_step_running(step.id)
            result = self.execute_step(step.id)
            results.append(result)
        return results

    def mark_step_skipped(self, step_id: str, reason: str = "") -> None:
        """跳过步骤。"""
        if self.run_state and step_id in self.run_state.steps:
            st = self.run_state.steps[step_id]
            st.status = "skipped"
            st.error = reason
            self.run_state.updated_at = time.time()
            self._save_checkpoint()

    def is_finished(self) -> bool:
        """检查是否所有步骤都已完成/跳过/失败。"""
        if not self.run_state:
            return True
        return all(st.status in ("completed", "skipped", "failed")
                   for st in self.run_state.steps.values())

    def progress(self) -> dict:
        """返回当前进度。"""
        if not self.run_state:
            return {"status": "not_started"}
        total = len(self.run_state.steps)
        completed = sum(1 for st in self.run_state.steps.values() if st.status == "completed")
        failed = sum(1 for st in self.run_state.steps.values() if st.status == "failed")
        skipped = sum(1 for st in self.run_state.steps.values() if st.status == "skipped")
        running = sum(1 for st in self.run_state.steps.values() if st.status == "running")
        pending = total - completed - failed - skipped - running

        ready = self.get_next_steps()

        return {
            "run_id": self.run_state.run_id,
            "workflow": self.workflow_id,
            "status": self.run_state.status,
            "total_steps": total,
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "running": running,
            "pending": pending,
            "ready_next": [s.id for s in ready],
            "current_step": self.run_state.current_step,
            "progress_pct": round((completed + skipped) / total * 100, 1) if total > 0 else 0,
        }

    def _save_checkpoint(self) -> None:
        """持久化 checkpoint。"""
        if self.run_state:
            RUNS_DIR.mkdir(parents=True, exist_ok=True)
            path = RUNS_DIR / f"{self.run_state.run_id}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.run_state.to_dict(), f, ensure_ascii=False, indent=2)

    def _render_template(self, text: str) -> str:
        """Very small template renderer for {{params.*}} placeholders."""
        rendered = text
        for key, value in self.params.items():
            rendered = rendered.replace(f"{{{{params.{key}}}}}", str(value))
        return rendered

    def _glob_paths(self, pattern: str) -> list[Path]:
        """Resolve a rendered glob pattern into paths."""
        return list(WORKSTUDY.glob(pattern))

    def load_workflow_steps(self) -> list[dict]:
        """加载工作流步骤定义的详细信息（供 Agent 使用）。"""
        levels = topological_sort(self.workflow.steps)
        steps_info = []
        for level_idx, level in enumerate(levels):
            for step in level:
                info = {
                    "id": step.id,
                    "name": step.name,
                    "agent": step.agent,
                    "skill": step.skill,
                    "phase": step.phase,
                    "description": step.description,
                    "depends_on": step.depends_on,
                    "level": level_idx,
                    "parallel_group": [s.id for s in level],
                    "outputs": step.outputs,
                    "artifact_pattern": step.artifact_pattern,
                }
                if self.run_state and step.id in self.run_state.steps:
                    info["status"] = self.run_state.steps[step.id].status
                steps_info.append(info)
        return steps_info

    @property
    def workflow_id(self) -> str:
        return self.workflow.id


# ══════════════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python workflow_engine.py run|execute|resume|status <workflow-id> [--module=<name>] [--run-id=<id>]")
        print("\nAvailable workflows:")
        for wf_file in sorted(WORKFLOW_DIR.glob("*.yaml")):
            print(f"  {wf_file.stem}")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "run":
        if len(sys.argv) < 3:
            print("Usage: python workflow_engine.py run <workflow-id> [--module=<name>]")
            sys.exit(1)

        wf_id = sys.argv[2]
        params = {}
        for arg in sys.argv[3:]:
            if arg.startswith("--") and "=" in arg:
                k, v = arg[2:].split("=", 1)
                params[k] = v

        wf_path = WORKFLOW_DIR / f"{wf_id}.yaml"
        if not wf_path.exists():
            print(f"Workflow not found: {wf_path}")
            sys.exit(1)

        wf = WorkflowDef.from_yaml(wf_path)
        runner = WorkflowRunner(wf, params)
        state = runner.start()
        print(f"Workflow started: {state.run_id}")

        levels = topological_sort(wf.steps)
        print(f"DAG levels: {len(levels)}")
        for i, level in enumerate(levels):
            print(f"  Level {i}: {[s.id for s in level]}")

        ready = runner.get_next_steps()
        print(f"\nReady to execute: {[s.id for s in ready]}")
        print(f"Run: python -m aitest.workflow_engine execute {state.run_id}")

    elif cmd == "execute":
        # 执行就绪步骤（调用 AgentLoop）
        if len(sys.argv) < 3:
            print("Usage: python workflow_engine.py execute <run-id> [--all]")
            sys.exit(1)

        run_id = sys.argv[2]
        execute_all = "--all" in sys.argv

        # Find matching workflow YAML
        found = False
        for wf_path in sorted(WORKFLOW_DIR.glob("*.yaml")):
            wf = WorkflowDef.from_yaml(wf_path)
            runner = WorkflowRunner(wf)
            try:
                state = runner.resume(run_id)
                found = True
                break
            except FileNotFoundError:
                continue

        if not found:
            print(f"Checkpoint not found for run_id: {run_id}")
            sys.exit(1)

        print(f"Workflow: {runner.workflow_id} | Run: {run_id}")
        progress = runner.progress()
        print(f"Progress: {progress['completed']}/{progress['total_steps']} completed, "
              f"{len(progress['ready_next'])} ready")

        if execute_all:
            while not runner.is_finished():
                results = runner.execute_ready_steps()
                if not results:
                    break
                for r in results:
                    print(f"  {'✅' if r.get('status') == 'completed' else '⚠️'} {r['step']}: {r.get('status')}")
                progress = runner.progress()
                print(f"  Progress: {progress['progress_pct']}%")
        else:
            results = runner.execute_ready_steps()
            for r in results:
                print(f"  {'✅' if r.get('status') == 'completed' else '⚠️'} {r['step']}: {r.get('status')}")
                if r.get('completed_skills'):
                    print(f"    Skills: {r['completed_skills']}")
                if r.get('failed_skills'):
                    print(f"    Failed: {r['failed_skills']}")
        if len(sys.argv) < 3:
            print("Usage: python workflow_engine.py resume <run-id>")
            sys.exit(1)

        run_id = sys.argv[2]
        path = RUNS_DIR / f"{run_id}.json"
        if not path.exists():
            print(f"Checkpoint not found: {path}")
            # Find the workflow ID from the run_id prefix
            wf_id = run_id.rsplit("-", 1)[0]
            wf_path = WORKFLOW_DIR / f"{wf_id}.yaml"
            if not wf_path.exists():
                wf_paths = list(WORKFLOW_DIR.glob("*.yaml"))
                if wf_paths:
                    wf_path = wf_paths[0]
            if wf_path.exists():
                wf = WorkflowDef.from_yaml(wf_path)
                runner = WorkflowRunner(wf)
                state = runner.resume(run_id)
                ready = runner.get_next_steps()
                progress = runner.progress()
                print(json.dumps(progress, ensure_ascii=False, indent=2))
            else:
                sys.exit(1)
        else:
            # Find matching workflow YAML
            run_id_short = run_id.rsplit("-", 1)[0]
            wf_path = WORKFLOW_DIR / f"{run_id_short}.yaml"
            if not wf_path.exists():
                wf_paths = list(WORKFLOW_DIR.glob("*.yaml"))
                wf_path = wf_paths[0] if wf_paths else None
            if wf_path and wf_path.exists():
                wf = WorkflowDef.from_yaml(wf_path)
                runner = WorkflowRunner(wf)
                state = runner.resume(run_id)
                ready = runner.get_next_steps()
                progress = runner.progress()
                print(json.dumps(progress, ensure_ascii=False, indent=2))

    elif cmd == "status":
        run_id = sys.argv[2] if len(sys.argv) > 2 else None
        if run_id:
            path = RUNS_DIR / f"{run_id}.json"
            if path.exists():
                with open(path, "r") as f:
                    print(json.dumps(json.load(f), ensure_ascii=False, indent=2))
            else:
                print(f"No run found: {run_id}")
        else:
            if RUNS_DIR.exists():
                runs = sorted(RUNS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
                for r in runs[:10]:
                    print(f"  {r.stem}  ({time.strftime('%Y-%m-%d %H:%M', time.localtime(r.stat().st_mtime))})")
            else:
                print("No runs found.")
    else:
        print(f"Unknown command: {cmd}")
