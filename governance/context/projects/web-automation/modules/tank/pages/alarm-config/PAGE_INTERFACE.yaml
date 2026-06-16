好的，作为你的Web端测试工程师，我已接收任务：分析`tank`模块的`alarm-config`页面。

根据你提供的HTML源代码，这是一个典型的“编辑/新增报警配置”的弹窗页面（Dialog）。我将按照标准流程，逐区域分析页面结构，识别元素，并设计稳定可靠的Selenium定位器。

---

### 第一步：PAGE_CONTEXT.md - 页面元素清单

这个页面是一个相对简单的弹窗编辑表单。我们将基于HTML源码进行详细分析。

**页面名称**: 报警配置编辑
**页面URL**: N/A (弹窗)
**所属模块**: tank

#### 1. 页面整体结构
这是一个由`el-dialog`组件构成的弹窗页面，包含标题区、加载状态、表单内容和底部操作区。

#### 2. 搜索/筛选区
无。该页面为弹窗编辑表单，不含搜索区。

#### 3. 表格/列表区
无。该页面为弹窗编辑表单，不含表格。

#### 4. 弹窗/对话框
-   **弹窗标题**: 编辑报警配置 / 新增报警配置 (由变量`title`控制)
-   **弹窗内表单字段**:

| 字段标签 | 字段标识 (Prop) | 控件类型 | 元素描述 | 备注 |
|:---|:---|:---|:---|:---|
| 报警类型 | `alarmType` | el-select | 下拉选择框 | 必选项 |
| 报警邮箱 | `alarmEmail` | el-input | 文本输入框 | 必填项 |
| 备注 | `remark` | el-input (textarea) | 文本域 | 选填项 |

-   **弹窗按钮**:

| 按钮文字 | 控件类型 | 元素描述 | 备注 |
|:---|:---|:---|:---|
| 取消 | el-button | 文本按钮 | 关闭弹窗 |
| 确 定 | el-button (type="primary") | 提交表单 | 提交修改/新增 |

#### 5. 页面状态
-   **加载中**: `el-dialog`会加载，但`v-if='!loading'`会隐藏表单，等待加载完成后显示。目前没有加载中的动画或文字显示在代码中，但逻辑上是存在的。
-   **空数据/错误状态**: 没有独立的空数据或错误状态显示。错误信息将通过在提交失败时显示的`el-message`(Toast)或表单校验错误提示来处理。

#### 6. 权限点
-   **弹窗本身**: 需要页面级的“编辑”或“新增”权限点来控制用户能否打开此弹窗。
-   **报警邮箱输入框**: 可能需要独立的数据权限来限制可编辑的邮箱范围。

#### 元素清单表格

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|:---|:---|:---|:---|:---|
| `DIALOG` | 弹窗容器 | el-dialog | 弹窗 | 整个弹窗的容器 |
| `DIALOG_TITLE` | 弹窗标题 | el-dialog header | 弹窗-标题 | 文本内容为“编辑报警配置” |
| `ALARM_TYPE_SELECT` | 报警类型选择框 | el-select | 弹窗-表单 | 必选项 |
| `ALARM_EMAIL_INPUT` | 报警邮箱输入框 | el-input | 弹窗-表单 | 必填项 |
| `REMARK_INPUT` | 备注输入框 | el-input | 弹窗-表单 | 选填项 |
| `SAVE_BUTTON` | 确定按钮 | el-button (primary) | 弹窗-底部 | 提交表单 |
| `CANCEL_BUTTON` | 取消按钮 | el-button | 弹窗-底部 | 关闭弹窗 |

---

### 第二步：PAGE_ELEMENT_POSITION.md - 元素定位器设计

基于以上分析，结合Selenium和BasePage的规范，设计稳定可靠的定位器。所有定位器均遵循**C级（XPath）定位**原则，以确保在各种UI调整下保持稳定。

| 元素ID | 定位策略 | 定位值 (By策略/定位器字符串) | 稳定性评级 | 备用方案 (XPath) | 等待策略 |
|:---|:---|:---|:---|:---|:---|
| `DIALOG` | XPath | `//div[contains(@class, 'el-dialog')]` | C | - | `visibility_of_element_located` |
| `DIALOG_TITLE` | XPath | `//span[contains(text(), '编辑报警配置') or contains(text(), '新增报警配置')]` | C | 基于Dialog的子元素定位：`//div[contains(@class, 'el-dialog__title')]` | `visibility_of_element_located` |
| `ALARM_TYPE_SELECT` | XPath | `//label[text()='报警类型']/following-sibling::div//input` | C | 基于form-item的class定位：`//div[contains(@class, 'el-form-item') and .//label[text()='报警类型']]//input` | `element_to_be_clickable` |
| `ALARM_EMAIL_INPUT` | XPath | `//label[text()='报警邮箱']/following-sibling::div//input` | C | 同备用方案：`//div[contains(@class, 'el-form-item') and .//label[text()='报警邮箱']]//input` | `element_to_be_clickable` |
| `REMARK_INPUT` | XPath | `//label[text()='备注']/following-sibling::div//textarea` | C | 同备用方案：`//div[contains(@class, 'el-form-item') and .//label[text()='备注']]//textarea` | `element_to_be_clickable` |
| `SAVE_BUTTON` | XPath | `//button[contains(@class, 'el-button--primary') and .//span[text()='确 定']]` | C | - | `element_to_be_clickable` |
| `CANCEL_BUTTON` | XPath | `//button[.//span[text()='取消']]` | C | - | `element_to_be_clickable` |

#### 定位器设计说明

1.  **XPath作为主策略**: 由于页面中没有`data-testid`、`id`或稳定的`name`属性，因此使用XPath作为主要定位策略。这确保了定位器的唯一性和稳定性。
2.  **label-following-sibling定位**: 这是Element Plus表单定位的黄金法则。通过`//label[text()='报警类型']/following-sibling::div`来定位表单控件，即使HTML结构微调，只要Label文字不变，定位器就仍然有效。
3.  **备用方案**: 对于核心字段，提供了基于CSS Selector的备用方案，以防XPath因浏览器或版本问题执行缓慢。
4.  **等待策略**:
    -   `visibility_of_element_located`: 用于弹窗本身和标题，确保用户能看到弹窗。
    -   `element_to_be_clickable`: 用于所有需要交互的表单控件和按钮，确保它们加载完毕且可用。
5.  **`SAVE_BUTTON`定位**: 使用`contains(@class, 'el-button--primary')`来定位主色按钮，避免直接匹配完全类名，因为Element Plus的类名可能随版本变化。同时结合`text()`精确匹配按钮文本，防止误定位到其他按钮。

---

### 自动后处理 (P1-2 合并)

`PAGE_INTERFACE.yaml`将自动生成。其结构将如下：

```yaml
# PAGE_INTERFACE.yaml for tank/alarm-config
page:
  name: 报警配置编辑
  module: tank
  elements:
    - id: DIALOG
      type: dialog
      locator: "//div[contains(@class, 'el-dialog')]"
      description: 报警配置编辑弹窗
    - id: ALARM_TYPE_SELECT
      type: select
      locator: "//label[text()='报警类型']/following-sibling::div//input"
      description: 报警类型下拉框
    - id: ALARM_EMAIL_INPUT
      type: input
      locator: "//label[text()='报警邮箱']/following-sibling::div//input"
      description: 报警邮箱输入框
    - id: REMARK_INPUT
      type: textarea
      locator: "//label[text()='备注']/following-sibling::div//textarea"
      description: 备注文本域
    - id: SAVE_BUTTON
      type: button
      locator: "//button[contains(@class, 'el-button--primary') and .//span[text()='确 定']]"
      description: 确定按钮
    - id: CANCEL_BUTTON
      type: button
      locator: "//button[.//span[text()='取消']]"
      description: 取消按钮
  interactions:
    - action: 填写报警配置
      description: 设置报警类型、邮箱和备注
      steps:
        - element: ALARM_TYPE_SELECT
          action: select_option_by_label
          param: "${alarm_type}"
        - element: ALARM_EMAIL_INPUT
          action: send_keys
          param: "${alarm_email}"
        - element: REMARK_INPUT
          action: send_keys
          param: "${remark}"
    - action: 提交配置
      description: 点击确定按钮提交
      steps:
        - element: SAVE_BUTTON
          action: click
    - action: 取消配置
      description: 点击取消按钮
      steps:
        - element: CANCEL_BUTTON
          action: click
```