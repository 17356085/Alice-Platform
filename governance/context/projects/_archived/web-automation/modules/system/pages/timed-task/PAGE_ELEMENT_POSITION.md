# PAGE_ELEMENT_POSITION — system / timed-task

> 基于 TimedTaskPage.py 实际定位器常量

## 搜索区
| 元素 | 定位器常量 | 策略 | 值 |
|------|-----------|------|-----|
| 任务名称输入 | TASK_NAME_INPUT | CSS | `input[placeholder*="请输入任务名称"]` |
| 任务类型下拉 | TASK_TYPE_SELECT | XPATH | label含"任务类型"的el-select |
| 状态-全部 | STATUS_ALL | XPATH | radio含"全部" |
| 状态-运行中 | STATUS_RUNNING | XPATH | radio含"运行中" |
| 状态-已暂停 | STATUS_PAUSED | XPATH | radio含"已暂停"或"已停停" |
| 搜索按钮 | SEARCH_BUTTON | XPATH | 文字"搜索" |
| 重置按钮 | RESET_BUTTON | XPATH | 文字"重置" |

## 工具栏
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| 新增按钮 | TOOLBAR_ADD | XPATH 文字"新增" |
| 修改按钮 | TOOLBAR_EDIT | XPATH 文字"修改" |
| 删除按钮 | TOOLBAR_DELETE | XPATH 文字"删除" |
| 日志按钮 | TOOLBAR_LOG | XPATH 文字"日志" |

## 弹窗/抽屉
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| 弹窗面板 | DIALOG_PANEL | XPATH `(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]` |
| 弹窗确定 | DIALOG_CONFIRM | XPATH dialog内"确定"或"保存"按钮 |
| 弹窗取消 | DIALOG_CANCEL | XPATH dialog内"取消"按钮 |
| Cron抽屉 | CRON_VISUAL_DRAWER | XPATH `//div[contains(@class,"cron-generator-drawer")]` |
| Cron确认 | CRON_VISUAL_CONFIRM | XPATH drawer内"确认使用"按钮 |

## 下拉面板
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| 下拉选项 | SELECT_DROPDOWN_PANEL | XPATH `(//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))])[last()]` |

## 注意事项
- 状态radio文字可能有变体("已暂停"/"已停停")，需用contains宽松匹配
- Cron生成器为独立drawer组件，不建议自动化覆盖
