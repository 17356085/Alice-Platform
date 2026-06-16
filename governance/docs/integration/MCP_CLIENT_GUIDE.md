# MCP 跨客户端配置指南

> 版本：v1.1 | 日期：2026-06-14
> 前提：aitest MCP Server 已就绪（`aitest/mcp/` 包 + `aitest/knowledge_server.py`）

---

## 你拥有的 MCP 能力

| MCP Server | 协议 | 提供 | 关键能力 |
|------------|------|------|---------|
| `aitest-tools` | Tools + Prompts | 13 Tools + 6 Prompts | 代码质量检查、已知问题搜索（关键词+RAG）、模块状态、自动化覆盖率、Agent 编排（test-design / automation / full-sop）、一致性校验、质量门禁 |
| `aitest-knowledge` | Resources | 参数化资源 | PROJECT_CONTEXT 按章节加载、known-issues 检索、模块/页面 Context 按需获取 |

---

## 客户端配置

### 1. Claude Code（你现在用的）

已配置，见项目根目录 `.claude/mcp.json`。无需额外操作。

---

### 2. Claude Desktop

文件路径（任选其一）：
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "aitest-tools": {
      "command": "python",
      "args": ["-m", "aitest.mcp_server"],
      "env": {
        "PYTHONPATH": "D:\\Desktop\\WorkStudy"
      },
      "description": "AI 测试平台 — 代码检查、已知问题搜索、模块状态、Agent 编排"
    },
    "aitest-knowledge": {
      "command": "python",
      "args": ["-m", "aitest.knowledge_server"],
      "env": {
        "PYTHONPATH": "D:\\Desktop\\WorkStudy"
      },
      "description": "AI 测试平台 — 知识库按需检索（PROJECT_CONTEXT、已知问题、页面上下文）"
    }
  }
}
```

> ⚠️ `PYTHONPATH` 必须指向 `WorkStudy` 目录，否则 Python 找不到 `aitest` 模块。

---

### 3. Continue.dev（VS Code / JetBrains）

文件：项目根目录 `.continuerc.json` 或全局 `~/.continue/config.json`

```json
{
  "experimental": {
    "mcpServers": [
      {
        "name": "aitest-tools",
        "command": "python",
        "args": ["-m", "aitest.mcp_server"],
        "env": {
          "PYTHONPATH": "/absolute/path/to/WorkStudy"
        }
      },
      {
        "name": "aitest-knowledge",
        "command": "python",
        "args": ["-m", "aitest.knowledge_server"],
        "env": {
          "PYTHONPATH": "/absolute/path/to/WorkStudy"
        }
      }
    ]
  }
}
```

使用方式：在 Continue.dev 聊天框中，直接引用 MCP Tool：
```
/aitest-tools:run_full_sop module="equipment" mode="status"
/aitest-tools:rag_search_known_issues query="NoSuchElementException el-dialog"
```

---

### 4. Cline（VS Code）

文件：VS Code 设置 → `cline.mcpServers`

```json
{
  "cline.mcpServers": {
    "aitest-tools": {
      "command": "python",
      "args": ["-m", "aitest.mcp_server"],
      "env": {
        "PYTHONPATH": "D:\\Desktop\\WorkStudy"
      }
    },
    "aitest-knowledge": {
      "command": "python",
      "args": ["-m", "aitest.knowledge_server"],
      "env": {
        "PYTHONPATH": "D:\\Desktop\\WorkStudy"
      }
    }
  }
}
```

使用方式：在 Cline 中直接提及工具名或描述，Cline 会自动调用 MCP Tool：
> "帮我看看 equipment 模块目前 SOP 进度到哪了" → Cline 自动调用 `get_module_status`

---

### 5. Cursor

Cursor 的 MCP 支持通过 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "aitest-tools": {
      "command": "python",
      "args": ["-m", "aitest.mcp_server"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/WorkStudy"
      }
    }
  }
}
```

---

## 前置条件检查清单

在任何客户端中配置 MCP 前，确认以下条件：

- [ ] Python 版本 ≥ 3.10（`python --version`）
- [ ] 依赖已安装：`pip install mcp chromadb pyyaml`（其余依赖按需）
- [ ] `PYTHONPATH` 或工作目录正确指向 `WorkStudy`
- [ ] `.env` 中的 API Key 已配置（如需使用需要 LLM 的工具）
- [ ] 启动测试：`python -c "from aitest.mcp_server import server; print(server.name)"` 无报错

### 诊断命令

```bash
# 测试 MCP Server 能否启动
python -m aitest.mcp_server &
# 观察输出：应显示 "Started server..." （stdio 模式，不会打印到终端）
# Ctrl+C 停止

# 测试 Python 路径
python -c "import sys; print('\n'.join(sys.path))"
# 确保 WorkStudy 目录在列表中，或 PYTHONPATH 包含它
```

---

## 常见问题

### Q: `ModuleNotFoundError: No module named 'aitest'`

A: 设置 `PYTHONPATH` 环境变量指向 `WorkStudy` 目录，或在 `args` 中先 `cd` 到项目目录：

```json
{
  "command": "python",
  "args": ["-m", "aitest.mcp_server"],
  "env": {
    "PYTHONPATH": "D:\\Desktop\\WorkStudy"
  }
}
```

### Q: Windows 下路径用 `\` 还是 `/`？

A: JSON 中用 `\\`（转义反斜杠）或 `/`（都支持）：
- `"PYTHONPATH": "D:\\Desktop\\WorkStudy"` ✅
- `"PYTHONPATH": "D:/Desktop/WorkStudy"` ✅

### Q: MCP Tool 调用后返回"请在 AI 客户端中执行"是什么意思？

A: `run_test_design_agent` / `run_automation_agent` / `run_full_sop` 这三个 Tool 返回的是**触发指令**而非执行结果。因为 Agent 执行需要 LLM 推理能力（读取 Skill Prompt → 分析页面 → 生成代码），MCP Tool 负责参数校验和前置检查，实际执行由 AI 客户端完成。Tool 返回中包含了可直接执行的斜杠命令。

### Q: Ollama 怎么配？

A: 确保 `OLLAMA_BASE_URL` 指向正确的地址（Windows 默认 `http://localhost:11434`），且在 `.env` 中已配置。CLI 中使用 `--provider ollama`。

---

## 能力速查（给 AI 客户端的提示）

当你接入 `aitest-tools` MCP Server 后，你可以：

| 你想做什么 | 调用哪个 Tool | 参数 |
|-----------|-------------|------|
| 检查代码有没有违规 | `check_code_quality` | `target="page/equipment_page/..."` |
| 搜索已知 Element Plus 坑位 | `search_known_issues` | `query="el-cascader"` |
| RAG 语义匹配已知问题 | `rag_search_known_issues` | `query="NoSuchElementException loading"` |
| 查看某个模块的 SOP 进度 | `get_module_status` | `module_name="equipment"` |
| 查看自动化覆盖率 | `get_automation_coverage` | `module_name="equipment"` |
| 启动测试设计（需客户端 LLM） | `run_test_design_agent` | `module="equipment" page="alarm-config"` |
| 启动自动化代码生成（需客户端 LLM） | `run_automation_agent` | `module="equipment" page="alarm-config"` |
| 一键启动全流程 SOP | `run_full_sop` | `module="tank" mode="full"` |
