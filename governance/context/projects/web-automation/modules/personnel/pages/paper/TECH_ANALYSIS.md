# TECH_ANALYSIS — personnel / paper

## 分析对象
- 模块：personnel | 页面：试卷管理 | 代码：PaperManagePage.py (1531行)

## 定位器设计表（从代码提取）
| 元素 | 策略 | 定位值 | 稳定性 |
|------|------|--------|--------|
| 搜索-名称 | XPATH | `//input[contains(@placeholder,'试卷名称')]` | A |
| 搜索-分类下拉 | XPATH | 搜索区 el-select [1] | B |
| 搜索-组卷方式下拉 | XPATH | 搜索区 el-select [2] | B |
| 搜索-状态下拉 | XPATH | 搜索区 el-select [3] | B |
| 搜索按钮 | XPATH | `//button[.//span[contains(text(),'查询') or contains(text(),'搜索')]]` | A |
| 重置按钮 | XPATH | `//button[.//span[contains(text(),'重置')]]` | A |

## 异步等待策略
| 场景 | 条件 |
|------|------|
| 页面加载 | 表格行数 ≥ 0 |
| 手工选题 | 左栏(题库列表) + 右栏(已选题) 均可见 |
| 自动组卷 | 抽题规则表单可见 |

## 自动化代码
- Page Object: `page/personnel_page/PaperManagePage.py`
- 测试: `script/personnel/test_paper_management.py`
