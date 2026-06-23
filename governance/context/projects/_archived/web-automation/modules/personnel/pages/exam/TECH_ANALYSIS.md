# TECH_ANALYSIS — personnel / exam

## 分析对象
- 模块：personnel | 页面：考试管理 | 代码：ExamManagePage.py (856行)

## 定位器设计表（从代码提取）
| 元素 | 策略 | 定位值 | 稳定性 |
|------|------|--------|--------|
| 搜索-名称 | XPATH | `//input[contains(@placeholder,'考试名称')]` | A |
| 搜索-状态下拉 | XPATH | `//div[contains(@class,'el-select')][.//label[contains(.,'状态')]]` | B |
| 搜索-发布状态下拉 | XPATH | `//div[contains(@class,'el-select')][.//label[contains(.,'发布状态')]]` | B |
| 搜索-日期 | XPATH | `//input[contains(@placeholder,'开始日期') or contains(@placeholder,'结束日期')]` | A |
| 搜索按钮 | XPATH | `//button[.//span[contains(text(),'查询') or contains(text(),'搜索')]]` | A |
| 重置按钮 | XPATH | `//button[.//span[contains(text(),'重置')]]` | A |

## 异步等待策略
| 场景 | 条件 |
|------|------|
| 页面加载 | 表格行数 ≥ 0 |
| 阅卷模式 | 考生答卷区 + 评分表单可见 |

## 自动化代码
- Page Object: `page/personnel_page/ExamManagePage.py`
- 测试: `script/personnel/test_exam_management.py`
