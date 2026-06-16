# 远期路径实施计划书（路径 3 / 4 / 6）

> 版本：v1.0 | 日期：2026-06-12
> 状态：**暂缓执行**，待触发条件满足时启用
> 背景：`PLATFORM_INDEPENDENCE_ROADMAP.md` § 路径 3/4/6
> 当前进展：`IMPLEMENTATION_PLAN_PLATFORM_INDEPENDENCE.md` Phase 1-5

---

## 触发条件总览

| 路径 | 暂缓原因 | 触发信号 | 预计投入 |
|------|---------|---------|:---:|
| 3. LangGraph | ✅ 已启动 (2026-06-13) | 已完成 — 8 Agent StateGraph 替换编排层 | 已完成 |
| 4. Dify 低代码 | 当前无 Web UI / 非开发用户需求 | 手工测试工程师/BA 开始使用时 | 1-2 周 |
| 6. 容器化 | 单团队单机足够 | 多项目并行 / 3+ 团队共用时 | 3-4 周 |

---

## 路径 3：LangGraph 移植计划

### 适用时机

当以下 **≥2 个信号** 同时出现时，启动此路径：
- [ ] 自研 Workflow Engine 的 YAML DAG 无法表达新的条件路由需求
- [ ] bug-analysis 需要「分析→修复→验证」自动循环（最多 N 次）
- [ ] 需要 Human-in-the-loop（人工审批修复方案后继续）
- [ ] 需要时间旅行调试（回溯到某个中间状态重新执行）
- [ ] 需要 LangSmith 可观测性（调用链追踪、Token 统计 Dashboard）

### 实施步骤

#### Step 1：PoC — 用 LangGraph 重写 bug-analysis-agent（预计 3-4 天）

这是风险最低的切入点——只迁移一个 Agent，验证 LangGraph 的增量价值。

**文件**：`aitest/graphs/bug_analysis.py`（新建，~300 行）

**核心图结构**：
```
RAG匹配 → 深度分析 → 路由判断
                ├── 全部已知问题 → 自动修复 → 重新分析（循环）
                ├── 需人工介入 → Human Review → 生成报告
                └── 超过3次 → 放弃 → 生成报告
```

**关键代码骨架**（执行时参考）：
```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict, Literal

class BugAnalysisState(TypedDict):
    failures: list[dict]
    rag_matches: list[dict]
    root_causes: list[str]
    fix_attempts: int
    human_approved: bool
    final_report: str

builder = StateGraph(BugAnalysisState)
# ... 添加节点和边 ...
graph = builder.compile(
    checkpointer=SqliteSaver(...),
    interrupt_before=["human_review"]
)
```

**依赖**：`pip install langgraph langchain-core langchain-community`

#### Step 2：对比评估（预计 1 天）

- 用同一个模块的失败用例，分别跑自研 Workflow Engine 和 LangGraph 版本
- 评估维度：执行时间、Token 消耗、修复成功率、代码复杂度
- **决策门禁**：LangGraph 版本在至少 2 个维度上明显优于自研版本，才继续 Step 3

#### Step 3：渐进迁移其余 Agent（预计 1-2 周）

仅当 Step 2 通过后才执行。迁移顺序：
1. test-design-agent（简单串行，验证基本模式）
2. automation-agent（中等复杂，含 code-consistency-checker 机械化步骤）
3. full-sop（顶层编排图，组合子图）

#### Step 4：废弃自研 Workflow Engine 的 LangGraph 覆盖部分

保留自研 Workflow Engine 用于简单 YAML DAG 场景，LangGraph 用于复杂场景。两者共存而非完全替换。

### 验收标准

- [ ] bug-analysis-agent 在 LangGraph 上运行，支持「分析→修复→验证」最多 3 次循环
- [ ] Human-in-the-loop：修复方案需人工确认后才执行
- [ ] LangSmith Dashboard 可见完整调用链
- [ ] Token 消耗和修复成功率不低于自研版本

---

## 路径 4：Dify 低代码编排计划

### 适用时机

当以下 **≥1 个信号** 出现时，启动此路径：
- [ ] 手工测试工程师开始询问「这个页面怎么测」
- [ ] 业务 BA 想查看测试覆盖率趋势
- [ ] 运维团队想在值班时快速排查失败（需要 Web UI）
- [ ] 管理层想看月度测试报告（需要定时生成 + 推送）

### 实施步骤

#### Step 1：Dify 部署 + 知识库导入（预计 1 天）

```bash
# Docker 部署 Dify 社区版
docker compose -f docker-compose.yaml up -d

# 导入知识库
# 1. 文档知识库：上传 PROJECT_CONTEXT.md（自动分块+向量化）
# 2. 结构化知识库：导入 known-issues.yaml
```

#### Step 2：核心工作流迁移（预计 2-3 天）

按优先级迁移以下工作流：

| 优先级 | Dify 工作流 | 对应现有能力 | 目标用户 |
|:---:|------|------|------|
| P0 | Bug 分析工作流 | bug-analysis Skill | 运维/值班 |
| P1 | 测试报告生成 | report-generator Skill | 管理层 |
| P2 | 页面分析工作流 | page-analysis Skill | 手工测试工程师 |
| P3 | 代码生成工作流 | page-object-generator Skill | 测试开发（CLI 更高效，优先级低） |

**Bug 分析工作流设计**（Dify 可视化节点）：
```
触发: Webhook (Jenkins) 或 手动输入
  → LLM 节点: 解析失败日志（系统提示词 = bug-analysis.md）
  → 知识检索节点: RAG 搜索 known-issues
  → 条件分支: 匹配到已知问题？
      ├── 是 → 输出修复方案
      └── 否 → LLM 深度分析 → 输出分析报告
  → 通知节点: 飞书/钉钉/邮件推送结果
```

#### Step 3：Skill 内容适配（预计 1 天）

将 28 个 Skill Markdown 中的 **高频使用 Skill** 转换为 Dify 的 Prompt 模板格式：
- Dify 的 `{{variable}}` 语法替代原有参数占位符
- 分段提示词（System / User / Assistant 角色分离）
- 测试验证：同一输入，Dify 输出 vs Claude Code 输出对比

#### Step 4：权限 + 多用户配置（预计 0.5 天）

- 测试工程师：可触发所有工作流
- 手工测试工程师：可触发页面分析 + 测试用例生成
- 管理层：只读 Dashboard

### 验收标准

- [ ] 非开发用户可通过 Web 表单输入「模块名 + 页面名」触发页面分析
- [ ] Bug 分析工作流支持 Webhook 自动触发（模拟 Jenkins 回调）
- [ ] 月度报告可通过定时任务自动生成
- [ ] 至少 3 个核心 Skill 在 Dify 上的输出质量不低于 Claude Code

---

## 路径 6：容器化 + 消息队列计划

### 适用时机

当以下 **≥2 个信号** 同时出现时，启动此路径：
- [ ] 同时有 3+ 个模块在并行测试
- [ ] 多个团队共享同一套 Agent 能力
- [ ] Agent 执行耗时影响其他服务稳定性
- [ ] 需要不同 Agent 使用不同 LLM（test-design 用 Claude，automation 用 GPT-4o，bug-analysis 用本地模型）
- [ ] 需要独立扩缩容（automation-agent 高峰期需要 5 个 Worker）

### 架构设计

```
Kubernetes Cluster / Docker Compose
│
├── ingress-nginx → API Gateway (FastAPI, 2 replicas)
│
├── Redis (消息队列 + 结果缓存)
│   ├── Queue: agent.tasks         ← Celery 任务队列
│   └── Cache: agent.results       ← 执行结果临时存储
│
├── Celery Workers (HPA 自动扩缩容)
│   ├── test-design-worker    (1-2 replicas, GPU node)
│   │   └── LLM: Claude Sonnet（结构化分析最优）
│   ├── automation-worker     (2-5 replicas, CPU node)
│   │   └── LLM: GPT-4o（代码生成能力强）
│   ├── execution-worker      (1 replica, needs Selenium Grid)
│   │   └── 无需 LLM（调用 pytest）
│   ├── bug-analysis-worker   (1-2 replicas, GPU node)
│   │   └── LLM: 本地 Qwen3（敏感日志不出内网）
│   └── report-worker         (1 replica, CPU node)
│       └── 无需 LLM（数据聚合 + Excel 生成）
│
├── PostgreSQL
│   ├── Context 版本化存储（替代 Markdown 文件？保留文件优先）
│   ├── Bug 历史库（已建：aitest/bug_history.py → SQLite）
│   └── 用户/权限管理
│
├── ChromaDB (向量检索，单副本)
│
└── MinIO (截图 + Allure 报告对象存储)
```

### 实施步骤

#### Phase 1：容器化现有服务（预计 3-4 天）

```dockerfile
# Dockerfile — 通用 Agent Worker 镜像
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY aitest/ aitest/
COPY governance/skills/ governance/skills/
COPY governance/context/ governance/context/
CMD ["celery", "-A", "aitest.tasks", "worker", "--loglevel=info"]
```

```yaml
# docker-compose.yaml — 开发环境
services:
  api:
    build: .
    command: uvicorn aitest.server.main:app --host 0.0.0.0
    ports: ["8000:8000"]
  redis:
    image: redis:7-alpine
  worker-test-design:
    build: .
    command: celery -A aitest.tasks worker -Q test-design
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
  worker-automation:
    build: .
    command: celery -A aitest.tasks worker -Q automation
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
  chromadb:
    image: chromadb/chroma
```

#### Phase 2：Celery 任务队列集成（预计 2-3 天）

```python
# aitest/tasks.py（新建）

from celery import Celery
app = Celery('aitest', broker='redis://localhost:6379/0')

@app.task(bind=True, max_retries=2)
def run_agent_task(self, agent_name: str, module: str, page: str = None, provider: str = "claude"):
    """异步执行 Agent。"""
    from aitest.agent_runner import run_agent
    try:
        result = run_agent(agent_name=agent_name, module=module, page=page, provider=provider, verbose=False)
        return result
    except Exception as e:
        self.retry(exc=e, countdown=60)
```

```python
# aitest/server/api/agents.py — 改为异步触发

@router.post("/run")
async def trigger_agent(req: AgentRunRequest):
    from aitest.tasks import run_agent_task
    task = run_agent_task.delay(req.agent, req.module, req.page, req.provider)
    return {"status": "queued", "task_id": task.id, "agent": req.agent}

@router.get("/status/{task_id}")
async def task_status(task_id: str):
    from aitest.tasks import run_agent_task
    task = run_agent_task.AsyncResult(task_id)
    return {"task_id": task_id, "status": task.status, "result": task.result if task.ready() else None}
```

#### Phase 3：按 Agent 分 Queue（预计 1 天）

不同 Agent 绑定不同 LLM Provider，通过 Celery Queue 路由：

```python
# Agent → Queue 映射
AGENT_QUEUE_MAP = {
    "test-design-agent": "test-design",    # Claude 专用
    "automation-agent":  "automation",     # GPT-4o 专用
    "bug-analysis-agent":"bug-analysis",   # 本地 Ollama 专用
    "execution-agent":   "execution",      # 无需 LLM
    "report-agent":      "report",         # 无需 LLM
}
```

#### Phase 4：Kubernetes 部署（预计 2-3 天，仅生产环境需要）

- Helm Chart 编写
- HPA（Horizontal Pod Autoscaler）配置
- ConfigMap / Secret 管理（API Key 等）
- 健康检查 + 就绪探针

### 验收标准

- [ ] `docker compose up` 一键启动全部服务
- [ ] `POST /api/agent/run` 立即返回 task_id，Agent 后台异步执行
- [ ] `GET /api/agent/status/{task_id}` 可查询进度
- [ ] 不同 Agent 任务路由到不同 Queue（Claude / OpenAI / Ollama 隔离）
- [ ] Selenium Grid 集成（execution-agent Worker 能够调度浏览器测试）

---

## 决策矩阵（快速判断何时启动哪条路径）

| 你遇到的情况 | 启动路径 |
|-------------|:---:|
| 「bug-analysis 需要自动修复并重新测试，修复失败再修复」 | 路径 3 |
| 「手工测试同事问我能不能帮他也分析页面」 | 路径 4 |
| 「两个模块同时在跑 full-sop，CLI 卡住了」 | 路径 6 |
| 「需要 LangSmith 看每次 Agent 调用的 Token 和延迟」 | 路径 3 |
| 「领导问能不能在网页上看测试进度」 | 路径 4 |
| 「需要 bug-analysis-agent 用内网 Ollama 保护日志隐私」 | 路径 6 |
| 「并行 5 个页面生成代码，sequential 太慢了」 | 路径 6 |
| 「想让 GPT-4o 写代码、Claude 做分析，各取所长」 | 路径 6 |

---

> **如何启用此计划书**：当触发条件满足时，将本文件 + `PLATFORM_INDEPENDENCE_ROADMAP.md` 一起交给 AI 会话，说明「启动路径 X」，AI 会按照上述步骤执行。
