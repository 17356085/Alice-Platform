# TECH_ANALYSIS — system / login-log

## 分析对象
- 模块：system
- 页面：登录日志（只读审计页面）
- 自动化目标：覆盖搜索/详情/清空弹窗/分页的 Page Object (LoginLogPage)

## 技术要点

### Element Plus 组件识别
| 组件类型 | 用途 | 特殊性 |
|----------|------|--------|
| el-input | 用户名搜索 | placeholder="请输入用户名" |
| el-radio-group | 状态筛选(全部/成功/失败) | |
| el-select | 登录状态下拉 | 备用筛选方式 |
| el-date-picker (×2) | 开始/结束日期 | |
| el-table | 登录日志表格 | 用户名/IP/地点/浏览器/OS/状态/时间/操作 |
| el-dialog | 详情弹窗 | 标题"登录日志详情" |
| el-button | 搜索/重置/清空/导出 | |
| el-pagination | 分页器 | |

### 定位器设计表
| 元素 | 策略 | 定位值 | 稳定性 |
|------|------|--------|--------|
| 用户名搜索 | XPATH | `//input[contains(@placeholder,"请输入用户名")]` | A |
| 状态-成功 | XPATH | radio含"成功" | A |
| 状态-失败 | XPATH | radio含"失败" | A |
| 开始日期 | XPATH | `//input[contains(@placeholder,"开始日期")]` | A |
| 结束日期 | XPATH | `//input[contains(@placeholder,"结束日期")]` | A |
| 搜索按钮 | XPATH | 文字"搜索" | A |
| 清空按钮 | XPATH | 文字"清空" | A |
| 详情弹窗标题 | XPATH | `//*[contains(@class,"el-dialog__title") and normalize-space(.)="登录日志详情"]` | A |
| 确认弹窗 | XPATH | `(//div[contains(@class,"el-message-box")])[last()]` | A |

### 异步等待策略
| 场景 | 等待条件 |
|------|----------|
| 页面加载 | 表格出现 |
| 搜索完成 | loading消失 |
| 详情弹窗 | 弹窗标题可见 |
| 清空确认 | el-message-box可见 |

## 实现建议
- Page Object: LoginLogPage 继承 BasePage
- 只读页面：无需数据清理
- 日期选择: el-date-picker，选择日期后需手动点搜索
- 清空操作：仅验证弹窗交互，不实际确认

## 风险与限制
- 清空操作：高风险，自动化仅验证弹窗存在+取消功能，不实际执行
- 时间筛选：date-range-picker面板定位需等待展开
- 详情弹窗：内容动态生成，含多字段
