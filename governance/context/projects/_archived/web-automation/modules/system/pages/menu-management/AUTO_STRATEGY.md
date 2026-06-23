# AUTO_STRATEGY — system-management / menu-management

> 基于 TECH_ANALYSIS + TEST_CASES | 2026-06-12
> RBAC权限标识配置源。树形表格，PC/小程序双Tab，3种菜单类型(M/C/F)

## 自动化目标
覆盖菜单管理的树形展示、搜索过滤、展开/收起、新增3种类型节点(M/C/F)、编辑、删除。跨模块验证（权限标识→角色权限弹窗）后续补充。

## 覆盖矩阵

| 用例编号 | 标题 | 优先级 | 自动化 | 理由 |
|----------|------|--------|--------|------|
| TC-MENU-001 | 页面正常加载 | P0 | ✅ | 冒烟 |
| TC-MENU-002 | 权限标识生效验证 | P0 | ❌ | 跨模块（→角色管理），待开发 |
| TC-MENU-003 | 表头完整性 | P1 | ✅ | 8列 |
| TC-MENU-004 | PC/小程序Tab切换 | P1 | 🔄 | |
| TC-MENU-005 | 树节点默认展开 | P1 | ✅ | |
| TC-MENU-006 | 菜单名称搜索 | P1 | ✅ | A级placeholder |
| TC-MENU-007~008 | 展开/收起全部 | P1 | ✅ | |
| TC-MENU-009 | 新增弹窗打开 | P1 | ✅ | |
| TC-MENU-010 | 必填项校验 | P1 | 🔄 | |
| TC-MENU-011~013 | 新增目录/菜单/按钮(3条) | P1 | ✅ | M/C/F三种类型 |
| TC-MENU-014 | 取消新增 | P1 | ✅ | |
| TC-MENU-015~017 | 编辑(回显/保存/取消) | P1 | ✅ | |
| TC-MENU-018~019 | 删除/P2边缘 | P2 | ❌/🔄 | |

## PageObject 拆分

```
MenuManagePage  ← 搜索区 + 树形表格 + PC/小程序Tab + CRUD弹窗（重构版，继承BasePage）
  ├── 搜索/工具栏：名称搜索 + 展开/收起全部 + 新增
  ├── Tab切换：PC端菜单 / 小程序菜单
  ├── 树形表格：8列（名称/图标/排序/权限标识/组件路径/状态/创建时间/操作）
  ├── 弹窗：新增/编辑（名称/类型(M/C/F)/上级菜单/权限标识/路径/图标/排序/状态）
  └── 4级fallback：弹窗确定按钮覆盖多种DOM结构
```

## 公共组件复用

| 方法 | 来源 | 复用状态 |
|------|------|----------|
| navigate_to("系统管理", "菜单管理") | BasePage | ✅ |
| wait_page_ready() | BasePage | ✅ |
| _wait_loading_gone() | BasePage | ✅ |
| wait_vue_stable() | BasePage | ✅ |

## ROI 分析

| 指标 | 值 |
|------|----|
| 已投入开发时间 | ~1.5 小时（重构版PO + 18用例） |
| 维护成本 | ~0.3 小时/月（菜单结构变更少） |
| 手工执行时间 | 15 分钟/次 |
| 当前状态 | 稳定（重构完成，去绝对XPath+time.sleep） |

## 在RBAC体系中的位置

```
菜单管理（本页面）
  └── 定义权限标识（system:user:list, system:user:add...）
        └── 角色管理 → 权限分配弹窗 → 勾选权限标识
              └── 用户管理 → 分配角色 → 用户获得权限
```

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 | next_phase: Phase 4 | next_agent: automation-agent -->
