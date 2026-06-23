好的，测试工程师。已收到你的代码注入。我将严格按照**模式 A：代码反推**，为你分析 `warehouse` 模块的 `spare-item` 页面。核心原则是：**所有内容必须源于代码，绝不编造**。

现在开始执行四步分析。

---

### 第一步：分析已注入的代码

从你提供的代码中，我已成功提取到以下核心信息：

1.  **Page Object 代码 (`SpareItemPage`)**: 这是一个标准的 CRUD 管理页面，具备搜索、新增、查看、删除功能，但不包含审批流。关键方法包括 `navigate()`、`search_by_item_name()`、`click_add()`、`click_view_first()`、`fill_item_name()` 等。
2.  **测试脚本 (`test_spare_item.py`)**: 测试覆盖了页面加载、搜索、CRUD完整链路（新增、查看、删除）、取消操作和必填校验。使用了 `spare_item_page` fixture。
3.  **模块上下文 (`MODULE_CONTEXT.md`)**: 显示这是一个`warehouse` 模块的 `spare-item` 页面。但请注意，此上下文为占位版，我将主要依赖你提供的真实Page Object和测试代码进行分析。

---

### 第二步：逐区域分析（基于真实代码）

#### 搜索/筛选区

| 元素 | 标签 | 类型 | 定位器 | 来源 |
| :--- | :--- | :--- | :--- | :--- |
| 物品名称输入框 | 请输入物品名称 | el-input | `By.XPATH, '//input[@placeholder="请输入物品名称"]'` | PO代码 (`FILTER_ITEM_NAME`) |
| 厂家名称输入框 | 请输入厂家名称 | el-input | `By.XPATH, '//input[@placeholder="请输入厂家名称"]'` | PO代码 (`FILTER_FACTORY`) |
| 查询按钮 | 查询 | el-button | `By.XPATH, '//button[contains(.,"查询")]'` | PO代码 (`BTN_QUERY`) |
| 重置按钮 | 重置 | el-button | `By.XPATH, '//button[contains(.,"重置")]'` | PO代码 (`BTN_RESET`) |

#### 表格/列表区

- 从PO代码和测试脚本中，可以推断出存在一个表格。
- **列标题**: PO代码中未直接定义列，但通过测试场景 `test_search_by_item_name` 和 `is_row_present` 方法，可以推断表格中至少有一列显示**物品名称**。
- **操作列**: 存在 `查看` 和 `删除` 按钮。`view` 和 `delete` 操作是逐行进行的（`click_view_first` 和 `click_row_button(name, "删除")`），表明每行都有操作按钮。
- **数据行**: `TABLE_ROWS` 定位器用于定位表格数据行。
- **分页**: 测试 `test_pagination_visible` 断言总条目数元素存在，表明有分页组件。`get_total_count()` 方法也间接证明了这一点。

| 序号 | 列标题（推断） | 数据类型 | 来源 |
| :--- | :--- | :--- | :--- |
| 1 | 物品名称 | 文本 | 测试脚本 (`is_row_present`, `search_by_item_name`) |
| ... | 其他列 | 待确认 | PO代码未体现 |
| N | 操作 (查看/删除) | 按钮 | PO代码 (`BTN_VIEW`, `delete_item_by_name`) |

#### 弹窗/对话框

| 弹窗 | 触发方式 | 表单字段（推断） | 来源 |
| :--- | :--- | :--- | :--- |
| 新增弹窗 | 点击 `新增` 按钮 | `物品名称`、`物品编码` | PO代码 (`fill_item_name`, `fill_item_code`) |
| 查看弹窗 | 点击 `查看` 按钮 | 表单字段 | PO代码 (`click_view_first`) |
| 删除确认框 | 点击 `删除` 按钮 | 无内置表单 | PO代码 (`delete_item_by_name` → `confirm_message_box`) |

#### 分页区

- **是否存在**: 是。测试 `test_pagination_visible` 和 `get_total_count()` 方法证明了其存在。

---

### 第三步 & 第四步：生成 PAGE_CONTEXT.md 和 PAGE_INTERFACE.yaml

基于上述分析，已为你生成以下文档。所有定位器和结论均来源于你提供的代码。

---

## 产出物 1: PAGE_CONTEXT.md

```markdown
# 备品物品管理 — 页面上下文

## 页面信息
- 路由: 从左侧导航 `库管管理` → `备品备件管理` → `物品管理`
- Page Object: SpareItemPage
- 测试脚本: test_spare_item.py

## 搜索/筛选区
| 序号 | 元素 | 标签 | 类型 | 定位器 | 来源 |
|-----|------|------|------|-------|------|
| 1 | 物品名称 | 请输入物品名称 | el-input | `By.XPATH, '//input[@placeholder="请输入物品名称"]'` | PO代码 |
| 2 | 厂家名称 | 请输入厂家名称 | el-input | `By.XPATH, '//input[@placeholder="请输入厂家名称"]'` | PO代码 |

## 操作按钮
| 序号 | 按钮 | 触发动作 | 定位器 | 来源 |
|-----|------|---------|-------|------|
| 1 | 查询 | 触发搜索 | `By.XPATH, '//button[contains(.,"查询")]'` | PO代码 |
| 2 | 重置 | 清空搜索条件 | `By.XPATH, '//button[contains(.,"重置")]'` | PO代码 |
| 3 | 新增 | 打开新增弹窗 | `By.XPATH, '//button[contains(.,"新增")]'` | PO代码 |

## 表格列定义（部分推断）
| 序号 | 列标题 | 数据类型 | 来源 |
|-----|-------|---------|------|
| 1 | 物品名称 | 文本 | 测试脚本推断（`is_row_present`） |
| 2 | 操作(查看) | el-button | PO代码 (`BTN_VIEW`) |
| 3 | 操作(删除) | el-button | PO代码 (`delete_item_by_name`) |
| 4 | 其他列 | 未知 | PO代码未体现 |

## 弹窗
| 弹窗 | 触发方式 | 表单字段 | 来源 |
|------|---------|---------|------|
| 新增弹窗 | 点击 `新增` 按钮 | 物品名称、物品编码 (通过placeholder "物品名称"、"物品编码" 填写) | PO代码 (`fill_item_name`, `fill_item_code`) |
| 查看弹窗 | 点击行内 `查看` 按钮 | （未定义） | PO代码 (`click_view_first`) |
| 删除确认框 | 点击行内 `删除` 按钮 | 无，调用 `confirm_message_box()` | PO代码 (`delete_item_by_name`) |

## 业务规则（从代码推断）
| 规则 | 推断依据 | 置信度 |
|------|---------|-------|
| 搜索可通过物品名称进行 | `search_by_item_name()` 方法 | 高 |
| 重置搜索会清空条件 | `reset_search()` 方法 | 高 |
| 新增操作会打开一个弹窗 | `click_add()` → `wait_dialog_open()` | 高 |
| 新增弹窗内必填项未填时，保存会失败，并有错误提示 | `test_add_empty_required` 中的 `get_form_error()` 断言 | 中 |
| 创建时至少需要填写物品名称和物品编码 | `fill_item_name`, `fill_item_code` 方法名称和 `test_add_item_success` 场景 | 中 |
| “查看”按钮按行显示 | `click_view_first()` 方法名暗示 | 中 |
| “删除”操作需要弹窗确认 | `delete_item_by_name` → `confirm_message_box()` | 高 |
| 列表是分页的 | `get_total_count()` 和 `test_pagination_visible` | 高 |
| 行上可能有一个“查看”和一个“删除”按钮 | `BTN_VIEW` 和 `delete_item_by_name` (内含 `click_row_button(name, "删除")`) | 中 |
| 物品名称在表中是唯一的（用于定位） | `is_row_present(name)` 和 `delete_item_by_name(name)` 使用名称进行行定位 | 中 |

## 测试场景映射
| 测试函数 | 场景描述 | 验证点 |
|---------|---------|-------|
| `test_page_loads` | 页面加载 | 表格行数 >= 0 |
| `test_pagination_visible` | 分页组件可见 | 总条数元素存在 |
| `test_add_button_visible` | 新增按钮可见 | 新增按钮存在 |
| `test_search_by_item_name` | 按名称搜索 | 无断言，确保不崩溃 |
| `test_reset_search` | 重置搜索 | 无断言，确保不崩溃 |
| `test_add_dialog_opens` | 点击新增 | 弹窗可见 |
| `test_add_dialog_has_form_fields` | 新增弹窗有表单 | 输入项数量 >= 1 |
| `test_view_first_record` | 点击查看 | 弹窗可见 |
| `test_add_item_success` | 新增物品成功 | 列表出现新物品，总数增加 |
| `test_delete_created_item` | 删除已建物品 | 列表消失，总数减少或不增加 |
| `test_add_item_cancel` | 取消新增 | 列表不出现取消时输入的名称 |
| `test_add_empty_required` | 必填校验 | 错误提示非空 |
```

---

## 产出物 2: PAGE_INTERFACE.yaml

```yaml
page: spare-item
route: 库管管理 > 备品备件管理 > 物品管理
elements:
  search:
    - name: 物品名称
      label: 物品名称
      type: el-input
      locator: "By.XPATH, '//input[@placeholder="请输入物品名称"]'"
    - name: 厂家名称
      label: 厂家名称
      type: el-input
      locator: "By.XPATH, '//input[@placeholder="请输入厂家名称"]'"
  buttons:
    - name: 查询
      locator: "By.XPATH, '//button[contains(.,"查询")]'"
    - name: 重置
      locator: "By.XPATH, '//button[contains(.,"重置")]'"
    - name: 新增
      locator: "By.XPATH, '//button[contains(.,"新增")]'"
  table:
    - column: 物品名称
      type: text
    - column: 操作
      type: action_buttons
      actions:
        - view
        - delete
  dialogs:
    - name: 新增弹窗
      fields:
        - name: 物品名称
          type: el-input
          placeholder: 物品名称
        - name: 物品编码
          type: el-input
          placeholder: 物品编码
    - name: 删除确认框
      type: message_box
```