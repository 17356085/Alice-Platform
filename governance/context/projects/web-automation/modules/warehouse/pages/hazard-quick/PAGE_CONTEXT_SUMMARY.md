# PAGE_CONTEXT 快速汇总 — 环保危废（3 个辅助页面）+ 三剂消耗（2 页）

---

## 环保库存查询 — `#/warehouse/hazard/stock`

| 属性 | 值 |
|------|-----|
| 数据行数 | 2 |
| 搜索 | 物品名称 + 2×el-select |
| 按钮 | 查询、重置 |
| 操作 | 只读 |
| 审批流 | 无 |

---

## 环保出入库明细表 — `#/warehouse/hazard/io-record`

| 属性 | 值 |
|------|-----|
| 数据行数 | 4 |
| 搜索 | 物品名称 + 日期范围(el-range-input) + 3×el-select |
| 按钮 | 查询、重置 |
| 操作 | 只读日志 |
| 审批流 | 无 |

---

## 环保物品管理 — `#/warehouse/hazard/item`

| 属性 | 值 |
|------|-----|
| 搜索 | 危废品名称(input, placeholder="请输入危废品名称") + checkbox组 + 2×el-select |
| 操作 | CRUD + 批量选择 |
| 审批流 | 无 |

---

## 三剂消耗-物品管理 — `#/warehouse/reagent/item`

| 属性 | 值 |
|------|-----|
| 数据行数 | 3 |
| 搜索 | 物品名称 + 厂家名称 + checkbox组 + 2×el-select |
| 操作 | CRUD + 批量选择 + 导入导出 |
| 审批流 | 无 |

---

## 三剂消耗-装填管理 — `#/warehouse/reagent/fill`

| 属性 | 值 |
|------|-----|
| 数据行数 | 1 |
| 搜索 | 物品编号 + 日期 + 2×el-select |
| 操作 | CRUD + 导入导出 |
| 审批流 | 无 |
