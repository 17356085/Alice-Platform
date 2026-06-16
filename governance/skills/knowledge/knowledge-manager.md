# Skill: knowledge-manager

## 目标
知识全生命周期管理。支持三种模式：
- **模式 A (extract)**：从 Bug 分析产物中提取通用坑位知识 → 增量更新 known-issues.yaml
- **模式 B (precipitate)**：测试周期结束时批量沉淀经验 → 更新 PROJECT_CONTEXT + known-issues + 进度追踪
- **模式 C (event-driven)**：监听 Event Bus 事件，自动触发知识沉淀 → 实现真正的"横向贯穿"

## 触发模式

| 模式 | 入口 | 说明 |
|------|------|------|
| `mode=extract` | 单个 Bug / Agent → 知识提取 | 原有模式 |
| `mode=precipitate` | 测试周期结束 → 批量沉淀 | 原有模式 |
| `mode=event-driven` | Event Bus `process` 输出 → 自动处理 | **新增** |

## 输入

| 模式 | 输入 | 触发时机 |
|------|------|----------|
| A: extract | `BUG_ANALYSIS.md`（单个或批量）+ known-issues.yaml | Bug 分析完成后 |
| B: precipitate | 本轮新增模块上下文 + 用例统计 + 高频Bug + 踩坑记录 | 测试周期结束 |
| C: event-driven | `python -m aitest.event_bus process` 输出 | full-sop Phase 8 自动调用 |

## 输出

| 模式 | 输出 |
|------|------|
| A | 坑位分类（🆕/🔗/⚪）+ known-issues.yaml 更新 + PROJECT_CONTEXT § 坑位清单更新 |
| B | PROJECT_CONTEXT 更新 + known-issues.yaml 更新 + 进度追踪更新 + 模块状态标记 |
| C | 事件处理摘要 + known-issues 增量更新 + occurrence_count 自动递增 |

## 规则（通用）

1. **去重优先**：沉淀前必须查询 known-issues.yaml，避免重复录入
2. **高频优先**：同一问题出现 ≥3 次 → 必须沉淀；1-2 次 → 视通用性决定
3. **唯一写入者**：只有 Knowledge Agent（通过本 Skill）能写入 known-issues.yaml 和 PROJECT_CONTEXT.md 坑位清单
4. **分类标准**：
   - Element Plus 组件坑位 → known-issues EP-XXX
   - 通用失败模式 → known-issues FP-XXX
   - 环境/数据问题 → known-issues ENV-XXX
   - 一次性偶发 → 不沉淀，仅归档 BUG_ANALYSIS

## 依赖

- `governance/context/known-issues.yaml`（已知问题库）
- `governance/context/projects/web-automation/PROJECT_CONTEXT.md`（§ Element Plus 已知坑位清单）
- `governance/skills/diagnosis/bug-analysis.md`（Bug 分析 Skill）
- `governance/skills/project/context-sync.md`（上下文同步 Skill）
- `governance/templates/bug-analysis.template.md`

## 边界

- ❌ 不分析 Bug 根因（那是 bug-analysis 的职责）
- ❌ 不生成测试报告（那是 report-generator 的职责）
- ❌ 不修改测试代码（那是 automation-agent 的职责）
- ✅ 可读取所有 Agent 的产出，但只有本 Skill 能写入知识库
- ✅ 模式 A 聚焦"单一事件→知识提取"，模式 B 聚焦"批量经验→知识更新"

---

## Prompt 模板

### 模式 A：Bug → 坑位提取（extract）

```text
分析以下 BUG_ANALYSIS.md，判断根因是否为可复用的通用坑位。

## 已知坑位清单（来自 known-issues.yaml）
{{粘贴 known-issues.yaml 中的 EP/FP/ENV 条目}}

## Bug 分析
{{粘贴 BUG_ANALYSIS.md 完整内容}}

## 任务
按以下流程判断：

### 1. 坑位分类
- 🆕 **新坑位**：根因是 Element Plus / Vue / Selenium / 浏览器行为特性，其他模块也可能遇到
- 🔗 **已知坑位**：根因已被已有编号覆盖
- ⚪ **一次性问题**：特定数据错误/环境配置/测试脚本逻辑错误

### 2. 如果是 🔗 已知坑位
输出：
```
🔗 关联已有坑位：XX-XXX（坑位名称）
已在 known-issues.yaml 中记录。
建议：更新 last_seen 和 occurrence_count
```

### 3. 如果是 🆕 新坑位
按类别分配编号：
- Element Plus 组件 → EP-012, EP-013, ...
- 失败模式 → FP-005, FP-006, ...
- 环境问题 → ENV-002, ENV-003, ...

输出 YAML 格式（可直接插入 known-issues.yaml）：
```yaml
- id: EP-012
  title: "{{简短名称}}"
  category: element-plus
  component: {{受影响的组件}}
  severity: {{high/medium/low}}
  reproduce_rate: {{百分比}}
  symptoms: ["{{现象1}}", "{{现象2}}"]
  root_cause: "{{根因分析}}"
  solution: "{{已验证的修复/规避方法}}"
  affected_modules: [{{模块列表}}]
  first_seen: {{日期}}
  last_seen: {{日期}}
  occurrence_count: 1
  status: active
```

### 4. 如果是 ⚪ 一次性问题
输出：
```
⚪ 不沉淀 — 原因：{{一次性数据错误 / 环境配置问题 / 测试脚本逻辑缺陷}}
```
```

### 模式 A-批量：批量 Bug → 坑位归类

```text
分析以下 N 个 BUG_ANALYSIS.md 文件，批量提取和归类。

## 已知坑位清单
{{粘贴 known-issues.yaml 完整内容}}

## Bug 列表
{{逐一粘贴或列出 BUG_ANALYSIS 文件路径}}

## 任务
1. 逐条分析每个 Bug 的根因
2. 按坑位归类（同坑位多次出现 = 高频，标注频次）
3. 输出汇总表：

| Bug编号 | 根因简述 | 分类 | 关联编号 | 建议 |
|---------|----------|------|----------|------|
| BUG-ALARM-001 | 空结果集loading不关闭 | 🔗 | EP-003 | 更新 occurrence_count |
| BUG-USER-002 | el-tree-select Teleport定位失效 | 🆕 | — | 建议新增 EP-012 |
| BUG-ROLE-001 | 测试数据冲突 | ⚪ | — | 更新测试数据种子 |

4. 新坑位按频次排序（高频→低频），便于确定沉淀优先级
5. 输出 "高频未沉淀坑位 Top 3" 列表
```

---

### 模式 B：周期沉淀（precipitate）

```text
本轮测试已完成，请更新项目知识库。

## 本轮新增
- 新增模块上下文：{{列表}}
- 新增测试用例：{{N}} 条
- 新增自动化用例：{{N}} 条
- 新发现的高频Bug：{{列表，含复现条件}}
- 新的踩坑经验：{{列表}}

## 任务
更新以下文件：

### 1. known-issues.yaml
- 高频 Bug（≥3次）→ 新增或更新条目
- 新发现的组件坑位 → 立即沉淀
- 更新已有条目的 occurrence_count / last_seen

### 2. PROJECT_CONTEXT.md
- § Element Plus 已知坑位清单：与 known-issues.yaml 同步
- § 已知坑位 → 新增/更新条目
- 「已确认的模块 UI 框架差异」：如有新发现

### 3. 模块状态更新
- 各模块 MODULE_CONTEXT.md 页面状态标记（✅/🔄/⏳）
- 测试进度追踪数据

### 4. 踩坑经验记录
每条经验必须包含四要素：
- 问题描述
- 原因分析
- 解决方案
- 预防措施
```

---

### 模式 C：事件驱动（event-driven）

```text
从 Event Bus 消费待处理事件，自动执行知识沉淀。

## 输入
运行 `python -m aitest.event_bus process` 获取待处理事件列表。

## 任务
对每条事件执行对应处理：

### AgentCompleted 事件处理
```
agent={{agent}} module={{module}} status={{status}} artifacts={{artifacts}}

检查该 Agent 的产出中是否有可沉淀的知识：
1. 读取该模块的 governance/context/projects/web-automation/modules/{{module}}/ 目录
2. 检查本轮新增/修改的文件（PAGE_CONTEXT.md, TECH_ANALYSIS.md, BUG_ANALYSIS.md）
3. 从中提取：
   - 新的 Element Plus 组件使用模式（如 el-cascader 级联选择器的特殊处理方式）
   - 新的失败模式（如特定组件的定位策略）
   - 新的等待策略（如自定义组件的显式等待方法）
4. 与 known-issues.yaml 现有条目去重
5. 如有新知识 → 添加到 known-issues.yaml
```

### BugClosed 事件处理
```
bug_id={{bug_id}} module={{module}} root_cause={{root_cause}} known_issue_id={{known_issue_id}}

1. 如果 known_issue_id 非空：
   - 更新 known-issues.yaml 中对应条目的 occurrence_count += 1
   - 更新 last_seen 为当前日期
2. 如果 known_issue_id 为空但 root_cause 是通用模式：
   - 评估是否应新建 known-issues 条目
   - 按分类标准分配编号（EP/FP/ENV）
```

### CycleEnd 事件处理
```
module={{module}} stats={{stats}}

1. 执行模式 B (precipitate) 的完整流程：
   - 汇总本轮所有产出
   - 更新 known-issues.yaml
   - 更新 PROJECT_CONTEXT.md 坑位清单
   - 更新模块状态标记
2. 输出沉淀摘要
```

### ContextUpdated 事件处理
```
file={{file}} changes={{changes}}

1. 检查被更新的文件的下游依赖
2. 如有下游文件需要同步 → 标记为待同步
3. 建议运行 context-sync Skill
```

## 约束
- 去重优先：写入前必须与 known-issues.yaml 现有条目比对
- 高频优先：同一问题出现 ≥3 次才沉淀（或在 BugClosed 中自动递增 occurrence_count）
- 事件处理完后标记 processed（由 event_bus CLI 自动完成）
```

---

## 检查清单

### 模式 A
- [ ] 每条 Bug 根因已分类（🆕 / 🔗 / ⚪）
- [ ] 新坑位检查了与已有条目的相似度（避免重复）
- [ ] 新坑位包含全部必填字段
- [ ] 编号延续现有序列（不跳号）
- [ ] 类别分配正确（EP/FP/ENV）
- [ ] 批量模式下输出了 Top N 高频未沉淀坑位

### 模式 B
- [ ] known-issues.yaml 高频 Bug 已新增/更新
- [ ] PROJECT_CONTEXT.md 坑位清单已同步
- [ ] 各模块 MODULE_CONTEXT 页面状态已更新
- [ ] 踩坑经验含四要素（问题/原因/方案/预防）
- [ ] 进度追踪数据已更新
- [ ] 去重检查已执行

## 产出物

| 模式 | 产出 |
|------|------|
| A | known-issues.yaml 更新 + PROJECT_CONTEXT § 坑位清单同步更新 |
| B | known-issues.yaml 更新 + PROJECT_CONTEXT 更新 + 模块状态更新 + 进度追踪更新 |
