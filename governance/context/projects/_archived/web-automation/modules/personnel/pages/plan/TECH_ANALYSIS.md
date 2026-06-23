# TECH_ANALYSIS — personnel / plan

## 分析对象
- 模块：personnel | 页面：培训计划 | 代码：TrainPlanPage.py (1528行，最大PageObject)

## 定位器设计表（从代码提取）
| 元素 | 策略 | 定位值 | 稳定性 |
|------|------|--------|--------|
| 搜索-名称 | XPATH | `//input[contains(@placeholder,'计划名称')]` | A |
| 搜索-类型下拉 | XPATH | 搜索区 el-select [1] | B |
| 搜索-状态下拉 | XPATH | 搜索区 el-select [2] | B |
| 搜索-发布下拉 | XPATH | 搜索区 el-select [3] | B |
| 搜索按钮 | XPATH | `//button[.//span[contains(text(),'查询') or contains(text(),'搜索')]]` | A |
| 重置按钮 | XPATH | `//button[.//span[contains(text(),'重置')]]` | A |
| 表格行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | A |

## 异步等待策略
| 场景 | 条件 |
|------|------|
| 页面加载 | 表格行数 ≥ 0 |
| 多步骤弹窗 | 每步切换后等待该步骤元素可见 |
| 搜索完成 | loading 消失 |

## 自动化代码
- Page Object: `page/personnel_page/TrainPlanPage.py`
- 测试: `script/personnel/test_train_plan_management.py`
