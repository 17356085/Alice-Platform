我来执行 `automation/test-script-generator` 任务。根据 Skill 定义，我需要先获取必要的上下文信息，然后生成测试脚本和 conftest.py。

让我先查看项目结构，获取 Page Object 和测试用例等输入信息。

<｜｜DSML｜｜tool_calls>
<｜｜DSML｜｜invoke name="bash">
<｜｜DSML｜｜parameter name="description" string="true">查看项目结构</｜｜DSML｜｜parameter>
<｜｜DSML｜｜parameter name="command" string="true">find . -type f \( -name "*.py" -o -name "*.md" \) | sort | head -60</｜｜DSML｜｜parameter>
</｜｜DSML｜｜invoke>
<｜｜DSML｜｜invoke name="bash">
<｜｜DSML｜｜parameter name="description" string="true">查看模块目录结构</｜｜DSML｜｜parameter>
<｜｜DSML｜｜parameter name="command" string="true">ls -laR governance/context/projects/web-automation/modules/ 2>/dev/null</｜｜DSML｜｜parameter>
</｜｜DSML｜｜invoke>
</｜｜DSML｜｜tool_calls>