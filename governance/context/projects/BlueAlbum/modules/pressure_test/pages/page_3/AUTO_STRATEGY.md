为了制定 `AUTO_STRATEGY.md`，我需要先补齐以下关键输入：

### 1. 页面技术分析（TECH_ANALYSIS.md）

请提供 `pressure_test/page_3` 页面的：

- **HTML 源码**：在浏览器中按 F12 → 复制 `<body>` 内完整 HTML（或整个文档）
- **页面截图**（可选）：帮助判断 Element Plus 组件状态

收到后我会生成 `TECH_ANALYSIS.md`，包含：
- 组件识别（表格/弹窗/分页等）
- A/B/C 三级定位器表
- Vue 异步等待策略
- 自动化风险点

### 2. 测试用例清单（TEST_CASES.md）

请粘贴 `TEST_CASES.md` 中所有用例的 **用例编号**、**标题** 和 **优先级**，或者直接上传文件。

### 3. 已有 BasePage 能力清单

从 `AUTOMATION_ARCHITECTURE.md` 中摘录 BasePage 已提供的公共方法（如 `wait_table_render`、`fill_input` 等）。

---

这些材料齐全后，我会立刻按模板输出 `AUTO_STRATEGY.md`，覆盖：
- 自动化覆盖矩阵（P0 必须自动化，标注风险）
- PageObject 拆分方案
- 公共组件复用分析
- 等待策略建议
- 完整的 ROI 计算

请先提供页面源码或截图，我们立即开始。