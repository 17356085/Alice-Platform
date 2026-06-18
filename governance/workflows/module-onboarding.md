# Workflow: Module Onboarding

## 目标
为新模块建立完整的上下文基础：模块建模 → 需求分析 → 页面分析 → 风险建模。

## 适用对象
- 新模块初次接入治理层
- 已有模块补充页面级分析

## 输入
- PROJECT_CONTEXT.md
- 模块名称与入口 URL
- 页面截图 / HTML 源码
- PRD / 原型图 / 产品说明（如有）
- 已有旧资产（contexts 或 testcases）

## 阶段
1. 模块边界确认 — 确定子页面清单、权限要求、模块定位
2. 需求分析（如有 PRD）— 提取业务规则、测试范围、需求风险
3. 逐个页面分析 — 截图/HTML 分析 → PAGE_CONTEXT
4. 风险建模 — 6 维度风险识别 → RISK_MODEL

## 产物
- context/projects/*/modules/*/MODULE_CONTEXT.md
- context/projects/*/modules/*/pages/*/PAGE_CONTEXT.md
- context/projects/*/modules/*/pages/*/PAGE_ELEMENT_POSITION.md
- context/projects/*/modules/*/pages/*/RISK_MODEL.md

## 依赖 Skill
- module-modeling
- requirement-analysis
- page-analysis
- risk-modeling

## 完成标准
- 模块的页面清单完整、状态明确
- 每个核心页面有 PAGE_CONTEXT 和 RISK_MODEL
- 定位器至少覆盖 A/B 两级
- 风险点标注了 P0/P1/P2

## 上下文同步（必须执行）

> ⚠️ 完成上述阶段后，**必须**执行以下同步动作。不执行将导致上下文树与实际情况不一致。

| 动作 | 目标文件 | 具体操作 |
|------|----------|----------|
| 1. 更新模块索引 | `MODULE_INDEX.md` | 若为新模块，新增一行模块记录 |
| 2. 更新模块上下文 | `MODULE_CONTEXT.md` | 将已完成页面的状态标记为 ✅，补充页面路由和元素概要 |
| 3. 注册页面目录 | `context/projects/web-automation/modules/<module>/pages/` | 确保每个新页面有独立目录 |
| 4. 更新进度追踪 | `测试进度追踪.md` | 标记该模块 Phase 0.5 / 1 / 1.5 完成 |
| 5. 记录产物 | `MIGRATION_MAP.md` | 新增的 PAGE_CONTEXT/RISK_MODEL 记录到映射表 |

**执行方式**：调用 `context-sync` Skill，输入本轮新增文件清单。

> 强制门禁：完成本 Workflow 后，只有在 `MODULE_INDEX.md`、`MODULE_CONTEXT.md`、`PAGE_CONTEXT.md`、`PAGE_ELEMENT_POSITION.md`、`RISK_MODEL.md` 都已同步到位时，才算真正完成模块入场。只完成页面分析但未同步上下文，视为未完成。






<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: workflow-check -->
## Dependency Check (2026-06-17 21:52)

- [OK] No deprecated skill references
- [OK] Validated 2026-06-17 21:52

> sync_progress.py
<!-- ⚠️ AUTO-GENERATED SECTION END: workflow-check -->