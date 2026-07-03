"""
Replay — execution recording and playback. v3.1

v3.1: Uses parameterized queries via aitest.infra.sql (no more f-string SQL).

Usage:
    from aitest.platform.replay import ReplayRecorder, ReplayPlayer

    recorder = ReplayRecorder(run_id="run-123", module="equipment")
    step = recorder.begin_step(type="skill", name="page-analyze", input={...})
    recorder.end_step(step.id, output={...}, status="success")
    recorder.finish()

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

from aitest.infra.sql import safe_exec, safe_query

logger = logging.getLogger("replay")


class ReplayMode:
    MOCK = "mock"
    LIVE_COMPARE = "compare"
    STEP_DEBUG = "debug"


class StepType:
    SKILL = "skill"
    TOOL = "tool"
    WORKFLOW = "workflow"
    PLUGIN = "plugin"
    LLM_CALL = "llm_call"


@dataclass
class ExecutionStep:
    id: str
    session_id: str
    step_index: int
    step_type: str
    name: str
    input_data: dict = field(default_factory=dict)
    output_data: dict = field(default_factory=dict)
    status: str = "running"
    duration_ms: float = 0.0
    error_message: str = ""
    started_at: float = 0.0
    completed_at: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"id": self.id, "session_id": self.session_id, "step_index": self.step_index,
                "step_type": self.step_type, "name": self.name, "input_data": self.input_data,
                "output_data": self.output_data, "status": self.status, "duration_ms": self.duration_ms,
                "error_message": self.error_message, "started_at": self.started_at,
                "completed_at": self.completed_at, "metadata": self.metadata}


@dataclass
class LLMTrace:
    id: str
    step_id: str
    session_id: str
    model: str = ""
    provider: str = ""
    messages: list = field(default_factory=list)
    response: str = ""
    usage: dict = field(default_factory=dict)
    temperature: float = 0.0
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {"id": self.id, "step_id": self.step_id, "session_id": self.session_id,
                "model": self.model, "provider": self.provider, "messages": self.messages,
                "response": self.response, "usage": self.usage,
                "temperature": self.temperature, "duration_ms": self.duration_ms}


@dataclass
class ReplaySession:
    id: str
    run_id: str
    module: str
    page: str = ""
    agent: str = ""
    mode: str = "mock"
    step_count: int = 0
    total_duration_ms: float = 0.0
    status: str = "recording"
    created_at: str = ""

    def to_dict(self) -> dict:
        return {"id": self.id, "run_id": self.run_id, "module": self.module,
                "page": self.page, "agent": self.agent, "mode": self.mode,
                "step_count": self.step_count, "total_duration_ms": self.total_duration_ms,
                "status": self.status, "created_at": self.created_at}


class ReplayRecorder:
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

        now = datetime.now(timezone.utc).isoformat()
        safe_exec(
            "INSERT INTO replay_sessions (id, run_id, module, page, agent, mode, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, 'mock', 'recording', ?)",
            [self.session_id, run_id, module, page, agent, now],
        )

    def begin_step(self, step_type: str, name: str,
                   input_data: dict = None, metadata: dict = None) -> ExecutionStep:
        self._step_counter += 1
        step = ExecutionStep(
            id=f"step-{uuid.uuid4().hex[:8]}", session_id=self.session_id,
            step_index=self._step_counter, step_type=step_type, name=name,
            input_data=input_data or {}, metadata=metadata or {},
            status="running", started_at=time.time(),
        )
        self._steps.append(step)

        safe_exec(
            "INSERT INTO execution_steps "
            "(id, session_id, step_index, step_type, name, input_data, output_data, "
            "status, duration_ms, error_message, started_at, completed_at, metadata) "
            "VALUES (?, ?, ?, ?, ?, ?, '{}', 'running', 0, '', ?, 0, ?)",
            [step.id, self.session_id, step.step_index, step_type, name,
             json.dumps(input_data or {}, ensure_ascii=False),
             step.started_at, json.dumps(metadata or {}, ensure_ascii=False)],
        )
        return step

    def end_step(self, step_id: str, output_data: dict = None,
                 status: str = "success", error_message: str = ""):
        now = time.time()
        for step in self._steps:
            if step.id == step_id:
                step.output_data = output_data or {}
                step.status = status
                step.error_message = error_message
                step.completed_at = now
                step.duration_ms = round((now - step.started_at) * 1000, 1)

                safe_exec(
                    "UPDATE execution_steps SET output_data=?, status=?, error_message=?, "
                    "completed_at=?, duration_ms=? WHERE id=?",
                    [json.dumps(step.output_data, ensure_ascii=False), status,
                     error_message, now, step.duration_ms, step_id],
                )
                return

    def record_llm_call(self, step_id: str, model: str, provider: str,
                        messages: list, response: str, usage: dict = None,
                        temperature: float = 0.0, duration_ms: float = 0.0):
        trace = LLMTrace(
            id=f"llm-{uuid.uuid4().hex[:8]}", step_id=step_id,
            session_id=self.session_id, model=model, provider=provider,
            messages=messages, response=response, usage=usage or {},
            temperature=temperature, duration_ms=duration_ms,
        )
        self._llm_traces.append(trace)

        safe_exec(
            "INSERT INTO llm_traces "
            "(id, step_id, session_id, model, provider, messages, response, usage, temperature, duration_ms) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [trace.id, step_id, self.session_id, model, provider,
             json.dumps(messages, ensure_ascii=False), response,
             json.dumps(usage or {}, ensure_ascii=False), temperature, duration_ms],
        )

    def finish(self):
        total_ms = round((time.time() - self._started_at) * 1000, 1)
        safe_exec(
            "UPDATE replay_sessions SET status='completed', step_count=?, total_duration_ms=? WHERE id=?",
            [len(self._steps), total_ms, self.session_id],
        )

    @property
    def session(self) -> ReplaySession:
        return ReplaySession(
            id=self.session_id, run_id=self.run_id, module=self.module,
            page=self.page, agent=self.agent, step_count=len(self._steps),
            total_duration_ms=round((time.time() - self._started_at) * 1000, 1),
            status="recording",
        )


class ReplayPlayer:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self._session: Optional[ReplaySession] = None
        self._steps: list[ExecutionStep] = []
        self._llm_traces: dict[str, LLMTrace] = {}
        self._load()

    def _load(self):
        rows = safe_query("SELECT * FROM replay_sessions WHERE id=?", [self.session_id])
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

        step_rows = safe_query(
            "SELECT * FROM execution_steps WHERE session_id=? ORDER BY step_index ASC",
            [self.session_id],
        )
        for r in step_rows:
            self._steps.append(ExecutionStep(
                id=r["id"], session_id=r["session_id"],
                step_index=r["step_index"], step_type=r["step_type"], name=r["name"],
                input_data=r.get("input_data", {}), output_data=r.get("output_data", {}),
                status=r.get("status", ""), duration_ms=r.get("duration_ms", 0),
                error_message=r.get("error_message", ""), started_at=r.get("started_at", 0),
                completed_at=r.get("completed_at", 0), metadata=r.get("metadata", {}),
            ))

        trace_rows = safe_query(
            "SELECT * FROM llm_traces WHERE session_id=?", [self.session_id],
        )
        for r in trace_rows:
            trace = LLMTrace(
                id=r["id"], step_id=r["step_id"], session_id=r["session_id"],
                model=r.get("model", ""), provider=r.get("provider", ""),
                messages=r.get("messages", []), response=r.get("response", ""),
                usage=r.get("usage", {}), temperature=r.get("temperature", 0),
                duration_ms=r.get("duration_ms", 0),
            )
            self._llm_traces[trace.step_id] = trace

    @property
    def session(self) -> ReplaySession:
        return self._session

    def steps(self) -> list[ExecutionStep]:
        return self._steps

    def get_llm_trace(self, step_id: str) -> Optional[LLMTrace]:
        return self._llm_traces.get(step_id)

    def mock_execute(self, step: ExecutionStep) -> dict:
        if step.step_type == StepType.LLM_CALL:
            trace = self.get_llm_trace(step.id)
            if trace:
                return {"mock": True, "response": trace.response,
                        "usage": trace.usage, "model": trace.model}
        return {"mock": True, "output": step.output_data}

    def compare(self, new_outputs: dict[str, dict]) -> dict:
        comparison = {}
        for step in self._steps:
            recorded = step.output_data
            new = new_outputs.get(step.id, {})
            match = recorded == new
            comparison[step.id] = {
                "step_name": step.name, "match": match,
                "recorded_keys": list(recorded.keys()),
                "new_keys": list(new.keys()),
            }
        return comparison
