# ChatGPT 建议评审

> 2026-06-23 | 对 `.tlo/` 方案的第三方评审

---

## 总体判断：ChatGPT 的改进方向正确，但有一个关键误判

---

## 一、三层分类 ✅ 完全同意

ChatGPT 把 `.tlo/` 内容分成三类：

| 类别 | 性质 | Git | 举例 |
|------|------|:---:|------|
| **项目知识** | 描述项目是什么 | ✅ | project.yaml, PAGE_CONTEXT.md, TEST_CASES.md |
| **缓存** | 可从源码重新生成 | ❌ | .discovery/, pages.json |
| **运行状态** | 执行进度快照 | ❌ | SOP_STATUS |

这个分类**比我原来的扁平结构好**。我原方案把所有东西平铺在 `.tlo/` 下，没有区分可版本化 vs 不可版本化。

**评审结论: 采纳。** 改为三层目录:

```
.tlo/
  context/       ← Git ✅  项目知识
  cache/         ← Git ❌  可重新生成
  runtime/       ← Git ❌  执行状态
```

---

## 二、运行状态不放 `.tlo/`？❌ 不同意

ChatGPT 认为 SOP_STATUS 是"平台运行时状态"，不应该放在项目目录。

**我不同意。** 理由：

### 2.1 SOP_STATUS 是项目级状态，不是平台级状态

```
SOP_STATUS_equipment.json  →  描述"ZJSN 的 equipment 模块的测试进度"
                            →  跟项目绑定，不跟平台绑定
```

如果两个平台实例操作两个不同项目，状态不存在跨项目共享需求。
如果一个平台实例操作一个项目，状态应该跟着项目走。

### 2.2 放回平台目录会复现耦合

```
# ChatGPT 隐含的建议
平台目录/sop-status/SOP_STATUS_equipment.json   ← 项目 A 的 equipment
平台目录/sop-status/SOP_STATUS_equipment.json   ← 项目 B 的 equipment → 覆盖！
```

这就是现在的遗留问题——不按项目隔离。

### 2.3 正确做法：gitignore 而非移走

```
.tlo/
  runtime/                    ← 整个目录 .gitignore
    sop-status/
      SOP_STATUS_equipment.json
```

既不污染 Git 历史，又物理隔离不同项目。两全其美。

**评审结论: 拒绝。** SOP_STATUS 留在 `.tlo/runtime/`，gitignore 整个 `runtime/` 目录。

---

## 三、`.tlo` 升级为 Manifest ✅ 非常同意

ChatGPT 提出的核心理念：

> **`.tlo` 不是"上下文目录"，而是"项目对平台的声明（Project Manifest）"**

类比:

| 生态 | Manifest | 作用 |
|------|----------|------|
| npm | `package.json` | 声明依赖、脚本、入口 |
| Python | `pyproject.toml` | 声明构建、依赖、元数据 |
| Rust | `Cargo.toml` | 声明 crate 配置 |
| **TLO** | **`.tlo/manifest.yaml`** | **声明测试项目结构、模块、能力** |

这个视角转换很重要:

```
之前: .tlo/ 是平台的"输出目录"（平台生成上下文存这里）
之后: .tlo/ 是项目的"自描述文件"（项目告诉平台自己是什么）
```

**评审结论: 采纳。** `project.yaml` → `manifest.yaml`，语义从"平台配置项目"转为"项目声明自己"。

---

## 四、平台 = Registry, 不是 Storage ✅ 同意

ChatGPT:

> 平台只负责: 发现 → 注册 → 加载。不负责保存。

对应到实现:

```python
# 之前: 平台"拥有"项目数据
class ProjectContext:
    def artifacts(self):
        return ArtifactStore(WORKSTUDY / "governance/context/projects" / project_id)

# 之后: 平台"读取"项目声明
class ProjectLoader:
    def discover(self, root: Path) -> Optional[Project]:
        manifest = root / ".tlo" / "manifest.yaml"
        if manifest.exists():
            return Project.from_manifest(manifest)
    
    def scan_workspace(self) -> list[Project]:
        # 扫描已知目录，找所有 .tlo/manifest.yaml
        ...
```

平台维护的只是一个轻量索引:

```yaml
# governance/context/project-index.yaml
projects:
  - id: zjsn
    path: D:/Desktop/WorkStudy2/ZJSN_Test-master526
    type: pytest-selenium
  - id: miniapp-automation
    path: D:/Desktop/WorkStudy2/mp-weixin-automator
    type: jest-miniprogram
```

真正的配置在项目自己的 `.tlo/manifest.yaml` 里。

**评审结论: 采纳。** 平台降级为 Registry + Loader。

---

## 五、ChatGPT 遗漏的问题

### 5.1 纯 URL 项目没有本地路径

Onboarding 通过 URL（非本地源码）发现的项目，没有文件系统路径。
`.tlo/` 无处存放。

**方案**: 分两类项目

| 类型 | manifest 位置 | 说明 |
|------|-------------|------|
| **Local** | `<project_path>/.tlo/manifest.yaml` | 有本地源码 |
| **Remote** | `governance/projects/<id>/manifest.yaml` | URL 导入，平台托管 |

Remote 项目在平台目录下的 `manifest.yaml` 中标记 `source: url`，行为与 Local 一致，只是物理位置不同。这是必要的妥协。

### 5.2 `manifest.yaml` vs `project.yaml` 兼容

现有代码大量引用 `project.yaml`。一次性改名兼容成本高。

**方案**: 两个文件名都支持，优先 `manifest.yaml`:

```python
def load_project_config(root: Path) -> dict:
    for name in ["manifest.yaml", "project.yaml"]:
        p = root / ".tlo" / name
        if p.exists():
            return yaml.safe_load(p.read_text())
```

新项目用 `manifest.yaml`，旧项目继续用 `project.yaml`，逐步迁移。

---

## 六、最终修订方案

### 目录结构

```
项目/
├── .tlo/
│   ├── manifest.yaml              # 项目声明（原 project.yaml）
│   │
│   ├── context/                   # 📁 项目知识 — Git ✅
│   │   ├── PROJECT_CONTEXT.md
│   │   ├── MODULE_INDEX.md
│   │   ├── coding-standards.md
│   │   └── modules/
│   │       └── <module>/
│   │           ├── MODULE_CONTEXT.md
│   │           └── pages/
│   │               └── <page>/
│   │                   ├── PAGE_CONTEXT.md
│   │                   ├── PAGE_INTERFACE.yaml
│   │                   ├── RISK_MODEL.md
│   │                   ├── TEST_CASES.md
│   │                   └── TEST_DESIGN.md
│   │
│   ├── runtime/                   # 📁 运行状态 — Git ❌
│   │   ├── sop-status/
│   │   │   └── SOP_STATUS_<module>.json
│   │   ├── sessions/
│   │   └── checkpoints/
│   │
│   └── cache/                     # 📁 缓存 — Git ❌
│       ├── discovery/
│       │   ├── pages.json
│       │   └── menu_tree.json
│       └── embeddings/
│
├── .gitignore                     # .tlo/runtime/  .tlo/cache/
├── script/                        # 测试脚本
├── page/                          # Page Object
└── src/                           # 源码
```

### 平台端

```
WorkStudy/
├── aitest/                        # 平台引擎
├── governance/
│   ├── skills/                    # 通用技能（只读）
│   ├── agents/                    # Agent 定义（只读）
│   ├── context/
│   │   ├── project-index.yaml     # 轻量项目注册表
│   │   ├── environments.yaml      # 环境汇总
│   │   └── shared-language.md     # 术语
│   └── projects/                  # 仅 Remote 项目 manifest 缓存
│       └── <remote-project>/
│           └── manifest.yaml
```

### 加载流程

```
Platform 启动
  ↓
ProjectLoader.scan(workspace_paths)
  ↓ 扫描每个路径，找 .tlo/manifest.yaml
  ↓
ProjectRegistry (project-index.yaml)
  ↓
用户选择 active project
  ↓
Project.from_manifest(.tlo/manifest.yaml)
  ↓
Context = ProjectKnowledge + RuntimeState + Cache
  ↓
Agent 可操作
```

---

## 七、ChatGPT 建议的采纳/拒绝汇总

| 建议 | 判断 | 理由 |
|------|:---:|------|
| 三层分类 (context/cache/runtime) | ✅ 采纳 | 比扁平结构清晰，区分 Git 策略 |
| SOP_STATUS 不放 .tlo | ❌ 拒绝 | 需要项目隔离；gitignore 即可解决污染问题 |
| `.tlo` 升级为 Manifest | ✅ 采纳 | 核心视角转换：平台输出 → 项目声明 |
| 平台 = Registry | ✅ 采纳 | 平台不再"拥有"项目数据 |
| `.tlo/` 应包含 prompts/workflows/reports | ⚠️ 部分 | 暂不需要。当前阶段 context + runtime + cache 足够 |
| `project.yaml` → `manifest.yaml` | ✅ 采纳 | 渐进迁移，兼容旧名 |
| 项目上下文放在项目自己的 `.tlo/` | ✅ 采纳 | 原方案核心，ChatGPT 确认 |
