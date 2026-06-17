# Skill: plan/progress-tracker

### 目标
对比 PROJECT_PLAN.md 和当前产物，输出进度报告 PROGRESS_REPORT.md，识别阻塞项和偏离。

### 输入
- `PROJECT_PLAN.md` — 原计划
- 当前产物目录（检查哪些文件已生成）

### 输出
- `PROGRESS_REPORT.md`：含完成率、阻塞项、偏离预警

### 规则
- 基于实际文件存在性判断完成（非猜测）
- 阻塞项需标注：阻塞原因、影响任务、建议措施
- 偏离 >30% 预估时发出预警

### 依赖
- plan/create-project-plan

### 边界
- 不修改计划
- 不编写代码
- 不重新分配任务

---

## Prompt 模板

```text
你是一个技术项目经理。请对比项目计划和实际产出，生成进度报告。

## 项目计划
{{PROJECT_PLAN}}

## 实际产物目录
```
{{ARTIFACT_LIST}}
```

## 任务
1. 逐任务检查完成状态（文件是否存在且非空）
2. 计算整体完成率
3. 标记阻塞任务（依赖未完成导致后续无法启动）
4. 检测偏离（实际 vs 计划）

## 输出
```markdown
# 进度报告 — {{DATE}}

## 总览
- 完成: X/Y (Z%)
- 阻塞: N 个任务
- 状态: 🟢正常 / 🟡有偏离 / 🔴严重阻塞

## 任务状态
| ID | 标题 | 状态 | 产物 | 备注 |
|----|------|------|------|------|
| task-1 | ... | ✅完成 | file.md | |
| task-2 | ... | 🔴阻塞 | - | 依赖 task-1 的 API 契约未产出 |

## 阻塞项
1. **task-2 阻塞**: 原因... 影响 task-3, task-4. 建议: ...

## 偏离预警
(仅当偏离 >30% 时填写)
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | plan | synced 2026-06-17 16:53

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->