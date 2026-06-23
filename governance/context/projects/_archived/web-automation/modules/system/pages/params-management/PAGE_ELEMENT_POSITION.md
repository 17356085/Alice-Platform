# PAGE_ELEMENT_POSITION — system / params-management

> 基于 ParamsManagePage.py 实际定位器常量

## 搜索区
| 元素 | 定位器常量 | 策略 | 值 |
|------|-----------|------|-----|
| 参数名称输入 | PARAM_NAME_INPUT | XPATH | `//input[@placeholder="请输入参数名称"]` |
| 参数键名输入 | PARAM_KEY_INPUT | XPATH | `//input[@placeholder="请输入参数键名"]` |
| 参数类型下拉 | PARAM_TYPE_SELECT | XPATH | label含"参数类型"的el-select |
| 业务模块下拉 | BUSINESS_MODULE_SELECT | XPATH | label含"业务模块"的el-select |
| 搜索按钮 | SEARCH_BUTTON | XPATH | `//button[.//span[normalize-space(.)="搜索"]]` |
| 重置按钮 | RESET_BUTTON | XPATH | `//button[.//span[normalize-space(.)="重置"]]` |

## 工具栏
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| 新增按钮 | TOOLBAR_ADD | XPATH 文字"新增" |
| 导出按钮 | TOOLBAR_EXPORT | XPATH 文字"导出" |
| 刷新缓存 | TOOLBAR_REFRESH_CACHE | XPATH 文字"刷新缓存" |

## 表格区
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| 表格行 | TABLE_ROWS | XPATH `//div[contains(@class,"el-table__body-wrapper")]//table/tbody/tr` |
| 空文本 | EMPTY_TEXT | CSS `.el-table__empty-text` |
| 表头 | TABLE_HEADERS | XPATH `//div[contains(@class,"el-table__header-wrapper")]//th//div` |
| loading | LOADING_MASK | CSS `.el-loading-mask` |

## 分页区
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| 分页器 | PAGINATION | CSS `.el-pagination` |
| 当前页 | CURRENT_PAGE | CSS `.el-pagination .el-pager li.active` |
| 下一页 | NEXT_PAGE_BUTTON | CSS `.el-pagination .btn-next` |

## 弹窗区
| 元素 | 定位器常量 |
|------|-----------|
| 确认弹窗-确定 | MESSAGEBOX_CONFIRM |
| 确认弹窗-取消 | MESSAGEBOX_CANCEL |

## 公共组件复用
| 方法 | 来源 |
|------|------|
| click_search_button() / click_reset_button() | BasePage |
| get_table_rows() / get_total_count() | BasePage |
