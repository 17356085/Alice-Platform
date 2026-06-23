"""Codegen Capability Providers."""
import time
from aitest.platform.capability_router.router import CapabilityProvider, ToolDef, ToolCall, ToolResult


class PageObjectGenProvider(CapabilityProvider):
    capability = "codegen.page_object"
    provider_name = "skill_delegate"
    priority = 100

    def get_tool_def(self) -> ToolDef:
        return ToolDef(
            name="codegen__page_object",
            description="生成Page Object类文件。保存到page/<module>_page/<PageName>Page.py。",
            parameters={
                "type": "object",
                "properties": {
                    "module": {"type": "string"},
                    "page": {"type": "string"},
                    "context_summary": {"type": "string", "description": "页面DOM结构摘要"},
                },
                "required": ["module", "page"],
            },
            capability=self.capability, side_effect="write", estimated_duration="20s",
        )

    def available(self, context: dict) -> bool:
        return True

    def execute(self, call: ToolCall, context: dict) -> ToolResult:
        start = time.time()
        try:
            from aitest.agents.skill_executor import run_skill
            module = call.arguments.get("module", context.get("module", ""))
            page = call.arguments.get("page", context.get("page", ""))
            ctx_summary = call.arguments.get("context_summary", "")
            response = run_skill(
                skill_id="automation/page-object-generator",
                user_input=f"模块:{module}\n页面:{page}\n上下文:{ctx_summary}",
                provider=context.get("provider", "claude"),
                context_vars={"module": module, "page": page},
            )
            return ToolResult(call_id=call.id, success=response.finish_reason!="error",
                content=f"Page Object生成完成。\n{response.content[:3000]}",
                data={"full_content": response.content}, duration_ms=(time.time()-start)*1000)
        except Exception as e:
            return ToolResult(call_id=call.id, success=False, content=f"生成失败: {e}", error=str(e))


class TestScriptGenProvider(CapabilityProvider):
    capability = "codegen.test_script"
    provider_name = "skill_delegate"
    priority = 100

    def get_tool_def(self) -> ToolDef:
        return ToolDef(
            name="codegen__test_script",
            description="生成pytest测试脚本。保存到script/<module>/test_<page>.py。",
            parameters={
                "type": "object",
                "properties": {
                    "module": {"type": "string"},
                    "page": {"type": "string"},
                    "testcase_summary": {"type": "string", "description": "测试用例设计摘要"},
                },
                "required": ["module", "page"],
            },
            capability=self.capability, side_effect="write", estimated_duration="25s",
        )

    def available(self, context: dict) -> bool:
        return True

    def execute(self, call: ToolCall, context: dict) -> ToolResult:
        start = time.time()
        try:
            from aitest.agents.skill_executor import run_skill
            module = call.arguments.get("module", context.get("module", ""))
            page = call.arguments.get("page", context.get("page", ""))
            tc_summary = call.arguments.get("testcase_summary", "")
            response = run_skill(
                skill_id="automation/test-script-generator",
                user_input=f"模块:{module}\n页面:{page}\n测试用例:{tc_summary}",
                provider=context.get("provider", "claude"),
                context_vars={"module": module, "page": page},
            )
            return ToolResult(call_id=call.id, success=response.finish_reason!="error",
                content=f"测试脚本生成完成。\n{response.content[:3000]}",
                data={"full_content": response.content}, duration_ms=(time.time()-start)*1000)
        except Exception as e:
            return ToolResult(call_id=call.id, success=False, content=f"生成失败: {e}", error=str(e))
