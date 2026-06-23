"""Browser Capability Providers."""
import time
from aitest.platform.capability_router.router import CapabilityProvider, ToolDef, ToolCall, ToolResult


class BrowserNavigateProvider(CapabilityProvider):
    capability = "browser.navigate"
    provider_name = "browseruse"
    priority = 100

    def get_tool_def(self) -> ToolDef:
        return ToolDef(
            name="browser__navigate",
            description="导航到目标页面URL。返回页面标题和主要内容摘要。",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "目标页面完整URL"},
                    "wait_until": {"type": "string", "enum": ["load", "networkidle", "visible"], "default": "networkidle"},
                },
                "required": ["url"],
            },
            capability=self.capability, side_effect="read", estimated_duration="5s",
        )

    def available(self, context: dict) -> bool:
        try:
            from aitest.discovery.browser_use import BrowserUseDiscovery
            return True
        except ImportError:
            return False

    def execute(self, call: ToolCall, context: dict) -> ToolResult:
        start = time.time()
        try:
            from aitest.bu_adapter import BrowserUseDriver
            driver = BrowserUseDriver()
            info = driver.navigate(url=call.arguments["url"], wait_until=call.arguments.get("wait_until", "networkidle"))
            return ToolResult(call_id=call.id, success=True,
                content=f"已导航: {info.get('title','N/A')}\nURL: {info.get('url', call.arguments['url'])}\n{str(info.get('summary',''))[:2000]}",
                data=info, duration_ms=(time.time()-start)*1000)
        except Exception as e:
            return ToolResult(call_id=call.id, success=False, content=f"导航失败: {e}", error=str(e), duration_ms=(time.time()-start)*1000)


class BrowserScreenshotProvider(CapabilityProvider):
    capability = "browser.screenshot"
    provider_name = "browseruse"
    priority = 100

    def get_tool_def(self) -> ToolDef:
        return ToolDef(
            name="browser__screenshot",
            description="截取当前页面截图。返回截图文件路径。",
            parameters={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "截图文件名"},
                    "full_page": {"type": "boolean", "default": False},
                },
                "required": [],
            },
            capability=self.capability, side_effect="write", estimated_duration="3s",
        )

    def available(self, context: dict) -> bool:
        try:
            from aitest.bu_adapter import BrowserUseDriver
            return True
        except ImportError:
            return False

    def execute(self, call: ToolCall, context: dict) -> ToolResult:
        start = time.time()
        try:
            from aitest.bu_adapter import BrowserUseDriver
            from aitest.platform.paths import get_context_modules
            driver = BrowserUseDriver()
            module = context.get("module", "unknown")
            page = context.get("page", "unknown")
            evidence_dir = get_context_modules() / module / "pages" / page / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)
            filename = call.arguments.get("filename", f"screenshot_{int(time.time())}.png")
            path = evidence_dir / filename
            driver.screenshot(str(path), full_page=call.arguments.get("full_page", False))
            return ToolResult(call_id=call.id, success=True,
                content=f"截图已保存: {path}", data={"path": str(path)}, duration_ms=(time.time()-start)*1000)
        except Exception as e:
            return ToolResult(call_id=call.id, success=False, content=f"截图失败: {e}", error=str(e), duration_ms=(time.time()-start)*1000)
