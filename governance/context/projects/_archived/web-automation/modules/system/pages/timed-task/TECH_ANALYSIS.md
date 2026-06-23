# TECH_ANALYSIS — system / timed-task

## 分析对象
- 模块：system
- 页面：定时任务
- 自动化目标：覆盖状态筛选/搜索/CRUD的 Page Object (TimedTaskPage)

## 技术要点

### Element Plus 组件识别
| 组件类型 | 用途 | 特殊性 |
|----------|------|--------|
| el-input | 任务名称搜索 | placeholder="请输入任务名称" |
| el-select | 任务类型下拉 | 选项异步加载 |
| el-radio-group | 状态筛选(全部/运行中/已暂停) | 标签文字稳定 |
| el-table | 任务列表表格 | 名称/任务组/Cron/状态/操作 |
| el-dialog | 新增/编辑弹窗 | |
| el-drawer | Cron可视化生成器 | 第三方组件 |
| el-button | 搜索/重置/新增/修改/删除/日志/执行 | |

### 定位器设计表
| 元素 | 策略 | 定位值 | 稳定性 |
|------|------|--------|--------|
| 任务名称搜索 | CSS | `input[placeholder*="请输入任务名称"]` | A |
| 任务类型下拉 | XPATH | label含"任务类型"的el-select | B |
| 状态-全部 | XPATH | radio含"全部" | A |
| 状态-运行中 | XPATH | radio含"运行中" | A |
| 状态-已暂停 | XPATH | radio含"已暂停" | B |
| 搜索按钮 | XPATH | 文字"搜索" | A |
| 新增按钮 | XPATH | 文字"新增" | A |
| 弹窗 | XPATH | `(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]` | B |
| Cron抽屉 | XPATH | `//div[contains(@class,"cron-generator-drawer")]` | C |

### 异步等待策略
| 场景 | 等待条件 |
|------|----------|
| 页面加载 | 表格出现 |
| 状态切换 | 表格刷新 |
| 弹窗打开 | el-dialog可见 |
| Cron抽屉 | drawer可见 |

## 实现建议
- Page Object: TimedTaskPage 继承 BasePage
- 状态筛选: radio-button直接点击，表格异步刷新
- Cron生成器: 手工测试，自动化跳过
- 清理策略: teardown中按名称前缀删除

## 风险与限制
- Cron可视化生成器: 第三方组件，DOM不稳定，仅手工验证
- 任务执行: 需要后端调度环境，自动化仅验证按钮存在
- 状态切换: radio-button定位需注意文字变体(已暂停/已停停)
