"""
aitest run list — 列出 Run 记录（增强版）。

支持高级筛选、分页、排序和导出功能。
"""

import typer
from typing import Optional
import httpx
from aitest.cli.utils.output import format_output, print_error
from aitest.cli.utils.config import get_resolver


def run_list(
    status: Optional[str] = typer.Option(
        None,
        "--status", "-s",
        help="按状态筛选 (completed/running/failed/pending，支持逗号分隔多个)"
    ),
    target_type: Optional[str] = typer.Option(
        None,
        "--target-type",
        help="按目标类型筛选 (agent/workflow/skill/evaluation)"
    ),
    module: Optional[str] = typer.Option(
        None,
        "--module", "-m",
        help="按模块筛选"
    ),
    from_date: Optional[str] = typer.Option(
        None,
        "--from",
        help="开始时间筛选 (格式: YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS)"
    ),
    to_date: Optional[str] = typer.Option(
        None,
        "--to",
        help="结束时间筛选 (格式: YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS)"
    ),
    sort_by: str = typer.Option(
        "created_at",
        "--sort",
        help="排序字段 (created_at/status/module/duration)"
    ),
    order: str = typer.Option(
        "desc",
        "--order",
        help="排序顺序 (asc/desc)"
    ),
    limit: int = typer.Option(
        20,
        "--limit", "-n",
        help="每页返回数量"
    ),
    offset: int = typer.Option(
        0,
        "--offset",
        help="跳过前 N 条记录（分页）"
    ),
    export: Optional[str] = typer.Option(
        None,
        "--export",
        help="导出到文件 (格式: json/csv/yaml)"
    ),
    output: str = typer.Option(
        "table",
        "--output", "-o",
        help="输出格式 (table/json/yaml)"
    ),
):
    """
    列出 Run 记录（增强版）。

    示例:

      # 列出所有 Run
      aitest run list

      # 列出失败的 Run
      aitest run list --status failed

      # 列出多个状态的 Run
      aitest run list --status completed,failed

      # 时间范围筛选
      aitest run list --from 2026-07-01 --to 2026-07-11

      # 分页查询
      aitest run list --limit 10 --offset 20

      # 排序
      aitest run list --sort duration --order desc

      # 导出到文件
      aitest run list --export json > runs.json
      aitest run list --export csv > runs.csv

      # JSON 格式输出（用于脚本）
      aitest run list --status completed --output json | jq '.runs[0].run_id'
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
    params = {
        "limit": limit,
        "offset": offset,
        "sort_by": sort_by,
        "order": order,
    }

    # 状态筛选（支持逗号分隔）
    if status:
        params["status"] = status

    if target_type:
        params["target_type"] = target_type

    if module:
        params["module"] = module

    # 时间范围筛选
    if from_date:
        params["from_date"] = from_date

    if to_date:
        params["to_date"] = to_date

    # 发送请求
    try:
        response = httpx.get(
            f"{api_base}/api/v1/runs",
            params=params,
            timeout=10.0,
        )
        response.raise_for_status()
        result = response.json()

        runs = result.get("runs", [])
        total = result.get("total", len(runs))

        # 导出功能
        if export:
            _export_runs(runs, export, total, offset, limit)
            return

        # 输出结果
        if output in ("json", "yaml"):
            format_output(result, output_format=output)
        else:
            if not runs:
                print_error("未找到 Run 记录")
                raise typer.Exit(0)

            # 格式化表格数据
            table_data = [
                {
                    "run_id": r["run_id"][:12] + "...",
                    "target": f"{r['target']['type']}:{r['target']['id'][:20]}",
                    "module": r.get("module", "N/A"),
                    "status": r["status"],
                    "created_at": r.get("created_at", "N/A")[:19],
                }
                for r in runs
            ]

            # 分页提示
            page_info = f"第 {offset + 1}-{offset + len(runs)} 条，共 {total} 条"

            format_output(
                table_data,
                output_format="table",
                columns=["run_id", "target", "module", "status", "created_at"],
                title=f"Run 列表 ({page_info})"
            )

            # 分页导航提示
            if total > offset + len(runs):
                next_offset = offset + limit
                print_error(f"\n💡 查看下一页: aitest run list --offset {next_offset} --limit {limit}")

    except httpx.HTTPStatusError as e:
        print_error(f"API 请求失败: {e.response.status_code}")
        print_error(e.response.text)
        raise typer.Exit(1)
    except httpx.RequestError as e:
        print_error(f"网络错误: {e}")
        print_error(f"请确认测试工作台已启动: aitest server start")
        raise typer.Exit(1)


def _export_runs(runs: list, format: str, total: int, offset: int, limit: int):
    """导出 Run 记录到文件。"""
    import json
    import csv
    import yaml
    import sys
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if format == "json":
        # JSON 导出
        output_data = {
            "export_info": {
                "timestamp": timestamp,
                "total": total,
                "offset": offset,
                "limit": limit,
                "count": len(runs),
            },
            "runs": runs,
        }
        json.dump(output_data, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")

    elif format == "csv":
        # CSV 导出
        if not runs:
            print_error("没有数据可导出")
            return

        writer = csv.DictWriter(
            sys.stdout,
            fieldnames=["run_id", "target_type", "target_id", "module", "status", "created_at", "duration"],
        )
        writer.writeheader()

        for r in runs:
            writer.writerow({
                "run_id": r["run_id"],
                "target_type": r["target"]["type"],
                "target_id": r["target"]["id"],
                "module": r.get("module", ""),
                "status": r["status"],
                "created_at": r.get("created_at", ""),
                "duration": r.get("duration", ""),
            })

    elif format == "yaml":
        # YAML 导出
        output_data = {
            "export_info": {
                "timestamp": timestamp,
                "total": total,
                "offset": offset,
                "limit": limit,
                "count": len(runs),
            },
            "runs": runs,
        }
        yaml.dump(output_data, sys.stdout, allow_unicode=True, default_flow_style=False)

    else:
        print_error(f"不支持的导出格式: {format}")
        print_error("支持的格式: json, csv, yaml")
        raise typer.Exit(1)
