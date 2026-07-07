我来观察 workflow 模块的 approval-todo 页面，提取可测元素。

首先，我需要查看当前环境和可能的页面 URL。

<minimax:tool_invocation name="shell" arguments={"command": "find /home/user -name \"*.md\" -path \"*/workflow/*\" 2>/dev/null | head -20; find /home/user -name \"config*\" -path \"*/workflow/*\" 2>/dev/null | head -10"} />