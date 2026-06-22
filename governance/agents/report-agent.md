# /report-agent — 报告 Agent (v2.1)
> 本文件已精简。完整 Agent 定义（含 SOP 门禁、核心能力、报告结构、执行流程）见 `.claude/skills/report-agent/SKILL.md`。
> 架构全景见 `governance/agents/README.md`。

## v2.1 变更：Excel 生成统一化

**旧流程**: Agent 读取 excel-exporter Skill 模板 → 编写临时 Python 脚本 → 执行脚本 → 删除脚本
**新流程**: Agent 收集 TEST_CASES.md + 元数据 → 调用 `excel_renderer.render_page_report()` → 完成

Agent 角色从"代码生成器"变为"数据准备器"。格式 100% 由共享库 `ZJSN_Test-master526/tools/report/excel_renderer.py` 保证。

### 调用示例

```python
from tools.report.excel_renderer import render_page_report

render_page_report(
    module="equipment",
    module_cn="设备管理",
    page_key="alarm-config",
    page_cn="设备报警配置",
    testcases_md_path="governance/kpi/testcases/equipment/testcases-equipment-alarm-config.md",
)
```

### 输出
- 每页面一个文件: `governance/kpi/reports/{module}/测试报告-{module}-{page}.xlsx`
- 11 列固定格式，含分组标题 `"功能测试 (N条)"` + 🆕/⚠️ 标注
- 覆盖式，无日期后缀










<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: agent-meta -->
## Auto-Metadata (2026-06-18 10:54)

| Agent | Phase | Skills | Source |
|-------|-------|--------|--------|
| report-agent | 8~9 | 2 (reporting/report-generator, execution/excel-exporter) | agent-definitions.yaml |

> synced by sync_progress.py
<!-- ⚠️ AUTO-GENERATED SECTION END: agent-meta -->