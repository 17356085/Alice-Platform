# Workflow: Automation Failure Closure

## 目标
对自动化失败进行标准化分析，形成可执行的修复闭环。

## 输入
- Jenkins 日志
- Allure 结果
- 截图 / 录屏
- 页面对象 / 测试脚本上下文

## 阶段
1. 失败归类
2. 复现条件提取
3. 根因假设
4. 证据核对
5. 修复建议
6. 回归范围确认

## 输出
- Bug 分析报告
- 根因分类
- 修复建议
- 回归建议

## 依赖 Skill
- bug-analysis
- ci-pipeline-analysis
- knowledge-extractor（新增：Bug 根因 → 通用坑位知识沉淀）

## 完成标准
- 分析结果可直接交付给开发或自动化维护者

## 上下文同步（必须执行）

> ⚠️ Bug 分析完成后，**必须**执行以下同步。

| 动作 | 目标文件 | 具体操作 |
|------|----------|----------|
| 1. 坑位知识沉淀 | `PROJECT_CONTEXT.md` | 调用 `knowledge-extractor` 判断根因是否为通用坑位。若是新坑位 → 追加 EP-XXX 到坑位清单；若已知 → 关联已有 EP 编号 |
| 2. Bug 分析归档 | `BUG_ANALYSIS.md` | 若沉淀为新坑位，在分析报告中添加"根因已沉淀为 EP-XXX"引用 |
| 3. 更新回归范围 | `TEST_CASES.md` | 若 Bug 揭示未覆盖的测试场景，新增用例 |
| 4. 更新进度追踪 | `测试进度追踪.md` | 记录 Bug 数量、严重程度、修复状态 |

**执行方式**：调用 `knowledge-extractor` Skill → 调用 `context-sync` Skill。
