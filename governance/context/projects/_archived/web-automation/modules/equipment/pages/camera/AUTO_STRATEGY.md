```yaml
---
version: 1.0
source: ai
source_agent: auto-strategy
created: 2026-06-18T13:00:00+08:00
module: equipment
page: camera
description: 摄像头管理页面自动化覆盖策略（基于 AI 推测版页面分析）
---

# AUTO_STRATEGY — 摄像头管理

## 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
|---------|------|--------|----------|------|
| TC-001 | 页面正常加载 - 默认展示列表 | P0 | ✅ | 基础冒烟，定位器稳定（表格 data-testid 或 el-table） |
| TC-002 | 搜索摄像头 - 按名称/IP模糊搜索 | P0 | ✅ | 核心搜索功能，输入框 placeholder 稳定，按钮文案稳定 |
| TC-003 | 搜索摄像头 - 按分组筛选 | P0 | ✅ | 下拉选择，使用 aria-label 定位，稳定 |
| TC-004 | 搜索摄像头 - 按在线状态筛选 | P0 | ✅ | 同上 |
| TC-005 | 搜索摄像头 - 组合条件搜索 | P0 | ✅ | 覆盖多种条件组合 |
| TC-006 | 搜索后重置 | P0 | ✅ | 重置按钮文案稳定 |
| TC-007 | 添加摄像头 - 成功创建 | P0 | ✅ | 弹出 dialog，输入框 placeholder 稳定，确定按钮可点击 |
| TC-008 | 添加摄像头 - 必填项为空校验 | P1 | ✅ | 弹窗校验提示，定位器稳定 |
| TC-009 | 添加摄像头 - 重复名称/IP校验 | P1 | ✅ | 需要测试接口返回，但自动化可覆盖 |
| TC-010 | 编辑摄像头 - 修改名称/IP | P0 | ✅ | 编辑按钮可通过图标或文字定位（稳定），dialog 复用 |
| TC-011 | 删除摄像头 - 确认删除 | P0 | ✅ | 使用 el-popconfirm 或按钮文字，需留意定位器稳定性 |
| TC-012 | 分页 - 切换每页条数 | P0 | ✅ | el-pagination 有稳定的 class/aria-label |
| TC-013 | 分页 - 跳转下一页/上一页 | P0 | ✅ | 分页按钮文本或 class 稳定 |
| TC-014 | 表格 - 排序（如有） | P2 | ❌ | 若支持，但优先级低；且定位器依赖列头点击，易受 UI 变更影响，建议手动覆盖 |
| TC-015 | 导出摄像头列表（如有） | P1 | ✅ | 导出按钮定位器稳定，但需注意文件下载处理 |
| TC-016 | 表格空状态展示 | P1 | ✅ | 通过 el-table__empty-block 定位，稳定 |

**风险标注**：
- TC-011 删除：若使用 el-popconfirm，其确认按钮的定位器可能需要在不同版本中验证，标注⚠️风险。
- TC-014 排序：如果采用 aria-sort 属性，可提升稳定性，默认暂不自动化。
- TC-015 导出：需处理浏览器下载路径，可能增加维护，但值得自动化。

## 2. PageObject 拆分方案

### 建议的 Page 类及职责

```
CameraPage                    # 主页面（搜索区、表格、分页、添加按钮）
├── __init__(driver)          # 组合所有组件
├── search_with(...)          # 封装搜索操作
├── reset_search()            # 重置搜索
├── get_table_row_count()     # 获取表格行数
├── get_pagination_info()     # 获取分页信息
├── click_add_button()        # 点击添加摄像头（返回 CameraAddDialog）
├── click_edit_button(row)    # 点击编辑（返回 CameraEditDialog）
├── click_delete_button(row)  # 点击删除
├── confirm_delete()          # 确认删除
├── cancel_delete()           # 取消删除
└── wait_for_table_loaded()   # 等待表格渲染完成

CameraAddDialog               # 添加摄像头弹窗
├── __init__(driver, parent_page)
├── fill_name(name)
├── fill_ip(ip)
├── fill_port(port)
├── select_group(group_name)
├── select_protocol(protocol)
├── click_confirm()
├── click_cancel()
└── get_validation_message()

CameraEditDialog              # 编辑摄像头弹窗（可复用 CameraAddDialog，根据需要）
├── __init__(driver, parent_page)
└── (与 AddDialog 结构相似，可继承或组合)

CameraDeleteConfirm           # 删除确认浮层（如 el-popconfirm）
├── click_confirm()
└── click_cancel()
```

**说明**：
- 每个 Page 类接收 `driver` 参数，操作方法返回 `self` 支持链式调用。
- 复杂弹窗独立为类，便于维护和复用（添加/编辑弹窗结构类似，可提取共用基类 `CameraDialogBase`）。
- 删除确认框因交互简单且全局只有一个，可合并到 `CameraPage` 中，但若存在多个删除场景则独立。

## 3. 公共组件复用分析

### 可复用的 BasePage 方法

| BasePage 方法 | 复用场景 |
|--------------|---------|
| `wait_visible(locator)` | 等待搜索区、表格、弹窗可见 |
| `wait_clickable(locator)` | 等待按钮可点击 |
| `input_text(locator, text)` | 输入框填写（名称/IP 等） |
| `click(locator)` | 点击按钮、链接 |
| `get_text(locator)` | 获取表格单元格文本 |
| `is_element_present(locator)` | 检查弹窗是否出现 |
| `select_option_by_label(locator, label)` | el-select 下拉选择分组、状态、协议等 |
| `get_table_data(locator)` | 获取表格所有行数据（需要封装） |
| `click_pagination_page(page_number)` | 分页跳转（若 BasePage 已有） |

### ElementPlusHelper 扩展建议

- **el-select 定位辅助**：鉴于 camera 页面多次使用 `el-select` 且 aria-label 可能有重复风险，建议在 `ElementPlusHelper` 中添加 `select_by_aria_label(label, option_text)` 方法，稳定处理下拉展开与选择。
- **el-table 排序处理**：如有需要，添加 `click_table_header(column_index)` 并等待排序状态更新。
- **el-popconfirm 确认**：添加 `confirm_popup(locator)` 方法，内部处理确认按钮的显式等待。

## 4. 等待策略建议

### 页面特有的异步行为

| 行为 | 触发条件 | 等待时机 | 建议方案 |
|------|---------|---------|---------|
| 表格数据加载 | 页面加载 / 搜索 / 分页 / 添加/编辑后 | 表格 body 出现 data-row | `wait.until(EC.visibility_of_element_located(table_locator))` + 等待 loading 消失（若有 el-loading） |
| 搜索/重置响应 | 点击搜索/重置 | 等待表格刷新（行数变化或 loading 消失） | 使用自定义 `wait_for_table_refresh(previous_rows)` |
| 弹窗出现 | 点击添加/编辑 | el-dialog__wrapper 出现并完成动画 | `wait.until(EC.visibility_of_element_located(dialog_locator))` |
| 弹窗关闭（添加/编辑成功） | 点击确定 | 弹窗消失，表格刷新 | 配合 `wait_for_invisibility` + 表格刷新等待 |
| 下拉菜单展开 | 点击 el-select | el-select-dropdown 出现 | `wait.until(EC.visibility_of_element_located(dropdown_locator))` |
| 删除确认框 | 点击删除 | el-popconfirm 出现 | `wait.until(EC.visibility_of_element_located(popconfirm_locator))` |

### 建议的等待封装

在 `CameraPage` 中定义 `_wait_for_table_loaded(timeout=10)` 方法：

```python
def _wait_for_table_loaded(self, timeout=10):
    # 方案1：等待 loading 消失（若存在 el-loading）
    try:
        wait(self.driver, 2).until_not(EC.visibility_of_element_located(self.loading_mask))
    except TimeoutException:
        pass
    # 方案2：等待表格 body 中至少出现第一个数据行
    wait(self.driver, timeout).until(
        lambda d: len(d.find_elements(*self.table_row_locator)) > 0
        # 或：self.is_element_present(self.table_body_locator)
    )
```

对于弹窗操作，建议在 `click_confirm()` 后调用 `wait_for_dialog_close()` + `_wait_for_table_loaded()`。

## 5. ROI 分析

### 预估工时

| 项目 | 预估时间（小时） |
|------|----------------|
| PageObject 类编写（CameraPage + CameraAddDialog + CameraEditDialog） | 4 |
| 测试用例实现（10个自动化用例 + 公共 fixture） | 6 |
| 调试与首次执行 | 2 |
| **首次部署总开发时间** | **12 小时** |
| **月度维护成本**（定位器变更、功能迭代） | **2 小时/月** |

### 手工执行成本

| 项目 | 数值 |
|------|------|
| 每轮手工执行所有 P0 用例时间（10个） | 20 分钟 |
| 每轮手工执行所有 P1 用例时间（3个） | 8 分钟 |
| 合计手工执行时间 | 28 分钟/轮 |
| 回归频率（假设每周 2 次回归） | 8 次/月 |

### ROI 计算

- 月度手工执行时间：28 分钟 × 8 = 224 分钟 ≈ 3.73 小时
- 月度自动化维护成本：2 小时
- 自动化节省时间（每月）：3.73 - 2 = 1.73 小时
- 回收开发投入时间：12 / 1.73 ≈ 6.93 个月

**结论**：约 7 个月可收回开发成本。考虑到摄像头管理页面是设备模块核心功能，后续迭代频繁，长期 ROI 正向。建议优先开发搜索、添加、编辑等 P0 用例，分页和删除次之。

---

> 本策略基于 AI 推测版页面上下文，所有定位器在真实环境验证后需更新 `AUTO_STRATEGY.md` 中的风险标注。