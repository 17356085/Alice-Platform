# 自动化策略: 三剂消耗-物品管理 (Reagent Item)

## 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
|---|---|---|---|---|
| TC-RI-001 | 页面正常加载 — 表格渲染正常 | P0 | ✅ 已自动化 | 基础冒烟，验证表格、分页渲染正常。 |
| TC-RI-002 | 分页组件应可见 | P0 | ✅ 已自动化 | 验证关键组件可用性。 |
| TC-RI-003 | 新增按钮应可见 | P0 | ✅ 已自动化 | 验证关键操作入口可用性。 |
| TC-RI-010 | 按物品名称搜索不崩溃 | P1 | ✅ 已自动化 | 核心查询功能 smoke。 |
| TC-RI-011 | 重置搜索条件 | P1 | ✅ 已自动化 | 核心 UI 功能。 |
| TC-RI-020 | 点击新增应弹出弹窗 | P0 | ✅ 已自动化 | 核心交互功能。 |
| TC-RI-021 | 新增弹窗内应有表单输入项 | P1 | ✅ 已自动化 | 验证弹窗内容完整性。 |
| TC-RI-030 | 新增物品 — 填写名称并保存成功 | P0 | ✅ 已自动化 | 核心正向链路，验证新增、数据刷新、总数变化。 |
| TC-RI-031 | 删除刚创建的物品 | P0 | ✅ 已自动化 | 核心反向链路，保障数据闭环和清理。 |
| TC-RI-032 | 新增物品 — 取消操作 | P1 | ✅ 已自动化 | 验证取消行为幂等性。 |
| TC-RI-033 | 新增物品 — 必填校验 | P0 | ✅ 已自动化 | 验证表单校验，`assert error != ""` 严格断言。 |
| TC-RI-040 | 导入物品 (批量) | P2 | ❌ 未自动化 | Import 功能需文件准备，复杂度高。 |
| TC-RI-041 | 导出物品 (批量) | P2 | ❌ 未自动化 | Export 需文件下载处理。 |
| TC-RI-042 | 批量选择删除 | P2 | ❌ 未自动化 | 多选交互复杂度高。 |
| TC-RI-043 | 编辑物品名称 | P2 | ❌ 未自动化 | PO 中无编辑方法，当前版本无编辑功能。 |

**覆盖率总结**: 所有 P0 用例（6 个）已全部自动化；P1 用例（4 个）已全部自动化；P2 用例（4 个）未自动化。P0/P1 覆盖率达 100%。

## 2. PageObject 拆分方案

| Page 类 | 职责 | 关键方法 |
|---|---|---|
| **ReagentItemPage** | 主列表页全部操作 + 新增弹窗交互（通过 `_fill_dialog_by_placeholder` 完成） | `search_by_item_name`, `reset_search`, `click_add`, `fill_item_name`, `delete_item_by_name` |
| **不推荐拆分独立 Dialog 类** | 新增弹窗交互通过 `_fill_dialog_by_placeholder` JS Helper 完成，是 Page 内部实现细节。拆分会引入额外耦合。 | 保持现状。 |

**决策理由**: 同 hazard-item 页面分析 — 单个弹窗且交互通过统一 JS 方法完成时，保持内聚更优。

## 3. 公共组件复用分析

| 公共能力 | 复用情况 | 说明 |
|---|---|---|
| `BasePage.navigate_to` | ✅ **直接复用** | 三参数导航。 |
| `BasePage._wait_loading_gone` | ✅ **直接复用** | 在 `_wait_page_ready` 中调用。 |
| `BasePage.wait_vue_stable` | ✅ **直接复用** | 搜索、重置、弹窗填写后调用。 |
| `BasePage.wait_dialog_open` | ✅ **直接复用** | 在 `click_add()` 中调用。 |
| `BasePage.confirm_message_box` | ✅ **直接复用** | 在 `delete_item_by_name` 中调用。 |
| `BasePage.is_dialog_visible` | ✅ **直接复用** | 在 `test_add_dialog_opens` 中使用。 |
| `BasePage.click_dialog_cancel` / `click_dialog_save` | ✅ **直接复用** | 取消/保存弹窗操作。 |
| `BasePage.get_total_count` | ✅ **直接复用** | 新增后验证总数增加。 |
| `BasePage.is_row_present` | ✅ **直接复用** | 搜索后验证数据存在性。 |
| `BasePage.get_form_error` | ✅ **直接复用** | 必填校验错误信息获取。 |
| `BasePage.click_row_button` | ✅ **直接复用** | 在 `delete_item_by_name` 中定位并点击删除按钮。 |
| **ElementPlusHelper** | **无需扩展** | 当前交互未超出 BasePage 能力范围。`_fill_dialog_by_placeholder` 是私有方法，不适合抽取到全局 Helper。 |

## 4. 等待策略建议

| 场景 | 当前策略 | 建议 | 原因 |
|---|---|---|---|
| 页面初始加载 | `_wait_loading_gone()` + `wait_vue_stable()` | 保持当前策略 | 最可靠的组合。 |
| 搜索/重置 | `wait_vue_stable()` | 保持当前策略 | 确保 Vue 响应完成。 |
| 弹窗打开 | `wait_dialog_open()` | 保持当前策略 | 专用高效方法。 |
| 弹窗填写后 | `wait_vue_stable()` | 保持当前策略 | JS 填写后等待 Vue 更新。 |
| 保存后 | 无显式等待 | **建议增加** `wait_dialog_close()` | 使意图更明确，在 `click_dialog_save` 后等待弹窗关闭再执行后续搜索。 |
| 删除后确认 | `confirm_message_box()`（内含等待） | 保持当前策略 | 方法封装良好。 |

## 5. 特殊模式: CRUD 测试的数据生命周期

```
test_add_item_success:
  before = get_total_count()
  click_add() → fill_item_name(AUTO_三剂_{ts}) → click_dialog_save()
  search_by_item_name(AUTO_三剂_{ts})
  assert is_row_present(name)
  assert after >= before + 1

test_delete_created_item:
  name = TestReagentItemCRUD.CREATED_ITEM_NAME  (类变量传递)
  delete_item_by_name(name)
  search_by_item_name(name)
  assert not is_row_present(name)
  cleanup_tracker 注册兜底

test_add_item_cancel:
  name = AUTO_CANCEL_{ts}
  click_add() → fill_item_name(name) → click_dialog_cancel()
  search_by_item_name(name)
  assert not is_row_present(name)

test_add_empty_required:
  click_add() → click_dialog_save()
  error = get_form_error()
  assert error != ""
```

**数据生命周期**:
- 创建数据用 `AUTO_三剂_` 前缀 + 时间戳 → 保证唯一性
- 取消测试用 `AUTO_CANCEL_` 前缀 + 时间戳 → 隔离
- 类变量 `CREATED_ITEM_NAME` 跨测试传递 → 创建→删除强依赖
- `cleanup_tracker` 兜底 → 保障 CI 环境无残留数据
- 依赖顺序: test_add_item_success → test_delete_created_item

## 6. ROI 分析

| 项目 | 评估值 | 说明 |
|---|---|---|
| 手工执行时间 (每次) | ~8 分钟 | 包括登录、导航、CRUD 全流程验证。 |
| 预估开发成本 | **16 小时** | 包含 PO 编写、JS Helper、测试脚本、数据清理。 |
| 预估维护成本 | **3 小时/月** | 定位器维护、数据清理逻辑维护、CRUD 流程变化调整。 |
| 执行频率 (假设) | 每日 2 次 (CI) | 在 CI/CD 中作为回归测试的一部分执行。 |
| 月度手工执行成本 | 8 分钟 x 2 次 x 30 天 = 480 分钟 = **8 小时** | 每月手工执行时间。 |
| 月度自动化维护成本 | **3 小时** | 维护成本合理。 |
| ROI 计算 (首月) | 手工成本(8h) - 开发成本(16h) - 维护成本(3h) = **-11h** | 首月为负收益，CRUD 页面自动化投入较高。 |
| ROI 计算 (次月及以后) | 手工成本(8h) - 维护成本(3h) = **5h** | 次月开始每月净节约 5 小时。 |

**结论**: 自动化投入合理。首月 ROI 为负是 CRUD 页面的常见情况，次月起稳定节约人工时间。对于 CI/CD 环境和高频回归测试，该投入是值得的。
