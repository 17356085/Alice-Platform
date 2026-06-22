## 开始执行: automation/auto-strategy

我将基于您提供的测试用例和技术分析，制定自动化覆盖策略、PageObject 拆分方案和ROI分析。

**请提供以下输入信息：**

1. **TEST_CASES.md** - 测试用例（用例编号、标题、优先级、步骤）
2. **TECH_ANALYSIS.md** - 技术分析（定位器设计、页面元素分析）
3. **模块名称**（如 equipment、personnel、warehouse、tank 等）
4. **页面名称**（如 列表页、新增弹窗、详情页等）
5. **已有 BasePage 能力清单**（可选，如不提供我将使用标准 BasePage API）

在等待您提供信息的同时，我先加载项目上下文。

<｜｜DSML｜｜tool_calls>
<｜｜DSML｜｜invoke name="read">
<｜｜DSML｜｜parameter name="filePath" string="true">governance/context/projects/web-automation/project-profile.md</｜｜DSML｜｜parameter>
</｜｜DSML｜｜invoke>
<｜｜DSML｜｜invoke name="read">
<｜｜DSML｜｜parameter name="filePath" string="true">governance/context/projects/web-automation/base-api-reference.md</｜｜DSML｜｜parameter>
</｜｜DSML｜｜invoke>
<｜｜DSML｜｜invoke name="read">
<｜｜DSML｜｜parameter name="filePath" string="true">governance/context/projects/web-automation/coding-standards.md</｜｜DSML｜｜parameter>
</｜｜DSML｜｜invoke>
<｜｜DSML｜｜invoke name="read">
<｜｜DSML｜｜parameter name="filePath" string="true">templates/auto-strategy.template.md</｜｜DSML｜｜parameter>
</｜｜DSML｜｜invoke>
</｜｜DSML｜｜tool_calls>