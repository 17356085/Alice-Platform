"""
aitest agent list — 列出所有 Agent。
"""

import typer
import httpx
from aitest.cli.utils.output import format_output, print_error
from aitest.cli.utils.config import get_resolver


def agent_list(
    output: str = typer.Option(
        "table",
        "--output", "-o",
        help="输出格式 (table/json/yaml)"
    ),
):
    """
    列出所有 Agent。

    示例:

      aitest agent list
      aitest agent list --output json
    """
    # 解析配置
    resolver = get_resolver()
    api_base = resolver.resolve(
        cli_value=None,
        env_var="AITEST_API_BASE",
        config_key="api.base_url",
        default="http://localhost:8000"
    )

    # 发送请求
    try:
        response = httpx.get(
            f"{api_base}/api/v1/agents",
            timeout=10.0,
        )
        response.raise_for_status()
        result = response.json()

        agents = result.get("agents", [])

        # 输出结果
        if output in ("json", "yaml"):
            format_output(result, output_format=output)
        else:
            if not agents:
                print_error("未找到 Agent")
                raise typer.Exit(0)

            # 格式化表格数据
            table_data = [
                {
                    "agent_id": a["id"],
                    "version": a.get("version", "N/A"),
                    "description": a.get("description", "")[:50],
                    "skills": str(len(a.get("skills", []))),
                }
                for a in agents
            ]

            format_output(
                table_data,
                output_format="table",
                columns=["agent_id", "version", "description", "skills"],
                title=f"Agent 列表 (共 {len(agents)} 个)"
            )

    except httpx.HTTPStatusError as e:
        print_error(f"API 请求失败: {e.response.status_code}")
        print_error(e.response.text)
        raise typer.Exit(1)
    except httpx.RequestError as e:
        print_error(f"网络错误: {e}")
        print_error(f"请确认测试工作台已启动: aitest server start")
        raise typer.Exit(1)
