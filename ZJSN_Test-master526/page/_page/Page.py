我来重新生成 `AlarmConfigPage.py`，确保继承 `BasePage` 并通过所有自检。

<｜｜DSML｜｜tool_calls>
<｜｜DSML｜｜invoke name="read_file">
<｜｜DSML｜｜parameter name="description" string="true">读取模块上下文配置</｜｜DSML｜｜parameter>
<｜｜DSML｜｜parameter name="path" string="true">governance/context/projects/web-automation/modules/equipment/MODULE_CONTEXT.md</｜｜DSML｜｜parameter>
</｜｜DSML｜｜invoke>
<｜｜DSML｜｜invoke name="read_file">
<｜｜DSML｜｜parameter name="description" string="true">读取页面上下文配置</｜｜DSML｜｜parameter>
<｜｜DSML｜｜parameter name="path" string="true">governance/context/projects/web-automation/modules/equipment/PAGE_CONTEXT.md</｜｜DSML｜｜parameter>
</｜｜DSML｜｜invoke>
<｜｜DSML｜｜invoke name="read_file">
<｜｜DSML｜｜parameter name="description" string="true">读取技术分析文档</｜｜DSML｜｜parameter>
<｜｜DSML｜｜parameter name="path" string="true">governance/context/projects/web-automation/modules/equipment/TECH_ANALYSIS.md</｜｜DSML｜｜parameter>
</｜｜DSML｜｜invoke>
</｜｜DSML｜｜tool_calls>