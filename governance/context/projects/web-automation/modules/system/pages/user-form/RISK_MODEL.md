# RISK_MODEL — system-user / user-form (弹窗层)

## 页面/模块
- 名称：用户表单弹窗（新增/编辑/查看/分配角色） | 所属模块：system-user
- 路由：`#/system/user`（弹窗在列表页上打开）
- 关联：user-list（列表页，已有完整7文档）

## 风险清单

| 风险ID | 维度 | 风险描述 | 影响 | 等级 | 缓解措施 | 自动化覆盖 |
|--------|------|----------|------|------|----------|-----------|
| RISK-UF-001 | 业务 | 分配角色弹窗中勾选admin角色导致普通用户提权 | 高 | P0 | 仅admin可见admin角色选项；后端校验不可分配高于自身权限的角色 | ❌ |
| RISK-UF-002 | 业务 | 编辑弹窗中部门/用户类型/岗位/角色/性别均为disabled却可绕过前端直接调API修改 | 中 | P1 | 后端PUT接口同样拒绝修改disabled字段 | ❌ |
| RISK-UF-003 | 数据 | 新增弹窗密码与确认密码不一致仍可提交 | 中 | P1 | 前端实时校验密码一致性；后端二次校验 | ❌ |
| RISK-UF-004 | 数据 | 用户名/手机号重复提交 | 中 | P1 | 后端唯一约束 + 前端异步校验 | ✅ test_user_management |
| RISK-UF-005 | 数据 | 分配角色弹窗17个checkbox全选/全不选的边界（用户无角色） | 中 | P1 | 后端校验用户至少拥有一个角色；前端提示 | ❌ |
| RISK-UF-006 | 接口 | 新增/编辑提交时接口超时，弹窗卡死 | 中 | P1 | 前端超时关闭弹窗+Toast | ❌ |
| RISK-UF-007 | UI/UX | 编辑弹窗13个字段中5个disabled——用户困惑为何不可修改 | 低 | P2 | disabled字段加tooltip说明"请在角色/组织管理中修改" | — |
| RISK-UF-008 | UI/UX | 查看弹窗使用el-descriptions而非form，定位方式不同 | 低 | P2 | PO代码需区分form定位和descriptions定位 | ✅ |

## 高风险路径

- 分配角色 → 勾选admin角色 → 普通用户提权（全链路P0）
- 编辑弹窗 → disabled字段绕过 → API直接修改（需后端校验）

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 | next_phase: Phase 2 | next_agent: test-design-agent -->
