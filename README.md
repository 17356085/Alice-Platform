# AITest — AI-Native Test Automation Platform

> **测试自动化 Agent Native 平台** — 以 Browser/Page/SOP/Evidence/Knowledge 为第一公民，
> Agent 通过 Capability Router 自主调用测试能力。
>
> 平台与项目解耦（ADR-001: `.tlo/`），支持多项目注册与切换。

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](pyproject.toml)
[![Version](https://img.shields.io/badge/version-1.6.0-green)](pyproject.toml)
[![License](https://img.shields.io/badge/license-AGPL--3.0-orange)](LICENSE)

## 是什么

AITest 不是代码生成器。它是 **Agent Native** 平台：Agent 自主完成从模块分析、策略设计、页面探索、代码生成、执行验证到报告产出的完整测试生命周期。

与通用 AI 编码助手的区别：

| | 通用 AI 编码助手 | AITest |
| --- | --- | --- |
| 核心流程 | Task → Plan → Code → Review → Git | Module → Strategy → Design → Execute → Validate → Report |
| 第一公民 | Code, Diff, PR | Browser, Page, SOP, Evidence, Knowledge |
| Agent 产出 | 代码 + Commit | 测试脚本 + 执行报告 + Evidence |
| 并行单元 | 子任务 | 页面 (Send API, ~Nx 加速) |
| 记忆类型 | 代码模式 + Gotcha | UI Pattern + Locator History + Business Rule + Known Bug |

## 核心能力

```
aitest/
├── server/                    FastAPI 服务 (12+ 端点: agents, chat, sessions, workflows, execution)
├── agent_runner.py            AgentLoop 执行引擎 — LLM ↔ Tool 循环编排
├── graphs/                    测试 SOP 图 (LangGraph: 串行 + parallel_sop Send API)
├── graphs_dev/                9 Agent 10 Phase 开发 SOP
├── llm/
│   ├── reliable_provider.py   Retry(3x) + Fallback (Claude → DeepSeek → OpenAI)
│   └── context_window.py      85%/90% 阈值 + DeepSeek 摘要 + continuation
├── platform/
│   ├── capability_router/     Agent 按名称调用能力，不关心底层实现
│   ├── complexity/            18 因子评分 → SIMPLE/STANDARD/COMPLEX 路由
│   ├── testing_memory.py      8 种测试记忆类型 (ChromaDB 持久化)
│   └── observation_bus.py     事件总线 + Memory 自动同步
├── infra/
│   ├── security.py            三层安全: Denylist + Validator + PromptInjectionGuard
│   └── secure_subprocess.py   subprocess 安全 wrapper
└── web/                       TLO — 测试生命周期编排器 (Vue 3 + Electron)
```

## 快速开始

```bash
# 安装
pip install -e .

# 启动工作台
aitest server start                    # → http://localhost:8000/chat

# 注册测试项目
aitest project register --path=<项目路径>
aitest project set --id=<项目ID>

# 运行测试 SOP
aitest graph run --module=<模块> --pages=<页面>
```

## 架构

v1.0 设计文档 → [`docs/architecture/`](docs/architecture/)

| 文档 | 内容 |
|---|---|
| [00-OVERVIEW](docs/architecture/00-ARCHITECTURE_OVERVIEW.md) | 定位、目标架构、模块映射 |
| [01-CAPABILITY_ROUTER](docs/architecture/01-CAPABILITY_ROUTER.md) | 统一能力注册与路由 |
| [02-PROVIDER_RELIABILITY](docs/architecture/02-PROVIDER_RELIABILITY.md) | LLM 多 Provider 可靠性链 |
| [03-CONTEXT_WINDOW](docs/architecture/03-CONTEXT_WINDOW.md) | 上下文窗口监控与 continuation |
| [04-TESTING_MEMORY](docs/architecture/04-TESTING_MEMORY.md) | 8 种测试记忆类型设计 |
| [05-COMPLEXITY_ROUTING](docs/architecture/05-COMPLEXITY_ROUTING.md) | 18 因子复杂度评分 |
| [06-SECURITY_LAYER](docs/architecture/06-SECURITY_LAYER.md) | 三层安全模型 |
| [CONSTITUTION](docs/architecture/CONSTITUTION.md) | 项目宪章 |

## 治理层

```
governance/
├── agents/              Agent 定义 YAML (测试 8 + 开发 9)
├── skills/              测试 Skill 提示 (24)
├── skills-dev/          开发 Skill 提示 (32)
├── workflows/           标准化流程 (9)
├── context/             共享语言 + 来源真值 + 项目上下文
├── templates/           输出格式模板
└── knowledge/           踩坑经验库 (pitfalls)
```

## 目录

```
Alice/
├── aitest/              平台核心 (FastAPI + AgentLoop + LLM + Platform)
├── governance/          治理层 (Agent/Skill/Workflow/Template/KPI)
├── docs/                架构设计 + ADR
├── project-study/       架构逆向分析
└── ZJSN_Test-master526/ 测试项目示例 (Python + Selenium + pytest)
```

## AI 入口

新 AI 会话 → 读 [`CLAUDE.md`](CLAUDE.md)。包含口语化入口、工作线、编码红线、目录速查。

## 技术栈

Python 3.10+ / FastAPI / LangGraph / ChromaDB / Vue 3 + Vite + Electron
