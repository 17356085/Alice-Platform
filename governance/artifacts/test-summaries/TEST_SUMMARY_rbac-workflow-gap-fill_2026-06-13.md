# TEST SUMMARY — 角色职权 + 工作流管理 补齐测试

> 2026-06-13 | Phase 1-5 | 补齐核心空白：权限即时生效 + 工作流端到端

## 一、执行摘要

| 指标 | 值 |
| --- | --- |
| 补齐范围 | 角色权限即时生效 (6条) + 工作流端到端 (4条) |
| 新增文件 | 4 个 |
| 新增/修改代码 | ~1,100 行 |
| 新增用例 | 10 条 (P0×3 / P1×6 / P2×1) |
| 首次执行 | 双浏览器基础设施验证通过 ✅ |
| 已知问题 | `select_permission_module` 需匹配 perm-group DOM（已修复 v2） |

## 二、交付物清单

| 类别 | 文件 | 行数 | 说明 |
|------|------|:--:|------|
| **基建** | [conftest_dual.py](ZJSN_Test-master526/script/system/conftest_dual.py) | 94 | 双/三浏览器 fixture (dual_driver, triple_driver) |
| **基建** | [conftest.py](ZJSN_Test-master526/script/system/conftest.py) (修改) | +4 | 注册 pytest_plugins 引入双浏览器 fixtures |
| **基建** | [RoleManagePage.py](ZJSN_Test-master526/page/system_page/RoleManagePage.py) (修改) | +120 | 新增 `click_clear_cache()` + `select_permission_module()` |
| **测试** | [test_rbac_instant_effect.py](ZJSN_Test-master526/script/system/test_rbac_instant_effect.py) | 480 | 权限即时生效 6 条用例 |
| **测试** | [test_workflow_e2e.py](ZJSN_Test-master526/script/system/test_workflow_e2e.py) | 380 | 工作流端到端 4 条用例 |

## 三、测试用例矩阵

### 3.1 角色权限即时生效 (test_rbac_instant_effect.py)

| 编号 | 用例 | 优先级 | 浏览器 | 代码行 | 状态 |
|:--:|------|:--:|:--:|:--:|:--:|
| TC-RBAC-016 | 权限变更 → 清空缓存 → 用户刷新 → 菜单即时生效 | **P0** | 双浏览器 | ~80行 | ✅ 已编写 |
| TC-RBAC-017 | 权限变更 → 不清空缓存 → 菜单不变（反例） | **P0** | 双浏览器 | ~75行 | ✅ 已编写 |
| TC-RBAC-018 | 多角色叠加 → 菜单取并集（API 追加角色） | P1 | 双浏览器 | ~70行 | ✅ 已编写 |
| TC-RBAC-019 | 角色被删除 → 用户权限降级（临时角色闭环） | P1 | 双浏览器 | ~80行 | ✅ 已编写 |
| TC-RBAC-020 | 角色被停用 → 用户菜单消失（临时角色闭环） | P1 | 双浏览器 | ~90行 | ✅ 已编写 |
| TC-RBAC-021 | 内置角色删除保护 | P1 | 单浏览器 | ~40行 | ✅ 已编写 |

### 3.2 工作流端到端 (test_workflow_e2e.py)

| 编号 | 用例 | 优先级 | 浏览器 | 代码行 | 状态 |
|:--:|------|:--:|:--:|:--:|:--:|
| TC-WF-001 | 端到端审批闭环：申请→待审批→审批通过→历史记录 | **P0** | 双浏览器 | ~110行 | ✅ 已编写 |
| TC-WF-002 | 审批驳回流程 | P1 | 双浏览器 | ~50行 | ✅ 已编写 |
| TC-WF-004 | 多级审批基础验证 | P2 | 双浏览器 | ~60行 | ✅ 已编写 |
| TC-WF-005 | 撤回申请 | P1 | 双浏览器 | ~55行 | ✅ 已编写 |

## 四、架构亮点

### 4.1 双浏览器 fixture (conftest_dual.py)

```
dual_driver:
  admin_drv  ← 已登录 admin（操作角色/审批）
  target_drv ← 空白浏览器（由测试用例决定登录哪个用户）

triple_driver:
  admin_drv + user_a + user_b（支持多级审批验证）
```

### 4.2 清空缓存按钮定位

```python
# JS 文本搜索 + 可见性检查 → 全局浮动 danger 按钮
role_page.click_clear_cache()
```

### 4.3 权限模块选择

```python
# 三级降级策略:
#   1. .perm-group__name 精确匹配
#   2. .perm-group textContent 模糊匹配  
#   3. .el-checkbox__label 文本匹配
role_page.select_permission_module("设备管理")
```

### 4.4 API 辅助数据准备

```python
# 浏览器内 fetch API（绕过 UI 权限弹窗复杂度）
# 用于: 角色停用/删除、多角色分配、临时数据创建
api_fetch(driver, "PUT", "/api/system/user/123", body)
```

## 五、首次执行发现

| 发现 | 严重度 | 根因 | 修复 |
|------|:--:|------|------|
| `select_permission_module` 返回 `no_module` | 🔴 阻塞 | JS 查询用 `.el-tree-node` 但实际 DOM 是 `.perm-group` + `.perm-group__name` | 重写 JS → 三级降级策略，优先匹配 `.perm-group__name` |
| 权限树异步渲染 → select 时 DOM 未就绪 | 🟡 时序 | el-tab-pane 切换后 perm-group 异步加载 | 添加 5 次轮询等待 `.perm-group__name` 出现 |
| 双浏览器 teardown 偶发连接拒绝 | 🟢 环境 | Windows Chrome 进程残留 | `conftest_dual._close_all()` 已添加异常保护 |
| Seed 数据权限不完整 | 🟡 已有 | `rbac_seed_clean.py` Phase 3 UI 权限分配不稳定 | 新增测试中 TC-RBAC-019/020 自建临时角色闭环 |

## 六、运行方式

```bash
# 前置：准备测试数据
python script/system/rbac_seed_clean.py

# 冒烟：单浏览器测试
pytest script/system/test_rbac_instant_effect.py::TestRBACInstantEffect::test_rbac_021_builtin_role_delete_protection -v

# 核心 P0：权限即时生效（双浏览器）
pytest script/system/test_rbac_instant_effect.py::TestRBACInstantEffect::test_rbac_016_permission_change_with_cache_clear -v

# 核心 P0：工作流端到端（双浏览器）
pytest script/system/test_workflow_e2e.py::TestWorkflowE2E::test_wf_001_e2e_approval_flow -v

# 全量补齐测试
pytest script/system/test_rbac_instant_effect.py script/system/test_workflow_e2e.py -v
```

## 七、与原测试的关系

```
角色职权:
  原: test_role_management.py (CRUD 15条) + test_rbac_permission.py (静态侧边栏) + test_rbac_check.py
  新: test_rbac_instant_effect.py (动态权限即时生效 6条)
  → 形成完整覆盖：静态验证 + CRUD + 动态权限传播

工作流管理:
  原: test_approval_todo/history/chain/my_application/sap_push_log.py (各页面独立 46条)
  新: test_workflow_e2e.py (跨页面端到端 4条)
  → 形成完整覆盖：页面独立功能 + 端到端业务闭环
```

## 八、遗留项

| 项 | 优先级 | 说明 |
|------|:--:|------|
| Seed 数据重建 | P1 | `rbac_seed_clean.py` Phase 3 权限 UI 分配不稳定，建议改为 API 直接操作 |
| 多级审批完整验证 | P2 | TC-WF-004 当前仅验证审批链配置存在，全流程需要三级浏览器 |
| 审批链参数化验证 | P2 | "配置参数"下拉框的具体业务含义待业务方确认 |
| CI 集成 | P2 | 双浏览器测试耗时长（~2min/用例），建议独立 job 串行执行 |
