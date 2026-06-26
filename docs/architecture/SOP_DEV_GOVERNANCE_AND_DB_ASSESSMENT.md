# sop_dev 治理体系 + 数据库评估

> 日期: 2026-06-25 | 基于 6 个 sprint task 完成后的资产盘点

---

# Part 1: sop_dev/ — AI 自举开发工作流治理

## 现有资产盘点

### 已存在 (成熟，可直接纳入治理)

| 资产 | 位置 | 规模 | 状态 |
|------|------|------|------|
| Dev SOP Graph | `aitest/graphs_dev/sop_graph_dev.py` | 9 Agent, 10 Phase | ✅ 生产可用 |
| Dev Phase 定义 | `aitest/graphs_dev/state_dev.py` | 10 CANONICAL_PHASES + mode skip | ✅ 完整 |
| Dev Skills | `governance/skills-dev/` | 14 目录, 50+ .md 文件 | ✅ 完整 |
| Dev Skill Registry | `governance/skills-dev/skill-registry-dev.yaml` | YAML 注册表 | ✅ 完整 |
| Agent 定义 | `governance/agents/agent-definitions.yaml` | 524 行, dev + test agents | ✅ 完整 |
| Dev Agent→Phase 映射 | `state_dev.py:72-84` | `DEV_AGENT_PHASE_MAP` | ✅ 完整 |

### 缺失 (需创建)

| 缺口 | 原因 | 建议 |
|------|------|------|
| **SOP_STATUS for dev** | 测试模块有 `artifacts/sop-status/SOP_STATUS_<module>.json`，dev 模块无 | 创建 `artifacts/sop-status-dev/` |
| **Dev Phase 治理文档** | 测试 Phase 有 `governance/context/` 下的文档；dev 无 | 创建 `governance/sop_dev/phases/` |
| **Dev Gate 检查** | 测试有 `check_sop_gate.py`；dev 无 | 克隆 `check_sop_gate.py` → `check_sop_gate_dev.py` |
| **Dev KPI 报告** | 测试有 `governance/kpi/reports/`；dev 无 | 创建 `governance/kpi/reports-dev/` |
| **Dev Module 注册** | 测试模块在 `shared-language.md` 自动生成；dev 模块无 | dev 平台本身作为 "module" 注册 |

## 建议目录结构

```
governance/
├── sop_dev/                              # 🆕 Dev SOP 治理
│   ├── README.md                         # 开发 SOP 概述
│   ├── CANONICAL_PHASES.md               # 10 Phase 定义 + 依赖
│   ├── AGENT_PHASE_MAP.md                # Agent → Phase 映射
│   ├── MODE_SKIP_MAP.md                  # 模式跳过规则
│   ├── phases/
│   │   ├── 01-plan.md                    # Phase 1 治理文档
│   │   ├── 02-requirements.md
│   │   ├── 03-architecture.md
│   │   ├── 04-component-design.md
│   │   ├── 05-frontend-impl.md
│   │   ├── 06-backend-impl.md
│   │   ├── 07-code-review.md
│   │   ├── 08-dev-test.md
│   │   ├── 09-debug-fix.md
│   │   └── 10-build.md
│   └── agents/
│       ├── pm-agent.md                   # Agent 职责 + Skill 清单
│       ├── arch-agent.md
│       ├── frontend-agent.md
│       └── ...
│
├── kpi/
│   └── reports-dev/                      # 🆕 Dev KPI 报告
│       └── <project>/                    # 按开发项目分
│           └── 开发报告-<project>.xlsx
│
artifacts/
└── sop-status-dev/                       # 🆕 Dev SOP 状态
    └── SOP_STATUS_<project>.json
```

## 执行步骤 (3 个工作日)

### Step 1: 创建治理文档 (1d)

从 `state_dev.py` 和 `sop_graph_dev.py` 中提取声明式配置，转为 Markdown 治理文档。每个 Phase 文档包含:
- Phase 定义 (输入 / 输出 / Agent / Skills)
- 门禁条件 (进入此 Phase 的前提)
- 产出物规范 (文件路径 + 验证规则)
- 跳过条件 (MODE_SKIP_MAP 中哪些模式可跳过)

### Step 2: SOP_STATUS 追踪 + Gate (1d)

- 克隆 `check_sop_gate.py` → `check_sop_gate_dev.py`，适配 Dev Phase 枚举
- 创建 `artifacts/sop-status-dev/`，生成首份 `SOP_STATUS_aitest.json`
- 注册 "aitest-platform" 作为 dev 工作流的首个 "module"

### Step 3: agent-definitions.yaml 补齐 (1d)

- 确认 9 个 dev agent 在 `agent-definitions.yaml` 中均有条目
- 补全 `capabilities` / `boundaries` / `skills` 字段
- 新增 `mcp_servers` 字段 (对齐 Task 6 registry)

---

# Part 2: 数据库评估 — SQLite 是否满足未来需求

## 当前数据库使用全景

| 数据库 | 位置 | 用途 | 引擎 | 问题 |
|--------|------|------|------|------|
| ChromaDB | `governance/.chroma/` | RAG 向量检索 (5 集合, ~235 文档) | SQLite3 嵌入式 | ✅ 无问题 — 嵌入式向量 DB，规模小 |
| LangGraph Checkpoint | `governance/.graph_state/checkpoints.sqlite` | SOP 断点续跑 + 时间旅行 | SQLite (SqliteSaver) | ✅ 无问题 — LangGraph 官方推荐 |
| Chat Sessions | `aitest/server/session_store.py` | 聊天会话持久化 (115 行) | SQLite (SQLAlchemy) | ✅ 无问题 — 会话数据轻量 |
| Audit Log | `governance/.data/audit.db` | 安全审计日志 | SQLite | ⚠️ 单文件，无内置复制 |
| Bug Tracker | `governance/.data/bugs.db` | 已知缺陷跟踪 | SQLite | ⚠️ 同上 |
| Run History | `governance/.data/runs.db` | 执行历史记录 | SQLite | ⚠️ 同上 |
| Memory Counters | `governance/.data/dead_ends/counters.json` | 死胡同计数器 | JSON 文件 | ✅ 无问题 — 运行时状态，非长期数据 |

## 评估维度

### 1. 并发写入

| 维度 | 现状 | SQLite 上限 | 风险 |
|------|------|------------|------|
| 并发写入者 | 1 (单 FastAPI worker 执行测试) | 1 writer (WAL mode 允许多 reader) | **低** — 测试执行是单任务串行 |
| 未来多 worker | 如果水平扩展 FastAPI workers | 写入需排队，性能线性下降 | **中** — 如扩展需迁移 |

**结论**: 短期不需要迁移。如果后续支持多任务并发执行（如 3 个模块同时跑 SOP），需评估 WAL 模式下的写入吞吐。

### 2. 数据量

| 数据集 | 当前大小 | 年增长预估 | 10 年总量 |
|--------|---------|-----------|----------|
| ChromaDB 向量 | ~50MB | 100MB/年 | ~1GB |
| Checkpoints | ~10MB | 50MB/年 | ~500MB |
| Audit Log | ~1MB | 10MB/年 | ~100MB |
| Runs + Bugs | ~5MB | 20MB/年 | ~200MB |

**结论**: SQLite 单文件上限 281TB。10 年总量 < 2GB，完全不构成瓶颈。

### 3. 备份与恢复

| 场景 | SQLite 方案 | 风险 |
|------|------------|------|
| 每日备份 | `sqlite3 .backup` 或文件复制 | **低** — 简单可靠 |
| 灾难恢复 | 从 Git (`checkpoints.sqlite` 在 governance/) | **低** |
| 多环境同步 | 无内置方案 | **中** — 如需 dev/staging/prod 同步需自定义 |

**结论**: 单机部署场景下 SQLite 备份最简单。多环境同步需引入外部工具（Litestream 或 pg_dump）。

### 4. 查询能力

| 需求 | SQLite 能力 | 是否满足 |
|------|------------|---------|
| 模糊文本搜索 | LIKE / FTS5 (全文索引) | ✅ 可满足 |
| 聚合统计 (KPI) | GROUP BY / window functions | ✅ 满足 |
| JSON 字段查询 | `json_extract()` / `->` 运算符 | ✅ SQLite 3.38+ |
| 向量相似度搜索 | 不支持 | ❌ 需 ChromaDB (已有) |
| 时间序列分析 | 无内置 | ⚠️ 需应用层实现 |

**结论**: 结构化和 JSON 查询 SQLite 完全满足。向量搜索已由 ChromaDB 覆盖。唯一缺口是时间序列（需应用层）。

## 迁移阈值

满足以下**任意 2 项**时才考虑迁移到 PostgreSQL:

1. ☐ 并发写入者 > 3 (多 worker 并行执行独立模块)
2. ☐ 单表行数 > 1000 万 (当前最大表 < 1 万行)
3. ☐ 需要多环境实时同步 (dev/staging/prod)
4. ☐ 需要时间序列数据库 (InfluxDB/TimescaleDB)
5. ☐ 团队从 1 人扩展到 5+ 人，需要 DBA 运维

**当前状态**: 0/5 项触发。**维持 SQLite**。

## 建议行动

| 优先级 | 行动 | 原因 |
|--------|------|------|
| P0 | 维持现状 — SQLite + ChromaDB | 当前规模远低于阈值 |
| P1 | `audit.db` 启用以 WAL 模式 | 预防并发读/写冲突 |
| P2 | 为 `runs.db` 添加 FTS5 全文索引 | 加速执行历史搜索 |
| P2 | 评估 Litestream 实时备份 | 零停机备份到 S3/本地 |
| — | PostgreSQL 迁移 | 等到 ≥2 项阈值触发后再评估 |

---

# 总结

| 工作线 | 下一步 | 预估 |
|--------|------|------|
| sop_dev 治理 | 创建 3 步 (治理文档 → SOP_STATUS → agent-definitions 补齐) | 3d |
| 数据库评估 | P0: 维持 SQLite; P1: WAL 模式; P2: FTS5 + Litestream | 0.5d |
