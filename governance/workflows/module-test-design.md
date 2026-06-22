# Workflow: Module Test Design

## 目标
围绕具体模块或页面，输出标准化测试设计与自动化边界建议。

## 输入
- MODULE_CONTEXT
- PAGE_CONTEXT
- 风险信息
- 业务规则
- 已有缺陷或历史脚本

## 阶段
1. 模块边界确认
2. 页面行为分析
3. 风险拆分
4. 场景设计
5. 自动化策略判断
6. 产出测试设计与用例

## 输出
- TEST_DESIGN.md
- TEST_CASES.md
- AUTO_STRATEGY.md

## 依赖 Skill
- testcase-design
- project-context-manager

## 完成标准
- 可直接进入评审或自动化实现

## 上下文同步（必须执行）

> ⚠️ 完成测试设计后，**必须**执行以下同步。

| 动作 | 目标文件 | 具体操作 |
|------|----------|----------|
| 1. 更新模块上下文 | `MODULE_CONTEXT.md` | 标记该页面 Phase 2 / 2.5 完成 |
| 2. 关联风险覆盖 | `RISK_MODEL.md` | 确认每个 P0 风险有对应 TEST_DESIGN 场景 |
| 3. 更新进度追踪 | `测试进度追踪.md` | 标记 Phase 2 完成，记录用例数量 |
| 4. 标注自动化建议 | `TEST_CASES.md` | 每个用例标注 ✅🔄❌ 自动化状态 |

**执行方式**：调用 `context-sync` Skill。










<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: workflow-check -->
## Dependency Check (2026-06-18 10:54)

- [OK] No deprecated skill references
- [OK] Validated 2026-06-18 10:54

> sync_progress.py
<!-- ⚠️ AUTO-GENERATED SECTION END: workflow-check -->