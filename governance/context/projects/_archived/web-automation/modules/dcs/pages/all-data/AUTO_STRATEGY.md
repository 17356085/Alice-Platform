# AUTO_STRATEGY.md

## 模块：dcs，页面：all-data (所有数据列表页面)

---

### 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
|---------|------|--------|----------|------|
| TC-DCS-ALL-001 | 页面正常加载（表格+分页展示） | P0 | ✅ | 基础冒烟，定位器稳定（el-table__body / el-pagination） |
| TC-DCS-ALL-002 | 按名称搜索（关键词+回车/点击搜索） | P0 | ✅ | 高频操作，搜索输入框定位器 A 级 |
| TC-DCS-ALL-003 | 按状态下拉筛选 | P0 | ✅ | 下拉框稳定（el-select），需注意 popper 层定位 |
| TC-DCS-ALL-004 | 组合搜索（名称+状态+时间范围） | P1 | ✅ | 中等频次，跟随 P0 自动化 |
| TC-DCS-ALL-005 | 搜索后清空条件并重置 | P1 | ✅ | 重置按钮逻辑较简单，可附在 TC-002/003 中 |
| TC-DCS-ALL-006 | 表格分页（首页/上一页/下一页/末页/精确页码） | P0 | ✅ | 分页器定位 A 级，核心功能 |
| TC-DCS-ALL-007 | 新增数据（表单填写+提交） | P0 | ✅ | 弹窗定位 A 级，但需配合 cleanup 清理数据 |
| TC-DCS-ALL-008 | 编辑已有数据 | P0 | ✅ | 需先定位行，再点击编辑按钮，弹窗表单修改后保存 |
| TC-DCS-ALL-009 | 删除单条数据（确认弹窗） | P0 | ✅ | 确认弹窗定位 A 级，删除后需验证表格刷新 |
| TC-DCS-ALL-010 | 批量删除（选择多行） | P1 | ↔️ 部分自动化 | 批量选择涉及 checkbox 定位（动态 id），暂标记 B 级风险，可先自动化单行删除 |
| TC-DCS-ALL-011 | 查看详情（弹窗只读） | P1 | ✅ | 弹窗定位同上，读取字段即可 |
| TC-DCS-ALL-012 | 表格空数据状态展示 | P2 | ❌ | 一次性场景，需构造空数据（cleanup 复杂），手工验证更高效 |
| TC-DCS-ALL-013 | 长时间搜索（等待 loading 后数据刷新） | P1 | ✅ | 结合 wait_loading_disappear()，已有 BasePage 支持 |
| TC-DCS-ALL-014 | 搜索无结果（显示“暂无数据”） | P1 | ✅ | 可复用 TC-002 搜索不存在的名称 |
| TC-DCS-ALL-015 | 新增/编辑表单校验（必填项、格式） | P2 | ✅ | 定位弹窗内校验提示，但需确保校验规则稳定（A 级） |
| TC-DCS-ALL-016 | 页面权限控制（无权限按钮不显示） | P1 | ❌ | 依赖权限系统，环境不稳定，建议手工或 E2E 账号切换测试 |
| TC-DCS-ALL-017 | 大量数据滚动+分页性能（>1000条） | P2 | ❌ | 一次性性能基准，手工执行或放到性能测试 |
| TC-DCS-ALL-018 | 导出数据（若存在导出按钮） | P0 | ✅ | 若页面上有导出按钮，下载行为自动化（注意清理下载文件） |

> **风险标注**  
> - TC-DCS-ALL-010 批量删除：checkbox 定位若使用 `el-checkbox__input` 可能稳定，但需进一步观察实际 DOM（动态 id 风险高），建议先排除或降级为手动。  
> - TC-DCS-ALL-016 权限：定位器可能因元素不出现而超时，需单独处理。  
> - TC-DCS-ALL-018 导出：需要等待文件下载完成，不同浏览器行为不同，建议用 Chrome 偏好设置无弹窗下载。

### 2. PageObject 拆分方案

#### 页面类设计

```
pages/
├── dcs/
│   ├── all_data/
│   │   ├── __init__.py
│   │   ├── all_data_page.py          # 主页面操作（搜索、表格、分页）
│   │   ├── all_data_dialog.py        # 新增/编辑/详情弹窗（独立）
│   │   └── all_data_components.py    # 可选：拆分搜索区域（若复用频繁）
│   └── ...
```

**具体职责**：

| 类名 | 职责 | 说明 |
|------|------|------|
| `AllDataPage` | 搜索区域、表格行操作、分页器操作、按钮点击（新增/导出/删除） | 继承 BasePage，注入 ElementPlusHelper |
| `AllDataDialog` | 弹窗内表单填写、提交、取消，验证字段 | 单独类，避免与页面方法混合 |

**不独立封装的组件**：  
- 搜索区域直接放在 `AllDataPage` 中，因为该页面搜索条件固定；若将来需多层复用才考虑拆分 `SearchAreaComponent`。

#### 方法清单（草案）

```python
# AllDataPage
class AllDataPage(BasePage):
    def search_by_name(self, name: str) -> None
    def search_by_status(self, status: str) -> None
    def click_search(self) -> None
    def click_reset(self) -> None
    def get_table_row_count(self) -> int
    def get_cell_text(self, row_index: int, column_index: int) -> str
    def click_edit_on_row(self, row_index: int) -> AllDataDialog
    def click_detail_on_row(self, row_index: int) -> AllDataDialog
    def click_delete_on_row(self, row_index: int) -> AllDataDialog
    def click_add_button(self) -> AllDataDialog
    def go_to_page(self, page_num: int) -> None

# AllDataDialog
class AllDataDialog(BasePage):
    def fill_form(self, data: dict) -> None
    def submit(self) -> None
    def cancel(self) -> None
    def is_visible(self) -> bool
    def get_form_error(self, field: str) -> str
```

### 3. 公共组件复用分析

| 操作 | 基础方法 | 来源 | 说明 |
|------|---------|------|------|
| 等待表格加载 | `wait_table_loaded()` | BasePage | 直接使用 |
| 等待 loading 消失 | `wait_loading_disappear()` | BasePage | 直接使用 |
| 等待弹窗可见 | `wait_dialog_visible()` | ElementPlusHelper | 已封装，传入 dialog CSS |
| 获取表格行数 | `get_table_rows()` | ElementPlusHelper | 返回元素列表 |
| 下拉选择 | `select_from_el_dropdown()` | ElementPlusHelper | 封装了 body 层点击 |
| 弹窗内输入框操作 | `type_input_by_placeholder()` | ElementPlusHelper | placeholder 定位 |
| 清除按钮 | `click_reset_button()` | BasePage | 若统一样式可直接复用 |
| 数据清除注册 | `get_cleanup_tracker()` | base.cleanup_tracker | 每个新增/编辑用例必须使用 |

**需扩展的部分**：  
- 若表格操作按钮（编辑/删除/详情）的 CSS 选择器一致，可在 `ElementPlusHelper` 中加入 `click_action_on_row(row, action_text)` 通用方法。
- 弹窗验证错误提示（`el-form-item__error`）目前无封装，可在 `ElementPlusHelper` 中增加 `get_form_field_error(field_label)`。

### 4. 等待策略建议

| 场景 | 等待条件 | 使用 BasePage 方法 |
|------|---------|-------------------|
| 页面数据初始加载 | 表格 `tbody tr` 数量 > 0（或等待首次 loading 消失） | `wait_table_loaded()` |
| 搜索后刷新 | `el-loading-mask` 消失（loading 遮罩） | `wait_loading_disappear()` |
| 分页切换后 | 表格重新渲染（可等待分页器高亮页码变化，或再次等待 loading） | 同上 |
| 弹窗打开 | `.el-dialog__wrapper` 出现且 visible | `wait_dialog_visible()` |
| 弹窗关闭 | `.el-dialog__wrapper` 消失 | `wait.until(EC.invisibility_of_element())` |
| 下拉选项弹出 | `body > .el-popper` 内 `el-select-dropdown__item` 可见 | 使用 `select_from_el_dropdown()` 已封装等待 |
| 新增/编辑提交后 | 弹窗消失 + 表格刷新 | `wait_dialog_close()` + `wait_loading_disappear()` |
| 删除后确认 | 同上 | 同上 |

**特殊等待**：  
- 当搜索无结果时，表格显示“暂无数据”占位，`wait_table_loaded()` 可能失败。建议在搜索后判断：若有表格行则走正常流程，否则判断“暂无数据”元素。可封装 `wait_search_completed(with_data=True/False)` 方法。

### 5. ROI 分析

#### 假设数据
- 手工执行一轮全部 P0+P1 用例（约 15 条）平均耗时：**30 分钟**
- 该页面回归集执行频率：每天 2 次（持续集成） + 每周 1 次全量（50周/年）
- 动态成本：每次手工需切换账号、清理数据、记录结果，自动化约 5 分钟

| 指标 | 数值 |
|------|------|
| 手工执行时间 (每次) | 30 min |
| 自动化执行时间 (每次) | 5 min |
| 每日执行次数（CI） | 2 次 |
| 每周手工全量次数 | 1 次 |
| 年度手动总耗时 | 30×2×365 + 30×52 ≈ 21,900+1,560 ≈ 23,460 min ≈ 391 h |
| 年度自动化总耗时 | 5×2×365 + 5×52 ≈ 3,650+260 ≈ 3,910 min ≈ 65.2 h |
| 年度手工投入 | 391 h |
| 年度自动化投入 | 65.2 h |
| **年度节省工时** | **325.8 h** |

#### 开发与维护成本
| 项目 | 估算 |
|------|------|
| P0+P1 用例自动化开发 (包含 PageObject + 用例脚本 + 数据清理) | 60 h (约 8 人天) |
| 年度维护成本（定位器微调 + 新功能适配） | 30 h / 年 |
| 脚本初始投入 | 60 h |
| 年度 ROI (第一年) | 节省(325.8 h) - 开发维护(60+30) = **+235.8 h** |
| 年度 ROI (第二年及以后) | 325.8 - 30 = **+295.8 h** |

#### 非量化收益
- 发现缺陷时间提前（CI 触发，平均提前 4 h）
- 手工测试人员释放，专注更复杂场景
- 回归覆盖稳定，减少漏测风险

---

### 6. 风险与缓解措施

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 定位器因前端重构变差 | 中 | 维护成本上升 | 遵循 A/B/C 分级，定期（每个迭代）执行定位器健康巡检脚本 |
| 环境不稳定导致用例失败 | 高 | 误报增加 | 增加幂等设计 + 重试机制（最多 3 次），失败后保留截图和日志 |
| 测试数据残留 | 低 | 影响其他用例 | 强制使用 `CleanupTracker`，teardown 中清理，并设定全局清理定时任务 |
| 权限控制的元素动态显示 | 低 | 部分用例执行失败 | 使用 `is_element_present(by, locator, timeout=2)` 判断，跳过或标记 skip |

---

### 7. 后续实施计划

1. **阶段一（第1-2天）**：创建 `AllDataPage` 和 `AllDataDialog` 类，提取与 BasePage 的差异，完成 P0 用例（TC-001 ~ TC-006, TC-009）。
2. **阶段二（第3-4天）**：实现新增、编辑、删除自动化（TC-007, TC-008, TC-009），集成 CleanupTracker。
3. **阶段三（第5-6天）**：补充 P1 用例（组合搜索、详情、无结果等），编写公共组件扩展（如下拉等待）。
4. **阶段四（第7-8天）**：执行冒烟测试，修复定位器不稳定点，集成 CI（Jenkins Job）。
5. **持续**：每个迭代更新定位器表和等待策略，运行健康巡检。

---

> **文档版本**：v1.0  
> **创建日期**：2025-03-30  
> **维护者**：自动化架构师  
> **状态**：待评审