"""
Replay — execution recording and playback.

Part of the Run System lifecycle: Execute → Observe → Replay → Compare

Tables:
  replay_sessions   — one per recorded run
  execution_steps   — each skill/tool/workflow/plugin call
  llm_traces        — optional LLM call details

Usage:
    from aitest.platform.replay import ReplayRecorder, ReplayPlayer

    # Record
    recorder = ReplayRecorder(run_id="run-123", module="equipment")
    step = recorder.begin_step(type="skill", name="page-analyze", input={...})
    # ... execute ...
    recorder.end_step(step.id, output={...}, status="success")

    # Replay
    player = ReplayPlayer(session_id=recorder.session_id)
    for step in player.steps():
        result = player.mock_execute(step)
"""

import json
import time
import uuid
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Any

from aitest.infra.database import pg_exec, pg_query

logger = logging.getLogger("replay")


def _escape(val) -> str:
    if val is None:
        return "NULL"
    return "'" + str(val).replace("'", "''") + "'"


def _escape_json(val) -> str:
    if val is None:
        return "'{}'"
    return "'" + json.dumps(val, ensure_ascii=False).replace("'", "''") + "'"


# ── Replay Modes ─────────────────────────────────────────────────────

class ReplayMode:
    MOCK = "mock"              # Use recorded LLM responses (default, deterministic)
    LIVE_COMPARE = "compare"   # Re-execute and compare with recorded results
    STEP_DEBUG = "debug"       # Single-step with pause/inspect


# ── Step Types ───────────────────────────────────────────────────────

class StepType:
    SKILL = "skill"
    TOOL = "tool"
    WORKFLOW = "workflow"
    PLUGIN = "plugin"
    LLM_CALL = "llm_call"


# ── Data Classes ─────────────────────────────────────────────────────

@dataclass
class ExecutionStep:
    """A single recorded execution step."""
    id: str
    session_id: str
    step_index: int
    step_type: str          # skill | tool | workflow | plugin | llm_call
    name: str               # e.g., "page-analyze", "browser.click"
    input_data: dict = field(default_factory=dict)
    output_data: dict = field(default_factory=dict)
    status: str = "running"  # running | success | failed | skipped
    duration_ms: float = 0.0
    error_message: str = ""
    started_at: float = 0.0
    completed_at: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "step_index": self.step_index,
            "step_type": self.step_type,
            "name": self.name,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
        }


@dataclass
class LLMTrace:
    """Optional LLM call trace."""
    id: str
    step_id: str
    session_id: str
    model: str = ""
    provider: str = ""
    messages: list = field(default_factory=list)
    response: str = ""
    usage: dict = field(default_factory=dict)  # {input_tokens, output_tokens}
    temperature: float = 0.0
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "step_id": self.step_id,
            "session_id": self.session_id,
            "model": self.model,
            "provider": self.provider,
            "messages": self.messages,
            "response": self.response,
            "usage": self.usage,
            "temperature": self.temperature,
            "duration_ms": self.duration_ms,
        }


@dataclass
class ReplaySession:
    """A recorded execution session."""
    id: str
    run_id: str
    module: str
    page: str = ""
    agent: str = ""
    mode: str = "mock"
    step_count: int = 0
    total_duration_ms: float = 0.0
    status: str = "recording"  # recording | completed | replaying
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "module": self.module,
            "page": self.page,
            "agent": self.agent,
            "mode": self.mode,
            "step_count": self.step_count,
            "total_duration_ms": self.total_duration_ms,
            "status": self.status,
            "created_at": self.created_at,
        }


# ══════════════════════════════════════════════════════════════════════════
#  ReplayRecorder — records execution steps
# ══════════════════════════════════════════════════════════════════════════

class ReplayRecorder:
    """Records execution steps for later replay.

    Usage:
        recorder = ReplayRecorder(run_id="run-123", module="equipment")
        step = recorder.begin_step(type="skill", name="page-analyze", input={...})
        # ... execute ...
        recorder.end_step(step.id, output={...}, status="success")
        recorder.finish()
    """

    def __init__(self, run_id: str, module: str, page: str = "", agent: str = ""):
        self.session_id = f"replay-{uuid.uuid4().hex[:12]}"
        self.run_id = run_id
        self.module = module
        self.page = page
        self.agent = agent
        self._steps: list[ExecutionStep] = []
        self._llm_traces: list[LLMTrace] = []
        self._step_counter = 0
        self._started_at = time.time()

        # Persist session
        now = datetime.now(timezone.utc).isoformat()
        pg_exec(f"""
            INSERT INTO replay_sessions (id, run_id, module, page, agent, mode, status, created_at)
            VALUES ({_escape(self.session_id)}, {_escape(run_id)}, {_escape(module)},
                    {_escape(page)}, {_escape(agent)}, 'mock', 'recording', {_escape(now)})
        """)

    def begin_step(
        self,
        step_type: str,
        name: str,
        input_data: dict = None,
        metadata: dict = None,
    ) -> ExecutionStep:
        """Begin recording a new step. Returns the step object."""
        self._step_counter += 1
        step = ExecutionStep(
            id=f"step-{uuid.uuid4().hex[:8]}",
            session_id=self.session_id,
            step_index=self._step_counter,
            step_type=step_type,
            name=name,
            input_data=input_data or {},
            metadata=metadata or {},
            status="running",
            started_at=time.time(),
        )
        self._steps.append(step)

        # Persist
        pg_exec(f"""
            INSERT INTO execution_steps
            (id, session_id, step_index, step_type, name, input_data, output_data,
             status, duration_ms, error_message, started_at, completed_at, metadata)
            VALUES ({_escape(step.id)}, {_escape(self.session_id)}, {step.step_index},
                    {_escape(step_type)}, {_escape(name)}, {_escape_json(input_data or {})},
                    '{{}}', 'running', 0, '', {step.started_at}, 0, {_escape_json(metadata or {})})
        """)

        return step

    def end_step(
        self,
        step_id: str,
        output_data: dict = None,
        status: str = "success",
        error_message: str = "",
    ):
        """End a recording step."""
        now = time.time()
        for step in self._steps:
            if step.id == step_id:
                step.output_data = output_data or {}
                step.status = status
                step.error_message = error_message
                step.completed_at = now
                step.duration_ms = round((now - step.started_at) * 1000, 1)

                # Persist
                pg_exec(f"""
                    UPDATE execution_steps SET
                        output_data={_escape_json(step.output_data)},
                        status={_escape(status)},
                        error_message={_escape(error_message)},
                        completed_at={now},
                        duration_ms={step.duration_ms}
                    WHERE id={_escape(step_id)}
                """)
                return

    def record_llm_call(
        self,
        step_id: str,
        model: str,
        provider: str,
        messages: list,
        response: str,
        usage: dict = None,
        temperature: float = 0.0,
        duration_ms: float = 0.0,
    ):
        """Record an LLM call (optional, for mock replay)."""
        trace = LLMTrace(
            id=f"llm-{uuid.uuid4().hex[:8]}",
            step_id=step_id,
            session_id=self.session_id,
            model=model,
            provider=provider,
            messages=messages,
            response=response,
            usage=usage or {},
            temperature=temperature,
            duration_ms=duration_ms,
        )
        self._llm_traces.append(trace)

        # Persist
        pg_exec(f"""
            INSERT INTO llm_traces
            (id, step_id, session_id, model, provider, messages, response,
             usage, temperature, duration_ms)
            VALUES ({_escape(trace.id)}, {_escape(step_id)}, {_escape(self.session_id)},
                    {_escape(model)}, {_escape(provider)},
                    {_escape_json(messages)}, {_escape(response)},
                    {_escape_json(usage or {})}, {temperature}, {duration_ms})
        """)

    def finish(self):
        """Mark recording as completed."""
        total_ms = round((time.time() - self._started_at) * 1000, 1)
        pg_exec(f"""
            UPDATE replay_sessions SET
                status='completed', step_count={len(self._steps)},
                total_duration_ms={total_ms}
            WHERE id={_escape(self.session_id)}
        """)

    @property
    def session(self) -> ReplaySession:
        return ReplaySession(
            id=self.session_id,
            run_id=self.run_id,
            module=self.module,
            page=self.page,
            agent=self.agent,
            step_count=len(self._steps),
            total_duration_ms=round((time.time() - self._started_at) * 1000, 1),
            status="recording",
        )


# ══════════════════════════════════════════════════════════════════════════
#  ReplayPlayer — replays recorded execution
# ══════════════════════════════════════════════════════════════════════════

class ReplayPlayer:
    """Replays a recorded execution session.

    Usage:
        player = ReplayPlayer(session_id="replay-abc123")
        for step in player.steps():
            if step.step_type == "llm_call":
                # Mock: return recorded response
                trace = player.get_llm_trace(step.id)
                mock_response = trace.response
            else:
                # Re-execute tool/skill
                result = execute(step.input_data)
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._session: Optional[ReplaySession] = None
        self._steps: list[ExecutionStep] = []
        self._llm_traces: dict[str, LLMTrace] = {}  # step_id → LLMTrace
        self._load()

    def _load(self):
        """Load session and steps from database."""
        # Load session
        rows = pg_query(f"SELECT * FROM replay_sessions WHERE id={_escape(self.session_id)}")
        if not rows:
            raise ValueError(f"Replay session not found: {self.session_id}")
        r = rows[0]
        self._session = ReplaySession(
            id=r["id"], run_id=r["run_id"], module=r["module"],
            page=r.get("page", ""), agent=r.get("agent", ""),
            mode=r.get("mode", "mock"), step_count=r.get("step_count", 0),
            total_duration_ms=r.get("total_duration_ms", 0),
            status=r.get("status", ""), created_at=r.get("created_at", ""),
        )

        # Load steps
        step_rows = pg_query(
            f"SELECT * FROM execution_steps WHERE session_id={_escape(self.session_id)} "
            f"ORDER BY step_index ASC"
        )
        for r in step_rows:
            self._steps.append(ExecutionStep(
                id=r["id"], session_id=r["session_id"],
                step_index=r["step_index"], step_type=r["step_type"],
                name=r["name"],
                input_data=r.get("input_data", {}),
                output_data=r.get("output_data", {}),
                status=r.get("status", ""),
                duration_ms=r.get("duration_ms", 0),
                error_message=r.get("error_message", ""),
                started_at=r.get("started_at", 0),
                completed_at=r.get("completed_at", 0),
                metadata=r.get("metadata", {}),
            ))

        # Load LLM traces
        trace_rows = pg_query(
            f"SELECT * FROM llm_traces WHERE session_id={_escape(self.session_id)}"
        )
        for r in trace_rows:
            trace = LLMTrace(
                id=r["id"], step_id=r["step_id"], session_id=r["session_id"],
                model=r.get("model", ""), provider=r.get("provider", ""),
                messages=r.get("messages", []),
                response=r.get("response", ""),
                usage=r.get("usage", {}),
                temperature=r.get("temperature", 0),
                duration_ms=r.get("duration_ms", 0),
            )
            self._llm_traces[trace.step_id] = trace

    @property
    def session(self) -> ReplaySession:
        return self._session

    def steps(self) -> list[ExecutionStep]:
        """Get all recorded steps in order."""
        return self._steps

    def get_llm_trace(self, step_id: str) -> Optional[LLMTrace]:
        """Get the LLM trace for a step (for mock replay)."""
        return self._llm_traces.get(step_id)

    def mock_execute(self, step: ExecutionStep) -> dict:
        """Mock execute a step — returns recorded output without calling real services."""
        if step.step_type == StepType.LLM_CALL:
            trace = self.get_llm_trace(step.id)
            if trace:
                return {
                    "mock": True,
                    "response": trace.response,
                    "usage": trace.usage,
                    "model": trace.model,
                }
        # For non-LLM steps, return recorded output
        return {"mock": True, "output": step.output_data}

    def compare(self, new_outputs: dict[str, dict]) -> dict:
        """Compare new execution results with recorded results.

        Returns:
            Dict with comparison results per step.
        """
        comparison = {}
        for step in self._steps:
            recorded = step.output_data
            new = new_outputs.get(step.id, {})
            match = recorded == new
            comparison[step.id] = {
                "step_name": step.name,
                "match": match,
                "recorded_keys": list(recorded.keys()),
                "new_keys": list(new.keys()),
            }
        return comparison


# ── Query helpers ────────────────────────────────────────────────────

def list_replay_sessions(run_id: str = "", module: str = "", limit: int = 20) -> list[dict]:
    """List replay sessions."""
    where = ["1=1"]
    if run_id:
        where.append(f"run_id={_escape(run_id)}")
    if module:
        where.append(f"module={_escape(module)}")
    return pg_query(
        f"SELECT * FROM replay_sessions WHERE {' AND '.join(where)} "
        f"ORDER BY created_at DESC LIMIT {limit}"
    )


def get_replay_summary(session_id: str) -> dict:
    """Get a summary of a replay session."""
    session_rows = pg_query(f"SELECT * FROM replay_sessions WHERE id={_escape(session_id)}")
    if not session_rows:
        return {}

    step_rows = pg_query(
        f"SELECT step_type, status, COUNT(*) as cnt, AVG(duration_ms) as avg_ms "
        f"FROM execution_steps WHERE session_id={_escape(session_id)} "
        f"GROUP BY step_type, status"
    )

    llm_rows = pg_query(
        f"SELECT model, COUNT(*) as calls, SUM((usage->>'input_tokens')::int) as input_tokens, "
        f"SUM((usage->>'output_tokens')::int) as output_tokens "
        f"FROM llm_traces WHERE session_id={_escape(session_id)} "
        f"GROUP BY model"
    )

    return {
        "session": session_rows[0],
        "steps_by_type": step_rows,
        "llm_usage": llm_rows,
    }
