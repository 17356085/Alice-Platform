"""
P1-1: MCP Prompts — 预制提示模板。
_PromptDef 注册表 + list_prompts / get_prompt 处理器。
"""
from dataclasses import dataclass
from mcp.types import Prompt, PromptArgument, PromptMessage, TextContent

from aitest.mcp.prompts import templates


@dataclass
class PromptDef:
    """MCP Prompt 注册项。"""
    name: str
    title: str
    description: str
    arguments: list[PromptArgument]
    template: str  # {variable} 占位


def _build_prompt_registry() -> dict[str, PromptDef]:
    """构建 Prompt 注册表。"""
    return {
        "generate-page-object": PromptDef(
            name="generate-page-object",
            title="生成 Page Object",
            description="从 PAGE_CONTEXT.md + PAGE_INTERFACE.yaml 生成符合 8 条代码红线的 Page Object 类",
            arguments=[
                PromptArgument(name="module", description="模块名", required=True),
                PromptArgument(name="page", description="页面 slug", required=True),
            ],
            template=templates.GENERATE_PAGE_OBJECT,
        ),
        "analyze-failure": PromptDef(
            name="analyze-failure",
            title="分析测试失败",
            description="分析 pytest 失败输出，匹配已知问题，给出根因和修复方案",
            arguments=[
                PromptArgument(name="module", description="模块名", required=True),
                PromptArgument(name="error_output", description="pytest 失败输出 / 堆栈信息", required=True),
            ],
            template=templates.ANALYZE_FAILURE,
        ),
        "design-test-cases": PromptDef(
            name="design-test-cases",
            title="设计测试用例",
            description="从 PAGE_CONTEXT.md + RISK_MODEL.md 设计覆盖 P0/P1/P2 优先级的测试用例",
            arguments=[
                PromptArgument(name="module", description="模块名", required=True),
                PromptArgument(name="page", description="页面 slug", required=True),
            ],
            template=templates.DESIGN_TEST_CASES,
        ),
        "review-code": PromptDef(
            name="review-code",
            title="代码红线检查",
            description="对生成的 Page Object / 测试脚本执行 8 条代码红线检查并给出修复建议",
            arguments=[
                PromptArgument(name="file", description="要检查的文件路径", required=True),
            ],
            template=templates.REVIEW_CODE,
        ),
        "sop-status": PromptDef(
            name="sop-status",
            title="查看模块 SOP 进度",
            description="查看指定模块的 SOP 流水线进度，判断从哪个 Phase 继续",
            arguments=[
                PromptArgument(name="module", description="模块名（留空查看全部）", required=False),
            ],
            template=templates.SOP_STATUS,
        ),
        "bug-report": PromptDef(
            name="bug-report",
            title="生成标准化 Bug 报告",
            description="从测试失败输出生成结构化的 Bug 报告（含复现步骤/根因/严重度）",
            arguments=[
                PromptArgument(name="module", description="模块名", required=True),
                PromptArgument(name="test_name", description="失败的测试用例名", required=True),
                PromptArgument(name="failure_output", description="pytest 失败输出", required=True),
            ],
            template=templates.BUG_REPORT,
        ),
    }


PROMPT_REGISTRY: dict[str, PromptDef] = _build_prompt_registry()


def build_list_prompts_handler():
    """返回 list_prompts 处理器（闭包捕获 server）。"""
    async def handler() -> list[Prompt]:
        return [
            Prompt(name=p.name, title=p.title, description=p.description,
                   arguments=p.arguments if p.arguments else None)
            for p in PROMPT_REGISTRY.values()
        ]
    return handler


def build_get_prompt_handler():
    """返回 get_prompt 处理器（闭包捕获 server）。"""
    async def handler(name: str, arguments: dict[str, str] | None = None) -> list[PromptMessage]:
        pdef = PROMPT_REGISTRY.get(name)
        if not pdef:
            return [PromptMessage(
                role="user",
                content=TextContent(type="text",
                    text=f"Unknown prompt: {name}. Available: {sorted(PROMPT_REGISTRY.keys())}")
            )]

        args = arguments or {}
        rendered = pdef.template
        for key, value in args.items():
            rendered = rendered.replace("{" + key + "}", value)

        return [PromptMessage(role="user", content=TextContent(type="text", text=rendered))]
    return handler
