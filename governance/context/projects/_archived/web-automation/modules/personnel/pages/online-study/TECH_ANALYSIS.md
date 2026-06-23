```markdown
# 技术分析：在线学习管理页面 (OnlineStudyPage)

## 1. Element Plus 组件识别

| 组件类型 | 用途 | 定位器来源 |
|:---------|:-----|:-----------|
| `el-input` | 课程名称搜索框、弹窗课程名称输入框、授课老师输入框 | `SEARCH_COURSE_NAME_INPUT`, `FORM_COURSE_NAME_INPUT`, `FORM_TEACHER_INPUT` |
| `el-select` | 课程分类下拉、课程状态下拉、每页条数选择 | `SEARCH_CATEGORY_SELECT`, `SEARCH_STATUS_SELECT`, `PAGE_SIZE_SELECT`, `FORM_CATEGORY_SELECT` |
| `el-date-picker` | 创建日期范围选择 | `SEARCH_DATE_RANGE` |
| `el-button` | 查询、重置、新建课程、编辑、删除、查看进度、弹窗确定/取消 | `SEARCH_BTN`, `RESET_BTN`, `NEW_COURSE_BTN`, `BTN_EDIT_BY_ROW` 等 |
| `el-table` | 课程列表展示 | `TABLE`, `TABLE_ROWS` |
| `el-pagination` | 分页 | `PAGINATION`, `PAGINATION_NEXT_BTN` |
| `el-dialog` | 新建/编辑课程弹窗 | `DIALOG_COURSE`, `DIALOG_TITLE` |
| `el-switch` | 上架/下架状态开关 | `FORM_STATUS_SWITCH` |
| `el-upload` | 封面图片上传 | `FORM_COVER_UPLOAD` |
| `el-tag` | 表格中课程分类、状态标签（预期） | 未显式定位，通过表格数据读取时处理 |
| `el-loading` | 表格加载遮罩 | `TABLE_LOADING` |
| `el-link` | 课程名称链接 | `COL_COURSE_NAME_LINK` |
| `el-select-dropdown` | 下拉选项弹出层（渲染在 body） | `SEARCH_CATEGORY_DROPDOWN`（通用class） |

## 2. DOM 结构分析

### 关键层级结构

```
<div id="app">
  <!-- 导航侧栏 -->
  <aside class="sidebar">...</aside>
  <!-- 主内容区域 -->
  <main class="main-content">
    <!-- 面包屑 + 页面标题 -->
    <div class="page-header">
      <span class="breadcrumb">...</span>
      <h2>在线学习管理</h2>
      <button id="btn-newCourse">新建课程</button>
    </div>
    <!-- 搜索/筛选区 -->
    <div class="search-area">
      <div id="search-courseName" class="el-input">...</div>
      <div id="search-category" class="el-select">...</div>
      <div id="search-status" class="el-select">...</div>
      <div id="search-dateRange" class="el-date-editor el-date-editor--daterange">...</div>
      <button id="btn-search">查询</button>
      <button id="btn-reset">重置</button>
    </div>
    <!-- 表格区 -->
    <div class="table-container">
      <div class="el-table">
        <div class="el-table__header-wrapper">...</div>
        <div class="el-table__body-wrapper">
          <div class="el-loading-mask" v-if="loading">...</div>
          <table><tbody><tr class="el-table__row">...</tr></tbody></table>
        </div>
      </div>
      <div class="el-pagination">...</div>
    </div>
    <!-- 弹窗 -->
    <div id="dialog-course" class="el-dialog__wrapper" v-if="dialogVisible">
      <div class="el-dialog">
        <div class="el-dialog__header"><span>新建课程</span></div>
        <div class="el-dialog__body">
          <el-form>
            <el-form-item id="form-courseName">...</el-form-item>
            <!-- 其他表单项 -->
          </el-form>
        </div>
        <div class="el-dialog__footer">
          <button>取消</button>
          <button>确定</button>
        </div>
      </div>
    </div>
  </main>
</div>
```

### 稳定属性分析

| 属性类型 | 示例 | 稳定性 |
|:---------|:-----|:-------|
| `id` | `btn-search`, `dialog-course`, `form-courseName` | **A级** — 唯一且稳定 |
| `name` | 未使用（Vue+EP 通常不生成 name） | — |
| `data-*` | 未在代码中体现，但可通过 `data-testid` 扩展（当前未用） | 若存在则为A级 |
| 纯 CSS class | `.el-table`, `.el-dialog__title`, `.el-switch` | **B级** — 可能随版本变化 |
| EP 组件内部 class | `.el-select__wrapper`, `.el-date-editor--daterange` | **B级** — 组件内部稳定，但可能升级调整 |
| Vue 动态 class | `el-table__row` 是静态，但 `el-loading-mask` 由 v-if 控制 | 需配合等待策略 |

### 动态/不稳定因素

- `v-if="dialogVisible"` 控制弹窗 DOM 存在/消失，必须先确保可见再操作。
- `el-select` 的下拉选项 (`el-select-dropdown`) 渲染在 `document.body` 下，不是选择器的父级内部。
- `el-table` 的行数动态变化，行元素 class 固定 `el-table__row`，但每行内容不同，需通过行文本或索引定位。
- `el-upload` 的内部 `input[type=file]` 可能隐藏，需特殊处理。

## 3. 定位器设计表（A/B/C 三级）

| 元素 | 推荐定位策略 | 定位值 | 稳定性 | 备注 |
|:-----|:------------|:-------|:-------|:-----|
| **课程名称搜索输入框** | CSS (基于 id) | `#search-courseName .el-input__inner` | **A** | id 唯一 |
| **课程分类下拉** | CSS (基于 id) | `#search-category .el-select__wrapper` | **A** | 点击触发下拉 |
| **课程状态下拉** | CSS (基于 id) | `#search-status .el-select__wrapper` | **A** | id 唯一 |
| **日期范围选择** | CSS (基于 id) | `#search-dateRange .el-date-editor--daterange` | **A** | id 唯一 |
| **查询按钮** | CSS (基于 id) | `button#btn-search` | **A** | id 唯一 |
| **重置按钮** | CSS (基于 id) | `button#btn-reset` | **A** | id 唯一 |
| **新建课程按钮** | CSS (基于 id) | `button#btn-newCourse` | **A** | id 唯一 |
| **表格** | CSS | `.el-table` | **B** | 通用 class，无 id |
| **表格加载遮罩** | CSS | `.el-table__body-wrapper .el-loading-mask` | **B** | 可能因 EP 版本改动 |
| **表格行** | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | **B** | 动态行，数量可变 |
| **课程名称链接** | CSS | `.cell a.el-link` (或更具体 `.el-table__row .cell a.el-link`) | **B** | 可能随列配置变化 |
| **操作列编辑按钮（某行内）** | XPath (相对行) | `.//button[.//span[text()='编辑']]` | **B** | 需先定位对应行 |
| **操作列删除按钮（某行内）** | XPath (相对行) | `.//button[.//span[text()='删除']]` | **B** | 同上 |
| **操作列查看进度按钮** | XPath (相对行) | `.//button[.//span[text()='查看进度']]` | **B** | 同上 |
| **分页** | CSS | `.el-pagination` | **B** | 通用 class |
| **每页条数选择** | CSS | `.el-pagination .el-select__wrapper` | **B** | |
| **下一页按钮** | CSS | `.el-pagination .btn-next` | **B** | |
| **弹窗（新建/编辑）** | CSS (基于 id) | `div#dialog-course` | **A** | id 唯一 |
| **弹窗标题** | CSS | `div#dialog-course .el-dialog__title` | **B** | 依赖弹窗可见 |
| **弹窗课程名称输入** | CSS | `#dialog-course #form-courseName .el-input__inner` | **A** | 嵌套 id |
| **弹窗课程分类下拉** | CSS | `#dialog-course #form-category .el-select__wrapper` | **A** | |
| **弹窗授课老师输入** | CSS | `#dialog-course #form-teacher .el-input__inner` | **A** | |
| **弹窗课程描述** | CSS | `#dialog-course #form-description .el-textarea__inner` | **A** | |
| **弹窗封面上传拖拽区** | CSS | `#dialog-course #form-cover .el-upload-dragger` | **B** | 文件上传需特殊处理 |
| **弹窗上架开关** | CSS | `#dialog-course #form-status .el-switch` | **A** | id 稳定 |
| **弹窗确定按钮** | XPath (基于弹窗id) | `//div[@id='dialog-course']//button[.//span[text()='确定']]` | **A** | id + 文本 |
| **弹窗取消按钮** | XPath (基于弹窗id) | `//div[@id='dialog-course']//button[.//span[text()='取消']]` | **A** | |

### 补充 C 级定位策略（备用）

当 A/B 级失败时：

- 表格行：`(By.XPATH, "//tr[contains(@class,'el-table__row')]")` — C 级，脆弱
- 弹窗内任意输入框：`(By.XPATH, "//div[@id='dialog-course']//input[@type='text'][1]")` — C 级，依赖顺序
- 下拉选项（body 下）：`(By.XPATH, "//body//div[contains(@class,'el-select-dropdown') and contains(@style,'display: none') = false]//li[.//span[text()='具体选项文本']]")` — C 级，通常不需要，但可用于备选

## 4. Vue 异步等待策略

| 场景 | 等待条件 | WebDriverWait 示例（利用 BasePage 封装） |
|:-----|:---------|:----------------------------------------|
| **页面导航完成** | 表格元素存在 | `self.wait_element_visible(self.TABLE)` |
| **表格数据加载中** | loading 遮罩消失 | `self.wait_loading_disappear(self.TABLE_LOADING)` |
| **搜索/刷新后** | loading 消失 + 表格行非空（可选） | `self.wait_loading_disappear(self.TABLE_LOADING)`；可追加 `self.wait.until(lambda d: len(d.find_elements(*self.TABLE_ROWS)) > 0)` |
| **弹窗打开** | 弹窗可见 | `self.wait_element_visible(self.DIALOG_COURSE)` |
| **弹窗关闭** | 弹窗不可见 | `self.wait_element_invisible(self.DIALOG_COURSE)` |
| **下拉选项弹出** | 下拉选项容器可见 | `self.wait_element_visible(self.SEARCH_CATEGORY_DROPDOWN)` |
| **文件上传完成** | 上传组件内出现缩略图或进度条消失 | 自定义回调，一般等待 `el-upload-list` 中的文件项出现 |
| **分页切换** | 表格重新加载（loading 出现 then 消失） | `self.wait_loading_disappear(self.TABLE_LOADING)` |

> BasePage 已经封装了 `wait_vue_stable()`（等待 Vue 异步渲染完成）、`wait_loading_disappear(locator)`、`wait_element_visible(locator)`、`wait_element_invisible(locator)`。可直接复用。

## 5. 自动化风险点

| 风险点 | 说明 | 应对措施 |
|:-------|:-----|:---------|
| **动态 ID** | 未发现动态 ID（所有 id 均为固定字符串） | 当前无风险 |
| **Vue 动态 class** | 例如 `el-select-dropdown__list` 可能随版本变动 | 使用 A 级定位（id）规避；若使用 B 级，监控 EP 升级 |
| **v-if 控制元素** | 弹窗、loading 遮罩、空状态组件均由 v-if 控制 | 操作前必须等待可见/不可见；添加显式等待 |
| **if rame 嵌套** | 当前页面未见 iframe | 后续若集成第三方课件预览可能引入，需额外处理 |
| **虚拟列表/懒加载** | 课程列表可能使用 `el-table-v2`（虚拟滚动）？当前推测为普通 `el-table` | 如果改用虚拟列表，滚动加载会改变行定位方式，需更新定位器 |
| **权限控制导致元素缺失** | 新建/编辑/删除按钮可能根据角色隐藏 | 测试前应确认测试账号权限； fixture 中处理断言缺失 |
| **Element Plus 下拉选项渲染在 body 层** | `el-select` 的下拉菜单附加到 `document.body`，不在父组件内 | 点击触发后，使用 `SEARCH_CATEGORY_DROPDOWN` 定位（通用 class），避免使用父级作为上下文 |
| **日期范围选择** | 需要两次点击输入框来打开/关闭面板，且输入格式需匹配组件期望 | 使用 `send_keys` 填入带 `~` 的格式；或拆分选取具体日期 |
| **文件上传** | `input[type=file]` 被隐藏，不能直接点击 | 使用 Selenium 的 `send_keys(locator, file_path)` 直接设置文件路径，或者通过 JS 触发 |
| **表格操作列按钮** | 同一行有多个按钮，需区分“编辑”“删除”“查看进度” | 使用 XPath 文本选择，或先定位到行再 `.find_element` |

---

**总结**：页面定位器以 `id` 为主，A 级稳定性高。建议优先使用基于 id 的 CSS 选择器；对于动态部分（表格行、操作按钮）采用组合定位（行索引 + 相对 XPath）。等待策略聚焦 `el-loading` 的消失和弹窗的切换。需特别关注 `el-select` 下拉渲染在 body 层以及文件上传的特殊处理。
```