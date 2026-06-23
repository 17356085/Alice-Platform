# 备品盘点调整 — 页面上下文

## 页面信息
- 路由: 从左侧导航 `库管管理` → `备品备件管理` → `盘点调整`
- 路由 Hash: `#/warehouse/spare/stock_adjust`（从 conftest.py 推断）
- Page Object: `SpareStockAdjustPage`（位于 `page/warehouse_page/SpareStockAdjustPage.py`）
- 测试脚本: `test_spare_stock_adjust.py`（位于 `script/warehouse/test_spare_stock_adjust.py`）
- 页面类型: 只读查询页面，盘点调整直接生效，无审批流
- 权限类型: 只读（无增删改按钮，仅可查询和重置）

## 页面整体结构
- **搜索区**: 位于页面顶部，包含物品编号输入框、日期选择器、查询/重置按钮
- **主内容区**: 展示 `el-table` 表格，列出所有盘点调整记录
- **分页区**: 位于表格下方，包含 `el-pagination` 分页器

## 搜索/筛选区
| 序号 | 元素 | 标签 | 类型 | 定位器 | 来源 |
|-----|------|------|------|-------|------|
| 1 | 物品编号输入框 | FILTER_ITEM_CODE | `el-input` | `//input[@placeholder="请输入物品编号"]` | 从 PO 代码直接提取 |
| 2 | 日期选择器 | FILTER_DATE | `el-date-picker` | `//input[@placeholder="选择日期"]` | 从 PO 代码直接提取 |

## 操作按钮
| 序号 | 按钮 | 触发动作 | 定位器 | 来源 |
|-----|------|---------|-------|------|
| 1 | 查询 | 根据筛选条件刷新表格数据 | `//button[contains(.,"查询")]` | 从 PO 代码直接提取 |
| 2 | 重置 | 清空所有筛选条件，恢复全量数据 | `//button[contains(.,"重置")]` | 从 PO 代码直接提取 |

## 表格列定义（部分推断）
| 序号 | 列标题 | 数据类型 | 来源 |
|-----|-------|---------|------|
| 1 | 物品编号 | 文本 | 从搜索字段"物品编号"反向推断 |
| 2 | 物品名称 | 文本 | 从同类备品页面推断 |
| 3 | 调整前数量 | 数值 | 从页面业务含义推断 |
| 4 | 调整后数量 | 数值 | 从页面业务含义推断 |
| 5 | 调整数量 | 数值 | 从页面业务含义推断 |
| 6 | 调整日期 | 日期 | 从搜索字段"日期"反向推断 |
| 7 | 操作人 | 文本 | 从审计日志惯例推断 |

> 注：表格列定义为推断，未在 PO 或测试中显式引用具体列。上述列名根据业务场景推测，实际 DOM 可能不同。

## 弹窗
无。页面为只读查询，无新增/编辑/删除弹窗，无审批对话框。

## 业务规则（从代码推断）
| 规则 | 推断依据 | 置信度 |
|------|---------|-------|
| 盘点调整直接生效，无需审批 | PO 模块 docstring 明确说明 | 高（从 PO 代码确认） |
| 所有搜索字段均为可选，可单独使用 | PO 方法 `search_by_item_code` 仅输入物品编号 | 高（从 PO 方法推断） |
| 重置后清除所有搜索条件 | PO 方法 `reset_search` 仅点击重置按钮 | 高（从 PO 方法推断） |
| 日期筛选为单日选择（非范围） | 定位器名称为 `FILTER_DATE`（单数非 `_START`/`_END`） | 中（从定位器命名推断） |

## 测试场景映射
| 测试函数 | 场景描述 | 验证点 |
|---------|---------|-------|
| `TestSpareStockAdjustLoad::test_page_loads` | 页面正常加载，表格渲染 | `len(rows) >= 0`，确认表格行可见 |
| `TestSpareStockAdjustLoad::test_pagination_visible` | 分页器可见 | `len(pag) > 0`，确认分页组件渲染 |
| `TestSpareStockAdjustSearch::test_search_by_item_code` | 按物品编号搜索 | 输入"test"并点击查询，Vue 稳定 |
| `TestSpareStockAdjustSearch::test_reset_search` | 重置搜索 | 点击重置按钮，Vue 稳定 |
