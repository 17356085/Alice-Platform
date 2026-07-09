"""Phase 4 extension template samples.

This file is intentionally small and reusable:
- provider extension sample
- capability extension sample
- graph extension sample

Future extensions can copy these patterns and reuse the shared assertions.
"""

from __future__ import annotations

from alice_engine.capabilities import (
    CapabilityProvider,
    ToolCall,
    ToolDef,
    ToolResult,
    capability_contract,
)
from alice_engine.providers.base import LLMProvider, LLMResponse
from alice_engine.workflow import get_graph_contract, register_graph

from .contract_support import (
    assert_capability_contract_shape,
    assert_graph_contract_shape,
    assert_provider_contract_shape,
)


class SampleProvider(LLMProvider):
    provider_name = "sample-provider"
    provider_description = "A sample provider used as the extension contract template."
    provider_supports_tools = True
    provider_supports_streaming = False

    def complete(self, system_prompt, user_prompt, tools=None, **kwargs):
        return LLMResponse(content="sample provider response", model="sample-provider")

    def supports_tools(self):
        return True


class SampleCapabilityProvider:
    capability = "sample.capability"
    provider_name = "sample-capability"
    priority = 10

    def get_tool_def(self) -> ToolDef:
        return ToolDef(
            name="sample__echo",
            description="Echo sample payload",
            parameters={
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                },
                "required": ["message"],
                "additionalProperties": False,
            },
            capability=self.capability,
            side_effect="read",
            estimated_duration="1s",
            requires_confirmation=False,
        )

    def available(self, context: dict) -> bool:
        return True

    def execute(self, call: ToolCall, context: dict) -> ToolResult:
        message = call.arguments.get("message", "")
        return ToolResult(call_id=call.id, success=True, content=message, data={"echo": message})


def build_sample_graph(**kwargs):
    return {"graph_id": "sample.graph", "kwargs": kwargs}


def test_extension_contract_template_reuses_shared_assertions():
    provider_contract = SampleProvider.contract()
    assert_provider_contract_shape(provider_contract, expected_name="sample-provider")
    assert provider_contract.supports_tools is True

    sample_capability: CapabilityProvider = SampleCapabilityProvider()
    capability_contract_ = capability_contract(sample_capability)
    assert_capability_contract_shape(
        capability_contract_,
        expected_capability="sample.capability",
        expected_tool_name="sample__echo",
    )

    register_graph(
        "sample.graph",
        build_sample_graph,
        name="Sample Graph",
        description="A sample graph used as the extension template.",
        module="alice_engine.tests",
        builder_name="build_sample_graph",
        entrypoint="tests.sample_graph",
        supports_checkpoint=True,
        supports_parallel=False,
    )
    graph_contract = get_graph_contract("sample.graph")
    assert_graph_contract_shape(graph_contract, expected_graph_id="sample.graph")
    assert graph_contract.name == "Sample Graph"
