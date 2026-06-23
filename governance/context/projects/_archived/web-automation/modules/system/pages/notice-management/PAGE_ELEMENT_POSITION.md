# PAGE_ELEMENT_POSITION — system / notice-management

> 基于 NoticeManagePage.py 实际定位器常量

## 搜索区
| 元素 | 定位器常量 | 策略 | 值 |
|------|-----------|------|-----|
| 标题搜索框 | NOTICE_TITLE_INPUT | XPATH | `//input[contains(@placeholder,"请输入通知标题")]` |
| 类型下拉 | NOTICE_TYPE_SELECT | XPATH | 标题输入框ancestor::form内el-select |
| 搜索按钮 | (复用BasePage) | CSS/XPath/JS | 文字"搜索" |
| 重置按钮 | (复用BasePage) | CSS/XPath/JS | 文字"重置" |

## 工具栏
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| 新增按钮 | TOOLBAR_ADD | XPATH `//div[contains(@class,"el-table__toolbar")]//button[.//span[contains(text(),"新增")]]` |

## 弹窗区
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| 弹窗面板 | DIALOG_PANEL | XPATH `(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[@role="dialog"])[last()]` |
| 弹窗确定 | DIALOG_CONFIRM | XPATH dialog内footer含"确定"按钮 |
| 弹窗取消 | DIALOG_CANCEL | XPATH dialog内footer含"取消"按钮 |
| 弹窗标题输入 | DIALOG_TITLE_INPUT | XPATH `.//input[contains(@placeholder,"请输入通知标题")]` |
| 删除确认 | DIALOG_DELETE_CONFIRM | XPATH el-message-box含确定按钮 |

## 表格区
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| 表格行 | (继承BasePage) | XPATH |
| loading | (继承BasePage) | CSS |

## 公共组件复用
| 方法 | 来源 |
|------|------|
| click_search_button() / click_reset_button() | BasePage JS文本搜索 |
| wait_table_loaded() | BasePage |

## 注意事项
- 页面使用 `el-overlay` + `el-dialog[role="dialog"]`，非标准 `.el-dialog__wrapper`
- 弹窗可能有多个 hidden overlay，需用 `[not(contains(@style,"display: none"))]` 排除
- 富文本编辑器不在此文档覆盖范围（手工测试）
