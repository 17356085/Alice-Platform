# .tlo/ 方案 — 项目上下文跟随项目

> 2026-06-23 | 将项目上下文从平台中央目录迁入项目自身的 `.tlo/` 目录

---

## 一、当前 vs 方案

### 当前架构（平台中央式）

```
WorkStudy/                               ← 平台
  governance/context/projects/
    web-automation/                      ← ZJSN 上下文存平台里
      project.yaml
      MODULE_INDEX.md
      modules/equipment/pages/...        ← 数百个 PAGE_CONTEXT 文件
    miniapp-automation/
    blue-album-v2/

WorkStudy2/
  ZJSN_Test-master526/                   ← 只有测试代码
    script/  page/  config/
```

**问题**: 上下文和代码分离。项目迁移 → 上下文留在平台 → 路径断裂。

### 方案架构（项目自包含）

```
WorkStudy2/
  ZJSN_Test-master526/
    .tlo/                                ← 🆕 上下文跟着项目
      project.yaml
      MODULE_INDEX.md
      modules/
        equipment/pages/
          alarm-config/PAGE_CONTEXT.md
          maintenance/PAGE_CONTEXT.md
      sop-status/                        ← 🆕 SOP 状态也在这里
        SOP_STATUS_equipment.json
    .env                                 ← 已有（凭证）
    script/                              ← 测试脚本
    page/                                ← Page Object
    config/                              ← 配置
```

**优点**: 项目完全自包含。移走项目 → 上下文跟着走。Git 可版本控制。

---

## 二、类比：业界标准模式

| 目录 | 所属 | 内容 |
|------|------|------|
| `.vscode/` | VS Code | 工作区设置、调试配置、推荐扩展 |
| `.github/workflows/` | GitHub | CI/CD 流程定义 |
| `.claude/` | Claude Code | 项目指令、设置、记忆 |
| `.cursor/` | Cursor | AI 编辑器规则 |
| `.husky/` | Husky | Git hooks |
| **`.tlo/`** | **TLO Platform** | **测试生命周期编排上下文** |

所有这些的共同模式：**工具配置跟着项目走，不存工具自己目录里**。

---

## 三、`.tlo/` 目录结构

```yaml
.tlo/
  project.yaml              # 项目配置（原 governance/context/projects/<id>/project.yaml）
  MODULE_INDEX.md           # 模块索引
  PROJECT_CONTEXT.md        # 项目上下文
  coding-standards.md       # 编码规范
  element-plus-pitfalls.md  # UI 框架陷阱
  
  modules/                  # 模块上下文（原 governance/context/projects/<id>/modules/）
    <module>/
      MODULE_CONTEXT.md
      pages/
        <page>/
          PAGE_CONTEXT.md
          PAGE_INTERFACE.yaml
          RISK_MODEL.md
          TEST_CASES.md
          TEST_DESIGN.md
  
  sop-status/               # SOP 执行状态（原 governance/artifacts/sop-status/<project_id>/）
    SOP_STATUS_<module>.json
  
  .discovery/               # 自动发现缓存
    pages.json
    menu_tree.json
```

---

## 四、平台改动

### 4.1 paths.py 重写

```python
# 之前
def get_test_project_root(project_id=None) -> Optional[Path]:
    ctx = get_project(project_id)
    code_path = ctx.config.test_project_code_path
    if code_path:
        return _WORKSTUDY / code_path
    return None

def get_context_modules(project_id=None) -> Path:
    ctx = get_project(project_id)
    return ctx.artifacts()._modules_dir   # governance/context/projects/<id>/modules/

# 之后
def get_test_project_root(project_id=None) -> Optional[Path]:
    """返回测试项目根目录（包含 .tlo/ 的目录）"""
    ctx = get_project(project_id)
    return ctx.config.test_project_path    # 从 project.yaml 或 discovery 获取

def get_tlo_dir(project_id=None) -> Path:
    """返回项目下的 .tlo/ 目录"""
    root = get_test_project_root(project_id)
    return root / ".tlo"

def get_context_modules(project_id=None) -> Path:
    """返回 .tlo/modules/"""
    return get_tlo_dir(project_id) / "modules"
```

### 4.2 project.yaml 改动

```yaml
# 之前
project:
  id: "web-automation"
test_project:
  code_path: "../WorkStudy2/ZJSN_Test-master526"

# 之后
project:
  id: "web-automation"
  name: "鞍集涂源管理系统"
test_project:
  path: "D:/Desktop/WorkStudy2/ZJSN_Test-master526"   # 绝对路径
  type: "pytest-selenium"
  page_objects: "page/"
  test_scripts: "script/"
  tlo_dir: ".tlo/"                                     # 上下文目录（默认 .tlo/）
```

### 4.3 平台只保留什么？

```
WorkStudy/                               ← 平台本身
  aitest/                                ← 平台引擎代码
  governance/
    skills/                              ← 通用测试技能（平台资产）
    skills-dev/                          ← 通用开发技能（平台资产）
    agents/                              ← Agent 定义（平台资产）
    context/
      environments.yaml                  ← 多项目环境汇总
      project-index.yaml                 ← 项目注册表（指向各项目的 .tlo/）
      shared-language.md                 ← 术语表
    artifacts/
      sop-status/                        ← 只剩汇总索引（每个项目的详细状态在各自 .tlo/ 里）
      audits/                            ← 跨项目审计报告
    kpi/                                 ← 跨项目 KPI 汇总
    knowledge/                           ← 跨项目知识库（ChromaDB）
```

---

## 五、影响分析

### 5.1 旧 web-automation 上下文迁移

```bash
# 从平台中央 → 项目 .tlo/
cp -r governance/context/projects/web-automation/* \
      D:/Desktop/WorkStudy2/ZJSN_Test-master526/.tlo/
```

### 5.2 Onboarding 流程

```
之前:  onboard → governance/context/projects/<id>/
之后:  onboard → <project_path>/.tlo/
```

项目导入时，用户指定项目本地路径。Onboarding 直接在项目目录下创建 `.tlo/`。

无本地路径的项目（纯 URL 导入）→ 平台仍需一个 fallback 位置。可以放在 `governance/context/projects/<id>/` 作为缓存，标记 `source: url`。

### 5.3 覆盖风险消除

```
之前: governance/artifacts/sop-status/SOP_STATUS_equipment.json  ← 多项目冲突
之后: <project>/.tlo/sop-status/SOP_STATUS_equipment.json         ← 完全隔离
```

每个项目的 SOP 状态在自己的 `.tlo/` 里，不可能跨项目覆盖。

### 5.4 Skill 提示自动解耦

```
之前: governance/context/projects/web-automation/modules/<module>/
之后: {project_path}/.tlo/modules/<module>/
```

Skill 提示中的路径从硬编码 `web-automation` 变成变量 `{project_path}`。
Agent 执行时从 active project 的路径动态解析。

---

## 六、优缺点

### ✅ 优点

| | |
|---|---|
| **自包含** | 项目 = 源码 + 测试 + 上下文，一个目录包含一切 |
| **可移植** | 移动/复制项目目录 → 上下文自动跟随 |
| **Git 友好** | `.tlo/` 可提交到仓库，团队共享上下文 |
| **多项目隔离** | 每个项目的上下文物理隔离，零覆盖风险 |
| **平台解耦** | 平台不再"拥有"项目数据，只是读取工具 |
| **IDE 对标** | 与 `.vscode/`、`.github/` 一致的开发者心智模型 |

### ⚠️ 注意事项

| | |
|---|---|
| **纯 URL 项目** | 没有本地路径的项目需要平台提供 fallback 存储 |
| **多平台实例** | 两个 TLO 实例操作同一项目 → `.tlo/` 并发写入。需文件锁 |
| **迁移兼容** | 旧 `governance/context/projects/` 数据需要一次性迁移脚本 |
| **只读项目** | 项目源码在只读文件系统上 → `.tlo/` 不可写。需 fallback |
| **发现成本** | 平台需要"发现"项目而非从注册表查找 → 需要 project-index 或扫描 |

---

## 七、与现有 `.claude/` 的关系

`ZJSN_Test-master526` **已有 `.claude/` 目录**（Claude Code 项目指令）。

`.tlo/` 与 `.claude/` 不冲突：
- `.claude/` → AI 编码助手的项目设置（Claude Code 专属）
- `.tlo/` → 测试生命周期编排的项目上下文（TLO 平台专属）

两者共存，职责不同。类比：项目同时有 `.vscode/` 和 `.github/`。

---

## 八、实施路线

### Phase 1: 试点（1 天）
- blue-album-v2 项目创建 `.tlo/` → 验证 onboarding 写到 `.tlo/`
- paths.py 增加 `get_tlo_dir()` 函数，先兼容新旧两套路径

### Phase 2: 迁移（1 天）
- web-automation 上下文 → `WorkStudy2/ZJSN_Test-master526/.tlo/`
- miniapp-automation 上下文 → `WorkStudy2/mp-weixin-automator/.tlo/`
- 遗留 SOP_STATUS → 各项目的 `.tlo/sop-status/`

### Phase 3: 切换（1 天）
- `get_context_modules()` 等全部切到 `.tlo/`
- Skill 提示改为 `{project_path}/.tlo/`
- `governance/context/projects/` 降级为纯 URL 项目的 fallback 缓存

### Phase 4: 清理（1 天）
- 移除 `paths.py` 中所有 ZJSN fallback
- 删除 $WORKSTUDY/ZJSN_Test-master526 引用
- 更新文档
