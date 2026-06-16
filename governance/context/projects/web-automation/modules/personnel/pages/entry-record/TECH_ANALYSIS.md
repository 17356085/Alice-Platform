# TECH_ANALYSIS — personnel / entry-record

## 分析对象
- 模块：personnel
- 页面：入场记录
- 自动化目标：覆盖列表/搜索/详情/导出的 Page Object（`EntryRecordPage`），**纯只读页面**
- 路由：`#/personnel/contractor/record`

## 技术要点

### Element Plus 组件识别
| 组件类型 | 用途 | 特殊性 |
|----------|------|--------|
| el-input | 人员姓名搜索框 | 标准搜索区 |
| el-select | 承包商单位下拉 | 标准 |
| el-date-picker | 入场日期范围选择 | 起止日期两个 date-picker |
| el-table | 入场记录列表 | 7~11列：记录编号/申请人/承包商/人员姓名/岗位/状态/操作(详情) |
| el-tag | 状态标签 | 动态颜色 |
| el-dialog | 详情弹窗 | 只读展示 |
| el-pagination | 分页器 | 标准 |
| el-button | 导出/详情按钮 | 导出在工具栏，详情在行内 |

### 定位器设计表
| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 姓名搜索框 | XPATH | `//input[contains(@placeholder,"姓名") or contains(@placeholder,"人员")]` | A | |
| 承包商单位下拉 | XPATH | `//div[contains(@class,"el-form") or contains(@class,"search-bar")]//div[contains(@class,"el-select")][.//span[contains(.,"承包商") or contains(.,"单位")]]` | B | |
| 开始日期 | XPATH | `//input[contains(@placeholder,"开始") or contains(@placeholder,"入场时间")][1]` | B | date-picker可能为readonly input |
| 结束日期 | XPATH | `//input[contains(@placeholder,"结束") or contains(@placeholder,"离场时间")]` | B | |
| 导出按钮 | XPATH | `//button[.//span[contains(.,"导出")]]` | A | 工具栏 |
| 详情按钮(行内) | BasePage | `self.click_row_button(name, "详情")` → 回退"查看" | B | |
| 表格列头 | XPATH | `//div[contains(@class,"el-table__header-wrapper")]//th//div[contains(@class,"cell")]` | A | |
| 分页总数 | BasePage | `self.TOTAL_COUNT` | A | 零数据时显示"共 0 条" |

### 异步等待策略
| 场景 | 等待条件 | 代码 |
|------|----------|------|
| 页面加载 | 表格出现 | `is_page_loaded()` 检查 `.el-table` |
| 日期选择 | Vue稳定 | 输入日期后 `wait_vue_stable()` |
| 详情弹窗 | 弹窗可见 | `wait_dialog_open(10)` |
| 导出 | 无需等待结果 | 验证无异常即可 |

## 实现建议
- Page Object：`EntryRecordPage(BasePage)`，纯查询+导出
- **零副作用**：所有操作只读，无数据创建/修改/删除
- 导出测试：仅验证按钮可点击，不验证下载文件内容
- 空数据容错：断言不强制要求 `total_text` 含数字
- 清理策略：无

## 风险与限制
- **零数据场景**：页面可能 0 条数据，分页显示"共 0 条"，断言需容错
- **date-picker**：Element Plus date-picker 为 readonly input + 弹出面板，直接 send_keys 可能无法触发
- **导出行为**：可能触发浏览器下载弹窗（Selenium无法验证），仅验证按钮可点击
- **详情弹窗**：与审批页面的详情弹窗可能不同（入场记录详情展示更多字段）
