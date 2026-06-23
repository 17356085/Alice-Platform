# AI 自动化测试项目 — 改进计划 v2.1

> **来源**：架构审计评估（2026-06-12）→ 提取 3 个高 ROI 改进方向
> **目标**：交付给独立 AI 会话执行，无需原始对话上下文
> **前提**：执行前请先阅读 `CLAUDE.md`（项目入口）和 `governance/README.md`（治理骨架）

---

## 快速导航

| 任务 | 优先级 | 预计工期 | 预期收益 | 依赖 |
|------|--------|----------|----------|------|
| [任务 A：RAG 接入 bug-analysis Skill](#任务-arag-接入-bug-analysis-skill) | **P0** | 1-2 小时 | Token -30%, Bug 匹配速度 10x | 无 |
| [任务 B：Knowledge Agent 事件驱动](#任务-bknowledge-agent-事件驱动自动化) | **P1** | 2-3 小时 | Agent 自动触发率 +40% | 任务 A 完成后更佳 |
| [任务 C：Agent 间结构化接口](#任务-cagent-间结构化接口) | **P2** | 3-4 小时 | 下游 Agent Token 节省 50%, 准确率提升 | 无硬依赖 |

---

## 背景（给接手 AI 的上下文）

### 项目是什么

鞍集涂源管理系统（Vue 3 + Element Plus Web 管理端 + 微信小程序端）的 AI 辅助自动化测试项目。使用 Python 3.x + pytest + Selenium + Allure。

### 当前架构（三层）

```
Skill 层 (28 个原子 AI 能力) → Agent 层 (8 个 Skill 编排器) → Workflow 层 (full-sop 全流程编排)
```

- **8 个 Agent**：project / requirement / test-design / automation / execution / bug-analysis / report / knowledge
- **文件驱动上下文传递**：PROJECT_CONTEXT → MODULE_CONTEXT → PAGE_CONTEXT → TECH_ANALYSIS
- **RAG 引擎已就绪**：`aitest/rag_engine.py` — ChromaDB 5 集合 235 文档已入库
- **Event Bus 已就绪**：`aitest/event_bus.py` — 4 种事件类型，emit/listen/process CLI
- **Agent Scheduler 已就绪**：`aitest/agent_scheduler.py` — 前置条件检测 + 自动推荐
- **MCP Server 已就绪**：`aitest/mcp_server.py` + `aitest/knowledge_server.py` — 2 个 MCP Server 已配置

### 核心痛点

1. **Bug 分析时 RAG 未集成**：`rag_engine.py` 的 `search_known_issues()` 存在但 bug-analysis Skill 没有调用它。Bug 分析时靠 AI 手动检索已知问题，浪费 Token 且容易遗漏。
2. **Knowledge Agent 仍是手动触发**：Event Bus 定义了 `AgentCompleted → knowledge-manager` 的映射，但 full-sop workflow 在末尾才显式调用 Knowledge Agent，不是事件驱动的"横向贯穿"。
3. **Agent 间靠 Markdown 传递信息**：下游 Agent（如 automation-agent）每次需完整解析上游的 PAGE_CONTEXT.md / TEST_CASES.md，没有结构化接口。

### 关键文件路径

```
governance/
├── skills/
│   ├── diagnosis/bug-analysis.md          ← 任务 A 修改目标
│   ├── knowledge/knowledge-manager.md      ← 任务 B 涉及
│   ├── automation/
│   │   ├── page-object-generator.md        ← 任务 C 涉及
│   │   ├── test-script-generator.md        ← 任务 C 涉及
│   │   └── tech-analysis.md               ← 任务 C 涉及
│   └── skill-registry.yaml
├── agents/
│   ├── full-sop.workflow.js               ← 任务 B 修改目标
│   ├── bug-analysis-agent.workflow.js     ← 任务 A 可能涉及
│   └── automation-agent.workflow.js       ← 任务 C 涉及
├── context/
│   ├── known-issues.yaml
│   └── source-of-truth.md
├── templates/
└── docs/
    ├── IMPROVEMENT_PLAN_v2.1.md           ← 你正在读的文件
    └── AI_TEST_PLATFORM_ARCHITECTURE_OPTIMIZATION.md  ← 架构背景参考

aitest/
├── rag_engine.py        ← RAG 引擎 (已实现, 5 集合)
├── event_bus.py         ← Event Bus (已实现, 4 事件类型)
├── agent_scheduler.py   ← Agent 调度器 (已实现)
├── workflow_engine.py   ← Workflow DAG 引擎 (已实现)
├── mcp_server.py        ← MCP Server - aitest-tools
└── knowledge_server.py  ← MCP Server - aitest-knowledge

.claude/
├── mcp.json             ← MCP 配置
└── skills/              ← Agent 斜杠命令入口
```

---

## 任务 A：RAG 接入 bug-analysis Skill

### 目标

让 bug-analysis Skill 在执行失败分析时，**自动优先检索已知问题库**（RAG），匹配结果作为分析上下文注入，减少 Token 浪费和漏检。

### 当前状态

- `aitest/rag_engine.py` 的 `search_known_issues(query)` 已实现且可用
- `aitest/mcp_server.py` 暴露了 `rag_search_known_issues` MCP Tool
- `governance/skills/diagnosis/bug-analysis.md` **没有**自动调用 RAG 的步骤
- Bug 分析时 AI 可能手动检索 known-issues.yaml，但不保证每次都做

### 改造内容

#### A-1：修改 bug-analysis.md Skill Prompt（核心改动）

文件：`governance/skills/diagnosis/bug-analysis.md`

在 Skill 的流程定义中，**在执行前增加 L0 自动 RAG 检索步骤**：

```markdown
## 执行流程

### L0：自动 RAG 已知问题匹配（必须执行，不可跳过）

在分析任何失败用例之前，先调用 RAG 检索：

1. 对每个失败的测试用例，提取错误签名：
   - 异常类型（如 `NoSuchElementException`, `TimeoutException`, `AssertionError`）
   - 关键报错信息（如 "el-cascader", "loading", "遮罩"）
   - 失败的页面/模块名称

2. 调用 MCP Tool `rag_search_known_issues`：
   ```json
   {
     "query": "<错误签名拼接>",
     "n_results": 5
   }
   ```

3. 对返回结果：
   - 若 `distance < 1.0`（高相似度）→ 标记为「可能已知问题」
   - 若 `distance < 0.5`（极高相似度）→ 直接匹配，跳过深度分析
   - 将匹配结果写入 BUG_ANALYSIS 报告的「已知问题匹配」栏

4. 如果 RAG 未匹配（所有结果 distance > 1.0），正常进入 L1 深度分析。

### L1：深度分析（仅在 RAG 未匹配时执行）
...（原有分析流程）
```

**关键约束**：L0 步骤标记为「必须执行，不可跳过」，并在 Skill Prompt 开头用 `🔴 MANDATORY` 标注。

#### A-2：确保 MCP Tool `rag_search_known_issues` 可用

文件：`aitest/mcp_server.py`

检查 `rag_search_known_issues` 工具是否已正确定义并暴露。如果已有则跳过；如果缺失则添加。

工具签名：
```python
@mcp.tool()
def rag_search_known_issues(query: str, n_results: int = 5, category: str = None) -> list[dict]:
    """搜索已知问题库，返回匹配的已知问题和相似度。用于 Bug 分析时的自动匹配。"""
    from aitest.rag_engine import search_known_issues
    return search_known_issues(query, n_results=n_results, category=category)
```

验证方式：
```bash
python -m aitest.rag_engine index   # 确保索引是最新的
python -m aitest.rag_engine status  # 确认 5 个集合都有文档
```

#### A-3：修改 bug-analysis-agent.workflow.js（可选）

文件：`governance/agents/bug-analysis-agent.workflow.js`

如果 bug-analysis Agent 的 workflow 脚本中有显式的步骤定义，在分析步骤前增加 L0 检索步骤。如果 Agent 直接委托给 Skill（即 Skill 工具调用），则只需改 A-1。

#### A-4：添加降级逻辑

在 bug-analysis.md 中增加降级规则：
```markdown
### 降级规则
- 如果 MCP Tool `rag_search_known_issues` 调用失败（超时/服务不可用）：
  → 降级为手动读取 `governance/context/known-issues.yaml`
  → 基于关键字做简单匹配
  → 在报告中标注「RAG 不可用，使用降级匹配」
- 如果 known-issues.yaml 也不可读：
  → 跳过已知问题匹配，直接进入深度分析
  → 在报告中标注「已知问题匹配不可用」
```

### 验收标准

1. 对任意模块执行 bug-analysis，日志/BUG_ANALYSIS 报告中出现「已知问题匹配」栏
2. 用已知问题（如 "el-cascader NoSuchElementException"）测试，RAG 能匹配到 EP-001
3. 报告中标注匹配相似度（distance 值）
4. RAG 不可用时能降级到手动匹配或跳过，不会阻塞分析流程

---

## 任务 B：Knowledge Agent 事件驱动自动化

### 目标

让 Knowledge Agent 从「full-sop workflow 末尾显式调用」变为「监听 Event Bus 事件自动触发」，
实现真正的"横向贯穿"——每个 Agent 完成时 Knowledge Agent 自动执行知识沉淀。

### 当前状态

- `aitest/event_bus.py` 完整实现了 emit / listen / process CLI
- 4 种事件类型已定义：`AgentCompleted`, `BugClosed`, `CycleEnd`, `ContextUpdated`
- `EVENT_ACTIONS` 映射已定义（事件 → Knowledge Agent 动作）
- 但 **没有人调用 `emit()`**（事件未产生）和 **没有人调用 `process_pending()`**（事件未消费）
- full-sop.workflow.js 中 Knowledge Agent 在 Phase 8 显式调用，不是事件驱动的

### 改造内容

#### B-1：在 full-sop.workflow.js 中埋点 emit 事件

文件：`governance/agents/full-sop.workflow.js`

在每个 Agent 调用成功后，通过 Bash 命令发射事件：

```javascript
// 在每个 Agent 完成后添加 (示例: requirement-agent 完成后)
const emitResult = await agent(
  `Run: python -m aitest.event_bus emit AgentCompleted agent=requirement-agent module=${MODULE} status=success artifacts="MODULE_CONTEXT.md"
  
  Return JSON: { "emitted": true, "event_id": "..." }`,
  {
    label: 'emit-event-req',
    schema: { type: 'object', properties: { emitted: { type: 'boolean' }, event_id: { type: 'string' } }, required: ['emitted'] }
  }
)
```

需要埋点的位置（共 8 处）：
| Agent 完成时 | 事件类型 | 触发时机 |
|-------------|---------|---------|
| Project Agent | `AgentCompleted` | PROJECT_CONTEXT 初始化完成后 |
| Requirement Agent | `AgentCompleted` | MODULE_CONTEXT 生成后 |
| Test Design Agent (每页面) | `AgentCompleted` | 每页面 PAGE_CONTEXT + TEST_CASES 完成后 |
| Automation Agent (每页面) | `AgentCompleted` | 每页面代码生成 + 合规检查通过后 |
| Execution Agent | `AgentCompleted` | 测试执行完成后 |
| Bug Analysis Agent | `BugClosed` | Bug 分析完成后 |
| Report Agent | `CycleEnd` | 报告生成完成后 |

> 💡 实际埋点时，可以仅在关键的几个 Agent 完成后埋点（requirement / test-design / automation / execution / bug-analysis），而不是全部 8 个。避免事件爆炸。

#### B-2：将 full-sop Phase 8 的 Knowledge Agent 调用改为事件消费

文件：`governance/agents/full-sop.workflow.js`

将 Phase 8 (Knowledge) 改为：

```javascript
phase('Knowledge')

log(`🧠 处理待处理事件...`)

const eventResult = await agent(
  `Run: python -m aitest.event_bus process
  
  然后检查输出的每个事件的动作建议，调用 Skill 工具执行 knowledge-agent 斜杠命令处理它们。
  
  Call: Skill skill="knowledge-agent" args="source=event-bus"
  
  完成后汇报 JSON:
  {
    "events_processed": 0,
    "new_known_issues": 0,
    "updated_pitfalls": 0,
    "knowledge_synced": true
  }`,
  {
    label: `knowledge:${MODULE}`,
    phase: 'Knowledge',
    schema: { ... }
  }
)
```

#### B-3：增强 knowledge-manager Skill 以支持事件驱动模式

文件：`governance/skills/knowledge/knowledge-manager.md`

在现有双模式（extract / precipitate）基础上增加第三种触发模式：

```markdown
## 触发模式

| 模式 | 入口 | 说明 |
|------|------|------|
| `mode=extract` | 单个 Bug / Agent → 知识提取 | 原有模式 |
| `mode=precipitate` | 测试周期结束 → 批量沉淀 | 原有模式 |
| `mode=event-driven` | Event Bus `process` 输出 → 自动处理 | **新增** |

### mode=event-driven 流程

1. 读取 `python -m aitest.event_bus process` 的输出
2. 对每条待处理事件：
   - `AgentCompleted` → 检查该 Agent 的产出中是否有可沉淀的知识
   - `BugClosed` → 更新 known-issues.yaml 中对应条目的 occurrence_count
   - `CycleEnd` → 执行批量知识沉淀
   - `ContextUpdated` → 检查下游文档是否需要同步
3. 去重：新知识写入前，与 known-issues.yaml 现有条目比对
4. 输出：更新后的 known-issues 条目数
```

#### B-4（可选）：在 Agent Scheduler 中集成事件发射

文件：`aitest/agent_scheduler.py`

在 `auto_advance()` 函数中，当 Agent 完成时自动调用 `event_bus.emit()`：

```python
from aitest.event_bus import emit

def auto_advance(module_name: str, auto_trigger: bool = False) -> dict:
    ...
    if result["action"] == "complete":
        emit("CycleEnd", module=module_name, stats=json.dumps(result))
    ...
```

这样，即使不走 full-sop workflow，单独使用 Agent 时也能产生事件。

### 验收标准

1. 运行 `python -m aitest.event_bus listen` 能看到 `AgentCompleted` 事件被发射（如果刚执行过 full-sop）
2. full-sop 运行完后，Knowledge Agent 自动处理所有待处理事件
3. 事件处理后，known-issues.yaml 中被匹配条目的 `occurrence_count` 自动递增
4. 如果 Event Bus 无待处理事件，Knowledge Agent 不报错，正常跳过

---

## 任务 C：Agent 间结构化接口

### 目标

在高频 Agent 对之间建立结构化数据接口，替代「下游 Agent 通读上游 Markdown 文档」的模式，
减少 Token 消耗，提升信息传递准确性。

### 当前状态

| Agent 对 | 当前传递方式 | Token 浪费估算 |
|----------|-------------|---------------|
| test-design → automation | PAGE_CONTEXT.md + TEST_CASES.md（Markdown） | automation-agent 每次通读 2-3 个完整 Markdown 文件 |
| automation → execution | PageObject.py（代码） | 较低（代码本身就是结构化） |
| execution → bug-analysis | 失败日志 + Allure JSON | 中等 |

**最高价值的优化对象**：test-design-agent → automation-agent 这一对。因为：
- 这是最频繁的 Agent 对调用（每个页面都要走一次）
- PAGE_CONTEXT.md 和 TEST_CASES.md 的 Markdown 体量最大
- automation-agent 需要的是元素定位信息，不是完整的页面描述

### 改造内容

#### C-1：定义结构化接口 Schema

新建文件：`governance/context/interfaces/page-to-automation.schema.yaml`

```yaml
# test-design-agent → automation-agent 结构化接口
interface: page-to-automation
version: "1.0"
source_agent: test-design-agent
target_agent: automation-agent

fields:
  meta:
    module: string          # 模块名
    page_name: string       # 页面名 (PascalCase)
    page_slug: string       # URL slug
    page_url: string        # 完整 URL 路径
    vue_components:         # 页面使用的 Element Plus / 自定义组件
      - component: string   # el-table, el-dialog, el-cascader, stat-card ...
        count: integer
        risk_flags: [string]  # teleport, dynamic, animation, conditional

  elements:                 # 核心交互元素（从 PAGE_CONTEXT 提取）
    - name: string          # 业务名称（如 "告警名称输入框"）
      selector: string      # 推荐定位器（CSS 或 相对 XPath）
      selector_type: enum   # CSS_SELECTOR | XPATH | ID | NAME | TEXT
      element_type: enum    # input | button | select | table | dialog | cascader | switch | datepicker
      el_component: string  # Element Plus 组件名（如 el-input, el-cascader），无则为 null
      interaction: enum     # click | input | select | wait | scroll | hover | upload
      wait_strategy: string # 交互后需要的等待策略（如 "wait_vue_stable" / "WebDriverWait 3s"）
      locator_notes: string # 定位注意事项（如 "级联选择器需等待子节点加载"）
      risk_level: enum      # low | medium | high
      risk_reason: string   # 风险原因

  test_scenarios:           # 关键测试场景摘要（从 TEST_CASES 提取）
    - id: string            # TC-001
      title: string         # 场景名称
      priority: enum        # P0 | P1 | P2
      type: enum            # positive | negative | boundary | destructive
      preconditions: [string]
      steps_summary: string # 操作步骤简述
      expected: string      # 预期结果
      relates_to_elements: [string]  # 关联的元素 name

  page_behaviors:           # 页面行为特征（从 RISK_MODEL 提取）
    - behavior: string      # 如 "表格行内编辑弹窗" / "批量操作后刷新"
      triggers: [string]    # 触发条件
      wait_required: boolean
      wait_suggestion: string
```

这个 Schema 是**纯数据**，不含任何格式排版——automation-agent 拿到后可以直接消费，不用解析 Markdown。

#### C-2：修改 test-design-agent 产出结构化接口文件

文件：`governance/agents/test-design-agent.workflow.js`（或对应的 `.md` 文件）

在 test-design-agent 的 Skill 编排中，**在生成完 PAGE_CONTEXT.md + TEST_CASES.md 后**，增加一步：
生成 `PAGE_INTERFACE.yaml`（遵循 C-1 的 Schema）。

具体做法：修改 test-design-agent 的定义，在其 Skill 集合中增加一个隐式的结构化提取步骤：

```markdown
## test-design-agent 产出物（更新后）

| 文件 | 格式 | 说明 |
|------|------|------|
| PAGE_CONTEXT.md | Markdown | 页面元素完整分析（人类可读） |
| RISK_MODEL.md | Markdown | 风险模型 |
| TEST_DESIGN.md | Markdown | 测试设计 |
| TEST_CASES.md | Markdown | 测试用例 |
| **PAGE_INTERFACE.yaml** | **YAML** | **结构化接口（新增）** |

PAGE_INTERFACE.yaml 的生成规则：
- 从 PAGE_CONTEXT.md 中提取元素信息 → 填入 elements 数组
- 从 TEST_CASES.md 中提取场景摘要 → 填入 test_scenarios 数组
- 从 RISK_MODEL.md 中提取行为特征 → 填入 page_behaviors 数组
```

#### C-3：修改 automation-agent 消费结构化接口

文件：`governance/agents/automation-agent.workflow.js`

修改 automation-agent 的上下文加载逻辑：

**改造前**：
```javascript
// automation-agent 启动时
1. Read PAGE_CONTEXT.md (完整读取)
2. Read TEST_CASES.md (完整读取)
3. Read RISK_MODEL.md (完整读取)
```

**改造后**：
```javascript
// automation-agent 启动时
1. Read PAGE_INTERFACE.yaml (结构化数据，直接消费)  ← 新增
2. Read PAGE_CONTEXT.md (仅在需要补充细节时按需读取)  ← 降级为可选
3. Read TEST_CASES.md (仅在需要补充细节时按需读取)   ← 降级为可选
```

具体修改：在 `automation-agent.workflow.js` 的初始上下文加载阶段，先检查 `PAGE_INTERFACE.yaml` 是否存在：
```javascript
const hasInterface = await checkFile(`${MODULE_DIR}/pages/${pageName}/PAGE_INTERFACE.yaml`)
if (hasInterface) {
  // 优先消费结构化接口
  loadStructuredInterface()
} else {
  // 降级：完整读取 Markdown（向后兼容）
  loadMarkdownContext()
}
```

#### C-4：更新 source-of-truth.md

文件：`governance/context/source-of-truth.md`

在事实源分工表中增加一行：
```markdown
| Agent 间结构化接口 | context/interfaces/*.schema.yaml + modules/*/pages/*/PAGE_INTERFACE.yaml | 新增 |
```

#### C-5：为其他 Agent 对预留接口定义（骨架）

新建文件：`governance/context/interfaces/README.md`

```markdown
# Agent 间结构化接口

## 已实现
- `page-to-automation.schema.yaml` — test-design-agent → automation-agent

## 规划中
- `execution-to-bug-analysis.schema.yaml` — execution-agent → bug-analysis-agent（失败用例摘要）
- `automation-to-execution.schema.yaml` — automation-agent → execution-agent（测试清单）
```

### 向后兼容策略

- PAGE_INTERFACE.yaml 是**增量产物**，不影响现有 Markdown 文档
- automation-agent 检测 PAGE_INTERFACE.yaml 存在时优先使用，不存在时降级为完整 Markdown 读取
- 已完成的模块（如 tank, equipment）不需要重新生成 PAGE_INTERFACE.yaml——仅对新模块生效
- 旧模块如需享受 Token 优化，可手动运行 test-design-agent 重新生成

### 验收标准

1. 新模块执行 test-design-agent 后，页面目录下出现 `PAGE_INTERFACE.yaml`
2. automation-agent 消费 PAGE_INTERFACE.yaml 时，不再读取完整 PAGE_CONTEXT.md（或仅按需读取）
3. 生成的 PageObject / test_*.py 代码质量不低于改造前
4. Token 消耗对比：test-design → automation 阶段的 Token 消耗下降 40%+
5. 旧模块不受影响（降级到 Markdown 读取）

---

## 执行顺序建议

```
第 1 步：任务 A (RAG 接入)     ← 最快见效，1-2h，独立无依赖
第 2 步：任务 B (事件驱动)     ← 依赖对 full-sop workflow 的理解，2-3h
第 3 步：任务 C (结构化接口)   ← 涉及文件最多，3-4h，需仔细测试向后兼容
```

如果时间有限，**只做任务 A** 就能获得最大的单点收益（Token -30%, Bug 匹配速度 10x）。

---

## 风险与注意事项

### 任务 A 风险
- RAG 索引可能过期：执行前先跑 `python -m aitest.rag_engine index` 确保索引最新
- ChromaDB 依赖：确认 `chromadb` 包已安装（`pip list | grep chromadb`）
- MCP Tool 不可用时的降级逻辑必须在 Skill 中写死，不能靠 AI 自己判断

### 任务 B 风险
- 事件爆炸：如果每个 Agent 完成都发射事件，full-sop 一次运行会产生 8+ 个事件。建议先在关键节点（3-4 个 Agent）埋点试点
- Event Bus 是文件持久化的，注意清理旧事件（`python -m aitest.event_bus clean`）

### 任务 C 风险
- Schema 过度设计：PAGE_INTERFACE.yaml 的字段定义不要一上来就追求完美。先定义 automation-agent **实际需要**的字段，后续迭代补充
- 向后兼容：确保 `if hasInterface then ... else ...` 的分支逻辑覆盖所有 automation-agent 的入口路径

---

## 相关文件索引

| 文件 | 任务 A | 任务 B | 任务 C |
|------|:---:|:---:|:---:|
| `governance/skills/diagnosis/bug-analysis.md` | ✏️ | | |
| `aitest/rag_engine.py` | 📖 | | |
| `aitest/mcp_server.py` | 📖 | | |
| `governance/agents/full-sop.workflow.js` | | ✏️ | |
| `aitest/event_bus.py` | | 📖 | |
| `governance/skills/knowledge/knowledge-manager.md` | | ✏️ | |
| `aitest/agent_scheduler.py` | | ✏️ | |
| `governance/context/interfaces/page-to-automation.schema.yaml` | | | ✨ |
| `governance/agents/automation-agent.workflow.js` | | | ✏️ |
| `governance/agents/test-design-agent.workflow.js` | | | ✏️ |
| `governance/context/source-of-truth.md` | | | ✏️ |

> 图例：✏️ = 需编辑 | 📖 = 需阅读理解 | ✨ = 新文件

---

> **给接手 AI 的提示**：按顺序执行任务 A → B → C。每个任务完成后运行对应的验收测试。遇到不确定时，参考 `governance/docs/architecture/AI_TEST_PLATFORM_ARCHITECTURE_OPTIMIZATION.md` 了解架构背景。
