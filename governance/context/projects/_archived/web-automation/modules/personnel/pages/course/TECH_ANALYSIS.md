# TECH_ANALYSIS — personnel / course

## 分析对象
- 模块：personnel | 页面：课程管理 | 代码：CourseManagePage.py (570行)

## 定位器设计表（从代码提取）
| 元素 | 策略 | 定位值 | 稳定性 |
|------|------|--------|--------|
| 新增课程 | XPATH | 含"新增"文字的 el-button | B |
| 搜索-名称 | XPATH | 课程名称输入框 | B |
| 搜索-分类下拉 | XPATH | `//div[contains(@class,'el-select')][1]` | B |
| 搜索-素材类型下拉 | XPATH | `//div[contains(@class,'el-select')][2]` | B |
| 搜索-发布状态下拉 | XPATH | `//div[contains(@class,'el-select')][3]` | B |
| 搜索按钮 | XPATH | `//button[.//span[text()='查询' or text()='搜索']]` | A |
| 重置按钮 | XPATH | `//button[.//span[text()='重置']]` | A |
| 课程卡片-查看 | XPATH | 课程卡片查看按钮 | B |

## 异步等待策略
| 场景 | 条件 |
|------|------|
| 页面加载 | 课程卡片/列表出现 |
| 搜索完成 | loading 消失 |

## 自动化代码
- Page Object: `page/personnel_page/CourseManagePage.py`
- 测试: `script/personnel/test_course_management.py`
