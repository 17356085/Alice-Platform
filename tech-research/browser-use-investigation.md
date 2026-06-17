# Browser-Use 技术调研：集成可行性分析

> 日期: 2026-06-17 | 版本: v1.0

---

## 1. Browser-Use 是什么

Browser-Use 是开源 Python 库（MIT License），让 LLM 驱动的 AI Agent 控制真实浏览器。底层基于 Playwright，上层用 LLM 做**观察→决策→行动**循环。

**核心架构**:
```
用户任务(NL) → Agent(LLM) → observe(DOM+截图) → decide → act(Playwright) → loop
```

**关键数据**:
- GitHub: 58K stars, 319 contributors, 9182 commits
- 最新版本: 0.12.9 (2026-05-26)
- Python >= 3.11
- 支持 Claude、GPT、Gemini、Ollama 等所有主流 LLM
- 专用模型 `ChatBrowserUse()` 号称 3-5x 快于通用模型

---

## 2. 现状架构分析

### 2.1 当前技术栈

| 层 | 技术 | 规模 |
|---|---|---|
| 浏览器引擎 | Selenium + ChromeDriver | 1 个 BaseDriver |
| Page Object | BasePage (1083 行) + ~80 个页面类 | ~80 文件 |
| 定位策略 | CSS_SELECTOR 优先, XPath 保底, JS 兜底 | 4 级降级 |
| 测试框架 | Pytest + Allure | ~80+ 测试文件 |
| 编排层 | LangGraph SOP Graph (8 Agent) | aitest/graphs/ |
| 治理层 | 24 Skills + RAG + Event Bus | governance/ |

### 2.2 当前痛点

1. **选择器脆弱**: UI 变化→选择器失效，Element Plus 2.x 动态 class (`data-v-xxx`) 加剧问题
2. **PO 编写成本高**: 每新增页面需手写 ~100-300 行定位器+方法
3. **Element Plus Teleport 问题**: 下拉框/弹窗渲染到 `body >` 下，Selenium `is_displayed()` 对 teleport 元素失效 (见 [AlarmConfigPage.py:6-9](../ZJSN_Test-master526/page/equipment_page/AlarmConfigPage.py#L6-L9))
4. **Vue 异步渲染**: 需要 `wait_vue_stable()` + `_wait_loading_gone()` + 多级 fallback click
5. **定制 UI 框架**: tank 模块使用非标准 UI，BasePage 通用定位器完全不可用（需独立 PO）
6. **维护债务**: 15-25% 脚本每月因 UI 变更而失效（行业数据，本项目中 AlarmConfigPage 已有 `@skip` 标记的方法）

### 2.3 现有优势（不宜替换的部分）

- **BasePage 企业级封装**: 4 级点击降级、JS 原生 setter、Element Plus 弹窗/Toast/分页的深度适配——这些都是针对被测系统专门优化的
- **Fixture 体系**: module-scope 浏览器复用 + 自动登录 + 侧边栏导航
- **SOP 编排**: LangGraph 驱动的 8 Agent 协作，已集成 RAG、Event Bus
- **执行速度**: Selenium 每条操作 ~100-200ms，适合 CI/CD 高频回归

---

## 3. Browser-Use vs Selenium 对比

| 维度 | 当前 (Selenium) | Browser-Use |
|---|---|---|
| **执行速度** | ~200ms/操作 | 2-5s/操作 (LLM 延迟) |
| **可靠性** | ~98% (脚本正确时) | 72-78% (WebVoyager 基准) |
| **维护成本** | 高 (选择器修复) | 低 (<5% prompt 需调整) |
| **编写成本** | 高 (手写定位器+方法) | 低 (自然语言描述) |
| **自愈能力** | 无 | 自动适应 UI 变化 |
| **LLM 成本** | $0 | $0.02-0.30/task |
| **确定性** | 100% 确定 | 非确定（LLM 决策） |
| **Vue/Element Plus** | 深度适配但需大量代码 | 视觉理解绕过 DOM 复杂性 |

---

## 4. 推荐集成策略：混合架构

Browser-Use **不是 Selenium 的替代品**，而是互补层。推荐三层架构：

```
┌──────────────────────────────────────────────┐
│ Layer 3: AI Agent (Browser-Use)              │
│ - 探索性测试、新页面快速验证                    │
│ - UI 大幅变更后的自愈回退                      │
│ - 自然语言驱动的临时任务                       │
├──────────────────────────────────────────────┤
│ Layer 2: SOP 编排 (LangGraph + 8 Agent)      │
│ - 不变：Agent 协作、治理、RAG                 │
│ - 新增：Browser-Use Agent 节点               │
├──────────────────────────────────────────────┤
│ Layer 1: 确定性回归 (Selenium + BasePage)     │
│ - CI/CD 高频回归                             │
│ - 核心业务流断言                              │
│ - 速度敏感的批量执行                          │
└──────────────────────────────────────────────┘
```

### 4.1 具体集成点

#### A. 新页面快速接入（最高 ROI）

当前流程: 诊断 DOM → 写 Page Object (~200行) → 写测试 (~100行) → debug 选择器
Browser-Use 流程: 写 NL 任务描述 → Agent 自动执行 → 从成功执行中提取选择器生成 PO

```python
# 示例：用 Browser-Use 探索新页面，自动生成 Page Object 骨架
from browser_use import Agent, Browser, ChatAnthropic

async def explore_page_and_generate_po(url: str, page_name: str):
    """探索页面 → 识别元素 → 生成 Page Object 代码"""
    browser = Browser()
    agent = Agent(
        task=f"""
        1. 导航到 {url}
        2. 识别页面上所有搜索条件（input/select/date-picker）
        3. 识别所有操作按钮（新增/查询/重置/导出）
        4. 识别表格列定义
        5. 对每个交互元素，记录其 CSS selector 和 XPath
        
        输出格式：Python dict，key=元素名，value={{"css": "...", "xpath": "...", "type": "input|select|button|..."}}
        """,
        llm=ChatAnthropic(model="claude-sonnet-4-6"),
        browser=browser,
    )
    result = await agent.run()
    # result → 自动生成 Page Object 类
    return generate_po_from_result(result, page_name)
```

**价值**: 将新页面 PO 编写从 2-4 小时降到 15-30 分钟。

#### B. 失败自愈（解决痛点 #1/#4/#5）

当前: 选择器失效 → 测试报错 → 人工诊断 DOM → 修复定位器
Browser-Use: 选择器失效 → fallback 到 AI Agent 用自然语言重试 → 记录新选择器

```python
# conftest.py 中新增：智能重试 fixture
import asyncio
from browser_use import Agent, Browser

async def ai_fallback_click(driver, element_description: str):
    """当 Selenium 选择器失败时，用 Browser-Use 自然语言定位并点击"""
    # 复用当前浏览器的 Playwright 连接
    browser = Browser(connect_to_existing=True)
    agent = Agent(
        task=f"找到'{element_description}'并点击",
        browser=browser,
    )
    await agent.run()
```

可集成到 BasePage.click() 的降级链中作为**第 5 级兜底**。

#### C. 探索性测试 Agent（新增能力）

当前 SOP 图中有 8 个 Agent，可新增第 9 个 `explorer-agent`：

```yaml
# governance/agents/explorer-agent.yaml
name: explorer-agent
description: 基于 Browser-Use 的页面探索 Agent
phase: exploration
llm: ChatAnthropic(model="claude-sonnet-4-6")
tool: browser-use
skills:
  - page-element-discovery
  - interaction-path-mapping
  - selector-generation
```

这个 Agent 自动遍历页面所有可交互元素，生成交互路径图，发现边界情况。

#### D. Tank 等定制 UI 模块（解决痛点 #5）

Tank 模块非标准 UI，BasePage 定位器不可用。Browser-Use 的视觉理解能力直接绕过 DOM 结构差异：

```python
# tank 模块可以完全用 NL 驱动
agent = Agent(
    task="""
    在罐区监控页面:
    1. 找到显示液位的区域
    2. 读取所有罐的液位数值
    3. 点击第一个罐查看详情
    4. 验证详情弹窗包含温度/压力/液位三个指标
    """,
    llm=ChatAnthropic(model="claude-sonnet-4-6"),
)
```

---

## 5. 成本分析

### 5.1 运行成本

| 场景 | 频率 | Browser-Use 月成本 |
|---|---|---|
| CI/CD 全量回归 (828 tests) | 每天 1 次 | $5-75/天 → **$150-2250/月** ❌ 不可接受 |
| 新页面 PO 生成 | 每周 2-3 页 | $0.06-0.90/周 → **$0.24-3.60/月** ✅ 可忽略 |
| 失败自愈 fallback | ~5% 测试失败时 | $0.10-0.75/次 → **$2-15/月** ✅ 可接受 |
| 探索性测试 | 每周 1 次全量 | $0.50-5/周 → **$2-20/月** ✅ 可接受 |

### 5.2 结论

- **全量回归用 Browser-Use**: 不可行，成本太高+速度太慢
- **辅助场景用 Browser-Use**: 月成本 $5-40，ROI 极高

---

## 6. 实施路线图

### Phase 1: 实验验证（1-2 周）

- [ ] 安装 `browser-use` + Playwright
- [ ] 选 1 个简单模块（如 hazard_item）用 Browser-Use 重写 2-3 个测试
- [ ] 对比：成功率 / 执行时间 / 编写时间 / 维护体验
- [ ] 选 1 个问题模块（如 tank 或 alarm_config 弹窗部分）验证自愈能力

### Phase 2: PO 自动生成工具（2-3 周）

- [ ] 开发 `po-generator` Skill：输入页面 URL → Browser-Use 探索 → 输出 Page Object 骨架
- [ ] 集成到 SOP 的 `project-agent` 阶段（module onboarding）
- [ ] 生成代码质量对比：人工 vs AI 生成的定位器准确率

### Phase 3: 失败自愈集成（3-4 周）

- [ ] BasePage.click() 增加第 5 级降级：Browser-Use AI fallback
- [ ] 自愈成功后自动更新定位器（写入 Page Object 文件）
- [ ] 自愈事件通过 Event Bus 通知 knowledge-agent 沉淀

### Phase 4: 探索性测试 Agent（4-6 周）

- [ ] 新增 `explorer-agent` 到 SOP 图
- [ ] 自动发现页面交互路径、边界条件
- [ ] 与 bug-analysis agent 联动：发现的异常 → 自动创建 Bug 记录

---

## 7. 风险与注意事项

| 风险 | 缓解 |
|---|---|
| **LLM 非确定性** 导致同一测试结果不一致 | 仅用于辅助场景；确定性回归保留 Selenium |
| **API 成本失控** | 设 `max_steps` 限制 + token 预算告警 |
| **Browser-Use 执行速度慢** (2-5s/step) | 不用于高频 CI；探索性任务可接受 |
| **登录态复用** | Browser-Use 支持 `Browser(connect_to_existing=True)` 复用当前 Playwright context |
| **与现有 Selenium 驱动共存** | 需要额外的 Playwright 浏览器实例或 CDP 连接 |
| **Browser-Use 本身不稳定** | 锁定版本；Phase 1 实验验证后再推广 |

---

## 8. 结论

**Browser-Use 值得引入，但定位是辅助层而非替代层。**

三个最高 ROI 的切入点:
1. **新页面 PO 自动生成** — 直接减少 80% 的 PO 编写时间
2. **失败自愈 fallback** — 解决选择器脆弱的根本痛点
3. **Tank 等非标准 UI 模块** — 绕过 DOM 差异，视觉理解直接驱动

不建议: 用 Browser-Use 替换现有 Selenium 回归测试套件。成本、速度、确定性都不匹配。

下一步: 选一个简单模块做 Phase 1 实验验证，拿到真实数据后再决定 Phase 2 投入。

---

## 参考

- [Browser-Use GitHub](https://github.com/browser-use/browser-use)
- [Browser-Use PyPI](https://pypi.org/project/browser-use/)
- [Browser-Use vs Selenium vs Playwright 对比](https://dev.to/alexcloudstar/ai-browser-agents-in-2026-stagehand-vs-browser-use-vs-playwright-38ob)
- [Browser-Use 实测: AI 完成 80% Web 自动化测试](https://www.cnblogs.com/easy-test/p/20148092)
- [Thoughtworks Technology Radar - Browser Use](https://www.thoughtworks.com/en-us/radar/languages-and-frameworks/browser-use)
