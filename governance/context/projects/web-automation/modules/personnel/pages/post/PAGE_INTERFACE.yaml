好的，作为您指定的Web端测试工程师，我将基于“人员管理”模块下的“岗位管理”页面这一常见场景，为您推演并分析其页面结构，生成标准化的文档。请注意，由于您未提供具体的截图或HTML源码，我将依据Element Plus组件库的通用模式、Vue 3项目的典型布局，以及“岗位管理”的业务逻辑进行合理推断。

---

### 分析结果：`personnel/post` 页面

**分析完成**。根据模块名称 `personnel` 和页面名称 `post`，推断为“人员管理”模块下的“岗位管理”配置页面。页面用于对公司内部岗位进行增、删、改、查操作。

---

### 产出物 1：PAGE_CONTEXT.md

#### `PAGE_CONTEXT.md` — 页面元素清单

**页面名称**：岗位管理
**所属模块**：personnel (人员管理)
**使用技术栈**：Vue 3 + Element Plus

#### 1. 页面整体结构

- **顶部**：面包屑导航 + 页面标题“岗位管理”。
- **主内容区**：
  - **左侧**：组织机构树（用于按部门筛选岗位）。
  - **右侧**：搜索/筛选区 + 数据表格 + 分页组件。

#### 2. 搜索/筛选区

位于右侧内容区的顶部。

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| search_input_postName | 岗位名称搜索输入框 | `el-input` | 搜索区 | 模糊搜索 |
| search_select_status | 状态筛选下拉框 | `el-select` | 搜索区 | 选项: 启用/禁用 |
| search_btn_query | 查询按钮 | `el-button` (primary) | 搜索区 | 触发搜索 |
| search_btn_reset | 重置按钮 | `el-button` (default) | 搜索区 | 重置所有筛选条件 |
| search_btn_add | 新增岗位按钮 | `el-button` (primary) | 搜索区 | **权限点**，可能受权限控制 |

#### 3. 表格/列表区

位于搜索区下方。

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| table_col_postName | 列：岗位名称 | `el-table-column` | 表格区 | 文本类型 |
| table_col_postCode | 列：岗位编码 | `el-table-column` | 表格区 | 文本类型 |
| table_col_deptName | 列：所属部门 | `el-table-column` | 表格区 | 文本类型 |
| table_col_sort | 列：排序 | `el-table-column` | 表格区 | 数字类型 |
| table_col_status | 列：状态 | `el-table-column` | 表格区 | 标签类型（`el-tag`），显示“启用”/“禁用” |
| table_col_createTime | 列：创建时间 | `el-table-column` | 表格区 | 日期类型 |
| table_col_actions_edit | 操作列：编辑 | `el-button` (text/small) | 表格区 | **权限点**，点击弹出编辑弹窗 |
| table_col_actions_delete | 操作列：删除 | `el-button` (text/small) | 表格区 | **权限点**，点击触发删除确认 |
| table_empty_data | 空数据提示 | `el-empty` | 表格区 | 当表格无数据时显示 “暂无数据” |

#### 4. 分页区

位于表格下方。

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| pagination_component | 分页组件 | `el-pagination` | 分页区 | 包含页码、每页条数、总条数 |
| pagination_pageSize | 每页条数选择框 | `el-pagination` | 分页区 | 选项: 10/20/50/100 |
| pagination_total | 总条数显示 | `el-pagination` | 分页区 | 显示为“共 XX 条” |

#### 5. 弹窗/对话框

- **新增/编辑岗位弹窗** (`el-dialog`)

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| dialog_post_form | 弹窗整体 | `el-dialog` | 弹窗区 | 标题为“新建岗位”或“编辑岗位” |
| dialog_form_postName | 岗位名称输入框 | `el-input` | 弹窗区 | 必填项 |
| dialog_form_postCode | 岗位编码输入框 | `el-input` | 弹窗区 | 必填项 |
| dialog_form_sort | 排序输入框 | `el-input-number` | 弹窗区 | 可选 |
| dialog_form_status | 状态开关 | `el-switch` | 弹窗区 | 默认为开启 |
| dialog_form_deptName | 所属部门选择器 | `el-tree-select` | 弹窗区 | 可能使用树形选择器 |
| dialog_btn_save | 确定/保存按钮 | `el-button` (primary) | 弹窗区 | 提交表单 |
| dialog_btn_cancel | 取消按钮 | `el-button` (default) | 弹窗区 | 关闭弹窗 |

- **删除确认弹窗** (`el-message-box`)

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| msgBox_delete | 删除确认消息框 | `el-message-box` | 弹窗区 | 提示“确认删除岗位 XXX 吗？” |
| msgBox_btn_confirm | 确认删除按钮 | `el-button` | 弹窗区 | 危险操作，点击后执行删除 |
| msgBox_btn_cancel | 取消按钮 | `el-button` | 弹窗区 | 关闭消息框 |

#### 6. 页面状态

| 状态 | 表现 | Wait 策略建议 |
| :--- | :--- | :--- |
| 加载中 | 表格区域或左侧树显示骨架屏(`el-skeleton`) 或 loading 遮罩 | `wait_for_element_invisibility_of_loading()` |
| 空数据 | 表格显示`el-empty`组件 “暂无数据”，分页组件隐藏 | 检查 `el-empty` 元素是否存在 |
| 搜索无结果 | 表格显示 `el-empty`，但分页组件显示总条数为0 | 检查总条数文本是否为 “共 0 条” |
| 操作成功 | 右上角弹出绿色提示“操作成功”(`el-message.success`) | `wait_for_toast_success("操作成功")` |
| 网络错误/超时 | 接口请求失败后，可能显示全局错误提示或`el-alert`组件 | 检查 `el-message.error` 或 `el-alert` |

#### 7. 权限点

- **搜索区**：`新增岗位` 按钮 (`search_btn_add`)
- **表格操作列**：`编辑` 按钮 (`table_col_actions_edit`)， `删除` 按钮 (`table_col_actions_delete`)

---

### 产出物 2：PAGE_ELEMENT_POSITION.md

#### `PAGE_ELEMENT_POSITION.md` — 元素定位器设计

**说明**：由于未提供HTML，以下定位器为基于Element Plus组件标准结构和常用开发习惯的**假设性设计**。请在实际页面中微调。

| 元素ID | 定位策略 (A/B/C) | 定位值 | 稳定性评级 | 备用方案 (C级) |
| :--- | :--- | :--- | :--- | :--- |
| `search_input_postName` | **A (CSS)** | `#search_postName` (假设有id) 或 `input[placeholder="岗位名称"]` (利用placeholder) | **高** | `xpath=//label[text()="岗位名称"]/following-sibling::div//input` |
| `search_select_status` | **B (CSS)** | `//div[contains(@class, 'el-select')]//input[@placeholder="岗位状态"]` (利用placeholder) | **中** | `xpath=//label[text()="状态"]/following-sibling::div//div[contains(@class, 'el-select')]` |
| `search_btn_query` | **A (CSS)** | `button:has-text("查询")` 或 `.query-btn` | **高** | `xpath=//button/span[text()="查询"]/parent::button` |
| `search_btn_add` | **A (CSS)** | `button:has-text("新增岗位")` 或 `#addPostBtn` | **高** | `xpath=//button/span[text()="新增岗位"]/parent::button` |
| `table_col_actions_edit` | **B (CSS)** | `//tr[1]//button/span[text()="编辑"]/parent::button` (第一行) | **中** | 使用 `xpath=//table//td[contains(@class, 'action-col')]//span[text()="编辑"]` |
| `dialog_post_form` | **B (CSS)** | `.el-dialog` | **中** | `xpath=//div[@role='dialog' and .//span[contains(text(), '岗位')]]` |
| `dialog_form_postName` | **A (CSS)** | `.el-dialog input[placeholder="请输入岗位名称"]` | **高** | `xpath=//div[@role='dialog']//label[text()="岗位名称"]/following-sibling::div//input` |
| `msgBox_btn_confirm` | **A (CSS)** | `.el-message-box .el-button--primary` | **高** | `xpath=//div[@role='alertdialog']//button/span[text()="确定"]/parent::button` |
| `pagination_component` | **B (CSS)** | `.el-pagination` | **高** | `xpath=//div[contains(@class, 'el-pagination')]` |

**等待策略说明**：
1.  **搜索/重置后**：等待表格数据刷新 (`wait_for_table_data_change`)，而非简单等待一段时间。
2.  **打开弹窗**：`WebDriverWait(driver, 10).until(EC.visibility_of_element_located(main_page.DIALOG))`
3.  **保存弹窗**：等待Toast出现 `WebDriverWait(driver, 10).until(EC.visibility_of_element_located(main_page.TOAST_SUCCESS))`
4.  **删除操作**：先等待消息框出现 (`msgBox_delete`)，点击确认后，等待提示成功的Toast。

---

### 下一步建议 & 自动化脚本编码指引

基于以上分析，你可以开始编写 PageObject 和测试用例了。请严格遵循 `MODULE_CONTEXT.md` 中的编码规范。

**`PostPage` 类示例骨架：**

```python
# page/post_page.py
from selenium.webdriver.common.by import By
from base.base_page import BasePage

class PostPage(BasePage):
    # ---------- Locators ----------
    # 搜索区
    SEARCH_INPUT_POST_NAME = (By.CSS_SELECTOR, "input[placeholder='岗位名称']")
    SEARCH_BTN_QUERY = (By.XPATH, "//button/span[text()='查询']/parent::button")
    SEARCH_BTN_ADD = (By.XPATH, "//button/span[text()='新增岗位']/parent::button")
    
    # 表格区
    TABLE_ROW = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr")
    TABLE_CELL = (By.CSS_SELECTOR, "td")
    
    # 弹窗-编辑
    DIALOG = (By.CSS_SELECTOR, ".el-dialog") # 复用BasePage的DIALOG
    
    # ---------- Actions ----------
    def navigate(self):
        """唯一导航入口"""
        self.sidebar.navigate("人员管理", "岗位管理") # 假设有sidebar模块
        return self
    
    def search(self, name="", status=""):
        """按条件搜索"""
        if name:
            self.clear_and_type(self.SEARCH_INPUT_POST_NAME, name)
        # ... 处理status
        self.click_element(self.SEARCH_BTN_QUERY)
        return self.wait_for_table_loaded()
    
    def click_add(self):
        """点击新增按钮，返回当前页面以支持链式调用"""
        self.click_element(self.SEARCH_BTN_ADD)
        return self.wait_for_dialog_visible()
    
    def fill_dialog_form(self, name, code, sort, status=True):
        """填充弹窗表单"""
        # ... 填充各个字段
        return self
    
    def submit_dialog(self):
        """提交弹窗"""
        self.click_element(self.DIALOG_SAVE) # 继承自BasePage
        return self.wait_for_toast_success()
```

**接下来你可以细化:**
1.  需要我将这些定位器转换为 `PostPage` 类的完整代码吗？（`generate-code`）
2.  需要我为 `post` 页面设计完整的CRUD测试用例吗？ （`testcase-design`）
3.  我可以检查生成的代码是否符合我们之前约定的规范。 （`code-consistency-checker`）