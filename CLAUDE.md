# AITest Platform

> 被测: 鞍集涂源管理系统 (Vue 3 + Element Plus) | 自建测试工作台 v0.6
> ADR-001: 项目上下文跟随项目 (.tlo/) — 平台与项目解耦

## 新 AI 启动

1. **Memory 文件**（自动注入上下文，不需要你读）:
   - `self-hosted-chat-agent-status` — 测试工作台状态
   - `dev-agent-ecosystem-phase1` — 9 开发 Agent 体系
2. **共享语言**（每次会话加载，术语一致性）:
   - `governance/context/shared-language.md` — 平台术语 + 业务术语 + 歧义消除（~350 tokens）
3. **架构决策**:
   - `docs/adr/ADR_001_TLO_DIRECTORY.md` — .tlo/ 项目目录设计
4. 需要深入时再读具体文件

## 两条工作线

| 工作线 | 项目路径 | .tlo/ | 详情 |
|--------|---------|-------|------|
| **测试自动化** | `D:\Desktop\TestingProject\ZJSN_Test-master526` | `.tlo/` ✅ | 8 Agent SOP → `governance/` 治理文档 |
| **平台开发** | aitest/ | — | 测试工作台 + 9 开发 Agent + Dev SOP |

## 项目切换

```bash
aitest project set --id=<project>           # CLI 切换活跃项目
aitest project register --path=<path>       # 注册新项目
AITEST_PROJECT=<id> python -m aitest.server.main  # 启动时指定项目
```

## 启动

```bash
aitest server start          # 测试工作台 → http://localhost:8000/chat
aitest graph run --module=<m> --pages=<p1>  # 运行测试 SOP
```

## 目录速查

```
D:\Desktop\TestingProject\    ← 测试项目（与平台分离）
  ZJSN_Test-master526/    ← Web 测试自动化 (base/page/script/config)
    .tlo/                 ← 项目上下文（ADR-001）
  mp-weixin/               ← 小程序源码
  mp-weixin-automator/     ← 小程序测试项目
    .tlo/                 ← 项目上下文

aitest/server/          ← FastAPI + chat.html 工作台 + session_store
aitest/graphs/          ← 测试 SOP 图 (sop_graph.py, sop_runner.py)
aitest/graphs_dev/      ← 开发 SOP 图 (9 Agent, 10 Phase)
aitest/agent_runner.py  ← AgentLoop 执行引擎 (测试+开发共用)
governance/agents/      ← Agent 定义 YAML (测试+开发)
governance/skills/      ← 测试 Skill 提示 (24 个)
governance/skills-dev/  ← 开发 Skill 提示 (32 个)
```

| 工作线 | 入口 | 详情 |
|--------|------|------|
| **测试自动化** | ZJSN_Test-master526/ | 8 Agent SOP → `governance/` 治理文档 |
| **平台开发** | aitest/ | 测试工作台 + 9 开发 Agent + Dev SOP |

## 启动

```bash
aitest server start          # 测试工作台 → http://localhost:8000/chat
aitest graph run --module=<m> --pages=<p1>  # 运行测试 SOP
```

## v1.0 架构 (2026-06-23)

平台升级为 **测试自动化 Agent Native 平台**。详见 `docs/architecture/00-ARCHITECTURE_OVERVIEW.md`。

核心新增模块:

```
aitest/llm/
├── reliable_provider.py     ← Retry(3x)+Fallback(claude→deepseek→openai)
└── context_window.py        ← 85%/90%阈值+DeepSeek摘要+continuation
aitest/infra/
├── security.py              ← Denylist+Per-command validator+PromptInjectionGuard
└── secure_subprocess.py     ← subprocess安全wrapper
aitest/platform/
├── capability_router/       ← 8 caps×8 agents+native tool calling
├── complexity/              ← 18因子评分+3档SOP路由(SIMPLE/STANDARD/COMPLEX)
├── testing_memory.py        ← 8种Memory类型+MemoryLifecycle+SignalObserver
├── testing_memory_store.py  ← 类型化ChromaDB CRUD
└── observation_bus.py       ← 事件总线+Memory自动同步
aitest/graphs/
└── parallel_sop.py          ← LangGraph Send()多页面并行(3.2x)
aitest/web/src/
├── api/client.ts            ← 统一HTTP/SSE/WS客户端
├── api/endpoints.ts         ← 端点常量
├── router/index.ts          ← 独立路由+懒加载
├── composables/useChatSSE.ts← SSE流处理
└── e2e/smoke.spec.ts        ← Playwright冒烟测试
```

## 目录速查

```
ZJSN_Test-master526/   ← 测试自动化 (base/page/script/config)
aitest/server/          ← FastAPI + chat.html 工作台 + session_store
aitest/graphs/          ← 测试 SOP 图 (sop_graph.py, sop_runner.py, parallel_sop.py)
aitest/graphs_dev/      ← 开发 SOP 图 (9 Agent, 10 Phase)
aitest/agent_runner.py  ← AgentLoop 执行引擎 (v1.0: reliable+continuation+tool_calling+observation)
aitest/llm/             ← LLM Provider 层 (provider + reliable_provider + context_window)
aitest/infra/           ← 基础设施 (security + secure_subprocess)
aitest/platform/        ← 平台层 (capability_router + complexity + testing_memory + observation_bus)
governance/agents/      ← Agent 定义 YAML (测试+开发)
governance/skills/      ← 测试 Skill 提示 (24 个)
governance/skills-dev/  ← 开发 Skill 提示 (32 个)
docs/architecture/      ← v1.0 设计文档 (8个)
```

## 口语化入口

| 指令 | 效果 |
|------|------|
| `/caveman` 或 "洞穴人模式" | 超压缩通信，省 ~75% token（lite/full/ultra 三级） |
| `/continue` | 恢复上次中断的工作 |
| `aitest graph run --module=<m>` | 运行测试 SOP |

## 常用命令

```bash
# 测试
cd ZJSN_Test-master526 && pytest script/<m>/test_*.py -v --alluredir=../allure-results/json

# 平台
aitest server start
python -c "from aitest.agent_runner import AgentLoop; AgentLoop('arch-agent', module='x').run()"

# 门禁
python ZJSN_Test-master526/tools/check_sop_gate.py --module <m> --agent <a> --json
```

## Browser-Use 集成（🆕 AI 辅助层）

- **定位**: Selenium 互补层，不替代 CI/CD 回归
- **驱动**: `ZJSN_Test-master526/base/bu_driver.py`（多 provider: MiMo / Claude / Gemini）
- **适配器**: `aitest/bu_adapter.py`（Skill → BrowserUseDriver 桥接）
- **Skill**: `page-observe`（页面探索）, `page-object-generator`（mode: browser-use）
- **Fixture**: `bu_heal`（自愈，@pytest.mark.bu_heal 启用，仅 ENV=dev）
- **LLM Provider**: `.env` 中 `BU_LLM_PROVIDER=mimo`（默认）, 可选 claude/gemini
- **文档**: `tech-research/` 下有调研、计划、评审、验证全套

## 环境

- 测试地址: `https://aiwechatminidemo.cimc-digital.com/`
- API Key: 项目根目录 `.env` (ANTHROPIC_API_KEY, GOOGLE_API_KEY, MIMO_API_KEY)
- 详细文档: `governance/README.md` → `governance/context/source-of-truth.md`
