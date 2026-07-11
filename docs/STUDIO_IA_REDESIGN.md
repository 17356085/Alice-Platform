# Studio IA 重组设计文档

> **任务**: P2-6/P7-3 Studio IA 重组  
> **目标**: 将 19 个平铺 Views 重组为 5-resource 模型（Projects/Runs/Quality/Registry/Assets）  
> **设计时间**: 2026-07-11  
> **状态**: ✅ 路由与导航已实施（2026-07-11）；保留现有视图文件的惰性加载，物理目录迁移作为后续无功能变更整理。

---

## 📊 当前状态分析

### 现有 19 个 Views（平铺结构）

```
aitest/web/src/views/
├── DashboardView.tsx              # 仪表盘
├── ProjectOverviewView.tsx        # 项目概览
├── ExecutionView.tsx              # 执行面板
├── RunInspectorView.tsx           # Run 详情
├── AgentDetailView.tsx            # Agent 详情
├── AgentTerminalView.tsx          # Agent 终端
├── TimelineView.tsx               # 时间线
├── KanbanView.tsx                 # 看板
├── GapDiscoveryView.tsx           # Gap 发现
├── ReportsView.tsx                # 报告
├── ArtifactsView.tsx              # 构件
├── KnowledgeView.tsx              # 知识库
├── KnowledgeGraphView.tsx         # 知识图谱
├── ObservabilityView.tsx          # 可观测性
├── SettingsView.tsx               # 全局设置
├── ProjectSettingsView.tsx        # 项目设置
├── StrategyPlannerView.tsx        # 策略规划
├── IntelligenceChatView.tsx       # AI 助手
├── OnboardingWizardView.tsx       # 引导向导
└── (未完成: WorkflowBuilderView.tsx)
```

**问题**:
- 导航结构扁平，无层级关系
- 全局功能与项目功能混在一起
- 缺少上下文感知（当前在哪个项目？）
- 难以扩展（新功能往哪里放？）

---

## 🎯 目标架构：5-Resource 模型

### 核心概念

将 Studio 分为两个主要层级：

1. **Global Context（全局上下文）**  
   - 跨项目的资源和设置
   - 顶级导航入口

2. **Project Context（项目上下文）**  
   - 项目内的资源和操作
   - 二级导航（项目选中后显示）

### 5 个核心资源

| Resource | 中文名 | 职责 |
|----------|--------|------|
| **Projects** | 项目 | 项目列表、创建、切换 |
| **Runs** | 运行 | 执行历史、状态查询 |
| **Quality** | 质量 | 测试报告、Gap 分析 |
| **Registry** | 注册中心 | Agent/Workflow/Provider 管理 |
| **Assets** | 资产 | 构件、知识库、Agent 详情 |

---

## 🗂️ 新导航结构

### 一级导航（Global）

```
┌─────────────────────────────────────┐
│  Studio                             │
├─────────────────────────────────────┤
│  📂 Projects         ← 项目列表      │
│  🏃 Runs (Global)    ← 全局运行历史  │
│  📊 Evaluations      ← 全局质量评估  │
│  📦 Registry         ← 注册中心      │
│  ⚙️  Settings        ← 全局设置      │
└─────────────────────────────────────┘
```

**路由**:
- `/projects` → ProjectsView
- `/runs` → GlobalRunsView
- `/evaluations` → EvaluationsView
- `/registry` → RegistryView
- `/settings` → SettingsView

### 二级导航（Project Context）

选中项目后，显示项目内导航：

```
┌─────────────────────────────────────┐
│  Project: web-automation            │
├─────────────────────────────────────┤
│  📊 Overview         ← 项目概览      │
│  🔨 Build            ← 构建资源      │
│  ▶️  Run             ← 执行资源      │
│  ✅ Quality          ← 质量资源      │
│  📦 Assets           ← 资产资源      │
└─────────────────────────────────────┘
```

**路由**:
- `/projects/:projectId/overview` → ProjectOverviewView
- `/projects/:projectId/build` → BuildView（包含 Workflow/Strategy）
- `/projects/:projectId/run` → RunView（包含 Execution/Kanban）
- `/projects/:projectId/quality` → QualityView（包含 Gap/Reports）
- `/projects/:projectId/assets` → AssetsView（包含 Agent/Artifacts/Knowledge）

---

## 📐 详细设计

### 1. Global Views（全局视图）

#### ProjectsView（新增）
- **路由**: `/projects`
- **功能**:
  - 项目列表（卡片视图 + 表格视图）
  - 创建新项目（按钮 → Onboarding）
  - 项目搜索、筛选、排序
  - 最近访问项目（快速切换）
- **组件**:
  ```tsx
  ProjectsView/
  ├── ProjectCard.tsx       # 项目卡片
  ├── ProjectTable.tsx      # 项目表格
  ├── CreateProjectButton.tsx
  └── ProjectFilters.tsx
  ```

#### GlobalRunsView（新增）
- **路由**: `/runs`
- **功能**:
  - 所有项目的 Run 历史
  - 高级筛选（项目、状态、时间、Agent）
  - 批量操作（对比、导出）
  - 分页（50/页）
- **复用**: 当前 RunInspectorView 的列表部分

#### EvaluationsView（新增）
- **路由**: `/evaluations`
- **功能**:
  - 全局质量报告
  - 跨项目对比
  - 趋势分析
- **复用**: 当前 ReportsView + GapDiscoveryView（聚合视图）

#### RegistryView（新增）
- **路由**: `/registry`
- **功能**:
  - Agent 注册表（列表 + 版本管理）
  - Workflow 模板库
  - Provider 配置
  - Skill 市场（未来）
- **标签页**:
  - Agents
  - Workflows
  - Providers

#### SettingsView（已有，移动）
- **路由**: `/settings`
- **功能**: 全局设置（当前功能保持不变）

---

### 2. Project Views（项目视图）

#### Overview（概览）
- **路由**: `/projects/:projectId/overview`
- **功能**:
  - 项目摘要（模块数、覆盖率、最近 Run）
  - 最近活动时间线
  - 快速操作（Run SOP、查看报告）
- **合并**:
  - DashboardView（项目仪表盘）
  - ProjectOverviewView（项目概览）
  - TimelineView（时间线，作为组件嵌入）

#### Build（构建）
- **路由**: `/projects/:projectId/build`
- **功能**:
  - Workflow 编辑器
  - 策略规划器
  - 测试设计工具（未来）
- **标签页**:
  - Workflows → WorkflowBuilderView
  - Strategy → StrategyPlannerView

#### Run（执行）
- **路由**: `/projects/:projectId/run`
- **功能**:
  - 执行面板（启动 SOP、查看进度）
  - Run 历史（项目内）
  - 看板视图（SOP 阶段）
- **标签页**:
  - Execute → ExecutionView
  - History → RunInspectorView（项目内筛选）
  - Kanban → KanbanView

#### Quality（质量）
- **路由**: `/projects/:projectId/quality`
- **功能**:
  - Gap 发现
  - 测试报告
  - 质量趋势
- **标签页**:
  - Gap Discovery → GapDiscoveryView
  - Reports → ReportsView

#### Assets（资产）
- **路由**: `/projects/:projectId/assets`
- **功能**:
  - Agent 详情（项目专属）
  - 构件管理（测试脚本、截图、日志）
  - 知识库（项目文档）
  - 知识图谱
- **标签页**:
  - Agents → AgentDetailView + AgentTerminalView
  - Artifacts → ArtifactsView
  - Knowledge → KnowledgeView
  - Graph → KnowledgeGraphView

---

### 3. 横向功能（Cross-cutting）

这些功能不属于导航层级，作为独立入口：

#### IntelligenceChatView（AI 助手）
- **位置**: 全局悬浮按钮（右下角）
- **功能**: 随时可唤起的 AI 对话
- **路由**: 无（Modal/Drawer）

#### OnboardingWizardView（引导向导）
- **位置**: 首次进入或创建项目时触发
- **功能**: 项目初始化引导
- **路由**: `/onboarding/:sessionId`

#### ObservabilityView（可观测性）
- **位置**: 全局设置 → Observability 子页面
- **功能**: 系统监控（开发/运维）
- **路由**: `/settings/observability`

#### ProjectSettingsView（项目设置）
- **位置**: 项目内右上角设置按钮
- **功能**: 项目级配置
- **路由**: `/projects/:projectId/settings`

---

## 🗺️ 完整路由表

### Global Routes

| 路由 | View | 说明 |
|------|------|------|
| `/` | Redirect → `/projects` | 默认首页 |
| `/projects` | ProjectsView | 项目列表 |
| `/runs` | GlobalRunsView | 全局运行历史 |
| `/evaluations` | EvaluationsView | 全局质量评估 |
| `/registry` | RegistryView | 注册中心 |
| `/settings` | SettingsView | 全局设置 |
| `/settings/observability` | ObservabilityView | 可观测性 |
| `/onboarding/:sessionId` | OnboardingWizardView | 引导向导 |

### Project Routes

| 路由 | View | 说明 |
|------|------|------|
| `/projects/:projectId` | Redirect → `overview` | 项目默认页 |
| `/projects/:projectId/overview` | OverviewView | 项目概览 |
| `/projects/:projectId/build` | BuildView | 构建资源 |
| `/projects/:projectId/build/workflows` | WorkflowBuilderView | Workflow 编辑器 |
| `/projects/:projectId/build/strategy` | StrategyPlannerView | 策略规划 |
| `/projects/:projectId/run` | RunView | 执行资源 |
| `/projects/:projectId/run/execute` | ExecutionView | 执行面板 |
| `/projects/:projectId/run/history` | RunInspectorView | Run 历史 |
| `/projects/:projectId/run/kanban` | KanbanView | 看板 |
| `/projects/:projectId/quality` | QualityView | 质量资源 |
| `/projects/:projectId/quality/gaps` | GapDiscoveryView | Gap 发现 |
| `/projects/:projectId/quality/reports` | ReportsView | 报告 |
| `/projects/:projectId/assets` | AssetsView | 资产资源 |
| `/projects/:projectId/assets/agents` | AgentDetailView | Agent 详情 |
| `/projects/:projectId/assets/agents/:agentId/terminal` | AgentTerminalView | Agent 终端 |
| `/projects/:projectId/assets/artifacts` | ArtifactsView | 构件 |
| `/projects/:projectId/assets/knowledge` | KnowledgeView | 知识库 |
| `/projects/:projectId/assets/graph` | KnowledgeGraphView | 知识图谱 |
| `/projects/:projectId/settings` | ProjectSettingsView | 项目设置 |

---

## 🧩 组件架构

### Layout 组件

```tsx
// src/layouts/GlobalLayout.tsx
<GlobalLayout>
  <GlobalSidebar />  {/* Projects/Runs/Evaluations/Registry/Settings */}
  <Outlet />         {/* Global Views */}
</GlobalLayout>

// src/layouts/ProjectLayout.tsx
<ProjectLayout projectId={projectId}>
  <ProjectSidebar />  {/* Overview/Build/Run/Quality/Assets */}
  <Outlet />          {/* Project Views */}
</ProjectLayout>
```

### Sidebar 重构

```tsx
// src/components/SidebarNav.tsx（当前）
// → 拆分为两个组件

// src/components/GlobalSidebar.tsx
const GLOBAL_MENU = [
  { icon: FolderIcon, label: 'Projects', path: '/projects' },
  { icon: PlayIcon, label: 'Runs', path: '/runs' },
  { icon: ChartIcon, label: 'Evaluations', path: '/evaluations' },
  { icon: PackageIcon, label: 'Registry', path: '/registry' },
  { icon: SettingsIcon, label: 'Settings', path: '/settings' },
]

// src/components/ProjectSidebar.tsx
const PROJECT_MENU = [
  { icon: HomeIcon, label: 'Overview', path: 'overview' },
  { icon: HammerIcon, label: 'Build', path: 'build' },
  { icon: PlayIcon, label: 'Run', path: 'run' },
  { icon: CheckIcon, label: 'Quality', path: 'quality' },
  { icon: BoxIcon, label: 'Assets', path: 'assets' },
]
```

### Breadcrumb 导航

```tsx
// src/components/Breadcrumb.tsx
<Breadcrumb>
  <BreadcrumbItem href="/projects">Projects</BreadcrumbItem>
  <BreadcrumbItem href="/projects/web-automation">web-automation</BreadcrumbItem>
  <BreadcrumbItem>Quality</BreadcrumbItem>
  <BreadcrumbItem active>Gap Discovery</BreadcrumbItem>
</Breadcrumb>
```

---

## 📂 新目录结构

```
aitest/web/src/
├── layouts/
│   ├── GlobalLayout.tsx          # 全局布局
│   └── ProjectLayout.tsx         # 项目布局
│
├── components/
│   ├── GlobalSidebar.tsx         # 全局侧边栏
│   ├── ProjectSidebar.tsx        # 项目侧边栏
│   ├── Breadcrumb.tsx            # 面包屑导航
│   └── SidebarNav.tsx            # (保留，向后兼容)
│
├── views/
│   ├── global/                   # 全局视图
│   │   ├── ProjectsView.tsx      # 新增
│   │   ├── GlobalRunsView.tsx    # 新增
│   │   ├── EvaluationsView.tsx   # 新增
│   │   ├── RegistryView.tsx      # 新增
│   │   └── SettingsView.tsx      # 移动
│   │
│   ├── project/                  # 项目视图
│   │   ├── overview/
│   │   │   ├── OverviewView.tsx         # 合并 Dashboard + ProjectOverview
│   │   │   ├── TimelinePanel.tsx        # Timeline 作为组件
│   │   │   └── QuickActionsPanel.tsx
│   │   │
│   │   ├── build/
│   │   │   ├── BuildView.tsx            # 新增（Tab 容器）
│   │   │   ├── WorkflowBuilderView.tsx  # 移动
│   │   │   └── StrategyPlannerView.tsx  # 移动
│   │   │
│   │   ├── run/
│   │   │   ├── RunView.tsx              # 新增（Tab 容器）
│   │   │   ├── ExecutionView.tsx        # 移动
│   │   │   ├── RunInspectorView.tsx     # 移动（项目筛选）
│   │   │   └── KanbanView.tsx           # 移动
│   │   │
│   │   ├── quality/
│   │   │   ├── QualityView.tsx          # 新增（Tab 容器）
│   │   │   ├── GapDiscoveryView.tsx     # 移动
│   │   │   └── ReportsView.tsx          # 移动
│   │   │
│   │   ├── assets/
│   │   │   ├── AssetsView.tsx           # 新增（Tab 容器）
│   │   │   ├── AgentDetailView.tsx      # 移动
│   │   │   ├── AgentTerminalView.tsx    # 移动
│   │   │   ├── ArtifactsView.tsx        # 移动
│   │   │   ├── KnowledgeView.tsx        # 移动
│   │   │   └── KnowledgeGraphView.tsx   # 移动
│   │   │
│   │   └── ProjectSettingsView.tsx      # 移动
│   │
│   ├── cross-cutting/            # 横向功能
│   │   ├── IntelligenceChatView.tsx     # 移动
│   │   ├── OnboardingWizardView.tsx     # 移动
│   │   └── ObservabilityView.tsx        # 移动
│   │
│   └── (legacy)/                 # 旧文件（向后兼容期）
│       └── ... (旧的 19 个 Views，逐步删除)
│
└── router/
    └── index.ts                  # 重构路由配置
```

---

## 🔄 迁移策略

### Phase 1: 脚手架（基础设施）

**目标**: 搭建新架构，不影响现有功能

1. 创建 `GlobalLayout.tsx` 和 `ProjectLayout.tsx`
2. 创建 `GlobalSidebar.tsx` 和 `ProjectSidebar.tsx`
3. 创建 `Breadcrumb.tsx`
4. 创建新目录结构（空文件占位）

**验证**: 新 Layout 可以渲染，旧 Views 继续工作

---

### Phase 2: 全局视图迁移

**目标**: 实现 5 个全局视图

1. 创建 `ProjectsView`（新功能）
2. 创建 `GlobalRunsView`（复用 RunInspectorView 列表部分）
3. 创建 `EvaluationsView`（复用 ReportsView + GapDiscoveryView）
4. 创建 `RegistryView`（新功能）
5. 移动 `SettingsView` 到 `views/global/`

**验证**: 全局导航可用，可以切换到各个视图

---

### Phase 3: 项目视图迁移（分批）

#### Batch 1: Overview + Settings（低风险）
- 合并 `DashboardView` + `ProjectOverviewView` → `OverviewView`
- 移动 `ProjectSettingsView`

#### Batch 2: Run（高优先级）
- 创建 `RunView`（Tab 容器）
- 移动 `ExecutionView`、`RunInspectorView`、`KanbanView`

#### Batch 3: Quality（中优先级）
- 创建 `QualityView`（Tab 容器）
- 移动 `GapDiscoveryView`、`ReportsView`

#### Batch 4: Assets（低优先级）
- 创建 `AssetsView`（Tab 容器）
- 移动 `AgentDetailView`、`AgentTerminalView`、`ArtifactsView`、`KnowledgeView`、`KnowledgeGraphView`

#### Batch 5: Build（未来）
- 创建 `BuildView`（Tab 容器）
- 移动 `WorkflowBuilderView`、`StrategyPlannerView`

**验证**: 每批迁移后，功能保持不变

---

### Phase 4: 横向功能整合

1. 移动 `IntelligenceChatView` 到 `cross-cutting/`（全局悬浮按钮）
2. 移动 `OnboardingWizardView` 到 `cross-cutting/`
3. 移动 `ObservabilityView` 到 `cross-cutting/`（设置子页面）

**验证**: 横向功能可以在任意页面使用

---

### Phase 5: 清理与优化

1. 删除 `views/(legacy)/` 中的旧文件
2. 删除旧的 `SidebarNav.tsx`（如果不再需要）
3. 更新所有 `import` 路径
4. 优化路由配置（懒加载）
5. 添加路由守卫（权限检查）

**验证**: 无冗余代码，性能良好

---

## 🎨 UI/UX 设计要点

### 导航流程

```
用户进入 Studio
  ↓
默认显示 Projects 列表（/projects）
  ↓
用户选择项目 "web-automation"
  ↓
进入项目概览（/projects/web-automation/overview）
  ↓
左侧显示项目内导航（Overview/Build/Run/Quality/Assets）
  ↓
用户点击 "Run"
  ↓
进入 Run 视图（/projects/web-automation/run）
  ↓
显示 Execute/History/Kanban 三个 Tab
  ↓
用户点击 "History" Tab
  ↓
显示项目内 Run 历史（自动筛选当前项目）
```

### 视觉层级

```
┌─────────────────────────────────────────────────────────┐
│ Global Nav (Level 1)                                    │
│ Projects | Runs | Evaluations | Registry | Settings    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ┌─────────────┬─────────────────────────────────────┐ │
│ │ Project Nav │ Breadcrumb: Projects > web-auto...  │ │
│ │ (Level 2)   │                                     │ │
│ │             ├─────────────────────────────────────┤ │
│ │ Overview    │                                     │ │
│ │ Build       │  Content Area                       │ │
│ │ Run         │  (Views + Tabs)                     │ │
│ │ Quality     │                                     │ │
│ │ Assets      │                                     │ │
│ │             │                                     │ │
│ └─────────────┴─────────────────────────────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 响应式设计

- **Desktop（>1200px）**: 双层导航（Global + Project）
- **Tablet（768-1200px）**: 折叠 Project 导航为抽屉
- **Mobile（<768px）**: 汉堡菜单，单层导航

---

## 📊 工作量估算

| Phase | 任务 | 预计工时 | 复杂度 |
|-------|------|---------|--------|
| Phase 1 | 脚手架 | 3-4h | 中 |
| Phase 2 | 全局视图 | 4-6h | 中 |
| Phase 3.1 | Overview + Settings | 2-3h | 低 |
| Phase 3.2 | Run | 3-4h | 中 |
| Phase 3.3 | Quality | 2-3h | 低 |
| Phase 3.4 | Assets | 4-5h | 中 |
| Phase 3.5 | Build | 2-3h | 低 |
| Phase 4 | 横向功能 | 2-3h | 低 |
| Phase 5 | 清理优化 | 2-3h | 低 |
| **总计** | | **24-34h** | |

**分多次会话完成**，建议每次 4-6 小时。

---

## ✅ 验收标准

### 功能完整性
- ✅ 所有 19 个 Views 都能访问
- ✅ 导航流程符合设计
- ✅ 无功能丢失或降级

### 代码质量
- ✅ 无 TypeScript 错误
- ✅ 无 ESLint 警告
- ✅ 目录结构清晰

### 用户体验
- ✅ 导航逻辑清晰直观
- ✅ 面包屑导航正确
- ✅ 响应式布局正常

### 性能
- ✅ 路由懒加载正常
- ✅ 首屏加载时间 < 2s
- ✅ 页面切换流畅（< 300ms）

---

## 🚨 风险与缓解

### 风险 1: 影响面大，测试不足

**影响**: 19 个 Views 全部重新组织，可能引入回归 bug

**缓解**:
- 分阶段迁移，每次只改动少量文件
- 保留旧文件作为备份（legacy 目录）
- 每个 Phase 完成后充分测试

### 风险 2: 路由复杂度增加

**影响**: 嵌套路由、动态参数增多，容易出错

**缓解**:
- 使用 React Router v6 的嵌套路由特性
- 集中管理路由配置（`router/index.ts`）
- 添加路由单元测试

### 风险 3: 用户习惯改变

**影响**: 老用户需要重新学习导航

**缓解**:
- 提供迁移指南（文档）
- 首次登录显示引导提示
- 保留常用功能的快捷入口

---

## 📚 参考资料

- React Router v6 文档: https://reactrouter.com/
- shadcn/ui Layout 示例: https://ui.shadcn.com/examples/dashboard
- Material Design Navigation Patterns
- 交接文档: `docs/NEXT_SESSION_HANDOVER.md`

---

**设计状态**: ✅ 完成  
**下一步**: 开始 Phase 1 实施（创建脚手架）
