我来为你进行 `tank` 模块的 Hygiene Check（治理文档完整性检查）。

✅ **项目级别文档**
- [x] `project.yaml` — 存在

✅ **模块级别文档（MODULE_CONTEXT.md）**

| 模块 | 状态 |
|-----------|--------|
| tank | ❌ 缺失 |
| core | ❌ 缺失 |
| session | ❌ 缺失 |

❌ **未发现任何模块级别的 MODULE_CONTEXT.md**

✅ **页面级别文档（PAGE_CONTEXT.md）**

| 路径 | 状态 |
|------|--------|
| tank/ | ❌ 缺失 |
| tank/platoon/ | ❌ 缺失 |
| tank/position/ | ❌ 缺失 |
| tank/upgrade/ | ❌ 缺失 |
| tank/stat/ | ❌ 缺失 |
| core/ | ❌ 缺失 |
| core/weapon/ | ❌ 缺失 |
| core/damage/ | ❌ 缺失 |
| core/movement/ | ❌ 缺失 |
| session/ | ❌ 缺失 |
| session/command/ | ❌ 缺失 |
| session/event/ | ❌ 缺失 |
| session/state/ | ❌ 缺失 |

❌ **未发现任何页面级别的 PAGE_CONTEXT.md**

---

## 🔴 缺失清单（按优先级排序）

### P0 — 模块级文档（必须优先补全）
1. `modules/tank/modules/tank/MODULE_CONTEXT.md`
2. `modules/tank/modules/core/MODULE_CONTEXT.md`
3. `modules/tank/modules/session/MODULE_CONTEXT.md`

### P1 — 页面级文档（第二优先级）
- `modules/tank/pages/tank/PAGE_CONTEXT.md`
- `modules/tank/pages/tank/platoon/PAGE_CONTEXT.md`
- `modules/tank/pages/tank/position/PAGE_CONTEXT.md`
- `modules/tank/pages/tank/upgrade/PAGE_CONTEXT.md`
- `modules/tank/pages/tank/stat/PAGE_CONTEXT.md`
- `modules/tank/pages/core/PAGE_CONTEXT.md`
- `modules/tank/pages/core/weapon/PAGE_CONTEXT.md`
- `modules/tank/pages/core/damage/PAGE_CONTEXT.md`
- `modules/tank/pages/core/movement/PAGE_CONTEXT.md`
- `modules/tank/pages/session/PAGE_CONTEXT.md`
- `modules/tank/pages/session/command/PAGE_CONTEXT.md`
- `modules/tank/pages/session/event/PAGE_CONTEXT.md`
- `modules/tank/pages/session/state/PAGE_CONTEXT.md`

## 📊 统计

| 类型 | 应有 | 实有 | 缺失率 |
|----------|------|------|-----------|
| MODULE_CONTEXT.md | 3 | 0 | **100%** 🔴 |
| PAGE_CONTEXT.md | 13 | 0 | **100%** 🔴 |
| project.yaml | 1 | 1 | 0% ✅ |
| **合计** | **17** | **1** | **94%** 🔴 |

## 💡 建议

1. **立即修复 P0 缺失**：为 3 个模块（tank、core、session）编写 MODULE_CONTEXT.md
2. **使用模板**：每个 MODULE_CONTEXT.md 应包含：目标、职责、核心概念、依赖关系、状态标记
3. **同步补全页面文档**：确保 PAGE_CONTEXT.md 包含：页面目标、输入数据、输出动作、UI 状态描述
4. **建立 CI 检查**：添加 lint 配置，阻止新页面在没有 PAGE_CONTEXT.md 的情况下合并

> ⚠️ 当前状态：该项目缺少治理文档，可运行性/可维护性受到严重影响。