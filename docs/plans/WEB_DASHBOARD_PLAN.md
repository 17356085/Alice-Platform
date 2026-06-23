# Web Dashboard 实施计划

> 版本：v1.0 | 日期：2026-06-12
> 状态：**暂缓**，路径 5 剩余 10%
> 前提：路径 5 已建成 16 API 端点 + CLI Dashboard，Web Dashboard 在此基础上做可视化

---

## 前置 API（已就绪）

Web Dashboard 是已有 API 的可视化层，不需要新增后端接口。现有 16 个端点直接可用：

| API | 用途 | Dashboard 对应 |
|-----|------|---------------|
| `GET /api/agent/status/{module}` | 模块 SOP 进度 | 模块状态卡片 |
| `GET /api/agent/queue` | 任务队列统计 | 任务队列面板 |
| `GET /api/bugs/trends?module=` | Bug 趋势 | 趋势折线图 |
| `GET /api/bugs/list?status=open` | 未修复 Bug | Bug 列表 |
| `GET /health` | RAG + 队列综合状态 | 顶部状态栏 |

---

## 页面设计

```
┌──────────────────────────────────────────────────────────┐
│  AITest Platform                             [健康: OK]  │
│  dashboard  │  modules  │  bugs  │  tasks  │  reports    │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│  │ Modules     │ │ Task Queue  │ │ RAG Status  │        │
│  │  10 active  │ │  2 queued   │ │ 5 coll/242d │        │
│  │   2 done    │ │  0 running  │ │              │        │
│  └─────────────┘ └─────────────┘ └─────────────┘        │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Module SOP Progress                              │   │
│  │                                                  │   │
│  │ equipment  ████████████████░░░░  80% Phase 4     │   │
│  │ tank       ████████████████████ 100% Complete    │   │
│  │ personnel  ██████░░░░░░░░░░░░░░  30% Phase 2     │   │
│  │ ...                                              │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────┐ ┌──────────────────────────┐   │
│  │ Bug Trends (30d)    │ │ Recent Tasks             │   │
│  │   ▲                 │ │ [OK] test-design 2m ago  │   │
│  │  ─┤─╲               │ │ [>>] automation  running │   │
│  │    ╲ ───           │ │ [XX] bug-analysis 1h ago │   │
│  │                     │ │ [..] report       queued │   │
│  └─────────────────────┘ └──────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Quick Actions                                    │   │
│  │ [Run full-sop ▾] [module: equipment ▾] [Go]     │   │
│  │ [Run bug-analysis ▾] [module: tank ▾] [Go]      │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 页面清单

| 路由 | 内容 | 核心组件 |
|------|------|---------|
| `/` | 总览 Dashboard | 统计卡片 + 进度条 + 趋势图 + 快速操作 |
| `/modules` | 模块列表 + 各模块 SOP 详情 | 表格 + 展开详情面板 |
| `/modules/:name` | 单模块详情（所有页面文档状态 + 代码覆盖率） | 文件树 + 进度指示 |
| `/bugs` | Bug 列表 + 筛选 + 趋势图 | 表格 + 折线图 |
| `/tasks` | 任务队列（实时刷新） | 实时列表 + 操作按钮 |
| `/reports` | 测试报告列表（Allure 链接 + Excel 下载） | 卡片列表 |

---

## 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| 框架 | React 18 + Vite | 轻量，生态丰富 |
| UI 库 | shadcn/ui 或 Ant Design | shadcn 更轻量，AntD 表格/图表开箱即用 |
| 图表 | Recharts 或 ECharts | Recharts 更 React 化，ECharts 图表种类更全 |
| 状态管理 | React Query (TanStack) | 自动缓存 API 响应 + 后台刷新 |
| 路由 | React Router v6 | 标准选择 |
| 部署 | 静态文件挂载到 FastAPI `/dashboard` 下 | 无需独立服务 |

---

## 实施步骤

### Step 1：项目脚手架（0.5 天）

```bash
npm create vite@latest dashboard -- --template react-ts
cd dashboard
npm install react-router-dom @tanstack/react-query recharts antd
```

目录结构：
```
aitest/server/ui/
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx      # 总览
│   │   ├── Modules.tsx        # 模块列表
│   │   ├── ModuleDetail.tsx   # 单模块详情
│   │   ├── Bugs.tsx           # Bug 管理
│   │   └── Tasks.tsx          # 任务队列
│   ├── components/
│   │   ├── StatCard.tsx       # 统计卡片
│   │   ├── ProgressBar.tsx    # 进度条
│   │   ├── TrendChart.tsx     # 趋势图
│   │   ├── TaskList.tsx       # 任务列表
│   │   └── QuickAction.tsx    # 快速操作
│   ├── hooks/
│   │   └── useApi.ts          # API 调用封装
│   └── types/
│       └── index.ts           # TypeScript 类型定义
├── package.json
└── vite.config.ts
```

### Step 2：核心页面开发（3-5 天）

按优先级：

| 优先级 | 页面 | 耗时 | 依赖 API |
|:---:|------|:---:|------|
| P0 | Dashboard 总览 | 1 天 | `/health`, `/api/agent/queue`, `/api/agent/list` |
| P0 | 模块列表 + SOP 进度 | 1 天 | `/api/agent/status/{module}` |
| P1 | Bug 趋势 + 列表 | 1 天 | `/api/bugs/trends`, `/api/bugs/list` |
| P1 | 任务队列（实时） | 0.5 天 | `/api/agent/queue`, `/api/agent/task/{id}` |
| P2 | 单模块详情 | 1 天 | `/api/agent/status/{module}` |
| P2 | 快速操作 | 0.5 天 | `/api/agent/run`, `/api/workflow/run` |

### Step 3：集成到 FastAPI（0.5 天）

```python
# aitest/server/main.py
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# 生产构建后挂载静态文件
UI_DIR = Path(__file__).parent / "ui" / "dist"
if UI_DIR.exists():
    app.mount("/dashboard", StaticFiles(directory=str(UI_DIR), html=True), name="dashboard")
```

开发时前端独立运行 `npm run dev`，生产时 `npm run build` 后由 FastAPI 托管。

### Step 4：Jenkins 构建集成（0.5 天）

```groovy
// Jenkinsfile 中增加
stage('Build Dashboard') {
    steps {
        dir('aitest/server/ui') {
            bat 'npm ci'
            bat 'npm run build'
        }
    }
}
```

---

## 验收标准

- [ ] 浏览器打开 `http://localhost:8000/dashboard` 看到总览面板
- [ ] 模块列表显示所有模块的 SOP 进度（进度条/百分比）
- [ ] Bug 趋势图从 API 拉取数据（30 天范围内）
- [ ] 任务队列每 5 秒自动刷新
- [ ] 快速操作可触发 Agent 执行（调用 `POST /api/agent/run`）
- [ ] 页面在移动端也能基本查看（响应式布局）

---

## 与 CLI Dashboard 的分工

| 场景 | 推荐入口 |
|------|---------|
| 开发/调试时快速查看状态 | `aitest dashboard` |
| 给领导/同事展示进度 | Web Dashboard |
| 值班时监控任务队列 | Web Dashboard（自动刷新） |
| CI 完成后查看报告 | Web Dashboard |
| 写脚本/自动化流程 | CLI + API |

---

> **如何启用此计划**：将此文件交给 AI 会话，说明「启动 Web Dashboard 开发」，AI 按照 Step 1→2→3→4 执行。
