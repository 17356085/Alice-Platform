# TECH_ANALYSIS — personnel / certificate

## 分析对象
- 模块：personnel | 页面：证书管理 | 代码：待开发
- 页面类型：标准 CRUD 管理页（表格+弹窗表单）

## 定位器设计表
| 元素 | 策略 | 定位值 | 稳定性 |
|------|------|--------|--------|
| 新增证书按钮 | XPATH | `//button[.//span[normalize-space(.)="新增证书"]]` | A |
| 证书核发按钮 | XPATH | `//button[.//span[normalize-space(.)="证书核发"]]` | A |
| 搜索-证书名称 | CSS | `input[placeholder*="请输入证书名称"]` | A |
| 搜索-状态下拉 | XPATH | `//div[contains(@class,"search")]//div[contains(@class,"el-select")]` | B |
| 查询按钮 | XPATH | `//button[.//span[normalize-space(.)="查询"]]` | A |
| 重置按钮 | XPATH | `//button[.//span[normalize-space(.)="重置"]]` | A |
| 表格容器 | CSS | `.el-table` | A |
| 表头行 | CSS | `.el-table__header-wrapper th` | A |
| 数据行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | A |
| 弹窗-证书名称 | CSS | `.el-dialog:not([style*="display: none"]) input[placeholder*="请输入证书名称"]` | A |
| 弹窗-用户 | CSS | `.el-dialog:not([style*="display: none"]) input[placeholder*="请输入用户名称"]` | A |
| 弹窗-证书类型 | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//label[contains(.,"证书类型")]/following::div[contains(@class,"el-select")][1]` | A |
| 弹窗-颁发机构 | CSS | `.el-dialog:not([style*="display: none"]) input[placeholder*="请输入颁发机构"]` | A |
| 弹窗-颁发日期 | CSS | `.el-dialog:not([style*="display: none"]) input[placeholder*="请选择颁发日期"]` | A |
| 弹窗-有效期 | CSS | `.el-dialog:not([style*="display: none"]) input[placeholder*="开始日期"]` | A |
| 弹窗-永久有效 | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//label[contains(.,"永久有效")]/following::*[contains(@class,"el-switch") or contains(@class,"el-checkbox")][1]` | B |
| 弹窗-备注 | CSS | `.el-dialog:not([style*="display: none"]) input[placeholder*="请输入备注"]` | A |
| 弹窗-确定 | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[.//span[normalize-space(.)="确定"]]` | A |
| 弹窗-取消 | XPATH | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[.//span[normalize-space(.)="取消"]]` | A |
| 行内编辑 | XPATH | `//tr[.//td[contains(.,"{cert_name}")]]//button[contains(.,"编辑")]` | A |
| 行内删除 | XPATH | `//tr[.//td[contains(.,"{cert_name}")]]//button[contains(.,"删除")]` | A |
| 删除确认-确定 | XPATH | `//div[contains(@class,"el-message-box")]//button[.//span[normalize-space(.)="确定"]]` | A |
| 分页容器 | CSS | `.el-pagination` | A |
| 空状态 | CSS | `.el-empty` | B |

## 异步等待策略
| 场景 | 条件 |
|------|------|
| 页面加载 | 表格或空状态出现 |
| 搜索/筛选完成 | loading 遮罩消失 |
| 弹窗打开 | el-dialog visible + 表单渲染完成 |
| 弹窗提交 | loading 消失 + dialog 关闭 + toast 出现 |
| 删除完成 | 确认弹窗消失 + toast 出现 |

## 自动化代码
- Page Object: `page/personnel_page/CertificateManagePage.py`（待创建）
- 测试: `script/personnel/test_certificate_management.py`（待创建）
- conftest: 已有，需添加 `test_certificate_management` 路由映射
