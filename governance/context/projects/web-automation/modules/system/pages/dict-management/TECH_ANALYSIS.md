# TECH_ANALYSIS — system / dict-management

## 分析对象
- 模块：system
- 页面：字典管理
- 自动化目标：覆盖分类切换/字典CRUD/搜索的 Page Object (DictManagePage)

## 技术要点

### Element Plus 组件识别
| 组件类型 | 用途 | 特殊性 |
|----------|------|--------|
| el-tabs | 字典/字典分类标签切换 | 默认激活"字典" |
| el-radio-button (×3) | 分类筛选(全部/系统/自定义) | 左侧面板 |
| el-input | 分类搜索 + 字典标签搜索 | 两个独立搜索框 |
| el-select | 状态下拉 | 右侧表格搜索区 |
| el-table | 字典明细表格 | 标签/键值/状态/备注/操作 |
| el-dialog | 新增/编辑弹窗 | |
| el-pagination | 分页器 | |

### 定位器设计表
| 元素 | 策略 | 定位值 | 稳定性 |
|------|------|--------|--------|
| 分类筛选-全部 | XPATH | `//span[contains(@class,"el-radio-button__inner") and normalize-space(.)="全部"]/ancestor::label[1]` | A |
| 分类搜索框 | XPATH | `//input[contains(@placeholder,"搜索字典分类")]` | A |
| 字典标签搜索 | XPATH | `//input[contains(@placeholder,"字典") and contains(@placeholder,"标签")]` | A |
| 搜索按钮 | XPATH | `//button[.//*[normalize-space(.)="搜索"]]` | A |
| 新增按钮 | XPATH | `//button[.//*[normalize-space(.)="新增"]]` | A |
| 第1行编辑 | XPATH | `(//tr[contains(@class,"el-table__row")])[1]//button[.//span[contains(text(),"编辑")]]` | B |
| 第1行删除 | XPATH | `(//tr[contains(@class,"el-table__row")])[1]//button[.//span[contains(text(),"删除")]]` | B |

### 异步等待策略
| 场景 | 等待条件 |
|------|----------|
| 页面加载 | 左侧分类面板 + 右侧表格出现 |
| 切换分类 | 右侧表格loading → 数据刷新 |
| 弹窗操作 | 弹窗出现/消失 |
| 搜索完成 | loading消失 |

## 实现建议
- Page Object: DictManagePage 继承 BasePage
- 分类切换方法: click_category_filter() / search_category()
- CRUD闭环: 新增→搜索验证→编辑→搜索验证→删除→搜索确认无
- 清理策略: 闭环删除，teardown仅兜底

## 风险与限制
- 双面板布局: 左侧分类+右侧表格，需各自独立定位
- 分类切换: 右侧表格异步刷新，需等待loading完成
- 系统字典: 不可删除/编辑，需验证拦截行为
