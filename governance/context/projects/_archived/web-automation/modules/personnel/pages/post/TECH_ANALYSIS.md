# TECH_ANALYSIS — personnel / post

## 分析对象
- 模块：personnel | 页面：岗位管理 | 代码：PostManagePage.py (542行)

## 定位器设计表（从代码提取）
| 元素 | 策略 | 定位值 | 稳定性 |
|------|------|--------|--------|
| 搜索-名称/编码 | XPATH | `//input[@placeholder='请输入岗位编码或名称']` | A |
| 搜索-部门下拉 | XPATH | `//div[contains(@class,'search-bar')]//div[contains(@class,'el-select')][1]` | B |
| 搜索-分类下拉 | XPATH | `//div[contains(@class,'search-bar')]//div[contains(@class,'el-select')][2]` | B |
| 搜索-状态下拉 | XPATH | `//div[contains(@class,'search-bar')]//div[contains(@class,'el-select')][3]` | B |
| 搜索按钮 | XPATH | `//button[.//span[contains(text(),'查询') or contains(text(),'搜索')]]` | A |
| 重置按钮 | XPATH | `//button[.//span[contains(text(),'重置')]]` | A |
| 新增按钮 | XPATH | `//button[contains(@class,'el-button--primary') and contains(.,'新增')]` | A |
| 表格行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | A |

## 异步等待策略
| 场景 | 条件 |
|------|------|
| 页面加载 | 表格行数 ≥ 0 |
| 搜索完成 | loading 消失 |
| 弹窗打开 | el-dialog visible |

## 自动化代码
- Page Object: `page/personnel_page/PostManagePage.py`
- 测试: `script/personnel/test_post_management.py`
