好的，已收到您的请求。模块: `personnel`，页面: `exam-record`。

基于您提供的 **PAGE_CONTEXT.md** 中的页面分析框架，并结合 **Vue 3 + Element Plus** 项目基座上下文，我将输出该页面的技术分析文档。

---

# TECH_ANALYSIS.md — 考试记录页面

## 1. 技术栈概况
- **前端框架**: Vue 3 (Composition API)
- **UI 组件库**: Element Plus 2.x
- **测试框架**: Selenium 4.15.2 + pytest 7.4.4
- **已封装基座**: BasePage (wait_table_loaded, wait_dialog_visible, wait_loading_disappear) + ElementPlusHelper (select_option, get_table_data)

## 2. Element Plus 组件识别与 DOM 结构分析

### 2.1 组件清单
| 组件类型 | 用途 | 所在区域 | 页面元素ID (预测) |
| :--- | :--- | :--- | :--- |
| `el-input` | 搜索：人员姓名 | 搜索区 | `search_person_name` |
| `el-date-picker` | 搜索：考试日期范围 | 搜索区 | `search_exam_date` |
| `el-select` | 搜索：考试类型、状态 | 搜索区 | `search_exam_type`, `search_status` |
| `el-button` | 搜索、重置、导出、详情 | 搜索区/操作区 | `btn_search`, `btn_reset`, `btn_export`, `action_*` |
| `el-table` | 考试记录数据展示 | 主内容区 | `exam_record_table` |
| `el-table-column` | 表头（姓名、考试类型、成绩、结果、操作） | 表格区 | 动态生成 |
| `el-tag` | 考试结果（通过/未通过）状态标签 | 表格行中 | 动态渲染 |
| `el-pagination` | 数据分页 | 表格底部 | `pagination` |
| `el-dialog` | 查看详情、导出确认弹窗 | 覆盖层 | `dialog_detail`, `dialog_export` |

### 2.2 DOM 结构层级（预测）
```html
<div id="app">
  <div class="page-container">
    <!-- 面包屑/标题区域 -->
    <!-- 搜索/筛选区 -->
    <div class="search-area">
      <el-form>
        <!-- 姓名输入 -->
        <el-form-item>
          <el-input placeholder="请输入姓名" />
        </el-form-item>
        <!-- 日期范围 -->
        <el-form-item>
          <el-date-picker type="daterange" />
        </el-form-item>
        <!-- 考试类型下拉 -->
        <el-form-item>
          <el-select placeholder="考试类型" />
        </el-form-item>
        <!-- 状态下拉 -->
        <el-form-item>
          <el-select placeholder="状态" />
        </el-form-item>
        <!-- 搜索/重置按钮 -->
        <el-form-item>
          <el-button>搜索</el-button>
          <el-button>重置</el-button>
        </el-form-item>
      </el-form>
    </div>
    <!-- 操作按钮区域 -->
    <div class="button-group">
       <el-button>导出</el-button>
    </div>
    <!-- 数据表格区域 -->
    <div class="table-container">
      <el-table>
        <el-table-column label="姓名" prop="name" />
        <el-table-column label="考试类型" prop="examType" />
        <el-table-column label="成绩" prop="score" />
        <el-table-column label="结果" prop="result">
          <el-tag>通过</el-tag>
        </el-table-column>
        <el-table-column label="操作">
          <el-button>查看</el-button>
        </el-table-column>
      </el-table>
    </div>
    <!-- 分页区域 -->
    <div class="pagination-container">
      <el-pagination layout="total, sizes, prev, pager, next, jumper" />
    </div>
  </div>
</div>

<!-- 弹窗渲染在 body 层 -->
<div class="el-dialog__wrapper" id="dialog_detail">
  <el-dialog title="考试记录详情">
    <el-form>
      <!-- 详情字段 -->
    </el-form>
    <span slot="footer">
      <el-button>确定</el-button>
    </span>
  </el-dialog>
</div>
```

### 2.3 动态属性分析
- **表格列**: `el-table-column` 的 `prop` 和 `label` 属性是稳定的，可作为定位依据。
- **弹窗**: `el-dialog` 的标题 `title` 属性稳定。其 `wrapper` 层常动态生成，但 `title` 属性可作为定位。
- **下拉选项**: `el-select` 的下拉面板 (`el-select-dropdown`) 通常渲染在 `<body>` 层，不在其父组件内，需通过 `XPath` 或 `CSS` 结合 `aria-label` 或文本定位。
- **动态 Class**: Vue 生成的 `el-` 前缀 class 通常是稳定的，但自定义的 `is-` 或动态绑定 class 需要警惕。

## 3. 页面元素定位器设计表 (A/B/C 三级)

| 元素描述 | 元素Id | 定位策略 | 定位值 (示例) | 稳定性 | 备注 (Vue/EP特性) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **姓名输入框** | `search_person_name` | **A级 - CSS** | `input[placeholder='请输入姓名']` | **A** | `placeholder` 属性稳定 |
| **考试类型下拉** | `search_exam_type` | **A级 - XPath** | `//label[text()='考试类型']/following-sibling::div//input` | **A** | 通过 `label` 关联输入框 |
| **状态下拉** | `search_status` | **A级 - XPath** | `//label[text()='状态']/following-sibling::div//input` | **A** | 同上 |
| **日期范围** | `search_exam_date` | **B级 - CSS** | `input[placeholder='选择日期范围']` | **A** | `placeholder` 稳定 |
| **搜索按钮** | `btn_search` | **A级 - XPath** | `//button[.//span[text()='搜索']]` | **A** | 按钮文本稳定 |
| **重置按钮** | `btn_reset` | **A级 - XPath** | `//button[.//span[text()='重置']]` | **A** | 按钮文本稳定 |
| **导出按钮** | `btn_export` | **A级 - XPath** | `//button[.//span[text()='导出']]` | **A** | 按钮文本稳定 |
| **表格容器** | `exam_record_table` | **A级 - CSS** | `.el-table` | **A** | 页面通常只有一个主表 |
| **表头: 姓名** | `table_col_name` | **B级 - XPath** | `//div[@class='el-table__header-wrapper']//th[.//span[text()='姓名']]` | **B** | 通过表头文本定位列索引 |
| **表格行** | `row_*` | **B级 - CSS** | `.el-table__body-wrapper .el-table__row` | **B** | 动态行集合 |
| **查看按钮 (行内)** | `action_view` | **B级 - XPath** | `//div[contains(@class, 'el-table__body-wrapper')]//tr[1]//button[.//span[text()='查看']]` | **B** | 需要结合行号 |
| **分页器** | `pagination` | **A级 - CSS** | `.el-pagination` | **A** | class 稳定 |
| **详情弹窗** | `dialog_detail` | **A级 - XPath** | `//div[contains(@class,'el-dialog__wrapper')][.//span[text()='考试记录详情']]` | **A** | 通过弹窗标题文本定位 |
| **弹窗确定按钮** | `dialog_submit` | **A级 - XPath** | `//div[contains(@class,'el-dialog__wrapper')][.//span[text()='考试记录详情']]//button[.//span[text()='确定']]` | **A** | 限定在弹窗内部 |
| **考试结果标签** | `tag_result_*` | **B级 - XPath** | `//div[@class='el-table__body-wrapper']//tr[1]//span[contains(@class, 'el-tag')]` | **B** | 动态内容，通过文本值断言 |
| **下拉选项 (考试类型)** | `select_exam_type_option` | **C级 - XPath** | `//div[contains(@class, 'el-select-dropdown') and not(contains(@class, 'is-hidden'))]//span[text()='理论考试']` | **C** | 下拉面板在 `<body>` 层，需要先点击触发 |

## 4. 异步等待策略

| 场景 | 触发条件 | 等待对象 | 判断条件 | 基座方法 |
| :--- | :--- | :--- | :--- | :--- |
| **页面初始加载** | 导航到页面 | `exam_record_table` (CSS: `.el-table`) | `presence_of_element_located` | `wait_table_loaded()` |
| **搜索/重置刷新** | 点击“搜索”/“重置”按钮 | `//div[contains(@class, 'el-table__body-wrapper')]//tr` | `staleness_of` 旧行 / `presence_of_element_located` 新行 | `wait_table_loaded()` |
| **弹窗打开** | 点击行内“查看”按钮 | `dialog_detail` (XPath: `//div[contains(@class,'el-dialog__wrapper')]`) | `visibility_of_element_located` | `wait_dialog_visible("考试记录详情")` |
| **弹窗关闭** | 点击弹窗“确定”/“取消” | `dialog_detail` (XPath: `//div[contains(@class,'el-dialog__wrapper')]`) | `invisibility_of_element_located` | `wait_dialog_closed()` |
| **下拉菜单展开** | 点击 `el-select` 输入框 | `//div[contains(@class, 'el-select-dropdown')]` | `visibility_of_element_located` | `element_plus_helper.wait_dropdown_visible()` |
| **数据导出下载** | 点击“导出”按钮 | 浏览器下载状态 | 文件下载完成 (需特殊处理) | 无（需自定义或使用等待硬编码） |
| **Loading 状态** | 异步数据请求 | `//div[@class='el-loading-mask']` | `invisibility_of_element_located` | `wait_loading_disappear()` |

## 5. 自动化风险点

### 5.1 Element Plus 特有风险 (EP-Attention)
- **下拉选项渲染**: `el-select` 和 `el-date-picker` 的下拉面板 (`el-select-dropdown`, `el-picker-panel`) 默认渲染到 `<body>` 元素下，不在其父级 DOM 中。**不能**在其父容器内搜索下拉选项，必须使用全局 XPath。
- **弹窗嵌套**: `el-dialog` 的 `wrapper` 层 (`el-dialog__wrapper`) 也是渲染在 `<body>` 层。操作弹窗内元素时，建议先显式等待 `dialog` 可见，再在其 `wrapper` 上下文中查找元素，以避免冲突。
- **表格虚拟滚动**: EP 的 `el-table` 默认支持虚拟滚动，这意味着 DOM 中的行数可能远少于实际数据行数。定位表格行时，应依赖 `el-table__row` class，而不是根据 DOM 元素数量做断言。
- **动态 Class 与 ID**: Vue 生成的组件实例 ID 和部分动态 class (如 `is-checked`, `is-active`) 可能随状态变化，但 `el-` 前缀的 core class 是稳定的。

### 5.2 页面交互风险
- **日期选择器**: 日期范围需要先点击输入框，弹出面板后再点击日期。直接向输入框 `send_keys` 可能无效，建议使用 `click` + 面板日期 `click` 方式。
- **权限控制**: “导出”按钮 (`btn_export`) 和操作列的“编辑/删除”按钮可能因用户权限动态隐藏。应在测试前置条件中明确角色，或在定位时添加 `is_present` 检查。
- **非唯一组件**: 若页面存在多个 `el-table` 或 `el-dialog`，使用 `.el-table` 或 `//div[contains(@class,'el-dialog__wrapper')]` 定位器将匹配多个元素，应使用更具体的上下文 (如标题文本、关联的 `id` 或 `data-*` 属性)。

### 5.3 数据状态风险
- **空数据状态**: 表格无数据时，会显示“暂无数据”的空状态，此时 `el-table__row` 不存在。等待策略需要区分“表格已加载”和“表格有数据”。
- **分页状态**: 数据翻页后，原始表格行被替换，需重新获取行元素引用，避免使用过时的 `WebElement`。

## 6. ElementPlusHelper 策略扩展建议

基于以上分析，建议为 `exam-record` 页面扩展 `ElementPlusHelper` 或 `BasePage` 的专用方法：

1.  **`search_person_record(name, exam_type, date_range, status)`**: 封装搜索流程，填入筛选条件并点击搜索，最后等待表格刷新。
2.  **`get_exam_record_data_from_table()`**: 封装 `get_table_data()`，获取表格中当前页显示的所有考试记录。
3.  **`view_exam_record_detail(row_index)`**: 封装点击指定行的“查看”按钮，并等待详情弹窗可见的流程。
4.  **`click_dialog_submit()`**: 封装点击弹窗内的“确定”按钮，并等待弹窗关闭的方法。

---