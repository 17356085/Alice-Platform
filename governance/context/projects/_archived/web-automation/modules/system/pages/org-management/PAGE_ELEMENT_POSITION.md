# PAGE_ELEMENT_POSITION — system / org-management

> 基于 OrgManagePage.py 实际定位器常量

## 搜索区
| 元素 | 定位器常量 | 策略 | 值 |
|------|-----------|------|-----|
| 组织名称输入 | ORG_NAME_INPUT | XPATH | `//input[contains(@placeholder,"组织名称")]` |
| 组织类型下拉 | ORG_TYPE_SELECT_FALLBACK | XPATH | `.//div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"组织类型")]]//div[contains(@class,"el-select")]` |
| 状态下拉 | STATUS_SELECT_FALLBACK | XPATH | `.//div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"状态")]]//div[contains(@class,"el-select")]` |
| 搜索按钮 | SEARCH_BUTTON | XPATH | `//button[.//*[normalize-space(.)="搜索" or normalize-space(.)="查询"]]` |
| 重置按钮 | RESET_BUTTON | XPATH | `//button[.//*[normalize-space(.)="重置"]]` |

## 工具栏
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| 新增按钮 | TOOLBAR_ADD | XPATH `//button[.//span[normalize-space(.)="新增"]]` |
| 导出按钮 | TOOLBAR_EXPORT_FALLBACK | XPATH 含"导出"文字 |

## 表格区
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| 表格行 | TABLE_ROWS (继承BasePage) | XPATH |
| 第1行查看 | FIRST_ROW_VIEW_BUTTON_FALLBACK | XPATH `(//tr[...]//td[last()]//button[1]` |
| 第1行编辑 | FIRST_ROW_EDIT_BUTTON_FALLBACKS | XPATH `(//tr[...]//td[last()]//button[2]` |

## 弹窗区
| 元素 | 策略 |
|------|------|
| 确认弹窗 | `.el-message-box` |
| 弹窗确认按钮 | `//div[contains(@class,"el-message-box")]//button[2]` |

## 公共组件复用
| 方法 | 来源 | 用途 |
|------|------|------|
| click_search_button() | BasePage | JS文本搜索+点击 |
| click_reset_button() | BasePage | JS文本搜索+点击 |
| get_table_rows() | BasePage | el-table__row 计数 |
| wait_table_loaded() | BasePage | loading消失等待 |
