好的，遵照您的要求，我将以测试自动化专家的身份，分析您提供的页面元素和现存的定位器设计，并输出更新后的 `PAGE_CONTEXT.md` 和 `PAGE_ELEMENT_POSITION.md`。

## 分析过程

1.  **源数据对齐**：对比 `ContractorUnitPage.py` 中的定位器常量和测试脚本 `test_contractor_unit.py` 中的操作函数，确定当前页面的核心交互元素。
2.  **定位器优化**：基于 Vue 3 + Element Plus 技术栈的最佳实践，评估现有定位器（大部分为 C 级 XPath `contains` 匹配），并提供更稳定、更语义化的 B 级及可能的 A 级定位方案。特别是针对用户明确提出的“弹窗表单元素”缺失问题，将根据通用 Element Plus 模式推导并补充定位器。
3.  **输出产出物**：根据 `skill: page-analysis` 的要求，生成结构化的 `PAGE_CONTEXT.md` 和 `PAGE_ELEMENT_POSITION.md`，确保信息完整、定位器优先级明确、等待策略合理。

---

### 产出物 1：PAGE_CONTEXT.md (更新版)

```markdown
# PAGE_CONTEXT — personnel / contractor-unit

## 页面概览
- **页面名称**: 承包商单位管理
- **所属模块**: personnel (人员管理)
- **页面URL**: #/personnel/contractor
- **UI 框架**: Vue 3 + Element Plus
- **页面功能**: 管理承包商单位，提供列表展示、搜索、分页、新增、编辑、启停用、删除等操作。

## 页面结构
- **布局**: 页面主体包含上部的搜索区、中部的数据表格区、底部的分页区。操作按钮位于工具栏和表格行内。

## 元素清单

### 1. 搜索/筛选区 (Search Area)
| 元素ID | 元素描述 | 控件类型 | 备注 |
| :--- | :--- | :--- | :--- |
| search-name | 单位名称输入框 | el-input | 用于按名称模糊搜索 |
| search-code | 单位编码输入框 | el-input | 用于按编码模糊搜索 |
| search-status | 状态下拉框 | el-select | 筛选启用/禁用状态 |
| search-btn | 搜索按钮 | el-button | 触发搜索 |
| reset-btn | 重置按钮 | el-button | 清空搜索条件，重置列表 |

### 2. 工具栏 (Toolbar)
| 元素ID | 元素描述 | 控件类型 | 备注 |
| :--- | :--- | :--- | :--- |
| add-btn | 新增按钮 | el-button | 打开新增承包商单位弹窗 |

### 3. 列表/表格区 (Table Area)
**列定义 (1-based)**

| 字段ID | 字段描述 | 数据类型 | 备注 |
| :--- | :--- | :--- | :--- |
| col-unit-code | 单位编码 | string | 列索引 `COL_UNIT_CODE = 1` |
| col-unit-name | 单位名称 | string | 列索引 `COL_UNIT_NAME = 2` |
| col-contact-person | 联系人 | string | 列索引 `COL_CONTACT_PERSON = 3` |
| col-contact-phone | 联系电话 | string | 列索引 `COL_CONTACT_PHONE = 4` |
| col-status | 启用状态 | tag | 列索引 `COL_STATUS = 5`，常以 `el-tag` 颜色区分 |
| col-operations | 操作 | buttons | 列索引 `COL_OPERATIONS = 6`，包含行内操作按钮 |

**行内操作按钮 (行内 `col-operations` 列)**
| 元素ID | 元素描述 | 控件类型 | 备注 |
| :--- | :--- | :--- | :--- |
| row-edit-btn | 编辑按钮 | el-button | 打开编辑弹窗 |
| row-toggle-status-btn | 启用/停用按钮 | el-button | 按钮文字根据状态在“启用”和“停用”间切换 |
| row-delete-btn | 删除按钮 | el-button | 触发删除确认对话框 |

### 4. 分页区 (Pagination Area)
| 元素ID | 元素描述 | 控件类型 | 备注 |
| :--- | :--- | :--- | :--- |
| pagination | 分页组件 | el-pagination | 位于表格底部 |
| page-size-select | 每页条数选择器 | el-select | 位于分页组件内 |
| next-page-btn | 下一页按钮 | el-button | 位于分页组件内 |
| prev-page-btn | 上一页按钮 | el-button | 位于分页组件内 |
| total-count | 总条数文本 | span | 显示“共 X 条” |

### 5. 弹窗/对话框 (Dialog / Modal)
#### 5.1 新增/编辑 弹窗 (`ContractorFormDialog.vue` 推断)
| 元素ID | 元素描述 | 控件类型 | 备注 |
| :--- | :--- | :--- | :--- |
| dialog-title | 弹窗标题 | span | 文字为“新增承包商单位”或“编辑承包商单位” |
| form-unit-code | 单位编码输入框 | el-input | 编辑时可读性假设 |
| form-unit-name | 单位名称输入框 | el-input | 必填 |
| form-contact-person | 联系人输入框 | el-input | 可选 |
| form-contact-phone | 联系电话输入框 | el-input | 可选 |
| form-submit-btn | 确定按钮 | el-button | 提交表单 |
| form-cancel-btn | 取消按钮 | el-button | 关闭弹窗 |

#### 5.2 确认对话框 (Confirm Dialog)
| 元素ID | 元素描述 | 控件类型 | 备注 |
| :--- | :--- | :--- | :--- |
| confirm-title | 确认标题 | span | 如“提示”、“删除确认” |
| confirm-message | 确认内容 | span | 如“确定要停用/删除该项吗？” |
| confirm-btn | 确认按钮 | el-button | (通常带 `el-button--primary` 类) |
| cancel-btn | 取消按钮 | el-button | |

### 6. 特殊状态
- **加载中**: 表格区域显示骨架屏 (skeleton) 或加载动画。
- **空数据**: 表格区域显示空状态占位图，分页组件不可用。
- **错误状态**: 网络异常时，表格区域或页面主体显示错误提示信息。

### 7. 权限点
| 权限点ID | 元素ID | 描述 | 备注 |
| :--- | :--- | :--- | :--- |
| permission-add | add-btn | 是否允许新增 | 无权限时按钮隐藏 |
| permission-edit | row-edit-btn | 是否允许编辑行 | 无权限时整行按钮隐藏 |
| permission-toggle-status | row-toggle-status-btn | 是否允许启停用 | 无权限时整行按钮隐藏 |
| permission-delete | row-delete-btn | 是否允许删除行 | 无权限时整行按钮隐藏 |
```
---

### 产出物 2：PAGE_ELEMENT_POSITION.md (更新版)

```markdown
# PAGE_ELEMENT_POSITION — personnel / contractor-unit

## 概述
- **页面ID**: contractor-unit
- **模块**: personnel
- **UI 框架**: Vue 3 + Element Plus
- **定位器优化依据**: `ContractorUnitPage.py` 代码中的定位器模式及 Element Plus 通用 UI 结构。

## 元素定位器设计

> 优先级定义：
> - **A级（最优）**：通过稳定的 `id`、`name`、`data-testid`、唯一`aria-label` 定位。最稳定。
> - **B级（推荐）**：通过稳定的 CSS 选择器或基于文本/占位符的相对 XPath 定位。
> - **C级（备用）**：通过复杂 XPath（基于索引、动态 class）或绝对路径定位。易受 UI 变更影响。

### 1. 搜索区 (Search Area)
| 元素ID | 优先定位器 (A级) | 备用定位器 (B级) | 备用定位器 (C级) | 等待策略 | 备注 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| search-name | `N/A` (假设无`testid`) | `(By.CSS_SELECTOR, "input[placeholder*='单位名称']")` | `(By.XPATH, "//input[contains(@placeholder, '单位名称')]")` | `presence_of_element_located` | B级定位清晰，优于原XPath。 |
| search-code | `N/A` | `(By.CSS_SELECTOR, "input[placeholder*='单位编码']")` | `(By.XPATH, "//input[contains(@placeholder, '编码') or contains(@placeholder, '代码')]")` | `presence_of_element_located` | B级定位更精确。 |
| search-status | `N/A` | `(By.XPATH, "//label[contains(text(), '状态')]/following-sibling::div//input")` | `(By.XPATH, '//div[contains(@class,"el-select")][.//span[contains(.,"状态")]]')` | `element_to_be_clickable` | B级与表单标签关联，更稳定。 |
| search-btn | `N/A` | `(By.XPATH, "//button[.//span[contains(text(), '搜索')] and contains(@class, 'el-button')]")` | `(By.XPATH, "//button[contains(text(), '搜索')]")` | `element_to_be_clickable` | B级通过class和文本双重确认。 |
| reset-btn | `N/A` | `(By.XPATH, "//button[.//span[contains(text(), '重置')] and contains(@class, 'el-button')]")` | `(By.XPATH, "//button[contains(text(), '重置')]")` | `element_to_be_clickable` | B级通过class和文本双重确认。 |

### 2. 工具栏 (Toolbar)
| 元素ID | 优先定位器 (A级) | 备用定位器 (B级) | 备用定位器 (C级) | 等待策略 | 备注 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| add-btn | `N/A` | `(By.XPATH, "//button[.//span[contains(text(), '新增')] and contains(@class, 'el-button')]")` | `(By.XPATH, "//button[contains(text(), '新增')]")` | `element_to_be_clickable` | B级通过class和文本双重确认。 |

### 3. 表格区 (Table Area)
> 注意：此处的行内按钮定位器是全表范围的。在具体的测试步骤中，应结合行筛选逻辑（如需操作第N行），将范围缩小到特定行，例如 `tuple(list(TABLE_EDIT_BUTTON_ROW) + (f"[{row_index}]",))`。

| 元素ID | 优先定位器 (A级) | 备用定位器 (B级) | 备用定位器 (C级) | 等待策略 | 备注 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| row-edit-btn | `N/A` | `(By.XPATH, "//button[.//span[contains(text(), '编辑')] and contains(@class, 'el-button')]")` | `(By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[contains(text(),"编辑")]]')` | `element_to_be_clickable` | B级定位更简洁，不依赖绝对路径。 |
| row-toggle-status-btn | `N/A` | `(By.XPATH, "//button[.//span[contains(text(), '停用') or contains(text(), '启用')] and contains(@class, 'el-button')]")` | `(By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[contains(text(),"停用") or contains(text(),"启用")]]')` | `element_to_be_clickable` | B级定位更简洁。 |
| row-delete-btn | `N/A` | `(By.XPATH, "//button[.//span[contains(text(), '删除')] and contains(@class, 'el-button')]")` | `(By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[contains(text(),"删除")]]')` | `element_to_be_clickable` | B级定位更简洁。 |

### 4. 分页区 (Pagination Area)
| 元素ID | 优先定位器 (A级) | 备用定位器 (B级) | 备用定位器 (C级) | 等待策略 | 备注 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| page-size-select | `N/A` | `(By.CSS_SELECTOR, '.el-pagination .el-select__wrapper')` | `(By.XPATH, '//div[contains(@class,"el-pagination")]//div[contains(@class,"el-select")]')` | `element_to_be_clickable` | 使用稳定的CSS选择器。 |
| next-page-btn | `N/A` | `(By.CSS_SELECTOR, '.el-pagination .btn-next')` | `(By.XPATH, '//button[contains(@class,"btn-next")]')` | `element_to_be_clickable` | 使用稳定的CSS选择器。 |
| prev-page-btn | `N/A` | `(By.CSS_SELECTOR, '.el-pagination .btn-prev')` | `(By.XPATH, '//button[contains(@class,"btn-prev")]')` | `element_to_be_clickable` | 使用稳定的CSS选择器。 |
| total-count | `N/A` | `(By.CSS_SELECTOR, '.el-pagination__total')` | `(By.XPATH, '//div[contains(@class,"el-pagination")]//span[contains(@class,"total")]')` | `presence_of_element_located` | 使用稳定的CSS选择器。 |

### 5. 弹窗/对话框 (Dialog / Modal)
#### 5.1 新增/编辑 弹窗 (`ContractorFormDialog.vue` 推断)
| 元素ID | 优先定位器 (A级) | 备用定位器 (B级) | 备用定位器 (C级) | 等待策略 | 备注 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| dialog-title | `N/A` | `(By.CSS_SELECTOR, '.el-dialog__title')` | `(By.XPATH, '//div[contains(@class,"el-dialog")]//span[contains(@class,"title")]')` | `visibility_of_element_located` | 等待弹窗可见。 |
| form-unit-code | `N/A` | `(By.XPATH, "//label[contains(text(), '单位编码')]/following-sibling::div//input")` | `(By.CSS_SELECTOR, '.el-dialog .el-form-item:nth-child(1) input')` | `presence_of_element_located` | B级定位与标签绑定，更稳健。 |
| form-unit-name | `N/A` | `(By.XPATH, "//label[contains(text(), '单位名称')]/following-sibling::div//input")` | `(By.CSS_SELECTOR, '.el-dialog .el-form-item:nth-child(2) input')` | `presence_of_element_located` | B级定位更稳健。 |
| form-contact-person | `N/A` | `(By.XPATH, "//label[contains(text(), '联系人')]/following-sibling::div//input")` | `(By.CSS_SELECTOR, '.el-dialog .el-form-item:nth-child(3) input')` | `presence_of_element_located` | B级定位更稳健。 |
| form-contact-phone | `N/A` | `(By.XPATH, "//label[contains(text(), '联系电话')]/following-sibling::div//input")` | `(By.CSS_SELECTOR, '.el-dialog .el-form-item:nth-child(4) input')` | `presence_of_element_located` | B级定位更稳健。 |
| form-submit-btn | `N/A` | `(By.CSS_SELECTOR, '.el-dialog__footer .el-button--primary')` | `(By.XPATH, '//div[contains(@class,"el-dialog")]//button[contains(@class,"el-button--primary")]')` | `element_to_be_clickable` | 使用样式类，非常稳定。 |
| form-cancel-btn | `N/A` | `(By.XPATH, '//div[contains(@class,"el-dialog__footer")]//button[.//span[contains(text(),"取消")]]')` | `(By.CSS_SELECTOR, '.el-dialog__footer .el-button:not(.el-button--primary)')` | `element_to_be_clickable` | B级通过文本定位，C级通过样式排除。 |

#### 5.2 确认对话框 (Confirm Dialog)
| 元素ID | 优先定位器 (A级) | 备用定位器 (B级) | 备用定位器 (C级) | 等待策略 | 备注 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| confirm-btn | `N/A` | `(By.CSS_SELECTOR, '.el-message-box__btns .el-button--primary')` | `(By.XPATH, "//div[contains(@class, 'el-message-box')]//button[contains(@class, 'el-button--primary')]")` | `element_to_be_clickable` | 使用样式类，非常稳定。 |
| cancel-btn | `N/A` | `(By.XPATH, "//div[contains(@class, 'el-message-box')]//button[.//span[contains(text(),'取消')]]")` | `(By.CSS_SELECTOR, '.el-message-box__btns .el-button:not(.el-button--primary)')` | `element_to_be_clickable` | B级通过文本定位。 |
```
---