# Browser-Use 集成项目计划书

> 版本: v1.0 | 日期: 2026-06-17 | 作者: AI Test Platform Team
>
> 前置文档: [Browser-Use 技术调研](browser-use-investigation.md)

---

## 1. 执行摘要

### 1.1 项目目标

将 Browser-Use（开源 AI 浏览器自动化框架）集成到 AITest Platform，作为现有 Selenium 测试体系的**智能辅助层**，解决三大核心痛点：

| 痛点 | 现状 | 目标 |
|------|------|------|
| Page Object 编写慢 | 新页面 PO 需 2-4 小时手写定位器 | 15-30 分钟自动生成 |
| 选择器脆弱 | UI 变更后需人工修复 | AI 自动定位 + 自愈 |
| 非标准 UI 模块难覆盖 | tank 等模块 BasePage 定位器不可用 | NL 驱动，绕过 DOM 差异 |

### 1.2 核心原则

- **不替换**现有 Selenium + BasePage + Pytest + SOP 体系
- **不增加**CI/CD 回归测试的 LLM 成本
- Browser-Use 定位为**辅助/加速层**：PO 生成、失败自愈、探索测试
- 开源自托管，不依赖 Browser-Use Cloud 付费服务

### 1.3 预期收益

| 指标 | 当前 | 目标 | 量化 |
|------|------|------|------|
| 新页面 PO 编写时间 | 2-4 h/页 | 0.25-0.5 h/页 | **减少 80%** |
| 选择器失效修复时间 | 0.5-2 h/次 | 自动自愈 (<1 min) | **减少 95%** |
| 非标准 UI 模块覆盖率 | 0% (tank) | 60%+ | **新增覆盖** |
| 新模块接入周期 | 3-5 天 | 1-2 天 | **缩短 50%** |

### 1.4 费用预估

| 项目 | 费用 |
|------|------|
| 软件许可 | **$0**（MIT 开源） |
| 基础设施 | **$0**（复用现有机器） |
| LLM API（Claude Sonnet 4.6 已有） | **$5-40/月**（辅助场景 token 消耗） |
| 人力 | **1 人 × 8-12 周**（兼职） |
| **总计** | **$0 新增固定成本 + $5-40/月浮动成本** |

---

## 2. 项目范围

### 2.1 范围内 (In Scope)

| 交付物 | 描述 | 优先级 |
|--------|------|--------|
| **Browser-Use Core 集成** | Playwright 驱动层 + BasePage 兼容适配 | P0 |
| **PO Generator Skill** | 输入 URL → 探索页面 → 输出 Page Object 骨架代码 | P0 |
| **Self-Healing Fallback** | BasePage 第 5 级降级：选择器失败→AI 自然语言定位 | P1 |
| **Explorer Agent** | SOP 图新增探索性测试 Agent，自动发现交互路径 | P1 |
| **Tank 模块 PO 生成** | 用 PO Generator 为 tank 模块生成首批 Page Object | P2 |
| **知识沉淀集成** | 自愈事件→Event Bus→knowledge-agent→RAG 更新 | P2 |

### 2.2 范围外 (Out of Scope)

- 用 Browser-Use 替换现有 Selenium 回归测试套件
- Browser-Use Cloud 订阅
- 小程序自动化（Browser-Use 不支持微信 WebView）
- CI/CD 管道中启用 AI fallback（仅本地开发/探索阶段使用）

---

## 3. 技术方案

### 3.1 总体架构

```
                    ┌──────────────────────────────────┐
                    │        AITest Platform            │
                    │                                   │
┌─────────┐         │  ┌────────────────────────────┐  │
│ 用户/CI  │────────▶│  │  SOP Graph (LangGraph)      │  │
└─────────┘         │  │  ┌──────┐ ┌──────┐ ┌──────┐ │  │
                    │  │  │project│ │design│ │exec  │ │  │
                    │  │  │agent  │ │agent │ │agent │ │  │
                    │  │  └──┬───┘ └──────┘ └──────┘ │  │
                    │  │     │                        │  │
                    │  │  ┌──┴─────────────────────┐  │  │
                    │  │  │  🆕 explorer-agent      │  │  │
                    │  │  │  (Browser-Use powered)  │  │  │
                    │  │  └────────────────────────┘  │  │
                    │  └────────────────────────────┘  │
                    │                                   │
                    │  ┌────────────────────────────┐  │
                    │  │  Test Execution Layer        │  │
                    │  │  ┌──────────┐ ┌───────────┐ │  │
                    │  │  │ Selenium │ │ 🆕 B-Use  │ │  │
                    │  │  │ (fast)   │ │ (fallback)│ │  │
                    │  │  └──────────┘ └───────────┘ │  │
                    │  └────────────────────────────┘  │
                    │                                   │
                    │  ┌────────────────────────────┐  │
                    │  │  🆕 PO Generator             │  │
                    │  │  (Browser-Use → .py 文件)    │  │
                    │  └────────────────────────────┘  │
                    └──────────────────────────────────┘
```

### 3.2 技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| AI 浏览器引擎 | Browser-Use 0.12.x | 开源 MIT，基于 Playwright，Claude 原生支持 |
| LLM | `ChatAnthropic(model="claude-sonnet-4-6")` | 复用现有 API key，成本可控 |
| 浏览器 | Playwright Chromium | Browser-Use 内置，与 Selenium Chrome 共存 |
| 集成方式 | Python asyncio wrapper | BasePage 同步→异步桥接，不破坏现有接口 |

### 3.3 关键设计决策

**D1: Selenium + Playwright 共存**

```
当前: Selenium Chrome (chrome:// 协议，chromedriver)
新增: Playwright Chromium (CDP 协议，独立浏览器实例)

方案: 两套驱动独立运行，通过 BasePage 统一接口层切换。
     Selenium 用于确定性回归（默认），
     Playwright/Browser-Use 用于 AI 辅助场景。
```

**D2: BasePage 降级链扩展**

```python
# base_page.py 现有 4 级降级
# 1. Selenium 原生 click()
# 2. 等待遮罩消失后重试
# 3. JS click()
# 4. MouseEvent 派发

# 🆕 第 5 级（可选启用）:
# 5. Browser-Use AI fallback（自然语言定位+点击）

def click(self, locator, timeout=None, ai_fallback=False):
    # ... 现有 4 级 ...
    if ai_fallback and self._bu_agent:
        return self._bu_click_fallback(locator_description)
```

**D3: PO Generator 输出格式**

生成的 Page Object 代码直接兼容现有 BasePage 规范，无缝插入 `page/` 目录。

---

## 4. 实施计划

### 4.1 时间线总览

```
Week 1  2  3  4  5  6  7  8  9  10 11 12
├──┴──┼──┴──┼──┴──┼──┴──┼──┴──┼──┴──┤
│ P1   │ P2      │ P3        │ P4        │
│ 实验  │ PO生成器  │ 自愈集成    │ 探索Agent  │
└──────┴─────────┴───────────┴───────────┘
                                  ↑ Go/No-Go 门禁
              ↑ Go/No-Go 门禁
```

### 4.2 Phase 1: 实验验证（Week 1-2）

**目标**: 验证 Browser-Use 在真实被测系统上的可行性。

| # | 任务 | 产出 | 工时 |
|---|------|------|------|
| 1.1 | 安装 browser-use + Playwright Chromium | 开发环境就绪 | 2h |
| 1.2 | 编写 `BrowserUseDriver` 基类（playwright 连接 + 登录态复用） | `base/bu_driver.py` | 4h |
| 1.3 | 选 `hazard_item` 模块，用 Browser-Use 写 3 个测试（页面加载 / 搜索 / 新增） | 实验脚本 | 4h |
| 1.4 | 选 `alarm_config` 弹窗部分（已知 Selenium 失败场景），验证自愈能力 | 对比数据 | 3h |
| 1.5 | 选 `tank_monitor` 页面，验证非标准 UI 的 NL 驱动 | 可行性报告 | 3h |
| 1.6 | 数据汇总：成功率 / 耗时 / 成本 / 编写时间对比 | 实验报告 | 2h |

**Go/No-Go 门禁**:
- ✅ Browser-Use 能成功导航到被测系统并完成登录
- ✅ 3 个 hazmat_item 用例成功率 ≥ 80%
- ✅ 单个任务平均 LLM cost < $0.05
- ❌ 任一条件不满足 → 暂停，评估替代方案

### 4.3 Phase 2: PO Generator（Week 3-5）

**目标**: 开发自动化工具，输入页面 URL/Hash，输出符合规范的 Page Object 代码。

| # | 任务 | 产出 | 工时 |
|---|------|------|------|
| 2.1 | 设计 PO Generator 的 prompt 工程（元素分类、选择器策略、代码模板） | Prompt spec | 3h |
| 2.2 | 实现 `POModel` 数据结构（页面元信息 + 元素列表 + 选择器 + XPath） | `base/po_model.py` | 3h |
| 2.3 | 实现 `POGenerator` 核心类（Browser-Use Agent → 结构化输出 → 代码生成） | `base/po_generator.py` | 6h |
| 2.4 | 实现 Jinja2 代码模板（匹配现有 Page Object 风格） | `templates/po_template.py.j2` | 2h |
| 2.5 | 对 5 个已稳定模块（hazard_item, spare_item, unit_manage, exam_manage, alarm_config）生成 PO，与现有人工版本对比 | 对比矩阵 | 4h |
| 2.6 | 基于对比结果调优 prompt + 模板 | 迭代优化 | 3h |
| 2.7 | 集成到 SOP `project-agent` 阶段——模块接入时自动生成首批 PO | 集成代码 | 3h |

**Go/No-Go 门禁**:
- ✅ 生成的 PO 代码可执行率 ≥ 70%（无需人工修改即可通过编译+运行）
- ✅ 人工修改量 ≤ 30%（按行数计）
- ✅ PO 生成时间 ≤ 30 分钟/页面
- ❌ 不满足 → 视为 prompt 优化工具，不作为完全自动化

### 4.4 Phase 3: Self-Healing Fallback（Week 6-8）

**目标**: 选择器失效时自动回退到 Browser-Use 自然语言定位。

| # | 任务 | 产出 | 工时 |
|---|------|------|------|
| 3.1 | 为每个 Page Object 元素建立 NL 描述注册表（`{locator: "搜索按钮"}`） | `base/locator_registry.py` | 3h |
| 3.2 | 实现 `SelfHealingMixin` ——捕获 NoSuchElementException → 调用 Browser-Use → 提取新选择器 → 可选更新 PO 文件 | `base/self_healing.py` | 6h |
| 3.3 | 在 BasePage 核心方法（click / input_text / get_text）中集成自愈开关 | 修改 `base_page.py` | 3h |
| 3.4 | 对 5 个已知脆弱点做注入测试（人工改错选择器→验证自愈） | 测试报告 | 3h |
| 3.5 | 实现自愈事件→Event Bus→knowledge-agent 的知识沉淀链路 | 集成代码 | 3h |
| 3.6 | 添加 `max_ai_fallbacks` 和 `ai_fallback_cost_budget` 成本控制 | 配置项 | 1h |

### 4.5 Phase 4: Explorer Agent（Week 9-12）

**目标**: 新增 SOP Agent 节点，自动探索页面交互路径，发现边界条件。

| # | 任务 | 产出 | 工时 |
|---|------|------|------|
| 4.1 | 设计 `explorer-agent` 的 prompt 体系（页面漫游→交互树→边界生成→可疑行为报告） | Agent YAML | 3h |
| 4.2 | 实现 Explorer Agent 核心（Browser-Use 驱动，输出结构化探索结果） | `aitest/graphs_dev/explorer.py` | 6h |
| 4.3 | 在 SOP Graph 中添加 `exploration` 节点（Phase 2.5，在 test-design 之后、automation 之前） | 图修改 | 3h |
| 4.4 | 与 bug-analysis agent 联动：探索发现异常→自动创建 Bug 记录 | 集成 | 3h |
| 4.5 | 端到端验证：选 1 个模块跑完整 SOP（含 explorer） | E2E 报告 | 3h |

---

## 5. 资源计划

### 5.1 人力

| 角色 | 人数 | 投入 | 职责 |
|------|------|------|------|
| 测试开发工程师 | 1 | 50% × 12 周 | 核心开发 + 集成 |
| 代码审查 | 0.25 | 按需 | PR review |

### 5.2 环境

| 资源 | 说明 |
|------|------|
| 开发机 | 现有 Windows 11 机器，16G RAM+ |
| Chrome / Chromium | 已安装 Playwright Chromium |
| LLM API Key | 已有 ANTHROPIC_API_KEY |
| Python 3.11+ | 需确认版本（browser-use 要求 ≥3.11） |

### 5.3 依赖

| 依赖 | 版本 | 状态 |
|------|------|------|
| `browser-use` | 0.12.x | 需安装 |
| `playwright` | latest | 需安装 |
| `anthropic` | 已有 | ✅ |
| `langgraph` | 已有 | ✅ |
| `pytest` | 已有 | ✅ |

---

## 6. 风险管理

| # | 风险 | 概率 | 影响 | 缓解措施 |
|---|------|------|------|----------|
| R1 | Browser-Use 无法处理被测系统的登录流程（验证码/SSO） | 中 | 高 | Phase 1 第一优先级验证；备选：复用现有 Selenium 登录后传 cookie 给 Playwright |
| R2 | Element Plus 2.x Teleport 组件导致 Browser-Use 视觉定位失败 | 中 | 中 | Phase 1 用 alarm_config 弹窗场景实测 |
| R3 | LLM token 成本超出预估 | 低 | 中 | `max_steps` 硬限制 + 月度 budget 告警 + 成本监控 dashboard |
| R4 | Browser-Use API 大版本 breaking change | 中 | 低 | 锁定 0.12.x 版本；Phase 3 后评估升级 |
| R5 | 生成的 PO 代码质量不稳定 | 高 | 中 | Phase 2 设 Go/No-Go 门禁；不达标则降级为"人工辅助工具"而非全自动 |
| R6 | Playwright 和 Selenium 浏览器实例资源竞争 | 低 | 低 | 不同时运行；Selenium 回归用 Chrome，B-Use 用独立 Chromium |

---

## 7. 成功指标

| KPI | 测量方法 | 基线 | 目标 |
|-----|----------|------|------|
| PO 生成时间 | 从 URL 输入到可执行 PO 文件 | 2-4 h (人工) | ≤ 30 min |
| 生成代码可用率 | 不需人工修改的行数占比 | N/A | ≥ 70% |
| 选择器自愈成功率 | NoSuchElementException → 自动恢复 | 0% (当前无自愈) | ≥ 60% |
| 自愈 LLM 成本 | 单次自愈 token 消耗 | N/A | ≤ $0.05 |
| Explorer 发现有效 Bug 数 | 探索结果中经确认的真实 Bug | N/A | ≥ 1/模块 |
| 非标准 UI 模块覆盖率 | tank 模块有 Page Object 的页面数 | 0 | ≥ 3 页面 |

---

## 8. 审批与门禁

| 门禁 | 时间点 | 决策标准 | 决策人 |
|------|--------|----------|--------|
| **G1: 实验启动** | Week 0 | 计划书评审通过 | Tech Lead |
| **G2: Phase 1→2** | Week 2 末 | 实验报告通过 Go/No-Go 条件 | Tech Lead |
| **G3: Phase 2→3** | Week 5 末 | PO Generator 通过 Go/No-Go 条件 | Tech Lead |
| **G4: 项目结项** | Week 12 末 | 全部 P0/P1 交付物验收 | Tech Lead + QA Lead |

---

## 9. 附录

### A. 相关文档

- [技术调研报告](browser-use-investigation.md)
- [AITest Platform 架构文档](../governance/docs/architecture/)
- [SOP Graph 设计](../aitest/graphs/sop_graph.py)
- [BasePage 实现](../ZJSN_Test-master526/base/base_page.py)

### B. 参考资源

- [Browser-Use GitHub](https://github.com/browser-use/browser-use)
- [Browser-Use 文档](https://docs.browser-use.com/)
- [Browser-Use vs Playwright 对比 (2026)](https://dev.to/alexcloudstar/ai-browser-agents-in-2026-stagehand-vs-browser-use-vs-playwright-38ob)
