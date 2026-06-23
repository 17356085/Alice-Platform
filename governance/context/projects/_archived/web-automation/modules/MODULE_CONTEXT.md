我来执行 `requirements/module-modeling` 任务。首先，我需要了解当前可用的模块信息。

让我先扫描项目结构，看看有哪些模块可用。

<tool_calls>
<tool_call id="scan_modules">
<parameters>
<command>ls</command>
<path>ZJSN_Test-master526/page</path>
</parameters>
</tool_call>
<tool_call id="scan_scripts">
<parameters>
<command>ls</command>
<path>ZJSN_Test-master526/script</path>
</parameters>
</tool_call>
<tool_call id="read_project_context">
<parameters>
<command>cat</command>
<path>governance/context/projects/web-automation/PROJECT_CONTEXT.md</path>
</parameters>
</tool_call>
</tool_calls>