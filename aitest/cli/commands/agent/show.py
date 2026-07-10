"""
aitest agent show — 显示 Agent 详情。
"""

import typer
from typing import Optional
import httpx
from aitest.cli.utils.output import format_output, print_error
from aitest.cli.utils.config import get_resolver


def agent_show(
    agent_id: str = typer.Argument(..., help="Agent ID"),
    version: Optional[str] = typer.Option(
        None,
        "--version", "-v",
        help="Agent 版本（默认最新）"
    ),
    output: str = typer.Option(
        "table",
        "--output", "-o",
        help="输出格式 (table/json/yaml)"
    ),
):
    """
    显示 Agent 详情。

    示例:

      aitest agent show page-observer
      aitest agent show page-observer --version 2.5.0
      aitest agent show page-observer --output json
    """
    # 解析配置
    resolver = get_resolver()
    api_base = resolver.resolve(
        cli_value=None,
        env_var="AITEST_API_BASE",
        config_key="api.base_url",
        default="http://localhost:8000"
    )

    # 构造查询参数
    params = {}
    if version:
        params["version"] = version

    # 发送请求
    try:
        response = httpx.get(
            f"{api_base}/api/v1/agents/{agent_id}",
            params=params,
            timeout=10.0,
        )
        response.raise_for_status()
        result = response.json()

        # 输出结果
        if output in ("json", "yaml"):
            format_output(result, output_format=output)
        else:
            # 格式化关键信息
            agent = result.get("agent", result)
            table_data = {
                "agent_id": agent["id"],
                "version": agent.get("version", "N/A"),
                "description": agent.get("description", "N/A"),
                "model": agent.get("model", "N/A"),
                "temperature": agent.get("temperature", "N/A"),
                "skills_count": len(agent.get("skills", [])),
                "skills": ", ".join([s if isinstance(s, str) else s.get("id", "?") for s in agent.get("skills", [])][:5]),
            }

            format_output(
                table_data,
                output_format="table",
                title=f"Agent 详情: {agent_id}"
            )

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            print_error(f"Agent 不存在: {agent_id}")
        else:
            print_error(f"API 请求失败: {e.response.status_code}")
            print_error(e.response.text)
        raise typer.Exit(1)
    except httpx.RequestError as e:
        print_error(f"网络错误: {e}")
        print_error(f"请确认测试工作台已启动: aitest server start")
        raise typer.Exit(1)
