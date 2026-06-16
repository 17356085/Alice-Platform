# TECH_ANALYSIS — personnel / wrong-question

> ⚠️ 当前页面无数据，定位器为推断。数据就绪后需验证。

## 分析对象
- 模块：personnel | 页面：错题本（侧边栏"错题集"） | 代码：待开发
- 页面类型：个人端数据列表（8个筛选条件+表格+行操作+重新作答弹窗）

## 定位器设计表
| 元素 | 策略 | 定位值 | 稳定性 |
|------|------|--------|--------|
| 查询按钮 | XPATH | `//button[.//span[normalize-space(.)="查询"]]` | A |
| 重置按钮 | XPATH | `//button[.//span[normalize-space(.)="重置"]]` | A |
| 筛选下拉(多个) | XPATH | `//div[contains(@class,"search")]//div[contains(@class,"el-select")]` | B |
| 关键词搜索 | CSS | `input[placeholder*="搜索"]` | B |
| 表格容器 | CSS | `.el-table` | A |
| 数据行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | A |
| 重新作答 | XPATH | `//tr[.//td[contains(.,"{q}")]]//button[contains(.,"作答") or contains(.,"重做")]` | B |
| 查看解析 | XPATH | `//tr[.//td[contains(.,"{q}")]]//button[contains(.,"解析")]` | B |
| 作答弹窗-提交 | XPATH | `//div[contains(@class,"el-dialog")]//button[contains(.,"提交")]` | B |
| 分页容器 | CSS | `.el-pagination` | A |
| 空状态 | CSS | `.el-empty` | B |

## 异步等待策略
| 场景 | 条件 |
|------|------|
| 页面加载 | 表格或空状态出现 |
| 筛选完成 | loading 消失 |
| 重新作答弹窗 | el-dialog visible + 题目渲染完成 |
| 作答提交 | 判分结果出现 + 解析展示 |

## 自动化代码
- Page Object: `page/personnel_page/WrongQuestionPage.py`（待创建）
- 测试: `script/personnel/test_wrong_question.py`（待创建）
- conftest: 已有，需添加 `test_wrong_question` 路由 `#/personnel/training/wrongQuestion`
