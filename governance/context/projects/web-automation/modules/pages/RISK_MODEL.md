好的，我来执行 `test-design/risk-modeling` 任务，基于页面上下文和模块上下文进行风险建模。

首先，我需要找到页面上下文文件。让我扫描项目的结构。

<｜｜DSML｜｜tool_calls>
<｜｜DSML｜｜invoke name="bash">
<｜｜DSML｜｜parameter name="description" string="true">查找页面上下文文件</｜｜DSML｜｜parameter>
<｜｜DSML｜｜parameter name="command" string="true">find . -name "PAGE_CONTEXT*" -o -name "page-context*" 2>/dev/null | head -30</｜｜DSML｜｜parameter>
</｜｜DSML｜｜invoke>
<｜｜DSML｜｜invoke name="bash">
<｜｜DSML｜｜parameter name="description" string="true">查找模块上下文文件</｜｜DSML｜｜parameter>
<｜｜DSML｜｜parameter name="command" string="true">find . -name "MODULE_CONTEXT*" -o -name "module-context*" 2>/dev/null | head -30</｜｜DSML｜｜parameter>
</｜｜DSML｜｜invoke>
<｜｜DSML｜｜invoke name="bash">
<｜｜DSML｜｜parameter name="description" string="true">查找风险模型模板</｜｜DSML｜｜parameter>
<｜｜DSML｜｜parameter name="command" string="true">find . -name "risk-model.template*" 2>/dev/null | head -10</｜｜DSML｜｜parameter>
</｜｜DSML｜｜invoke>
</｜｜DSML｜｜tool_calls>