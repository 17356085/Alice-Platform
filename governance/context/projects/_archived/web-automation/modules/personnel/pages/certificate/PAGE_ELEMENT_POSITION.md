# PAGE_ELEMENT_POSITION — personnel / certificate

> 从 Selenium 实机分析提取 | 2026-06-12

## 搜索区

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 证书名称搜索框 | CSS | `input[placeholder*="请输入证书名称"]` | A |
| 证书名称搜索框(备选) | XPATH | `//input[contains(@placeholder,"证书名称")]` | A |
| 状态下拉 | XPATH | `//div[contains(@class,"search")]//div[contains(@class,"el-select")][.//label[contains(.,"状态")]]` | B |
| 查询按钮 | XPATH | `//button[.//span[normalize-space(.)="查询"]]` | A |
| 重置按钮 | XPATH | `//button[.//span[normalize-space(.)="重置"]]` | A |

## 操作按钮

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 新增证书 | XPATH | `//button[.//span[normalize-space(.)="新增证书"]]` | A |
| 证书核发 | XPATH | `//button[.//span[normalize-space(.)="证书核发"]]` | A |

## 表格

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 表格容器 | CSS | `.el-table` | A |
| 表头行 | CSS | `.el-table__header-wrapper th` | A |
| 数据行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | A |
| 空状态 | CSS | `.el-empty` / `.el-table__empty-block` | B |
| 行内操作-编辑 | XPATH | `//tr[.//td[contains(.,"{cert_name}")]]//button[contains(.,"编辑")]` | A |
| 行内操作-删除 | XPATH | `//tr[.//td[contains(.,"{cert_name}")]]//button[contains(.,"删除")]` | A |
| 行内操作-核发 | XPATH | `//tr[.//td[contains(.,"{cert_name}")]]//button[contains(.,"核发")]` | B |

## 新增/编辑弹窗

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 弹窗标题 | CSS | `.el-dialog:not([style*="display: none"]) .el-dialog__title` | A |
| 弹窗-证书名称 | CSS | `.el-dialog:not([style*="display: none"]) input[placeholder*="请输入证书名称"]` | A |
| 弹窗-用户 | CSS | `.el-dialog:not([style*="display: none"]) input[placeholder*="请输入用户名称"]` | A |
| 弹窗-证书类型 | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//label[contains(.,"证书类型")]/following::div[contains(@class,"el-select")][1]` | A |
| 弹窗-颁发机构 | CSS | `.el-dialog:not([style*="display: none"]) input[placeholder*="请输入颁发机构"]` | A |
| 弹窗-颁发日期 | CSS | `.el-dialog:not([style*="display: none"]) input[placeholder*="请选择颁发日期"]` | A |
| 弹窗-有效期 | CSS | `.el-dialog:not([style*="display: none"]) input[placeholder*="开始日期"]` | A |
| 弹窗-永久有效 | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//label[contains(.,"永久有效")]/following::*[contains(@class,"el-switch") or contains(@class,"el-checkbox")][1]` | B |
| 弹窗-备注 | CSS | `.el-dialog:not([style*="display: none"]) input[placeholder*="请输入备注"]` | A |
| 弹窗-取消按钮 | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[.//span[normalize-space(.)="取消"]]` | A |
| 弹窗-确定按钮 | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[.//span[normalize-space(.)="确定"]]` | A |
| 弹窗-关闭(X) | CSS | `.el-dialog:not([style*="display: none"]) .el-dialog__headerbtn` | B |

## 分页

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 分页容器 | CSS | `.el-pagination` | A |
| 总数 | CSS | `.el-pagination__total` | B |
| 每页条数 | CSS | `.el-pagination__sizes .el-select` | B |

## 删除确认弹窗

| 元素 | 策略 | 定位值 | 等级 |
|------|------|--------|:--:|
| 确认框 | CSS | `.el-message-box:not([style*="display: none"])` | A |
| 确认按钮 | XPATH | `//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))]//button[.//span[normalize-space(.)="确定"]]` | A |

> 定位器等级: A=生产可用(稳定) / B=需验证 / C=临时方案(文字匹配, 可能随版本变更)
> 
> 注: 当前页面无测试数据，表格为空。部分定位器（如行内操作按钮、状态筛选下拉选项）需在录入测试数据后验证。

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 -->
