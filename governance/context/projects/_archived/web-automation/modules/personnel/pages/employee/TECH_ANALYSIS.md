# TECH_ANALYSIS — personnel / employee

## 分析对象
- 模块：personnel | 页面：员工管理 | 代码：EmployeeManagePage.py (123行)

## 定位器设计表（从代码提取）
| 元素 | 策略 | 定位值 | 稳定性 |
|------|------|--------|--------|
| 页面标题 | XPATH | `//h2[contains(text(),'员工') or contains(text(),'人员')]` | A |
| 表格行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | A |
| 表头 | XPATH | `//div[contains(@class,'el-table__header-wrapper')]//th//div[contains(@class,'cell')]` | A |
| 总条数 | CSS | `.el-pagination__total` | A |
| 下一页 | CSS | `.el-pagination .btn-next` | A |
| 上一页 | CSS | `.el-pagination .btn-prev` | A |
| 搜索-姓名/工号 | XPATH | `//input[contains(@placeholder,'姓名') or contains(@placeholder,'工号')]` | A |
| 搜索-部门 | XPATH | `//input[contains(@placeholder,'搜索部门')]` | A |

## 异步等待策略
| 场景 | 条件 |
|------|------|
| 页面加载 | 表格行数 ≥ 0 + 表头不为空 |
| 搜索完成 | loading 消失 + 表格行数稳定 |

## 自动化代码
- Page Object: `page/personnel_page/EmployeeManagePage.py`
- 测试: `script/personnel/test_employee_management.py`
