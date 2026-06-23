# PAGE_CONTEXT — sales / sales-order

> 从 SalesOrderPage.py 实际代码提取 | 2026-06-17 | 覆盖过期文档

## 页面信息
- **页面名称**: 销售订单
- **路由**: `#/sales/order`
- **PO**: `page/sales_page/SalesOrderPage.py` (继承 BasePage，无 ElementPlusHelper)
- **侧边栏导航**: `navigate_to("销售管理", "销售订单")`
- **页面性质**: CRUD 页面（新增/查看详情）

## 页面整体结构

顶部全局导航栏 → 左侧菜单 → 主内容区：
1. **搜索/筛选区**: 2 个 el-input + 1 个 el-select + 1 个 el-date-picker range + 3 个 el-button
2. **表格区**: el-table 8 列，第1列单号为可点击 el-button (link)，第3列产品类型为 el-tag
3. **分页区**: el-pagination

## 搜索/筛选区

| 元素ID | 描述 | 控件类型 | 定位器 | 等级 |
|:---|:---|:---|:---|:--:|
| `SEARCH_ORDER_NO` | 销售单号 | el-input | CSS: `input[placeholder="销售单号"]` | A |
| `SEARCH_CUSTOMER` | 客户名称 | el-input | CSS: `input[placeholder="客户名称"]` | A |
| `SEARCH_PRODUCT_TYPE` | 产品类型 | el-select | `//div[contains(@class,"el-select")][.//*[contains(@class,"el-select__placeholder") and contains(.,"产品类型")]]` | B |
| `SEARCH_DATE_START` | 开始日期 | el-date-picker | CSS: `input[placeholder="开始日期"]` | B |
| `SEARCH_DATE_END` | 结束日期 | el-date-picker | CSS: `input[placeholder="结束日期"]` | B |
| `BTN_SEARCH` | 查询 | el-button (primary) | `//button[contains(@class,"el-button--primary")]//span[contains(normalize-space(.),"查询")]/parent::button` | A |
| `BTN_RESET` | 重置 | el-button (default) | `//button[not(contains(@class,"el-button--primary"))]//span[contains(normalize-space(.),"重置")]/parent::button` | A |
| `BTN_ADD` | 新增销售 | el-button (primary) | `//button[contains(@class,"el-button")]//span[contains(normalize-space(.),"新增销售")]/parent::button` | A |

> **注意**: 按钮文本为"查询"（非"搜索"），"新增销售"（非"新增订单"）。搜索区无"关联合同"下拉字段 — 关联合同仅出现在新增弹窗中作为级联下拉。

## 表格区

| 列索引 | COL 常量 | 列名 | 数据类型 | 备注 |
|:--:|:---|:---|:---|:---|
| 1 | `COL_ORDER_NO` | 销售单号 | el-button (link) | 可点击跳转详情 |
| 2 | `COL_CUSTOMER` | 客户名称 | 文本 | — |
| 3 | `COL_PRODUCT_TYPE` | 产品类型 | el-tag | `el-tag--primary`=LNG, `el-tag--warning`=焦油 |
| 4 | `COL_QUANTITY` | 销售量 | 数字 | 浮点数，精度4位 |
| 5 | `COL_PLATE` | 车牌号 | 文本 | — |
| 6 | `COL_SALE_TIME` | 销售时间 | 日期时间 | — |
| 7 | `COL_CONTRACT` | 关联合同 | 文本 | — |
| 8 | `COL_OPERATIONS` | 操作 | 按钮组 | 详情 |

### 行操作
| 操作 | 定位器 | 备注 |
|:---|:---|:---|
| 单号链接 | `.//button[contains(@class,"el-button--text")]` | 点击跳转详情 |
| 详情按钮 | `click_row_button(identifier, "详情")` | XPATH `.//button[contains(.,"详情")]` |

### 产品类型标签
| 产品 | CSS 类 | 颜色 |
|:---|:---|:---|
| LNG | `el-tag--primary` | 蓝色 |
| 焦油 | `el-tag--warning` | 橙色 |

获取方法: `get_product_tag_type(row)` / `get_product_tag_text(row)` — 解析 `td:nth-child(3) .cell span.el-tag` 的 CSS 类。

## 弹窗（新增销售）

`click_add()` 4 级降级: XPATH → XPATH fallback → CSS → JS 文本搜索。

| 字段 | 定位器 label | 必填 | 备注 |
|:---|:---|:--:|:---|
| 客户 | `请选择客户` (el-select) | ✅ | 级联触发合同下拉过滤 |
| 产品类型 | el-select | ✅ | — |
| 净重 | `净重(吨)` (el-input) | ✅ | 浮点数, `input_order_quantity()` |
| 车牌号 | `车牌号` (el-input) | ✅ | `input_vehicle_plate()` |
| 关联合同 | `请选择关联合同` (el-select) | ✅ | 按客户级联过滤 |
| 发货日期 | el-date-picker | ❌ | `input_delivery_date()` |
| 司机姓名 | el-input | ❌ | `input_driver_name()` |

对话框按钮: "保存" → `click_dialog_save()` (返回 toast) / "取消" → `click_dialog_cancel()`

**弹窗填充方式**:
- `fill_dialog_input(label, value)` (BasePage 方法) — 填充 input 字段
- `select_contract_in_dialog(search_text)` — ActionChains 点击 el-select → 逐字符 send_keys 过滤 → 点击第一个选项 → 点击弹窗标题关闭下拉

## 核心业务规则
- **客户-合同级联**: 选择客户后，关联合同下拉自动过滤为该客户的合同
- **超卖防护**: `try_oversell(customer, contract, oversized_qty)` — 净重超合同剩余量时后端拒绝 + Toast 错误 + 弹窗仍打开
- **浮点精度**: 比较使用 `round(x, 4)`

## 页面状态
- **加载中**: `_wait_table_ready()` — JS 轮询 thead th offsetHeight
- **空数据**: `el-table__empty-text`
- **错误**: `el-message--error` Toast / 表单校验错误

## 技术难点
- el-select 级联下拉 Teleport → `select_contract_in_dialog()` 逐字符 keys 过滤
- `el-button--primary` 多个实例（查询+新增）→ XPath 文本区分
- 跨 PO 依赖: 测试中引用 `CustomerPage` + `ContractPage` 获取测试数据

## 测试文件
`script/sales/test_sales_order.py`, `test_sales_order_search.py`, `test_sales_order_display.py`, `test_sales_order_crud.py`
