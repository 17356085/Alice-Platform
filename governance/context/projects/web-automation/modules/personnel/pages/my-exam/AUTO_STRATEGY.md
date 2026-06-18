# AUTO_STRATEGY: 我的考试 (my-exam)

> **模块**: personnel | **页面**: my-exam  
> **版本**: 1.0 | **日期**: 2026-06-18  
> **生成自**: PAGE_CONTEXT.md + TECH_ANALYSIS.md + 典型测试用例  

---

## 1. 自动化覆盖矩阵

| 用例编号 | 标题 | 优先级 | 是否自动化 | 理由 |
|---------|------|--------|----------|------|
| TC-001 | 页面正常加载 – 验证标题、表格、分页可见 | P0 | ✅ | 基础冒烟，所有元素定位器稳定（`data-testid` 或 `id`） |
| TC-002 | 搜索 – 按考试名称模糊搜索 | P0 | ✅ | 核心流程，`exam_name_input` 有 `placeholder` 可定位，风险低 |
| TC-003 | 筛选 – 按考试状态筛选（未开始/进行中/已完成） | P0 | ✅ | `exam_status_select` 使用 `el-select`，通过 `aria-label` / `placeholder` 可稳定定位 |
| TC-004 | 分页 – 切换每页条数（10/20/50）并验证显示 | P1 | ✅ | `el-pagination` 虽有 Element Plus 坑（EP-001），但可通过 `aria-label` 或 `class` 定位，添加 `data-testid` 后稳定 |
| TC-005 | 分页 – 翻页（点击下一页/上一页） | P1 | ✅ | 同上，建议额外添加 `data-testid` 提升稳定性 |
| TC-006 | 表格列显示 – 验证所有列名和内容 | P2 | ❌ | 列内容验证属于 UI 一致性，手工检查更快；且表格列名可能动态变化，维护成本高 |
| TC-007 | 开始考试 – 点击“未开始”行中的“开始考试”按钮 | P0 | ✅ | 核心业务路径，`row_cell_action_start` 使用 `@click` 绑定，可通过 `data-testid` 或文本定位 |
| TC-008 | 开始考试 – 确认弹窗（点击确定） | P0 | ✅ | 弹窗 `confirm_start_submit_btn` 有 `data-testid`，稳定 |
| TC-009 | 开始考试 – 取消弹窗 | P1 | ✅ | 取消按钮同样可使用测试 ID |
| TC-010 | 查看详情 – 点击“未开始”或“已完成”行的“查看”按钮 | P0 | ✅ | 操作按钮区分文本 `'查看'`，可稳定定位 |
| TC-011 | 查看详情弹窗 – 验证内容展示 | P1 | ✅ | 弹窗内字段如 `dialog_exam_detail_title` 等有 `data-testid` |
| TC-012 | 空数据状态 – 搜索结果为空时展示 `el-empty` | P1 | ✅ | 搜索后断言空状态元素可见，定位器稳定 |
| TC-013 | 加载状态 – 数据加载时表格显示 `v-loading` 骨架屏 | P2 | ❌ | 加载状态时间极短，人工观察即可；自动化捕获时机困难，维护成本高 |
| TC-014 | 重置搜索 – 点击重置按钮清空搜索条件 | P1 | ✅ | 重置后断言输入框和下拉框值恢复默认，操作简单 |

**风险标注**:  
- `el-pagination` 相关用例（TC-004、TC-005）定位器存在 **Element Plus 坑 EP-001**（分页按钮无唯一 ID），建议开发添加 `data-testid`，否则备用方案使用 `class` + `aria-label`。  
- 弹窗关闭按钮 `close_detail_btn` 在 TECH_ANALYSIS 中无明确 ID，建议统一添加 `data-testid`，否则使用 `.el-dialog__headerbtn` 通用类。

---

## 2. PageObject 拆分方案

```
page/
  my_exam/
    __init__.py
    my_exam_page.py          # 【主 Page】— 我的考试页面整体操作（搜索、表格、分页）
    my_exam_detail_dialog.py # 【独立 Page】— 考试详情弹窗（查看详情弹窗）
    start_exam_dialog.py     # 【独立 Page】— 确认开始考试弹窗
```

### 职责说明

| Page 类 | 职责 | 理由 |
|---------|------|------|
| `MyExamPage` | 封装搜索区、表格区、分页区的所有操作：输入搜索词、选择状态、点击搜索/重置、获取表格行、点击行内操作按钮、切换分页等 | 一个页面一个 Page 类，聚合该页面的全部主交互 |
| `MyExamDetailDialog` | 封装考试详情弹窗：获取弹窗标题、读取字段文本、关闭弹窗 | 弹窗独立逻辑，复用到其他页面时避免耦合；弹窗频繁出现，独立管理定位器更清晰 |
| `StartExamDialog` | 封装确认开始考试弹窗：点击确定、取消 | 同上面的理由，弹窗独立且包含业务断言 |

---

## 3. 公共组件复用分析

### 可复用 `BasePage` 已有方法

- `wait_for_element_visible` / `wait_for_element_clickable` — 用于所有元素等待
- `input_text` — 可封装到 `exam_name_input`
- `select_by_placeholder` — 如果 `BasePage` 已有基于 `placeholder` 选择下拉框的方法，可直接复用；否则需扩展
- `click_button` — 通用按钮点击
- `get_table_rows` — 如果 `BasePage` 有通用表格行获取方法（基于 `el-table` 的行选择器）
- `switch_page` — `el-pagination` 翻页通用方法（先定位到 `.el-pagination .btn-next` 等）

### 是否需要扩展 `ElementPlusHelper`

| 需要 | 原因 |
|------|------|
| **是** | 需要封装 `el-select` 的选择/清空方法（基于 `placeholder` 或 `aria-label` 定位下拉框，然后选择选项） |
| **是** | `el-table` 的行内按钮点击：根据行索引和按钮文本定位，复用度高 |
| **是** | `el-pagination` 的翻页和每页条数切换：封装 `select_page_size(value)`、`go_to_page(page_num)` 等方法 |
| **否** | `el-tag` 状态列读取：直接读取列文本 `get_cell_text(row_index, column_label)` 即可，无需单独封装 |

**建议**: 在 `ElementPlusHelper` 中新增 `select_el_option(locator, option_text)` 和 `pagination_go_to_page(locator, page)` 等通用方法。

---

## 4. 等待策略建议

### 页面特有的异步行为

| 触发动作 | 异步表现 | 等待策略 |
|---------|---------|---------|
| 页面首次加载 | `v-loading` 显示骨架屏 → 数据请求完成 → 表格渲染 | 等待 `el-table` 的 `loading` 属性为 false，或等待表格行出现（`table_exam_list .el-table__body` 下第一个 `tr`） |
| 搜索/筛选 | 重新请求接口 → 刷新表格 | 同上，建议使用 `wait_for_table_loading_finish()` 自定义方法 |
| 分页切换 | 重新请求数据 → 表格更新 | 同上 |
| 点击“开始考试” | 弹出确认弹窗（可能有短暂动画） | 等待弹窗 `dialog_start_exam_confirm` 可见（`displayed`） |
| 点击弹窗确定 | 可能请求接口 → 刷新表格 | 等待弹窗消失 + 表格加载完成 |
| 点击“查看详情” | 弹出详情弹窗 | 等待弹窗可见 |

### 建议的等待封装

在 `MyExamPage` 中添加：

```python
def wait_for_table_loading_finish(self, timeout=10):
    """等待表格加载完成（v-loading 消失且出现行）"""
    self.wait.until_not(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".el-table--loading"))
    )
    # 可选：进一步等待第一行数据渲染
    self.wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".el-table__body tr"))
    )
    return self
```

对于 `el-dialog` 弹窗，使用 `EC.visibility_of_element_located` 等待弹窗显示。

---

## 5. ROI 分析

### 预估数据

| 项 | 值 | 说明 |
|----|-----|------|
| **预估开发时间** | 24 小时 | 包括：PageObject 编写（8h）、测试脚本编写（10h）、定位器调试（4h）、CI 集成（2h） |
| **手工执行一次耗时** | 30 分钟 | 覆盖所有 P0 用例的完整回归 |
| **日均执行频率** | 2 次 | 主分支合并 + 每日定时 |
| **月执行次数** | 约 44 次（22工作日×2） |
| **月手工工时** | 22 小时 | 30min×44≈22h |
| **自动化维护成本** | 4 小时/月 | 定位器变更、UI 微调、分页坑处理 |
| **自动化执行时间** | 5 分钟 | 全自动（含等待） |
| **自动化月执行工时** | 3.7 小时 | 5min×44≈3.7h |

### ROI 计算

**自动化后每月节省工时** = 手工工时 - 自动化维护 - 自动化执行时间  
= 22h - 4h - 3.7h = **14.3 小时/月**

**投资回收期** = 开发时间 / 每月节省工时 = 24h / 14.3 ≈ **1.68 个月**

> 即约 1.7 个月回本，后续每月净节省 14.3 小时。对于 P0 优先的高频页面，自动化价值显著。

**结论**: 强烈推荐自动化 P0/P1 用例（TC-001 至 TC-011、TC-012、TC-014），ROI 为正。

---

## 6. 风险与缓解措施

| 风险 | 缓解措施 |
|------|---------|
| `el-pagination` 定位器不稳定（EP-001） | 与开发协商添加 `data-testid` 到分页按钮；备选方案使用 `aria-label` 定位 |
| 弹窗无唯一标识 | 推动开发统一添加 `data-testid` 到弹窗标题和按钮 |
| `el-tag` 颜色状态依赖 CSS 类 | 断言状态文本而非颜色样式，避免 UI 主题变更影响 |
| 搜索/筛选结果为空时表格行消失 | 优先判断 `el-empty` 组件的可见性，而非等待行 |
| 页面权限控制导致按钮不显示 | 测试前确保使用具有相应权限的账号登录（通过 fixture 控制） |

---

## 7. 下一步行动

- [ ] 与开发沟通在关键元素上添加 `data-testid`（参考 `PAGE_ELEMENT_POSITION.md` 中的定位器设计）
- [ ] 实现 `ElementPlusHelper` 中的 `pagination` 和 `select` 通用方法
- [ ] 编写 `MyExamPage`、`MyExamDetailDialog`、`StartExamDialog` 三个 Page 类
- [ ] 编写 P0 测试脚本（TC-001～TC-011）
- [ ] 集成到 CI 流水线，配置定时执行

// EOF