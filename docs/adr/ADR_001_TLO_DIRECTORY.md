# ADR-001: `.tlo` 项目目录设计

> 状态: 已决议 | 日期: 2026-06-23 | 基于 ChatGPT 方案修订

---

## 背景

AITest 从测试项目演进为 AI Test Platform。平台需要与项目完全解耦。
项目数据应跟随项目，不跟随平台。

## 核心原则

### 原则 1: 项目上下文属于项目

> **项目上下文属于项目，不属于平台。**

`git clone` → `.tlo/` 跟随 → TLO 自动恢复上下文。

### 原则 2: Source of Truth

> **任何 AI 可推导的数据，都不应成为唯一事实来源。**

```
Markdown 文档（knowledge/modules/）    ← Source of Truth
        │
        ▼
Knowledge Builder（AI 推导）
        │
        ▼
graph.json / vector index / embedding  ← Derived Data
```

- `knowledge/modules/*.md` → 真实知识，Agent 读写，Git 跟踪
- `graph.json` / `index/` / `embedding` → 派生加速层，可随时删除重建
- `cache/` → 同理，`rm -rf` 后平台自动恢复

这确保 Agent（Discovery / Planner / Navigator / Knowledge Builder）职责边界清晰，
避免多个知识副本互相漂移。

---

## 目录结构

```text
project/
├── src/                         # 业务源码
├── tests/ / script/             # 测试代码
│
└── .tlo/
    │
    ├── project.yaml              # 项目配置（唯一入口）
    │
    ├── knowledge/                # Project Knowledge — Git ✅
    │   ├── MODULE_INDEX.md       # 模块索引
    │   └── modules/
    │       └── <module>/
    │           ├── MODULE_CONTEXT.md
    │           └── pages/
    │               └── <page>/
    │                   ├── PAGE_CONTEXT.md
    │                   ├── PAGE_INTERFACE.yaml
    │                   ├── RISK_MODEL.md
    │                   ├── TEST_CASES.md
    │                   └── TEST_DESIGN.md
    │
    ├── context/                  # AI 理解 — Git ✅（可选）
    │   ├── PROJECT_CONTEXT.md    # 项目摘要
    │   ├── decisions.md          # 架构决策记录
    │   └── conversations/        # 重要对话存档
    │
    ├── graph/                    # 派生数据 — Git ❌
    │   ├── knowledge-graph.json  # 从 knowledge/ 自动构建
    │   └── vector.index          # 向量索引
    │
    ├── runtime/                  # 运行状态 — Git ❌
    │   ├── sop-status/
    │   │   └── SOP_STATUS_<module>.json
    │   ├── session.json
    │   └── checkpoints/
    │
    ├── artifacts/                # AI 产物 — Git 按需
    │   ├── reports/
    │   ├── generated-tests/
    │   └── analysis/
    │
    └── cache/                    # 临时缓存 — Git ❌
        ├── discovery/
        │   ├── pages.json
        │   └── menu_tree.json
        ├── screenshots/
        └── embeddings/
```

---

## ChatGPT 方案的改动点

| ChatGPT 方案 | 修订 | 理由 |
|---|---|---|
| `knowledge/` 放 JSON 文件 | 改为嵌套 markdown（同当前结构） | 当前 Agent 读写 .md 文件，JSON 是未来目标 |
| 无 modules/ 子目录 | 保留 `knowledge/modules/<m>/pages/<p>/` 层次 | SOP 各 Phase 产出按模块/页面组织 |
| `context/` 放摘要+记忆 | 保留，增加 `PROJECT_CONTEXT.md` | 与当前 platform 已有文件兼容 |
| 无 `project.yaml` 详细定义 | 保留现有字段 + 新增平台字段 | 见下方 schema |
| `runtime/sop_status.json` | 改为 `runtime/sop-status/` 目录多文件 | 一个模块一个文件，避免单文件膨胀 |

---

## `project.yaml` Schema

```yaml
# .tlo/project.yaml — 项目对平台的唯一声明

version: 1

project:
  id: "web-automation"
  name: "鞍集涂源管理系统"
  type: "web"                     # web | miniapp | api

connection:
  base_url: "https://..."
  login_required: true
  login_method: "form"

test:
  type: "pytest-selenium"         # pytest-selenium | jest-miniprogram | playwright
  page_objects: "page/"
  scripts: "script/"

runtime:
  engine: "langgraph"
  provider: "claude"

# 未来扩展:
# agents:
# knowledge:
```

Schema 保持最小化。字段按需添加，不影响已有 Agent。

---

## 生命周期划分

| 类型 | 位置 | Git | 可删除 | 说明 |
|------|------|:---:|:---:|------|
| 项目配置 | `project.yaml` | ✅ 建议 | ❌ | 唯一手工维护的配置 |
| Project Knowledge | `knowledge/` | ✅ 建议 | ❌ | SOP Phase 1-3 产出，Agent 读写，**Source of Truth** |
| AI Context | `context/` | ✅ 可选 | ❌ | AI 对项目的理解与决策 |
| Knowledge Graph | `graph/` | ❌ | ✅ | 从 knowledge/ 派生，可重建 |
| Runtime | `runtime/` | ❌ | ✅ | SOP 执行进度，可重建 |
| Artifacts | `artifacts/` | ⚠️ 按需 | ✅ | AI 生成的报告/脚本 |
| Cache | `cache/` | ❌ | ✅ | `rm -rf` 后平台自动重建 |

---

## 平台端保留

```text
WorkStudy/                       ← 平台安装目录
├── aitest/                      ← 平台引擎
├── governance/
│   ├── skills/                  ← 通用技能（平台资产，只读）
│   ├── skills-dev/              ← 开发技能（平台资产，只读）
│   ├── agents/                  ← Agent 定义（平台资产，只读）
│   ├── context/
│   │   ├── project-index.yaml   ← 项目注册表（指向各项目路径）
│   │   ├── environments.yaml    ← 多项目环境汇总
│   │   └── shared-language.md   ← 术语表
│   └── projects/                ← 仅 Remote(URL) 项目的 knowledge fallback
└── plugins/
```

---

## 平台加载流程

```python
# 1. 项目发现
ProjectLoader.scan(workspace_paths)
  → 扫描每个路径，找 .tlo/project.yaml
  → 注册到 project-index.yaml

# 2. 项目加载
Project.from_tlo("/path/to/project")
  → 读取 .tlo/project.yaml
  → 加载 knowledge/modules/
  → 加载 runtime/sop-status/
  → 初始化 cache/

# 3. Path resolution（消除 ZJSN 硬编码）
get_test_project_root()  → project.yaml.test_project.path
get_tlo_dir()            → project_root / ".tlo"
get_context_modules()    → tlo_dir / "knowledge" / "modules"
get_sop_status_dir()     → tlo_dir / "runtime" / "sop-status"
```

---

## 迁移路径

### Phase 1: 试点（blue-album-v2）

1. 在项目目录创建 `.tlo/` 结构
2. Onboarding 输出写到 `.tlo/knowledge/`
3. SOP 状态写到 `.tlo/runtime/sop-status/`
4. 平台兼容新旧两套路径（`.tlo/` 优先，`governance/context/projects/` 兜底）

### Phase 2: ZJSN 迁移

1. `governance/context/projects/web-automation/` → `WorkStudy2/ZJSN_Test-master526/.tlo/knowledge/`
2. `governance/context/projects/miniapp-automation/` → `WorkStudy2/mp-weixin-automator/.tlo/knowledge/`
3. 遗留 `sop-status/` 根目录文件 → 各项目的 `.tlo/runtime/sop-status/`

### Phase 3: 清理

1. 删除平台端 `governance/context/projects/` 下的旧项目数据
2. 移除 paths.py 中所有 ZJSN fallback
3. 更新 Skill 提示中的路径为 `{project_root}/.tlo/`

---

## 与当前代码的兼容

```python
# aitest/platform/paths.py 渐进改动

def get_tlo_dir(project_root: Path = None) -> Optional[Path]:
    """返回项目的 .tlo/ 目录"""
    root = project_root or get_test_project_root()
    if root and (root / ".tlo").exists():
        return root / ".tlo"
    return None

def get_context_modules(project_id: str = None) -> Path:
    """优先 .tlo/，fallback 旧路径"""
    tlo = get_tlo_dir()
    if tlo and (tlo / "knowledge" / "modules").exists():
        return tlo / "knowledge" / "modules"
    # Fallback: 旧 governance/context/projects/ 路径
    return _WORKSTUDY / "governance" / "context" / "projects" / project_id / "modules"
```

---

## 决议

- `.tlo/` 作为项目级目录，包含 knowledge / context / runtime / artifacts / cache
- `knowledge/modules/` 保持当前嵌套 markdown 结构（未来可扩展 JSON knowledge graph）
- 平台端仅保留 skills / agents / project-index / Remote 项目 fallback
- 实施顺序: blue-album-v2 试点 → ZJSN 迁移 → 清理旧路径
