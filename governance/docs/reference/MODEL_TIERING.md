# 模型分层策略（Provider-Agnostic）

> 版本: 2.0 | 2026-06-12 | 支持 DeepSeek / GLM / Claude / ChatGPT / 其他模型

## 核心原则

**按任务复杂度选择能力层级，而非绑定特定模型。** 模型选择权在 CLI session（用户启动时指定 `--model`），工作流只表达意图。

## 能力层级定义（L0-L3）

| 层级 | 能力需求 | 特征 | 适用任务 | 占比 |
|------|---------|------|---------|------|
| **L0** | 无 LLM | 纯工具调用（Write/Bash） | 文件写入、状态持久化、Excel 生成 | 15% |
| **L1** | 快速模型 | 结构化 I/O、规则匹配、模板填充、无需深度推理 | 状态检查、骨架分析、合规检查、去重、策略生成 | 35% |
| **L2** | 均衡模型 | 代码生成、业务理解、中等推理 | 模块建模、页面分析、代码生成、Bug 分析、报告 | 45% |
| **L3** | 最强模型 | 复杂架构决策、首次分析、多步推理 | PROJECT_CONTEXT 初始化、跨模块架构审计 | 5% |

## Provider → 模型映射

| 层级 | Claude | DeepSeek | GLM | ChatGPT | 通用原则 |
|------|--------|----------|-----|---------|---------|
| **L1** | Haiku 4.5 | Flash / V3-Lite | GLM-4-Flash | GPT-4o-mini | 选该 provider 最快/最便宜的模型 |
| **L2** | Sonnet 4.6 | V4-Pro / R1 | GLM-4 | GPT-4o / GPT-5 | 选该 provider 性价比最优的模型 |
| **L3** | Opus 4.8 | R1-0528 / V4-Pro(1M) | GLM-4-Plus | GPT-5 / o3 | 选该 provider 最强推理模型 |

> 💡 **实际使用**: 用户在 CLI 指定 session 模型（如 `--model deepseek-v4-pro`），对应 L2。L1 任务由工作流内的 `model` 参数尝试降级（Claude 可用 `haiku`，其他 provider 忽略该参数，仍用 session 模型）。L3 任务由用户显式切换 session 模型执行。

## full-sop.workflow.js 中的层级分配

| agent() 调用 | 层级 | 意图 | workflow.js 标记 |
|-------------|------|------|-----------------|
| `preflight-full-sop` | **L1** | 文件读取 + JSON 输出，纯结构化 | `model: 'haiku'`（Claude 降级，其他忽略） |
| `write-status` | **L1** | 文件写入 + 验证 | `model: 'haiku'` |
| `event-process:{module}` | **L1** | 事件队列检查 | `model: 'haiku'` |
| `init-project` | L2 | 项目初始化需要推理 | 跟随 session |
| `req:{module}` | L2 | 模块建模需要业务理解 | 跟随 session |
| `design:{page}` | L2 | 测试设计需要推理 | 跟随 session |
| `auto:{page}` | L2 | 代码生成需要准确性 | 跟随 session |
| `exec:{module}` | L2 | 测试执行需要判断 | 跟随 session |
| `bug:{module}` | L2 | Bug 分析需要深度推理 | 跟随 session |
| `fix:{module}` | L2 | 代码修复需要准确性 | 跟随 session |
| `report:{module}` | L2 | 报告生成需要综合 | 跟随 session |
| `knowledge:{module}` | L2 | 知识提取需要判断 | 跟随 session |
| **PROJECT_CONTEXT 初始化** | **L3** | 首次项目分析 | 用户手动切换到最强模型 |

## 独立 Skill 的层级推荐

| Skill | 层级 | 原因 |
|-------|------|------|
| `code-consistency-checker` | **L1** | 纯规则匹配，8 条红线逐项检查 |
| `auto-strategy` | **L1** | 覆盖矩阵是结构化模板输出 |
| `completeness-check` | **L1** | 文件存在性 + 行数统计 |
| `page-analysis`（骨架/无 HTML） | **L1** | 模板填充，无深度分析 |
| `excel-exporter` | **L0** | Python 脚本执行，无 LLM |
| `page-analysis`（有 HTML） | L2 | HTML 解析需要推理 |
| `tech-analysis` | L2 | 定位器设计需要 DOM 理解 |
| `page-object-generator` | L2 | 代码生成需要准确性 |
| `test-script-generator` | L2 | 代码生成需要准确性 |
| `bug-analysis` | L2 | 根因分析需要深度推理 |
| `module-modeling` | L2 | 模块边界分析需要业务理解 |
| `requirement-analysis` | L2 | 需求文档解析需要推理 |

## 成本估算（以价格最低的 L1 模型为基准 = 1×）

| 场景 | 全 L2 | 分层后（L0+L1+L2） | 节省 |
|------|-------|-------------------|------|
| Full SOP（5 页，1 轮通过） | 100% | ~55% | **45%** |
| Full SOP（含 2 轮调试） | 100% | ~60% | **40%** |
| 单 Skill 调用（合规检查） | 100% | ~25% | **75%** |
| 单 Skill 调用（代码生成） | 100% | 100% | 0% |
| DeepSeek 全部 V4-Pro vs V4-Pro+Flash 混合 | ¥100 | ¥55 | **45%** |
| GLM 全部 GLM-4 vs GLM-4+Flash 混合 | ¥100 | ¥55 | **45%** |
| Claude 全部 Sonnet vs Haiku+Sonnet 混合 | $100 | $45 | **55%** |

## 实施状态

| 项目 | 状态 |
|------|------|
| full-sop.workflow.js L1 标记 | ✅ 3 处 `model: 'haiku'`（Claude 生效，其他 provider 忽略） |
| Skill 层级推荐文档 | ✅ 本文档 |
| CLI session 模型控制 | ✅ 用户通过 `--model` 指定 |
| L0 无 LLM 任务 | ✅ writeStatus batched, event emit 移除 |
| L3 手动切换 | 🔜 建议 PROJECT_CONTEXT 初始化时提示切换最强模型 |
