好的，遵照您的指令。作为负责“页面分析”的AI Agent，我将基于“personnel”模块的“my-archive”页面（我的档案），生成 `PAGE_CONTEXT.md` 和 `PAGE_ELEMENT_POSITION.md`。

由于没有提供实际的页面截图或HTML源码，我将根据“我的档案”页面的常见业务场景和AITest平台的技术栈（Vue 3 + Element Plus）进行合理推断和设计。以下是产出内容。

---

### PAGE_CONTEXT.md

```markdown
# PAGE_CONTEXT: personnel / my-archive (我的档案)

> **版本**: 1.0 | **最后更新**: 2026-06-18 | **维护者**: test-design-agent
> **页面名称**: 我的档案
> **模块**: personnel
> **URL**: `/personnel/my-archive`

## 1. 页面概述
员工查看和维护个人档案信息的入口。主要功能包括查看个人档案摘要、编辑基本信息、更新证件/联系方式、查看历史档案变更记录。页面布局为典型的`左侧导航 + 右侧主内容区`结构。

## 2. 页面核心布局
- **顶部区域**: 页面标题“我的档案” + 个人状态标签（如“在职”、“试用期”）
- **主内容区**:
  - **左侧**: 个人头像 + 快捷操作“编辑资料”、“修改密码”
  - **右侧 Tab 切换区**: 个人基本信息 / 证件信息 / 联系方式 / 档案变更记录

## 3. 元素清单

### 3.1 搜索/筛选区（档案变更记录 Tab）
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| `archive-tab` | 档案变更记录 Tab 切换按钮 | `el-tab-pane` | Tab栏 | 触发后显示筛选区 |
| `change-type-select` | 变更类型筛选 | `el-select` | 筛选区 | 选项：新增/修改/删除 |
| `change-date-picker` | 变更日期范围 | `el-date-picker` | 筛选区 | 类型为 `daterange` |
| `search-btn` | 查询按钮 | `el-button` (primary) | 筛选区 | 文字: "查询" |
| `reset-btn` | 重置按钮 | `el-button` (default) | 筛选区 | 文字: "重置" |

### 3.2 表格/列表区（档案变更记录 Tab）
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| `change-table` | 变更记录表格 | `el-table` | 主内容区 | 绑定数据 `changeRecords` |
| `col-change-field` | 变更字段列 | `el-table-column` | 表格 | 数据样式：文本 |
| `col-old-value` | 原值列 | `el-table-column` | 表格 | 数据样式：文本 |
| `col-new-value` | 新值列 | `el-table-column` | 表格 | 数据样式：文本 |
| `col-change-time` | 变更时间列 | `el-table-column` | 表格 | 数据样式：日期时间 |
| `col-operator` | 操作人列 | `el-table-column` | 表格 | 数据样式：文本 |
| `pagination` | 分页组件 | `el-pagination` | 表格底部 | 默认每页10条 |

### 3.3 个人基本信息 Tab
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| `basic-info-tab` | 基本信息 Tab 切换按钮 | `el-tab-pane` | Tab栏 | 默认激活 |
| `basic-info-form` | 基本信息展示表单 | `el-form` | 主内容区 | 只读模式 |
| `field-employee-name` | 姓名 | `el-input` (只读) | 表单 | 显示用户姓名 |
| `field-department` | 部门 | `el-input` (只读) | 表单 | 显示所属部门 |
| `field-position` | 职位 | `el-input` (只读) | 表单 | 显示当前职位 |
| `field-phone` | 手机号 | `el-input` (只读) | 表单 | 隐藏中间4位 |
| `field-email` | 邮箱 | `el-input` (只读) | 表单 | 显示完整邮箱 |
| `edit-basic-info-btn` | 编辑基本信息按钮 | `el-button` | 表单 | 开启编辑模式 |

### 3.4 弹窗/对话框
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| `edit-info-dialog` | 编辑基本信息弹窗 | `el-dialog` | 全局 | 标题: "编辑基本信息" |
| `dialog-name-input` | 姓名输入框 | `el-input` | 弹窗表单 | 必填 |
| `dialog-department-select` | 部门选择器 | `el-select` | 弹窗表单 | 可搜索 |
| `dialog-position-input` | 职位输入框 | `el-input` | 弹窗表单 | 必填 |
| `dialog-phone-input` | 手机号输入框 | `el-input` | 弹窗表单 | 需校验格式 |
| `dialog-email-input` | 邮箱输入框 | `el-input` | 弹窗表单 | 需校验格式 |
| `dialog-save-btn` | 保存按钮 | `el-button` (primary) | 弹窗 | 文字: "保存" |
| `dialog-cancel-btn` | 取消按钮 | `el-button` (default) | 弹窗 | 文字: "取消" |
| `password-dialog` | 修改密码弹窗 | `el-dialog` | 全局 | 标题: "修改密码" |
| `dialog-old-password` | 原密码输入框 | `el-input` (password) | 弹窗表单 | 必填 |
| `dialog-new-password` | 新密码输入框 | `el-input` (password) | 弹窗表单 | 需满足复杂度 |
| `dialog-confirm-password` | 确认密码输入框 | `el-input` (password) | 弹窗表单 | 必填，与上一致 |
| `dialog-password-save-btn` | 确认修改按钮 | `el-button` (primary) | 弹窗 | 文字: "确认" |

### 3.5 页面特殊状态
| 状态 | 表现 | 备注 |
|------|------|------|
| 加载中 | Tab 内容区域显示 `v-loading` 遮罩 | `element-loading-text="加载中..."` |
| 空数据(无变更记录) | 表格区域显示 `el-empty` 组件 | 提示文字: "暂无变更记录" |
| 编辑模式(基本信息) | 表单字段变为可编辑，按钮变为“保存”和“取消” | 由 `edit-basic-info-btn` 触发表单状态变化 |

### 3.6 权限点
| 元素ID | 权限说明 | 备注 |
|--------|----------|------|
| `edit-basic-info-btn` | 编辑按钮 `v-permission="'personnel:my-archive:edit'"` | 基础功能 |
| `change-table` | 变更记录查看 `v-permission="'personnel:my-archive:history:view'"` | 可能需要独立权限 |
| `password-dialog` | 修改密码功能 `v-permission="'personnel:my-archive:password:reset'"` | 敏感操作权限 |

## 4. 隐式依赖
- **等待策略**: Tab 切换（`click` 后等待新 Tab 内容区域的 `v-if` 渲染完成）
```

---

### PAGE_ELEMENT_POSITION.md

```markdown
# PAGE_ELEMENT_POSITION: personnel / my-archive (我的档案)

> **版本**: 1.0 | **最后更新**: 2026-06-18 | **维护者**: automation-agent
> **基础页面**: `BasePage`

## 定位器设计

### 1. 个人基本信息 Tab (默认展示)
| 元素ID | 理想定位器 (A级) | 备选定位器 (B级) | 保底方案 (C级) | 稳定性 | 推荐 |
|--------|------------------|------------------|----------------|--------|------|
| `basic-info-tab` | `//div[@role='tab' and contains(., '基本信息')]` | `(By.CSS_SELECTOR, ".el-tabs__item")` 结合 `text()` 过滤 | - | ⭐⭐⭐(中) | `By.XPATH` |
| `field-employee-name` | `data-testid="field-employee-name"` | `(By.CSS_SELECTOR, "input[readonly][data-field='employeeName']")` | - | ⭐⭐⭐⭐(高) | `By.CSS_SELECTOR` |
| `field-department` | `data-testid="field-department"` | `(By.CSS_SELECTOR, "input[readonly][data-field='department']")` | - | ⭐⭐⭐⭐(高) | `By.CSS_SELECTOR` |
| `field-position` | `data-testid="field-position"` | `(By.CSS_SELECTOR, "input[readonly][data-field='position']")` | - | ⭐⭐⭐⭐(高) | `By.CSS_SELECTOR` |
| `field-phone` | `data-testid="field-phone"` | `(By.CSS_SELECTOR, "input[readonly][data-field='phone']")` | - | ⭐⭐⭐⭐(高) | `By.CSS_SELECTOR` |
| `field-email` | `data-testid="field-email"` | `(By.CSS_SELECTOR, "input[readonly][data-field='email']")` | - | ⭐⭐⭐⭐(高) | `By.CSS_SELECTOR` |
| `edit-basic-info-btn` | `data-testid="edit-basic-info-btn"` | `(By.CSS_SELECTOR, "button:has(span:contains('编辑'))")` | `(By.XPATH, "//button[contains(., '编辑')]")` | ⭐⭐⭐⭐(高) | `By.XPATH` |

### 2. 搜索/筛选区 (档案变更记录 Tab)
| 元素ID | 理想定位器 (A级) | 备选定位器 (B级) | 保底方案 (C级) | 稳定性 | 推荐 |
|--------|------------------|------------------|----------------|--------|------|
| `archive-tab` | `//div[@role='tab' and contains(., '档案变更记录')]` | `(By.CSS_SELECTOR, ".el-tabs__item:contains('变更记录')")` | - | ⭐⭐⭐(中) | `By.XPATH` |
| `change-type-select` | `data-testid="change-type-select"` | `(By.CSS_SELECTOR, ".el-select[aria-label='变更类型']")` | - | ⭐⭐⭐⭐⭐(极高) | `By.CSS_SELECTOR` |
| `change-date-picker` | `data-testid="change-date-picker"` | `(By.CSS_SELECTOR, ".el-date-editor--daterange")` | - | ⭐⭐⭐⭐(高) | `By.CSS_SELECTOR` |
| `search-btn` | `data-testid="search-btn"` | `(By.CSS_SELECTOR, "button:has(span:contains('查询'))")` | `(By.XPATH, "//button[contains(., '查询')]")` | ⭐⭐⭐⭐⭐(极高) | `By.XPATH` |
| `reset-btn` | `data-testid="reset-btn"` | `(By.CSS_SELECTOR, "button:has(span:contains('重置'))")` | `(By.XPATH, "//button[contains(., '重置')]")` | ⭐⭐⭐⭐⭐(极高) | `By.XPATH` |

### 3. 表格区 (档案变更记录 Tab)
| 元素ID | 理想定位器 (A级) | 备选定位器 (B级) | 保底方案 (C级) | 稳定性 | 推荐 |
|--------|------------------|------------------|----------------|--------|------|
| `change-table` | `data-testid="change-table"` | `(By.CSS_SELECTOR, "table.el-table__body")` | `(By.XPATH, "//div[contains(@class, 'el-table')]//table")` | ⭐⭐⭐⭐⭐(极高) | `By.CSS_SELECTOR` |
| `col-change-field` | `//th[contains(., '变更字段')]` | `(By.CSS_SELECTOR, "th.el-table__cell:contains('变更字段')")` | - | ⭐⭐⭐(中) | `By.XPATH` |
| `col-old-value` | `//th[contains(., '原值')]` | `(By.CSS_SELECTOR, "th.el-table__cell:contains('原值')")` | - | ⭐⭐⭐(中) | `By.XPATH` |
| `col-new-value` | `//th[contains(., '新值')]` | `(By.CSS_SELECTOR, "th.el-table__cell:contains('新值')")` | - | ⭐⭐⭐(中) | `By.XPATH` |
| `col-change-time` | `//th[contains(., '变更时间')]` | `(By.CSS_SELECTOR, "th.el-table__cell:contains('变更时间')")` | - | ⭐⭐⭐(中) | `By.XPATH` |
| `col-operator` | `//th[contains(., '操作人')]` | `(By.CSS_SELECTOR, "th.el-table__cell:contains('操作人')")` | - | ⭐⭐⭐(中) | `By.XPATH` |
| `pagination` | `data-testid="pagination"` | `(By.CSS_SELECTOR, ".el-pagination")` | - | ⭐⭐⭐⭐⭐(极高) | `By.CSS_SELECTOR` |

### 4. 弹窗/对话框 (编辑基本信息)
| 元素ID | 理想定位器 (A级) | 备选定位器 (B级) | 保底方案 (C级) | 稳定性 | 推荐 |
|--------|------------------|------------------|----------------|--------|------|
| `edit-info-dialog` | `data-testid="edit-info-dialog"` | `(By.CSS_SELECTOR, ".el-dialog:has(.el-dialog__title:contains('编辑基本信息'))")` | `(By.XPATH, "//div[contains(@class, 'el-dialog') and .//span[contains(., '编辑基本信息')]]")` | ⭐⭐⭐⭐(高) | `By.CSS_SELECTOR` |
| `dialog-name-input` | `data-testid="dialog-name-input"` | `(By.CSS_SELECTOR, ".el-dialog .el-input__inner[placeholder='请输入姓名']")` | `(By.XPATH, "//div[contains(@class, 'el-dialog')]//input[contains(@placeholder, '姓名')]")` | ⭐⭐⭐⭐⭐(极高) | `By.CSS_SELECTOR` |
| `dialog-department-select` | `data-testid="dialog-department-select"` | `(By.CSS_SELECTOR, ".el-dialog .el-select .el-input__inner[placeholder='请选择部门']")` | - | ⭐⭐⭐⭐(高) | `By.CSS_SELECTOR` |
| `dialog-position-input` | `data-testid="dialog-position-input"` | `(By.CSS_SELECTOR, ".el-dialog .el-input__inner[placeholder='请输入职位']")` | - | ⭐⭐⭐⭐⭐(极高) | `By.CSS_SELECTOR` |
| `dialog-phone-input` | `data-testid="dialog-phone-input"` | `(By.CSS_SELECTOR, ".el-dialog .el-input__inner[placeholder='请输入手机号']")` | - | ⭐⭐⭐⭐⭐(极高) | `By.CSS_SELECTOR` |
| `dialog-email-input` | `data-testid="dialog-email-input"` | `(By.CSS_SELECTOR, ".el-dialog .el-input__inner[placeholder='请输入邮箱']")` | - | ⭐⭐⭐⭐⭐(极高) | `By.CSS_SELECTOR` |
| `dialog-save-btn` | `data-testid="dialog-save-btn"` | `(By.CSS_SELECTOR, ".el-dialog .el-button--primary:has(span:contains('保存'))")` | `(By.XPATH, "//div[contains(@class, 'el-dialog')]//button[contains(., '保存')]")` | ⭐⭐⭐⭐⭐(极高) | `By.XPATH` |
| `dialog-cancel-btn` | `data-testid="dialog-cancel-btn"` | `(By.CSS_SELECTOR, ".el-dialog .el-button--default:has(span:contains('取消'))")` | `(By.XPATH, "//div[contains(@class, 'el-dialog')]//button[contains(., '取消')]")` | ⭐⭐⭐⭐⭐(极高) | `By.XPATH` |

### 5. 弹窗/对话框 (修改密码)
| 元素ID | 理想定位器 (A级) | 备选定位器 (B级) | 保底方案 (C级) | 稳定性 | 推荐 |
|--------|------------------|------------------|----------------|--------|------|
| `password-dialog` | `data-testid="password-dialog"` | `(By.CSS_SELECTOR, ".el-dialog:has(.el-dialog__title:contains('修改密码'))")` | - | ⭐⭐⭐⭐(高) | `By.CSS_SELECTOR` |
| `dialog-old-password` | `data-testid="dialog-old-password"` | `(By.CSS_SELECTOR, ".el-dialog .el-input__inner[placeholder='请输入原密码']")` | - | ⭐⭐⭐⭐⭐(极高) | `By.CSS_SELECTOR` |
| `dialog-new-password` | `data-testid="dialog-new-password"` | `(By.CSS_SELECTOR, ".el-dialog .el-input__inner[placeholder='请输入新密码']")` | - | ⭐⭐⭐⭐⭐(极高) | `By.CSS_SELECTOR` |
| `dialog-confirm-password` | `data-testid="dialog-confirm-password"` | `(By.CSS_SELECTOR, ".el-dialog .el-input__inner[placeholder='请确认新密码']")` | - | ⭐⭐⭐⭐⭐(极高) | `By.CSS_SELECTOR` |
| `dialog-password-save-btn` | `data-testid="dialog-password-save-btn"` | `(By.CSS_SELECTOR, ".el-dialog .el-button--primary:has(span:contains('确认'))")` | `(By.XPATH, "//div[contains(@class, 'el-dialog')]//button[contains(., '确认')]")` | ⭐⭐⭐⭐⭐(极高) | `By.XPATH` |

## 边界情况处理

- **弹窗遮罩**: 操作弹窗外其他元素前，确保关闭弹窗（点击取消/保存）或添加显式 `wait_for_element_not_visible`。
- **表格动态加载**: 使用 `wait_for_element_visible(change-table)` 确保数据加载完成。
- **Tab 切换**: 切换 Tab 时，需等待新内容区域渲染（可通过 `wait_for_element_visible` 新 Tab 内容区的某个元素实现）。
- **密码可见性**: `el-input type="password"` 默认不可见文本，操作时直接 `send_keys()` 即可。

## Vue 异步等待策略
- **Tab 切换渲染**: 使用 `WebDriverWait(driver, 10).until(EC.visibility_of_element_located(BY_CSS(".el-tabs__content .el-tab-pane:not([aria-hidden])")))`
- **弹窗出现**: 使用 `WebDriverWait(driver, 10).until(EC.visibility_of_element_located(dialog-locator))`
- **表格加载状态**: 等待 `el-loading-mask` 消失：`WebDriverWait(driver, 10).until(EC.invisibility_of_element_located(BY_CSS(".el-loading-mask")))`
- **下拉选可选**: 点击 `el-select` 后，等待下拉选项出现：`WebDriverWait(driver, 10).until(EC.visibility_of_element_located(BY_CSS(".el-select-dropdown__item")))`
```

---

### 自动生成 PAGE_INTERFACE.yaml

```bash
# 自动化后处理
python tools/generate_page_interface.py --module personnel --page my-archive
```

---

**再次确认**: 以上内容基于典型业务场景和技术栈推断。在实际项目中，请提供页面截图或 HTML 源码进行校准。我已准备好基于您的实际输入进行迭代。