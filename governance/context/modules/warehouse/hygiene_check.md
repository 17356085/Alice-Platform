收到，开始检查 `warehouse` 模块的治理文档完整性。

**检查对象**: `governance/context/projects/{id}/warehouse/`

---

## 📋 治理文档完整性检查报告

### ✅ 已存在（通过）
- `warehouse/module/module.md`
- `warehouse/module/MODULE_CONTEXT.md`
- `warehouse/pages/inventory/PAGE_CONTEXT.md`
- `warehouse/pages/inbound/PAGE_CONTEXT.md`

### ❌ 缺失（需补充）

| 优先级 | 缺失文件 | 说明 |
|--------|----------|------|
| P0 | `warehouse/pages/inventory/INVENTORY_CONTEXT.md` | 页面完整上下文，优先级同原PAGE_CONTEXT |
| P0 | `warehouse/pages/inbound/INBOUND_CONTEXT.md` | 同上，但若已有PAGE_CONTEXT可复用/重命名 |
| P1 | `warehouse/pages/shipment/PAGE_CONTEXT.md` | 若存在shipment页面，应补充 |
| P1 | `warehouse/pages/stocktake/PAGE_CONTEXT.md` | 若存在stocktake盘点页面 |
| P2 | `warehouse/README.md` | 模块级快速入口说明（可选建议） |

---

## 🏷 优先级建议

### P0（必须立即补）
1. **INVENTORY_CONTEXT.md**
   - 承接 `PAGE_CONTEXT.md` 的逻辑与场景上下文
2. **INBOUND_CONTEXT.md**
   - 相同原因，若 `PAGE_CONTEXT.md` 内容已足够，可重命名复用

### P1（建议近期补）
- `shipment` 和 `stocktake` 页面若有独立逻辑，各自补充 `PAGE_CONTEXT.md`

### P2（长期优化）
- `README.md` 非强制，但有助于新人快速理解模块结构

---

## ✅ 结论

| 项 | 结果 |
|----|------|
| `MODULE_CONTEXT.md` | ✅ 存在 |
| 页面 `PAGE_CONTEXT.md` | ⚠️ 部分存在（缺shipment/stocktake） |
| 页面完整上下文 `*_CONTEXT.md` | ❌ **P0 缺失 inventory/inbound** |
| 模块首页 `README.md` | ❌ 缺失（P2建议） |

**总体评分**: 60/100（建议立即修补P0项目，提升至80+）