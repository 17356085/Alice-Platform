# TECH_ANALYSIS — personnel / entry-approval

## 分析对象
- 模块：personnel
- 页面：入场审批
- 自动化目标：覆盖列表/搜索/审批操作（通过/驳回/详情）的 Page Object（`EntryApprovalPage`）
- 路由：`#/personnel/contractor/approval`

## 技术要点

### Element Plus 组件识别
| 组件类型 | 用途 | 特殊性 |
|----------|------|--------|
| el-input | 申请人姓名搜索框 | 标准搜索区 |
| el-select | 承包商单位下拉、审批状态下拉 | 审批状态：待审批/已通过/已驳回 |
| el-table | 入场审批列表 | 8列：申请人/承包商/入场时间/入场说明/作业类型/状态/操作(通过+驳回+详情) |
| el-tag | 审批状态标签 | 待审批=橙色/已通过=绿色/已驳回=红色 |
| el-dialog | 审批意见弹窗、详情弹窗 | 驳回时弹出审批意见输入框 |
| el-textarea | 审批意见输入 | placeholder="审批意见" |
| el-pagination | 分页器 | 标准 |
| el-button | 通过/驳回/详情 行内按钮 | 文字区分操作类型 |

### 定位器设计表
| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 申请人搜索框 | XPATH | `//input[contains(@placeholder,"姓名") or contains(@placeholder,"申请人")]` | A | |
| 承包商单位下拉 | XPATH | `//div[contains(@class,"el-form") or contains(@class,"search-bar")]//div[contains(@class,"el-select")][.//span[contains(.,"承包商") or contains(.,"单位")]]` | B | |
| 审批状态下拉 | XPATH | `//div[contains(@class,"el-form") or contains(@class,"search-bar")]//div[contains(@class,"el-select")][.//span[contains(.,"审批状态") or contains(.,"状态")]]` | B | |
| 通过按钮(行内) | XPATH | `//tr[contains(@class,"el-table__row")][.//td[contains(.,"{name}")]]//button[contains(.,"通过")]` | B | 动态参数化 |
| 驳回按钮(行内) | XPATH | `//tr[contains(@class,"el-table__row")][.//td[contains(.,"{name}")]]//button[contains(.,"驳回")]` | B | |
| 详情按钮(行内) | BasePage | `self.click_row_button(name, "详情")` → 回退"查看" | B | 双文字容错 |
| 审批意见输入 | XPATH | `//textarea[contains(@placeholder,"审批意见") or contains(@placeholder,"备注")]` | A | |
| 弹窗确认 | BasePage | `self.click_dialog_save()` | A | |
| 表格列头 | XPATH | `//div[contains(@class,"el-table__header-wrapper")]//th//div[contains(@class,"cell")]` | A | |

### 异步等待策略
| 场景 | 等待条件 | 代码 |
|------|----------|------|
| 页面加载 | 表格出现 | `is_page_loaded()` 检查 `.el-table` |
| 审批操作完成 | toast + Vue稳定 | `get_toast_text(10)` + `wait_vue_stable()` |
| 详情弹窗 | 弹窗可见 | `wait_dialog_open(10)` |
| 筛选结果 | Vue稳定 | `wait_vue_stable()` |

## 实现建议
- Page Object：`EntryApprovalPage(BasePage)`，专注审批操作（通过/驳回/详情）
- **无CRUD操作**：不创建/编辑/删除数据，仅对已有记录执行审批
- 数据依赖：需线上存在"待审批"记录，无则跳过审批用例
- 清理策略：无（审批操作不可逆，不产生需清理的数据）

## 风险与限制
- **数据依赖**：审批通过/驳回依赖待审批记录存在，线上数据变化可能导致用例跳过
- **状态按钮显隐**：已审批记录不显示"通过/驳回"按钮，需确认按钮存在后再点击
- **审批意见**：驳回时可能必填，通过时可选 — 需处理两种弹窗逻辑
- **el-select 定位**：搜索区多个下拉框，使用语义文本区分
