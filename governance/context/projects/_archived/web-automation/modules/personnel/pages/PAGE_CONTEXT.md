好的，收到。根据您的指令「模块: personnel」，我将进入 **模式 A：代码反推**，为 `personnel` 模块下的页面生成页面上下文文档。

为确保准确性，我需要确认您希望分析的具体页面。

从 `MODULE_CONTEXT.md` 可知，`personnel` 模块包含两个页面：
1.  **人员管理** (`PersonnelPage`) — 路径: `/personnel/personnel`
2.  **用户管理** (`UserPage`) — 路径: `/personnel/user`

**请确认您要分析的是哪个页面？**

在您回复之前，我将默认以 **人员管理 (`PersonnelPage`)** 为例执行分析流程，并向您展示分析草案。若需分析 `UserPage`，请告知。

---

### 分析草案：人员管理 (PersonnelPage)

根据已注入的 `MODULE_CONTEXT.md` 和预期的 `PersonnelPage.py` 及 `test_personnel_page.py` 代码结构，我正在进行以下分析：

**第一步：分析代码（基于预期代码结构）**

- **Page Object 代码 (`PersonnelPage.py`)**:
  - **URL**: `/personnel/personnel`
  - **定位器（推测）**: `search_input`, `search_btn`, `add_btn`, `edit_btn`, `delete_btn`, `table_rows`, `table_columns`, `form_name`, `form_mobile`, `form_email` 等。
  - **操作方法**: `add_personnel()`, `edit_personnel()`, `search()`, `get_first_row_data()`, `total_count()`.
- **测试脚本 (`test_personnel_page.py`)**:
  - **Fixture**: `personnel_page` (来自 conftest.py)。
  - **测试场景**: `test_add_personnel`, `test_edit_personnel`, `test_search_personnel`。
  - **断言**: 预期涉及 `total_count()`, `get_first_row_data()`, 以及元素是否存在的断言。

**第二步：逐区域分析（基于推测）**

| 区域 | 元素 | 标签 | 类型 (推测) | 定位器 (推测) | 来源 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **搜索区** | 搜索关键词输入框 | 关键词/姓名 | `el-input` | `#searchInput` | 代码 |
| | 查询按钮 | 查询 | `el-button` | `.search-btn` | 代码 |
| | 重置按钮 | 重置 | `el-button` | `.reset-btn` | 代码 |
| **表格** | 姓名列 | - | `el-table-column` | `.el-table` | 代码 |
| | 手机号列 | - | `el-table-column` | `.el-table` | 代码 |
| | 操作列 | - | `el-table-column` | `.el-table` | 代码 |
| **表单 (新增/编辑弹窗)** | 姓名输入框 | 姓名 | `el-input` | `.el-dialog ...` | 代码 |
| | 手机号输入框 | 手机号 | `el-input` | `.el-dialog ...` | 代码 |
| **分页** | 分页组件 | - | `el-pagination` | `.el-pagination` | 代码 |

> **注意**: 以上表格中的“推测”项，需要您提供准确的代码文件才能确认为「代码提取」。

---

### 关键依赖缺失

为了完成精确的 `PAGE_CONTEXT.md` 和 `PAGE_INTERFACE.yaml`，我**缺少以下关键输入**：

1.  **具体页面名**：人员管理 (`PersonnelPage`) 还是用户管理 (`UserPage`)？
2.  **Page Object 代码路径**：`ZJSN_Test-master526/page/personnel_page/PersonnelPage.py` (当前上下文显示文件不存在)
3.  **测试脚本路径**：`ZJSN_Test-master526/script/personnel/test_personnel_page.py` (当前上下文显示文件不存在)
4.  **完整的 `MODULE_CONTEXT.md`**：上文中只截取了一部分，我应该加载完整文件以获得全部上下文。

**请提供上述信息，我将立即为您生成最终的 `PAGE_CONTEXT.md` 和 `PAGE_INTERFACE.yaml`。**