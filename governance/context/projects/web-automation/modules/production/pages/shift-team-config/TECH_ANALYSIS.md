# TECH_ANALYSIS — production / shift-team-config

> 基于 ShiftTeamConfigPage.py + 实地 HTML 探查 | 2026-06-12
> 页面路由: `#/production/shift-team-config` | PO: `page/production_page/ShiftTeamConfigPage.py`
> 页面类型：**CRUD 管理页**（搜索 + 表格 + 弹窗），环境无种子数据

## Element Plus 组件识别

| 组件类型 | 用途 | 定位特点 |
|----------|------|----------|
| el-input | 搜索区 工厂/班组/班次 | placeholder 唯一 |
| el-select | 搜索区 排班类型 | Teleport 到 body |
| el-button | 搜索/重置/新增 + 行内编辑/删除 | primary/default/danger 颜色 |
| el-table | 主数据表格 | 8列，含 checkbox + 操作列 |
| el-dialog | 新增/编辑弹窗 | 标题区分（"新增"/"修改"） |
| el-pagination | 分页 | "共 N 条" |

## 定位器设计表

### 搜索区
| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 工厂输入框 | CSS | `input[placeholder="请输入工厂编码"]` | A | placeholder 唯一 |
| 班组输入框 | CSS | `input[placeholder="请输入班组"]` | A | placeholder 唯一 |
| 班次输入框 | CSS | `input[placeholder="请输入班次"]` | A | placeholder 唯一 |
| 排班类型 | XPATH | `//label[contains(.,"排班类型")]/following-sibling::div//input` | B | el-select |
| 搜索 | XPATH | `//button[contains(.,"搜索")]` | B | 文本 |
| 重置 | XPATH | `//button[contains(.,"重置")]` | B | 文本 |
| 新增 | XPATH | `//button[contains(.,"新增")]` | B | 文本 |

### 表格
| 元素 | 策略 | 定位值 | 稳定性 |
|------|------|--------|--------|
| 表格 | CSS | `.el-table` | A |
| 表头 | CSS | `.el-table__header-wrapper th .cell` | A |
| 数据行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | B |
| 空状态 | CSS | `.el-empty` | B |
| 分页 | CSS | `.el-pagination__total` | A |

### 弹窗
| 元素 | 策略 | 定位值 | 稳定性 |
|------|------|--------|--------|
| 弹窗容器 | CSS | `.el-dialog:not([style*="display: none"])` | A |
| 弹窗标题 | CSS | `.el-dialog:not([style*="display: none"]) .el-dialog__title` | A |
| 弹窗字段(按label) | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//label[contains(.,"{label}")]/following-sibling::div//input` | B |
| 确定 | XPATH | 弹窗内 `//button[contains(.,"确")]` | B |
| 取消 | XPATH | 弹窗内 `//button[contains(.,"取")]` | B |

## 已知技术点

| 要点 | 处理方式 |
|------|----------|
| 排班类型实际为 el-input 而非 el-select | 使用 label 关联定位，不依赖 select 行为 |
| 页面身份验证 | `input[placeholder="请输入工厂编码"]` + `input[placeholder="请输入班组"]` 双标记 |
| 弹窗字段按 label 文本定位 | 参数化 `_DIALOG_FIELD_XPATH` 模板 |
| 环境无数据 | 搜索测试仅验证不报错，不断言行数 |
| 删除确认弹窗 | 当前未测试（需先有数据），后续补 `el-message-box` 处理 |

## 自动化代码映射
- Page Object：`page/production_page/ShiftTeamConfigPage.py`（23方法）
- 测试脚本：`script/production/test_shift_team_config.py`（5用例）
- conftest：`script/production/conftest.py`（shift_team_config_page fixture）
- 代码质量：✅ 继承BasePage、✅ 无绝对XPath、✅ 无time.sleep、✅ 无print

---
<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 -->
