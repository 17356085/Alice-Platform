好的，作为Web端测试工程师，我将根据页面名称 `business-type-config`（业务类型配置）和所属模块 `production`（生产管理），在缺乏实际截图和HTML源码的情况下，基于企业级后台管理的常见模式，为你构建一份详细且符合规范的页面分析与定位器设计文档。

---

## 产出物 1: PAGE_CONTEXT.md

```markdown
# 页面上下文: 业务类型配置 (Business Type Config)

## 1. 页面信息
- **页面名称**: 业务类型配置
- **所属模块**: 生产管理 (Production)
- **页面URL**: `/production/business-type-config`

## 2. 页面整体结构
该页面高度专注于“业务类型”的基础配置管理。整体布局遵循经典的后台管理范式，结构清晰：
- **顶部**: 页面标题“业务类型配置”及简短的提示文字（如：“管理生产过程中的不同业务类型”）。
- **主内容区**: 包含搜索/筛选区、表格列表、分页组件。
- **操作区域**: 位于表格右上方，包含“新增业务类型”主操作按钮。
- **弹窗系统**: 新增/编辑/配置操作均通过弹窗（Dialog）进行。
- **页面状态**: 加载中（Skeleton）、空数据（Empty）、错误边界（ErrorBoundary）。

## 3. 页面元素清单

### 3.1 搜索/筛选区
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `search-type-name` | 业务类型名称 | `el-input` | 搜索区 | 模糊搜索 |
| `search-status` | 状态筛选 | `el-select` | 搜索区 | 下拉选择，选项: 全部/启用/禁用 |
| `search-btn` | 搜索按钮 | `el-button` | 搜索区 | 触发搜索 |
| `reset-btn` | 重置按钮 | `el-button` | 搜索区 | 重置搜索条件 |

### 3.2 表格/列表区
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `table` | 业务类型列表 | `el-table` | 表格区 | 主要数据展示 |
| `th-id` | 表头：编号 | `el-table-column` | 表格区 | 文本类型 |
| `th-name` | 表头：业务类型名称 | `el-table-column` | 表格区 | 文本类型 |
| `th-code` | 表头：类型编码 | `el-table-column` | 表格区 | 文本类型 |
| `th-desc` | 表头：描述 | `el-table-column` | 表格区 | 文本类型，可省略 |
| `th-status` | 表头：状态 | `el-table-column` | 表格区 | 带状态标签，如 `el-tag` (成功/危险) |
| `th-operations` | 表头：操作 | `el-table-column` | 表格区 | 操作按钮集合 |
| `btn-edit. {row}` | 编辑按钮 | `el-button` | 表格区 | 文本/图标按钮 |
| `btn-toggle-status.{row}` | 启用/禁用按钮 | `el-button` | 表格区 | 切换开关 |
| `btn-delete.{row}` | 删除按钮 | `el-button` | 表格区 | 确认弹窗后删除 |

### 3.3 分页区
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `pagination` | 分页组件 | `el-pagination` | 表格底部 | 支持10/20/50/100条/页 |
| `pager-sizes` | 每页条数选择 | `el-select` | 分页区 | 下拉选择 |
| `pager-total` | 总条数显示 | `el-tag` | 分页区 | 文本显示 |

### 3.4 弹窗/对话框
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `dialog-create` | 新增业务类型弹窗 | `el-dialog` | 弹窗区 | 表单容器 |
| `dlg-title` | 弹窗标题 | `-` | 弹窗区 | 文本: 新增/编辑业务类型 |
| `dlg-name` | 业务类型名称输入 | `el-input` | 弹窗区 | 必填 |
| `dlg-code` | 业务类型编码 | `el-input` | 弹窗区 | 必填，唯一性校验 |
| `dlg-desc` | 描述输入 | `el-input` | 弹窗区 | 选填，文本框 |
| `dlg-status-switch` | 状态开关 | `el-switch` | 弹窗区 | 是否启用 |
| `dlg-save-btn` | 保存按钮 | `el-button` | 弹窗区 | `type="primary"` |
| `dlg-cancel-btn` | 取消按钮 | `el-button` | 弹窗区 | 关闭弹窗 |

### 3.5 页面其他状态
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|---|---|---|---|---|
| `error-boundary` | 错误状态 | `el-result` | 占位区 | 子标题+重试按钮 |
| `empty-data` | 空数据状态 | `el-empty` | 表格区 | 描述文字+操作按钮 |
| `loading-skeleton` | 加载骨架屏 | `el-skeleton` | 表格区 | 行1~5 |

## 4. 权限点
- **新增按钮（`search-btn`）**：需拥有“新增”权限
- **编辑/删除/状态变更按钮**：需拥有对应行级操作权限
- **弹窗表单中的字段（如编码、状态开关）**：可能受编辑权限控制，只读或可编辑
```

---

## 产出物 2: PAGE_ELEMENT_POSITION.md

```markdown
# 元素定位器: 业务类型配置 (Business Type Config)

## 定位器设计说明
- **优先级策略**: A级（唯一稳定属性）> B级（CSS Selector）> C级（XPath）
- **技术栈背景**: Vue 3 + Element Plus。所有 `el-` 前缀组件均采用其稳定类名进行定位。
- **等待策略**: 所有关键交互均依赖 WebDriverWait，确保元素可定位后操作。

## 核心元素定位器表

| 元素ID | 定位策略 | 定位器值 | 稳定性评级 | 备用方案 |
|---|---|---|---|---|
| `search-type-name` | CSS Selector | `input[placeholder*="请输入业务类型名称"]` | **A** | `@id=search-type-name` |
| `search-status` | CSS Selector | `div[data-testid="search-status"] .el-select__wrapper` | **A** | `@class=el-select` 下的 `.el-select__wrapper` |
| `search-btn` | XPath | `//button[.//span[text()='搜索']]` | **B** | `@data-testid=search-btn` |
| `reset-btn` | XPath | `//button[.//span[text()='重置']]` | **B** | `@data-testid=reset-btn` |
| `table` | CSS Selector | `.el-table` | **B** | 无，表格唯一 |
| `th-name` | CSS Selector | `.el-table__header-wrapper .el-table__header th:nth-child(2)` | **B** | 根据表头文本定位：`//th[.//div[text()='业务类型名称']]` |
| `btn-edit` (第1行) | XPath | `(//button[.//span[text()='编辑']])[1]` | **C** | 使用 `data-testid` 或 `:id` 绑定行ID |
| `btn-delete` (某一行) | XPath | `//tr[td[contains(text(),'{{业务类型名称}}')]]//button[.//span[text()='删除']]` | **C** | 结合行文本定位，稳定性较差 |
| `pagination` | CSS Selector | `.el-pagination` | **B** | 表内唯一 |
| `dialog-create` (弹窗) | CSS Selector | `div[role="dialog"][aria-label*="业务类型"]` | **A** | `.el-dialog` |
| `dlg-name` (弹窗内输入) | CSS Selector | `.el-dialog input[placeholder*="请输入名称"]` | **A** | `@data-testid=dlg-name` |
| `dlg-save-btn` | XPath | `//div[@role='dialog']//button[.//span[text()='确 认' or text()='保 存']]` | **B** | `.el-dialog .el-button--primary` |

## 特殊场景处理 & 等待策略

| 场景 | 元素 | 等待策略 | 说明 |
|---|---|---|---|
| **页面加载** | `table` | `presence_of_element_located` | 等待表格容器出现在DOM中 |
| **搜索** | `search-btn` | `element_to_be_clickable` | 等按钮可点击 |
| **新增/编辑弹窗** | `dialog-create` | `visibility_of_element_located` | 等弹窗完全可见（CSS transition结束） |
| **表单提交** | `dlg-save-btn` | `element_to_be_clickable` + 延时等待非活跃状态 | 防止异步重复提交 |
| **状态切换** | `btn-toggle-status` | `staleness_of` (原开关) 或 `element_to_be_clickable` (新开关) | 等待Vue响应式更新DOM |
| **请求失败** | `error-boundary` | 自定义超时断言 | 监控XHR请求状态 |

## 警告
- **分页切换**: 切换每页条数后，整个表格内容重新渲染，**所有表格内的行级定位器会失效**，需重新获取。
- **数据变更**: 新增、编辑、删除操作后，页面数据刷新，必须等待新的表格数据加载完毕（等待 `tbody` 的第一行数据显示）。
```

---

### 下一步建议

1.  **提供页面截图或HTML源码**：请提供实际的页面截图或某个关键功能的HTML源码（尤其是复杂表单、操作弹窗、表格和下拉选择组件），我可以用更精确的定位器替换上述推测性内容。
2.  **确认技术栈**：请确认后台是否使用了 `data-testid` 等测试专用属性，这将极大提升定位器的稳定性。
3.  **完善 `PAGE_INTERFACE.yaml`**：一旦 `PAGE_CONTEXT.md` 和 `PAGE_ELEMENT_POSITION.md` 确定下来，我将自动调用 `generate_page_interface.py` 脚本，为你生成供自动化引擎直接调用的 `PAGE_INTERFACE.yaml` 文件。