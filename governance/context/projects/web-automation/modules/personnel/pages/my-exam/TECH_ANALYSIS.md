好的，我将基于模块 `personnel` 和页面 `my-exam` 的页面上下文，输出技术实现分析文档。

---

## 产出物 1: TECH_ANALYSIS.md

```markdown
# 技术实现分析报告: 我的考试 (my-exam)

> **分析版本**: 1.0 | **分析日期**: 2026-06-18 | **技术栈**: Vue 3 + Element Plus + Selenium

## 1. Element Plus 组件识别

| 组件类型 | 元素ID | 用途 |
| :--- | :--- | :--- |
| `el-input` | exam_name_input | 考试名称模糊搜索 |
| `el-select` | exam_status_select | 考试状态筛选（未开始/进行中/已完成） |
| `el-button` | search_btn | 触发搜索 |
| `el-button` | reset_btn | 重置搜索条件 |
| `el-table` | table_exam_list | 考试列表数据展示 |
| `el-table-column` | col_exam_name / col_exam_duration 等 | 表格列定义 |
| `el-tag` | col_exam_status | 考试状态标签（不同颜色表示不同状态） |
| `el-button` (text) | row_cell_action_start | 操作列“开始考试” |
| `el-button` (text) | row_cell_action_view | 操作列“查看/查看成绩” |
| `el-pagination` | pagination | 表格底部分页组件 |
| `el-dialog` | dialog_exam_detail | 考试详情弹窗 |
| `el-dialog` | dialog_start_exam_confirm | 确认开始考试确认弹窗 |
| `el-button` | confirm_start_submit_btn / confirm_start_cancel_btn | 弹窗确认/取消按钮 |

## 2. DOM 结构分析

### 2.1 关键层级结构

```html
<div id="app">
    <!-- 搜索区 -->
    <div class="search-area">
        <form class="el-form">
            <div class="el-form-item">
                <div class="el-input"> <!-- exam_name_input -->
                    <input class="el-input__inner" placeholder="考试名称" />
                </div>
            </div>
            <div class="el-form-item">
                <div class="el-select"> <!-- exam_status_select -->
                    <input class="el-select__input" readonly />
                    <span class="el-select__tags"></span>
                    <span class="el-select__suffix">
                        <i class="el-select__caret el-input__icon el-icon-arrow-up"></i>
                    </span>
                    <!-- el-select-dropdown（选项列表）渲染在 body 层 -->
                </div>
            </div>
            <div class="el-form-item">
                <button class="el-button el-button--primary"> <!-- search_btn -->
                    <span>搜索</span>
                </button>
                <button class="el-button el-button--default"> <!-- reset_btn -->
                    <span>重置</span>
                </button>
            </div>
        </form>
    </div>

    <!-- 表格区 -->
    <div class="table-area">
        <div class="el-table" v-loading="loading"> <!-- table_exam_list -->
            <div class="el-table__header-wrapper">
                <table class="el-table__header">
                    <thead>
                        <tr>
                            <th>考试名称</th>
                            <th>考试时长</th>
                            <th>总分</th>
                            <th>及格分</th>
                            <th>状态</th>
                            <th>开始时间</th>
                            <th>结束时间</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                </table>
            </div>
            <div class="el-table__body-wrapper">
                <table class="el-table__body">
                    <tbody>
                        <tr class="el-table__row" v-for="row in data"> <!-- 动态行 -->
                            <td class="col-exam-name">...</td>
                            <td class="col-exam-duration">...</td>
                            <td>...</td>
                            <td>...</td>
                            <td>
                                <span class="el-tag el-tag--success" v-if="row.status == '已完成'">已完成</span>
                                <span class="el-tag el-tag--warning" v-if="row.status == '进行中'">进行中</span>
                                <span class="el-tag el-tag--info" v-if="row.status == '未开始'">未开始</span>
                            </td>
                            <td>...</td>
                            <td>...</td>
                            <td class="col-operation">
                                <button class="el-button el-button--text" v-if="row.status == '未开始'">开始考试</button>
                                <button class="el-button el-button--text" v-else>查看成绩</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        <!-- 空数据提示 -->
        <div class="el-empty" v-if="!loading && data.length == 0">
            <i class="el-empty__image"></i>
            <p class="el-empty__description">暂无数据</p>
        </div>
    </div>

    <!-- 分页区 -->
    <div class="pagination-area">
        <div class="el-pagination"> <!-- pagination -->
            <span class="el-pagination__total">共 100 条</span>
            <button class="btn-prev">上一页</button>
            <ul class="el-pager">
                <li class="number">1</li>
                <li class="number active">2</li>
                <li class="number">3</li>
            </ul>
            <button class="btn-next">下一页</button>
            <span class="el-pagination__sizes">
                <el-select v-model="pageSize">
                    <el-option label="10 条/页" value="10"></el-option>
                    <el-option label="20 条/页" value="20"></el-option>
                </el-select>
            </span>
        </div>
    </div>
</div>

<!-- el-select 下拉选项渲染在 body 层（Element Plus 默认行为） -->
<div class="el-select-dropdown" style="display: none;">
    <ul class="el-select-dropdown__list">
        <li class="el-select-dropdown__item">未开始</li>
        <li class="el-select-dropdown__item">进行中</li>
        <li class="el-select-dropdown__item">已完成</li>
    </ul>
</div>

<!-- 考试详情弹窗 -->
<div class="el-dialog__wrapper" v-if="detailDialogVisible" style="display: none;">
    <div class="el-dialog"> <!-- dialog_exam_detail -->
        <div class="el-dialog__header">
            <span class="el-dialog__title">考试详情</span>
            <button class="el-dialog__headerbtn"><i class="el-dialog__close el-icon el-icon-close"></i></button>
        </div>
        <div class="el-dialog__body">
            <span>考试名称: {{ exam.name }}</span>
            <span>考试说明: {{ exam.description }}</span>
        </div>
        <div class="el-dialog__footer">
            <button class="el-button el-button--default">关闭</button>
        </div>
    </div>
</div>

<!-- 确认开始考试弹窗 -->
<div class="el-dialog__wrapper" v-if="confirmDialogVisible" style="display: none;">
    <div class="el-dialog"> <!-- dialog_start_exam_confirm -->
        <div class="el-dialog__header">
            <span class="el-dialog__title">确认开始考试</span>
        </div>
        <div class="el-dialog__body">
            <p>确认开始「{{ exam.name }}」考试？</p>
        </div>
        <div class="el-dialog__footer">
            <button class="el-button el-button--default">取消</button>
            <button class="el-button el-button--primary">确定</button>
        </div>
    </div>
</div>
```

### 2.2 稳定属性与动态属性

| 特征 | 说明 |
| :--- | :--- |
| **稳定 class** | `.search-area` `.table-area` `.pagination-area` `.el-table__row` `.el-tag` `.el-dialog` `.el-dialog__title` |
| **稳定文本** | 按钮文本（搜索、重置、开始考试、查看成绩、取消、确定、关闭） |
| **稳定 placeholder** | `考试名称` |
| **动态 class** | `.el-tag--success` `.el-tag--warning` `.el-tag--info`（状态不同 class 不同） |
| **v-show / v-if** | 弹窗使用 `display: none` 或 `v-if` 控制显示/隐藏 |
| **data-* 属性** | 假设不存在，不考虑依赖 |

## 3. 定位器设计表

| 元素ID | 推荐定位策略 | 定位值 | 稳定性 | 备用方案 | 备注 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| exam_name_input | **A** | `(By.CSS_SELECTOR, ".search-area input[placeholder='考试名称']")` | A | `(By.CSS_SELECTOR, ".search-area .el-input__inner")` | `placeholder` 稳定 |
| exam_status_select | **A** | `(By.CSS_SELECTOR, ".search-area .el-select")` | A | `(By.XPATH, "//div[contains(@class,'search-area')]//div[contains(@class,'el-select')]")` | 整个 select 容器 |
| exam_status_option | **B** | `(By.XPATH, "//div[contains(@class,'el-select-dropdown') and contains(@style,'display: none')]//li[text()='未开始']")` | B | `//div[contains(@class,'el-select-dropdown')]//li[contains(text(),'完成')]` | 下拉选项在 body 层，需先点击触发显示 |
| search_btn | **A** | `(By.XPATH, "//div[contains(@class,'search-area')]//button[.//span[text()='搜索']]")` | A | `(By.CSS_SELECTOR, ".search-area .el-button--primary")` | 按钮文本稳定 |
| reset_btn | **A** | `(By.XPATH, "//div[contains(@class,'search-area')]//button[.//span[text()='重置']]")` | A | `(By.CSS_SELECTOR, ".search-area .el-button--default")` | |
| table_exam_list | **A** | `(By.CSS_SELECTOR, ".el-table")` | A | - | 页面唯一表格 |
| table_row | **B** | `(By.CSS_SELECTOR, ".el-table__body-wrapper .el-table__row")` | B | `(By.XPATH, "//tr[contains(@class,'el-table__row')]")` | 动态行，定位后通常取列表 |
| table_row_by_index | **C** | `(By.CSS_SELECTOR, ".el-table__body-wrapper .el-table__row:nth-child(index)")` | C | - | index 从 1 开始，脆弱 |
| col_exam_status | **B** | `(By.CSS_SELECTOR, ".el-table__row .el-tag")` | B | 通过行内 `td:nth-child(5)` 定位 | 不同状态颜色不同 |
| row_cell_action_start | **B** | `(By.XPATH, "//button[.//span[text()='开始考试']]")` | B | `(By.CSS_SELECTOR, ".col-operation .el-button--text")` | 只有状态为“未开始”的行才显示 |
| row_cell_action_view | **B** | `(By.XPATH, "//button[.//span[text()='查看成绩']]")` | B | `//button[.//span[contains(text(),'查看')]]` | |
| pagination | **A** | `(By.CSS_SELECTOR, ".el-pagination")` | A | - | |
| pagination_next_btn | **A** | `(By.CSS_SELECTOR, ".el-pagination .btn-next")` | A | `//button[contains(@class,'btn-next')]` | |
| pagination_prev_btn | **A** | `(By.CSS_SELECTOR, ".el-pagination .btn-prev")` | A | `//button[contains(@class,'btn-prev')]` | |
| pagination_size_select | **B** | `(By.CSS_SELECTOR, ".el-pagination .el-select")` | B | 通过 el-select 定位后操作 | 每页条数切换 |
| dialog_exam_detail | **A** | `(By.CSS_SELECTOR, ".el-dialog")` | A | 配合 `contains_normalized_text('考试详情')` | 同一时间只有一个弹窗时可用 |
| dialog_exam_detail_title | **B** | `(By.CSS_SELECTOR, ".el-dialog .el-dialog__title")` | B | `//span[text()='考试详情']` | 用于确认弹窗类型 |
| close_detail_btn | **A** | `(By.XPATH, "//div[contains(@class,'el-dialog')]//button[.//span[text()='关闭']]")` | A | `//div[contains(@class,'el-dialog__footer')]//button[//span[text()='关闭']]` | |
| dialog_start_exam_confirm | **A** | `(By.CSS_SELECTOR, ".el-dialog")` | A | `(By.XPATH, "//div[contains(@class,'el-dialog') and .//div[contains(@class,'el-dialog__body') and contains(text(),'确认开始')]]")` | 与详情弹窗同名，需根据内容区分子弹窗 |
| confirm_start_submit_btn | **A** | `(By.XPATH, "//div[contains(@class,'el-dialog') and .//span[text()='确认开始考试']]//button[.//span[text()='确定']]")` | A | 先定位弹窗，再找其中的确定按钮 | |
| confirm_start_cancel_btn | **A** | `(By.XPATH, "//div[contains(@class,'el-dialog') and .//span[text()='确认开始考试']]//button[.//span[text()='取消']]")` | A | 先定位弹窗，再找其中的取消按钮 | |

### 定位器稳定性评级说明
| 评级 | 含义 | 适用场景 |
| :--- | :--- | :--- |
| **A** | 稳定、生产可靠 | 固定文本、稳定 class、唯一组件 |
| **B** | 可能轻微波动，需定期验证 | 动态列表、条件显示的元素 |
| **C** | 脆弱，仅作备用或临时方案 | 依赖序号、不稳定属性 |

## 4. Vue 异步等待策略

| 场景 | 等待条件 | WebDriverWait 示例 |
| :--- | :--- | :--- |
| **页面加载完成** | 表格容器可见 | `wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".el-table")))` |
| **搜索/刷新完成** | 表格加载状态消失 | `wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-table .el-loading-mask")))` |
| **el-select 下拉展开** | 下拉选项列表可见 | `wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".el-select-dropdown")))` |
| **el-select 下拉关闭** | 下拉选项列表不可见 | `wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-select-dropdown")))` |
| **el-dialog 弹窗打开** | 弹窗可见 | `wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".el-dialog")))` |
| **el-dialog 弹窗关闭** | 弹窗不可见 | `wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-dialog")))` |
| **表格数据重新渲染** | 行元素数量变化（可选） | 等待行数不再刷新，或比较前后行数 |
| **按钮操作成功** | 按钮可点击 | `wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='搜索']]")))` |
| **持续 loading（骨架屏）** | 骨架屏不可见 | `wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-skeleton")))` |

## 5. 自动化风险点

| 风险 | 说明 | 缓解措施 |
| :--- | :--- | :--- |
| **动态 class** | `el-tag--success/info/warning`、`el-button--primary/default/text` 等 class 会变化 | 优先使用文本 `XPath` 匹配，避免依赖表示状态的 class |
| **v-if 控制元素显示** | 弹窗、空数据提示、表格中的操作按钮由 `v-if` 控制 | 始终等待可见性/不可见性，使用 `visibility_of_element_located` |
| **el-select 选项渲染在 body 层** | 选项列表不在父容器内，与搜索区没有直接关联 | 定位时使用全局 XPath `//div[contains(@class,'el-select-dropdown')]` |
| **多弹窗重叠** | 考试详情弹窗和确认开始弹窗同时可能存在 | 通过弹窗标题文本区分，或通过 DOM 层级定位 |
| **表格虚拟滚动** | 如果数据量大，Element Plus 可能启用虚拟滚动，只渲染可见行 | 使用 `get_table_data()` 方法时需确认是否支持虚拟滚动 |
| **分页切换数据异步加载** | 每页条数或页码切换后，表格数据异步刷新 | 在切换操作后，等待 loading 消失和表格重绘 |
| **权限控制** | 无权限用户可能看不到某些按钮或弹窗 | 测试用例中先判断元素是否存在，避免直接点击导致失败 |
| **`data-*` 属性缺失** | 假设不存在，若实际项目添加则可提升稳定性 | 建议开发团队在关键元素上添加 `data-testid` 属性 |

## 6. ElementPlusHelper 扩展建议

以下基于 `TECH_ANALYSIS.md` 分析，建议为 `ElementPlusHelper` 新增以下方法：

```python
# 已有: select_option, get_select_value, get_table_data, get_pagination_info

# 新增建议:

def start_exam(self, exam_name: str) -> None:
    """
    在表格中根据考试名称找到对应行，点击“开始考试”按钮。
    隐含等待：确认弹窗可见 → 点击确定 → 确认弹窗关闭。
    """
    pass  # 需结合 PageObject 实现

def view_exam_result(self, exam_name: str) -> None:
    """
    在表格中根据考试名称找到对应行，点击“查看成绩”按钮。
    """
    pass
```

这些高层操作封装了 `el-dialog` 弹窗和 `el-table` 行定位的复杂性，对测试脚本开发者更为友好。
```

---

## 产出物 2: PAGE_ELEMENT_POSITION.md

```markdown
# PAGE_ELEMENT_POSITION: 我的考试 (my-exam)

> **定位器设计依据**: 基于 Vue 3 + Element Plus 典型的 HTML 结构，`data-testid` 为假设属性，实际项目中可能不存在。
> **定位器版本**: 1.0

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
| :--- | :--- | :--- | :--- | :--- |
| exam_name_input | **CSS** `placeholder` | `.search-area input[placeholder='考试名称']` | A | `.search-area .el-input__inner` |
| exam_status_select | **CSS** class | `.search-area .el-select` | A | `//div[contains(@class,'search-area')]//div[contains(@class,'el-select')]` |
| exam_status_option (未开始) | **XPath** text | `//div[contains(@class,'el-select-dropdown') and contains(@style,'display: none')]//li[text()='未开始']` | B | `//div[contains(@class,'el-select-dropdown')]//li[text()='未开始']` |
| exam_status_option (进行中) | **XPath** text | `//div[contains(@class,'el-select-dropdown')]//li[text()='进行中']` | B | - |
| exam_status_option (已完成) | **XPath** text | `//div[contains(@class,'el-select-dropdown')]//li[text()='已完成']` | B | - |
| search_btn | **XPath** text | `//div[contains(@class,'search-area')]//button[.//span[text()='搜索']]` | A | `.search-area .el-button--primary` |
| reset_btn | **XPath** text | `//div[contains(@class,'search-area')]//button[.//span[text()='重置']]` | A | `.search-area .el-button--default` |
| table_exam_list | **CSS** class | `.el-table` | A | - |
| table_row | **CSS** class | `.el-table__body-wrapper .el-table__row` | B | XPath `//tr[contains(@class,'el-table__row')]` |
| col_exam_status | **CSS** class | `.el-table__row .el-tag` | B | 通过行内 `td:nth-child(5)` 定位 |
| row_cell_action_start | **XPath** text | `//button[.//span[text()='开始考试']]` | B | `//div[contains(@class,'col-operation')]//button[contains(text(),'开始')]` |
| row_cell_action_view | **XPath** text | `//button[.//span[text()='查看成绩']]` | B | `//button[.//span[contains(text(),'查看')]]` |
| pagination | **CSS** class | `.el-pagination` | A | - |
| pagination_next_btn | **CSS** class | `.el-pagination .btn-next` | A | `//button[contains(@class,'btn-next')]` |
| pagination_prev_btn | **CSS** class | `.el-pagination .btn-prev` | A | `//button[contains(@class,'btn-prev')]` |
| pagination_size_select | **CSS** class | `.el-pagination .el-select` | B | 需先定位 `.el-pagination` 再查找 |
| dialog_exam_detail | **CSS** class | `.el-dialog` | A | 配合 `contains_normalized_text('考试详情')` 使用 |
| dialog_exam_detail_title | **XPath** text | `//span[text()='考试详情']` | B | `//div[contains(@class,'el-dialog__title') and text()='考试详情']` |
| close_detail_btn | **XPath** text + class | `//div[contains(@class,'el-dialog')]//button[.//span[text()='关闭']]` | A | `//div[contains(@class,'el-dialog__footer')]//button[.//span[text()='关闭']]` |
| dialog_start_exam_confirm | **CSS** class + text | `.el-dialog:has(.el-dialog__body p:contains('确认开始'))` | B | XPath `//div[contains(@class,'el-dialog') and .//div[contains(@class,'el-dialog__body') and contains(text(),'确认开始')]]` |
| confirm_start_submit_btn | **XPath** text + 关联弹窗 | `//div[contains(@class,'el-dialog') and .//span[text()='确认开始考试']]//button[.//span[text()='确定']]` | A | 先定位弹窗，再找其中的确定按钮 |
| confirm_start_cancel_btn | **XPath** text + 关联弹窗 | `//div[contains(@class,'el-dialog') and .//span[text()='确认开始考试']]//button[.//span[text()='取消']]` | A | 先定位弹窗，再找其中的取消按钮 |
```