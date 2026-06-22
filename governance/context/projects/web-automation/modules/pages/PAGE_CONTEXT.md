我来执行 `test-design/page-analysis` 任务。首先，我需要了解当前项目的结构，特别是模块和页面信息。

让我先扫描项目结构。

<｜｜DSML｜｜tool_calls>
<｜｜DSML｜｜invoke name="bash">
<｜｜DSML｜｜parameter name="description" string="true">扫描项目 Page Object 目录结构</｜｜DSML｜｜parameter>
<｜｜DSML｜｜parameter name="command" string="true">ls page/ 2>/dev/null || echo "page/ 目录不存在"</｜｜DSML｜｜parameter>
</｜｜DSML｜｜invoke>
<｜｜DSML｜｜invoke name="bash">
<｜｜DSML｜｜parameter name="description" string="true">扫描项目测试脚本目录结构</｜｜DSML｜｜parameter>
<｜｜DSML｜｜parameter name="command" string="true">ls script/ 2>/dev/null || echo "script/ 目录不存在"</｜｜DSML｜｜parameter>
</｜｜DSML｜｜invoke>
<｜｜DSML｜｜invoke name="bash">
<｜｜DSML｜｜parameter name="description" string="true">扫描治理上下文目录</｜｜DSML｜｜parameter>
<｜｜DSML｜｜parameter name="command" string="true">ls governance/context/projects/web-automation/modules/ 2>/dev/null || echo "modules 目录不存在"</｜｜DSML｜｜parameter>
</｜｜DSML｜｜invoke>
</｜｜DSML｜｜tool_calls>