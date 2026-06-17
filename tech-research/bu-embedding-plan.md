# Browser-Use 嵌入 Skill/Agent/SOP 实施方案

> 日期: 2026-06-17 | 版本: v2.0 (修订) | 前置: [ARCH_REVIEW](ARCH_REVIEW.md) + [验证报告](experiments/validation_report.md)
>
> **修订记录**: B1-B4 + C1-C2 按架构评审反馈修复

---

## 1. 总览

### 嵌入策略: Skill 增强 + Fixture 隔离

```
                  现有架构                         🆕 嵌入层
┌──────────────────────────────┐    ┌──────────────────────────────┐
│ SOP Graph (9 Phase)          │    │                              │
│  ├ Preflight                 │    │  Test-Design Phase           │
│  ├ Project Init              │    │  └ 🆕 page-observe Skill     │
│  ├ Requirement               │    │     (BrowserUse → 页面结构)   │
│  ├ Test Design ◀─────────────┤    │                              │
│  ├ Automation ◀──────────────┤    │  Automation Phase            │
│  ├ Execute & Debug           │    │  └ page-object-generator     │
│  ├ Bug Analysis              │    │     (mode: manual | browser-use)│
│  ├ Report                    │    │                              │
│  └ Knowledge                 │    │  Execute & Debug Phase       │
│                              │    │  └ 🆕 bu_heal fixture        │
│ Agent Runner (AgentLoop)     │    │     (conftest teardown hook) │
└──────────────────────────────┘    └──────────────────────────────┘
```

**原则**:
- 不改 SOP 图拓扑（不新增 Phase，不新增 Agent）
- Browser-Use 作为现有 Agent 的 Skill 增强
- 自愈**不嵌入 BasePage.click()**——作为独立 pytest fixture（B1 修复）
- 不改现有 `page-object-generator` Skill，只增加 `browser-use` mode（B2 修复）
- 自愈第一阶段**仅记录不写入** PO 文件（B3 修复）
- **不接 Event Bus**，先写文件日志积累数据（B4 修复）

---

## 2. 架构变更清单（修订版）

### 2.1 新增文件

| 文件 | 类型 | 说明 |
|------|------|------|
| `aitest/bu_adapter.py` | 适配器 (C2 修复) | Skill → BrowserUseDriver 桥接层 |
| `governance/skills/test-design/page-observe.md` | Skill 定义 | BrowserUse 页面结构观察 |
| `ZJSN_Test-master526/base/bu_heal_fixture.py` | Fixture (B1 修复) | 自愈 fixture — 不侵入 BasePage |
| `tests/test_bu_skills.py` | 测试 | Skill 单元测试 |

### 2.2 修改文件

| 文件 | 改动 | 说明 |
|------|------|------|
| `governance/skills/automation/page-object-generator.md` | +browser-use mode (B2) | 现有 Skill 增加 BrowserUse 辅助模式 |
| `governance/agents/agent-definitions.yaml` | +1 Skill 引用 | test-design-agent 增加 page-observe |
| `governance/skills/skill-registry.yaml` | +1 条目 | page-observe 注册 |
| `ZJSN_Test-master526/script/*/conftest.py` | +bu_heal fixture | 各模块 conftest 注册自愈 fixture |

### 2.3 不变文件（审核确认）

| 文件 | 原因 |
|------|------|
| `base/base_page.py` | B1: 零改动，保持同步方法语义纯净 |
| `aitest/event_bus.py` | B4: 第一阶段不接，先写日志 |
| `aitest/graphs/state.py` | 不新增 PhaseName 或 AgentName |
| `governance/skills/automation/po-generator.md` | B2: 不建新文件，改现有 page-object-generator |

---

## 3. 两个 Skill + 一个 Fixture

### 3.1 `page-observe` Skill（test-design-agent 新增）

```
┌─────────────────────────────────────────────────────┐
│ Skill: page-observe                                 │
│ File: governance/skills/test-design/page-observe.md │
│ Category: test-design                               │
│ Owner: test-design-agent (Test Design phase)        │
│ Trigger: page-analysis 后处理 | "探索XX页面"         │
├─────────────────────────────────────────────────────┤
│ Input:                                              │
│   - page_hash       Vue hash 路由                   │
│   - page_name       页面中文名                       │
│                                                     │
│ Process:                                            │
│   1. aitest.bu_adapter.observe_structure(hash)      │
│   2. 提取 search_fields / buttons / columns /       │
│      pagination                                     │
│   3. 输出 → PAGE_STRUCTURE.json                     │
│                                                     │
│ Output: PAGE_STRUCTURE.json (注入 PAGE_CONTEXT.md)  │
│                                                     │
│ Boundaries: 不生成代码 / 不分析业务 / 不判断用途     │
└─────────────────────────────────────────────────────┘
```

### 3.2 `page-object-generator` Skill 增强（automation-agent 现有 Skill）

```
现有 page-object-generator Skill (automation/) 新增 mode:

  mode: manual (默认)
    现有流程: TECH_ANALYSIS → 人工选择器 → Jinja2 模板 → PO .py

  mode: browser-use (🆕)
    🆕 1. BrowserUseDriver 页面观察 (NL驱动)
    🆕 2. 提取选择器 (CSS + XPath) 注入到模板
       3. Jinja2 模板渲染 → PO .py
       4. code-consistency-checker 合规检查

  降级: BrowserUse 失败或 code-consistency-checker 不通过
        → 降级到 manual mode，人工介入
```

### 3.3 `bu_heal` Fixture（conftest 独立钩子，不侵入 BasePage）

```
┌─────────────────────────────────────────────────────┐
│ Fixture: bu_heal                                    │
│ File: base/bu_heal_fixture.py                       │
│ Trigger: test teardown (pytest_runtest_makereport)  │
│         检测到 NoSuchElementException                │
├─────────────────────────────────────────────────────┤
│ Process:                                            │
│   1. 捕获测试失败 + 失败类型 = 选择器相关             │
│   2. 调用 aitest.bu_adapter.heal_locator()          │
│   3. BrowserUse NL 定位 → 尝试恢复操作               │
│   4. ✅ 成功 → 写 artifacts/heal_log.jsonl           │
│      ❌ 失败 → 写 heal_log 标记 failed               │
│                                                     │
│ 关键设计决策 (B1, B3, B4):                          │
│   - 不嵌入 BasePage.click()                         │
│   - 不自动修改 PO 源码                               │
│   - 不接 Event Bus                                  │
│   - 仅记录 JSONL 日志，供人工审核后手动应用           │
│                                                     │
│ Cost Control:                                       │
│   - max_heals_per_session: 3                        │
│   - max_cost_per_session: $0.05                     │
│   - 仅开发环境启用 (ENV=dev)                         │
│   - pytest marker 显式启用: @pytest.mark.bu_heal    │
└─────────────────────────────────────────────────────┘
```

---

## 4. 代码改动详情（修订版）

### 4.1 `aitest/bu_adapter.py`（核心适配器 — C2 修复）

```python
"""BrowserUse Skill Adapter — Skill 与 BrowserUseDriver 之间的桥接层

位置: aitest/bu_adapter.py (与 agent_runner.py 同级, C2 修复)
依赖: ZJSN_Test-master526/base/bu_driver.py

每个方法对应一个 Skill/Fixture 场景。
"""

class BrowserUseSkillAdapter:
    """BrowserUse 能力适配器 — Skill/Fixture 通过此类调用 BrowserUse"""

    def __init__(self, driver: BrowserUseDriver):
        self.bu = driver

    async def observe_page_structure(self, hash_route: str) -> dict:
        """page-observe Skill: 返回 {search_fields, buttons, columns, pagination}"""

    async def generate_po_suggestions(self, hash_route: str) -> dict:
        """page-object-generator (browser-use mode):
        返回 {class_name, locators: [{name, css, xpath, type}], imports}"""

    async def heal_locator(self, failed_locator: tuple,
                           description: str, page_url: str) -> dict:
        """bu_heal fixture: 返回 {success, suggested_locator, confidence}"""
```

### 4.2 `bu_heal_fixture.py`（自愈 Fixture — B1 修复）

```python
"""bu_heal fixture — 测试失败后 BrowserUse 自愈钩子

用法 (conftest.py):
    from base.bu_heal_fixture import bu_heal
    # pytest 自动发现 fixture

用法 (test):
    @pytest.mark.bu_heal
    def test_something(hazard_item_page_with_heal):
        ...

设计:
  - 不侵入 BasePage（B1 修复）
  - pytest_runtest_makereport 钩子在 teardown 阶段检测失败
  - 仅在选择器相关异常时触发自愈
  - 结果写 artifacts/heal_log.jsonl（B3: 不修改源码）
  - 不接 Event Bus（B4: 先积累数据）
"""

def pytest_runtest_makereport(item, call):
    """检测选择器失败 → 触发 BrowserUse 自愈记录"""
    if call.excinfo and _is_locator_failure(call.excinfo):
        # 异步安全: 在 fixture finalizer 中运行
        item._bu_heal_pending = True

@pytest.fixture
def bu_heal(request):
    """自愈 fixture: 注入到需要自愈保护的测试"""
    yield
    if getattr(request.node, '_bu_heal_pending', False):
        _run_heal_and_log(request.node)
```

### 4.3 `page-object-generator.md` 改动（B2 修复）

```markdown
# page-object-generator

## Modes

### mode: manual (默认)
现有流程，不变。

### mode: browser-use (🆕)
1. 调用 aitest.bu_adapter.generate_po_suggestions(hash_route)
2. 从返回的 locators 中筛选置信度 >70% 的条目
3. Jinja2 模板渲染 → Page Object .py
4. code-consistency-checker 合规检查
5. 不通过 → 降级到 manual mode

## 口语化路由
- "生成XX的PageObject" → mode=manual (默认)
- "用AI生成XX的PageObject" → mode=browser-use
```

---

## 5. 实施阶段（修订版，16 天）

```
Week 1-2             Week 3-4              Week 5-6
├────────┼──────────┼────────┼──────────┼────────┼────────┤
│ Step 1  │ Step 2   │ Step 3  │ Step 4    │ Step 5  │
│ 适配器   │ page-ob │ PO gen  │ bu_heal   │ 文档     │
│ +MiMo测试│ Serve   │ 增强    │ fixture   │ +门禁    │
│ 3天     │ 2天     │ 3天     │ 6天       │ 2天      │
└────────┴──────────┴────────┴──────────┴────────┴────────┘
```

### Step 1: 适配器 + MiMo 验证（3 天）

| # | 任务 | 产出 |
|---|------|------|
| 1.1 | 实现 `BrowserUseSkillAdapter`（`aitest/bu_adapter.py`） | 适配器 |
| 1.2 | MiMo tool calling 专项测试（验证 structured output） | 测试报告 |
| 1.3 | 3 个方法 smoke test | 测试通过 |

### Step 2: page-observe Skill（2 天）

| # | 任务 | 产出 |
|---|------|------|
| 2.1 | 写 `governance/skills/test-design/page-observe.md` | Skill 定义 |
| 2.2 | 注册到 `skill-registry.yaml` | 注册条目 |
| 2.3 | `test-design-agent` page-analysis 后处理接入 | agent-definitions.yaml 改动 |
| 2.4 | 端到端验证：page-analysis → page-observe → PAGE_STRUCTURE.json | 对比报告 |

### Step 3: page-object-generator 增强（3 天）

| # | 任务 | 产出 |
|---|------|------|
| 3.1 | 改 `page-object-generator.md`，增加 `mode: browser-use` | Skill 定义修订 |
| 3.2 | automation-agent Skill 执行逻辑适配（mode 参数传递） | runner 改动 |
| 3.3 | 端到端验证：hazard_item → browser-use mode → PO 骨架 | 对比报告 |

### Step 4: bu_heal fixture（6 天，已延长）

| # | 任务 | 产出 |
|---|------|------|
| 4.1 | 实现 `bu_heal_fixture.py`（pytest 钩子 + JSONL 日志） | fixture 文件 |
| 4.2 | 注入测试：故意改错 3 个选择器 → 验证自愈记录 | 测试报告 |
| 4.3 | 模块 conftest 集成（warehouse → equipment → tank） | conftest 改动 |
| 4.4 | heal_log.jsonl 累积 20+ 条记录 → 人工审核准确性 | 审核报告 |

### Step 5: 文档 + 门禁（2 天）

| # | 任务 | 产出 |
|---|------|------|
| 5.1 | 更新 CLAUDE.md 口语化入口 | 新路由 |
| 5.2 | `check_sop_gate.py` 新增 `--check-bu-imports` + `--check-bu-skills` | 门禁检查 |
| 5.3 | context/source-of-truth.md 更新 | 架构文档 |

---

## 6. 风险与缓解（修订版）

| 风险 | 概率 | 缓解 |
|------|------|------|
| BrowserUse LLM 调用失败 | 高 | 每次调用有 Selenium fallback；自愈仅记录不阻塞 |
| MiMo tool calling 不兼容 | 中 | Step 1.2 专项测试，失败则保留 Gemini/DeepSeek 备选 |
| 自愈 fixture 在 teardown 中异步死锁 | 中 | 独立线程跑 BrowserUse event loop；ENV=dev 隔离 |
| 生成的 PO 选择器不准确 | 中 | 强制 code-consistency-checker；置信度 <70% 自动丢弃 |
| Playwright 与 Selenium 双浏览器资源竞争 | 低 | 串行运行：Selenium 测试完成 → teardown → BrowserUse |

---

## 7. 成功指标

| KPI | 基线 | 目标 | 测量 |
|-----|------|------|------|
| PO 生成时间 | 2-4h (人工) | ≤ 5min (含审核) | 计时 |
| PO 生成可用率 | N/A | ≥ 60% 行数无需修改 | diff |
| 自愈建议准确率 | 0% | ≥ 50% (人工确认有效) | heal_log 审核 |
| 自愈 LLM 成本 | N/A | ≤ $0.05/次 | token 统计 |
| BasePage 改动行数 | - | **0 行** (B1 修订) | `git diff base/base_page.py` |
| 新增 Agent/SOP 节点 | 0 | **0** (无变更) | 架构审计 |

---

## 8. 相关文件索引

```
tech-research/
├── browser-use-investigation.md    # 技术调研
├── browser-use-project-plan.md     # 项目计划书
├── bu-embedding-plan.md            # 🆕 本文件 (v2.0 修订版)
├── ARCH_REVIEW.md                  # 🆕 架构评审报告
└── experiments/
    ├── phase1_results.md
    ├── validation_report.md
    ├── validation_results.json
    └── *.py                        # 实验脚本

aitest/
├── bu_adapter.py                   # 🆕 Skill 适配器 (C2 修复)
├── agents/
│   ├── agent_runner.py             # 现有
│   └── skill_executor.py           # 现有
├── graphs/
│   ├── sop_graph.py                # 现有 (不改)
│   └── state.py                    # 现有 (不改)
└── event_bus.py                    # 现有 (不改, B4)

ZJSN_Test-master526/base/
├── base_page.py                    # ✅ 不改 (B1)
├── bu_driver.py                    # ✅ 已有
└── bu_heal_fixture.py              # 🆕 自愈 fixture

governance/
├── agents/agent-definitions.yaml   # +1 Skill 引用 (page-observe)
├── skills/skill-registry.yaml      # +1 条目
└── skills/
    ├── test-design/page-observe.md # 🆕
    └── automation/page-object-generator.md  # +browser-use mode (B2)
```
