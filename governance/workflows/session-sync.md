# Workflow: Session Sync

## 目标
在每次协作结束后，将新增事实、产物和待办同步到治理层。

## 输入
- 本轮会话内容
- 本轮新增分析
- 本轮新增脚本或配置
- 本轮待办

## 输出
- 上下文更新建议
- 新增产物记录
- 下一步动作清单

## 依赖 Skill
- context-sync

## 完成标准
- 稳定事实与临时产物被正确分流

## 上下文同步检查清单（每次会话结束必须逐项确认）

> ⚠️ 本 Workflow 本身就是同步机制，以下为执行 `context-sync` 时的检查清单。

| # | 检查项 | 目标 |
|---|--------|------|
| 1 | 本轮新增/修改了哪些文件？ | 完整清单，区分 context/ artifacts/ 代码 |
| 2 | 是否有新的事实需要写入 context/？ | 如新的页面元素、新的坑位、新的模块 |
| 3 | MODULE_CONTEXT.md 中的页面状态是否需要更新？ | ✅/🔄/⏳ 状态与实际进度一致 |
| 4 | 测试进度追踪是否需要更新？ | Phase 完成状态、用例数、自动化数 |
| 5 | 是否有新的 Bug 分析需要沉淀坑位？ | 调用 knowledge-extractor |
| 6 | 是否有新的自动化代码需要合规检查？ | 调用 code-consistency-checker |
| 7 | 下次会话的建议入口是什么？ | 明确的 Phase + 文件路径 |
| 8 | MODULE_INDEX.md 是否需要更新？ | 新模块注册 |

**执行方式**：
```
1. 调用 context-sync Skill，输入本轮变更摘要
2. 逐项确认上述 8 个检查项
3. 输出：①上下文更新建议 ②产物归档建议 ③下次会话入口
```






<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: workflow-check -->
## Dependency Check (2026-06-17 21:52)

- [OK] No deprecated skill references
- [OK] Validated 2026-06-17 21:52

> sync_progress.py
<!-- ⚠️ AUTO-GENERATED SECTION END: workflow-check -->