# Workflow: API Test Design

## 目标
基于 API 文档或 Network 抓包设计接口测试方案，可选生成自动化脚本。

## 适用对象
- 新增接口需要测试覆盖
- 已有 UI 自动化需要补充接口层验证

## 输入
- API 文档 / 浏览器 Network 抓包
- PAGE_CONTEXT.md（接口依赖关系）
- 自动化架构中的 requests 封装和 Token 处理

## 阶段
1. 接口清单整理 — 所有端点、方法、参数、触发时机
2. 参数边界设计 — 必填缺失、类型错误、超长、分页边界
3. 安全与权限设计 — Token 校验、权限校验、SQL 注入、XSS
4. 异常场景设计 — 资源不存在、重复提交、并发
5. （可选）生成接口测试脚本

## 产物
- context/projects/*/modules/*/API_TEST_DESIGN.md
- （可选）接口测试 pytest 脚本

## 依赖 Skill
- api-testing

## 完成标准
- 覆盖 5 个测试维度（参数边界 / Token / 权限 / 异常 / 安全）
- 每个接口至少一个正向用例和一个异常用例

## 上下文同步（必须执行）

> ⚠️ 接口测试设计完成后，**必须**执行以下同步。

| 动作 | 目标文件 | 具体操作 |
|------|----------|----------|
| 1. 更新页面上下文 | `PAGE_CONTEXT.md` | 补充接口依赖信息（端点/方法/触发时机） |
| 2. 关联测试设计 | `TEST_DESIGN.md` | 若接口测试揭示了新的 UI 测试场景，追加到测试设计 |
| 3. 更新进度追踪 | `测试进度追踪.md` | 标记 Phase 6 完成 |

**执行方式**：调用 `context-sync` Skill。






<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: workflow-check -->
## Dependency Check (2026-06-17 21:52)

- [OK] No deprecated skill references
- [OK] Validated 2026-06-17 21:52

> sync_progress.py
<!-- ⚠️ AUTO-GENERATED SECTION END: workflow-check -->