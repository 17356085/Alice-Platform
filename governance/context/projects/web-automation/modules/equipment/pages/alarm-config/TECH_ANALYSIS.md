# TECH_ANALYSIS — equipment / alarm-config

> 产出于 automation-implementation Workflow 实战验证（2026-06-11）
> 基于：AlarmConfigPage.py 已有代码 + PAGE_CONTEXT.md

## 分析对象
- 模块：equipment
- 页面：设备报警配置
- 自动化目标：覆盖统计卡片/搜索/表格/分页（稳定方法） + 弹窗CRUD（待攻克 Element Plus 2.x is_displayed 问题）

## 技术要点

### Element Plus 组件识别
| 组件类型 | 用途 | 定位特点 |
|----------|------|----------|
| el-form--inline | 搜索区容器 | 2个 el-select + 1个 el-input |
| el-select (filterable) | 报警类型/报警级别/状态筛选 | ⚠️ filterable + teleport → is_displayed() 对 body 层选项失效 |
| el-input | 关键词搜索框 | placeholder="报警名称/设备名称" |
| el-table | 报警配置列表 | 多列 + 操作列(编辑/删除/开关) |
| el-switch | 启用/禁用开关 | 行内操作 |
| el-dialog | 新增/编辑弹窗 | ⚠️ 多弹窗共存于DOM，需排除 display:none |
| el-pagination | 分页器 | 标准 Element Plus 分页 |

### 定位器设计表（从现有代码提取）
| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 统计卡片容器 | CSS | `.stat-value` | B | 非BEM命名 |
| 统计-总数 | XPATH | `//*[contains(text(),'总数')]/preceding-sibling::*[1]` | B | 需参数化 label |
| 搜索输入框 | CSS | `input[placeholder='报警名称/设备名称']` | A | placeholder 稳定 |
| 报警类型下拉 | XPATH | `(//form[contains(@class,'el-form--inline')]//div[contains(@class,'el-select')])[1]` | B | 位置索引 |
| 报警级别下拉 | XPATH | `(//form[contains(@class,'el-form--inline')]//div[contains(@class,'el-select')])[2]` | B | 位置索引 |
| 状态下拉 | XPATH | `(//form[contains(@class,'el-form--inline')]//div[contains(@class,'el-select')])[3]` | B | 位置索引 |
| 搜索按钮 | XPATH | `//button[.//span[text()='搜索']]` | A | 文字固定 |
| 重置按钮 | XPATH | `//button[.//span[text()='重置']]` | A | |
| 新增按钮 | XPATH | `//button[.//span[text()='新增']]` | A | |
| 表格容器 | CSS | `.el-table` | A | |
| 表格行 | CSS | `.el-table__body-wrapper .el-table__row` | B | |
| 弹窗 | CSS | `.el-dialog` | B | 多弹窗共存 |
| 弹窗确认 | XPATH | `//div[contains(@class,'el-dialog') and not(contains(@style,'display: none'))]//button[.//span[text()='确定']]` | B | |
| 分页器 | CSS | `.el-pagination` | A | |

### 已知技术难题
| 问题 | 影响 | 当前处理 |
|------|------|----------|
| Element Plus 2.x filterable select 选项 teleport 到 body | is_displayed() 对 body 层元素失效 | 弹窗CRUD方法标记 @skip，改用 API 层验证 |
| 多弹窗共存于 DOM（display:none 不移除） | 定位器容易选到隐藏弹窗 | 用 `not(contains(@style,'display: none'))` 排除 |
| el-switch 非标准 form 控件 | click() 行为不可靠 | 使用 JS click 降级 |

### 异步等待策略
| 场景 | 等待条件 | 实现 |
|------|----------|------|
| 页面加载 | 表格出现 | `wait_table_loaded()` (BasePage) |
| 搜索完成 | loading 消失 | `wait_loading_disappear()` (BasePage) |
| 弹窗打开 | el-dialog visible | `wait_dialog_visible()` (BasePage) |
| 弹窗关闭 | el-dialog invisible | `wait.until(EC.invisibility_of_element_located(DIALOG))` |

## 自动化代码映射
- Page Object：`page/equipment_page/AlarmConfigPage.py`（已实现，部分弹窗方法 @skip）
- 测试脚本：`script/equipment/test_alarm_config.py`（P0/P1 稳定，P2+ 弹窗通过 API 绕过）
- conftest：`script/equipment/conftest.py`
- 测试数据：`data/alarm_config_data.py`
