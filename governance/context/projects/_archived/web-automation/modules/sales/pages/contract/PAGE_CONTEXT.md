# PAGE_CONTEXT — sales / contract

> 从 ContractPage.py 实际代码提取 | 2026-06-17 | 覆盖过期文档

## 页面信息
- **页面名称**: 合同管理
- **路由**: `#/sales/contract`
- **PO**: `page/sales_page/ContractPage.py` (继承 BasePage + ElementPlusHelper)
- **侧边栏导航**: `navigate_to("销售管理", "合同管理")`
- **页面性质**: 只读查询+行操作（非 CRUD 页面，无编辑/删除按钮）

## 页面整体结构

顶部全局导航栏 → 左侧菜单 → 主内容区：
1. **搜索/筛选区**: 2 个 el-input + 2 个 el-select + 1 个 el-date-picker range + 3 个 el-button
2. **表格区**: el-table 8 列，含 el-progress 进度条 + el-tag 状态标签
3. **分页区**: el-pagination（每页条数 + 翻页 + 总条数）

## 搜索/筛选区

| 元素ID | 描述 | 控件类型 | 定位器 (CSS) | 定位器 (XPath) | 等级 |
|:---|:---|:---|:---|:---|:--:|
| `SEARCH_CONTRACT_NO` | 合同编号 | el-input | `input[placeholder="合同编号"]` | `//input[@placeholder="合同编号"]` | A |
| `SEARCH_CUSTOMER` | 客户名称 | el-input | `input[placeholder="客户名称"]` | `//input[@placeholder="客户名称"]` | A |
| `SEARCH_PRODUCT_TYPE` | 产品类型 | el-select | — | `//div[contains(@class,"el-select")][.//div[contains(@class,"el-select__placeholder")]/span[contains(normalize-space(.),"产品类型")]]` | B |
| `SEARCH_STATUS` | 合同状态 | el-select | — | `//div[contains(@class,"el-select")][.//div[contains(@class,"el-select__placeholder")]/span[contains(normalize-space(.),"合同状态")]]` | B |
| `SEARCH_START_DATE` | 有效期起 | el-date-picker | `input[placeholder="有效期起"]` | — | B |
| `SEARCH_END_DATE` | 有效期止 | el-date-picker | `input[placeholder="有效期止"]` | — | B |
| `BTN_SEARCH` | 查询 | el-button (primary) | `button.el-button--primary:not(.is-link)` | `//button[contains(@class,"el-button--primary")]//span[contains(normalize-space(.),"查询")]/parent::button` | A |
| `BTN_RESET` | 重置 | el-button (default) | `button.el-button:not([class*="el-button--"])` | `//button[not(contains(@class,"el-button--primary"))]//span[contains(normalize-space(.),"重置")]/parent::button` | A |
| `BTN_ADD` | 新增合同 | el-button | `button.el-button--success:not(.is-link)` | `//button[contains(@class,"el-button")]//span[contains(normalize-space(.),"新增合同")]/parent::button` | A |

> **注意**: 按钮文本为"查询"（非"搜索"），"新增合同"（非"新建合同"）。无导出按钮。

## 表格区

| 列索引 | COL 常量 | 列名 | 数据类型 | 备注 |
|:--:|:---|:---|:---|:---|
| 1 | `COL_CONTRACT_NO` | 合同编号 | 文本 | — |
| 2 | `COL_CUSTOMER_NAME` | 客户名称 | 文本 | — |
| 3 | `COL_PRODUCT` | 产品 | 文本 | — |
| 4 | `COL_TOTAL_QTY` | 合同总量(吨) | 数字 | — |
| 5 | `COL_EXECUTED_QTY` | 已执行量 | 进度条 | el-progress 百分比 + span.text-xs 文本 |
| 6 | `COL_EXPIRE_DATE` | 有效期至 | 日期 | — |
| 7 | `COL_STATUS` | 状态 | el-tag | `el-tag--danger`=已终止, `el-tag--success`=已完成 |
| 8 | `COL_OPERATIONS` | 操作 | 按钮组 | 详情 + 销售订单 |

### 行操作
| 操作 | 定位器 | 备注 |
|:---|:---|:---|
| 详情 | `//button[contains(.,"详情")]` | 始终显示 |
| 销售订单 | `//button[contains(.,"销售订单")]` | 生效中状态显示 |

> **注意**: 无"编辑"和"删除"按钮。已终止合同显示"详情"，生效中合同显示"详情+销售订单"。

### 特殊元素
| 元素 | 定位器 | 说明 |
|:---|:---|:---|
| 进度条 | CSS `.el-progress-bar__inner` | 3s CSS 动画，需等待动画完成 |
| 进度文本 | CSS `tr.el-table__row td:nth-child(5) .cell span.text-xs` | 百分比文本 |
| 状态标签 | CSS `span.el-tag--danger` / `span.el-tag--success` | 根据状态动态渲染 |

## 弹窗（新增合同）

PO 中通过 `click_add()` 打开。弹窗字段：

| 字段 | 定位器 placeholder | 必填 |
|:---|:---|:--:|
| 客户 | `请选择客户` (el-select filterable) | ✅ |
| 产品类型 | `产品类型` (el-select) | ✅ |
| 合同金额 | `合同金额(万元)` (el-input) | ✅ |
| 合同总量 | `合同总量(吨)` (el-input) | ✅ |
| 生效日期 | `生效日期` (el-date-picker) | ✅ |
| 有效期至 | `有效期至` (el-date-picker) | ✅ |
| 附件 | `.el-upload` | ❌ |

对话框按钮: "确定" / "取消"

## 页面状态
- **加载中**: `el-loading-mask` 遮罩
- **空数据**: `el-table__empty-text`
- **错误**: `el-message--error` Toast

## 技术难点
- el-progress 3s CSS 动画过渡 → 需等待宽度稳定再断言
- el-select filterable option 渲染到 `<body>` 下的 popper（Teleport）
- el-date-picker range 弹出层也在 body 下
- 多弹窗 DOM 共存（Vue keep-alive）
- ElementPlusHelper 辅助处理 select/datepicker 操作

## 测试文件
`script/sales/test_contract.py`, `test_contract_display.py`, `test_contract_search.py`, `test_contract_pagination.py`, `test_contract_workflow.py`
