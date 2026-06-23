"""Knowledge/RAG Capability Providers."""
import time
from aitest.platform.capability_router.router import CapabilityProvider, ToolDef, ToolCall, ToolResult


class RAGSearchProvider(CapabilityProvider):
    capability = "rag.search"
    provider_name = "chromadb"
    priority = 100

    def get_tool_def(self) -> ToolDef:
        return ToolDef(
            name="rag__search",
            description="搜索测试知识库: known_issues, ui_patterns, locator_history, business_rules, historical_failures。",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索查询"},
                    "collection": {"type": "string", "enum": ["known_issues","ui_patterns","locator_history","business_rules","historical_failures","all"], "default": "all"},
                    "top_k": {"type": "integer", "default": 5, "maximum": 10},
                },
                "required": ["query"],
            },
            capability=self.capability, side_effect="read", estimated_duration="0.5s",
        )

    def available(self, context: dict) -> bool:
        try:
            from aitest.platform.knowledge import get_knowledge
            return get_knowledge().available()
        except Exception:
            return False

    def execute(self, call: ToolCall, context: dict) -> ToolResult:
        start = time.time()
        try:
            from aitest.platform.knowledge import get_knowledge
            store = get_knowledge()
            results = store.search(query=call.arguments["query"], collection=call.arguments.get("collection", "all"), top_k=min(call.arguments.get("top_k", 5), 10))
            if not results:
                return ToolResult(call_id=call.id, success=True, content="未找到相关结果。")
            lines = [f"[{i+1}] (score: {r.get('score',0):.2f}) {str(r.get('content',''))[:500]}" for i, r in enumerate(results)]
            return ToolResult(call_id=call.id, success=True, content="\n\n".join(lines), data=results, duration_ms=(time.time()-start)*1000)
        except Exception as e:
            return ToolResult(call_id=call.id, success=False, content=f"RAG搜索失败: {e}", error=str(e))


class BusinessRuleLookupProvider(CapabilityProvider):
    capability = "rag.business_rules"
    provider_name = "chromadb"
    priority = 100

    def get_tool_def(self) -> ToolDef:
        return ToolDef(
            name="rag__business_rules",
            description="查询模块/页面的业务规则约束。",
            parameters={
                "type": "object",
                "properties": {
                    "module": {"type": "string"},
                    "page": {"type": "string"},
                },
                "required": ["module"],
            },
            capability=self.capability, side_effect="read", estimated_duration="0.3s",
        )

    def available(self, context: dict) -> bool:
        try:
            from aitest.platform.knowledge import get_knowledge
            return get_knowledge().available()
        except Exception:
            return False

    def execute(self, call: ToolCall, context: dict) -> ToolResult:
        start = time.time()
        try:
            from aitest.platform.knowledge import get_knowledge
            store = get_knowledge()
            module = call.arguments.get("module",""); page = call.arguments.get("page","")
            query = f"business_rules module={module}" + (f" page={page}" if page else "")
            results = store.search(query=query, collection="business_rules", top_k=5)
            lines = [f"[{i+1}] {r.get('content','')[:300]}" for i, r in enumerate(results)]
            return ToolResult(call_id=call.id, success=True,
                content="\n\n".join(lines) if lines else f"模块 '{module}' 未找到业务规则。", data=results)
        except Exception as e:
            return ToolResult(call_id=call.id, success=False, content=f"查询失败: {e}", error=str(e))
