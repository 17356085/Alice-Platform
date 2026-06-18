> ⚠️ **Agent 说明**：由于无法实际访问文件系统，本输出基于对 `personnel` 模块常见结构的合理推断，所有不确定项均标注了 **「待代码确认」**。  
> 实际使用时，请先执行 `ls page/personnel_page/` 和 `ls script/personnel/` 扫描目录，并读取 2-3 个 Page Object 文件，将本草案中的 `[待确认]` 替换为真实信息。

---

# MODULE_CONTEXT — Personnel（人员管理）

> **生成时间**：2026-06-17 | **状态**：草稿（需代码确认）  
> **维护者**：Requirement Agent  
> **下游文档**：PAGE_CONTEXT（每个子页面）、TEST_DESIGN、TECH_ANALYSIS  

---

## 1. 模块概述

| 项目 | 内容 |
|------|------|
| **模块名** | `personnel` |
| **业务领域** | 人员管理（员工、组织架构、权限人员） |
| **推测路由前缀** | `/personnel` 或 `/system/personnel` **「待确认」** |
| **推测权限要求** | 需登录，可能需 `personnel:view` / `personnel:edit` 等权限 **「待确认」** |
| **UI 技术栈** | Element Plus（符合项目全局技术栈） |

---

## 2. 子页面清单

> **扫描假设**：假设目录下存在以下 Page Object 文件（常见人员管理模块页面）。实际以 `ls page/personnel_page/` 结果为准。

| 页面名称 | Page Object 类 | 推测路由 | PO 状态 | 测试状态 | 备注 |
|---------|---------------|---------|--------|---------|------|
| 人员列表 | `PersonnelPage` | `/personnel` 或 `/personnel/list` | ✅ **「待代码确认」** | ✅ **「待代码确认」** | 列表页，含搜索/分页/操作列 |
| 新增人员 | `PersonnelAddPage` 或 `AddPersonnelPage` | `/personnel/add` | ✅ **「待代码确认」** | 🔄 **「待代码确认」** | 表单页，含基础字段验证 |
| 编辑人员 | `PersonnelEditPage` 或 `EditPersonnelPage` | `/personnel/edit/:id` | ✅ **「待代码确认」** | ❌ **「待代码确认」** | 通常与新增共用表单组件 |
| 人员详情 | `PersonnelDetailPage` | `/personnel/detail/:id` | ⏳ **「待代码确认」** | ❌ **「待代码确认」** | 只读详情页，可能无独立 PO |
| 部门选择 | `DeptSelect`（非独立页面，嵌入表单） | 内嵌 | ⏳ **「待代码确认」** | ❌ **「待代码确认」** | 树形部门选择控件 |

> **状态图标**：✅ = PO + test 都存在，🔄 = 仅有 PO，⏳ = 仅占位（目录或文件名提示）

**实际文件列表**（待扫描后填写）：
```
page/personnel_page/
├── PersonnelPage.py
├── PersonnelAddPage.py
├── PersonnelEditPage.py
├── PersonnelDetailPage.py         # 可能不存在
└── DeptSelectPage.py (or element) # 可能不存在

script/personnel/
├── conftest.py
├── test_personnel_list.py
├── test_personnel_add.py
├── test_personnel_edit.py
└── test_personnel_detail.py
```

---

## 3. 页面关系图

> 基于 PO 中的导航方法推断。**「待代码确认」**

```
[人员列表 PersonnelPage]
      |── 点击「新增」按钮 → 跳转到 [新增人员 PersonnelAddPage]
      |── 点击列表中「编辑」链接 → 跳转到 [编辑人员 PersonnelEditPage]
      |── 点击列表中「详情」链接 → 跳转到 [人员详情 PersonnelDetailPage]（若有）
      |── 搜索/筛选 → 刷新列表（当前页）
```

**典型导航方法（假设）**：
- `PersonnelPage.add_personnel()` → 返回 `PersonnelAddPage`
- `PersonnelPage.edit_personnel(name)` → 返回 `PersonnelEditPage`
- `PersonnelPage.view_detail(name)` → 返回 `PersonnelDetailPage`

---

## 4. 核心数据实体

> 从表单字段/表格列推断 **「待代码确认」**

| 字段名 | 推测类型 | 备注 |
|--------|---------|------|
| 姓名 | 输入框 | 文本，必填 |
| 工号 | 输入框 | 文本，唯一 |
| 手机号 | 输入框 | 数字格式校验 |
| 邮箱 | 输入框 | 邮箱格式校验 |
| 部门 | 树选择 / 下拉框 | 调用部门接口 |
| 岗位 | 输入框 / 下拉框 | 文本或选择 |
| 入职日期 | 日期选择器 | Element Plus DatePicker |
| 状态 | 开关 / 单选 | 启用/禁用 |
| 备注 | 文本域 | |

> 待从 PersonnelAddPage 的实际 locator 和 method 中提取准确字段。

---

## 5. 模块级风险点

> 基于代码实际情况（**待代码审计后确认**）

| 风险类别 | 推测风险点 | 严重程度 | 代码依据（待确认） |
|---------|-----------|---------|------------------|
| **PO 继承** | 所有 PO 是否继承 `BasePage`？若未继承，则缺少通用方法。 | 高 | 检查 `class PersonnelPage(BasePage)` |
| **定位器质量** | 是否大量使用 XPath 而非 CSS？定位器是否硬编码在方法内而非声明为类属性？ | 中 | 检查 `self.find_element(By.XPATH, '//...')` 出现频率 |
| **数据清理** | 新增人员是否在 teardown 中按名称前缀 `TC-` 删除？ | 高 | 检查 `conftest.py` 中的 fixture 清理逻辑 |
| **元素等待** | 是否显式等待 Element Plus 动画（loading/dialog）？ | 中 | 检查 `wait_loading_hide()`、`wait_for_dialog()` 调用 |
| **Fixture 配置** | `conftest.py` 是否正确初始化登录态、driver、页面对象？ | 中 | 检查 fixture scope 和 yield 清理 |
| **多浏览适配** | Element Plus 不同版本下样式差异可能导致定位失败 | 低 | 需检查已知问题列表 |

---

## 6. 自动化价值评估

| 维度 | 评估 | 说明 |
|------|------|------|
| **UI 变更频次** | 中 | 人员管理表单结构相对稳定，但部门树等组件可能随业务调整 |
| **回归工作量** | 高 | 人员管理是核心模块，每次变更需回归列表/增/删/改/查 |
| **现有覆盖率** | **「待代码确认」** | 假设有基础增删改查测试，但可能缺少边界值、权限、并发场景 |
| **性价比** | 高 | 表单字段多、操作链条长（新增→编辑→搜索→删除），自动化收益明显 |
| **建议优先度** | ⭐⭐⭐ | 仅次于登录/基础权限模块 |

---

## 附：待确认事项清单

1. [ ] 实际 Page Object 文件列表（扫描 `page/personnel_page/`）
2. [ ] 实际测试脚本文件列表（扫描 `script/personnel/`）
3. [ ] 每个 PO 类是否继承 `BasePage`？
4. [ ] 路由信息（从 URL 注释或类名推测）
5. [ ] 定位器风格（CSS vs XPath）
6. [ ] 数据清理 fixture 实现
7. [ ] 页面间导航方法（是否返回正确的 PO 实例）
8. [ ] 是否存在 `conftest.py` 及 scope/teardown

> **下一步行动**：执行代码扫描 → 读取 2-3 个代表性 PO 文件 → 更新本文档为最终版。


<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: module-stats -->
<!-- Source: tools/sync_progress.py — regenerated on each SOP run -->
## 自动统计数据 (更新于 2026-06-18 10:54)

| 指标 | 数值 |
|------|:---:|
| 测试文件 | 19 (script/personnel/test_*.py) |
| Page Object | 17 (page/personnel_page/*.py) |
| 治理文档 | 102 .md 文件 |
| TECH_ANALYSIS | 16 |
| AUTO_STRATEGY | 12 |
| RISK_MODEL | 13 |
| PAGE_CONTEXT | 18 |
| SOP 状态 | completed |
| Phase 完成 | Automation, Bug Analysis, Data Sanitization, Execute & Debug, Knowledge, Project Init, Report, Requirement, Test Design |

> 此段由 sync_progress.py 自动更新。手动编辑会被覆盖。
<!-- ⚠️ AUTO-GENERATED SECTION END: module-stats -->