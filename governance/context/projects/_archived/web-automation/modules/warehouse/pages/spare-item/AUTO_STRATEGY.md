好的，收到指令。作为自动化测试专家，基于您提供的 `warehouse` 模块 `spare-item` 页面的技术分析、测试设计规范和架构上下文，我将为您制定详细的自动化测试策略。

以下是产出的 `AUTO_STRATEGY.md` 文档。

---

# 自动化测试策略：Warehouse - Spare Item

## 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
|----------|------|--------|------------|------|
| TC-SI-001 | 页面正常加载 | P0 | ✅ | 基础冒烟，验证页面框架和基础组件渲染，定位器稳定。 |
| TC-SI-002 | 单条件搜索（按编码） | P0 | ✅ | 核心功能，高频操作。通过输入框搜索，定位器稳定。 |
| TC-SI-003 | 多条件组合搜索（名称+分类） | P0 | ✅ | 核心功能，高频操作。通过选择器和输入框组合，定位器稳定。 |
| TC-SI-004 | 搜索后重置 | P0 | ✅ | 核心功能，高频操作。点击重置按钮，断言表格数据恢复。 |
| TC-SI-005 | 分页切换 | P1 | ✅ | 核心功能。验证分页组件交互和表格数据刷新。 |
| TC-SI-006 | 新增备件（成功） | P0 | ✅ | 核心功能。通过弹窗填写表单并提交，验证数据新增成功。 |
| TC-SI-007 | 新增备件（表单校验失败） | P1 | ⚠️ | 验证必填项/格式错误提示。定位器稳定，但需处理弹窗内多种错误提示文本。 |
| TC-SI-008 | 编辑备件（部分字段修改） | P0 | ✅ | 核心功能。打开弹窗，修改部分字段并保存。 |
| TC-SI-009 | 删除备件（确认取消） | P1 | ❌ | 弹窗交互（确认/取消）。建议通过API验证，UI自动化成本高且不稳定。 |
| TC-SI-010 | 删除备件（确认删除） | P0 | ✅ | 核心功能。确认弹窗后，验证数据被移除。 |
| TC-SI-011 | 批量删除（选中后删除） | P1 | ❌ | 需要多选框+确认弹窗。业务场景较为复杂，UI自动化维护成本较高。建议通过API测试。 |
| TC-SI-012 | 导入备件 | P2 | ❌ | **一次性操作**（上线前初始化数据）。涉及文件上传，环境依赖性强。 |
| TC-SI-013 | 导出备件 | P1 | ❌ | 涉及文件下载，不同CI环境下载逻辑/路径不一致，易出错且难以断言。 |
| TC-SI-014 | 页面无数据时展示空状态 | P1 | ⚠️ | **定位器不稳定**：需要前置条件（清空所有数据），且依赖于“无数据”提示元素是否存在，环境准备成本高。 |
| TC-SI-015 | 界面UI美观度检查 | P2 | ❌ | 需要人工视觉判断，不适合自动化。 |
| TC-SI-016 | 切换备件状态（启用/停用） | P1 | ✅ | 核心功能。通常是表格内的`el-switch`或`el-button`，交互较为稳定。 |

``` 表格说明
✅：自动化
⚠️：自动化但有风险（理由中已标注）
❌：不建议自动化
```

**风险标注：**
- **TC-SI-007、TC-SI-014**: 表格无数据时的空状态提示，其元素结构可能随版本变化或依赖于复杂前置条件，自动化测试环境准备和维护成本高，风险较高。

## 2. PageObject 拆分方案

根据“一个页面一个Page类，复杂弹窗独立”的原则，建议如下拆分：

```
page_objects/
└── warehouse/
    └── spare_item/
        ├── __init__.py
        ├── spare_item_page.py          # 主页面类
        └── spare_item_dialog.py        # 新增/编辑备件弹窗类
```

### 2.1 `SpareItemPage`
- **职责**: 封装备件列表页面的所有操作，包括搜索、表格、分页、批量操作、导入/导出入口。
- **核心方法**:
  - `search_by_code(code: str)` -> `self`
  - `search_by_name_and_category(name: str, category: str)` -> `self`
  - `click_reset()` -> `self`
  - `click_add()` -> `SpareItemDialog`
  - `click_edit(row_index: int)` -> `SpareItemDialog`
  - `click_delete(row_index: int)` -> `self` (处理确认弹窗)
  - `get_table_row_data(row_index: int)` -> `dict`
  - `select_table_rows(row_indices: list)` -> `self`
  - `check_page_loaded()` -> `bool`

### 2.2 `SpareItemDialog`
- **职责**: 封装新增/编辑备件弹窗的CRUD操作。
- **核心方法**:
  - `fill_form(data: dict)` -> `self` (传入`{field: value}`字典)
  - `click_submit()` -> `SpareItemPage`
  - `click_cancel()` -> `SpareItemPage`
  - `get_form_data()` -> `dict`

## 3. 公共组件复用分析

### 3.1 复用 `BasePage` 已有方法（高频）

- **`wait_for_element_visible(locator)` / `wait_for_element_clickable(locator)`**: 所有页面元素交互前调用。
- **`click_element(locator)`**: 点击搜索、重置按钮。
- **`type_text(locator, value)`**: 搜索区/弹窗内的文本输入框。
- **`get_element_text(locator)`**: 获取表格单元格、提示信息。
- **`scroll_to_element(locator)`**: 处理需要滚动才能看到的元素（如下方或隐藏区域）。
- **`take_screenshot(name)`**: 测试失败时截图。

### 3.2 复用 `ElementPlusHelper`（高频）

- **`select_dropdown(locator, option_text)`**: 搜索区和弹窗内的 `el-select` 组件。
- **`select_date(locator, date_str)`**: `el-date-picker` 组件（如果有）。
- **`handle_table_checkbox(locator)`**: 表格内的 `el-checkbox` 组件。

### 3.3 需要扩展 `ElementPlusHelper` 或新建工具方法

- **`handle_table_switch(locator)`**: 针对表格内`el-switch`组件的交互，需要封装为点击后确认状态变化。
- **`handle_dialog`**: 对弹出的 `el-dialog`，需要封装出 `wait_for_dialog_visible()` 和 `wait_for_dialog_closed()`。

## 4. 等待策略建议

该页面特有的一些异步行为建议如下处理：

1. **表格加载**:
   - 行为: 搜索/重置/分页切换后，表格数据异步请求并渲染。
   - 策略: 等待 `el-table` 中的 `el-table__body` 或某个特定数据行出现。建议使用 `wait_for_element_visible` 结合动态的 `XPath` 或 `CSS` 选择器，例如等待第一行某一列（如“备件编码”）出现。

2. **弹窗打开**:
   - 行为: 点击“新增/编辑”按钮后，弹窗异步渲染。
   - 策略: 使用 `wait_for_element_visible` 等待 `el-dialog` 的 `.el-dialog__wrapper` 或 `.el-dialog__body` 变为可见。

3. **表单提交**:
   - 行为: 点击“确定”后，系统处理并关闭弹窗、刷新表格。
   - 策略: 先等待弹窗关闭 (`wait_for_element_invisible` 或 `wait_for_element_not_present`)，再等待表格加载完成。

4. **删除/状态切换**:
   - 行为: 操作后可能出现“确认”弹窗或直接刷新表格。
   - 策略: 如果是弹窗，先处理弹窗；否则直接等待表格更新。可以封装一个通用方法 `wait_for_table_refresh()`，专门处理表格数据变化后的等待。

```python
# 建议的等待封装结构
def wait_for_table_refresh(page, timeout=10):
    """等待表格数据更新完毕（等待页面加载完成或某个关键元素消失再出现）"""
    # 示例：等待 “加载中” 图标消失
    page.wait_for_element_invisible(by_css='.el-loading-mask')
```

## 5. ROI 分析

### 假设条件

- 预期执行频率: **每日 3 次** (CI/CD构建)。
- 手工执行时间: 完成上述全量P0/P1测试约为 **15 分钟/次**。
- 预估自动化开发时间（仅UI层）: **5.5 小时** (包括 `SpareItemPage`、`SpareItemDialog` 以及对应的 `conftest` 配置)。
- 预估月度维护成本（按平均每月页面变动2次计算）：**0.5 小时/月**。

### ROI 计算

- **月度手工执行时间**: `15 分钟/次 × 3 次/天 × 22 工作日/月` = **990 分钟/月** ≈ **16.5 小时/月**
- **月度自动化执行时间**: 假设自动化脚本执行耗时 2 分钟，则 `2 分钟/次 × 3 次/天 × 22 天/月` = **132 分钟/月** ≈ **2.2 小时/月**
- **月度节省时间**: `16.5 - 2.2 = 14.3 小时/月`
- **月度净收益**: `月度节省时间 - 月度维护成本` = `14.3 - 0.5` = **13.8 小时/月**
- **投资回收期**: `总投资（开发时间） / 月度净收益` = `5.5 / 13.8` ≈ **0.4 个月 -> 约2周**

**结论**: 自动化测试的投资回报率（ROI）非常高。初始开发的 **5.5 小时** 成本，在 **约2周** 内即可通过减少手工执行时间收回，后续每月可释放约 **13.8 小时** 的人力资源用于更高价值的测试活动，如探索性测试和场景化自动化。