"""workflow validate 命令 — 验证 Workflow 配置。

检查 Workflow 配置的合法性：
- 必填字段检查
- Agent 引用有效性
- Step ID 唯一性
- Transition 引用完整性
- Schema 格式检查
"""

import json
import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()


def validate_command(workflow_id: str, output_format: str = "table"):
    """验证 Workflow 配置。

    示例:
        aitest workflow validate my-workflow
        aitest workflow validate my-workflow --output json
    """
    from aitest.cli.config import CLIConfig

    config = CLIConfig()

    try:
        # 获取活跃项目路径
        project_path = config.active_project_path
        if not project_path:
            console.print("[red]✗ 未找到活跃项目，请先使用 'aitest project set --id=<id>'[/red]")
            raise ValueError("未找到活跃项目")

        workflow_dir = Path(project_path) / ".tlo" / "workflows"
        workflow_file = workflow_dir / f"{workflow_id}.yaml"

        if not workflow_file.exists():
            console.print(f"[red]✗ Workflow 不存在: {workflow_id}[/red]")
            raise ValueError(f"Workflow 不存在: {workflow_id}")

        # 加载 Workflow
        with open(workflow_file, "r", encoding="utf-8") as f:
            workflow_data = yaml.safe_load(f)

        # 执行验证
        checks = _validate_workflow(workflow_data, Path(project_path))

        # 输出
        if output_format == "json":
            result = {
                "workflow_id": workflow_id,
                "valid": all(c["status"] == "ok" for c in checks),
                "checks": checks,
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        # 表格输出
        _print_validation_result(workflow_id, checks)

        # 返回退出码
        if not all(c["status"] == "ok" for c in checks):
            raise ValueError("Workflow 验证失败")

    except Exception as e:
        console.print(f"[red]✗ 验证失败: {e}[/red]")
        raise


def _validate_workflow(workflow_data: dict, project_path: Path) -> list[dict]:
    """执行 Workflow 验证。"""
    checks = []

    # 1. 必填字段检查
    required_fields = ["id", "name", "agents", "steps"]
    for field in required_fields:
        if field in workflow_data and workflow_data[field]:
            checks.append({
                "name": f"必填字段: {field}",
                "status": "ok",
                "detail": "存在",
            })
        else:
            checks.append({
                "name": f"必填字段: {field}",
                "status": "error",
                "detail": "缺失",
            })

    # 2. Agents 检查
    agents = workflow_data.get("agents", [])
    if agents:
        checks.append({
            "name": "Agents 列表",
            "status": "ok",
            "detail": f"{len(agents)} 个",
        })

        # 检查 Agent 定义是否存在
        agent_dir = project_path / ".tlo" / "agents"
        if agent_dir.exists():
            for agent in agents:
                agent_file = agent_dir / f"{agent}.yaml"
                if agent_file.exists():
                    checks.append({
                        "name": f"Agent: {agent}",
                        "status": "ok",
                        "detail": "已定义",
                    })
                else:
                    checks.append({
                        "name": f"Agent: {agent}",
                        "status": "warn",
                        "detail": "未找到定义文件",
                    })
    else:
        checks.append({
            "name": "Agents 列表",
            "status": "error",
            "detail": "为空",
        })

    # 3. Steps 检查
    steps = workflow_data.get("steps", [])
    if steps:
        step_ids = set()
        for step in steps:
            step_id = step.get("id")
            if not step_id:
                checks.append({
                    "name": "Step ID",
                    "status": "error",
                    "detail": "缺失 ID",
                })
                continue

            # 检查 ID 唯一性
            if step_id in step_ids:
                checks.append({
                    "name": f"Step: {step_id}",
                    "status": "error",
                    "detail": "ID 重复",
                })
            else:
                step_ids.add(step_id)

            # 检查 Agent 引用
            agent = step.get("agent")
            if agent:
                if agent in agents:
                    checks.append({
                        "name": f"Step: {step_id}",
                        "status": "ok",
                        "detail": f"Agent: {agent}",
                    })
                else:
                    checks.append({
                        "name": f"Step: {step_id}",
                        "status": "error",
                        "detail": f"Agent {agent} 未在 agents 列表中",
                    })
            else:
                checks.append({
                    "name": f"Step: {step_id}",
                    "status": "error",
                    "detail": "缺失 agent 字段",
                })

        checks.append({
            "name": "Steps 总数",
            "status": "ok",
            "detail": f"{len(steps)} 个",
        })
    else:
        checks.append({
            "name": "Steps 列表",
            "status": "error",
            "detail": "为空",
        })

    # 4. Transitions 检查
    transitions = workflow_data.get("transitions", [])
    if transitions:
        step_ids = {s.get("id") for s in steps}
        for trans in transitions:
            from_step = trans.get("from")
            to_step = trans.get("to")

            if from_step not in step_ids:
                checks.append({
                    "name": f"Transition: {from_step} → {to_step}",
                    "status": "error",
                    "detail": f"from 步骤 {from_step} 不存在",
                })
            elif to_step not in step_ids:
                checks.append({
                    "name": f"Transition: {from_step} → {to_step}",
                    "status": "error",
                    "detail": f"to 步骤 {to_step} 不存在",
                })
            else:
                checks.append({
                    "name": f"Transition: {from_step} → {to_step}",
                    "status": "ok",
                    "detail": "有效",
                })

        checks.append({
            "name": "Transitions 总数",
            "status": "ok",
            "detail": f"{len(transitions)} 个",
        })
    else:
        checks.append({
            "name": "Transitions",
            "status": "warn",
            "detail": "无（单步流程）",
        })

    # 5. Schema 检查
    if "input_schema" in workflow_data:
        checks.append({
            "name": "Input Schema",
            "status": "ok",
            "detail": "已定义",
        })

    if "output_schema" in workflow_data:
        checks.append({
            "name": "Output Schema",
            "status": "ok",
            "detail": "已定义",
        })

    return checks


def _print_validation_result(workflow_id: str, checks: list[dict]):
    """打印验证结果。"""
    console.print(f"\n[bold]Workflow 验证: {workflow_id}[/bold]\n")

    table = Table(show_header=True)
    table.add_column("检查项")
    table.add_column("状态", width=10)
    table.add_column("详情")

    for check in checks:
        status = check["status"]
        if status == "ok":
            status_str = "[green]✓ OK[/green]"
        elif status == "warn":
            status_str = "[yellow]⚠ WARN[/yellow]"
        else:
            status_str = "[red]✗ ERROR[/red]"

        table.add_row(
            check["name"],
            status_str,
            check["detail"],
        )

    console.print(table)

    # 总结
    total = len(checks)
    ok_count = sum(1 for c in checks if c["status"] == "ok")
    warn_count = sum(1 for c in checks if c["status"] == "warn")
    error_count = sum(1 for c in checks if c["status"] == "error")

    console.print(f"\n[bold]总结:[/bold]")
    console.print(f"  总计: {total} 项")
    console.print(f"  [green]通过: {ok_count}[/green]")
    if warn_count > 0:
        console.print(f"  [yellow]警告: {warn_count}[/yellow]")
    if error_count > 0:
        console.print(f"  [red]错误: {error_count}[/red]")

    if error_count == 0:
        console.print(f"\n[green]✓ Workflow 配置有效[/green]")
    else:
        console.print(f"\n[red]✗ Workflow 配置无效（{error_count} 个错误）[/red]")
