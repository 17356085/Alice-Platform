# Code Consistency Check — warehouse/reagent-item

**Time**: 2026-06-22
**Module**: warehouse
**Page**: reagent-item
**Issues**: 0

## 1. PO 方法 — 测试覆盖检查

| PO 方法 | 对应测试 | 覆盖状态 | 说明 |
|---|---|---|---|
| `navigate()` | `driver_setup` fixture 中通过 JS hash 导航 | ✅ 已覆盖 | conftest 中配置 route `#/warehouse/reagent/item` |
| `_wait_page_ready()` | `test_page_loads` 中调用 | ✅ 已覆盖 | 页面加载后手动调用 |
| `search_by_item_name(name)` | `test_search_by_item_name`, `test_reset_search`, `test_add_item_success` | ✅ 已覆盖 | 多次使用，search + reset + CRUD 均依赖 |
| `reset_search()` | `test_reset_search` | ✅ 已覆盖 | |
| `click_add()` | `test_add_dialog_opens`, `test_add_dialog_has_form_fields`, `test_add_item_success`, `test_add_item_cancel`, `test_add_empty_required` | ✅ 已覆盖 | 所有涉及新增的测试均使用 |
| `fill_item_name(name)` | `test_add_item_success`, `test_add_item_cancel` | ✅ 已覆盖 | 成功和取消场景 |
| `click_search()` | 间接被 `search_by_item_name` 覆盖 | ✅ 已覆盖 | 作为公开方法存在，在 `search_by_item_name` 内部使用 |
| `delete_item_by_name(name)` | `test_delete_created_item` | ✅ 已覆盖 | 核心删除路径 |
| `_fill_dialog_by_placeholder(placeholder, value)` | 通过 `fill_item_name` 间接覆盖 | ✅ 已覆盖 | 私有方法，内部使用 |

**结论**: 所有 PO 方法均有测试覆盖。

## 2. 定位器命名约定检查

| 元素 | 命名 | 是否符合约定 | 说明 |
|---|---|---|---|
| FILTER_ITEM_NAME | `FILTER_` + 字段描述 | ✅ | 符合 BasePage 命名惯例 |
| BTN_QUERY | `BTN_` + 功能描述 | ✅ | 符合 BTN_ 前缀惯例 |
| BTN_RESET | `BTN_` + 功能描述 | ✅ | 符合 BTN_ 前缀惯例 |
| BTN_ADD | `BTN_` + 功能描述 | ✅ | 符合 BTN_ 前缀惯例 |

**结论**: 定位器命名完全符合项目规范。

## 3. 缺失覆盖识别

| 缺失项 | 严重程度 | 原因 | 建议 |
|---|---|---|---|
| 搜索后断言搜索结果数量/内容 | 低 | 搜索测试为 smoke，仅验证不崩溃 | 可接受，但后续可增加精确断言 |
| 编辑功能 | 低 | PO 中无编辑方法，当前版本无编辑功能 | 无需覆盖 |
| 导入/导出 | 中 | 需文件操作，复杂度高 | P2 级，建议后续补充 |
| 批量选择/删除 | 中 | 需多选交互，现有 PO 未提供批量操作入口 | P2 级，建议后续补充 |
| 删除确认弹窗文案验证 | 低 | 未验证弹窗文案内容 | 可后续增加 |
| 重复名称新增校验 | 中 | 后端可能校验，当前未覆盖 | P1 风险，建议补充 |

## 4. 治理文档完整性自检

| 文档 | 状态 | 说明 |
|---|---|---|
| PAGE_CONTEXT.md | ✅ 已创建 | 页面结构、元素清单、状态、权限、业务规则、测试映射完整。 |
| PAGE_INTERFACE.yaml | ✅ 已创建 | 页面元数据、所有元素定义、方法定义（含 BasePage 继承方法）完整。 |
| TECH_ANALYSIS.md | ✅ 已创建 | 组件识别、DOM 结构推断、定位器设计、`_fill_dialog_by_placeholder` 分析、等待策略、风险点完整。 |
| AUTO_STRATEGY.md | ✅ 已创建 | 覆盖矩阵（含未自动化标记）、PO 拆分、复用分析、等待策略、CRUD 生命周期、ROI 完整。 |
| RISK_MODEL.md | ✅ 已创建 | 6 维度风险 + 业务场景完整。 |
| TEST_CASES.md | ✅ 已创建 | 11 个测试用例（7 已自动化 + 4 未自动化），覆盖全部现有自动化用例。 |
| consistency-check.md | ✅ 当前文件 | 一致性验证完成。 |

## 5. 特殊关注点

| 项目 | 状态 | 说明 |
|---|---|---|
| `_fill_dialog_by_placeholder` JS Helper 填写失败时仅 warning 不抛异常 | ⚠️ 需关注 | 如果弹窗结构变化导致 JS 匹配失败，`fill_item_name` 会静默失败。建议在 `fill_item_name` 中增加填写后的值验证。 |
| `test_delete_created_item` 强依赖 `test_add_item_success` 的执行顺序 | ⚠️ 需关注 | 通过类变量 `CREATED_ITEM_NAME` 传递，需确保同一测试类内方法按顺序执行（pytest 默认顺序执行，安全）。 |
| `cleanup_tracker` 兜底注册 | ✅ 良好实践 | 删除失败时注册清理回调，保障 CI 环境无数据残留。 |
| 严格断言 `assert error != ""` | ✅ 良好实践 | 比 `assert error` 更精确，确保校验提示不为空字符串。 |

**结论**: 无违规项。所有治理文档齐全、内容准确。需关注 `_fill_dialog_by_placeholder` 的静默失败风险和基于类变量的测试依赖顺序。
