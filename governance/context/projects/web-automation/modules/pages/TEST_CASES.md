我来执行 `test-design/testcase-design` 任务。根据 Skill 定义，我需要：

1. **输入**：MODULE_CONTEXT、PAGE_CONTEXT、BUSINESS_SCENARIOS.md（来自 risk-modeling）、需求说明、风险信息、历史缺陷
2. **输出**：TEST_DESIGN.md、TEST_CASES.md、自动化优先级建议

让我先获取当前项目的所有必要上下文信息。

<｜｜DSML｜｜tool_calls>
<｜｜DSML｜｜invoke name="bash">
<｜｜DSML｜｜parameter name="description" string="true">扫描项目目录结构</｜｜DSML｜｜parameter>
<｜｜DSML｜｜parameter name="command" string="true">find . -type f -name "*.md" | sort</｜｜DSML｜｜parameter>
</｜｜DSML｜｜invoke>
<｜｜DSML｜｜invoke name="bash">
<｜｜DSML｜｜parameter name="description" string="true">查看模块目录详情</｜｜DSML｜｜parameter>
<｜｜DSML｜｜parameter name="command" string="true">ls -laR governance/context/projects/web-automation/modules/ 2>/dev/null | head -50</｜｜DSML｜｜parameter>
</｜｜DSML｜｜invoke>
</｜｜DSML｜｜tool_calls>