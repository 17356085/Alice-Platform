# TECH_ANALYSIS — system / system-log

## 分析对象
- 模块：system
- 页面：系统日志（只读运维页面）
- 自动化目标：覆盖日志类型/级别筛选、搜索、清空弹窗的 Page Object (SystemLogPage)

## 技术要点

### Element Plus 组件识别
| 组件类型 | 用途 | 特殊性 |
|----------|------|--------|
| el-select (×2) | 日志类型+日志级别下拉 | 选项由后端返回枚举值 |
| el-input | 模块名称搜索 | placeholder="请输入模块名称" |
| el-date-picker (×2) | 开始/结束日期 | |
| el-table | 系统日志表格 | 类型/级别/模块/内容/时间 |
| el-tag | 日志级别标识 | ERROR红/WARN黄/INFO蓝/DEBUG灰 |
| el-button | 搜索/重置/清空 | |
| el-pagination | 分页器 | |

### 定位器设计表
| 元素 | 策略 | 定位值 | 稳定性 |
|------|------|--------|--------|
| 日志类型下拉 | XPATH | label含"日志类型"的el-select | B |
| 日志级别下拉 | XPATH | label含"日志级别"的el-select | B |
| 模块名称搜索 | XPATH | `//input[contains(@placeholder,"请输入模块名称")]` | A |
| 开始/结束日期 | XPATH | placeholder含"开始日期"/"结束日期" | A |
| 搜索按钮 | XPATH | 文字"搜索" | A |
| 清空按钮 | XPATH | 文字"清空" | A |
| 下拉选项面板 | XPATH | `(//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))])[last()]` | B |

### 异步等待策略
| 场景 | 等待条件 |
|------|----------|
| 页面加载 | 表格出现 |
| 下拉选择(类型/级别) | 下拉面板可见→点击选项→表格刷新 |
| 搜索完成 | loading消失 |
| 清空确认 | el-message-box可见 |

## 实现建议
- Page Object: SystemLogPage 继承 BasePage
- 下拉筛选: el-select点击展开→选择选项→表格异步刷新
- 日志级别颜色: ERROR红/WARN黄/INFO蓝 — 仅验证元素存在
- 只读页面，无需数据清理

## 风险与限制
- 下拉选项依赖接口: 如果枚举接口返回空，下拉框无选项
- 大量日志数据: 搜索可能较慢，增加超时容错
- 无详情弹窗: 表格直接展示，无需额外弹窗操作
