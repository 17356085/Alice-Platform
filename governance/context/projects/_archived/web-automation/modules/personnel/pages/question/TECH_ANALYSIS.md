# TECH_ANALYSIS — personnel / question

## 分析对象
- 模块：personnel | 页面：题库管理 | 代码：QuestionBankPage.py (702行)

## 定位器设计表（从代码提取）
| 元素 | 策略 | 定位值 | 稳定性 |
|------|------|--------|--------|
| 搜索-题干 | XPATH | `//input[contains(@placeholder,'题干')]` | A |
| 搜索-题型下拉 | XPATH | 搜索区 el-select [1] | B |
| 搜索-难度下拉 | XPATH | 搜索区 el-select [2] | B |
| 搜索按钮 | XPATH | `//button[.//span[contains(text(),'查询') or contains(text(),'搜索')]]` | A |
| 重置按钮 | XPATH | `//button[.//span[contains(text(),'重置')]]` | A |
| 新建试题 | XPATH | `//button[.//span[contains(text(),'新建试题') or contains(text(),'新建')]]` | A |
| 导入按钮 | XPATH | `//button[.//span[contains(text(),'导入')]]` | A |
| 批量删除 | XPATH | `//button[.//span[contains(text(),'批量删除')]]` | B |

## 异步等待策略
| 场景 | 条件 |
|------|------|
| 页面加载 | 表格行数 ≥ 0 |
| 题型切换 | 动态表单区域元素可见 |

## 自动化代码
- Page Object: `page/personnel_page/QuestionBankPage.py`
- 测试: `script/personnel/test_question_bank.py`
