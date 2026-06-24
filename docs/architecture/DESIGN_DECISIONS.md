# Alice V1 — Design Decisions

> 记录所有不可逆的关键产品设计决策  
> 每次 PR、重构、新功能对照本文  
> 目的：不用重新讨论已经决定的事

---

## D-001: Project First, not Chat First

**决策:** Project 是平台第一公民。用户打开平台第一眼看到的是项目列表，不是聊天框。

**为什么不是 Chat First？**
- Chat 是瞬时对话，Project 是持久资产
- 测试工程师的工作单位是项目，不是对话
- Chat 作为 Agent 交互入口存在（终端内），但不是主导航

**代价:** Chat 体验不如独立 Chat 产品。需要用户理解 Project 概念。

**参考:** Aperant Workspace 理念。Vercel Dashboard 项目组织方式。

---

## D-002: Artifact First, not Conversation First

**决策:** SOP 每个 Phase 的产出是持久化的 Artifact（文档、脚本、报告），不是对话记录。平台是资产积累系统。

**为什么？**
- Artifact 可被搜索、版本对比、跨会话引用
- Memory 基于 Artifact 构建，不是基于对话
- 治理审计需要 Artifact 的来源链

**代价:** Agent 每次执行都需写文件。增加 I/O。短期看起来比 Chat 慢。

**参考:** Aperant Spec Directory。Constitution §P2 (Governance 配置层)。

---

## D-003: Timeline as Primary Debugger

**决策:** 当 Agent 出问题时，用户第一入口是 Timeline（Agent 活动时间线），不是原始日志。

**为什么不是 Logs First？**
- 日志是机器的，Timeline 是人的
- Timeline 展示因果关系（Phase → Artifact → Error → Retry）
- 降低调试 Agent 的认知负担

**代价:** 需要为每个 Agent 事件结构化记录。增加存储和处理。

**参考:** Aperant Agent Events。Datadog APM Timeline。Chrome DevTools Performance 面板。

---

## D-004: Observability 独立于 Execution

**决策:** Execution = Run/Pause/Resume/Cancel。Observability = Timeline/Logs/Metrics/Cost/Memory。两个独立视图。

**为什么不分在一起？**
- Execution 是操作面板，Observability 是分析面板
- 不同用户角色关注不同面板
- 避免单个页面功能膨胀

**代价:** 用户在两个页面间切换。需要一致的导航。

**参考:** Kubernetes Dashboard (Workloads vs Monitoring)。Grafana (Explore vs Dashboards)。

---

## D-005: Progressive Disclosure

**决策:** 用户首次进入只看到 Dashboard + 项目列表。打开项目后 Workspace 逐步展开。运行 SOP 后 Timeline/Reports/Knowledge 才出现。

**为什么不是一次性展示所有功能？**
- 新用户学习成本低
- 功能按使用阶段自然浮现
- 避免信息过载

**代价:** 开发复杂度增加（条件渲染）。高级用户可能需要多点一次。

**参考:** Vercel Dashboard。Figma 新手引导。Apple HIG Progressive Disclosure。

---

## D-006: .tlo/ as Project Context Boundary

**决策:** 项目上下文跟随项目（`.tlo/` 目录），不存储在平台中央。平台降级为 Registry + Loader。

**为什么不是中央存储？**
- 项目自包含：clone 项目即包含全部上下文
- 平台解耦：平台不依赖特定项目路径
- 团队协作：项目上下文可通过 Git 共享

**代价:** 平台需要扫描和加载逻辑。跨项目查询需额外索引。

**参考:** `.vscode/`, `.github/workflows/`, `.cursor/` — 工具配置跟随项目模式。

---

## D-007: Capability over Tool

**决策:** Agent 调用 `browser.navigate()`，不是 `tool('browser_use__navigate')`。Capability 是领域语义，Tool 是实现细节。

**为什么？**
- 更换底层工具不影响 Agent 行为（BrowserUse → Playwright 透明）
- Capability 可按 Agent 类型授权（Automation Agent 不能 Browser）
- 插件可注册新 Capability

**代价:** 多一层抽象。Capability→Tool 映射需维护。

**参考:** Constitution §P4。Aperant Tool Registry（借鉴但改为 Capability 抽象）。

---

## D-008: Live Agent Graph

**决策:** V1 必须包含 Live Agent Graph — 用户可看到 SOP 图实时执行状态，当前节点高亮，已完成节点标记。

**为什么 V1 就做？**
- 这是产品辨识度最高的页面
- 5 分钟 Demo 即可展示平台核心价值
- 区别于 ChatGPT 类产品的关键差异

**代价:** 前端需实现 LangGraph 状态图可视化。D3.js 或 Cytoscape.js。

**参考:** LangGraph Studio。Airflow DAG 可视化。N8N 工作流编辑器。

---

## D-009: Extension Points over Core Changes

**决策:** 新能力优先通过 Extension Point (Plugin / Skill / MCP / Config) 加入。Core 已冻结，非 Architecture Review 不得变更。

**为什么不是直接改 Core？**
- Core 稳定性是平台长期可维护的基础
- Extension Point 允许实验而不影响稳定
- 第三方可贡献而不需了解 Core

**代价:** Extension Point 设计需提前规划。某些能力可能受限于扩展接口。

**参考:** Constitution §P6。VSCode Extension API。Kubernetes CRD。

---

## D-010: Phase-Aware Model Tier

**决策:** 不同 SOP Phase 使用不同 LLM 模型。Complex phases (test-design, automation) → max tier。Simple phases (execution, report) → econ tier。

**为什么不是统一模型？**
- Token 成本可降 40-60%
- 简单 Phase 不需要强推理模型
- 可按项目预算调整

**代价:** 模型切换增加延迟（首次冷启动）。配置不当可能影响质量。

**参考:** Aperant phase-config.ts。Anthropic model tiering guide。

---

## D-011: Testing Workspace Hierarchy

**决策:** Workspace 以 Project → Module → Page 三层组织。不是 Git 仓库组织，不是 Chat 组织。

**为什么是 Module/Page？**
- 测试的最小执行单元是 Page
- Module 是业务领域的自然聚合
- 与现有 SOP 结构（module + pages）一致

**代价:** 非 Web 项目（API、Mobile）需适配不同的组织方式。

**参考:** 无。这是 AITest 独有的 Testing-native 设计。

---

## D-012: Backend API as Contract

**决策:** 所有前端功能通过 REST API 访问。API 是前后端的 Contract，后端实现可替换。

**核心端点:**

| 端点 | 用途 |
|------|------|
| `GET /api/projects` | 项目列表 |
| `GET /api/projects/:id` | 项目详情 + 模块列表 |
| `POST /api/sop/start` | 启动 SOP |
| `POST /api/sop/:runId/pause` | 暂停 |
| `POST /api/sop/:runId/resume` | 恢复 |
| `GET /api/sop/:runId/status` | SOP 状态 + 进度 |
| `GET /api/timeline/:projectId` | Timeline 事件流 |
| `GET /api/artifacts/:projectId/:module/:page` | Artifact 列表 |
| `GET /api/kpi/operational` | 8 运营指标 |
| `GET /api/kpi/summary` | KPI 摘要 |
| `GET /health` | 平台健康 |
| `GET /metrics` | Prometheus |

**代价:** 前后端需同步 API 变更。Contract 测试需维护。

---

> **以上 12 项决策是 Alice V1 的设计基线。任何偏离需重新讨论 D-XXX 并更新本文。**
