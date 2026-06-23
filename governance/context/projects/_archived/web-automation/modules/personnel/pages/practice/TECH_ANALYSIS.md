# TECH_ANALYSIS — personnel / practice

## 分析对象
- 模块：personnel | 页面：自主练习 | 代码：待开发
- 页面类型：个人端记录列表（表格+筛选+行操作）

## 定位器设计表
| 元素 | 策略 | 定位值 | 稳定性 |
|------|------|--------|--------|
| 筛选状态下拉 | XPATH | `//div[contains(@class,"el-select")]` | B |
| 表格容器 | CSS | `.el-table` | A |
| 数据行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | A |
| 已完成-开始练习 | XPATH | `//tr[.//td[contains(.,"{name}")]]//button[contains(.,"开始练习")]` | A |
| 未完成-继续练习 | XPATH | `//tr[.//td[contains(.,"{name}")]]//button[contains(.,"继续练习")]` | A |
| 查看成绩 | XPATH | `//tr[.//td[contains(.,"{name}")]]//button[contains(.,"查看成绩")]` | A |
| 删除 | XPATH | `//tr[.//td[contains(.,"{name}")]]//button[contains(.,"删除")]` | A |
| 删除确认-确定 | XPATH | `//div[contains(@class,"el-message-box")]//button[.//span[normalize-space(.)="确定"]]` | A |
| 分页容器 | CSS | `.el-pagination` | A |
| 空状态 | CSS | `.el-empty` | B |

## 异步等待策略
| 场景 | 条件 |
|------|------|
| 页面加载 | 表格或空状态出现 |
| 筛选完成 | loading 消失 + 表格刷新 |
| 删除完成 | 确认弹窗消失 + toast |
| 查看成绩弹窗 | el-dialog visible |

## 自动化代码
- Page Object: `page/personnel_page/PracticePage.py`（待创建）
- 测试: `script/personnel/test_practice.py`（待创建）
- conftest: 已有，需添加 `test_practice` 路由 `#/personnel/training/practice`
