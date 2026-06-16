# TECH_ANALYSIS — personnel / contractor-unit

## 分析对象
- 模块：personnel
- 页面：承包商单位
- 自动化目标：覆盖搜索/CRUD/分页的 Page Object（`ContractorUnitPage`）
- 路由：`#/personnel/contractor`

## 技术要点

### Element Plus 组件识别
| 组件类型 | 用途 | 特殊性 |
|----------|------|--------|
| el-input | 单位名称/编码搜索框 | placeholder 稳定 |
| el-select | 状态下拉筛选 | 标准 el-select 下拉 |
| el-table | 承包商单位列表 | 6列：名称/代码/安全负责人/联系人/电话/状态 + 操作列 |
| el-dialog | 新增/编辑弹窗 | 居中弹窗，含单位编码/名称/联系人/电话等字段 |
| el-pagination | 分页器 | 标准 .el-pagination 选择器 |
| el-button | 搜索/重置/新增/编辑/删除/启用/停用 | 通过按钮文字定位 |
| el-message-box | 删除确认弹窗 | Element Plus 标准消息框 |

### 定位器设计表
| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 单位名称搜索框 | XPATH | `//input[contains(@placeholder,"单位名称") or contains(@placeholder,"承包商名称")]` | A | 双重 placeholder 容错 |
| 单位编码搜索框 | XPATH | `//input[contains(@placeholder,"单位编码") or contains(@placeholder,"承包商编码")]` | A | |
| 状态下拉 | XPATH | `//div[contains(@class,"el-form") or contains(@class,"search-bar")]//div[contains(@class,"el-select")][.//span[contains(.,"状态") or contains(.,"启用")]]` | B | 需精确定位搜索区下拉 |
| 搜索按钮 | BasePage | `self.click_search_button()` | A | 继承 BasePage 通用方法 |
| 重置按钮 | BasePage | `self.click_reset_button()` | A | 继承 BasePage |
| 新增按钮 | XPATH | `//button[contains(.,"新增")]` | A | |
| 表格容器 | CSS | `.el-table` | A | Element Plus 固定 class |
| 表格列头 | XPATH | `//div[contains(@class,"el-table__header-wrapper")]//th//div[contains(@class,"cell")]` | A | |
| 表格行 | BasePage | `self.TABLE_ROWS` | A | 继承 BasePage |
| 分页总数 | BasePage | `self.TOTAL_COUNT` | A | 继承 `.el-pagination__total` |
| 分页器 | CSS | `.el-pagination .el-select__wrapper` | A | |
| 下一页 | CSS | `.el-pagination .btn-next` | A | |
| 弹窗-标题 | BasePage | `self.get_dialog_title()` | A | 继承 |
| 弹窗-输入框 | BasePage | `self.fill_dialog_input(label, value)` | A | 按 label 文本定位 |
| 弹窗-下拉 | BasePage | `self.select_dialog_dropdown(label, value)` | B | Element Plus 下拉渲染在 body |
| 弹窗-保存 | BasePage | `self.click_dialog_save()` | A | 继承 |
| 行内编辑按钮 | BasePage | `self.click_row_button(name, "编辑")` | B | 按行文本+按钮文字匹配 |
| 行内删除按钮 | BasePage | `self.click_row_button(name, "删除")` | B | |
| 消息框确认 | BasePage | `self.confirm_message_box()` | A | 继承 |

### 异步等待策略
| 场景 | 等待条件 | 代码 |
|------|----------|------|
| 页面加载 | 表格出现 + loading消失 | `self.wait_page_ready(15)` + `self._wait_loading_gone(10)` + `self.wait_vue_stable()` |
| 搜索完成 | Vue稳定 | `self.wait_vue_stable()` |
| 弹窗打开 | 弹窗可见 | `self.wait_dialog_open(15)` |
| 弹窗关闭 | 弹窗不可见 | `self.wait_dialog_close(5)` |
| Toast提示 | toast出现 | `self.wait_for_toast_text(10)` |
| JS hash导航 | 表格列数稳定 + 数据就绪 | `SidebarNavigator._navigate_by_js_hash()` 内置5阶段等待 |

## 实现建议
- Page Object：`ContractorUnitPage(BasePage)`，继承通用 CRUD 方法
- Fixture：module scope `driver_setup`，conftest 管理 JS hash 导航
- 清理策略：`conftest._teardown_contractor_unit()` 按名称前缀搜索删除，finally 块执行
- 数据策略：运行时 `datetime.now()` 生成唯一编码，闭环新增→编辑→删除

## 风险与限制
- **同路由双视图**：`#/personnel/contractor` 同时服务单位与人员视图，侧边栏 nest-menu 点击切换。JS hash 直接导航默认显示单位视图，人员视图需额外 sidebar click
- el-select 下拉渲染在 body 层，需使用 BasePage 的 `select_dialog_dropdown()` 方法
- 表格行索引动态变化，操作按钮使用行内文字匹配 + `click_row_button` 方法
- v-if 控制按钮显隐（权限受限时按钮不存在于 DOM）
