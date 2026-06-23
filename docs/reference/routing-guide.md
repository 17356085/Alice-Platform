# 口语化路由完整参考

> 从 CLAUDE.md 移出以节省 token。CLAUDE.md 仅保留 3 条强制路由。

## 单 Agent 调用

| 你说 | AI 使用 | 说明 |
|------|--------|------|
| "看看XX页面有什么元素" | `/test-design-agent` | 仅页面分析 |
| "给XX页面设计测试用例" | `/test-design-agent` | 仅测试设计 |
| "这个按钮怎么写定位" | `/automation-agent` | 仅技术分析 |
| "生成XX的PageObject代码" | `/automation-agent` | 仅代码生成 |
| "写XX功能的自动化脚本" | `/automation-agent` | 仅代码生成 |
| "这段代码写得对不对" | `code-consistency-checker` | |
| "这个用例为什么挂了" | `/bug-analysis-agent` | |
| "一堆失败用例帮我分类" | `/bug-analysis-agent` (batch) | |
| "运行XX模块测试" | `/execution-agent` | 仅执行 |
| "生成测试报告/导出Excel" | `/report-agent` | |
| "沉淀经验/这个Bug别人也会遇到吗" | `/knowledge-agent` | |
| "初始化项目/更新上下文" | `/project-agent` | |
| "分析XX模块" | `/requirement-agent` | |
| "上次做到哪了" | `context-sync` | |

## Agent 斜杠命令

| 命令 | Agent | 用途 |
|------|-------|------|
| `/full-sop` | 全流程编排 | 端到端 SOP，8 Agent 串联 + 断点续跑 |
| `/project-agent` | 项目 Agent | 项目初始化、上下文管理 |
| `/requirement-agent` | 需求 Agent | 模块建模、需求分析 |
| `/test-design-agent` | 测试设计 Agent | 页面分析、风险建模、测试用例 |
| `/automation-agent` | 自动化 Agent | 技术分析、定位器、代码生成+合规检查 |
| `/execution-agent` | 执行 Agent | 测试执行、报告生成 |
| `/bug-analysis-agent` | Bug分析 Agent | 失败根因分析、CI诊断 |
| `/report-agent` | 报告 Agent | 测试总结、Excel导出 |
| `/knowledge-agent` | 知识 Agent | 知识提取、已知问题库维护 |
