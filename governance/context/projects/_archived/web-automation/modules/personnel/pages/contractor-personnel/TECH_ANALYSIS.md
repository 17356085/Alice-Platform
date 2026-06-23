```markdown
# TECH_ANALYSIS — personnel / contractor-personnel

## 1. Element Plus 组件识别

| 组件 | 用途 | 所在区域 | 备注 |
|------|------|----------|------|
| `el-card` | 搜索区容器 | 搜索区 | 头部搜索区域整体包裹卡片 |
| `el-form` | 搜索表单容器 | 搜索区（推测） | 可能内嵌于 card，用于布局搜索项 |
| `el-input` | 姓名/身份证搜索框 | 搜索区 | placeholder 可能包含“姓名”或“身份证” |
| `el-select` | 所属单位下拉 | 搜索区 | 选项可能依赖前置数据（承包商单位） |
| `el-select` | 入场状态下拉 | 搜索区 | 静态选项：未进场/已进场/退场 |
| `el-button` | 搜索/重置/新增/编辑/停用/删除 | 搜索区/工具栏/表格操作列 | |
| `el-table` | 人员列表表格 | 表格区 | card+table 混合布局 |
| `el-table-column` | 各列（姓名、身份证等） | 表格区 | |
| `el-pagination` | 分页器 | 表格底部 | 默认每页20条 |
| `el-dialog` | 新增/编辑弹窗 | 弹窗 | 标题“新增人员”或“编辑人员” |
| `el-form` | 弹窗表单 | 弹窗 | 包含姓名、身份证、所属单位等字段 |
| `el-input` | 弹窗内的姓名/身份证/手机号等 | 弹窗 | |
| `el-select` | 所属单位下拉（弹窗内） | 弹窗 | |
| `el-message` | 操作成功/失败提示 | 全局 | 短暂出现后消失 |
| `el-message-box` | 确认弹窗（停用/删除） | 全局 | 标题“确认” |

## 2. DOM 结构分析

> ⚠️ 因未提供页面真实 HTML 源码，以下结构基于 PAGE_CONTEXT.md 描述及 Element Plus 通用布局推断。自动化前建议用浏览器 F12 实际验证。

```
<body>
  ⋮
  <div id="app">
    <div class="main-container">
      <!-- 侧边栏 -->
      <sidebar>
        <el-menu>
          <li class="el-menu-item">人员管理</li>
          <li class="el-menu-item">承包商管理</li>
          <li class="el-menu-item is-active">承包商人员</li>  <!-- 当前菜单项 -->
        </el-menu>
      </sidebar>
      <!-- 主内容区 -->
      <div class="content">
        <!-- 搜索区（el-card） -->
        <div class="el-card search-area">
          <div class="el-card__body">
            <div class="el-form">                 <!-- v-if 可能控制高级搜索展开 -->
              <div class="el-form-item">
                <label>姓名/身份证</label>
                <div class="el-input">
                  <input placeholder="请输入姓名/身份证" />
                </div>
              </div>
              <div class="el-form-item">
                <label>所属承包商</label>
                <div class="el-select">
                  <span class="el-select__placeholder">请选择</span>
                  <input type="hidden" />
                </div>
              </div>
              <div class="el-form-item">
                <label>入场状态</label>
                <div class="el-select">
                  <span class="el-select__placeholder">请选择</span>
                  <input type="hidden" />
                </div>
              </div>
              <div>
                <button class="el-button el-button--primary">搜索</button>
                <button class="el-button">重置</button>
              </div>
            </div>
          </div>
        </div>
        <!-- 工具栏 -->
        <div class="toolbar">
          <button class="el-button el-button--primary">新增</button>
        </div>
        <!-- 表格区 -->
        <div class="el-table">
          <div class="el-table__header-wrapper">
            <table><thead><tr>
              <th><div class="cell">姓名</div></th>
              <th><div class="cell">身份证号</div></th>
              <th><div class="cell">所属单位</div></th>
              <th><div class="cell">手机号</div></th>
              <th><div class="cell">入场状态</div></th>
              <th><div class="cell">操作</div></th>
            </tr></thead></table>
          </div>
          <div class="el-table__body-wrapper">
            <table><tbody>
              <tr class="el-table__row">...</tr>
            </tbody></table>
          </div>
        </div>
        <!-- 分页器 -->
        <div class="el-pagination">
          <span class="el-pagination__total">共 N 条</span>
          <button class="btn-prev">上一页</button>
          <ul class="el-pager">...</ul>
          <button class="btn-next">下一页</button>
          <span class="el-pagination__sizes">
            <div class="el-select__wrapper">20条/页</div>
          </span>
        </div>
      </div>
    </div>
  </div>
  <!-- Teleport 挂载点：下拉选项、弹窗、消息 -->
  <div id="el-popper-container-xxx">
    <div class="el-select-dropdown">...</div>
    <div class="el-dialog__wrapper">...</div>
  </div>
  <div class="el-message">...</div>
</body>
```

### 动态属性 / 可见性控制

| 特征 | 示例 | 影响 |
|------|------|------|
| **动态 class** | `el-table__row--striped`、`is-active`、`is-disabled` | 不能硬编码 class，应使用语义定位（数据行、按钮文本） |
| **v-if 控制元素** | 高级搜索区展开/收起、空数据提示 `<el-empty>`、加载中 `<el-loading>` | 元素可能不存在于 DOM，需等待条件 |
| **v-for 渲染的行** | `el-table__row` 数量随数据变化 | 不能依赖固定行数，应动态等待 |
| **Teleport 渲染** | `el-select` 选项面板挂载在 `<body>` 下 | 定位器需使用 `body .el-select-dropdown` 或 Relative XPath |
| **data- 属性** | Vue 可能自动生成 `data-v-xxx`，但一般不用于定位 | 不作为稳定选择器依赖 |

## 3. 定位器设计表（A/B/C 三级）

### 搜索区

| 元素 | 推荐定位策略 | 定位值 | 稳定性 | 备注 |
|------|-------------|--------|--------|------|
| 姓名/身份证搜索输入框 | **A级: CSS** | `.search-area .el-input__inner[placeholder*='姓名']` | A | 若 placeholder 固定包含“姓名” |
| 姓名/身份证搜索输入框 | B级: XPath (目前 PO 用) | `//input[contains(@placeholder,"姓名") or contains(@placeholder,"身份证")]` | B | 含有多个 or，可读性差，建议替换为更精确的 CSS |
| 所属单位下拉选择框 | **A级: CSS** | `.search-area .el-select:has(span:contains("所属"))`（注意 `:has` Selenium 4+ 支持）或 `(By.XPATH, '//div[@class="search-area"]//div[contains(@class,"el-select")][.//label[contains(text(),"所属")]] /..')` | B | 建议添加 `data-testid` 字段以获得 A 级定位 |
| 入场状态下拉选择框 | **A级: CSS** | `.search-area .el-select:has(span:contains("入场状态"))` | B | 同上 |
| 搜索按钮 | **A级: XPath** | `//button[.//span[text()='搜索']]` | A | 按钮文本固定，很少变化 |
| 重置按钮 | **A级: XPath** | `//button[.//span[text()='重置']]` | A | |

### 工具栏

| 元素 | 推荐定位策略 | 定位值 | 稳定性 | 备注 |
|------|-------------|--------|--------|------|
| 新增按钮 | **A级: XPath** | `//button[.//span[text()='新增']]` | A | |

### 表格

| 元素 | 推荐定位策略 | 定位值 | 稳定性 | 备注 |
|------|-------------|--------|--------|------|
| 表格容器 | **A级: CSS** | `.el-table` | A | |
| 表格行 | **A级: CSS** | `.el-table__body-wrapper .el-table__row` | B | 行数动态，需注意空数据时可能不存在 |
| 列头 | **A级: CSS** | `.el-table__header-wrapper .cell` | A | |
| 操作列按钮（编辑） | **A级: XPath** | `//tr[contains(@class,'el-table__row')]//button[.//span[text()='编辑']]` | A | 仅当只有一个行时；多行需配合行索引 |
| 操作列按钮（停用/启用） | B级: XPath | `//tr[contains(@class,'el-table__row')]//button[.//span[contains(text(),'停用') or contains(text(),'启用')]]` | B | 文本变体 |
| 操作列按钮（删除） | **A级: XPath** | `//tr[contains(@class,'el-table__row')]//button[.//span[text()='删除']]` | A | |

### 分页器

| 元素 | 推荐定位策略 | 定位值 | 稳定性 | 备注 |
|------|-------------|--------|--------|------|
| 分页器容器 | **A级: CSS** | `.el-pagination` | A | |
| 下一页按钮 | **A级: CSS** | `.el-pagination .btn-next` | A | |
| 上一页按钮 | **A级: CSS** | `.el-pagination .btn-prev` | A | |
| 每页条数选择器 | **A级: CSS** | `.el-pagination .el-select__wrapper` | B | 若分页器无 `size` 属性，可能不存在 |
| 总数文本 | **A级: CSS** | `.el-pagination__total` | A | |

### 弹窗（新增/编辑）

| 元素 | 推荐定位策略 | 定位值 | 稳定性 | 备注 |
|------|-------------|--------|--------|------|
| 弹窗容器 | **A级: CSS** | `.el-dialog` | A | 若存在 `.el-dialog__wrapper` 包裹 |
| 弹窗标题 | **A级: CSS** | `.el-dialog__header .el-dialog__title` | A | |
| 姓名输入框（弹窗内） | **A级: CSS** | `.el-dialog .el-form-item:has(label:contains("姓名")) .el-input__inner` | B | `:has` 兼容性需考虑 |
| 姓名输入框（弹窗内） | B级: XPath | `//div[contains(@class,'el-dialog')]//label[contains(text(),'姓名')]/following::input[1]` | B | |
| 所属单位下拉（弹窗内） | B级: XPath | `//div[contains(@class,'el-dialog')]//label[contains(text(),'所属单位')]/..//div[contains(@class,'el-select')]` | B | |
| 弹窗确定按钮 | **A级: XPath** | `//div[contains(@class,'el-dialog')]//button[.//span[text()='确定']]` | A | |
| 弹窗取消按钮 | **A级: XPath** | `//div[contains(@class,'el-dialog')]//button[.//span[text()='取消']]` | A | |

### 确认弹窗（停用/删除）

| 元素 | 推荐定位策略 | 定位值 | 稳定性 | 备注 |
|------|-------------|--------|--------|------|
| 确认弹窗 | **A级: CSS** | `.el-message-box` | A | 挂载在 body 下 |
| 确定按钮 | **A级: XPath** | `//div[contains(@class,'el-message-box')]//button[.//span[text()='确定']]` | A | |
| 取消按钮 | **A级: XPath** | `//div[contains(@class,'el-message-box')]//button[.//span[text()='取消']]` | A | |

### Toast 消息

| 元素 | 推荐定位策略 | 定位值 | 稳定性 | 备注 |
|------|-------------|--------|--------|------|
| 成功消息（存在时） | **A级: CSS** | `.el-message--success` | A | 短暂出现后自动消失 |
| 失败消息 | **A级: CSS** | `.el-message--error` | A | |

## 4. Vue 异步等待策略

> 基于 BasePage 已封装的方法设计，以下为每个场景的推荐等待条件。

| 场景 | 等待条件 | WebDriverWait 示例 | BasePage 对应方法 |
|------|---------|-------------------|-------------------|
| **页面加载** | 表格容器 `.el-table` 可见 | `wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".el-table")))` | `wait_page_ready()` |
| **搜索/表格刷新** | loading 覆盖层消失（`el-loading-mask`） | `wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-loading-mask")))` | `_wait_loading_gone()` |
| **Vue 更新完成** | DOM 稳定（200ms 无变化） | 自定义：记录旧 DOM，等待 `expected_conditions.staleness_of` 或轮询比较 | `wait_vue_stable()` |
| **弹窗打开** | 弹窗容器 `.el-dialog` 可见（或 `.el-dialog__wrapper` visible） | `wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".el-dialog")))` | —（可封装 `wait_dialog_visible`） |
| **弹窗关闭** | 弹窗容器不可见（invisibility） | `wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-dialog")))` | —（可封装 `wait_dialog_closed`） |
| **确认弹窗出现** | `.el-message-box` 可见 | `wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".el-message-box")))` | — |
| **Toast 出现** | `.el-message` 可见（可选，通常可忽略容并直接继续） | `wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".el-message")))` | — |
| **表格内容刷新** | 旧行 staleness，等待新行出现 | `wait.until(EC.staleness_of(old_row))` 或 `wait.until(EC.presence_of_all_elements_located(TABLE_ROWS))` | `get_table_row_count()` 可间接等待 |
| **下拉选项加载（弹窗内 select）** | `body .el-select-dropdown` 中的选项可见 | `wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body .el-select-dropdown__item")))` | —（建议封装 `wait_select_dropdown_loaded`） |

### 注意事项

- **el-loading-mask**：Element Plus 表格在异步加载时会出现全屏或局部 loading 层，必须在操作表格前确保 loading 消失。
- **el-dialog 动画**：弹窗打开/关闭有 0.3s 动画过渡，建议使用 visibility 而非 presence（presence 在动画开始时就满足）。
- **Toast 自动消失**：若需验证 toast 消息，应在出现后立即捕获文本，或等待其消失以继续操作。

## 5. 自动化风险点

| 风险类别 | 具体表现 | 应对策略 |
|----------|----------|----------|
| **动态 ID/Class** | Vue 生成的 `data-v-xxxxx` 属性、随机 ID | 避免使用这些属性定位，优先使用语义角色、文本内容、或稳定 data-testid |
| **v-if 控制元素缺失** | 空数据时表格行 `el-table__row` 不存在；高级搜索区默认隐藏 | 操作前使用 `WebDriverWait` 等待元素的 presence/visibility |
| **Teleport 渲染** | el-select 选项、el-date-picker 面板渲染在 `<body>` 下，不在组件内部 | 定位器使用 `body > .el-popper` 或 `body .el-select-dropdown`；避免依赖 `is_displayed()` 判断 Teleport 元素 |
| **异步数据加载延迟** | 表格数据在 Vue 异步请求完成后才渲染 | 必须等待 loading 消失（`el-loading-mask` invisible）后再操作表格或获取数据 |
| **分页器状态不稳定** | 总页数为 1 时上一页/下一页按钮 disabled | 先检查 `is_next_page_enabled()` 再点击，避免点击 disabled 按钮引发异常 |
| **弹窗嵌套混淆** | 新增弹窗（el-dialog）与确认弹窗（el-message-box）同时出现 | 确保当前弹窗关闭后再操作下一个弹窗；使用 `wait_dialog_closed()` |
| **权限控制导致的元素缺失** | 操作用户可能无“新增/编辑/删除”权限，对应按钮不存在 | 测试前确认测试账号权限，或设计灵活的定位器（仅在有权限时出现） |
| **动态表格列顺序** | 列顺序可能因配置变化（如表单字段动态显示/隐藏） | 使用列标题文本来定位列索引，而非硬编码第 N 列 |
| **左侧菜单嵌套** | 承包商人员菜单项依赖展开上级菜单才能点击 | 使用 `navigate_to("人员管理","承包商管理","承包商人员")` 确保完整展开路径 |
| **Vue 组件动画** | el-select 下拉展开动画、el-dialog 过渡 | 等待元素状态稳定（如 `wait.until(EC.element_to_be_clickable)`) |

## 附：定位器稳定性改进建议（针对当前 PO 代码）

| 当前定位器 | 稳定性 | 建议改为 | 新稳定性 |
|-----------|--------|----------|---------|
| `SEARCH_NAME_INPUT = (By.XPATH, '//input[contains(@placeholder,"姓名") or ...])` | B | `(By.CSS_SELECTOR, ".search-area .el-input__inner[placeholder*='姓名']")` | A（若 placeholder 固定） |
| `SEARCH_WORK_TYPE_SELECT` XPath 复杂 | C | 添加 `data-testid="search-unit"` 自定义属性 + CSS 定位 | A |
| `SEARCH_STATUS_SELECT` 同理 | C | 同上 | A |
| `TABLE_COLUMN_HEADERS` (XPath) | B | `(By.CSS_SELECTOR, ".el-table__header-wrapper .cell")` | A |
| `PAGE_SIZE_OPTION` (XPath with format) | B | 使用 `el-select-dropdown__item` 配合 `wait.until` 选择 | B |

> ⚠️ 任何使用 `contains(@class,"xxx")` 的方式（如 `//div[contains(@class,"el-form")]`）应替换为精确 `.el-form` 类或更可靠的祖先定位，以提高稳定性。
```