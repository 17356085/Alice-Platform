# TECH_ANALYSIS — personnel / study-record

## 分析对象
- 模块：personnel | 页面：学习记录 | 代码：待开发
- 页面类型：管理端记录列表（表格+3条件筛选，无行操作按钮）

## 定位器设计表
| 元素 | 策略 | 定位值 | 稳定性 |
|------|------|--------|--------|
| 学员名称输入 | CSS | `input[placeholder*="请输入学员名称"]` | A |
| 课程名称输入 | CSS | `input[placeholder*="请输入课程名称"]` | A |
| 是否完成下拉 | XPATH | `//label[contains(.,"是否完成")]/following::div[contains(@class,"el-select")][1]` | B |
| 查询按钮 | XPATH | `//button[.//span[normalize-space(.)="查询"]]` | A |
| 重置按钮 | XPATH | `//button[.//span[normalize-space(.)="重置"]]` | A |
| 表格容器 | CSS | `.el-table` | A |
| 数据行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | A |
| 分页容器 | CSS | `.el-pagination` | A |
| 空状态 | CSS | `.el-empty` | B |

## 异步等待策略
| 场景 | 条件 |
|------|------|
| 页面加载 | 表格或空状态出现 |
| 筛选完成 | loading 消失 + 表格刷新 |

## 自动化代码
- Page Object: `page/personnel_page/StudyRecordPage.py`（待创建）
- 测试: `script/personnel/test_study_record.py`（待创建）
- conftest: 已有，需添加 `test_study_record` 路由 `#/personnel/training/studyRecord`
