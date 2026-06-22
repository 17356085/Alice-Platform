# TECH_ANALYSIS — system / operation-log

## 分析对象
- 模块：system
- 页面：操作日志（只读审计页面）
- 自动化目标：覆盖多条件搜索/详情/清空弹窗/分页的 Page Object (OperationLogPage)

## 技术要点

### Element Plus 组件识别
| 组件类型 | 用途 | 特殊性 |
|----------|------|--------|
| el-input (×3) | 系统模块/操作类型/操作人员搜索 | placeholder稳定 |
| el-radio-group | 状态筛选(全部/成功/失败) | |
| el-date-picker (×2) | 开始/结束日期 | |
| el-table | 操作日志表格 | 模块/类型/操作人/IP/状态/时间/操作 |
| el-dialog | 详情弹窗 | 含请求参数/返回结果 |
| el-button | 搜索/重置/清空/导出 | |
| el-pagination | 分页器 | |

### 定位器设计表
| 元素 | 策略 | 定位值 | 稳定性 |
|------|------|--------|--------|
| 系统模块搜索 | XPATH | `//input[contains(@placeholder,"请输入系统模块")]` | A |
| 操作类型搜索 | XPATH | `//input[contains(@placeholder,"请输入操作类型")]` | A |
| 操作人员搜索 | XPATH | `//input[contains(@placeholder,"请输入操作人员")]` | A |
| 状态筛选-成功 | XPATH | radio含"成功" | A |
| 状态筛选-失败 | XPATH | radio含"失败" | A |
| 开始/结束日期 | XPATH | placeholder含"开始日期"/"结束日期" | A |
| 搜索按钮 | XPATH | 文字"搜索" | A |
| 清空按钮 | XPATH | 文字"清空" | A |

### 异步等待策略
| 场景 | 等待条件 |
|------|----------|
| 页面加载 | 表格出现 |
| 多条件搜索 | loading消失（多个条件组合） |
| 详情弹窗 | 弹窗可见 |
| 清空确认 | el-message-box可见 |

## 实现建议
- Page Object: OperationLogPage 继承 BasePage
- 多条件搜索：支持模块/类型/操作人/状态/时间五维组合
- 清空操作：仅验证弹窗交互，不实际确认
- 无数据清理需求（只读页面）

## 风险与限制
- 多条件组合：全条件组合时可能无数据，需容错空结果
- 详情弹窗：含JSON格式数据，DOM结构可能嵌套复杂
- 大量数据：操作日志数据量大，搜索可能较慢
