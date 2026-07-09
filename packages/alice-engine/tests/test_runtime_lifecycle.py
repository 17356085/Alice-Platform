from __future__ import annotations

from types import SimpleNamespace

from alice_engine.core.runtime_lifecycle import MCPClientLifecycle, ReplayStepSink


class _AsyncClosableClient:
    def __init__(self):
        self.closed = False

    async def close(self):
        self.closed = True


class _SyncClosableClient:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_mcp_lifecycle_connect_returns_clients_and_tools():
    lifecycle = MCPClientLifecycle(
        agent_name="automation-agent",
        log_fn=lambda _msg: None,
        create_clients_fn=lambda agent: ([f"{agent}-client"], {"tool": {"agent": agent}}),
    )

    clients, tools = lifecycle.connect()

    assert clients == ["automation-agent-client"]
    assert tools == {"tool": {"agent": "automation-agent"}}


def test_mcp_lifecycle_close_all_supports_sync_and_async_clients():
    async_client = _AsyncClosableClient()
    sync_client = _SyncClosableClient()
    clients = [async_client, sync_client]
    lifecycle = MCPClientLifecycle(agent_name="automation-agent", log_fn=lambda _msg: None)

    lifecycle.close_all(clients)

    assert async_client.closed is True
    assert sync_client.closed is True
    assert clients == []


def test_replay_sink_records_skill_step_payloads():
    calls: list[tuple] = []

    class _Recorder:
        def begin_step(self, kind, skill_id, input_data=None, metadata=None):
            calls.append(("begin", kind, skill_id, input_data, metadata))
            return SimpleNamespace(id="step-1")

        def record_llm_call(self, step_id, model, provider, messages, content, usage=None):
            calls.append(("record", step_id, model, provider, messages, content, usage))

        def end_step(self, step_id, output_data=None, status=None, error_message=""):
            calls.append(("end", step_id, output_data, status, error_message))

    sink = ReplayStepSink(recorder=_Recorder())
    step = sink.begin_skill_step(
        skill_id="automation/demo",
        skill_index=2,
        module="equipment",
        page="alarm-config",
        agent_name="automation-agent",
    )
    response = SimpleNamespace(
        model="demo-model",
        content="ok",
        finish_reason="stop",
        usage={"input": 10, "output": 20},
        tool_calls=[{"name": "x"}],
        tool_results=[{"ok": True}],
    )

    sink.record_skill_response(replay_step=step, response=response, provider="mock")

    assert calls[0] == (
        "begin",
        "skill",
        "automation/demo",
        {"module": "equipment", "page": "alarm-config", "agent": "automation-agent"},
        {"skill_index": 2},
    )
    assert calls[1] == ("record", "step-1", "demo-model", "mock", [], "ok", {"input": 10, "output": 20})
    assert calls[2] == (
        "end",
        "step-1",
        {"finish_reason": "stop", "tool_calls": [{"name": "x"}], "tool_results": [{"ok": True}]},
        "success",
        "",
    )
