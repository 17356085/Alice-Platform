# TECH_ANALYSIS — lab / water-compare

> Phase 2 | 页面: water-compare | 技术分析 | 2026-06-12  
> **分析依据**: Page Object 代码、测试脚本、PAGE_CONTEXT.md（未提供完整 HTML，基于 Element Plus 组件行为推断）

---

## 1. Element Plus 组件识别

| 组件类型 | 用途 | 出现数量 | 备注 |
|---------|------|---------|------|
| `el-input` (日期选择器) | 开始 / 结束日期输入 | 2 | 实际上由 `el-date-picker` 渲染，但 DOM 表现为 `input` |
| `el-select` | 取样位置选择 | 2 | 上下文提及，但当前 PO 代码未实现 |
| `el-button` | 查询 / 重置 | 2 | 主按钮风格 `el-button--primary`，重置可能为 `default` |
| `el-table` | 水质对比数据展示 | 1 | 自定义表格，与气体分析对比结构相同 |
| `el-loading` | 查询 / 重置后数据加载动画 | 1 | 由 `_wait_loading_gone` 处理 |
| `el-empty` (可能) | 无数据时的空状态占位 | 0~1 | 若查询结果为空，表格内显示空提示 |

---

## 2. DOM 结构分析 (推断)

```
<div class="page-container">
  <!-- 搜索表单 -->
  <div class="search-area">
    <div class="el-date-editor el-input">   <!-- 开始日期 -->
      <input placeholder="开始日期" />
    </div>
    <div class="el-date-editor el-input">   <!-- 结束日期 -->
      <input placeholder="结束日期" />
    </div>
    <div class="el-select">                  <!-- 取样位置1 -->
      <div class="el-select__wrapper">
        <input class="el-select__input" />
        <span class="el-select__selected-value">...</span>
      </div>
    </div>
    <div class="el-select">                  <!-- 取样位置2 -->
      ...同上...
    </div>
    <button class="el-button el-button--primary">查询</button>
    <button class="el-button el-button--default">重置</button>
  </div>

  <!-- 对比表格 -->
  <div class="el-table">
    <div class="el-table__header-wrapper">...</div>
    <div class="el-table__body-wrapper">
      <table><tbody>...</tbody></table>
    </div>
    <div class="el-table__empty-block" v-if="!data.length">暂无数据</div>
  </div>
</div>
```

- **稳定属性**: `placeholder` 文本可依赖（静态）；按钮文本可依赖；`el-select__wrapper` 结构固定。
- **动态属性**: Vue 生成的 `_uid`、`data-v-xxxxxxxx` 哈希 class；`el-select` 的下拉选项（`el-option`）动态渲染在 `body` 层；弹出层（`el-popper`）同样在 `body` 下。
- **v-if 控制**: `el-table__empty-block` 仅当无数据时渲染；加载动画 `el-loading` 通过 `v-loading` 控制，显示 `el-loading-mask` 遮罩。

---

## 3. 定位器设计表 (A/B/C 三级)

| 元素 | 推荐定位策略 | 定位值 | 稳定性 | 备注 |
|------|-------------|--------|--------|------|
| **开始日期输入框** | CSS A级（如有 data-testid） | `input[data-testid="start-date"]` | A | 未来建议添加 data-testid |
| | CSS B级（placeholder） | `input[placeholder*="开始日期"]` | B | 目前 PO 使用，暂可接受 |
| | XPath C级（基于 label 或同级别 text） | `//label[text()='开始日期']/following-sibling::div//input` | C | 易因结构变动失效 |
| **结束日期输入框** | CSS A级 | `input[data-testid="end-date"]` | A | 同上 |
| | CSS B级 | `input[placeholder*="结束日期"]` | B | 目前 PO 使用 |
| **取样位置1** | CSS B级（第一个 el-select） | `.search-area .el-select:first-of-type input` | B | 依赖顺序，若新增筛选字段失效 |
| | XPath B级（基于相邻 label） | `//label[text()='取样位置1']/following-sibling::div//input` | B | 需要 label 存在且稳定 |
| | XPath C级（位置索引） | `(//div[contains(@class,'el-select')])[1]//input` | C | 脆弱 |
| **取样位置2** | CSS B级（第二个 el-select） | `.search-area .el-select:nth-of-type(2) input` | B | 同上 |
| | XPath B级 | `//label[text()='取样位置2']/following-sibling::div//input` | B | |
| **查询按钮** | CSS A级 | `button[data-testid="btn-query"]` | A | 强烈建议添加 |
| | XPath A级（文本精确匹配） | `//button[.//span[text()='查询']]` | A | 目前 PO 通过 JS 点击，可改进 |
| | CSS B级（class+文本） | `button.el-button--primary:has( span:text("查询") )` | B | 低版本 Selenium 可能不支持 `:has/text` |
| **重置按钮** | CSS A级 | `button[data-testid="btn-reset"]` | A | |
| | XPath A级 | `//button[.//span[text()='重置']]` | A | |
| **对比表格** | CSS A级 | `table[data-testid="water-compare-table"]` | A | |
| | CSS B级 | `.el-table__body-wrapper table` | B | 当前 PO 通过 `table tbody tr` 获取行数 |
| | XPath C级 | `//div[contains(@class,'el-table')]//table` | C | |
| **加载遮罩** | CSS B级 | `.el-loading-mask` | B | 常用于等待 invisible |
| **空状态** | CSS B级 | `.el-table__empty-block` | B | 判断查询后表格无数据 |

> **评级说明**  
> A级：生产稳定，不随 UI 重构轻易变化（data-testid、唯一 ID、唯一文本）  
> B级：可能随布局或版本变动（placeholder、class 组合、顺序索引）  
> C级：脆弱（绝对位置、多层跟随、完全依赖顺序），仅作保底

---

## 4. 异步等待策略

| 场景 | 等待条件 | WebDriverWait 示例 | 当前 PO 实现 |
|------|---------|-------------------|-------------|
| **页面首次加载** | 表格容器出现 或 日期输入框可见 | `EC.presence_of_element_located(TABLE)` | `_wait_loading_gone` + `wait_vue_stable` |
| **点击查询后** | 加载遮罩消失（或表格行刷新） | `EC.invisibility_of_element_located(LOADING_MASK)` | 已实现 `_wait_loading_gone` |
| **点击重置后** | 日期输入框恢复默认值 + 加载完成 | 同上 + 等待输入框 value 为空 | 同查询，使用 `_wait_loading_gone` |
| **展开下拉选项** | 选项列表可见 | `EC.visibility_of_element_located(SELECT_DROPDOWN)` | 未实现（当前 PO 缺失 select 操作） |
| **选择下拉选项** | 选项列表不可见（已收起） | `EC.invisibility_of_element_located(SELECT_DROPDOWN)` | 未实现 |
| **输入日期后** | 日期面板关闭（如果使用 picker） | 需根据 picker 行为判断 | 当前直接 send_keys 绕过 picker |
| **弹窗相关** | 页面无弹窗，暂不适用 | — | — |

> **当前 PO 改进点**:  
> - `click_query` 使用 `_js_click_search_or_reset` 避免元素点击拦截，但应增加点击前等待元素可点击（`element_to_be_clickable`）作为容错。  
> - 建议统一使用 `wait_element_clickable` + `click_element`，而非 JS 强制点击（前者更接近用户操作，失败时更容易 debug）。  
> - 日期选择器 send_keys 前要确保 input 已启用且可交互（`is_enabled` 可忽略，但需 `presence_of_element_located` 后清除默认值）。

---

## 5. 自动化风险点

| 风险 | 说明 | 缓解建议 |
|------|------|---------|
| **动态 ID / Class** | Vue 生成的哈希 class（如 `el-input--suffix_12345`）无法直接定位 | 使用 stable attribute（placeholder, text, data-testid）避免依赖 class |
| **el-select 下拉渲染在 body 层** | 下拉选项 DOM 脱离当前 `.el-select` 容器，出现在 `<div id="el-popper-container-xxxx">` 中 | 不能使用嵌套关系定位下拉项，需全局搜索 `.el-select-dropdown__item` 并按文本过滤 |
| **日期选择器 UI 不统一** | 某些版本 `el-date-picker` 需要先点击输入框弹出 picker，send_keys 无效 | 优先使用 send_keys 一次输入完整格式；若失败则改为点击后选择日期 |
| **表格列数动态生成** | 对比表格可能根据对比指标动态列数（水质指标与气体不同） | 定位单元格时使用行索引+列索引，而非列名 |
| **查询按钮被遮挡** | 按钮可能被其他元素（如 sticky header）遮盖导致点击失败 | 使用 `scrollIntoView` + `element_to_be_clickable` 等待 |
| **无数据状态 vs 真实空状态** | 空状态 `.el-table__empty-block` 可能出现但表格实际有数据（过渡动画） | 等待表格 rows 可见后判断 |
| **权限控制导致元素缺失** | 如果用户无权限，部分输入框或按钮可能隐藏 | 在 Fixture 中保证角色权限符合测试用例 |
| **异步加载后 Vue 组件未稳定** | Element Plus 动画结束前组件行为异常（如表格高度闪烁） | 调用 `wait_vue_stable` 等待 DOM 稳定 |

---

## 6. 结论与建议

1. **定位器升级之路**: 当前 PO 主要使用 B 级定位器（placeholder、文本）。建议开发团队在关键元素上添加 `data-testid` 属性，提升至 A 级（尤其是查询/重置按钮、选择器、表格）。
2. **select 操作需补充**: 当前 PO 缺少取样位置选择方法。需实现 `select_location(index, text)` 公用方法，处理 el-select 点击展开 → 等待选项可见 → 按文本点击选项 → 等待选项关闭。
3. **等待策略统一**: 建议将所有阻塞操作（查询/重置）后的等待抽象为一行 `self.wait_load_complete()`，内部依次调用 `_wait_loading_gone` + `wait_vue_stable` + 表格可见断言。
4. **与 gas-compare 差异**: 仅指标和取样位置文本不同，建议抽公共基类或复用相同定位器模板，降低维护成本。

---

> ⚠️ **本分析基于代码和上下文推测，缺少实际页面 HTML 和截图验证。** 建议在执行自动化前通过开发者工具核对 DOM 结构，调整定位器。