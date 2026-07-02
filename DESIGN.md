# Alice v3 — Product Experience Design

> Architecture Freeze v1.0 已结束。Alice 从 Architecture Builder 切换为 Product Engineer。
> 目标：从"能运行"变成"好用、好看、好理解"。

---

## 总原则

```
ExecutionService、Run、RunEvent、EventBus、RunEventConsumer Protocol 为 Frozen Core。

除非存在明确 Bug，不允许修改核心执行链。

新增能力默认实现为 RunEvent Consumer、Artifact Producer 或 UI 能力。

目标不再是 Architecture Evolution，而是 Product Experience。

优先级：用户体验 > 可观测性 > 易理解 > 新架构

两个真实需求催生一个抽象。没有用户价值，不增加抽象。
```

---

## Frozen Core（不可修改）

| 模块 | 文件 | 状态 |
|------|------|------|
| ExecutionService | `aitest/platform/execution_service.py` | ❄️ Frozen |
| Run | `aitest/platform/run.py` | ❄️ Frozen |
| RunEvent | `aitest/platform/run_event.py` | ❄️ Frozen |
| EventBus | `aitest/platform/event_bus.py` | ❄️ Frozen |
| RunEventConsumer | `aitest/platform/consumer.py` | ❄️ Frozen |
| RunStore | `aitest/platform/run_store.py` | ❄️ Frozen |
| ExecutionRequest | `aitest/platform/execution_request.py` | ❄️ Frozen |

## 允许的扩展点

```
✅ 新 Consumer（实现 RunEventConsumer protocol）
✅ 新 UI（React 组件，shadcn/ui）
✅ 新 Inspector / Viewer / Panel
✅ 新 Report / Metrics / Visualization
✅ 新 Artifact Producer
✅ 新 API 端点（读取 Run + RunEvent）
```

## 禁止的操作

```
❌ 新 Manager / Coordinator / Engine
❌ 新 BaseClass / AbstractFactory
❌ EventBus v2 / RunEvent v2
❌ Repository Pattern 包装
❌ 新生命周期 / 新状态机
❌ 修改 ExecutionService 核心流程
```

---

## Epic 1: Run Inspector ⭐⭐⭐⭐⭐

### 现状

Run 是数据库对象。查看需调 API + 手动拼信息。

### 目标

Run → 像 Chrome DevTools 一样可浏览。

### 功能清单

#### 1.1 Run Header
- Run ID、状态徽章、持续时间
- 触发人、Workspace、Agent、Module
- Token 用量 + 成本（实时刷新）
- 一键 Cancel / Timeout

#### 1.2 Run Timeline
- 所有 RunEvent 按时间轴排列
- 颜色编码：execution（蓝）/ artifact（绿）/ error（红）/ lifecycle（灰）
- 点击事件展开详情

#### 1.3 Artifacts Tab
- 该 Run 产生的所有 Artifact
- 缩略图预览（screenshot）、代码块（html/trace）、JSON 树（console/network）
- 下载 + 复制路径

#### 1.4 Metrics Tab
- 总耗时、各 Phase 耗时
- Agent 调用次数、成功率
- Token 分布（prompt vs completion）
- 成本拆解

#### 1.5 Agent Calls Tab
- 每次 Agent 调用的 prompt/response
- Tool call 序列（展开查看参数+结果）
- 每步耗时

#### 1.6 Logs Tab
- 结构化日志流
- 按级别过滤（DEBUG/INFO/WARN/ERROR）
- 搜索 + 高亮

#### 1.7 Execution Tree
- 嵌套的 Phase → Step → Action 树
- 每节点：状态图标 + 耗时 + 展开箭头
- 失败节点红色高亮 + 错误摘要

### 技术约束

- **禁止修改 ExecutionService**
- **全部基于 Run + RunEvent 读取**
- 后端：新 API 端点聚合 Run + RunEvent 数据
- 前端：新 `RunInspector.tsx` 组件，路由 `/runs/:runId`

### 已有基础

| 能力 | 位置 | 复用方式 |
|------|------|----------|
| Run 数据模型 | `aitest/platform/run.py` | 直接读取 |
| RunEvent 流 | `aitest/platform/run_event.py` | 按 run_id 过滤 |
| Timeline 构建 | `aitest/platform/timeline.py` | `build_timeline(run_id)` 复用 |
| Debug 端点 | `aitest/server/api/execution.py` → `/runs/{run_id}/debug` | 扩展 |
| Timeline 端点 | `aitest/server/api/execution.py` → `/runs/{run_id}/timeline` | 扩展 |

---

## Epic 2: Artifact Center ⭐⭐⭐⭐⭐

### 现状

Artifact 存储存在但不便浏览。无预览、无 Diff、无元数据浏览。

### 目标

```
Run → Artifacts → Preview（不用下载，直接看）
```

### 功能清单

#### 2.1 Artifact Browser
- 按 Run / Module / Type 过滤
- 网格视图（缩略图）+ 列表视图（文件名+元数据）
- 搜索 + 排序

#### 2.2 Preview（内嵌查看器）
| Artifact 类型 | 查看器 |
|--------------|--------|
| `screenshot` | 图片查看器（放大/缩小/旋转） |
| `html` | 渲染的 iframe + 源码切换 |
| `trace` | JSON 树 + 搜索 |
| `console` | 虚拟终端回放 |
| `network` | HAR 查看器（类似 Chrome Network 标签） |
| `report` | Markdown/HTML 渲染 |
| `replay` | 步骤回放播放器 |

#### 2.3 Diff
- 同 Module 两次 Run 的 Artifact 对比
- Screenshot：并排 + 叠加对比
- HTML：unified diff
- Console/Network：表格 diff

#### 2.4 Metadata Panel
- 来源 Run
- 来源 Step / Agent
- 产生时间
- 文件大小
- MIME 类型
- Timeline 定位（点击跳转到 Run Inspector 对应时间点）

#### 2.5 Download
- 单文件下载
- 批量下载（zip）
- 复制路径

### 技术约束

- 后端：Artifact 索引 + 查询 API
- 前端：`ArtifactCenter.tsx`，路由 `/artifacts`

### 已有基础

| 能力 | 位置 | 复用方式 |
|------|------|----------|
| ArtifactStore | `aitest/platform/artifacts.py` | 读取 + 扩展查询 |
| Artifact Lineage | `aitest/platform/artifact_lineage.py` | `get_lineage()` 复用 |
| Artifacts API | `aitest/server/api/kpi.py` → `/artifacts/{project_id}` | 扩展 |
| Lineage API | `aitest/server/api/kpi.py` → `/artifacts/lineage/{project_id}` | 扩展 |

---

## Epic 3: Timeline Experience ⭐⭐⭐⭐⭐

### 现状

Timeline 更像日志列表，不是时间轴体验。

### 目标

像 GitHub Actions 或 Chrome Performance 的时间轴。

### 功能清单

#### 3.1 泳道时间轴
```
12:01:03  ──── Browser Started ────
12:01:05       ├── Navigate (1.2s)
12:01:07       ├── Login (0.8s)
12:01:08       │   ├── Fill username (0.3s)
12:01:08       │   ├── Fill password (0.2s)
12:01:09       │   └── Click submit (0.3s)
12:01:10       └── Screenshot (0.5s)
12:01:11  ──── Assertion Passed ────
```

#### 3.2 事件详情面板
点击事件展开：
- Duration
- 关联 Artifacts
- LLM 调用（Prompt + Response + Token）
- Screenshot（该时刻）
- 元数据

#### 3.3 缩放 + 导航
- 时间轴缩放（放大/缩小）
- 跳到上一个/下一个事件
- 跳到第一个/最后一个错误
- 键盘快捷键（← → 导航，Space 展开）

#### 3.4 对比模式
- 两次 Run 的时间轴并排对比
- 差异高亮（慢了 30% 的步骤标黄，失败步骤标红）

#### 3.5 Replay 模式
- 时间轴播放按钮
- 按时间顺序自动推进
- 每步显示对应 Screenshot + Console 输出
- 可调速（1x / 2x / 4x / 0.5x）

### 技术约束

- 后端：Timeline API 扩展（添加 Artifact 关联 + LLM 调用详情）
- 前端：`RunTimeline.tsx`，嵌入 Run Inspector 或独立路由

### 已有基础

| 能力 | 位置 | 复用方式 |
|------|------|----------|
| Timeline 构建 | `aitest/platform/timeline.py` | `build_timeline()` + `timeline_summary()` 复用 |
| Replay 端点 | `aitest/server/api/kpi.py` → `/timeline/replay/{run_id}` | 扩展 |
| Timeline 端点 | `aitest/server/api/kpi.py` → `/timeline/{project_id}` | 扩展 |

---

## Epic 4: AI Report ⭐⭐⭐⭐⭐

### 现状

Run 结束后无自动总结。用户需手动翻看。

### 目标

每次 Run 自动生成 Execution Summary。

### 示例输出

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Execution Summary — Run #a7f3b2c1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Modules      8      Duration     18.4s
Agents       13     Success      100%
Artifacts    23     Cost         $0.47

Issues (2)
🟡 登录耗时较高 (3.2s) → 建议缓存 Session
🟡 模块 Order 耗时占 43% → 推荐并行执行

Suggestions (3)
💡 页面列表页可跳过重复导航检查
💡 Agent "reviewer" 的 prompt 可精简 30%
💡 模块 Equipment 下次可启用 parallel 模式

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 功能清单

#### 4.1 自动生成（Run 结束时触发）
- Consumer 监听 `run.completed` / `run.failed` 事件
- 聚合 Run + RunEvent + Metrics 数据
- 调用 LLM 生成自然语言总结
- 持久化为 Artifact（type: `report`）

#### 4.2 报告内容
- 执行概览（模块数、Agent 数、耗时、成功率）
- Artifact 清单
- 异常检测（超时步骤、高耗时步骤、失败重试）
- 优化建议（基于历史对比 + 模式识别）
- 成本分析

#### 4.3 报告查看
- Run Inspector 内嵌 Report Tab
- 独立报告页（可分享链接）
- Markdown 渲染 + 导出（PDF/Markdown）

#### 4.4 历史趋势
- 多次 Run 的成功率趋势
- 耗时趋势
- 成本趋势
- 常见失败模式统计

### 技术约束

- 实现为 `ReportConsumer`（RunEventConsumer protocol）
- **不修改 ExecutionService**：在 `run.completed` 事件上触发
- LLM 调用使用现有 `reliable_provider`
- 报告持久化为 Artifact

### 已有基础

| 能力 | 位置 | 复用方式 |
|------|------|----------|
| MetricsConsumer | `aitest/platform/hooks/metrics_consumer.py` | 参考模式 |
| ArtifactStore | `aitest/platform/artifacts.py` | 写入 report |
| ReliableProvider | `aitest/llm/reliable_provider.py` | LLM 调用 |
| KPI API | `aitest/server/api/kpi.py` | 趋势数据已有 |

---

## 不做的事

```
❌ 新 Manager / Coordinator / Engine
❌ 新 BaseClass / AbstractFactory
❌ EventBus v2 / RunEvent v2
❌ Repository Pattern
❌ 新生命周期 / 新状态机
❌ Plugin SDK v2
❌ Remote Worker（等体验成熟后再做）
❌ Distributed Scheduler（等体验成熟后再做）
❌ Cloud Deployment（等体验成熟后再做）
```

---

## 优先级矩阵

```
        高影响
          │
  Epic 1  │  Epic 2
  Run     │  Artifact
  Inspector│  Center
──────────┼────────── 低 effort
  Epic 4  │  Epic 3
  AI      │  Timeline
  Report  │  Experience
          │
        低影响
```

全做。顺序：1 → 2 → 3 → 4。

---

## 设计系统参考

> 以下为 Alice 视觉设计令牌，UI 开发时引用。

### 主题色

| Token | 值 | 用途 |
|-------|-----|------|
| `alice-primary` | `#5A4F8A` | 主色调（Midnight Iris） |
| `alice-gold` | `#B89A60` | 强调色（Gold accent） |
| `alice-bg` | `#ECEAEF` | 亮色背景 |
| `alice-bg-dark` | `#100F1A` | 暗色背景 |
| `aoko-primary` | `#1E90FF` | Aoko 主题主色 |
| `soujuurou-primary` | `#8B4513` | Soujuurou 主题主色 |

### 组件规范

- 组件库：shadcn/ui (React 18 + Tailwind 3 + Radix)
- 图标：Lucide React
- 图表：Recharts
- 时间轴：自定义 Canvas/SVG 实现
- 代码高亮：Shiki

---

## 成功标准

1. 点击一个 Run → 3 秒内理解发生了什么
2. Artifact 不需要下载 → 浏览器内直接看
3. Run 结束后 → 自动收到 AI 总结报告
4. 时间轴 → 像看视频回放一样理解执行过程
5. 每次 Run 的每个步骤 → 都可追溯、可解释

---

> Alice 已完成 Runtime Architecture。
> 下一阶段不是证明架构还能继续扩展。
> 而是证明这套架构能够提供优秀的 DX 和 UX。
> 任何新功能，都必须让用户能够"看到"或"感受到"价值。
