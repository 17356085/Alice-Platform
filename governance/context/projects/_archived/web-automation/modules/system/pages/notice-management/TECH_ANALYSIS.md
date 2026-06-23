# TECH_ANALYSIS — system / notice-management

## 分析对象
- 模块：system
- 页面：通知管理
- 自动化目标：覆盖搜索/CRUD的 Page Object (NoticeManagePage)

## 技术要点

### Element Plus 组件识别
| 组件类型 | 用途 | 特殊性 |
|----------|------|--------|
| el-input | 通知标题搜索 | placeholder="请输入通知标题" |
| el-select | 通知类型下拉 | 通知/公告 |
| el-table | 通知列表表格 | 标题/类型/状态/创建时间/操作 |
| el-dialog | 新增/编辑弹窗 | 含富文本编辑器 |
| 富文本编辑器 | 通知内容编辑 | 第三方组件，DOM结构复杂 |
| el-button | 搜索/重置/新增/编辑/删除 | |

### 定位器设计表
| 元素 | 策略 | 定位值 | 稳定性 |
|------|------|--------|--------|
| 标题搜索框 | XPATH | `//input[contains(@placeholder,"请输入通知标题")]` | A |
| 类型下拉 | XPATH | el-select在标题输入框所在form中 | B |
| 新增按钮 | XPATH | `//div[contains(@class,"el-table__toolbar")]//button[.//span[contains(text(),"新增")]]` | A |
| 弹窗 | XPATH | `(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[@role="dialog"])[last()]` | B |
| 弹窗标题输入 | XPATH | `.//input[contains(@placeholder,"请输入通知标题")]` | A |
| 弹窗确定 | XPATH | dialog内footer含"确定"按钮 | B |
| 确认弹窗 | XPATH | el-message-box含确定/取消 | A |

### 异步等待策略
| 场景 | 等待条件 |
|------|----------|
| 页面加载 | 表格出现 |
| 弹窗打开 | el-overlay dialog可见 |
| 弹窗关闭 | el-overlay dialog消失 |
| 富文本加载 | 编辑器iframe可见 |

## 实现建议
- Page Object: NoticeManagePage 继承 BasePage
- 弹窗定位: 使用 `[last()]` 索引避免多个overlay冲突
- 富文本: 自动化测试用纯文本内容，避免操作iframe

## 风险与限制
- 富文本编辑器: 第三方组件DOM不稳定，自动化仅填纯文本
- 多overlay: 页面可能有多个隐藏overlay，需用`:not([style*="display: none"])`
- 弹窗表单: 确定/取消按钮在dialog footer内
