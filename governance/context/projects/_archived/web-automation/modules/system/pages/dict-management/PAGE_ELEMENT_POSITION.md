# PAGE_ELEMENT_POSITION — system / dict-management

> 基于 DictManagePage.py 实际定位器常量

## 分类面板(左侧)
| 元素 | 定位器常量 | 策略 | 值 |
|------|-----------|------|-----|
| 字典标签页 | TAB_DICT | XPATH | `//div[contains(@class,"el-tabs__item") and normalize-space(.)="字典"]` |
| 字典分类标签页 | TAB_DICT_CATEGORY | XPATH | `//div[contains(@class,"el-tabs__item") and normalize-space(.)="字典分类"]` |
| 筛选-全部 | CATEGORY_FILTER_ALL | XPATH | radio-button含"全部" |
| 筛选-系统 | CATEGORY_FILTER_SYSTEM | XPATH | radio-button含"系统" |
| 筛选-自定义 | CATEGORY_FILTER_CUSTOM | XPATH | radio-button含"自定义" |
| 分类搜索框 | CATEGORY_SEARCH_INPUT | XPATH | `//input[contains(@placeholder,"搜索字典分类")]` |
| 新增分类按钮 | CATEGORY_ADD_BUTTON_FALLBACK | XPATH | dict-type-panel内含"新增"按钮 |

## 明细表格(右侧)
| 元素 | 定位器常量 | 值 |
|------|-----------|-----|
| 字典标签搜索 | DICT_LABEL_INPUT | `//input[contains(@placeholder,"字典") and contains(@placeholder,"标签")]` |
| 搜索按钮 | SEARCH_BUTTON | 文字"搜索" |
| 状态下拉 | STATUS_SELECT / STATUS_SELECT_TRIGGER | el-select含"状态"label |
| 新增按钮 | TOOLBAR_ADD | 文字"新增" |
| 导出按钮 | TOOLBAR_EXPORT | 文字"导出" |
| 第1行编辑 | FIRST_ROW_EDIT_BUTTON | 行内含"编辑"文字 |
| 第1行删除 | FIRST_ROW_DELETE_BUTTON | 行内含"删除"文字 |

## 弹窗区
| 元素 | 定位器常量 |
|------|-----------|
| 确认弹窗 | MESSAGEBOX_CONFIRM (多级降级) |

## 公共组件复用
| 方法 | 来源 |
|------|------|
| click_search_button() / click_reset_button() | BasePage |
| get_table_rows() / get_total_count() | BasePage |
| wait_table_loaded() | BasePage |
