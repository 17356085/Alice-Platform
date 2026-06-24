# Alice — AI-Native Test Automation Platform

> AI 驱动测试自动化平台。被测对象: **鞍集涂源管理系统** (Vue 3 + Element Plus)。
> AI 入口: [`CLAUDE.md`](CLAUDE.md)

## 两条工作线

| 工作线 | 路径 | 说明 |
|--------|------|------|
| **平台开发** | `aitest/` | FastAPI + Vue 3 测试工作台，Agent 执行引擎 |
| **测试自动化** | `ZJSN_Test-master526/` | 8 Agent SOP Web/小程序 E2E 测试 |

## 快速开始

```bash
# 启动测试工作台
aitest server start                # → http://localhost:8000/chat

# 运行测试 SOP
aitest graph run --module=<m> --pages=<p>

# 项目管理
aitest project register --path=<path>
aitest project set --id=<project>
```

## 架构 (v1.0)

```
aitest/
├── server/              FastAPI + chat.html 工作台 + session 持久化
├── agent_runner.py      AgentLoop 执行引擎 (reliable + continuation + tool_calling)
├── graphs/              测试 SOP 图 (串行 sop_graph + 并行 parallel_sop)
├── graphs_dev/          9 Agent 10 Phase 开发 SOP
├── llm/                 LLM Provider (Claude → DeepSeek → OpenAI fallback)
├── infra/               基础设施 (security + secure_subprocess)
├── platform/            平台层 (capability_router + complexity + testing_memory)
└── web/                 Vue 3 前端 (Element Plus + SSE/WS)

governance/
├── agents/              Agent 定义 YAML (测试 8 + 开发 9)
├── skills/              测试 Skill 提示 (24)
├── skills-dev/          开发 Skill 提示 (32)
├── workflows/           标准化流程 (9)
└── context/             共享语言 + 来源真值 + 项目上下文

ZJSN_Test-master526/     测试项目 (Python + Selenium + pytest + Allure)
mp-weixin-automator/      小程序自动化 (Node.js)
project-study/            架构逆向分析
docs/                     ADR + v1.0 架构设计 (8 篇)
```text

## 技术栈

| 维度 | 内容 |
|------|------|
| 后端 | Python 3.11+ / FastAPI / LangGraph |
| 前端 | Vue 3 + Element Plus + Vite |
| LLM | Claude / DeepSeek / OpenAI (Retry + Fallback) |
| 向量存储 | ChromaDB |
| Web 自动化 | Selenium + pytest + Allure |
| 小程序自动化 | Node.js + mp-weixin-automator |

## 本地开发

```bash
pip install -e .
aitest server start                # → http://localhost:8000
aitest graph run --module=<m>      # 运行测试 SOP
```

## 项目上下文

ADB-001: 项目上下文跟随项目 (`.tlo/`) — 平台与项目解耦。

## 许可证

内部项目。
