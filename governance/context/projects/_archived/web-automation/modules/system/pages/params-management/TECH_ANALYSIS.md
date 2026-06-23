# TECH_ANALYSIS — system / params-management

## 分析对象
- 模块：system
- 页面：参数设置
- 自动化目标：覆盖搜索(多维)/CRUD/刷新缓存的 Page Object (ParamsManagePage)

## 技术要点

### Element Plus 组件识别
| 组件类型 | 用途 | 特殊性 |
|----------|------|--------|
| el-input (×2) | 参数名称+参数键名搜索 | placeholder稳定 |
| el-select (×2) | 参数类型+业务模块下拉 | 选项异步加载 |
| el-table | 参数列表表格 | 名称/键名/值/类型/模块/备注/操作 |
| el-dialog | 新增/编辑弹窗 | |
| el-button (×5) | 搜索/重置/新增/导出/刷新缓存 | 文字区分 |
| el-pagination | 分页器 | |

### 定位器设计表
| 元素 | 策略 | 定位值 | 稳定性 |
|------|------|--------|--------|
| 参数名称搜索 | XPATH | `//input[@placeholder="请输入参数名称"]` | A |
| 参数键名搜索 | XPATH | `//input[@placeholder="请输入参数键名"]` | A |
| 参数类型下拉 | XPATH | label含"参数类型"的el-select | B |
| 业务模块下拉 | XPATH | label含"业务模块"的el-select | B |
| 搜索按钮 | XPATH | `//button[.//span[normalize-space(.)="搜索"]]` | A |
| 新增按钮 | XPATH | `//button[.//span[normalize-space(.)="新增"]]` | A |
| 刷新缓存按钮 | XPATH | `//button[.//span[normalize-space(.)="刷新缓存"]]` | A |
| 表格行 | CSS | `.el-table__body-wrapper tbody tr` | B |

### 异步等待策略
| 场景 | 等待条件 |
|------|----------|
| 页面加载 | 表格出现 |
| 搜索完成 | loading消失 |
| 弹窗打开/关闭 | 弹窗可见/不可见 |
| 刷新缓存 | toast出现 |

## 实现建议
- Page Object: ParamsManagePage 继承 BasePage
- 搜索策略: 支持名称/键名/类型/模块四维组合搜索
- 数据清理: teardown中按键名前缀删除

## 风险与限制
- 参数类型校验: 数值/字符串类型不同，需验证类型匹配
- 系统参数: 不可删除/编辑，需验证拦截
- 刷新缓存: 需admin权限，验证toast反馈
