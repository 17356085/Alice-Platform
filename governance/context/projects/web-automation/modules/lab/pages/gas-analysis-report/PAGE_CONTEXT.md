# PAGE_CONTEXT — lab / gas-analysis-report

> 基于 GasAnalysisReportPage.py 逆向提取 | 2026-06-11
> 来源：Page Object 代码 (27 方法) + MODULE_CONTEXT.md

## 页面信息
- 模块：lab（化验室取样）
- 页面：气体分析报告单
- 路由：`#/lab/gas/report`
- UI 框架：Element Plus（标准）

## 页面元素清单

### 取样位置标签栏
| 元素 | 类型 | 定位策略 | 说明 |
|------|------|----------|------|
| 取样位置Tab | 自定义Tab组件 | XPATH 文本匹配 `//*[contains(normalize-space(.),"{text}")]` | 非标准el-tabs，蓝色下划线标识选中 |
| 激活Tab | CSS | `.el-tabs__item.is-active, [class*="tab"][class*="active"]` | 当前选中位置 |
| 位置列表 | 硬编码22个点位 | 界区原料气/除雾除尘/脱油脱萘/.../液氨/加样 | 已知清单 |

### 搜索区
| 元素 | 类型 | 定位 | 说明 |
|------|------|------|------|
| 开始日期 | el-date-picker | `input[placeholder*="开始日期"]` | 日期范围起始 |
| 结束日期 | el-date-picker | `input[placeholder*="结束日期"]` | 日期范围结束 |
| 查询按钮 | el-button (primary) | CSS/XPATH 双定位 | 触发筛选 |
| 重置按钮 | el-button (default) | CSS/XPATH 双定位 | 清空筛选条件 |
| 新增按钮 | el-button (primary) + icon | CSS/XPATH 双定位 | 打开新增弹窗 |
| 导出按钮 | el-button (default) + download icon | CSS/XPATH + JS降级 | 触发导出 |

### 表格区域
| 元素 | 类型 | 定位 | 说明 |
|------|------|------|------|
| 基本信息Tab | el-tabs__item | 文本匹配 "基本信息" | 表格所在Tab |
| 数据表格 | el-table (兼容标准table) | 双策略：el-table__body-wrapper + tbody | 气体分析数据 |
| 表头 | thead th | JS提取 + 6次重试 | 多行表头兼容（取最后一行） |
| 统计行 | tfoot/平均值行 | `tfoot tr, .el-table__footer-wrapper tr` | 各列平均值 |
| 空数据提示 | el-table__empty-text | 文本匹配 | 无数据时显示 |

### 表头列（19列）
日期 | 取样时间 | 取样位置 | 班组 | 检验员 | 复核员 | 备注 | 甲烷(%) | 乙烷(%) | 乙烯(%) | 乙炔(%) | 丙烷(%) | 丙烯(%) | H2(%) | CO2(%) | O2(%) | N2(%) | CO(%)

### 新增报告单弹窗
| 元素 | 类型 | 说明 |
|------|------|------|
| 弹窗标题 | el-dialog | "新增报告单" |
| 检验员* | el-input | 必填 |
| 复核员* | el-input | 必填 |
| 日期 | el-date-picker | 选填 |
| 取样时间 | el-time-picker | 选填 |
| 取样位置 | el-select | 默认"界区原料气" |
| 班组 | el-select | 选填 |
| 备注 | el-textarea | 选填 |
| 气体组分(13项) | el-input-number | 甲烷/乙烷/乙烯/.../焦油尘 |
| 保存按钮 | el-button--primary | 文字："保存报告" |
| 取消按钮 | el-button--default | 文字："取消" |

## 交互特征
- 页面加载后默认显示"界区原料气"取样位置数据
- 切换取样位置 → 表格异步刷新
- 日期筛选 → 查询按钮触发 → 表格刷新
- 新增弹窗：fill_dialog_input/select_dialog_dropdown 标准操作
- 导出：可能触发浏览器下载，无确认弹窗时直接返回True

## 完整度：85%（基于代码逆向，18类元素）
