```markdown
# DCS 模块 - Monitor 页面自动化策略

## 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
|----------|------|--------|------------|------|
| TC-MONITOR-001 | 页面正常加载（面包屑、标题、表格骨架） | P0 | ✅ | 基础冒烟，定位器稳定 |
| TC-MONITOR-002 | 输入设备名称关键词搜索 | P0 | ✅ | 核心功能，输入框稳定（`placeholder`） |
| TC-MONITOR-003 | 状态筛选框（下拉选择在线/离线） | P0 | ✅ | 选择器 + 选项，注意选项在body |
| TC-MONITOR-004 | 搜索后表格数据更新 | P0 | ✅ | 结合等待loading消失 |
| TC-MONITOR-005 | 点击“详情”按钮弹出弹窗 | P0 | ✅ | 弹窗稳定（`el-dialog`） |
| TC-MONITOR-006 | 分页切换页码 | P1 | ✅ | 页码按钮存在，但可能动态；降低维护优先级 |
| TC-MONITOR-007 | 空状态（无匹配数据）显示 | P1 | ✅ | 需要判断无数据文案 |
| TC-MONITOR-008 | 重置按钮清空搜索条件及表格 | P1 | ✅ | 重置逻辑稳定 |
| TC-MONITOR-009 | 时间范围筛选（日期选择器） | P1 | ✅ | 组件稳定，但需处理日期选择器渲染 |
| TC-MONITOR-010 | 导出按钮导出当前列表（如存在） | P2 | ❌ | 文件下载路径不稳定，浏览器弹窗差异大 |
| TC-MONITOR-011 | 浏览器刷新后保留搜索条件 | P2 | ❌ | 需验证前端URL参数，维护成本高 |
| TC-MONITOR-012 | 表格列排序（点击表头） | P2 | ❌ | 排序触发时机可能与加载冲突，且验证复杂 |

## 2. PageObject 拆分方案

```
pages/
  monitor/
    __init__.py
    monitor_page.py          # MonitorPage：搜索栏、表格、分页主体操作
    alarm_detail_dialog.py   # AlarmDetailDialog：详情弹窗（独立类）
    status_filter.py         # StatusFilter（可选，若下拉框复用可抽取为公共组件）
```

### 职责说明

- **MonitorPage**  
  - 搜索区域：`search_input`, `status_select`, `date_range_picker`, `search_btn`, `reset_btn`  
  - 表格区域：`table_rows`, `get_row_by_device_name()`, `click_detail_button()`  
  - 分页：`total_count`, `click_page(number)`, `current_page`  

- **AlarmDetailDialog**  
  - 弹窗标题、内容、关闭按钮、`wait_until_visible()` / `wait_until_hidden()`  
  - 读取弹窗内字段值（如设备详情）  

- **StatusFilter**  
  - 封装 `el-select` 选项选择逻辑，可被其他下拉类似组件复用  

## 3. 公共组件复用分析

| 组件 | 复用方式 | 说明 |
|------|----------|------|
| `BasePage` | ✅ 直接继承 | 已包含 `wait_element`, `wait_loading_disappear`, `screenshot` 等 |
| `ElementPlusHelper` | ✅ 扩展 | 新增 `select_dropdown_option(placeholder, option_text)` 方法，处理 `el-select` 选项在 body 下的问题 |
| `CleanupTracker` | ✅ 无需改动 | 监控页面没有创建数据，无需注册清理；若后续有“添加设备”则需注册 |
| `Page.wait_for_network_idle` | ✅ 复用 | 搜索后建议等待网络空闲 |

### BasePage 不足与扩展计划

- 缺少 `date_picker_select_range(start, end)` — 需新增  
- 缺少 `table_get_cell_text(row_index, column_label)` — 可新增通用方法  

## 4. 等待策略建议

### 页面特有异步行为

1. **搜索/筛选后**：`el-table` 的 `v-loading` 遮罩出现 → 等待 `.el-loading-mask` 消失（BasePage 已有 `wait_loading_disappear`）  
2. **弹窗打开**：等待 `.el-dialog` 出现且 `visibility:visible`（建议用 `wait_for_visibility`）  
3. **日期选择器展开**：`el-picker-panel` 渲染在 body 下，需等待 `body .el-picker-panel` 可见  
4. **下拉选项展开**：等待 `body .el-select-dropdown` 出现（ElementPlusHelper 封装）

### 建议封装

```python
# monitor_page.py
def search_with_wait(self, keyword):
    self.send_keys(self.search_input, keyword)
    self.click(self.search_btn)
    self.wait_loading_disappear()  # 继承 BasePage
    self.wait_for_network_idle(timeout=10)
```

## 5. ROI 分析

| 项目 | 估算 |
|------|------|
| 预估开发时间（含用例调试） | 8 小时（1 人天） |
| 预估维护成本 | 2 小时 / 月（关键组件变更、UI小改动） |
| 手工执行频率 | 每个版本（2周）执行 1 次，每月约 2 次 |
| 手工执行时间（全量12个用例） | 15 分钟 / 次 → 30 分钟 / 月 |
| 自动化执行时间 | 3 分钟 / 次 → 6 分钟 / 月 |
| **ROI 计算（按 6 个月）** | 手工总耗时：30 * 6 = 180 分钟 = 3 小时<br>自动化投资：8 + 2*6 = 20 小时<br>净收益：3 - 20 = -17 小时（前6个月亏损）<br>但是从第7个月起，每月手工3小时 vs 维护2小时，开始回本。<br>预计 12 个月内回本，适合长期回归 |

**结论**：建议对 P0 和 P1 用例自动化，P2 暂缓。定位器不稳定风险点（状态列文本、弹窗内容）已在策略中标注，应降低断言精确度或使用模糊匹配降低维护成本。

---

*生成日期：2025-04-15*  
*基于通用 DCS Monitor 页面结构，具体实现需依据实际 DOM 微调。*  
```