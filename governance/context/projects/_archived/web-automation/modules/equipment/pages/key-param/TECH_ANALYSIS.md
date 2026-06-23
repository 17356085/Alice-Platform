# TECH_ANALYSIS — equipment / key-param

> 从现有 KeyParamPage.py 代码提取定位器 | 2026-06-11
> 页面类型: 统计卡片 + el-table，非标准搜索区（裸input无placeholder无el-form）

## Element Plus 组件识别

| 组件 | 用途 | 定位特点 |
|------|------|----------|
| stat-card (BEM) | 4张统计卡片 | BEM命名 stat-card__label / stat-card__value |
| el-table | 9列参数数据表格 | 无 fixed="right"，无 .table-wrapper |
| el-pagination | 分页器 | 标准 |
| el-dialog | 详情弹窗 + 编辑弹窗 | 标准 el-dialog，有CRUD |
| input (裸) | 关键词搜索 | ⚠️ 无placeholder，无el-form，需JS定位 |

## 定位器设计表

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 统计卡片容器 | CSS | `.stat-card` | A | BEM命名 |
| 总监测参数 | XPATH | `//div[contains(@class,"stat-card")][.//div[contains(@class,"stat-card__label") and normalize-space(.)="总监测参数"]]//div[contains(@class,"stat-card__value")]` | A | |
| 正常运行 | XPATH | `//div[contains(@class,"stat-card")][.//div[contains(@class,"stat-card__label") and normalize-space(.)="正常运行"]]//div[contains(@class,"stat-card__value")]` | A | |
| 预警参数 | XPATH | `//div[contains(@class,"stat-card")][.//div[contains(@class,"stat-card__label") and normalize-space(.)="预警参数"]]//div[contains(@class,"stat-card__value")]` | A | |
| 报警参数 | XPATH | `//div[contains(@class,"stat-card")][.//div[contains(@class,"stat-card__label") and normalize-space(.)="报警参数"]]//div[contains(@class,"stat-card__value")]` | A | |
| 关键词输入 | XPATH | `//input[not(ancestor::div[contains(@class,"el-pagination")]) and not(ancestor::div[contains(@class,"el-switch")]) and not(ancestor::div[contains(@class,"el-select")]) and not(@type="hidden")]` | C | ⚠️ 复杂排除规则，脆弱 |
| 重置按钮 | XPATH | `//button[contains(@class,"el-button--danger")]//span[contains(.,"重置")]` | B | danger样式 |
| 表格容器 | CSS | `.el-table` | A | |
| 表格行 | CSS | `.el-table__body-wrapper .el-table__row` | B | |
| 查看按钮(行内) | XPATH | `.//button[contains(.,'查看')]` | B | |
| 编辑按钮(行内) | XPATH | `.//button[contains(.,'编辑')]` | B | |
| 删除按钮(行内) | XPATH | `.//button[contains(.,'删除')]` | B | |
| 运行状态文本 | CSS | `.el-table__row td:nth-child(N)` | C | 纯文本无el-tag，按列索引 |
| 弹窗 | CSS | `.el-dialog` | A | 标准 el-dialog |
| 弹窗确认 | XPATH | `//div[contains(@class,'el-dialog') and not(contains(@style,'display: none'))]//button[.//span[text()='确定']]` | B | |
| 分页器 | CSS | `.el-pagination` | A | |

## 异步等待策略

| 场景 | 等待条件 | 实现 |
|------|----------|------|
| 页面加载 | 表格+统计卡片出现 | `wait_table_loaded()` + `presence_of_element_located(STAT_CARD)` |
| 搜索完成 | 表格行数变化 | 自定义等待：old_rows != new_rows |
| 弹窗打开 | el-dialog visible | `wait_dialog_open()` |
| 弹窗关闭 | el-dialog invisible | `invisibility_of_element_located(DIALOG)` |

## 已知技术难点

| 问题 | 影响 | 处理 |
|------|------|------|
| 搜索区无标准结构 | 定位器使用复杂排除规则(C级)，脆弱 | JS定位作为替代：`document.querySelector('input:not([type="hidden"])')` |
| 运行状态为纯文本 | 无法用 el-tag class 定位 | 按列索引(1-based)获取文本 |
| 无 .search-wrapper | 定位器无法加容器前缀 | 使用全局选择器，注意排除分页/开关内的input |
| 关键词输入框无placeholder | 无法用[placeholder*="..."]定位 | 依赖排除规则，建议后续添加 data-testid |

## 代码映射

- Page Object: `page/equipment_page/KeyParamPage.py`
- 测试脚本: `script/equipment/test_key_param.py`
- conftest: `script/equipment/conftest.py`

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 | next_phase: Phase 3.5/4 | next_agent: automation-agent -->
