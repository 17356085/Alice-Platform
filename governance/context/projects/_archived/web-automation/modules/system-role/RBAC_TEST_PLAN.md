# RBAC_TEST_PLAN — 角色权限矩阵测试方案

> **测试目标**: 验证不同角色登录系统后，侧边栏菜单可见性和页面访问权限是否与角色配置一致
> **被测模块**: 系统管理 → 角色管理（权限分配功能）
> **编制日期**: 2026-06-10 | **版本**: V1.0
> **关联文档**: [PROJECT_CONTEXT.md](../../PROJECT_CONTEXT.md) | [sidebar_navigator.py](../../../../../ZJSN_Test-master526/base/sidebar_navigator.py)

---

## 1. 测试目标

| 维度 | 说明 |
|------|------|
| **核心目标** | 验证 RBAC（基于角色的访问控制）权限模型是否正确生效 |
| **子目标 1** | 验证侧边栏菜单按角色权限动态显隐 |
| **子目标 2** | 验证无权限页面的直接 URL 访问被拦截 |
| **子目标 3** | 验证页面内操作按钮（新增/编辑/删除等）按权限点显隐 |
| **子目标 4** | 验证权限变更后即时生效（无需重新登录） |

---

## 2. 权限模型速查

### 2.1 RBAC 链路

```
角色(Role) ──→ 菜单权限(Menu Permissions) ──→ 侧边栏菜单项可见性
    │
    ├──→ 按钮权限(Button Permissions) ──→ 页面内操作按钮显隐
    │
    └──→ 数据范围(Data Scope) ──→ 列表数据过滤
```

### 2.2 系统现有角色

| 角色 | roleCode | 典型权限范围 |
|------|------|------|
| 超级管理员 | `admin` | 全部菜单 + 全部按钮 + 全部数据 |
| 普通管理员 | `commonAdmin` | 大部分系统管理 + 数据范围受限 |
| 部门经理 | `manager` | 审批 + 培训 + 本部门数据 |
| 设备管理员 | `equipment_admin` | 设备管理模块 |
| 设备操作员 | `equipment_operator` | 设备查看 + 维保 |
| 员工 | `yuangong` | 培训考试（Web+小程序） |

### 2.3 侧边栏菜单完整映射（来自 sidebar_navigator.py）

```
系统管理:  用户管理 | 角色管理 | 菜单管理 | 组织管理 | 字典管理 | 参数设置 |
          日志管理→登录日志/操作日志/系统日志 | 定时任务 | 通知管理 | 接口管理 |
          系统监控 | 工作流管理→待我审批/我已审批/我发起的/SAP推送日志/审批链配置

设备管理:  装置台账 | 设备台账 | 传感器管理 | 设备维保 | 摄像头管理 | 关键参数监控 | 设备报警配置

储罐管理:  储罐监控管理 | 储罐日报表

DCS数据:   关键参数监控 | 全部点位 | 常用点位 | 点位配置 | 上传日志

化验室取样: 气体分析→报告单/对比/设计指标 | 水质分析→报告单/对比/设计指标

人员管理:  培训管理→课程/培训计划/题库/试卷/考试/考试记录/考试测评/在线学习/错题本/自主练习/学习记录/个人学习档案/证书
          员工管理 | 岗位管理

生产管理:  日报表管理 | 交接班日报表 | 生产月报表 | 班次班组配置 | 业务类型配置

销售管理:  客户管理 | 合同管理 | 销售订单 | 销售日报表
```

---

## 3. 测试策略

### 3.1 总体策略：混合测试

```
┌─────────────────────────────────────────────────────┐
│  Layer 1: API 层 — pytest 接口测试                    │
│  验证: 后端 GET /api/system/menu/routes 按角色返回    │
│        不同的菜单树                                    │
│  工具: requests + pytest                              │
│  频率: 每次提交                                       │
├─────────────────────────────────────────────────────┤
│  Layer 2: UI 层 — Selenium 端到端                     │
│  验证: 侧边栏实际渲染 + 直接URL访问拦截 + 按钮显隐     │
│  工具: Selenium + Page Object                         │
│  频率: 每次发布前                                     │
├─────────────────────────────────────────────────────┤
│  Layer 3: 手工探索 — 边界/组合场景                     │
│  验证: 多角色叠加、权限变更即时生效、特殊权限组合       │
│  工具: 手工                                           │
│  频率: 每迭代                                         │
└─────────────────────────────────────────────────────┘
```

### 3.2 测试环境准备

| 步骤 | 操作 | 执行人 | 工具 |
|:---:|------|:---:|------|
| 1 | 使用 admin 登录 | 自动化 | Selenium |
| 2 | 创建测试角色（含特定菜单权限） | 自动化 | Selenium → RoleManagePage |
| 3 | 创建测试用户并分配测试角色 | 自动化 | Selenium → UserManagePage |
| 4 | 用测试用户登录 | 自动化 | Selenium → LoginPage |
| 5 | 验证菜单可见性 | 自动化 | JS 提取侧边栏 DOM |
| 6 | 验证直接 URL 访问拦截 | 自动化 | `driver.get()` + 检测重定向 |
| 7 | 清理测试数据（角色+用户） | 自动化 | Selenium teardown |

---

## 4. 测试角色设计

### 4.1 测试角色矩阵

| 测试角色名 | 角色编码 | 分配菜单权限 | 预期可见一级菜单 | 用例编号前缀 |
|------|------|------|------|:---:|
| **RBAC-全权限** | `rbac_full` | 所有菜单 | 全部 8 个一级菜单 | TC-RBAC-01x |
| **RBAC-仅系统管理** | `rbac_sys` | 系统管理（全部子菜单） | 仅「系统管理」 | TC-RBAC-02x |
| **RBAC-仅设备管理** | `rbac_equip` | 设备管理（全部子菜单） | 仅「设备管理」 | TC-RBAC-03x |
| **RBAC-仅人员管理** | `rbac_hr` | 人员管理（培训+员工+岗位） | 仅「人员管理」 | TC-RBAC-04x |
| **RBAC-混合权限** | `rbac_mix` | 系统管理(用户管理+角色管理) + 设备管理(设备台账) + 销售管理(客户管理) | 系统管理+设备管理+销售管理（仅子集） | TC-RBAC-05x |
| **RBAC-零权限** | `rbac_none` | 无任何菜单 | 仅「首页」 | TC-RBAC-06x |
| **RBAC-仅查看** | `rbac_readonly` | 所有菜单（仅 list/view 按钮权限，无 add/edit/remove） | 全部菜单，但操作按钮受限 | TC-RBAC-07x |

### 4.2 测试用户设计

| 测试用户 | 用户名 | 分配角色 | 说明 |
|------|------|------|------|
| RBAC User 1 | `rbac_test_full` | RBAC-全权限 | 全权限验证 |
| RBAC User 2 | `rbac_test_sys` | RBAC-仅系统管理 | 单模块验证 |
| RBAC User 3 | `rbac_test_equip` | RBAC-仅设备管理 | 单模块验证 |
| RBAC User 4 | `rbac_test_hr` | RBAC-仅人员管理 | 单模块验证 |
| RBAC User 5 | `rbac_test_mix` | RBAC-混合权限 | 多模块子集 |
| RBAC User 6 | `rbac_test_none` | RBAC-零权限 | 边界：无权限 |
| RBAC User 7 | `rbac_test_ro` | RBAC-仅查看 | 按钮权限验证 |

---

## 5. 测试用例列表

### 5.1 Layer 1 — 后端 API 权限验证（pytest）

| 用例编号 | 用例标题 | 测试步骤 | 预期结果 | 优先级 |
|:---:|------|------|------|:---:|
| **API-RBAC-001** | admin 获取完整菜单树 | `GET /api/system/menu/routes` (admin token) | 返回全部 ~55 个路由 | P0 |
| **API-RBAC-002** | 单模块角色获取菜单树 | `GET /api/system/menu/routes` (rbac_sys token) | 仅返回系统管理模块路由 | P0 |
| **API-RBAC-003** | 混合权限角色获取菜单树 | `GET /api/system/menu/routes` (rbac_mix token) | 仅返回已授权的 3 个模块子集路由 | P1 |
| **API-RBAC-004** | 零权限角色获取菜单树 | `GET /api/system/menu/routes` (rbac_none token) | 仅返回首页路由 | P0 |
| **API-RBAC-005** | 无权限访问受保护API | 使用 rbac_none token 请求 `GET /api/system/user/list` | 返回 403 Forbidden | P0 |
| **API-RBAC-006** | 只读角色访问写API | 使用 rbac_readonly token 请求 `POST /api/system/user` | 返回 403 Forbidden | P1 |
| **API-RBAC-007** | 权限变更后即时生效 | PUT 修改角色权限 → 该角色用户刷新 → GET menu/routes | 菜单树立即反映变更 | P1 |

### 5.2 Layer 2 — UI 侧边栏可见性验证（Selenium）

| 用例编号 | 用例标题 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
|:---:|------|------|------|------|:---:|
| **TC-RBAC-001** | 全权限角色—侧边栏完整显示 | rbac_test_full 用户已创建 | 1. 以 rbac_test_full 登录<br>2. 提取侧边栏所有可见一级菜单<br>3. 展开系统管理，提取所有子菜单 | 侧边栏显示全部 8 个一级菜单：系统管理/设备管理/储罐管理/DCS数据/化验室取样/人员管理/生产管理/销售管理 | P0 |
| **TC-RBAC-002** | 仅系统管理—侧边栏只显示系统管理 | rbac_test_sys 用户已创建 | 1. 以 rbac_test_sys 登录<br>2. 提取侧边栏一级菜单<br>3. 展开系统管理子菜单 | 仅显示「系统管理」1个一级菜单。展开后显示全部子菜单（用户/角色/菜单/组织/字典/参数/日志/定时任务/通知/接口/监控/工作流） | P0 |
| **TC-RBAC-003** | 仅系统管理—其他模块不可见 | rbac_test_sys 用户已创建 | 1. 以 rbac_test_sys 登录<br>2. 检查侧边栏菜单列表 | 不包含：设备管理、储罐管理、DCS数据、化验室取样、人员管理、生产管理、销售管理 | P0 |
| **TC-RBAC-004** | 仅设备管理—侧边栏只显示设备管理 | rbac_test_equip 用户已创建 | 1. 以 rbac_test_equip 登录<br>2. 提取侧边栏菜单 | 仅显示「设备管理」1个一级菜单，含子菜单：装置台账/设备台账/传感器管理/设备维保/摄像头管理/关键参数监控/设备报警配置 | P0 |
| **TC-RBAC-005** | 仅人员管理—侧边栏只显示人员管理 | rbac_test_hr 用户已创建 | 1. 以 rbac_test_hr 登录<br>2. 提取侧边栏菜单 | 仅显示「人员管理」1个一级菜单 | P1 |
| **TC-RBAC-006** | 混合权限—侧边栏部分显示 | rbac_test_mix 用户已创建 | 1. 以 rbac_test_mix 登录<br>2. 提取侧边栏菜单<br>3. 展开系统管理 | 显示 3 个一级菜单：系统管理（仅用户管理+角色管理2个子菜单）/设备管理（仅设备台账1个子菜单）/销售管理（仅客户管理1个子菜单） | P0 |
| **TC-RBAC-007** | 零权限—侧边栏仅显示首页 | rbac_test_none 用户已创建 | 1. 以 rbac_test_none 登录<br>2. 提取侧边栏菜单 | 仅显示「首页」菜单项，无其他一级菜单 | P0 |
| **TC-RBAC-008** | 默认跳转验证 | rbac_test_none 用户已创建 | 1. 以 rbac_test_none 登录<br>2. 检查当前 URL | 自动跳转到 `#/welcome` 或 `#/` 首页 | P1 |

### 5.3 Layer 2 — 直接 URL 访问拦截验证（Selenium）

| 用例编号 | 用例标题 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
|:---:|------|------|------|------|:---:|
| **TC-RBAC-101** | 无权限角色—直接URL访问被拦截 | rbac_test_sys 已登录 | 1. `driver.get('#/equipment/device')`<br>2. 检查页面行为 | 页面重定向到首页或显示 403/无权限提示；不渲染设备台账页面内容 | P0 |
| **TC-RBAC-102** | 零权限角色—直接URL访问任意模块被拦截 | rbac_test_none 已登录 | 1. `driver.get('#/system/user')`<br>2. `driver.get('#/sales/customer')` | 每次都被重定向到首页或显示无权限提示 | P0 |
| **TC-RBAC-103** | 混合权限角色—有权限URL正常访问 | rbac_test_mix 已登录 | 1. `driver.get('#/system/user')`<br>2. `driver.get('#/equipment/device')`<br>3. `driver.get('#/sales/customer')` | 以上 3 个 URL 均正常渲染页面内容 | P0 |
| **TC-RBAC-104** | 混合权限角色—无权限URL被拦截 | rbac_test_mix 已登录 | 1. `driver.get('#/system/role')`<br>2. `driver.get('#/equipment/sensor')` | 被拦截（#/system/role 未被授权给 rbac_mix） | P1 |
| **TC-RBAC-105** | 有完整子菜单但无叶子菜单—URL访问被拦截 | rbac_test_mix 已登录 | 1. `driver.get('#/system/dict')` | 被拦截（系统管理下仅有用户管理+角色管理授权） | P1 |

### 5.4 Layer 2 — 页面内按钮权限验证（Selenium）

| 用例编号 | 用例标题 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
|:---:|------|------|------|------|:---:|
| **TC-RBAC-201** | 全权限角色—用户管理页按钮完整 | rbac_test_full 已登录 | 1. 导航到 `#/system/user`<br>2. 检查工具栏按钮<br>3. 检查行操作按钮 | 工具栏显示「新增」「导出」「删除」；每行显示「查看」「编辑」「分配角色」「更多」 | P0 |
| **TC-RBAC-202** | 只读角色—用户管理页无编辑按钮 | rbac_test_ro 已登录 | 1. 导航到 `#/system/user`<br>2. 检查工具栏<br>3. 检查行操作 | 「新增」「删除」「编辑」「分配角色」按钮不可见或 disabled；仅显示「查看」「导出」 | P1 |
| **TC-RBAC-203** | 只读角色—直接POST创建用户被拒绝 | rbac_test_ro 已登录 | 1. 通过 JS fetch 发 `POST /api/system/user` | 返回 403 | P1 |
| **TC-RBAC-204** | 混合权限角色—用户管理按钮正确 | rbac_test_mix 已登录 | 1. 导航到 `#/system/user` | 按钮按权限显示（rbac_mix 有 system:user:* 则显示完整按钮） | P1 |

### 5.5 Layer 2 — 数据范围验证（Selenium）

| 用例编号 | 用例标题 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
|:---:|------|------|------|------|:---:|
| **TC-RBAC-301** | 全部数据范围—看到所有用户 | rbac_test_full 登录（数据范围=全部） | 1. 导航到用户管理<br>2. 检查分页总数 | 总数 = 系统全部用户（~151） | P1 |
| **TC-RBAC-302** | 本部门数据范围—仅看到本部门用户 | 创建角色 rbac_dept（数据范围=本部门及下级）+用户 rbac_test_dept（部门=运行二部） | 1. 以 rbac_test_dept 登录<br>2. 导航到用户管理<br>3. 检查列表数据 | 仅显示所属部门「运行二部」及下级的用户 | P2 |

### 5.6 Layer 3 — 手工探索用例

| 用例编号 | 用例标题 | 测试步骤 | 预期结果 | 优先级 |
|:---:|------|------|------|:---:|
| **TC-RBAC-X01** | 多角色叠加—权限取并集 | 创建用户同时分配 2 个角色（rbac_equip + rbac_hr）→ 登录 | 侧边栏同时显示设备管理+人员管理 2 个一级菜单 | P2 |
| **TC-RBAC-X02** | 权限变更后无需重新登录 | admin 修改 rbac_test_sys 的权限（增加人员管理）→ rbac_test_sys 刷新页面 | 侧边栏即时更新，新增人员管理菜单 | P1 |
| **TC-RBAC-X03** | 角色被删除后用户行为 | admin 删除 rbac_equip 角色 → rbac_test_equip 刷新页面 | 设备管理菜单消失；显示无权限提示或仅保留默认权限 | P2 |
| **TC-RBAC-X04** | admin 角色不可被删除/停用 | 尝试在角色管理页删除 admin 角色 | 删除按钮 disabled 或提示"系统内置角色不可删除" | P1 |
| **TC-RBAC-X05** | 空角色（无任何菜单权限） | 用户仅分配一个"无任何菜单权限"的角色 → 登录 | 仅显示首页菜单，其余模块不可见 | P2 |

---

## 6. 测试执行步骤（详细操作指南）

### 6.1 阶段一：测试数据准备（admin 操作）

```
Step 1.1: 以 admin 登录系统
    ├── 打开 https://aiwechatminidemo.cimc-digital.com/
    ├── 输入 admin / Ajyl@2026
    └── 确认进入首页

Step 1.2: 创建测试角色（重复 6 次，对应 rbac_full/sys/equip/hr/mix/none）
    ├── 导航到 系统管理 → 角色管理
    ├── 点击「新增」
    ├── 填写：
    │   ├── 角色名称: "RBAC-全权限"
    │   ├── 角色编码: "rbac_full"
    │   └── 状态: 启用
    ├── 点击「确定」
    ├── 搜索该角色 → 点击「权限」
    ├── 在权限弹窗中：
    │   ├── PC操作权限 Tab → 勾选对应菜单权限（见下表）
    │   ├── 小程序操作权限 Tab → 按需勾选
    │   └── 数据权限 Tab → 选择"全部数据"
    └── 点击「确定」

Step 1.3: 权限勾选对照表
    ┌──────────────┬───────────────────────────────────┐
    │ 测试角色       │ PC操作权限 Tab 需勾选               │
    ├──────────────┼───────────────────────────────────┤
    │ rbac_full    │ 全部菜单（根节点勾选）               │
    │ rbac_sys     │ 仅 系统管理 → 全部子菜单             │
    │ rbac_equip   │ 仅 设备管理 → 全部子菜单             │
    │ rbac_hr      │ 仅 人员管理 → 全部子菜单             │
    │ rbac_mix     │ 系统管理→用户管理+角色管理           │
    │              │ 设备管理→设备台账                    │
    │              │ 销售管理→客户管理                    │
    │ rbac_none    │ 不勾选任何菜单                       │
    │ rbac_readonly│ 全菜单，但仅 list/view 按钮权限       │
    └──────────────┴───────────────────────────────────┘

Step 1.4: 创建测试用户（重复 7 次，对应每个测试角色）
    ├── 导航到 系统管理 → 用户管理
    ├── 点击「新增」
    ├── 填写：
    │   ├── 用户名: "rbac_test_full"
    │   ├── 姓名: "RBAC全权限测试"
    │   ├── 密码: "Ajyl@2026"
    │   ├── 部门: 任意有效部门
    │   └── 角色: 选择"RBAC-全权限"
    └── 点击「确定」
```

### 6.2 阶段二：权限验证（逐用户登录测试）

```
Step 2.1: 退出当前登录
    ├── 点击右上角头像 → 退出登录
    └── 确认回到登录页

Step 2.2: 以测试用户登录
    ├── 输入 rbac_test_sys / Ajyl@2026
    └── 确认进入首页

Step 2.3: 提取侧边栏菜单
    ├── 执行 JS: 提取所有 .el-menu-item 和 .el-sub-menu__title 文本
    └── 与预期菜单列表对比

Step 2.4: 直接 URL 访问验证
    ├── driver.get('#/equipment/device')  ← 应被拦截
    ├── driver.get('#/system/user')      ← 应正常访问
    └── 记录各 URL 的实际行为

Step 2.5: 重复 Step 2.1~2.4，覆盖全部 7 个测试用户
```

### 6.3 阶段三：数据清理

```
Step 3.1: 以 admin 登录
Step 3.2: 删除 7 个测试用户
Step 3.3: 删除 7 个测试角色
Step 3.4: 确认清理完成（搜索验证）
```

---

## 7. 自动化实现指南

### 7.1 架构设计

```python
# 文件结构
ZJSN_Test-master526/
├── script/system/
│   ├── test_role_management.py          # 现有：角色 CRUD
│   └── test_rbac_permission.py          # 新增：权限矩阵验证
├── page/system_page/
│   └── RoleManagePage.py               # 现有：需扩展权限树操作
└── data/fixtures/
    └── rbac_test_roles.json             # 新增：测试角色定义
```

### 7.2 核心测试流程（伪代码）

```python
class TestRBACPermissionMatrix:
    """RBAC权限矩阵端到端测试"""

    # 测试角色定义
    TEST_ROLES = [
        {"name": "RBAC-全权限",   "code": "rbac_full",    "menus": "all"},
        {"name": "RBAC-仅系统管理", "code": "rbac_sys",     "menus": ["系统管理"]},
        {"name": "RBAC-仅设备管理", "code": "rbac_equip",   "menus": ["设备管理"]},
        {"name": "RBAC-仅人员管理", "code": "rbac_hr",      "menus": ["人员管理"]},
        {"name": "RBAC-混合权限",   "code": "rbac_mix",     "menus": [
            "系统管理/用户管理", "系统管理/角色管理",
            "设备管理/设备台账", "销售管理/客户管理"
        ]},
        {"name": "RBAC-零权限",   "code": "rbac_none",    "menus": []},
    ]

    @pytest.fixture(scope="module")
    def rbac_setup(self):
        """模块级 fixture: 创建所有测试角色+用户, teardown 清理"""
        driver = ...  # admin 登录
        created_users = []
        created_roles = []
        try:
            for role_def in self.TEST_ROLES:
                # 创建角色 → 分配权限 → 创建用户
                role_name = create_role_and_assign_permissions(driver, role_def)
                created_roles.append(role_name)
                username = create_user_with_role(driver, role_name)
                created_users.append(username)
            yield {"users": created_users, "roles": created_roles}
        finally:
            # 清理
            for username in created_users:
                delete_user(driver, username)
            for role_name in created_roles:
                delete_role(driver, role_name)

    # ── 侧边栏验证 ──
    @pytest.mark.parametrize("role_code,expected_menus", [
        ("rbac_full",  ["系统管理","设备管理","储罐管理","DCS数据","化验室取样","人员管理","生产管理","销售管理"]),
        ("rbac_sys",   ["系统管理"]),
        ("rbac_equip", ["设备管理"]),
        ("rbac_hr",    ["人员管理"]),
        ("rbac_none",  []),  # 仅首页
    ])
    def test_sidebar_menu_visibility(self, rbac_setup, role_code, expected_menus):
        """验证不同角色登录后侧边栏菜单可见性"""
        driver = login_as(f"rbac_test_{role_code.split('_')[1]}", "Ajyl@2026")
        actual_menus = extract_sidebar_top_level_menus(driver)
        assert set(actual_menus) == set(expected_menus + ["首页"])

    # ── URL 拦截验证 ──
    UNAUTHORIZED_URLS = {
        "rbac_sys":   ["#/equipment/device", "#/sales/customer", "#/tank/monitor"],
        "rbac_equip": ["#/system/user", "#/sales/customer"],
        "rbac_none":  ["#/system/user", "#/equipment/device", "#/sales/customer"],
    }

    @pytest.mark.parametrize("role_code,url", [
        (role, url) for role, urls in UNAUTHORIZED_URLS.items() for url in urls
    ])
    def test_unauthorized_url_redirect(self, rbac_setup, role_code, url):
        """验证无权限角色直接访问URL被拦截"""
        driver = login_as(f"rbac_test_{...}", "Ajyl@2026")
        driver.get(f"https://aiwechatminidemo.cimc-digital.com/{url}")
        time.sleep(2)
        current = driver.current_url
        assert url not in current or "403" in driver.page_source or "无权限" in driver.page_source
```

### 7.3 侧边栏菜单提取函数

```python
def extract_sidebar_top_level_menus(driver):
    """提取侧边栏中所有可见的一级菜单文字"""
    return driver.execute_script("""
        var menus = [];
        // 一级子菜单标题
        var subTitles = document.querySelectorAll(
            '.el-menu > li.el-sub-menu > .el-sub-menu__title span'
        );
        subTitles.forEach(function(s) {
            menus.push(s.innerText.trim());
        });
        // 一级叶子菜单（如"首页"）
        var leafItems = document.querySelectorAll(
            '.el-menu > li.el-menu-item span'
        );
        leafItems.forEach(function(s) {
            var text = s.innerText.trim();
            if (text) menus.push(text);
        });
        return menus;
    """)
```

---

## 8. 测试交付物

| 交付物 | 路径 | 状态 |
|------|------|:---:|
| **本测试方案** | `contexts/system-role/RBAC_TEST_PLAN.md` | ✅ V1.0 |
| **自动化测试脚本** | `script/system/test_rbac_permission.py` | ⏳ 待开发 |
| **测试角色数据定义** | `data/fixtures/rbac_test_roles.json` | ⏳ 待开发 |
| **执行报告模板** | `governance/kpi/reports/system-role/测试报告-system-role.xlsx` | ⏳ 待开发 |

---

## 9. 风险与注意事项

| 风险 | 缓解措施 |
|------|------|
| **权限树操作复杂**: Element Plus Tree 组件在 Selenium 中难以精确定位和勾选 | 使用 JS 直接调用权限保存 API（绕过 UI 树操作），或使用 RoleManagePage 已有的 `select_first_two_permission_checkboxes_in_active_tab` 模式 |
| **测试数据残留**: 测试中途失败可能导致角色/用户未清理 | conftest module teardown 中做防御性清理（按 `rbac_test_*` 前缀搜索并删除） |
| **并发执行冲突**: 多个测试用户同时登录可能触发系统安全策略 | 串行执行角色权限测试，使用 `@pytest.mark.serial` |
| **权限变更延迟**: 后端缓存可能导致权限变更后未即时生效 | 在验证前添加 `time.sleep(2)` 或等待缓存刷新 |
| **admin 账号密码依赖**: 所有数据准备需要 admin 权限 | 使用 .env 注入，CI 环境变量管理 |

---

## 10. 执行计划

| 迭代 | 内容 | 工作量估算 | 负责人 |
|:---:|------|:---:|------|
| **Iter 1 (本周)** | 手工验证 7 个测试角色的侧边栏可见性 + URL 拦截 | 3h 手工 | 测试工程师 |
| **Iter 2 (下周)** | 编写 Layer 2 UI 自动化脚本（侧边栏+URL+按钮） | 8h 开发 | 测试工程师 |
| **Iter 3 (下下周)** | 编写 Layer 1 API 自动化 + 集成到 CI | 4h 开发 | 测试工程师 |
| **Iter 4 (按需)** | 数据范围验证 + 多角色叠加 + 边界场景探索 | 4h 手工 | 测试工程师 |
