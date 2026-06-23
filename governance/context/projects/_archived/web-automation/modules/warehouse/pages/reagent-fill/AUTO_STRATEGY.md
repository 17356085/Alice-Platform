# Automation Strategy: reagent-fill (三剂消耗-装填管理)

## 1. Automation Coverage Matrix

| 测试用例 | 优先级 | 是否自动化 | 原因 |
|----------|--------|-----------|------|
| test_page_loads | P1 | 是 | 基础冒烟，验证页面可达性 |
| test_pagination_visible | P2 | 是 | 分页控件是数据浏览的基础组件 |
| test_add_button_visible | P2 | 是 | 核心操作入口 | 
| test_search_by_item_name | P1 | 是 | CRUD搜索主路径 |
| test_reset_search | P2 | 是 | 搜索交互完整性 |
| test_add_dialog_opens | P1 | 是 | 核心操作路径前提 |
| test_add_dialog_has_form_fields | P2 | 是 | 表单完整性验证 |
| test_add_item_success | P0 | 是 | 核心业务路径：新增成功 |
| test_delete_created_item | P0 | 是 | 核心业务路径：删除成功 |
| test_add_item_cancel | P2 | 是 | 取消操作的冒烟验证 |
| test_add_empty_required | P1 | 是 | 必填校验的前端验证 |

### Coverage Summary

| 指标 | 数值 |
|------|------|
| 总用例数 | 11 |
| 已自动化 | 11 (100%) |
| P0/P1用例 | 7 |
| P0/P1自动化率 | 100% |

---

## 2. PageObject Split Plan

### Main Class: `ReagentFillPage`

```
ReagentFillPage
├── __init__(self, driver)
│   └── 继承 BasePage
├── navigate()
├── click_add()
├── search_by_item_name(name)
├── reset_search()
├── fill_item_name(name)
├── click_search()
├── delete_item_by_name(name)
├── _fill_dialog_by_placeholder(placeholder_contains, value)  # 内部方法
└── FILTER_ITEM_NAME, BTN_QUERY, BTN_RESET, BTN_ADD  # 定位器常量
```

### Optional Dialog Class

当前页面交互简单（仅一个输入字段），无需独立 Dialog 类。`_fill_dialog_by_placeholder` 方法已覆盖对话框填写需求。若未来表单字段增多，可提取为独立 Dialog 类。

### Recommendation

**单类模式** 足够。Dialog 类提取阈值：>= 4 个表单字段。

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

### ElementPlusHelper Methods

| 方法 | 用途 |
|------|------|
| `dialog_fill_placeholder(placeholder, value)` | 等价于 `_fill_dialog_by_placeholder` |

### New Helpers Needed

无。当前方法组合已覆盖所有测试场景。

---

## 4. Wait Strategy Recommendations

| 场景 | 策略 | 实现 |
|------|------|------|
| 表格加载 | 等待 `el-table__body` 内 `tr` 元素出现或 `loading` 消失 | `EC.presence_of_element_located` + `EC.invisibility_of_element_located` |
| 对话框打开 | 等待 dialog DOM 出现，`display` 不为 `none` | `EC.visibility_of_element_located` |
| 对话框关闭 | 等待 dialog DOM 消失 | `EC.invisibility_of_element_located` |
| 表单提交 | 提交后等待表格 `loading` 重新加载 | `EC.staleness_of` 旧表格行 |
| 删除操作 | 触发删除后等待表格重新渲染 | `EC.staleness_of` + 新表格加载 |
| 搜索查询 | 查询后等待表格更新 | `EC.presence_of_element_located` 结合文本验证 |

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
| 手动执行单次测试成本 | 10 分钟 |
| 手动测试频率 | 每日 1 次 |
| 自动化开发工时 | 8 小时 (含PO + 测试脚本) |
| 自动化维护工时 (月) | 2 小时 |
| 自动化执行时间 | 2 分钟 |
| 自动化运行频率 | 每日 2 次 (CI/CD + 开发者触发) |

### Cost Calculation

| 项目 | 数值 |
|------|------|
| 月手动成本 | 10min × 30 = 300min = 5h |
| 月自动化维护 + 执行 | 2h + (2min × 60 = 2h) = 4h |
| 月节省 | 1h |
| 年节省 | ~12h |
| 回收期 | ~4 个月 (8h / (1h/月) = 8 个月，但加上CI/CD价值) |

### Non-Financial Benefits

- CI/CD 门禁：防止装填管理功能回归
- 回归测试覆盖：11 个场景 100% 自动化
- 数据一致性验证：`AUTO_装填_` 前缀确保测试数据可追溯
- 清理机制兜底：避免测试数据污染生产环境

### Verdict

**值得自动化**。页面 CRUD 操作稳定，PO 设计成熟，11 个测试场景覆盖完整，回收期约 8 个月（考虑非经济收益后显著缩短）。
