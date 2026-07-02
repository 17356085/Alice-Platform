# Engine Demo Guide

> 架构解耦分析 — 文档 6/7 (最重要)
> 核心问题: **Platform 一个模块都没有的时候，怎么启动 Engine？**
> 注: 07 提供从当前代码到四层架构的迁移地图

## 1. 这份文档要回答什么

两个问题:

> 1. Engine 怎么知道"测什么"？(URL、技术栈、框架)
> 2. Platform 全删时怎么启动？

## 2. Engine 怎么知道测什么

### 2.1 答案: project.yaml

Engine 不猜。你告诉它。

```yaml
# .tlo/project.yaml — 项目的"身份证"
project:
  id: "web-automation"
  name: "鞍集涂源管理系统"

application:
  type: "web"                    # ← 什么技术? Web 应用
  runtime: "browser"             # ← 用什么跑? 浏览器

connection:
  base_url: "https://aiwechatminidemo.cimc-digital.com/"  # ← 测什么 URL?
  login_required: true           # ← 需要登录?
  login_method: "form"           # ← 怎么登录? 表单

test_project:
  type: "pytest-selenium"        # ← 用什么框架? Pytest + Selenium
  code_path: "../ZJSN_Test-master526"  # ← 测试代码在哪?
  page_objects_path: "page/"
  scripts_path: "script/"
```

### 2.2 信息流

```
project.yaml (你写的)
    │
    ▼
ProjectContext (读配置)
    │
    ├── .sut_url()           → "https://aiwechatminidemo.cimc-digital.com/"
    ├── .sut_type()          → "web"
    ├── .config.test_project_type → "pytest-selenium"
    ├── .list_modules()      → ["equipment", "tank", "production", ...]
    └── .list_pages("equipment") → ["alarm-config", "camera", "key-param", ...]
            │
            ▼
    Engine.run(project, module, pages)
            │
            ▼
    SOP Graph → AgentLoop → LLM → 产物
```

### 2.3 每个问题的答案

| 问题 | 答案来源 | 示例 |
|------|----------|------|
| **测什么项目?** | `project.yaml` → `project.id` | `web-automation` |
| **目标 URL?** | `project.yaml` → `connection.base_url` | `https://aiwechatminidemo.cimc-digital.com/` |
| **什么技术?** | `project.yaml` → `application.type` | `web` (Vue 3 + Element Plus) |
| **什么框架?** | `project.yaml` → `test_project.type` | `pytest-selenium` |
| **代码在哪?** | `project.yaml` → `test_project.code_path` | `../ZJSN_Test-master526` |
| **需要登录?** | `project.yaml` → `connection.login_required` | `true` |
| **有哪些模块?** | `.tlo/knowledge/modules/` 目录扫描 | `equipment`, `tank` |
| **有哪些页面?** | `.tlo/knowledge/modules/<m>/pages/` 扫描 | `alarm-config`, `camera` |

### 2.4 实际例子

```bash
# 项目目录结构
ZJSN_Test-master526/
├── .tlo/
│   ├── project.yaml              ← 项目配置 (URL, 技术, 框架)
│   └── knowledge/
│       └── modules/
│           ├── equipment/        ← 模块
│           │   └── pages/
│           │       ├── alarm-config/  ← 页面
│           │       │   └── PAGE_CONTEXT.md
│           │       ├── camera/
│           │       └── key-param/
│           ├── tank/
│           └── production/
├── page/                         ← Page Object 代码
│   ├── equipment_page/
│   ├── tank_page/
│   └── production_page/
└── script/                       ← 测试脚本
    ├── equipment/
    ├── tank/
    └── production/
```

Engine 读 `project.yaml` 知道:
- URL: `https://aiwechatminidemo.cimc-digital.com/`
- 技术: Web (Vue 3)
- 框架: pytest-selenium

Engine 扫 `.tlo/knowledge/modules/` 知道:
- 模块: equipment, tank, production
- 页面: alarm-config, camera, key-param

### 2.5 Engine 接口 (修正后)

```python
# 当前 (缺了 project 信息)
engine.run("equipment", ["alarm-config"])

# 应该是
engine.run(
    project="web-automation",    # ← 测什么项目 (对应 project.yaml)
    module="equipment",          # ← 测什么模块
    pages=["alarm-config"],      # ← 测什么页面
)

# 或者: 只给项目，自动发现模块和页面
engine.run(project="web-automation")
```

## 3. 最小启动清单

### 3.1 启动 Engine 需要什么

```
必须有:
  1. Python 3.10+
  2. .env (至少一个 LLM API Key)
  3. .tlo/project.yaml (项目配置: URL, 技术, 框架)
  4. governance/ (Agent 定义 + Skill 提示)
  5. .tlo/knowledge/modules/ (模块+页面目录)

不需要:
  ✗ Web API (server/)
  ✗ Dashboard (web/)
  ✗ Database
  ✗ Redis
  ✗ ChromaDB
  ✗ Docker
  ✗ 任何 Platform 模块
```

### 3.2 目录结构 (最小)

```
workstudy/
├── .env                              ← API Key
├── .tlo/
│   ├── project.yaml                  ← 项目配置 (URL, 技术, 框架)
│   └── knowledge/
│       └── modules/
│           └── equipment/
│               └── pages/
│                   └── alarm-config/
│                       └── PAGE_CONTEXT.md
├── governance/
│   ├── agents/                       ← Agent 定义 YAML
│   ├── skills/                       ← Skill 提示 .md
│   └── context/
│       └── shared-language.md
├── aitest/                           ← Engine 代码
│   ├── engine/
│   ├── graphs/
│   ├── agents/
│   ├── llm/
│   └── config.py
└── demo.py                           ← 入口
```

### 3.3 project.yaml 最小配置

```yaml
# .tlo/project.yaml
project:
  id: "my-project"
  name: "我的测试项目"

application:
  type: "web"
  runtime: "browser"

connection:
  base_url: "https://example.com/"    # ← 被测系统 URL

test_project:
  type: "pytest-selenium"
```

### 3.4 .env 最小配置

```bash
# 只需要一个 LLM API Key
ANTHROPIC_API_KEY=sk-ant-...
```

## 4. 三种启动方式

### 4.1 方式一: Python API (最直接)

```python
from aitest.engine import Engine

engine = Engine()

# 指定项目、模块、页面
result = engine.run(
    project="web-automation",
    module="equipment",
    pages=["alarm-config"],
)

print(result["status"])             # "completed"
print(result["completed_phases"])   # ["Project Init", "Requirement", ...]
```

### 4.2 方式二: demo.py CLI (最完整)

```bash
# 指定项目
python demo.py --project web-automation --module equipment --pages alarm-config

# 只给项目，自动发现模块和页面
python demo.py --project web-automation

# Mock LLM (不调 API，验证流程)
python demo.py --project web-automation --module equipment --mock-llm

# 带 Extension
python demo.py --project web-automation --module equipment --extensions audit

# Dry run (只看计划)
python demo.py --project web-automation --module equipment --dry-run
```

### 4.3 方式三: 交互式 (给领导演示)

```bash
python demo.py --interactive
```

交互流程:

```
$ python demo.py --interactive

  ╔══════════════════════════════════════╗
  ║     AITest Engine — Standalone       ║
  ╚══════════════════════════════════════╝

  扫描项目配置...
  发现项目: web-automation (鞍集涂源管理系统)
    URL: https://aiwechatminidemo.cimc-digital.com/
    技术: web (Vue 3 + Element Plus)
    框架: pytest-selenium

  发现模块: equipment, tank, production, dcs, ...

  请选择模块: equipment
  请选择页面 (留空=全部): alarm-config, camera

  📋 执行计划:
    项目: web-automation
    URL:  https://aiwechatminidemo.cimc-digital.com/
    模块: equipment
    页面: alarm-config, camera
    模式: full
    预计 Phase: 9 个
    预计耗时: ~3 分钟

  确认执行? [Y/n] y

  🚀 启动 Engine...

  [1/9] Project Init          ✅ 3.2s
  [2/9] Requirement            ✅ 8.1s
  [3/9] Test Design            ✅ 12.4s
  [4/9] Automation             ✅ 15.7s
  [5/9] Execute & Debug        ✅ 22.3s
  [6/9] Report                 ✅ 5.1s
  [7/9] Knowledge              ✅ 3.8s
  [8/9] Data Sanitization      ✅ 1.2s

  ✅ 执行完成! 总耗时: 71.8s

  📄 产物:
    - .tlo/runtime/sop-status/SOP_STATUS_equipment.json
    - .tlo/knowledge/modules/equipment/pages/alarm-config/PAGE_CONTEXT.md
    - .tlo/knowledge/modules/equipment/pages/camera/PAGE_CONTEXT.md

  继续测试其他模块? [Y/n] n
  👋 再见!
```

## 5. 端到端演示脚本

### 5.1 一键演示 (给领导看)

```bash
#!/bin/bash
# demo_e2e.sh — 一键演示 Engine 能力

echo "=========================================="
echo "  AITest Engine — Standalone Demo"
echo "=========================================="

# Step 1: 环境检查
echo ""
echo "📋 Step 1: 环境检查"
python -c "from aitest.engine import Engine; print('  ✅ Engine 可用')" || exit 1

# Step 2: 展示项目配置
echo ""
echo "📋 Step 2: 项目配置"
cat .tlo/project.yaml
echo ""

# Step 3: Dry Run
echo ""
echo "📋 Step 3: Dry Run (查看执行计划)"
python demo.py --project web-automation --module equipment --pages alarm-config --dry-run

# Step 4: Mock LLM 执行
echo ""
echo "📋 Step 4: Mock LLM 执行 (不调 API)"
python demo.py --project web-automation --module equipment --pages alarm-config --mock-llm

# Step 5: 真实执行 (如果 API Key 可用)
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "📋 Step 5: 真实 LLM 执行"
    python demo.py --project web-automation --module equipment --pages alarm-config
else
    echo ""
    echo "📋 Step 5: 跳过 (无 ANTHROPIC_API_KEY)"
fi

echo ""
echo "=========================================="
echo "  Demo 完成!"
echo "=========================================="
```

### 5.2 给领导的 5 分钟演示

```bash
# 准备 (提前做)
cd /d/Desktop/Alice
export ANTHROPIC_API_KEY=sk-ant-...

# 演示 1: 展示项目配置 (30秒)
echo "=== 被测系统 ==="
cat .tlo/project.yaml

# 演示 2: 展示 Engine 存在 (30秒)
python -c "from aitest.engine import Engine; print('Engine ready ✅')"

# 演示 3: 展示执行计划 (30秒)
python demo.py --project web-automation --module equipment --dry-run

# 演示 4: 展示完整执行 (3分钟)
python demo.py --project web-automation --module equipment --pages alarm-config

# 演示 5: 展示结果 (30秒)
cat .tlo/runtime/sop-status/SOP_STATUS_equipment.json | python -m json.tool
```

## 6. 常见问题

### 6.1 "Engine 怎么知道测什么 URL?"

从 `project.yaml` 读:

```yaml
connection:
  base_url: "https://aiwechatminidemo.cimc-digital.com/"
```

Engine 内部通过 `ProjectContext.sut_url()` 获取。

### 6.2 "Engine 怎么知道用什么技术?"

从 `project.yaml` 读:

```yaml
application:
  type: "web"              # Web 应用
  runtime: "browser"       # 用浏览器测试

test_project:
  type: "pytest-selenium"  # 用 Pytest + Selenium
```

Engine 根据这些信息选择对应的:
- Page Object 模板
- 测试脚本模板
- 断言策略
- 等待策略

### 6.3 "Engine 怎么知道有哪些页面?"

扫描 `.tlo/knowledge/modules/` 目录:

```
.tlo/knowledge/modules/
├── equipment/
│   └── pages/
│       ├── alarm-config/    ← 自动发现
│       ├── camera/          ← 自动发现
│       └── key-param/       ← 自动发现
├── tank/
│   └── pages/
│       └── ...
```

或者在 `engine.run()` 中显式指定:

```python
engine.run(project="web-automation", module="equipment", pages=["alarm-config"])
```

### 6.4 "没有 API Key 怎么办?"

```bash
python demo.py --project web-automation --module equipment --mock-llm
```

Mock LLM 不调用真实 API，但走完整 SOP 流程。

### 6.5 "没有 project.yaml 怎么办?"

创建一个:

```yaml
# .tlo/project.yaml
project:
  id: "my-project"
  name: "我的项目"

connection:
  base_url: "https://your-app.com/"

application:
  type: "web"
  runtime: "browser"

test_project:
  type: "pytest-selenium"
```

### 6.6 "Engine 和 aitest server start 有什么区别?"

```
aitest server start:
  Engine + Web API + Dashboard + Session + Auth + ...
  需要启动 HTTP 服务
  需要浏览器访问

python demo.py:
  Engine only
  直接在终端运行
  不需要 HTTP、不需要浏览器
```

## 7. 验收标准

给领导演示时，只需要证明:

```bash
# 输入
python demo.py --project web-automation --module equipment --pages alarm-config

# 输出 (预期)
📋 项目: web-automation (鞍集涂源管理系统)
   URL: https://aiwechatminidemo.cimc-digital.com/
   技术: web (Vue 3 + Element Plus)

✅ completed
Run ID: engine-a1b2c3d4
耗时: 45.2s
已完成 Phase (9):
  ✅ Project Init
  ✅ Requirement
  ✅ Test Design
  ✅ Automation
  ✅ Execute & Debug
  ✅ Report
  ✅ Knowledge
  ✅ Data Sanitization
处理页面 (1):
  📄 alarm-config
```

**这就够了。**

不需要 Dashboard。不需要 Web API。不需要 Database。

一个 project.yaml + 一个命令 = 一次完整执行。

这就是 Engine。

## 8. 已知限制

| 限制 | 原因 | 解决方案 |
|------|------|----------|
| 需要网络调用 LLM | API Key + 网络 | `--mock-llm` 模式 |
| 需要 project.yaml | 项目配置 | 创建最小配置 |
| 需要 governance 文件 | Agent/Skill 定义 | 从现有项目复制 |
| 需要模块目录 | 页面产物路径 | 自动创建最小目录 |
| 产物写到本地文件系统 | 无抽象层 | 未来加 Filesystem Adapter |
| 无法并发执行多个任务 | 单次执行设计 | 用 Platform 的 ExecutionService |
| 无法查看执行历史 | 无 RunStore | 用 Platform 的 RunStore |

## 9. 这份文档的真正价值

不是教你用 demo.py。

而是证明一个事实:

> **Engine 是一个独立的产品。**
>
> Platform 是它的附加层，不是它的前提条件。

就像:

- Docker 没有 Docker Desktop 也能跑
- Kubernetes 没有 Rancher 也能跑
- LangGraph 没有 LangGraph Platform 也能跑

**Engine 先于 Platform。永远。**
