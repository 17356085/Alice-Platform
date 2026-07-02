"""
CLI 错误处理器 — 提供友好的错误提示和恢复建议。
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


# ── 错误类型定义 ──────────────────────────────────────────────────

ERROR_MESSAGES = {
    # 项目配置错误
    "project_not_found": {
        "title": "项目不存在",
        "message": "未找到项目目录",
        "suggestion": "请检查项目路径是否正确，或使用 Phase 0 创建新项目",
    },
    "project_yaml_missing": {
        "title": "配置文件缺失",
        "message": "未找到 .tlo/project.yaml",
        "suggestion": "运行 alice run 将自动触发 Phase 0 配置",
    },
    "project_yaml_invalid": {
        "title": "配置文件无效",
        "message": "project.yaml 格式错误",
        "suggestion": "检查 YAML 语法，或删除后重新配置",
    },

    # 模块错误
    "module_not_found": {
        "title": "模块不存在",
        "message": "未找到指定模块",
        "suggestion": "使用 alice list-modules 查看可用模块",
    },
    "module_dir_missing": {
        "title": "模块目录缺失",
        "message": "模块目录不存在",
        "suggestion": "运行 Phase 0 将自动创建模块目录",
    },

    # LLM 错误
    "llm_api_key_missing": {
        "title": "API Key 缺失",
        "message": "未配置 LLM API Key",
        "suggestion": "在 .env 文件中设置 ANTHROPIC_API_KEY 或其他 API Key",
    },
    "llm_api_error": {
        "title": "LLM API 错误",
        "message": "调用 LLM API 失败",
        "suggestion": "检查网络连接和 API Key 是否正确",
    },
    "llm_rate_limit": {
        "title": "API 限流",
        "message": "LLM API 请求过于频繁",
        "suggestion": "等待一段时间后重试，或使用 --mock-llm 测试",
    },
    "llm_timeout": {
        "title": "API 超时",
        "message": "LLM API 请求超时",
        "suggestion": "检查网络连接，或使用 --mock-llm 测试",
    },

    # 文件错误
    "file_not_found": {
        "title": "文件不存在",
        "message": "未找到指定文件",
        "suggestion": "检查文件路径是否正确",
    },
    "file_permission_error": {
        "title": "权限错误",
        "message": "无法读写文件",
        "suggestion": "检查文件权限，或以管理员身份运行",
    },
    "file_encoding_error": {
        "title": "编码错误",
        "message": "文件编码不正确",
        "suggestion": "确保文件使用 UTF-8 编码",
    },

    # 网络错误
    "network_error": {
        "title": "网络错误",
        "message": "网络连接失败",
        "suggestion": "检查网络连接是否正常",
    },
    "url_not_accessible": {
        "title": "URL 不可访问",
        "message": "无法访问目标 URL",
        "suggestion": "检查 URL 是否正确，或网络是否通畅",
    },

    # 执行错误
    "execution_failed": {
        "title": "执行失败",
        "message": "SOP 执行过程中发生错误",
        "suggestion": "查看详细日志，或使用 --verbose 参数获取更多信息",
    },
    "agent_failed": {
        "title": "Agent 失败",
        "message": "Agent 执行失败",
        "suggestion": "检查 Agent 配置和 LLM Provider",
    },
    "skill_failed": {
        "title": "Skill 失败",
        "message": "Skill 执行失败",
        "suggestion": "检查 Skill 定义和输入参数",
    },

    # 门禁错误
    "gate_failed": {
        "title": "门禁不通过",
        "message": "质量门禁检查未通过",
        "suggestion": "查看门禁报告，修复问题后重试",
    },

    # 超时错误
    "timeout": {
        "title": "执行超时",
        "message": "执行时间超过限制",
        "suggestion": "检查是否有死循环，或增加超时时间",
    },

    # 中断
    "user_interrupt": {
        "title": "用户中断",
        "message": "用户按下了 Ctrl+C",
        "suggestion": "执行已被中断，可以使用 alice resume 继续",
    },
}


# ── 错误处理函数 ──────────────────────────────────────────────────

def print_error(error_type: str, detail: str = "", exception: Exception = None):
    """打印友好的错误信息。"""
    error_info = ERROR_MESSAGES.get(error_type, {
        "title": "未知错误",
        "message": error_type,
        "suggestion": "请查看详细日志",
    })

    # 构建错误信息
    text = Text()
    text.append(f"❌ {error_info['title']}\n\n", style="bold red")
    text.append(f"错误: {error_info['message']}\n")

    if detail:
        text.append(f"详情: {detail}\n")

    if exception:
        text.append(f"异常: {str(exception)[:200]}\n")

    text.append(f"\n💡 建议: {error_info['suggestion']}", style="yellow")

    # 显示面板
    panel = Panel(text, title="[bold red]错误[/bold red]", border_style="red")
    console.print(panel)


def print_warning(message: str, suggestion: str = ""):
    """打印警告信息。"""
    console.print(f"[yellow]⚠️  {message}[/yellow]")
    if suggestion:
        console.print(f"  💡 {suggestion}", style="dim")


def print_success(message: str):
    """打印成功信息。"""
    console.print(f"[green]✅ {message}[/green]")


def print_info(message: str):
    """打印信息。"""
    console.print(f"[blue]ℹ️  {message}[/blue]")


# ── 异常处理 ──────────────────────────────────────────────────

def handle_exception(e: Exception, verbose: bool = False):
    """处理异常并打印友好的错误信息。"""
    import traceback

    # 根据异常类型选择错误类型
    error_type = _classify_exception(e)

    # 打印错误信息
    print_error(error_type, exception=e)

    # 如果需要详细信息，打印堆栈跟踪
    if verbose:
        console.print("\n[dim]详细堆栈跟踪:[/dim]")
        console.print(traceback.format_exc())


def _classify_exception(e: Exception) -> str:
    """根据异常类型分类。"""
    exception_type = type(e).__name__

    # 文件相关错误
    if isinstance(e, FileNotFoundError):
        return "file_not_found"
    elif isinstance(e, PermissionError):
        return "file_permission_error"
    elif isinstance(e, UnicodeDecodeError):
        return "file_encoding_error"

    # 网络相关错误
    elif "ConnectionError" in exception_type or "Timeout" in exception_type:
        return "network_error"
    elif "HTTPStatusError" in exception_type:
        if "429" in str(e):
            return "llm_rate_limit"
        elif "401" in str(e) or "403" in str(e):
            return "llm_api_key_missing"
        else:
            return "llm_api_error"

    # LLM 相关错误
    elif "APIError" in exception_type or "APIStatusError" in exception_type:
        return "llm_api_error"
    elif "RateLimitError" in exception_type:
        return "llm_rate_limit"
    elif "Timeout" in exception_type:
        return "llm_timeout"

    # YAML 相关错误
    elif "YAMLError" in exception_type:
        return "project_yaml_invalid"

    # 超时错误
    elif "TimeoutError" in exception_type:
        return "timeout"

    # 默认
    else:
        return "execution_failed"
