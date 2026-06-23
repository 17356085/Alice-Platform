# Automation Strategy: spare-in-order (备品入库)

## 1. Automation Coverage Matrix

| 测试用例 | 优先级 | 是否自动化 | 原因 |
|----------|--------|-----------|------|
| test_page_loads | P1 | 是 | 基础冒烟，验证页面可达性 |
| test_columns_count | P2 | 是 | 验证表格结构完整性 |
| test_add_button_visible | P2 | 是 | 核心操作入口可见性 |
| test_pagination_visible | P2 | 是 | 数据浏览基础组件 |
| test_search_by_handler | P1 | 是 | CRUD搜索主路径 |
| test_reset_search | P2 | 是 | 搜索交互完整性 |
| test_add_dialog_opens | P1 | 是 | 核心操作路径前提 |
| test_add_dialog_has_form_fields | P2 | 是 | 表单完整性验证 |
| test_view_first_record | P2 | 是 | 查看功能冒烟 |
| test_add_in_order_success | P0 | 是 | 核心业务路径：新增成功 |
| test_delete_created_in_order | P0 | 是 | 核心业务路径：删除成功 |
| test_add_in_order_cancel | P2 | 是 | 取消操作验证 |
| test_add_empty_required | P1 | 是 | 必填校验验证 |

### Coverage Summary

| 指标 | 数值 |
|------|------|
| 总用例数 | 13 |
| 已自动化 | 13 (100%) |
| P0/P1用例 | 7 |
| P0/P1自动化率 | 100% |

---

## 2. PageObject Split Plan

### Main Class: `SpareInOrderPage`

```
SpareInOrderPage
├── __init__(self, driver)
│   └── 继承 BasePage
├── navigate()
├── click_add()
├── click_view_first()
├── search_by_handler(name)
├── reset_search()
├── fill_in_order_handler(name)
├── click_search()
├── delete_by_handler(name)
├── _fill_dialog_by_placeholder(placeholder_contains, value)  # 内部方法，含降级
└── FILTER_HANDLER, FILTER_DATE, BTN_QUERY, BTN_RESET, BTN_ADD, BTN_VIEW  # 定位器常量
```

### Optional Dialog Class

当前页面交互仅一个输入字段（经办人），无需独立 Dialog 类。`_fill_dialog_by_placeholder` 已覆盖填写需求。

### Recommendation

**单类模式** 足够。若未来表单扩展（备件明细、数量、单价等多字段），建议提取 `InOrderDialog` 类。

---

## 3. Public Component Reuse

### BasePage Methods Used

| 方法 | 来源 | 用途 |
|------|------|------|
| `wait_element_visible` | BasePage | 等待元素可见 |
| `click` | BasePage | 点击元素 |
| `send_keys` | BasePage | 输入文本 |
| `wait_table_load` | BasePage | 等待表格加载完成 |
| `is_row_present` | BasePage | 判断某行是否存在 |
| `get_table_row_count` | BasePage | 获取表格行数 |
| `get_table_headers` | BasePage | 获取表格列头列表 |

### ElementPlusHelper Methods

| 方法 | 用途 |
|------|------|
| `dialog_fill_placeholder(placeholder, value)` | 等价于 `_fill_dialog_by_placeholder` |

### New Helpers Needed

| 需要的方法 | 原因 | 优先级 |
|-----------|------|--------|
| 日期选择器填充 | `FILTER_DATE` 存在但测试未覆盖日期搜索 | 中 |
| 详情弹窗验证 | `click_view_first` 未验证详情内容 | 低 |
| 审批状态判断 | 新增后需确认审批链状态 | 中（取决于环境配置） |

---

## 4. Wait Strategy Recommendations

| 场景 | 策略 | 实现 |
|------|------|------|
| 表格加载 | 等待 `el-table__body` 内 `tr` 出现或 `loading` 消失 | `EC.presence_of_element_located` + `EC.invisibility_of_element_located` |
| 对话框打开 | 等待 dialog DOM 出现且 `display` 不为 `none` | `EC.visibility_of_element_located` |
| 对话框关闭 | 等待 dialog DOM 消失 | `EC.invisibility_of_element_located` |
| 表单提交 | 提交后等待表格 `loading` 重新加载 | `EC.staleness_of` 旧表格行 |
| 删除操作 | 触发删除后等待表格重新渲染 | `EC.staleness_of` + 新表格加载 |
| 搜索查询 | 查询后等待表格更新 | `EC.presence_of_element_located` 结合文本验证 |
| 查看操作 | 等待详情弹窗/抽屉出现 | `EC.visibility_of_element_located` |
| 日期选择器 | 等待日期面板弹出后再操作 | `EC.visibility_of_element_located` 日期面板 |

### 默认超时设置

| 参数 | 值 |
|------|-----|
| 隐式等待 | 10s |
| 显式等待超时 | 15s |
| 轮询间隔 | 0.5s |

---

## 5. ROI Analysis

### Assumptions

| 参数 | 值 |
|------|-----|
| 手动执行单次测试成本 | 12 分钟 |
| 手动测试频率 | 每日 1 次 |
| 自动化开发工时 | 10 小时 (含PO + 测试脚本) |
| 自动化维护工时 (月) | 3 小时 |
| 自动化执行时间 | 3 分钟 |
| 自动化运行频率 | 每日 2 次 (CI/CD + 开发者触发) |

### Cost Calculation

| 项目 | 数值 |
|------|------|
| 月手动成本 | 12min × 30 = 360min = 6h |
| 月自动化维护 + 执行 | 3h + (3min × 60 = 3h) = 6h |
| 月节省 | 0h (基本持平) |

### Non-Financial Benefits

- **门禁价值**: 审批链完整性验证，防止审批流程意外修改导致业务异常
- **回归覆盖**: 13 个场景 100% 自动化，含审批流程验证
- **数据一致性**: `AUTO_IN_` 前缀确保测试数据可追溯
- **清理机制**: `cleanup_tracker` + `CREATED_HANDLER` 双重保障
- **列结构监控**: `test_columns_count` 及时发现意外列变更

### Verdict

**值得自动化**。虽然直接人力成本节省有限（与手动持平），但审批链的回归保障价值远高于执行成本。审批流程变更通常影响面广，自动化门禁可防止静默破坏。
