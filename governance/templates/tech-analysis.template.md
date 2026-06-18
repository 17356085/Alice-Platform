# TECH_ANALYSIS Template

> 使用方式：基于页面 HTML 源码分析 Element Plus 组件、DOM 结构、定位器设计和异步等待策略。

## 分析对象
- 模块：<!-- e.g. "equipment" -->
- 页面：<!-- e.g. "设备报警配置" -->
- 自动化目标：<!-- e.g. "覆盖搜索/CRUD/分页的标准 Page Object" -->

## 技术要点

### Element Plus 组件识别
| 组件类型 | 用途 | 特殊性 |
|----------|------|--------|
| <!-- el-input --> | <!-- e.g. "报警名称搜索框" --> | <!-- placeholder 稳定 --> |
| <!-- el-select --> | <!-- e.g. "报警类型下拉" --> | <!-- 选项动态加载 --> |
| <!-- el-table --> | <!-- e.g. "报警规则列表" --> | <!-- 6列 + 操作列 --> |
| <!-- el-dialog --> | <!-- e.g. "新增/编辑弹窗" --> | <!-- 600px宽，居中 --> |
| <!-- el-pagination --> | <!-- e.g. "分页器" --> | <!-- 默认10条/页 --> |
| <!-- el-button --> | <!-- e.g. "搜索/重置/新增/编辑/删除/确认/取消" --> | <!-- 通过文字区分 --> |

### 定位器设计表
| 元素 | 推荐策略 | 定位值 | 稳定性 | 备注 |
|------|----------|--------|--------|------|
| <!-- e.g. 搜索输入框 --> | <!-- CSS --> | <!-- `input[placeholder*='报警名称']` --> | <!-- A --> | <!-- placeholder稳定 --> |
| <!-- e.g. 搜索按钮 --> | <!-- XPATH --> | <!-- `//button[.//span[text()='搜索']]` --> | <!-- A --> | <!-- 文字固定 --> |
| <!-- e.g. 表格容器 --> | <!-- CSS --> | <!-- `.el-table` --> | <!-- A --> | |
| <!-- e.g. 新增弹窗 --> | <!-- CSS --> | <!-- `.el-dialog__wrapper:not([style*='display: none']) .el-dialog` --> | <!-- B --> | <!-- 需排除隐藏弹窗 --> |
| <!-- e.g. 弹窗确认 --> | <!-- XPATH --> | <!-- `//div[contains(@class,'el-dialog') and not(contains(@style,'display: none'))]//button[.//span[text()='确定']]` --> | <!-- A --> | |

> A级 = 稳定属性 / B级 = CSS Selector / C级 = XPath/动态class保底

### 异步等待策略
| 场景 | 等待条件 | 代码示例 |
|------|----------|----------|
| <!-- 页面加载 --> | <!-- 表格出现 --> | <!-- `wait.until(EC.presence_of_element_located(TABLE))` --> |
| <!-- 搜索完成 --> | <!-- loading消失 --> | <!-- `wait.until(EC.invisibility_of_element_located(LOADING))` --> |
| <!-- 弹窗打开 --> | <!-- 弹窗可见 --> | <!-- `wait.until(EC.visibility_of_element_located(DIALOG))` --> |
| <!-- 弹窗关闭 --> | <!-- 弹窗不可见 --> | <!-- `wait.until(EC.invisibility_of_element_located(DIALOG))` --> |

## 实现建议
- Page Object 设计：<!-- e.g. "AlarmConfigPage(主页面) + AlarmConfigDialog(弹窗独立类)" -->
- Fixture 设计：<!-- e.g. "module scope driver + function scope page instance, navigate()在fixture中调用" -->
- 公共方法：<!-- e.g. "search/get_table_data/fill_form/confirm_dialog 共10个方法" -->
- 清理策略：<!-- e.g. "fixture teardown中按名称前缀删除测试数据" -->

## 风险与限制
- <!-- e.g. "el-select 下拉选项渲染在 body 层，需使用 ElementPlusHelper.select_option()" -->
- <!-- e.g. "表格行索引动态变化，编辑/删除按钮用行内文字匹配 + following-sibling" -->
- <!-- e.g. "v-if 控制操作按钮显隐，权限受限时元素不存在于 DOM 中" -->

---

## 示例填充（定位器设计表）

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 搜索输入框 | CSS | `input[placeholder*='报警名称']` | A | placeholder 简明稳定 |
| 搜索按钮 | XPATH | `//button[.//span[text()='搜索']]` | A | 按钮文字固定 |
| 重置按钮 | XPATH | `//button[.//span[text()='重置']]` | A | |
| 新增按钮 | XPATH | `//button[.//span[text()='新增']]` | A | |
| 表格容器 | CSS | `.el-table` | A | Element Plus 固定 class |
| 表格行 | CSS | `.el-table__body-wrapper .el-table__row` | B | 动态行索引 |
| 第1行编辑按钮 | XPATH | `(//tr[contains(@class,'el-table__row')])[1]//button[.//span[text()='编辑']]` | B | 行索引需参数化 |
| 弹窗 | CSS | `.el-dialog__wrapper:not([style*='display: none']) .el-dialog` | B | 排除隐藏弹窗 |
| 弹窗-名称输入 | CSS | `.el-dialog__wrapper:not([style*='display: none']) input[placeholder*='名称']` | B | |
| 弹窗-确定 | XPATH | `//div[contains(@class,'el-dialog') and not(contains(@style,'display: none'))]//button[.//span[text()='确定']]` | A | |
| 弹窗-取消 | XPATH | `//div[contains(@class,'el-dialog') and not(contains(@style,'display: none'))]//button[.//span[text()='取消']]` | B | 可能与其它弹窗冲突 |
| 删除确认弹窗 | CSS | `.el-message-box` | A | Element Plus 消息框 |
| 分页器 | CSS | `.el-pagination` | A | |






<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: template-meta -->
> last_verified: 2026-06-17 21:52 | sync_progress.py
<!-- ⚠️ AUTO-GENERATED SECTION END: template-meta -->