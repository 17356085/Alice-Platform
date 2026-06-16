# PAGE_CONTEXT — system-role / role-list

## 基本信息
- 页面ID：system-role | 页面名称：角色管理 | 所属模块：system-role
- 路由：`#/system/role` | PO：`page/system_page/RoleManagePage.py`
- 测试脚本：`script/system/test_role_management.py`
- 页面类型：列表页 + 多弹窗 CRUD + 权限分配弹窗 + 分配用户弹窗

## 页面职责
RBAC 权限体系核心——角色的 CRUD 管理、权限点分配（PC端+小程序端+数据权限）、将角色分配给用户。用户通过角色间接获得菜单/按钮/数据权限。

## 核心元素

### 搜索区
| 元素 | 控件类型 | 定位方式 |
|------|----------|----------|
| 角色名称输入 | el-input | `placeholder="请输入角色名称"` |
| 角色编码输入 | el-input | `placeholder="请输入角色编码"` |
| 状态下拉 | el-select | label="状态" 关联 |
| 搜索按钮 | el-button | `//button[.//span[normalize-space(.)="搜索"]]` |
| 重置按钮 | el-button | `//button[.//span[normalize-space(.)="重置"]]` |

### 工具栏
| 按钮 | 说明 |
|------|------|
| 新增 | 打开新增角色弹窗 |
| 修改 | 选中行后可用 |
| 删除 | 选中行后可用 |

### 表格区
| 列 | 说明 |
|------|------|
| 角色名称 | 文本 |
| 角色编码 | 文本（唯一） |
| 显示顺序 | 数字 |
| 状态 | 启用/停用 |
| 创建时间 | 日期时间 |
| 操作 | 权限分配 / 分配用户 / 编辑 / 删除 |

### 弹窗（3种核心弹窗）
| 弹窗 | 标题 | 说明 |
|------|------|------|
| 新增/编辑角色 | "新增"/"修改" | 角色名称/编码/显示顺序/状态/备注 |
| 权限分配 | "权限分配" | PC端权限(500+checkbox) + 小程序权限 + 数据权限 |
| 分配用户 | "分配用户" | 双栏穿梭框，已分配/未分配用户 |

## 关键交互
- **权限分配链路**：角色管理→权限分配→勾选菜单权限点(目录/菜单/按钮)→保存→用户通过分配角色获得权限
- **分配用户链路**：角色管理→分配用户→双栏选择→保存→用户获得该角色所有权限
- **角色CRUD**：新增/编辑弹窗→表单校验→提交→表格刷新

## 权限与角色
- 可见：admin、具有 `system:role:list` 权限的角色
- 操作：admin（全部）、角色管理员（CRUD + 权限分配）

## 自动化代码
- PO：`page/system_page/RoleManagePage.py`（重构版，继承BasePage，去绝对XPath）
- 测试：`script/system/test_role_management.py`（15用例，7 passed / 6 failed / 2 skipped，待修复）
- CURRENT_TASK：6个失败用例（4个wait_table_ready→wait_page_ready + 1个StaleElement + 1个Toast为空）

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 | next_phase: Phase 1.5 | next_agent: test-design-agent -->
