# PAGE_CONTEXT — warehouse / spare-stock

> **状态**: Phase 1 | **日期**: 2026-06-12 | **方式**: Selenium 自动抓取

---

## 基本信息

| 字段 | 值 |
|------|-----|
| 页面ID | spare-stock |
| 页面名称 | 备品库存查询 |
| 路由 | `#/warehouse/spare/stock` ✅ |
| 面包屑 | 库管管理 / 备品备件管理 / 库存查询 |
| 页面类型 | 只读查询 |
| 审批链 | 无 |

---

## 页面职责

备品备件库存查询，展示当前库存数量与物品信息。只读页面，不提供新增/编辑/删除功能。

---

## 核心元素

### 搜索区（自定义 wh-filter-toolbar）

| 元素ID | 描述 | 选择器 |
|--------|------|--------|
| filter-item-name | 物品名称输入框 | `//input[@placeholder="请输入物品名称"]` |
| filter-select-1 | el-select 下拉1 | — |
| filter-select-2 | el-select 下拉2 | — |
| btn-query | 查询按钮 | `//button[contains(.,"查询")]` |
| btn-reset | 重置按钮 | `//button[contains(.,"重置")]` |

### 表格

| 列 | 数据类型 | 备注 |
|------|----------|------|
| 序号 | 数字 | |
| 物品编号 | 文本 | |
| 物品名称 | 文本 | |
| 规格型号 | 文本 | |
| 单位 | 文本 | |
| 库存数量 | 数字 | 核心数据 |
| 安全库存 | 数字 | |
| 备注 | 文本 | |

### 分页

标准 el-pagination，位于表格底部。

---

## 操作说明

| 操作 | 类型 | 备注 |
|------|------|------|
| 查询 | 按钮 | 按物品名称+下拉条件筛选 |
| 重置 | 按钮 | 清空搜索条件 |
| 行内操作 | — | 无（只读页面） |

---

## 技术特征

| 组件层 | 技术 | 定位策略 |
|--------|------|----------|
| 搜索区 | 自定义 wh-filter-toolbar | placeholder + XPath |
| 表格 | 标准 el-table | ✅ BasePage 通用定位器可用 |
| 分页 | 标准 el-pagination | ✅ BasePage 通用定位器可用 |

---

## 自动化覆盖

| 文件 | 状态 |
|------|:--:|
| Page Object | `page/warehouse_page/SpareStockPage.py` ✅ |
| 测试脚本 | `script/warehouse/test_spare_stock.py` ✅ (4 cases) |
| conftest fixture | `spare_stock_page` ✅ |
