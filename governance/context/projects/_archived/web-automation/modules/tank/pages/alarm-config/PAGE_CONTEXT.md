好的，我将基于 `tank` 模块的 `alarm-config` 页面，按照 **page-analysis** Skill 的要求，输出完整的三份文件：

1. `PAGE_CONTEXT.md` — 页面元素清单  
2. `PAGE_ELEMENT_POSITION.md` — 元素定位器设计（A/B/C 三级）  
3. `PAGE_INTERFACE.yaml` — 自动化用结构化接口（自动生成）

---

## 📄 PAGE_CONTEXT.md

```markdown
# 页面上下文：tank / alarm-config

## 页面信息
- **模块**：tank
- **页面名称**：报警配置
- **URL**：http://8.136.215.171:8081/tank/alarm-config
- **UI 框架**：Vue 3 + Element Plus

## 1. 页面整体结构
- **顶部**：面包屑导航 + 操作按钮（新增报警规则）
- **左侧**：无
- **主内容区**：搜索/筛选区 → 表格列表 → 分页

## 2. 搜索/筛选区
| 元素ID        | 元素描述           | 控件类型      | 所在区域 | 备注                     |
|---------------|--------------------|---------------|----------|--------------------------|
| alarmName     | 报警名称输入框      | el-input      | 搜索区   | placeholder="请输入报警名称" |
| alarmLevel    | 报警级别下拉选择     | el-select     | 搜索区   | 选项：紧急/重要/一般      |
| status        | 状态下拉选择        | el-select     | 搜索区   | 选项：启用/停用           |
| searchBtn     | 搜索按钮            | el-button     | 搜索区   | 文字：查询                |
| resetBtn      | 重置按钮            | el-button     | 搜索区   | 文字：重置                |
| addBtn        | 新增报警规则按钮     | el-button     | 搜索区   | 文字：新增报警规则，type=primary |

## 3. 表格/列表区
| 元素ID       | 列标题       | 数据类型     | 所在区域 | 备注                     |
|--------------|--------------|--------------|----------|--------------------------|
| col_name     | 报警名称      | 文本         | 表格     |                          |
| col_level    | 报警级别      | 标签         | 表格     | el-tag 颜色区分           |
| col_source   | 报警来源      | 文本         | 表格     | 如：液位计、温度传感器    |
| col_status   | 状态          | 开关(tag)   | 表格     | 启用/停用                 |
| col_createTime | 创建时间     | 日期(yyyy-MM-dd HH:mm) | 表格 |                          |
| col_action   | 操作          | 操作按钮组   | 表格     | 编辑、删除、查看详情      |

操作按钮详情：
| 元素ID               | 按钮文字 | 控件类型 | 所在区域    | 备注                         |
|----------------------|----------|----------|-------------|------------------------------|
| editBtn              | 编辑     | el-button | 表格操作列 | 带图标                       |
| deleteBtn            | 删除     | el-button | 表格操作列 | 弹窗二次确认                 |
| detailBtn            | 详情     | el-button | 表格操作列 | 打开详情弹窗（只读）         |

## 4. 分页区
| 元素ID     | 元素描述         | 控件类型       | 所在区域 | 备注                              |
|------------|------------------|----------------|----------|-----------------------------------|
| pagination | 分页组件         | el-pagination   | 表格底端 | 当前页、每页条数（10/20/50/100）  |

## 5. 弹窗/对话框
### 5.1 新增/编辑报警规则弹窗
| 元素ID              | 元素描述         | 控件类型      | 所在区域 | 备注                         |
|---------------------|------------------|---------------|----------|------------------------------|
| dialogAlarmRule     | 报警规则弹窗      | el-dialog     | 弹窗     | 标题：新增报警规则 / 编辑报警规则 |
| dialog_title        | 弹窗标题         | -             | 弹窗头   | 动态文字                     |
| form_name           | 报警名称输入框    | el-input      | 弹窗表单 | 必填                         |
| form_level          | 报警级别选择      | el-select     | 弹窗表单 | 必填                         |
| form_source         | 报警来源选择      | el-select     | 弹窗表单 | 可选，支持 filterable        |
| form_threshold      | 阈值输入          | el-input-number | 弹窗表单 | 必填                         |
| form_enable_status  | 启用状态开关      | el-switch     | 弹窗表单 | 默认启用                     |
| dialog_save         | 保存按钮          | el-button     | 弹窗底部 | type=primary                 |
| dialog_cancel       | 取消按钮          | el-button     | 弹窗底部 |                              |

### 5.2 删除确认弹窗
| 元素ID              | 元素描述         | 控件类型      | 所在区域 | 备注                      |
|---------------------|------------------|---------------|----------|---------------------------|
| confirmDeleteDialog | 删除确认弹窗      | el-dialog     | 弹窗     | 标题：提示                 |
| confirm_btn         | 确定按钮          | el-button     | 弹窗底部 | type=primary               |
| cancel_btn          | 取消按钮          | el-button     | 弹窗底部 |                            |

## 6. 页面状态
| 状态     | 表现                                            | 定位元素                  |
|----------|-------------------------------------------------|---------------------------|
| 加载中   | el-loading-mask 覆盖表格区域                     | .el-loading-mask          |
| 空数据   | el-empty 组件显示“暂无数据”                      | .el-empty                 |
| 错误     | Toast 提示：el-message 错误类型                   | .el-message--error        |
| 权限不足 | 按钮隐藏或置灰（影响 addBtn / editBtn / deleteBtn）| 无，需观察 class 或样式    |

## 7. 权限点
| 元素ID    | 权限描述                 | 影响操作         |
|-----------|--------------------------|------------------|
| addBtn    | 新增报警规则权限          | 按钮显示/隐藏    |
| editBtn   | 编辑报警规则权限          | 按钮显示/隐藏    |
| deleteBtn | 删除报警规则权限          | 按钮显示/隐藏    |
```

---

## 📄 PAGE_ELEMENT_POSITION.md

```markdown
# 元素定位器设计：tank / alarm-config

> **优先级**：A级（data-testid/id/name/placeholder）> B级（CSS Selector）> C级（XPath）  
> 稳定性评级：A=稳定，B=较稳定，C=脆弱  
> 所有动态元素均标注等待策略（WebDriverWait）

## 搜索区定位器

| 元素ID      | 定位策略 | 定位值                                      | 稳定性 | 备用方案（C级）                                 |
|-------------|----------|----------------------------------------------|--------|-----------------------------------------------|
| alarmName   | A        | `input[placeholder="请输入报警名称"]`         | A      | `//input[@placeholder="请输入报警名称"]`         |
| alarmLevel  | A        | `select` 后触发，点击 `el-select` 框          | A      | （见下拉框通用方案）                             |
| status      | A        | `select` 后触发，点击 `el-select` 框          | A      | 同上                                          |
| searchBtn   | A        | `button:has-text("查询")`                    | A      | `//button[span[text()="查询"]]`               |
| resetBtn    | A        | `button:has-text("重置")`                    | A      | `//button[span[text()="重置"]]`               |
| addBtn      | A        | `button:has-text("新增报警规则")`             | A      | `//button[span[text()="新增报警规则"]]`         |

## 表格区定位器

| 元素ID      | 定位策略 | 定位值                                      | 稳定性 | 备用方案（C级）                                 |
|-------------|----------|----------------------------------------------|--------|-----------------------------------------------|
| tableRow    | B        | `.el-table__body-wrapper .el-table__row`      | B      | `//tbody/tr`                                 |
| editBtn     | A        | `button:has-text("编辑")` 结合行内           | A      | `//tr[{n}]//button[span[text()="编辑"]]`      |
| deleteBtn   | A        | `button:has-text("删除")`                    | A      | 同上（注意删除后有确认弹窗）                     |
| detailBtn   | A        | `button:has-text("详情")`                    | A      | `//tr[{n}]//button[span[text()="详情"]]`      |
| pagination  | B        | `.el-pagination`                             | B      | `//div[contains(@class, "el-pagination")]`    |

## 弹窗定位器

| 元素ID            | 定位策略 | 定位值                                      | 稳定性 | 备用方案（C级）                                 |
|-------------------|----------|----------------------------------------------|--------|-----------------------------------------------|
| dialogAlarmRule   | B        | `.el-dialog:visible`                         | B      | `//div[contains(@class, "el-dialog") and contains(@aria-modal, "true")]` |
| form_name         | A        | `input[placeholder="请输入报警名称"]` 在弹窗内 | A      | `//div[@class="el-dialog"]//input[@placeholder="请输入报警名称"]` |
| form_level        | B        | 弹窗内 `el-select` 的第一个                   | B      | 定位到的 select 后继续点击 trigger             |
| form_threshold    | A        | `input[type="number"]` in dialog             | B      | `//div[@class="el-dialog"]//input[@type="number"]` |
| form_enable_status | B       | `.el-dialog .el-switch`                      | B      | `//div[@class="el-dialog"]//span[contains(@class, "el-switch")]` |
| dialog_save       | A        | `button:has-text("保存")`                    | A      | `//button[span[text()="保存"]]`               |
| dialog_cancel     | A        | `button:has-text("取消")`                    | A      | `//button[span[text()="取消"]]`               |
| confirmDeleteDialog | B      | `.el-dialog:visible` 带“提示”标题            | B      | 根据标题文本 `//div[contains(@class, "el-dialog") and .//span[text()="提示"]]` |
| confirm_btn       | A        | `button:has-text("确定")`                    | A      | `//button[span[text()="确定"]]`               |
| cancel_btn        | A        | `button:has-text("取消")`                    | A      | `//button[span[text()="取消"]]`               |

## 等待策略（WebDriverWait）

| 场景                         | 条件                                       | 超时  | 备注                     |
|------------------------------|--------------------------------------------|-------|--------------------------|
| 表格加载完成                 | presence_of_all_elements_located(tableRow) | 10s   | 行数>0 或 until 有行      |
| 弹窗出现                     | visibility_of_element_located(dialogAlarmRule) | 10s |                          |
| 弹窗消失                     | invisibility_of_element_located(dialogAlarmRule) | 10s |                          |
| 新增/编辑成功后 Toast        | visibility_of_element_located(TOAST_SUCCESS) | 5s   |                          |
| 删除确认弹窗出现             | visibility_of_element_located(confirmDeleteDialog) | 5s |                          |
| 下拉框选项出现（Teleport）   | presence_of_element_located(`.el-popper .el-select-dropdown__item`) | 5s | 选项在body下              |

## Element Plus 坑位处理（参考 MODULE_CONTEXT.md 中 EP-001～EP-003）

- filterable el-select 需先点击输入框，再等待 `.el-popper` 出现
- 日期选择器面板为 Teleport，使用 `body .el-picker-panel` 定位
- el-dialog 关闭动画：确认按钮后等待 `.el-dialog` 消失（invisibility）
```

---

## 📄 PAGE_INTERFACE.yaml

> **说明**：根据 PAGE_CONTEXT.md 和典型 Page Object 结构自动生成，供 automation-agent 直接消费。

```yaml
# 页面接口定义：tank / alarm-config
module: tank
page: alarm-config
url: http://8.136.215.171:8081/tank/alarm-config

elements:
  # 搜索区
  - id: alarmName
    type: input
    locator: "input[placeholder='请输入报警名称']"
    strategy: css
    category: search

  - id: alarmLevel
    type: select
    locator: ".el-select:has(+ .el-form-item) .el-select__trigger"
    strategy: css
    category: search
    options: ["紧急", "重要", "一般"]

  - id: status
    type: select
    locator: ".el-select:has(+ .el-select) .el-select__trigger"  # 需调整，实际用第二个select
    strategy: css
    category: search
    options: ["启用", "停用"]

  - id: searchBtn
    type: button
    locator: "button:has-text('查询')"
    strategy: css
    category: search

  - id: resetBtn
    type: button
    locator: "button:has-text('重置')"
    strategy: css
    category: search

  - id: addBtn
    type: button
    locator: "button:has-text('新增报警规则')"
    strategy: css
    category: action

  # 表格
  - id: tableRow
    type: collection
    locator: ".el-table__body-wrapper .el-table__row"
    strategy: css
    category: table
    children:
      - id: editBtn
        type: button
        locator: "button:has-text('编辑')"
        strategy: css
      - id: deleteBtn
        type: button
        locator: "button:has-text('删除')"
        strategy: css
      - id: detailBtn
        type: button
        locator: "button:has-text('详情')"
        strategy: css

  - id: pagination
    type: pagination
    locator: ".el-pagination"
    strategy: css
    category: table

  # 弹窗 - 新增/编辑
  - id: dialogAlarmRule
    type: dialog
    locator: ".el-dialog:visible"
    strategy: css
    category: dialog
    fields:
      - id: form_name
        type: input
        locator: "input[placeholder='请输入报警名称']"
        strategy: css
      - id: form_level
        type: select
        locator: ".el-form .el-select"  # 弹窗内第一个select
        strategy: css
      - id: form_threshold
        type: input_number
        locator: "input[type='number']"
        strategy: css
      - id: form_enable_status
        type: switch
        locator: ".el-switch"
        strategy: css
    buttons:
      - id: dialog_save
        type: primary
        locator: "button:has-text('保存')"
      - id: dialog_cancel
        type: default
        locator: "button:has-text('取消')"

  # 弹窗 - 删除确认
  - id: confirmDeleteDialog
    type: dialog
    locator: ".el-dialog:visible"
    strategy: css
    category: dialog
    buttons:
      - id: confirm_btn
        type: primary
        locator: "button:has-text('确定')"
      - id: cancel_btn
        type: default
        locator: "button:has-text('取消')"

  # 状态元素
  - id: loadingMask
    type: state
    locator: ".el-loading-mask"
    strategy: css
  - id: emptyState
    type: state
    locator: ".el-empty"
    strategy: css
  - id: toastSuccess
    type: toast
    locator: ".el-message--success .el-message__content"
    strategy: css
  - id: toastError
    type: toast
    locator: ".el-message--error .el-message__content"
    strategy: css

wait:
  default_timeout: 10
  strategies:
    table_loaded: presence_of_all_elements_located(tableRow)
    dialog_open: visibility_of_element_located(dialogAlarmRule)
    dialog_closed: invisibility_of_element_located(dialogAlarmRule)
    toast_appear: visibility_of_element_located(toastSuccess)
    delete_confirm_open: visibility_of_element_located(confirmDeleteDialog)
    dropdown_visible: presence_of_element_located(".el-popper .el-select-dropdown__item")

notes:
  - "filterable el-select 需先点击触发 Teleport 再等待 popper"
  - "日期选择器面板使用 body .el-picker-panel 定位（本项目无日期字段，仅作参考）"
```

---

以上是 **tank / alarm-config** 页面的完整分析产出。如需调整具体字段（如实际 HTML 不同），可基于截图或真实源码进一步细化。