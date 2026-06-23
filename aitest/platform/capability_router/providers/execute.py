"""Execute Capability Providers — pytest, Python script."""
import time
from aitest.platform.capability_router.router import CapabilityProvider, ToolDef, ToolCall, ToolResult


class PytestProvider(CapabilityProvider):
    capability = "execute.pytest"
    provider_name = "pytest"
    priority = 100

    def get_tool_def(self) -> ToolDef:
        return ToolDef(
            name="execute__pytest",
            description="运行pytest测试并返回结构化结果（通过/失败/错误/跳过数）。",
            parameters={
                "type": "object",
                "properties": {
                    "module": {"type": "string", "description": "测试模块名称"},
                    "test_file": {"type": "string", "description": "指定测试文件（可选）"},
                    "marker": {"type": "string", "description": "pytest marker过滤（可选）"},
                    "timeout": {"type": "integer", "default": 300},
                },
                "required": ["module"],
            },
            capability=self.capability, side_effect="execute", estimated_duration="30s",
        )

    def available(self, context: dict) -> bool:
        return True

    def execute(self, call: ToolCall, context: dict) -> ToolResult:
        start = time.time()
        try:
            from aitest.mcp.tools.execution import run_pytest
            r = run_pytest(
                module=call.arguments.get("module", ""),
                test_file=call.arguments.get("test_file", ""),
                marker=call.arguments.get("marker", ""),
                timeout=call.arguments.get("timeout", 300),
            )
            content = (
                f"测试结果: {r.get('status','?').upper()}\n"
                f"总计:{r.get('total',0)} | 通过:{r.get('passed',0)} | 失败:{r.get('failed',0)} | "
                f"错误:{r.get('error',0)} | 跳过:{r.get('skipped',0)}\n"
                f"耗时:{r.get('duration_seconds',0)}s\n"
            )
            if r.get("status") == "fail":
                content += f"失败详情:\n{str(r.get('failure_output',''))[:2000]}"
            return ToolResult(call_id=call.id, success=r.get("status")=="pass",
                content=content, data=r, duration_ms=(time.time()-start)*1000)
        except Exception as e:
            return ToolResult(call_id=call.id, success=False, content=f"Pytest执行失败: {e}", error=str(e))


class PythonScriptProvider(CapabilityProvider):
    capability = "execute.python"
    provider_name = "subprocess"
    priority = 100

    def get_tool_def(self) -> ToolDef:
        return ToolDef(
            name="execute__python",
            description="执行Python脚本。用于验证生成代码语法或运行工具脚本。",
            parameters={
                "type": "object",
                "properties": {
                    "script_path": {"type": "string", "description": "Python脚本绝对路径"},
                    "args": {"type": "array", "items": {"type": "string"}, "default": []},
                    "timeout": {"type": "integer", "default": 60},
                },
                "required": ["script_path"],
            },
            capability=self.capability, side_effect="execute", estimated_duration="10s",
        )

    def available(self, context: dict) -> bool:
        return True

    def execute(self, call: ToolCall, context: dict) -> ToolResult:
        start = time.time()
        try:
            from aitest.infra.secure_subprocess import secure_run
            result = secure_run(
                ["python", call.arguments["script_path"]] + call.arguments.get("args", []),
                capture_output=True, text=True, timeout=call.arguments.get("timeout", 60), check=False,
            )
            output = (result.stdout or "") + (result.stderr or "")
            return ToolResult(call_id=call.id, success=result.returncode==0,
                content=f"Exit: {result.returncode}\n\n{output[:3000]}",
                data={"exit_code": result.returncode}, duration_ms=(time.time()-start)*1000)
        except Exception as e:
            return ToolResult(call_id=call.id, success=False, content=f"脚本执行失败: {e}", error=str(e))
