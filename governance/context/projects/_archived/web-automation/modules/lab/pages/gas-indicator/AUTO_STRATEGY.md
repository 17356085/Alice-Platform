好的，遵照您的指示。作为自动化测试架构师，我将基于您提供的 `GasIndicatorPage.py`、`test_gas_indicator.py` 和 `PAGE_CONTEXT.md`，制定该页面的自动化策略。

---

# AUTO_STRATEGY — lab / gas-indicator

> **版本**: 1.0 | **日期**: 2026-06-18  
> **策略依据**: `GasIndicatorPage.py`, `test_gas_indicator.py`, `PAGE_CONTEXT.md`, `BasePage` 能力清单  
> **架构约束**: P0 用例必须自动化，定位器不稳定的用例标注风险，一次性操作不自动化

---

## 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
|----------|------|--------|-----------|------|
| GI-01 | 页面正常加载并显示表格字段 | P0 | ✅ | 基础冒烟，PageObject 已完整实现 `navigate` 和 `get_table_headers`，定位器稳定 |
| GI-02 | 表格列数据可读 | P0 | ✅ | 冒烟延伸，已验证 `get_column_data` 可用，列索引已知 |
| GI-03 | 新增一条完整指标数据 | P0 | ✅ | 核心 CRUD，`click_add` + `dialog_input_*` + `dialog_confirm` 全链路已实现 |
| GI-04 | 必填项为空时新增失败 | P1 | ✅ | 异常场景，可复用“新增”弹窗链路，验证弹窗不关闭或错误提示 |
| GI-05 | 指标名称搜索 | P1 | ❌ | 当前页面无搜索区，搜索功能不属于本页面职责，自动化无意义 |
| GI-06 | 编辑单条指标数据 | P1 | ✅ | “编辑”操作可复用“新增”弹窗能力，仅需增加“编辑”按钮定位 |
| GI-07 | 清空必填项后编辑 | P2 | ❌ | 表单异常场景，需要判断错误样式，属于 UI 属性验证（CSS class），不自动化 |
| GI-08 | 备注字段支持长文本 | P2 | ❌ | 需验证 textarea 多行输入行为，回归价值低 |
| GI-09 | 删除单条指标 | P1 | ✅ | 核心 CRUD，Table 行+确认弹窗链路清晰 |
| GI-10 | 批量删除指标 | P2 | ❌ | 页面无“全选/批量删除”按钮，当前版本不支持该功能 |

**P0 覆盖率**: 100% | **总自动化率**: 5/10 = 50%

### 风险标注

| 用例 | 定位器风险等级 | 风险说明 |
|------|--------------|----------|
| GI-01 | B 级 | `.el-table__header-wrapper thead` 依赖 EP 类名，但表头稳定 |
| GI-03 | A 级 | `_find_field_in_dialog` 完全依赖标签文本（如“指标名称”），文案修改即失效 |
| GI-04 | A 级 | 同上，依赖标签文本 |
| GI-06 | A 级 | 同上，依赖标签文本 |

---

## 2. PageObject 拆分方案

### 当前拆分评估

`GasIndicatorPage` 已遵循 **“一个页面一个 Page 类”** 原则，弹窗表单操作以 `dialog_input_*` 内联方式实现。拆分建议如下：

| 拆分对象 | 建议 | 理由 |
|----------|------|------|
| 弹窗表单（6字段） | **不拆分** | 弹窗逻辑简单（仅有 Form，无 Table/其他组件），内联可减少复杂度，降低维护成本。保留 `dialog_input_*` 方法不变。 |
| 行操作（编辑/删除） | **不新增类** | 编辑/删除通过 TableRow 操作完成，属于 GasIndicatorPage 职责，可通过新增 `_edit_row` / `_delete_row` 私有方法实现。 |

### 最终建议 Page 结构

```
GasIndicatorPage (extends BasePage)
  ├─ 导航：navigate()
  ├─ 表格：click_add(), get_table_headers(), get_column_data(), get_empty_text(), 
  │         click_edit_row(index), click_delete_row(index)
  ├─ 弹窗：dialog_input_name(), dialog_input_category(), dialog_input_unit(), 
  │         dialog_input_rule(), dialog_input_threshold(), dialog_input_remark(), 
  │         dialog_confirm(), dialog_cancel()
  └─ 状态：_wait_loading_gone(), _get_dialog(), _find_field_in_dialog()
```

---

## 3. 公共组件复用分析

### 可复用 BasePage 方法

| 方法 | 复用点 | 当前使用 |
|------|--------|----------|
| `navigate_to(menu1, menu2)` | 导航 | `navigate()` 已使用 |
| `wait_page_ready(timeout)` | 页面加载 | `navigate()` 已使用 |
| `wait_vue_stable()` | Vue 渲染稳定 | 多处已使用 |
| `_wait_loading_gone(timeout)` | 等待 Loading 消失 | 新增独立方法，与 BasePage 版本对比 |
| `get_table_headers()` | 获取表头 | `test_gi_01` 已使用 |
| `get_empty_text()` | 获取空数据文本 | `test_gi_01` 已使用 |
| `get_column_data(col_index)` | 获取列数据 | `test_gi_02` 已使用 |
| `get_table_row_count()` | 行数 | `test_gi_01/02` 已使用 |

### 需扩展 ElementPlusHelper

当前弹窗表单的 `_find_field_in_dialog` 通过 JS 脚本实现文本定位，**无法**直接复用 `ElementPlusHelper.fill_form(fields_dict)` 方法（该方法基于 `el-form-item` 的 `prop` 属性）。建议：

| 方法 | 建议状态 | 理由 |
|------|----------|------|
| `fill_form(fields_dict)` | 不可复用 | 当前表单无 `prop` 属性，仅依赖标签文本 |
| 新增 `fill_form_by_label(labels_values)` | **建议扩展** | 封装通用“按标签文本填入表单”能力，可被无 `data-testid` 的页面复用 |

---

## 4. 等待策略建议

### 页面特异性异步行为

| 行为 | 触发时机 | 等待建议 |
|------|----------|----------|
| 表格数据异步加载 | `navigate()` 后 | `_wait_loading_gone()` 后，额外等待 **`TABLE_ROWS` 数量 > 0** 或 **`EMPTY_TEXT` 出现** |
| 弹窗异步渲染 | `click_add()` / `click_edit_row()` 后 | 等待 `DIALOG` 的 `presence_of_element_located`，并跟随 `wait_vue_stable()` |
| 表单字段加载延迟 | 弹窗打开后 | 等待第一个 `el-form-item__label` 出现，再进行 `_find_field_in_dialog` |

### 建议封装

```python
def _wait_table_data(self):
    """等待表格数据加载完成（行数>0 或空文本出现）"""
    self._wait_loading_gone(timeout=10)
    try:
        WebDriverWait(self.driver, 5).until(
            lambda d: d.find_elements(*self.TABLE_ROWS) or d.find_element(*self.EMPTY_TEXT)
        )
    except TimeoutException:
        raise TimeoutException("表格数据加载超时")
```

---

## 5. ROI 分析

| 项目 | 数值 | 说明 |
|------|------|------|
| 预估开发时间 | **6 小时** | 基于现有代码（~250行），增量开发 GI-04/06/09 的测试脚本 + 等待封装 |
| 预估维护成本 | **0.5 小时/月** | 主要风险为标签文案变更（A 级风险），若文案不变则维护量接近 0 |
| 手工执行时间 | **15 分钟/次** | 全链路 CRUD + 展示验证 |
| 建议执行频率 | **每日 5 次** | 集成测试 + 预发布回归 |

### ROI 计算（12个月）

```
总收益 = 手工时间 * 执行频率 * 月数
       = 15分钟 * 5次/天 * 250个工作日/年 ≈ 31,250分钟/年
       ≈ 520小时/年

总成本 = 开发时间 + 维护成本 * 12
       = 6小时 + 0.5小时 * 12
       = 6小时 + 6小时 = 12小时

ROI = (520 - 12) / 12 ≈ 42.3 倍
```

**结论**: 收益极高，自动化建议立即实施。对于标签文案不稳定风险，建议：
1. 在当前 A 级风险用例中增加 `@allure.issue("A级风险：依赖标签文本")` 标记。
2. 与产品/开发沟通，推动添加 `data-testid` 实现永久稳定。