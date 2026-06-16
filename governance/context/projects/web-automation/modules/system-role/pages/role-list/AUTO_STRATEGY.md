# AUTO_STRATEGY — system-role / role-list

> 基于 TECH_ANALYSIS + TEST_CASES + CURRENT_TASK | 2026-06-12
> RBAC 核心回归页面。当前通过率 46.7%（7/15），6 failed 待修复

## 自动化目标
覆盖角色管理的CRUD、搜索筛选、权限分配弹窗交互。分配用户弹窗 + 权限checkbox批量操作后续补充。

## 当前状态：修复优先

> 🔴 6个用例失败（2026-06-11执行），修复后再生成完整覆盖矩阵。

| 优先级 | 修复项 | 影响用例 | 修复方案 | 估时 |
|:--:|------|:--:|------|:--:|
| P0 | `wait_table_ready()` → `wait_page_ready()` | 4个 | 全局替换 | <5min |
| P1 | StaleElement — 状态下拉 | 1个 | 加WebDriverWait | 10min |
| P2 | 编辑Toast为空 | 1个 | 排查弹窗关闭时序 | 20min |

## 覆盖矩阵（修复后目标）

| 用例编号 | 标题 | 优先级 | 自动化 | 理由 |
|----------|------|--------|--------|------|
| TC-ROLE-001 | 页面正常加载 | P0 | ✅ | 冒烟 |
| TC-ROLE-002 | 权限分配弹窗 | P0 | ✅ | RBAC核心 |
| TC-ROLE-003 | 删除关联用户保护 | P0 | ❌ | 待开发 |
| TC-ROLE-004~005 | 名称/编码搜索 | P1 | ✅ | A级定位 |
| TC-ROLE-006 | 状态筛选 | P1 | ⚠️ 修复中 | StaleElement |
| TC-ROLE-007 | 停用筛选 | P1 | 🔄 | |
| TC-ROLE-008 | 重置搜索 | P1 | ✅ | |
| TC-ROLE-009 | 表头完整性 | P1 | ✅ | |
| TC-ROLE-011~015 | 新增CRUD(5条) | P1 | ✅/⚠️ | 依赖wait_page_ready修复 |
| TC-ROLE-016~018 | 编辑CRUD(3条) | P1 | ✅/⚠️ | Toast为空待修复 |
| TC-ROLE-019~021 | 删除(3条) | P1 | ✅ | |
| TC-ROLE-022~023 | 权限分配交互 | P1 | 🔄 | perm-group组件待分析 |
| TC-ROLE-024~027 | P2边缘 | P2 | 🔄/❌ | |

## PageObject 拆分

```
RoleManagePage  ← 搜索区 + 表格 + 分页 + CRUD弹窗（重构版，继承BasePage）
  ├── 搜索区：名称/编码输入 + 状态下拉 + 搜索/重置
  ├── 表格区：6列 + 行操作(权限分配/分配用户/编辑/删除)
  ├── CRUD弹窗：新增/编辑表单（名称/编码/顺序/状态/备注）
  ├── 权限分配弹窗：PC端+小程序+数据权限Tab (待分析)
  └── 分配用户弹窗：el-transfer 双栏穿梭
```

## 公共组件复用

| 方法 | 来源 | 复用状态 |
|------|------|----------|
| navigate_to("系统管理", "角色管理") | BasePage | ✅ |
| wait_page_ready() | BasePage | ⚠️ 修复中 (原wait_table_ready不存在) |
| _wait_loading_gone() | BasePage | ✅ |
| wait_vue_stable() | BasePage | ✅ |

## ROI 分析

| 指标 | 值 |
|------|----|
| 已投入开发时间 | ~2 小时（重构版PO + 15用例） |
| 待修复时间 | ~35 分钟 |
| 维护成本 | ~0.5 小时/月（权限弹窗DOM结构可能调整） |
| 手工执行时间 | 18 分钟/次 |
| 当前通过率 | 46.7% → 修复后预计 80%+ |

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 | next_phase: Phase 4 | next_agent: automation-agent -->
