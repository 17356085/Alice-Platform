# Alice Studio 产品设计规格说明书

> **版本**: v1.0  
> **日期**: 2026-07-12  
> **产品定位**: AI Native Agent Platform  
> **文档目的**: 让设计师无需阅读代码，仅凭此文档即可设计整个 Alice Studio

---

## 第一部分：产品概述

### 1.1 产品定位

Alice（有珠）是一套 **AI Native Agent Platform**，已经从单一 Agent 演进为平台化产品。软件测试只是 Alice 的一个应用场景，而不是产品定位。

**最终定位**: 一个开放式 Agent 平台（Open Agent Platform）

### 1.2 产品愿景

Alice Studio 是一个让开发者和测试工程师能够：
- 编排和管理多个 AI Agent
- 构建可复用的 Workflow
- 监控 Agent 执行状态
- 分析执行结果和质量指标
- 管理知识库和 Memory

### 1.3 目标用户

| 用户角色 | 核心需求 | 使用频率 |
|---------|---------|---------|
| **测试工程师** | 执行测试、分析结果、管理缺陷 | 每日 |
| **QA Lead** | 监控质量、查看报告、管理策略 | 每日 |
| **DevOps** | 监控系统、管理部署、查看日志 | 每日 |
| **开发者** | 构建 Workflow、调试 Agent、查看执行 | 按需 |
| **产品经理** | 查看报告、了解质量状态 | 每周 |

### 1.4 技术栈

| 层级 | 技术 |
|-----|------|
| **前端** | React 18 + TypeScript + Vite 5 |
| **UI 框架** | Tailwind CSS 3 + Radix UI (shadcn/ui) |
| **状态管理** | Zustand |
| **路由** | React Router 6 |
| **后端** | Python FastAPI |
| **数据库** | SQLite / PostgreSQL |
| **实时通信** | WebSocket + SSE |

---

## 第二部分：产品功能分析

### 2.1 Dashboard（仪表板）

**模块定位**: 全局概览入口，展示系统状态和关键指标

**模块职责**: 
- 展示活跃 Agent 数量和状态
- 显示今日 Workflow 执行统计
- 展示成功率和 Memory 节点数
- 提供快速入口访问核心功能

**核心功能**:
- 统计卡片展示（Active Agents, Workflows Today, Success Rate, Memory Nodes）
- Agent 注册表展示（6个预置 Agent）
- 最近运行记录列表
- 系统健康状态监控
- 执行中任务横幅

**用户能够完成什么**:
- 快速了解系统整体状态
- 一键启动新的执行
- 查看 Agent 运行状态
- 访问最近的运行记录

**输入**: 无（自动从后端获取数据）

**输出**: 可视化统计数据、状态指示器

**主要状态**: 
- `loading` - 数据加载中
- `healthy` - 系统健康
- `degraded` - 系统降级

**与哪些模块关联**: 
- Execution（执行监控）
- Agent Registry（Agent 注册表）
- Observability（可观测性）

**未来可扩展能力**: 
- 自定义仪表板布局
- 实时数据流
- 告警通知

**UI是否需要独立页面**: 是

**页面重要等级**: P0

---

### 2.2 Workflow Builder（工作流构建器）

**模块定位**: 可视化构建 Agent 执行流程

**模块职责**: 
- 创建和管理 Workflow 资源
- 可视化编辑节点图
- 校验 Workflow 结构
- 发布 Workflow

**核心功能**:
- 创建 Draft Workflow
- 添加 Agent 节点
- 添加连接边（Edge）
- 拖拽调整节点位置
- 校验 Workflow 结构
- 调试运行
- 发布 Workflow

**用户能够完成什么**:
- 设计 Agent 执行流程
- 配置节点间的数据流
- 验证 Workflow 逻辑
- 发布可执行的 Workflow

**输入**: 
- Workflow 名称和描述
- Agent 节点配置
- 连接边和条件

**输出**: 
- Workflow 资源（draft/published/archived）
- 校验结果
- 调试运行结果

**主要状态**: 
- `draft` - 草稿
- `published` - 已发布
- `archived` - 已归档

**与哪些模块关联**: 
- Agents（Agent 注册表）
- Execution（执行监控）
- Registry（注册中心）

**未来可扩展能力**: 
- 条件分支
- 循环结构
- 子 Workflow
- 版本管理

**UI是否需要独立页面**: 是

**页面重要等级**: P0

---

### 2.3 Execution Center（执行中心）

**模块定位**: 监控和控制 Agent 执行

**模块职责**: 
- 选择模块和执行模式
- 启动/暂停/取消执行
- 展示 SOP 阶段进度
- 实时 Agent 执行图
- Agent 终端日志

**核心功能**:
- 模块选择器
- SOP 模式选择（完整/从自动化开始/恢复上次）
- 执行控制（运行/暂停/取消）
- Phase 进度条（9个阶段）
- Agent 执行图（LiveAgentGraph）
- Agent 终端（TerminalPanel）
- Run Inspector（运行检查器）

**用户能够完成什么**:
- 选择要执行的模块
- 控制执行流程
- 实时监控 Agent 活动
- 查看执行详情

**输入**: 
- 模块 ID
- SOP 模式

**输出**: 
- 执行状态
- Phase 进度
- Agent 活动日志

**主要状态**: 
- `idle` - 空闲
- `running` - 执行中
- `paused` - 已暂停
- `completed` - 已完成
- `failed` - 失败

**与哪些模块关联**: 
- Dashboard（仪表板）
- Kanban Board（看板）
- Run Inspector（运行检查器）
- Agent Terminal（Agent 终端）

**未来可扩展能力**: 
- 并行执行
- 执行队列
- 调度执行

**UI是否需要独立页面**: 是

**页面重要等级**: P0

---

### 2.4 Kanban Board（看板）

**模块定位**: SOP 阶段可视化管理

**模块职责**: 
- 展示模块在 SOP 各阶段的分布
- 支持拖拽移动卡片
- 实时更新模块状态
- 启动模块 SOP

**核心功能**:
- 9列看板（Project Init → Knowledge）
- 模块卡片展示
- 拖拽移动卡片
- 模块详情 Sheet
- 启动 SOP 按钮
- 运行中状态指示

**用户能够完成什么**:
- 查看模块在各阶段的分布
- 手动调整模块阶段
- 启动模块 SOP
- 查看模块详情

**输入**: 
- 项目 ID

**输出**: 
- 模块阶段分布
- 模块状态

**主要状态**: 
- `loading` - 加载中
- `ready` - 就绪
- `running` - 运行中

**与哪些模块关联**: 
- Execution Center（执行中心）
- Project Overview（项目概览）
- Agent Detail（Agent 详情）

**未来可扩展能力**: 
- 自定义列
- 批量操作
- 过滤和搜索

**UI是否需要独立页面**: 是

**页面重要等级**: P0

---

### 2.5 Agent Detail（Agent 详情）

**模块定位**: 单个 Agent 的详细信息

**模块职责**: 
- 展示 Agent 基本信息
- 展示 Agent 能力标签
- 展示执行指标
- 展示最近执行历史
- 展示性能指标

**核心功能**:
- Agent 头像和描述
- 能力标签展示
- 指标卡片（成功率、执行次数、Tokens、成本）
- 最近执行列表
- 性能指标（成功率、平均耗时）
- 时间线链接

**用户能够完成什么**:
- 了解 Agent 功能和状态
- 查看 Agent 执行历史
- 分析 Agent 性能

**输入**: 
- Agent ID

**输出**: 
- Agent 信息
- 执行历史
- 性能指标

**主要状态**: 
- `idle` - 空闲
- `running` - 运行中
- `success` - 成功

**与哪些模块关联**: 
- Dashboard（仪表板）
- Timeline（时间线）
- Agent Terminal（Agent 终端）

**未来可扩展能力**: 
- Agent 配置编辑
- Agent 版本管理
- Agent 比较

**UI是否需要独立页面**: 是

**页面重要等级**: P1

---

### 2.6 Knowledge Base（知识库）

**模块定位**: ChromaDB 知识库管理

**模块职责**: 
- 展示知识库统计
- 管理集合和文档
- 展示 ChromaDB 状态

**核心功能**:
- 统计卡片（集合、文档、ChromaDB）
- 知识库状态展示
- 未来：文档管理界面

**用户能够完成什么**:
- 了解知识库状态
- 未来：管理知识库文档

**输入**: 无

**输出**: 知识库统计

**主要状态**: 
- `loading` - 加载中
- `ready` - 就绪

**与哪些模块关联**: 
- Knowledge Graph（知识图谱）
- Memory（记忆）

**未来可扩展能力**: 
- 文档上传
- 集合管理
- 搜索和检索

**UI是否需要独立页面**: 是

**页面重要等级**: P1

---

### 2.7 Knowledge Graph（知识图谱）

**模块定位**: 可视化展示 Agent 记忆节点关系

**模块职责**: 
- 展示模块节点
- 展示已知问题
- 展示定位器模式
- 展示节点间关系

**核心功能**:
- SVG 力导向图
- 节点按类型着色（module/issue/pattern）
- 缩放和重置控制
- 图例展示

**用户能够完成什么**:
- 可视化理解知识结构
- 发现模块间关系
- 识别问题模式

**输入**: 无（模拟数据）

**输出**: 可视化图谱

**主要状态**: 
- `ready` - 就绪

**与哪些模块关联**: 
- Knowledge Base（知识库）
- Memory（记忆）

**未来可扩展能力**: 
- 交互式节点操作
- 实时数据更新
- 筛选和搜索

**UI是否需要独立页面**: 是

**页面重要等级**: P2

---

### 2.8 Artifacts（产物）

**模块定位**: 浏览、预览和下载 SOP 生成的产物

**模块职责**: 
- 展示文件产物
- 展示 Run 产物
- 预览内容
- 下载文件

**核心功能**:
- 产物网格展示
- 搜索和筛选（类型、模块）
- 内容预览（Markdown、代码、图片）
- 下载和复制路径
- 详情 Sheet

**用户能够完成什么**:
- 浏览所有产物
- 预览产物内容
- 下载产物文件

**输入**: 
- 项目 ID

**输出**: 
- 产物列表
- 产物内容

**主要状态**: 
- `loading` - 加载中
- `ready` - 就绪
- `empty` - 无产物

**与哪些模块关联**: 
- Execution Center（执行中心）
- Run Inspector（运行检查器）

**未来可扩展能力**: 
- 产物版本管理
- 产物比较
- 产物分享

**UI是否需要独立页面**: 是

**页面重要等级**: P1

---

### 2.9 Reports（测试报告）

**模块定位**: KPI 和测试报告

**模块职责**: 
- 展示通过率
- 展示覆盖率
- 展示缺陷数

**核心功能**:
- 统计卡片（通过率、覆盖率、缺陷数）
- 报告生成提示

**用户能够完成什么**:
- 查看测试质量指标
- 了解测试覆盖情况

**输入**: 无

**输出**: 质量指标

**主要状态**: 
- `loading` - 加载中
- `ready` - 就绪

**与哪些模块关联**: 
- Execution Center（执行中心）
- Gap Discovery（缺口发现）

**未来可扩展能力**: 
- 报告导出
- 趋势分析
- 对比分析

**UI是否需要独立页面**: 是

**页面重要等级**: P1

---

### 2.10 Gap Discovery（缺口发现）

**模块定位**: 发现测试覆盖缺口

**模块职责**: 
- 扫描测试缺口
- 分类缺口类型
- 展示缺口详情
- 提供建议

**核心功能**:
- 自动扫描
- 缺口类型筛选（缺失测试、缺失类型、覆盖不足、不稳定、未测组件）
- 缺口卡片展示
- 创建任务、忽略、归档操作

**用户能够完成什么**:
- 发现测试覆盖不足
- 了解缺口严重程度
- 将缺口转化为任务

**输入**: 
- 项目 ID

**输出**: 
- 缺口列表
- 缺口统计

**主要状态**: 
- `scanning` - 扫描中
- `ready` - 就绪
- `empty` - 无缺口

**与哪些模块关联**: 
- Reports（测试报告）
- Execution Center（执行中心）

**未来可扩展能力**: 
- 自动修复建议
- 缺口趋势分析
- 优先级排序

**UI是否需要独立页面**: 是

**页面重要等级**: P1

---

### 2.11 Strategy Planner（策略规划）

**模块定位**: 测试策略和风险评分

**模块职责**: 
- 展示风险评分公式
- 提供测试建议

**核心功能**:
- 风险评分公式展示
- 模块选择提示

**用户能够完成什么**:
- 了解风险评分方法
- 未来：查看模块风险评分

**输入**: 
- 模块 ID

**输出**: 
- 风险评分
- 测试建议

**主要状态**: 
- `loading` - 加载中
- `ready` - 就绪

**与哪些模块关联**: 
- Execution Center（执行中心）
- Reports（测试报告）

**未来可扩展能力**: 
- 风险可视化
- 策略推荐
- 历史对比

**UI是否需要独立页面**: 是

**页面重要等级**: P2

---

### 2.12 Run Inspector（运行检查器）

**模块定位**: DevTools 风格的执行详情

**模块职责**: 
- 展示 Run 头部信息
- 展示 Timeline
- 展示 Artifacts
- 展示 Agent Calls
- 展示 Metrics
- 展示 Logs
- 展示 Execution Tree
- 展示 AI Report

**核心功能**:
- KPI 卡片（Duration, Module, Agent, Tokens, Cost, Artifacts, Pages）
- 6个 Tab（Timeline, Artifacts, Agent Calls, Metrics, Logs, Tree, Report）
- Swimlane Timeline 可视化
- Agent Call 详情（Prompt, Response, Tool Calls）
- 执行树可视化
- AI 报告生成

**用户能够完成什么**:
- 深入分析执行过程
- 查看 Agent 调用详情
- 分析性能指标
- 查看执行日志

**输入**: 
- Run ID

**输出**: 
- Run 详情
- 执行分析

**主要状态**: 
- `loading` - 加载中
- `ready` - 就绪
- `error` - 错误

**与哪些模块关联**: 
- Execution Center（执行中心）
- Global Runs（全局运行记录）

**未来可扩展能力**: 
- 时间线过滤
- 性能对比
- 导出报告

**UI是否需要独立页面**: 是

**页面重要等级**: P0

---

### 2.13 Timeline（时间线）

**模块定位**: 执行事件追踪

**模块职责**: 
- 展示执行事件时间线
- 按模块和类型筛选
- 展示事件详情

**核心功能**:
- 时间线可视化
- 模块筛选器
- 类型筛选器（Phase Start, Phase Done, Error, Warning, Artifact）
- 事件详情展开（Tokens, Cost, Duration, Output）

**用户能够完成什么**:
- 追踪执行过程
- 分析事件详情
- 发现问题和异常

**输入**: 
- 项目 ID

**输出**: 
- 事件时间线
- 事件详情

**主要状态**: 
- `loading` - 加载中
- `ready` - 就绪
- `empty` - 无事件

**与哪些模块关联**: 
- Agent Detail（Agent 详情）
- Execution Center（执行中心）

**未来可扩展能力**: 
- 实时事件流
- 事件关联分析
- 导出时间线

**UI是否需要独立页面**: 是

**页面重要等级**: P1

---

### 2.14 Agent Terminal（Agent 终端）

**模块定位**: 实时 Agent 日志查看器

**模块职责**: 
- 展示 Agent 实时日志
- 按 Agent 分 Tab
- 展示 Agent 指标

**核心功能**:
- Agent 列表侧边栏
- 实时日志流
- 连接状态指示
- Agent 指标（Tokens, Cost, Duration）
- 自动滚动控制

**用户能够完成什么**:
- 实时监控 Agent 活动
- 查看 Agent 日志
- 分析 Agent 性能

**输入**: 
- 项目 ID

**输出**: 
- 实时日志
- Agent 指标

**主要状态**: 
- `connecting` - 连接中
- `connected` - 已连接
- `disconnected` - 已断开

**与哪些模块关联**: 
- Execution Center（执行中心）
- Agent Detail（Agent 详情）

**未来可扩展能力**: 
- 日志搜索
- 日志过滤
- 日志导出

**UI是否需要独立页面**: 是

**页面重要等级**: P1

---

### 2.15 Intelligence Chat（智能对话）

**模块定位**: AI 驱动的测试智能对话

**模块职责**: 
- 展示对话历史
- 发送消息
- 展示 AI 响应
- 展示工具使用

**核心功能**:
- 对话界面
- 消息列表
- 输入框
- 建议问题
- 工具指示器
- Markdown 渲染
- 会话侧边栏

**用户能够完成什么**:
- 与 AI 对话了解测试情况
- 获取测试建议
- 分析测试数据

**输入**: 
- 用户消息

**输出**: 
- AI 响应
- 工具使用详情

**主要状态**: 
- `streaming` - 流式响应中
- `ready` - 就绪
- `error` - 错误

**与哪些模块关联**: 
- Dashboard（仪表板）
- Knowledge Base（知识库）

**未来可扩展能力**: 
- 多轮对话
- 上下文记忆
- 工具调用可视化

**UI是否需要独立页面**: 是

**页面重要等级**: P1

---

### 2.16 Observability（可观测性）

**模块定位**: 系统资源监控

**模块职责**: 
- 监控内存使用
- 监控线程和任务
- 监控队列和 WebSocket
- 监控存储

**核心功能**:
- 4个 Tab（Overview, Memory & GC, Threads & Tasks, Queue & WS）
- 实时数据刷新（10秒间隔）
- 自动刷新控制
- 统计卡片展示

**用户能够完成什么**:
- 监控系统资源使用
- 发现性能瓶颈
- 了解系统健康状态

**输入**: 无

**输出**: 
- 系统资源指标
- 健康状态

**主要状态**: 
- `loading` - 加载中
- `ready` - 就绪
- `error` - 错误

**与哪些模块关联**: 
- Dashboard（仪表板）
- System Health（系统健康）

**未来可扩展能力**: 
- 告警阈值配置
- 历史趋势分析
- 资源预测

**UI是否需要独立页面**: 是

**页面重要等级**: P1

---

### 2.17 Settings（设置）

**模块定位**: 应用全局配置

**模块职责**: 
- 管理外观设置
- 管理语言设置
- 管理 Provider 设置
- 管理预算设置

**核心功能**:
- 主题选择（Alice/Aoko/Soujuurou）
- 暗色模式切换
- 语言切换（中文/English）
- Provider 选择（claude/deepseek/openai/ollama）
- 预算设置

**用户能够完成什么**:
- 个性化外观
- 切换语言
- 配置 AI Provider
- 设置预算限制

**输入**: 
- 用户配置

**输出**: 
- 配置保存

**主要状态**: 
- `ready` - 就绪

**与哪些模块关联**: 
- 全局应用

**未来可扩展能力**: 
- 通知设置
- 快捷键设置
- 导入/导出配置

**UI是否需要独立页面**: 是

**页面重要等级**: P1

---

### 2.18 Global Runs（全局运行记录）

**模块定位**: 跨项目的运行记录查看

**模块职责**: 
- 展示所有项目的运行记录
- 搜索和筛选
- 查看运行详情

**核心功能**:
- 运行记录表格
- 搜索框
- 状态筛选器
- 分页

**用户能够完成什么**:
- 查看所有运行记录
- 搜索特定运行
- 按状态筛选

**输入**: 
- 无

**输出**: 
- 运行记录列表

**主要状态**: 
- `loading` - 加载中
- `ready` - 就绪
- `empty` - 无记录

**与哪些模块关联**: 
- Run Inspector（运行检查器）
- Dashboard（仪表板）

**未来可扩展能力**: 
- 高级筛选
- 批量操作
- 导出记录

**UI是否需要独立页面**: 是

**页面重要等级**: P1

---

### 2.19 Evaluations（质量评估）

**模块定位**: Dataset 驱动的质量评估

**模块职责**: 
- 管理评估任务
- 管理 Dataset
- 展示评估结果

**核心功能**:
- 统计卡片（Datasets, Evaluations, 平均通过率）
- 评估任务列表
- Dataset 列表

**用户能够完成什么**:
- 创建评估任务
- 管理 Dataset
- 查看评估结果

**输入**: 
- 无

**输出**: 
- 评估任务列表
- Dataset 列表
- 评估结果

**主要状态**: 
- `loading` - 加载中
- `ready` - 就绪
- `empty` - 无数据

**与哪些模块关联**: 
- Reports（测试报告）
- Run Inspector（运行检查器）

**未来可扩展能力**: 
- 自动评估
- 评估对比
- 评估报告

**UI是否需要独立页面**: 是

**页面重要等级**: P1

---

### 2.20 Registry（注册中心）

**模块定位**: 统一浏览可组合资源

**模块职责**: 
- 展示 Agents
- 展示 Workflows
- 展示 Providers
- 展示 Environments
- 展示 Plugins

**核心功能**:
- 5个 Tab（Agents, Workflows, Providers, Environments, Plugins）
- 资源列表展示
- 资源详情

**用户能够完成什么**:
- 浏览所有可用资源
- 了解资源状态
- 未来：管理资源

**输入**: 无

**输出**: 
- 资源列表

**主要状态**: 
- `loading` - 加载中
- `ready` - 就绪
- `empty` - 无资源

**与哪些模块关联**: 
- Workflow Builder（工作流构建器）
- Execution Center（执行中心）

**未来可扩展能力**: 
- 资源搜索
- 资源比较
- 资源版本管理

**UI是否需要独立页面**: 是

**页面重要等级**: P1

---

### 2.21 Onboarding Wizard（项目引导向导）

**模块定位**: 多步骤项目发现

**模块职责**: 
- 引导用户创建新项目
- 自动发现应用结构
- 生成菜单配置

**核心功能**:
- 4个步骤（Source, Discovery, Review, Results）
- 进度条展示
- URL/本地路径输入
- 实时扫描进度
- 菜单确认
- 结果展示

**用户能够完成什么**:
- 创建新项目
- 自动发现应用结构
- 确认生成的菜单

**输入**: 
- URL 或本地路径

**输出**: 
- 项目配置
- 菜单结构

**主要状态**: 
- `idle` - 空闲
- `scanning` - 扫描中
- `complete` - 完成
- `failed` - 失败
- `cancelled` - 已取消

**与哪些模块关联**: 
- Dashboard（仪表板）
- Project Overview（项目概览）

**未来可扩展能力**: 
- 模板选择
- 自定义配置
- 导入现有项目

**UI是否需要独立页面**: 是

**页面重要等级**: P1

---

### 2.22 Project Settings（项目设置）

**模块定位**: 单个项目配置

**模块职责**: 
- 管理项目 ID
- 管理最大并行数
- 管理主分支
- 管理 Provider/Model 覆盖

**核心功能**:
- 项目 ID 展示
- 最大并行数配置
- 主分支配置
- Provider/Model 覆盖展示

**用户能够完成什么**:
- 配置项目参数
- 自定义项目行为

**输入**: 
- 项目 ID

**输出**: 
- 项目配置

**主要状态**: 
- `ready` - 就绪

**与哪些模块关联**: 
- Project Overview（项目概览）

**未来可扩展能力**: 
- 环境变量管理
- 密钥管理
- 通知配置

**UI是否需要独立页面**: 是

**页面重要等级**: P2

---

## 第三部分：信息架构

### 3.1 全局导航结构

```
Alice Studio
├── Dashboard（仪表板）
├── Agents（Agent 注册表）
├── Workflow（工作流构建器）
├── Execution（执行中心）
├── Memory（记忆）
├── Knowledge（知识库）
├── Prompt（提示词）
├── Evaluation（质量评估）
├── Reports（测试报告）
├── Replay（重放）
├── Monitoring（监控）
├── Plugins（插件）
├── MCP（MCP 服务）
└── Settings（设置）
```

### 3.2 项目级导航结构

```
Project
├── Overview（项目概览）
├── Build（构建）
│   ├── Strategy Planner（策略规划）
│   └── Workflow Builder（工作流构建器）
├── Run（执行）
│   ├── Execution Center（执行中心）
│   ├── Kanban Board（看板）
│   └── Run Inspector（运行检查器）
├── Quality（质量）
│   ├── Reports（测试报告）
│   └── Gap Discovery（缺口发现）
└── Assets（资产）
    ├── Artifacts（产物）
    ├── Knowledge Base（知识库）
    ├── Knowledge Graph（知识图谱）
    ├── Agent Detail（Agent 详情）
    └── Agent Terminal（Agent 终端）
```

### 3.3 全局级导航结构

```
Global
├── Projects（项目列表）
├── Runs（全局运行记录）
├── Evaluations（质量评估）
├── Registry（注册中心）
├── Settings（设置）
└── Onboarding（项目引导向导）
```

---

## 第四部分：用户流程

### 4.1 新用户首次使用流程

```
进入 Dashboard
    ↓
查看系统状态和 Agent 信息
    ↓
点击 "New run" 或进入 Execution
    ↓
选择模块和 SOP 模式
    ↓
启动执行
    ↓
查看执行进度（Phase 进度条）
    ↓
查看 Agent 执行图
    ↓
查看 Agent 终端日志
    ↓
执行完成
    ↓
查看 Run Inspector
    ↓
分析 Timeline
    ↓
查看 Artifacts
    ↓
查看 AI Report
    ↓
优化策略
    ↓
再次执行
```

### 4.2 项目创建流程

```
进入 Onboarding Wizard
    ↓
选择 Source（URL 或本地路径）
    ↓
输入 URL 或选择本地文件夹
    ↓
自动扫描应用结构
    ↓
确认生成的菜单
    ↓
完成项目创建
    ↓
进入 Project Overview
    ↓
开始使用
```

### 4.3 Workflow 构建流程

```
进入 Workflow Builder
    ↓
创建 Draft Workflow
    ↓
添加 Agent 节点
    ↓
添加连接边
    ↓
调整节点位置
    ↓
校验 Workflow
    ↓
调试运行
    ↓
发布 Workflow
    ↓
在 Execution 中使用
```

### 4.4 质量分析流程

```
查看 Dashboard 成功率
    ↓
进入 Gap Discovery
    ↓
扫描测试缺口
    ↓
查看缺口详情
    ↓
创建任务
    ↓
执行修复
    ↓
再次扫描
    ↓
查看 Reports
    ↓
分析质量趋势
```

---

## 第五部分：页面规划

### 5.1 Dashboard

**页面目标**: 展示系统整体状态，提供快速入口

**主要内容**:
- 统计卡片（4个）
- Agent 注册表（6个 Agent 卡片）
- 最近运行记录（5条）
- 系统健康状态（4个指标）
- 执行中任务横幅

**必须展示的信息**:
- Active Agents 数量
- Workflows Today 数量
- Success Rate
- Memory Nodes 数量
- Agent 名称、状态、得分、运行次数
- 最近运行 ID、时间、测试数
- 系统健康状态

**主要交互**:
- 点击 Agent 卡片 → Agent Detail
- 点击运行记录 → Global Runs
- 点击 "New run" → Execution
- 点击执行中横幅 → Execution

**页面布局建议**:
- 顶部：标题 + 操作按钮
- 中部：统计卡片（4列网格）
- 下部：Agent 网格 + 侧边栏（运行记录 + 系统状态）

**适合使用哪些组件**:
- StatCard（统计卡片）
- AgentCard（Agent 卡片）
- HealthRow（健康状态行）
- Button（按钮）

**空状态**: 展示 "No agents registered" 提示

**加载状态**: Skeleton 卡片

**错误状态**: 错误提示 + 重试按钮

**移动端是否需要**: 是（响应式布局）

**未来扩展建议**:
- 自定义仪表板布局
- 实时数据流
- 告警通知

---

### 5.2 Workflow Builder

**页面目标**: 可视化构建 Agent 执行流程

**主要内容**:
- 新建 Workflow 表单
- Workflow 列表
- 节点编辑器
- 边编辑器

**必须展示的信息**:
- Workflow 名称、描述、版本
- Workflow 状态（draft/published/archived）
- 节点列表
- 边列表

**主要交互**:
- 创建 Workflow
- 添加/移除节点
- 添加/移除边
- 拖拽调整节点位置
- 校验 Workflow
- 调试运行
- 发布 Workflow

**页面布局建议**:
- 左侧：新建表单（360px）
- 右侧：Workflow 列表 + 编辑器

**适合使用哪些组件**:
- Card（卡片）
- Input（输入框）
- Textarea（文本域）
- Button（按钮）
- Badge（徽章）
- Select（选择器）

**空状态**: "从一个 Draft 开始" 提示

**加载状态**: 动画骨架

**错误状态**: 错误提示

**移动端是否需要**: 否（复杂交互）

**未来扩展建议**:
- 可视化节点编辑器
- 条件分支
- 版本管理

---

### 5.3 Execution Center

**页面目标**: 监控和控制 Agent 执行

**主要内容**:
- 模块选择器
- SOP 模式选择
- 执行控制按钮
- Phase 进度条
- Agent 执行图
- Agent 终端
- Run Inspector

**必须展示的信息**:
- 当前模块
- SOP 模式
- 执行状态
- Phase 进度
- Agent 活动
- 运行列表

**主要交互**:
- 选择模块
- 选择 SOP 模式
- 启动/暂停/取消执行
- 查看 Agent 执行图
- 查看 Agent 终端
- 查看 Run 详情

**页面布局建议**:
- 顶部：控制栏（模块选择 + 模式选择 + 按钮）
- 中部：Phase 进度条
- 下部：Agent 执行图 + Agent 终端（左右分栏）

**适合使用哪些组件**:
- Select（选择器）
- Button（按钮）
- Badge（徽章）
- LiveAgentGraph（Agent 执行图）
- TerminalPanel（终端面板）
- HumanGatePanel（人工门控面板）

**空状态**: "选择模块以开始" 提示

**加载状态**: 进度条动画

**错误状态**: 错误提示

**移动端是否需要**: 否（复杂交互）

**未来扩展建议**:
- 并行执行
- 执行队列
- 调度执行

---

### 5.4 Kanban Board

**页面目标**: SOP 阶段可视化管理

**主要内容**:
- 9列看板
- 模块卡片
- 模块详情 Sheet

**必须展示的信息**:
- 模块名称
- 模块阶段
- 模块状态
- 页面数量
- 产物数量

**主要交互**:
- 拖拽移动卡片
- 点击卡片查看详情
- 启动 SOP

**页面布局建议**:
- 全宽看板（9列）
- 每列显示模块卡片

**适合使用哪些组件**:
- KanbanBoard（看板）
- ModuleDetailSheet（模块详情 Sheet）
- Badge（徽章）

**空状态**: "No modules loaded" 提示

**加载状态**: 骨架卡片

**错误状态**: 错误提示

**移动端是否需要**: 否（桌面优先）

**未来扩展建议**:
- 自定义列
- 批量操作
- 过滤和搜索

---

### 5.5 Run Inspector

**页面目标**: DevTools 风格的执行详情

**主要内容**:
- KPI 卡片（8个）
- 6个 Tab（Timeline, Artifacts, Agent Calls, Metrics, Logs, Tree, Report）

**必须展示的信息**:
- Run ID、状态
- Duration、Module、Agent
- Tokens、Cost、Artifacts、Pages
- Timeline 事件
- Agent Call 详情
- 执行日志
- 执行树
- AI Report

**主要交互**:
- 切换 Tab
- 展开/折叠 Agent Call
- 查看 Timeline 详情
- 下载 Artifacts

**页面布局建议**:
- 顶部：返回按钮 + 标题 + 状态
- 中部：KPI 卡片（8列网格）
- 下部：Tab 内容

**适合使用哪些组件**:
- Tabs（标签页）
- Card（卡片）
- Badge（徽章）
- ScrollArea（滚动区域）
- SwimlaneTimeline（泳道时间线）
- TreeNodeRow（树节点行）

**空状态**: "No data available" 提示

**加载状态**: 骨架

**错误状态**: 错误提示 + 返回按钮

**移动端是否需要**: 否（桌面优先）

**未来扩展建议**:
- 时间线过滤
- 性能对比
- 导出报告

---

### 5.6 Knowledge Graph

**页面目标**: 可视化展示 Agent 记忆节点关系

**主要内容**:
- SVG 力导向图
- 图例
- 缩放控制

**必须展示的信息**:
- 模块节点
- 已知问题
- 定位器模式
- 节点关系

**主要交互**:
- 缩放
- 重置
- 查看节点详情

**页面布局建议**:
- 顶部：标题 + 缩放控制
- 中部：SVG 图谱
- 下部：图例卡片

**适合使用哪些组件**:
- SVG（图谱）
- Button（按钮）
- Card（卡片）

**空状态**: 无（始终有模拟数据）

**加载状态**: 无

**错误状态**: 无

**移动端是否需要**: 否（桌面优先）

**未来扩展建议**:
- 交互式节点操作
- 实时数据更新
- 筛选和搜索

---

### 5.7 Artifacts

**页面目标**: 浏览、预览和下载产物

**主要内容**:
- 产物网格
- 搜索和筛选
- 内容预览

**必须展示的信息**:
- 产物名称
- 产物类型
- 产物大小
- 产物状态

**主要交互**:
- 搜索产物
- 筛选类型
- 筛选模块
- 预览内容
- 下载文件
- 复制路径

**页面布局建议**:
- 顶部：标题 + 筛选器
- 中部：产物网格
- 侧边：内容预览 Sheet

**适合使用哪些组件**:
- Card（卡片）
- Input（输入框）
- Select（选择器）
- Badge（徽章）
- Sheet（侧边栏）
- ScrollArea（滚动区域）

**空状态**: "No artifacts yet" 提示

**加载状态**: 骨架网格

**错误状态**: 错误提示

**移动端是否需要**: 是（响应式布局）

**未来扩展建议**:
- 产物版本管理
- 产物比较
- 产物分享

---

### 5.8 Intelligence Chat

**页面目标**: AI 驱动的测试智能对话

**主要内容**:
- 对话界面
- 消息列表
- 输入框
- 建议问题
- 会话侧边栏

**必须展示的信息**:
- 用户消息
- AI 响应
- 工具使用详情
- 建议问题

**主要交互**:
- 发送消息
- 点击建议问题
- 切换会话
- 展开工具详情

**页面布局建议**:
- 左侧：会话侧边栏
- 右侧：对话界面（消息列表 + 输入框）

**适合使用哪些组件**:
- Button（按钮）
- Textarea（文本域）
- Badge（徽章）
- Markdown（Markdown 渲染）
- ToolIndicator（工具指示器）

**空状态**: 建议问题网格

**加载状态**: 流式响应动画

**错误状态**: 错误提示

**移动端是否需要**: 是（响应式布局）

**未来扩展建议**:
- 多轮对话
- 上下文记忆
- 工具调用可视化

---

## 第六部分：组件库分析

### 6.1 基础组件

| 组件 | 用途 | 来源 |
|-----|------|------|
| Button | 按钮 | shadcn/ui |
| Input | 输入框 | shadcn/ui |
| Textarea | 文本域 | shadcn/ui |
| Card | 卡片 | shadcn/ui |
| Badge | 徽章 | shadcn/ui |
| Select | 选择器 | shadcn/ui |
| Tabs | 标签页 | shadcn/ui |
| Separator | 分隔线 | shadcn/ui |
| ScrollArea | 滚动区域 | shadcn/ui |
| Skeleton | 骨架屏 | shadcn/ui |
| Checkbox | 复选框 | shadcn/ui |
| Label | 标签 | shadcn/ui |
| Tooltip | 工具提示 | shadcn/ui |
| Dialog | 对话框 | shadcn/ui |
| Sheet | 侧边栏 | shadcn/ui |
| Collapsible | 可折叠 | shadcn/ui |
| Progress | 进度条 | shadcn/ui |
| ToggleGroup | 切换组 | shadcn/ui |

### 6.2 业务组件

| 组件 | 用途 | 页面 |
|-----|------|------|
| StatCard | 统计卡片 | Dashboard |
| AgentCard | Agent 卡片 | Dashboard |
| HealthRow | 健康状态行 | Dashboard |
| ModuleCard | 模块卡片 | Kanban Board |
| RunRow | 运行记录行 | Global Runs |
| TimelineEvent | 时间线事件 | Timeline |
| LogEntry | 日志条目 | Agent Terminal |
| MessageBubble | 消息气泡 | Intelligence Chat |
| SuggestionCard | 建议卡片 | Intelligence Chat |

### 6.3 高级组件

| 组件 | 用途 | 页面 |
|-----|------|------|
| LiveAgentGraph | Agent 执行图 | Execution Center |
| TerminalPanel | 终端面板 | Execution Center |
| SwimlaneTimeline | 泳道时间线 | Run Inspector |
| TreeNodeRow | 树节点行 | Run Inspector |
| KanbanBoard | 看板 | Kanban Board |
| ModuleDetailSheet | 模块详情 | Kanban Board |
| ArtifactContentRenderer | 产物内容渲染器 | Artifacts |
| Markdown | Markdown 渲染 | Intelligence Chat |
| ToolIndicator | 工具指示器 | Intelligence Chat |
| ChatSidebar | 会话侧边栏 | Intelligence Chat |

---

## 第七部分：数据可视化建议

### 7.1 Dashboard

| 数据 | 推荐图表 | 说明 |
|-----|---------|------|
| Active Agents | 数字卡片 | 简洁展示 |
| Workflows Today | 数字卡片 | 简洁展示 |
| Success Rate | 数字卡片 + 进度条 | 展示趋势 |
| Memory Nodes | 数字卡片 | 简洁展示 |

### 7.2 Execution Center

| 数据 | 推荐图表 | 说明 |
|-----|---------|------|
| SOP Phase Progress | 进度点 | 9个阶段状态 |
| Agent Execution | 有向图 | 节点 + 边 |
| Agent Activity | 实时日志流 | 终端风格 |

### 7.3 Run Inspector

| 数据 | 推荐图表 | 说明 |
|-----|---------|------|
| Timeline | 泳道时间线 | 多 Agent 并行 |
| Token Distribution | 数字卡片 | 简洁展示 |
| Cost Analysis | 数字卡片 | 简洁展示 |
| Phase Breakdown | 进度条列表 | 各阶段耗时 |
| Execution Tree | 树形图 | 层级结构 |

### 7.4 Knowledge Graph

| 数据 | 推荐图表 | 说明 |
|-----|---------|------|
| Knowledge Nodes | 力导向图 | 节点关系 |
| Node Types | 颜色编码 | module/issue/pattern |

### 7.5 Timeline

| 数据 | 推荐图表 | 说明 |
|-----|---------|------|
| Events | 时间线 | 垂直时间线 |
| Event Details | 展开面板 | Tokens/Cost/Duration |

### 7.6 Observability

| 数据 | 推荐图表 | 说明 |
|-----|---------|------|
| Memory Usage | 进度条 | RSS/VMS |
| GC Generations | 进度条列表 | Gen0/1/2 |
| Task Breakdown | 进度条 | Pending/Done |
| Queue Status | 数字卡片 | 队列状态 |

---

## 第八部分：UX 分析

### 8.1 信息过载页面

| 页面 | 问题 | 建议 |
|-----|------|------|
| Run Inspector | 6个 Tab 信息密集 | 默认折叠详细信息，按需展开 |
| Execution Center | 同时展示控制、进度、图、终端 | 分区域明确，使用卡片分隔 |
| Dashboard | 统计卡片 + Agent 列表 + 运行记录 | 使用清晰的视觉层次 |

### 8.2 容易迷路页面

| 页面 | 问题 | 建议 |
|-----|------|------|
| Execution Center | 多个子区域 | 清晰的面包屑导航 |
| Run Inspector | 多个 Tab | 当前位置高亮 |
| Agent Terminal | Agent 列表 + 日志 | 当前 Agent 高亮 |

### 8.3 交互优化建议

| 页面 | 当前交互 | 优化建议 |
|-----|---------|---------|
| Kanban Board | 拖拽移动 | 添加拖拽反馈 |
| Workflow Builder | 拖拽节点 | 添加对齐辅助线 |
| Intelligence Chat | 发送消息 | 添加快捷键 |

### 8.4 内容折叠建议

| 页面 | 内容 | 建议 |
|-----|------|------|
| Run Inspector | Agent Call 详情 | 默认折叠，点击展开 |
| Timeline | 事件详情 | 默认折叠，点击展开 |
| Execution Tree | 子节点 | 默认展开前2层 |

### 8.5 渐进式展示建议

| 页面 | 内容 | 建议 |
|-----|------|------|
| Dashboard | Agent 详情 | Hover 显示更多 |
| Kanban Board | 模块详情 | 点击显示 Sheet |
| Artifacts | 产物内容 | 点击预览 |

### 8.6 动画建议

| 页面 | 元素 | 建议 |
|-----|------|------|
| Dashboard | 统计卡片 | 数字递增动画 |
| Execution Center | Phase 进度 | 脉冲动画 |
| Intelligence Chat | 流式响应 | 打字机效果 |
| Observability | 数据刷新 | 渐变动画 |

### 8.7 Skeleton 建议

| 页面 | 元素 | 建议 |
|-----|------|------|
| Dashboard | Agent 卡片 | 6个骨架卡片 |
| Kanban Board | 模块卡片 | 9个骨架卡片 |
| Run Inspector | KPI 卡片 | 8个骨架卡片 |
| Artifacts | 产物网格 | 9个骨架卡片 |

### 8.8 Hover 建议

| 页面 | 元素 | 建议 |
|-----|------|------|
| Dashboard | Agent 卡片 | 高亮边框 |
| Kanban Board | 模块卡片 | 高亮边框 |
| Artifacts | 产物卡片 | 显示操作按钮 |
| Global Runs | 运行行 | 高亮行 |

### 8.9 右键菜单建议

| 页面 | 元素 | 建议 |
|-----|------|------|
| Kanban Board | 模块卡片 | 启动/查看详情/移动 |
| Workflow Builder | 节点 | 编辑/删除/复制 |
| Artifacts | 产物卡片 | 预览/下载/复制路径 |

### 8.10 快捷键建议

| 操作 | 快捷键 | 页面 |
|-----|-------|------|
| 搜索 | ⌘K | 全局 |
| 新建 | ⌘N | 全局 |
| 保存 | ⌘S | Workflow Builder |
| 运行 | ⌘Enter | Execution Center |
| 刷新 | ⌘R | 全局 |

---

## 第九部分：设计原则

### 9.1 视觉原则

1. **Moonlight Iris & Gold（月下魔女 · 月下紫鸢与金）**
   - 主题色：Cyan Magic #22d3ee
   - 强调色：Moonlight Gold #f0c040
   - 背景：Paper Chill #f8fafc（亮色）/ Night Sky #080c14（暗色）

2. **Ghost Border Rule（幽灵边框规则）**
   - 边框使用 10% 透明度
   - 保持界面轻盈

3. **10% Accent Rule（10% 强调规则）**
   - 强调色使用面积不超过 10%
   - 避免视觉疲劳

4. **One Temperature Rule（单一温度规则）**
   - 每个主题保持统一的色温
   - Alice：冷色（Cyan）
   - Aoko：中性色（Blue + Orange）
   - Soujuurou：暖色（Green + Brown）

### 9.2 交互原则

1. **反馈及时**
   - 操作后立即反馈
   - 使用动画过渡

2. **渐进披露**
   - 默认展示核心信息
   - 按需展示详细信息

3. **一致性**
   - 相同操作相同反馈
   - 相同元素相同样式

4. **容错性**
   - 允许撤销操作
   - 提供错误恢复

### 9.3 布局原则

1. **F 型布局**
   - 重要信息放在左上角
   - 次要信息放在右侧

2. **卡片分组**
   - 相关信息放在同一卡片
   - 使用卡片分隔不同区域

3. **响应式设计**
   - 桌面优先
   - 移动端适配

---

## 第十部分：Figma Design Brief

### 10.1 产品定位

**Alice Studio** 是一个 AI Native Agent Platform，让开发者和测试工程师能够编排和管理多个 AI Agent，构建可复用的 Workflow，监控执行状态，分析结果和质量指标。

### 10.2 用户群体

- **测试工程师**: 执行测试、分析结果、管理缺陷
- **QA Lead**: 监控质量、查看报告、管理策略
- **DevOps**: 监控系统、管理部署、查看日志
- **开发者**: 构建 Workflow、调试 Agent、查看执行

### 10.3 页面结构

**全局导航**: 左侧 Sidebar（240px）
- Logo: Alice 有珠
- 实时状态: "● 3 agents running"
- 7个扁平菜单: Dashboard, Workflow, Execution, Memory, Knowledge, Tools, History
- 底部: Settings + 用户信息

**顶部栏**: TopBar（56px）
- 面包屑导航
- 搜索框
- 通知图标
- 时间显示
- 主题切换

**内容区域**: 主内容区（flex-1）

### 10.4 模块关系

```
Dashboard
├── Execution Center
│   ├── Kanban Board
│   ├── Run Inspector
│   └── Agent Terminal
├── Workflow Builder
├── Knowledge Base
│   └── Knowledge Graph
├── Artifacts
├── Reports
│   └── Gap Discovery
├── Timeline
├── Intelligence Chat
├── Observability
└── Settings
```

### 10.5 页面重点

| 页面 | 重点 | 次要 |
|-----|------|------|
| Dashboard | 统计卡片、Agent 列表 | 运行记录、系统状态 |
| Execution Center | 控制栏、Phase 进度 | Agent 执行图、终端 |
| Kanban Board | 模块卡片、拖拽交互 | 模块详情 |
| Run Inspector | KPI 卡片、Timeline | Agent Calls、Logs |
| Intelligence Chat | 消息列表、输入框 | 会话侧边栏 |

### 10.6 组件体系

**基础组件**: Button, Input, Textarea, Card, Badge, Select, Tabs, Separator, ScrollArea, Skeleton

**业务组件**: StatCard, AgentCard, HealthRow, ModuleCard, RunRow, TimelineEvent, LogEntry, MessageBubble

**高级组件**: LiveAgentGraph, TerminalPanel, SwimlaneTimeline, TreeNodeRow, KanbanBoard, ModuleDetailSheet

### 10.7 交互方式

- **点击**: 导航、选择、展开
- **拖拽**: 移动卡片、调整节点
- **Hover**: 显示详情、高亮
- **键盘**: 快捷键操作

### 10.8 设计原则

1. **Moonlight Iris & Gold**: 月下紫鸢与金
2. **Ghost Border**: 幽灵边框
3. **10% Accent**: 10% 强调
4. **One Temperature**: 单一温度

### 10.9 视觉重点

- **主题色**: Cyan Magic #22d3ee
- **强调色**: Moonlight Gold #f0c040
- **背景**: Paper Chill #f8fafc（亮色）/ Night Sky #080c14（暗色）
- **边框**: 10% 透明度

### 10.10 设计禁忌

1. **不要使用过多强调色**
2. **不要使用复杂边框**
3. **不要使用刺眼的颜色**
4. **不要使用不一致的间距**
5. **不要使用不一致的字体**

### 10.11 设计优化建议

**保持现有产品架构，不要重新设计产品逻辑，只优化**:

1. **信息层级**
   - 使用清晰的视觉层次
   - 重要信息突出显示
   - 次要信息弱化处理

2. **交互体验**
   - 添加微交互动画
   - 优化拖拽反馈
   - 添加快捷键支持

3. **视觉系统**
   - 统一颜色使用
   - 统一间距系统
   - 统一字体规范

4. **布局**
   - 优化响应式设计
   - 优化信息密度
   - 优化空间利用

5. **Design System**
   - 统一组件样式
   - 统一组件行为
   - 统一组件文档

6. **组件一致性**
   - 相同组件相同样式
   - 相同组件相同行为
   - 相同组件相同交互

7. **品牌统一性**
   - 统一主题色使用
   - 统一强调色使用
   - 统一背景色使用

### 10.12 最终目标

让整个产品更像：

**一款现代 AI Native Agent Platform，而不是普通后台管理系统。**

---

## 附录：改进建议（Version 2）

### A.1 信息架构优化

**当前问题**:
- 导航层级较深（3级）
- 部分功能入口不明显

**优化建议**:
- 简化导航层级
- 添加快速入口
- 优化搜索功能

### A.2 页面职责优化

**当前问题**:
- Execution Center 职责过重
- 部分页面信息过载

**优化建议**:
- 拆分 Execution Center
- 优化信息展示
- 添加渐进式披露

### A.3 交互优化

**当前问题**:
- 部分交互反馈不及时
- 缺少快捷键支持

**优化建议**:
- 添加微交互动画
- 添加快捷键支持
- 优化拖拽反馈

### A.4 视觉优化

**当前问题**:
- 部分页面视觉层次不清晰
- 部分组件样式不一致

**优化建议**:
- 优化视觉层次
- 统一组件样式
- 优化颜色使用

---

> **文档结束**  
> **版本**: v1.0  
> **日期**: 2026-07-12  
> **作者**: AI Product Designer
