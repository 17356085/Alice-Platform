# SOP 门禁检查模板 (L2 — Agent 层)

> 本模板定义了所有 Agent 启动时执行的 L2 门禁检查。每个 Agent 的 SKILL.md 引用此模板。
> L1 门禁由 `full-sop.workflow.js` 中的 `assertGate()` 执行。L3 门禁由 `check_sop_gate.py` 执行。

## 执行指令

```
1. 提取 module 参数（若用户未提供，必须询问）
2. 运行门禁脚本：
   python ZJSN_Test-master526/tools/check_sop_gate.py --module <module> --agent <agent-name> [--page <page>] --json
3. 检查返回的 blocked 字段：
   - blocked: true → 拒绝执行，输出阻断信息（见下方映射表）
   - blocked: false → 门禁通过，继续执行
```

## Agent → 前置 Phase → 阻断信息映射

| Agent | 前置 Phase | 阻断时提示 |
|-------|-----------|-----------|
| project-agent | 无（始终允许） | — |
| requirement-agent | Phase 0 | ⛔ 缺失 PROJECT_CONTEXT.md / MODULE_INDEX.md → 先执行 `/project-agent` 或 `/full-sop mode=full` |
| test-design-agent | Phase 0.5 | ⛔ 缺失 MODULE_CONTEXT.md → 先执行 `/requirement-agent` 或 `/full-sop mode=from-requirement` |
| automation-agent | Phase 2.5 | ⛔ 缺失 PAGE_CONTEXT.md / TEST_CASES.md → 先执行 `/test-design-agent` 或 `/full-sop mode=from-test-design` |
| execution-agent | Phase 4 | ⛔ 缺失 PageObject .py / test_*.py → 先执行 `/automation-agent` 或 `/full-sop mode=from-automation` |
| bug-analysis-agent | Phase 4.5+ | ⛔ allure-results/ 为空或不存在 → 先执行 `/execution-agent` |
| report-agent | Phase 4.5+ | ⛔ allure-results/ 为空或不存在 → 先执行 `/execution-agent` |
| knowledge-agent | Phase 0 | ⛔ 缺失 PROJECT_CONTEXT.md → 先执行 `/project-agent` |

## 特殊说明

- **automation-agent fix 模式**: `mode=fix` 时无需 `--page` 参数，门禁检查模块级代码存在性
- **knowledge-agent**: 横向贯穿 Agent，门禁较轻（仅验证 PROJECT_CONTEXT 存在）
