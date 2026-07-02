# 测试模式: 权限矩阵

> 适用: RBAC系统（角色→权限→菜单/按钮） | 来源: system-user/user-list, system-role/role-list

## 权限测试金字塔

```
        ┌──────────┐
        │ URL拦截   │  P0: 无权限角色直接输入路由→拦截
        │          │
       ┌┴──────────┴┐
       │ 菜单可见性  │  P1: 不同角色看到不同菜单项
       │            │
      ┌┴────────────┴┐
      │ 按钮可用性    │  P1: 新增/编辑/删除按钮按角色显示
      │              │
     ┌┴──────────────┴┐
     │ 数据隔离        │  P1: 部门主管仅看本部门数据
     │                │
    ┌┴────────────────┴┐
    │ API层权限         │  P0: 绕过前端直接调API→后端鉴权
```

## 必测场景

| # | 场景 | 验证点 | 自动化 |
|---|------|--------|:--:|
| 1 | 无权限URL直接访问 | 路由守卫拦截或页面仅查看不可操作 | ✅ |
| 2 | 不同角色菜单差异 | admin vs viewer 菜单项不同 | 🔄 |
| 3 | 操作按钮权限 | 无编辑权限角色→编辑按钮不可见 | 🔄 |
| 4 | 数据范围隔离 | 部门主管→仅看本部门 | 🔄 |
| 5 | API鉴权绕过 | 普通用户Token→调管理员API→403 | ❌ |

## 自动化实现

```python
class TestPermissionMatrix:
    def test_url_access_denied(self, driver_setup):
        """无权限角色直接访问URL"""
        driver = login_as("viewer", "password")
        driver.get(BASE_URL + "/#/system/role")
        # 验证: 页面不存在403 OR 仅查看无操作按钮
    
    def test_role_menu_diff(self, admin_page, viewer_page):
        """不同角色看到不同菜单"""
        admin_items = admin_page.get_sidebar_menu_items()
        viewer_items = viewer_page.get_sidebar_menu_items()
        assert len(admin_items) > len(viewer_items)
    
    def test_button_permission(self, page):
        """操作按钮权限控制"""
        assert page.is_element_present(page.ADD_BUTTON) == current_user_has_permission
```

## 数据准备模式

```python
# 创建测试角色→分配权限→分配给用户→切换用户验证
def setup_rbac_test():
    role = api_create_role("TC-测试角色")
    api_assign_permission(role, ["system:user:list"])  # 仅查询
    api_assign_role_to_user("testuser", role)
    return "testuser", "password"
```

## RBAC 关联图

```
角色管理(#/system/role)              用户管理(#/system/user)
┌─────────────────┐                ┌─────────────────┐
│ 权限弹窗(分配权限) │               │ 分配角色弹窗      │
│ ☑ 用户查询       │               │ ☑ 测试角色       │
│ ☐ 用户新增       │  ←── 权限点 ──→│ ☐ 管理员         │
│ ☐ 用户删除       │               │                  │
└─────────────────┘                └─────────────────┘
         │                                  │
         └──── 同一RBAC关系，不同视角 ───────┘
```
