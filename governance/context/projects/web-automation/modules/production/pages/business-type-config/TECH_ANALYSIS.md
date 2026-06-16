# TECH_ANALYSIS — production / business-type-config

> 基于 BusinessTypeConfigPage.py + 实地 HTML 探查 | 2026-06-12
> 页面路由: `#/production/business-type-config` | PO: `page/production_page/BusinessTypeConfigPage.py`
> 页面类型：**CRUD 管理页**（17字段复杂表单 + 批量删除），**production 模块最复杂页面**

## Element Plus 组件识别

| 组件类型 | 用途 | 定位特点 |
|----------|------|----------|
| el-input | 搜索区 计划参数/工厂/物料编码 + 弹窗 17字段 | placeholder 唯一 |
| el-select | 搜索区 业务类型 | Teleport 到 body |
| el-button | 搜索/重置/新增/删除(页面级) + 行内编辑/删除 | primary/danger/link 颜色 |
| el-table | 主数据表格 | 11列，含 checkbox + 操作列(fixed) |
| el-checkbox | 表格首列 + 表头全选 | 行级勾选 + 全选 |
| el-dialog | 新增/编辑弹窗 | 标题区分（"新增"/"修改"），17字段 |
| el-pagination | 分页 | "共 14 条" |

## 定位器设计表

### 搜索区
| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 计划参数 | CSS | `input[placeholder="请输入计划参数"]` | A | placeholder 唯一 |
| 工厂 | CSS | `input[placeholder="请输入工厂编码"]` | A | |
| 物料编码 | CSS | `input[placeholder="请输入物料编码"]` | A | placeholder 唯一 |
| 业务类型 | XPATH | `//label[contains(.,"业务类型")]/following-sibling::div//input` | B | el-select |
| 搜索 | XPATH | `//button[contains(.,"搜索")]` | B | |
| 重置 | XPATH | `//button[contains(.,"重置")]` | B | |
| 新增 | XPATH | `//button[contains(.,"新增")]` | B | |
| 删除(页面级) | XPATH | `//button[contains(.,"删除")]` | B | ⚠️ 默认 disabled |

### 表格
| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 表格行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | B | 10行可见 |
| 表头 | CSS | `.el-table__header-wrapper th .cell` | A | 含 "计划参数(ZPLPA)" |
| 分页总数 | CSS | `.el-pagination__total` | A | "共 14 条" |
| 行 checkbox | CSS | 行内 `.el-checkbox` | B | |
| 行编辑按钮 | XPATH | 行内 `.//button[contains(.,"编辑")]` | B | |
| 行删除按钮 | XPATH | 行内 `.//button[contains(.,"删除")]` | B | |

### 弹窗（17字段）
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
| 计划参数表头含 (ZPLPA) | 断言用包含匹配 `any(col in h for h in headers)` |
| 页面级删除默认 disabled | `is_batch_delete_enabled()` 检查 `is-disabled` class |
| 17字段弹窗 | `fill_dialog_field(label, value)` 按 label 参数化填写 |
| 14条数据分页 | `get_pagination_total()` 验证总数；`get_row_count()` 当前页行数 |
| 页面身份验证 | `input[placeholder="请输入计划参数"]` + `input[placeholder="请输入物料编码"]` 双标记 |
| 编辑弹窗回填 | 点击行编辑后弹窗字段有默认值，验证标题区分"新增/修改" |

## 自动化代码映射
- Page Object：`page/production_page/BusinessTypeConfigPage.py`（26方法）
- 测试脚本：`script/production/test_business_type_config.py`（8用例）
- conftest：`script/production/conftest.py`（business_type_config_page fixture）
- 代码质量：✅ 继承BasePage、✅ 无绝对XPath、✅ 无time.sleep、✅ 无print

---
<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 -->
