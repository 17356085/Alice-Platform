好的，既然你没有提供截图或HTML源码，我将基于“personnel（人员管理）”模块中典型的“qualification（资质管理）”页面功能，为你生成一份**基于行业最佳实践的假设性分析框架**。

这份分析会假设一个通用的、包含增删改查和权限控制的后台管理系统页面。你可以将此作为模板，等你提供截图或HTML后，我会进行精确校准。

---

## 输出：PAGE_CONTEXT.md（假设性分析）

### 页面信息

| 项目 | 内容 |
|------|------|
| **页面名称** | 资质管理 (qualification) |
| **所属模块** | personnel (人员管理) |
| **页面URL** | /personnel/qualification |
| **技术栈** | Vue 3 + Element Plus |
| **页面类型** | 列表页 + 弹窗表单 |

### 页面整体结构

```
[顶部导航/面包屑]： 人员管理 > 资质管理
[主功能区]：
    ├── [搜索/筛选区]： 一行布局，包含输入框、下拉选择、日期范围、搜索/重置按钮
    ├── [操作按钮区]： 新增资质 (若权限允许)
    ├── [表格/列表区]： 展示资质列表，支持多选
    ├── [分页区]： 底部固定，支持页码/页数切换
    └── [弹窗层]： el-dialog，用于新增/编辑/查看详情
```

### 页面元素清单

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| `search-name` | 资质名称搜索框 | `el-input` (input) | 搜索区 | placeholder: 请输入资质名称 |
| `search-type` | 资质类型下拉筛选 | `el-select` | 搜索区 | 选项: 学历证书/职业资格/技能等级/荣誉证书 |
| `search-status` | 状态下拉筛选 | `el-select` | 搜索区 | 选项: 全部/有效/无效/过期 |
| `search-date` | 获取日期范围 | `el-date-picker` | 搜索区 | type="daterange" |
| `btn-search` | 搜索按钮 | `el-button` | 搜索区 | 文字: "搜索" |
| `btn-reset` | 重置按钮 | `el-button` | 搜索区 | 文字: "重置" |
| `btn-add` | 新增资质按钮 | `el-button` | 表格上方操作栏 | **权限点** |
| `table-qualification` | 资质列表表格 | `el-table` | 主内容区 | |
| `th-name` | 表头: 资质名称 | `el-table-column` | 表格 | 文本类型 |
| `th-type` | 表头: 资质类型 | `el-table-column` | 表格 | 标签类型 (el-tag) |
| `th-issuer` | 表头: 发证机关 | `el-table-column` | 表格 | 文本类型 |
| `th-obtain-date` | 表头: 获得日期 | `el-table-column` | 表格 | 日期类型 |
| `th-expiry-date` | 表头: 有效期至 | `el-table-column` | 表格 | 日期类型，过期行标红 |
| `th-status` | 表头: 状态 | `el-table-column` | 表格 | el-tag (颜色区分) |
| `th-action` | 表头: 操作 | `el-table-column` | 表格 | 操作按钮列 |
| `btn-edit` | 编辑按钮 (行内) | `el-button link` | 表格-操作列 | **权限点** |
| `btn-delete` | 删除按钮 (行内) | `el-button link danger` | 表格-操作列 | **权限点** |
| `btn-view` | 查看详情按钮 (行内) | `el-button link` | 表格-操作列 | |
| `pagination` | 分页组件 | `el-pagination` | 页面底部 | 默认10条/页 |
| `dialog-qualification` | 新增/编辑资质弹窗 | `el-dialog` | 弹窗层 | title动态: "新增资质"/"编辑资质" |
| `dialog-name` | 弹窗: 资质名称 | `el-input` | 弹窗-表单 | 必填 |
| `dialog-type` | 弹窗: 资质类型 | `el-select` | 弹窗-表单 | 必填 |
| `dialog-issuer` | 弹窗: 发证机关 | `el-input` | 弹窗-表单 | 必填 |
| `dialog-obtain-date` | 弹窗: 获得日期 | `el-date-picker` | 弹窗-表单 | |
| `dialog-expiry-date` | 弹窗: 有效期至 | `el-date-picker` | 弹窗-表单 | |
| `dialog-remark` | 弹窗: 备注 | `el-input` type="textarea" | 弹窗-表单 | |
| `dialog-upload` | 弹窗: 上传附件 | `el-upload` | 弹窗-表单 | |
| `dialog-save` | 弹窗: 保存按钮 | `el-button` primary | 弹窗-底部 |
| `dialog-cancel` | 弹窗: 取消按钮 | `el-button` | 弹窗-底部 |

### 页面状态与权限

| 状态/权限 | 描述 | 验证要点 |
|-----------|------|----------|
| **加载中** | 表格显示 `v-loading` 动画 | 等待 loading 消失 |
| **空数据** | 表格显示空状态插槽 "暂无数据" | 定位 `el-empty` 组件 |
| **错误状态** | 接口返回 500 时，可能出现错误提示 | 观察 Toast |
| **权限-隐藏按钮** | 无权限时 `btn-add`, `btn-edit`, `btn-delete` 应隐藏 | 检查元素是否存在 |
| **权限-只读** | 无编辑权限时，点击行内按钮可能提示无权限 | 检查 Toast 提示 |

---

## 输出：PAGE_ELEMENT_POSITION.md（定位器设计）

> **注意**: 以下定位器基于通用 Element Plus 结构设计。**强烈建议**基于实际 HTML 源码优化。

| 元素ID | 定位策略 (A级优先) | 定位值 (示例) | 稳定性评级 | 备用方案 (B/C级) |
|--------|--------------------|---------------|------------|------------------|
| `search-name` | `By.CSS_SELECTOR` | `input[placeholder='请输入资质名称']` | A | 若多个，加 `.el-form-item` 限制 |
| `search-type` | `By.CSS_SELECTOR` | `.el-select.xxx .el-input__inner` | B | 使用 `XPath: //label[text()='资质类型']/following::input[1]` (C级) |
| `btn-add` | `By.XPATH` | `//button/span[contains(text(),'新增资质')]` | B | 优先找 `data-testid` 或 id (A级) |
| `table-qualification` | `By.CSS_SELECTOR` | `.el-table` | A | 若多表格，按 `tbody` 或父容器区分 |
| `th-name` | `By.CSS_SELECTOR` | `.el-table__header-wrapper th:contains('资质名称')` | B | **注意**: `:contains()` 不被部分浏览器支持，建议用 `XPath` |
| `th-name-alt` | `By.XPATH` | `//div[@class='el-table__header-wrapper']//th//span[text()='资质名称']` | B | 稳定 |
| `btn-edit` | `By.XPATH` | `//tr[...]//button/span[text()='编辑']` | C | 依赖行索引 `(//tr[@class='el-table__row'])[1]` |
| `btn-delete` | `By.XPATH` | `//tr[...]//button/span[text()='删除']` | C | 同上 |
| `dialog-name` | `By.CSS_SELECTOR` | `.el-dialog .el-form-item:has(label:contains('资质名称')) input` | B | 直接使用 `XPath: //div[@class='el-dialog']//label[text()='资质名称']/following::...` |
| `dialog-save` | `By.CSS_SELECTOR` | `.el-dialog__footer .el-button--primary` | B | 若多个弹窗同时打开，优先按 `XPath: //span[text()='确 定']` (C级) |
| `pagination` | `By.CSS_SELECTOR` | `.el-pagination` | A | 定位到元素后，获取 `el-pagination__total` |
| `TOAST` (成功/失败) | **使用 BasePage 通用** | - | A | BasePage 已定义常见 Toast 定位器 |

### 重要注意事项

1.  **等待策略**:
    - 表格加载: `WebDriverWait(driver).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-loading-mask")))`
    - 弹窗打开: `WebDriverWait(driver).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".el-dialog")))`
    - 下拉选项展开: `WebDriverWait(driver).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".el-select-dropdown__item")))`

2.  **弹窗复用**:
    - 新增和编辑共用一个 `el-dialog`，区别在于 `dialog-title` 是否为“编辑”。建议通过 `dialog-title` 文本来判断模式。

3.  **权限校验**:
    - 建议在登录时获取用户权限列表。测试用例中，针对权限按钮使用 **自定义 Attribute** (`data-permission`) 或 **CSS class** (如 `.permission-hidden`) 作为 A级定位器，而不是直接通过文字定位。**`btn-add` 应优先推荐使用这个自定义属性**。

4.  **表格行操作**:
    - 不建议通过行索引定位（增删改后索引会变）。
    - 更稳定的方法是: 在表格中找**唯一文本列**（如资质名称），然后从其所在行获取操作按钮。
    - 示例: `//tr[.//div[contains(text(), '{{资质名称}}')]]//button/span[text()='编辑']`

---

**接下来，请提供以下任意一项，我将为你生成精确的页面分析：**

1.  页面截图（1-3张，覆盖列表、搜索、弹窗）
2.  页面关键区域的HTML源码（特别是表格、搜索框、弹窗部分）
3.  该页面的Page Object代码（如果有初始版本）