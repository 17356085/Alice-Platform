# .tlo/ 团队使用场景分析

> 2026-06-23 | 核心矛盾：项目自包含 vs 团队协作

---

## 一、两个矛盾

### 矛盾1: 天然隔离 ≠ 团队共享

```
正确: .tlo/runtime/ 按项目隔离 → 项目A和项目B不冲突
也正确: .tlo/runtime/ 是本地文件 → Alice和Bob各有一份，不共享
```

项目间隔离解决了，**团队成员间共享**变成了新问题。

### 矛盾2: 项目负担

```
.tlo/context/   → Git 跟踪 → 项目仓库多了一堆 .md 文件
.tlo/runtime/   → 不跟踪   → 每个开发者本地独立
.tlo/cache/     → 不跟踪   → 每个开发者本地重建
```

对于不直接用 TLO 的团队成员，这些文件是噪音。

---

## 二、团队场景模拟

### 场景: 3 人团队 + CI

```
Alice (开发者)          Bob (测试)            CI (自动化)
     │                      │                     │
     ├─ .tlo/context/       ├─ .tlo/context/      ├─ .tlo/context/
     │   (Git pull 共享)     │   (Git pull 共享)    │   (Git checkout)
     │                      │                     │
     ├─ .tlo/runtime/       ├─ .tlo/runtime/      ├─ .tlo/runtime/
     │   SOP_STATUS:         │   SOP_STATUS:        │   SOP_STATUS:
     │   equipment: init     │   equipment: 空      │   equipment: done
     │   (Alice 本地状态)     │   (Bob 本地状态)      │   (CI 本地状态)
     │                      │                     │
     └─ 看到: 自己跑了啥      └─ 看到: 空的           └─ 看到: 全跑完了
```

**问题**: Alice 跑完 Phase 1-3，Bob 接手跑 Phase 4-6。Bob 看不到 Alice 的进度。每人看到的是自己的本地状态。

### 这才是 ChatGPT 真正想表达的

ChatGPT 说"SOP_STATUS 不是项目知识，是平台运行时状态"——他说对了一半。

| | 项目知识 (context/) | 运行时状态 (runtime/) |
|---|---|---|
| **对团队的意义** | 团队共享的真理 | 个人/会话的进度 |
| **一致性要求** | 所有人看到一致 | 需要"某人"是权威源 |
| **存储位置** | Git（天然一致） | 需要共享服务 |

---

## 三、拆分方案：双存储

```
.tlo/
  context/           ← Git ✅  团队共享的项目定义
    manifest.yaml
    modules/

  cache/             ← 本地 ❌  可重建，各自维护
    discovery/

  runtime/           ← 本地缓存 ❌  平台服务器是权威源
    sop-status/      ← 服务器同步下来的本地副本
```

### 真正的权威源：平台服务器

```
                    ┌──────────────┐
                    │  TLO Server  │  ← SOP 执行状态的权威源
                    │  (FastAPI)   │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         Alice (本地)   Bob (本地)    CI
              │            │            │
    .tlo/runtime/   .tlo/runtime/   .tlo/runtime/
    (本地缓存)       (本地缓存)       (本地缓存)
```

流程：

```
1. Alice 触发 SOP → Server 执行 → 更新服务器端 SOP_STATUS
2. Bob 打开 Kanban → 拉取服务器端 SOP_STATUS → 缓存到 .tlo/runtime/
3. CI 执行 Phase 7 → WebSocket 广播 → Alice/Bob 实时看到
```

`.tlo/runtime/` 降级为 **服务器状态的本地缓存**，不是权威源。

---

## 四、对项目负担的回答

### 负担是什么？

```
项目仓库/
  .tlo/
    context/           ← ~50-200 个 .md 文件
      modules/         ← 每个模块/页面 3-6 个文件
```

一个 12 模块、每模块 4 页面的项目 ≈ 12×4×4 = ~200 个上下文文件。

### 这些文件对非 TLO 用户是噪音吗？

**短期：是的。** 不熟悉 TLO 的开发者看到 `PAGE_CONTEXT.md`、`RISK_MODEL.md`、`TEST_CASES.md` 会困惑。

**长期：不是。** 这和 `.github/workflows/` 一样——不是所有人都写 CI，但所有人都接受它存在。

### 类比

| 目录 | 非用户感受 | 现在？ |
|------|-----------|:---:|
| `.github/workflows/` | "CI 配置，不影响我" | ✅ 普遍接受 |
| `.vscode/` | "IDE 配置，不影响我" | ✅ 普遍接受 |
| `.claude/` | "AI 配置，不影响我" | ⚠️ 新事物 |
| **`.tlo/`** | **"测试平台配置，不影响我"** | ❓ 待建立认知 |

所有这些都是 **工具配置跟着项目走**。接受度取决于工具本身的普及度。

### 减轻负担的措施

1. **README 一行说明**: `.tlo/` — TLO 测试生命周期编排，非 TLO 用户可忽略
2. **`.gitignore` 按需**: 如果团队决定不用 TLO，删除 `.tlo/` 不影响项目运行
3. **最小化 context/**: 只存不可自动生成的知识，缓存和运行时状态不提交

---

## 五、最终判断

| 问题 | 答案 |
|------|------|
| 放在项目是天然隔离吗？ | ✅ 是。项目间完全隔离 |
| 增加项目负担吗？ | ⚠️ 短期有（新目录认知成本），长期无（和 .github/ 一样） |
| 团队使用怎么办？ | runtime/ 的权威源应在平台服务器，.tlo/runtime/ 只是本地缓存 |
| ChatGPT 对的点？ | 运行时状态 ≠ 项目知识。需要共享服务而非本地文件 |
| ChatGPT 错的点？ | 不该把运行时状态搬回平台目录——应该搬到一个**共享服务** |

---

## 六、修订后的架构

```
┌─────────────────────────────────────────────────┐
│                    TLO Platform                  │
│                                                 │
│  governance/                                    │
│    skills/          ← 通用技能（只读）            │
│    agents/          ← Agent 定义（只读）          │
│    context/                                      │
│      project-index.yaml  ← 项目注册表            │
│                                                 │
│  aitest/server/                                  │
│    sop-state/        ← 🆕 SOP 执行状态存储       │
│      <project_id>/                               │
│        SOP_STATUS_<module>.json  ← 权威源        │
│                                                 │
└─────────────────────────────────────────────────┘
         │                    │
    Alice 本地            Bob 本地
    .tlo/                 .tlo/
      context/   ← Git     context/   ← Git
      cache/     ← 本地    cache/     ← 本地
      runtime/   ← 缓存    runtime/   ← 缓存
```

**两层存储**:
- **项目定义** (.tlo/context/) → Git，跟着项目，团队共享
- **执行状态** (平台服务器) → 共享服务，`.tlo/runtime/` 降级为本地缓存
