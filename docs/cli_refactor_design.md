# CLI 子命令重构设计

> **任务**: P2-1: CLI 子命令重构  
> **目标**: 将 CLI 命令与产品概念（5-resource 模型）对齐  
> **日期**: 2026-07-11

---

## 问题分析

### 当前问题

1. **命令不直观**: `aitest graph run` 不符合资源化思维
2. **概念不统一**: `graph` 是实现细节，不是产品概念
3. **缺少资源命令**: Agent/Workflow/Dataset/Evaluation 等资源无 CLI 入口
4. **别名混乱**: `run/validate/status` 等别名参数不一致

### 5-Resource 模型

根据架构，平台核心资源为：

1. **Run**: 执行记录（Agent/Workflow/Skill/Evaluation）
2. **Agent**: 智能体定义
3. **Workflow**: 工作流图
4. **Quality**: Dataset/Evaluation/Experiment
5. **Assets**: Artifacts/Knowledge

---

## 设计方案

### 核心原则

1. **资源优先**: 一级命令是资源名（run/agent/workflow/quality）
2. **CRUD 动词**: 二级命令是操作（create/list/show/delete）
3. **向后兼容**: 旧命令保留 6 个月，标记为 `hidden=True`
4. **输出统一**: 所有命令支持 `--output json|yaml|table`

---

## 新命令结构

### 1. `aitest run` — 执行资源

```bash
# 创建新 Run
aitest run create --target agent:page-observer --module equipment --pages alarm-config,camera
aitest run create --target workflow:test-automation-sop --module equipment
aitest run create --target skill:page-observe --input input.json
aitest run create --target evaluation:eval_001

# 查询 Run
aitest run list [--status completed|running|failed] [--limit 20] [--output json]
aitest run show <run_id> [--output json]
aitest run logs <run_id> [--follow] [--tail 100]

# 操作 Run
aitest run stop <run_id>
aitest run retry <run_id>
aitest run compare <run_id_1> <run_id_2> <run_id_3>

# 导出 Artifacts
aitest run artifacts <run_id> [--download] [--output-dir ./artifacts]
```

**映射关系**:
- `aitest graph run --module m` → `aitest run create --target agent:page-observer --module m`
- `aitest graph status` → `aitest run list`
- `aitest graph resume` → `aitest run retry <run_id>`

---

### 2. `aitest agent` — Agent 资源

```bash
# 查询 Agent
aitest agent list [--output json]
aitest agent show <agent_id> [--version 2.5.0]

# Agent 版本管理
aitest agent versions <agent_id>
aitest agent diff <agent_id> --from 2.5.0 --to 2.6.0

# 测试 Agent
aitest agent test <agent_id> --input input.json [--mock-llm]

# 导出 Agent
aitest agent export <agent_id> --output agent.yaml
```

---

### 3. `aitest workflow` — Workflow 资源

```bash
# 创建/导入 Workflow
aitest workflow create --file workflow.json
aitest workflow import --file workflow.json

# 查询 Workflow
aitest workflow list [--output json]
aitest workflow show <workflow_id> [--version 1.0.0]

# 编辑 Workflow
aitest workflow edit <workflow_id>  # 打开 JSON 编辑器
aitest workflow validate <workflow_id>

# 版本管理
aitest workflow publish <workflow_id> --version 1.1.0
aitest workflow versions <workflow_id>

# 执行 Workflow
aitest workflow run <workflow_id> [--module m] [--env staging]
# 等价于: aitest run create --target workflow:<workflow_id>
```

---

### 4. `aitest quality` — 质量资源

```bash
# Dataset 管理
aitest quality dataset create --name "regression-suite" --type test_cases
aitest quality dataset list
aitest quality dataset show <dataset_id>
aitest quality dataset add-examples <dataset_id> --from-runs <run_ids>

# Evaluation 管理
aitest quality eval run --dataset <dataset_id> --agent <agent_id> [--version 2.5.0]
aitest quality eval list [--dataset <dataset_id>]
aitest quality eval show <eval_id>

# Experiment (A/B 对比)
aitest quality experiment create --baseline <eval_id_1> --candidate <eval_id_2>
aitest quality experiment show <exp_id>
aitest quality experiment promote <exp_id>  # 提升候选版本
```

---

### 5. `aitest asset` — 资产资源

```bash
# Artifacts
aitest asset artifact list [--run-id <run_id>]
aitest asset artifact download <artifact_id> [--output-dir ./artifacts]

# Knowledge
aitest asset knowledge list
aitest asset knowledge show <knowledge_id>
aitest asset knowledge sync  # 同步到向量库
```

---

### 6. `aitest project` — 项目管理（保留）

```bash
aitest project init [--path <path>]
aitest project list [--workspace <workspace>]
aitest project show [--id <project_id>]
aitest project set --id <project_id>
aitest project register --path <path>
aitest project validate [--id <project_id>]
```

**无变化**，现有命令已符合资源化思维。

---

### 7. `aitest provider` — Provider 资源

```bash
# ModelProvider
aitest provider list [--type anthropic|openai|ollama]
aitest provider show <provider_id>
aitest provider create --name "claude-prod" --type anthropic --api-key-ref secret:anthropic-key
aitest provider test <provider_id>
aitest provider update <provider_id> --status inactive
aitest provider delete <provider_id>
```

---

### 8. `aitest mcp` — MCP Server 资源

```bash
# MCP Server 管理
aitest mcp list [--status running|stopped]
aitest mcp show <mcp_server_id>
aitest mcp start <mcp_server_id>
aitest mcp stop <mcp_server_id>
aitest mcp restart <mcp_server_id>
aitest mcp logs <mcp_server_id> [--follow]

# 健康检查
aitest mcp health <mcp_server_id>
aitest mcp health-all
```

---

### 9. `aitest plugin` — Plugin 资源

```bash
aitest plugin list [--output json]
aitest plugin show <plugin_name>
aitest plugin install <url_or_path>
aitest plugin uninstall <plugin_name>
aitest plugin enable <plugin_name>
aitest plugin disable <plugin_name>
```

---

### 10. `aitest env` — Environment 资源

```bash
aitest env list
aitest env show <env_id>
aitest env create --name staging --base-url https://staging.example.com
aitest env update <env_id> --variable DB_HOST=staging-db.example.com
aitest env delete <env_id>
aitest env set-default <env_id>
```

---

### 11. `aitest secret` — Secret 资源

```bash
aitest secret list [--type api_key|password|token]
aitest secret show <secret_id>  # 不显示明文值
aitest secret create --name "slack-token" --type token --value "xoxb-..."
aitest secret update <secret_id> --value "new-value"
aitest secret delete <secret_id>
aitest secret audit <secret_id>  # 审计日志
```

---

### 12. `aitest server` — 服务管理（保留 + 改名）

```bash
# 新命令
aitest server start [--host 0.0.0.0] [--port 8000] [--daemon]
aitest server stop
aitest server status
aitest server worker [--worker-id w1] [--poll-interval 1.0]

# 别名（向后兼容）
aitest chat start  # 等价于 aitest server start
```

---

### 13. 顶级命令（保留）

```bash
aitest config <action> [key] [value]
aitest ecosystem [--output json]
aitest doctor [--fix]
aitest version
aitest tui
```

---

## 向后兼容策略

### 旧命令保留（6 个月）

```python
# 旧命令标记为 hidden=True
@app.command("graph", hidden=True, deprecated=True)
def graph_deprecated():
    """已废弃，请使用 'aitest run' 命令。"""
    typer.echo("⚠️  'aitest graph' 已废弃，请使用:")
    typer.echo("  aitest run create --target agent:page-observer --module <m>")
    typer.echo("  aitest run list")
    raise typer.Exit(1)
```

### 别名映射

```python
# 向后兼容别名
@app.command("run", hidden=True)
def run_alias_old(module: str, pages: Optional[str] = None, ...):
    """向后兼容: aitest run <module> → aitest run create"""
    typer.echo("⚠️  旧语法已废弃，自动转换为:")
    typer.echo(f"  aitest run create --target agent:page-observer --module {module}")
    # 调用新命令
    run_create(target=f"agent:page-observer", module=module, pages=pages, ...)
```

---

## 实现计划

### Phase 1: 核心重构（本次实现）

1. 创建新命令组: `run/agent/workflow/quality/asset/provider/mcp/plugin/env/secret`
2. 实现 `aitest run create/list/show/logs/stop/retry/compare`
3. 实现 `aitest agent list/show/versions`
4. 保留旧命令，标记 `hidden=True` + deprecation warning

### Phase 2: 扩展命令（P2-4）

1. 实现 `workflow/quality/asset` 命令组
2. 实现 `provider/mcp/plugin/env/secret` 管理命令

### Phase 3: 清理（6 个月后）

1. 移除旧命令和别名
2. 更新文档

---

## 配置优先级（P2-2）

统一配置加载顺序：

```
CLI 参数 > 环境变量 > 配置文件 > 默认值
```

### 实现

```python
def resolve_config(cli_value, env_var, config_key, default):
    """统一配置解析逻辑。"""
    if cli_value is not None:
        return cli_value
    if os.getenv(env_var):
        return os.getenv(env_var)
    if config_file.get(config_key):
        return config_file.get(config_key)
    return default
```

---

## 帮助文本规范（P2-3）

### 命令帮助模板

```python
@app.command("create")
def run_create(
    target: str = typer.Option(
        ..., 
        "--target", 
        help="执行目标，格式: <type>:<id>，例如: agent:page-observer, workflow:test-sop"
    ),
    module: Optional[str] = typer.Option(
        None, 
        "--module", "-m", 
        help="模块名（Agent 类型必需）"
    ),
):
    """
    创建新的 Run。
    
    示例:
      aitest run create --target agent:page-observer --module equipment
      aitest run create --target workflow:test-automation-sop
      aitest run create --target evaluation:eval_001
    
    目标类型:
      - agent:<agent_id>: 执行单个 Agent
      - workflow:<workflow_id>: 执行工作流
      - skill:<skill_id>: 执行单个 Skill
      - evaluation:<eval_id>: 运行评估
    """
    ...
```

---

## 输出格式统一（P3-1）

所有命令支持 `--output` 参数：

```python
def format_output(data, output_format: str = "table"):
    """统一输出格式化。"""
    if output_format == "json":
        print(json.dumps(data, indent=2))
    elif output_format == "yaml":
        print(yaml.dump(data))
    else:  # table
        table = Table()
        # ... 使用 rich.Table
        console.print(table)
```

---

## 文件清单

### 新增文件

```
aitest/cli/commands/
  run/
    create.py         # aitest run create
    list.py           # aitest run list
    show.py           # aitest run show
    logs.py           # aitest run logs
    stop.py           # aitest run stop
    retry.py          # aitest run retry
    compare.py        # aitest run compare
  agent/
    list.py           # aitest agent list
    show.py           # aitest agent show
    versions.py       # aitest agent versions
  workflow/
    create.py         # aitest workflow create
    list.py           # aitest workflow list
    show.py           # aitest workflow show
    validate.py       # aitest workflow validate
    run.py            # aitest workflow run
```

### 修改文件

```
aitest/cli/main.py              # 新命令组注册
aitest/cli/utils/config.py      # 配置优先级统一（新增）
aitest/cli/utils/output.py      # 输出格式化（新增）
```

---

## 测试计划

### 单元测试

```python
def test_run_create_agent():
    """测试: aitest run create --target agent:xxx"""
    result = runner.invoke(app, [
        "run", "create",
        "--target", "agent:page-observer",
        "--module", "equipment"
    ])
    assert result.exit_code == 0
    assert "Run created:" in result.stdout

def test_backward_compatibility():
    """测试: 旧命令自动转换"""
    result = runner.invoke(app, ["run", "equipment"])
    assert "⚠️  旧语法已废弃" in result.stdout
    assert result.exit_code == 0
```

### 集成测试

```bash
# 端到端测试
aitest run create --target agent:page-observer --module equipment --output json | jq '.run_id'
aitest run list --status completed --output json | jq '.runs[0].run_id'
```

---

## 迁移指南（用户文档）

### 命令映射表

| 旧命令 | 新命令 | 说明 |
|--------|--------|------|
| `aitest graph run --module m` | `aitest run create --target agent:page-observer --module m` | 执行 Agent |
| `aitest graph status` | `aitest run list` | 查看 Run 列表 |
| `aitest graph resume --module m` | `aitest run retry <run_id>` | 重试失败的 Run |
| `aitest run m` | `aitest run create --target agent:page-observer --module m` | 别名自动转换 |
| `aitest status` | `aitest run list` | 别名自动转换 |
| `aitest server start` | `aitest server start` 或 `aitest chat start` | 无变化（可选别名） |

### 自动迁移

CLI 提供自动提示：

```bash
$ aitest graph run --module equipment
⚠️  'aitest graph' 已废弃（将在 2026-12-31 移除），请使用:
  aitest run create --target agent:page-observer --module equipment

是否继续? [Y/n]
```

---

## 风险与缓解

### 风险 1: 用户习惯旧命令

**缓解**: 
- 保留旧命令 6 个月
- 每次执行显示 deprecation warning
- 文档提供迁移指南

### 风险 2: 脚本依赖旧命令

**缓解**:
- CI/CD 脚本检测工具（`aitest doctor --check-deprecated`）
- 提供 `--no-warn` 参数抑制警告

### 风险 3: 新命令学习成本

**缓解**:
- 提供交互式 TUI（`aitest tui`）
- 详细帮助文本 + 示例
- 自动补全脚本（bash/zsh）

---

## 成功指标

1. ✅ 所有资源有对应 CLI 命令
2. ✅ 命令符合 CRUD 动词规范
3. ✅ 向后兼容测试通过
4. ✅ 输出格式统一（支持 json/yaml/table）
5. ✅ 帮助文本完整（包含示例）

---

## 参考

- **路线图**: `docs/MASTER_ROADMAP.md` — P2-1/P2-2/P2-3
- **API 设计**: `docs/api/POST_api_v1_runs.md` — Run 资源 API
- **产品定位**: `PRODUCT.md` — 5-resource 模型
