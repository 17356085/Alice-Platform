# Web Automation — 项目概况

> **父文件**: `PROJECT_CONTEXT.md`（索引）| **加载者**: 所有 Agent

## 项目目标
为 Web 端系统建立可长期维护的 AI 辅助测试开发协作体系。

## 当前技术栈

| 组件 | 版本 | 用途 |
|------|------|------|
| Python | 3.x | 测试脚本语言 |
| pytest | 7.4.4 | 测试框架 |
| Selenium | 4.15.2 | WebDriver 自动化 |
| Allure | 2.13.2 | 测试报告 |
| ChromeDriver | 与 Chrome 版本匹配 | 浏览器驱动 |
| Jenkins | — | CI/CD 调度 |

## 项目级稳定共性
- 自动化以模块为主组织测试资产
- 页面对象、测试脚本、测试数据、CI 报告是核心协作对象
- 适合从 Prompt 工程逐步演进为 Workflow / Skill 工程

---

## 已确认的模块 UI 框架差异

> 📌 不同模块可能使用不同 UI 框架。自动化代码生成前必须确认目标模块的技术栈。

| 模块 | UI 框架 | 组件特征 | 影响 |
|------|---------|----------|------|
| equipment / system-user / system-role 等 | **Element Plus** | el-table / el-dialog / el-select / el-button | 可使用 BasePage 通用定位器 |
| tank（储罐管理） | **自定义 UI 框架** | `btn btn-primary` / `data-table` / `stats-cards` / `filter-input` | BasePage 通用定位器不可用，需自定义 CSS 选择器 |

### 自定义 UI 框架模块的自动化注意事项

| 编号 | 差异点 | Element Plus 模块 | 自定义框架模块 | 应对 |
|------|--------|-------------------|---------------|------|
| UI-001 | 表格 | `el-table` → 固定 class | `table.data-table` → 原生 HTML table | CSS 定位器更简单但无内置分页/排序 |
| UI-002 | 按钮 | `el-button` | `btn btn-primary/success/info/default` | 通过 text() 匹配更稳定 |
| UI-003 | 输入框 | `el-input` 嵌套结构 | `input.filter-input` 单层 | 定位更直接 |
| UI-004 | 弹窗 | `el-dialog` 固定 class | 未确认（需补充） | 无法复用 BasePage.dialog 方法 |
| UI-005 | 统计卡片 | `el-statistic` | `stats-cards > .stat-card` | 自定义 class 体系 |
| UI-006 | 加载状态 | `el-loading-mask` 全局 | 无统一 loading 指示器 | 等待策略需依赖 DOM 变化 |
| UI-007 | 趋势图 | 无 | `<div class="chart-container">` + canvas/SVG | 断言图表内容需三级降级 |

---

## 上下文入口
- 模块上下文：`governance/context/projects/web-automation/modules/<module>/`
- 自动化项目：`ZJSN_Test-master526`
- CI 配置：`ZJSN_Test-master526/Jenkinsfile`
- 环境信息：`governance/context/environments.yaml`
- Element Plus 坑位：`governance/context/known-issues.yaml`
- 存量模块上下文（逐步废弃）：`TestIntern_library/02-项目文档/contexts/`
