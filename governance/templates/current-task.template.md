# CURRENT_TASK — 当前任务状态

> 每个模块会话创建一个 CURRENT_TASK.md，用于跨会话上下文恢复。
> 最后更新：{{date}} | 更新人：{{agent_name}}

---

## 基本信息

| 字段 | 值 |
|------|-----|
| **项目** | web-automation |
| **模块** | {{module_name}} |
| **当前 Phase** | {{current_phase}}（SOP Phase 0~9） |
| **开始日期** | {{start_date}} |
| **最后活动日期** | {{last_active_date}} |
| **状态** | 🔄 进行中 / ✅ 已完成 / ⏸️ 暂停 / ❌ 阻塞 |

## 当前进度

### 已完成 Phase

- [x] **Phase {{N}}** — {{phase_name}} → 产出：{{artifacts}}
- [x] **Phase {{N}}** — {{phase_name}} → 产出：{{artifacts}}

### 当前 Phase

**Phase {{N}} — {{phase_name}}**

| 步骤 | 状态 | 产出/备注 |
|------|------|-----------|
| Step 1: {{step_name}} | ✅/🔄/⏳ | {{output}} |
| Step 2: {{step_name}} | ✅/🔄/⏳ | {{output}} |
| Step 3: {{step_name}} | ✅/🔄/⏳ | {{output}} |

### 待执行 Phase

- [ ] **Phase {{N}}** — {{phase_name}}（预期产出：{{expected}}）

## 当前阻塞项

| 编号 | 描述 | 影响 Phase | 阻塞类型 | 状态 |
|------|------|------------|----------|------|
| BLK-001 | {{描述}} | Phase {{N}} | 缺素材/缺权限/环境问题/待确认 | 🔴/🟡/🟢 |

## 关键决策记录

| 编号 | 日期 | 决策 | 原因 | 影响范围 |
|------|------|------|------|----------|
| DEC-001 | {{date}} | {{decision}} | {{reason}} | {{scope}} |

## 产出文件清单

| 文件 | 路径 | 状态 |
|------|------|------|
| MODULE_CONTEXT.md | context/projects/.../modules/{{module}}/ | ✅ |
| PAGE_CONTEXT.md | context/projects/.../modules/{{module}}/pages/{{page}}/ | 🔄 |
| ... | ... | ... |

## 下一会话恢复指南

1. **上次做到哪了**：{{一句话描述上次最后的操作}}
2. **接下来要做什么**：{{一句话描述接下来第一步}}
3. **需要的上下文文件**：{{列出需要读取的文件路径}}
4. **需要的素材**：{{截图/HTML/API文档/原型}}

---

> 💡 本文件由 context-sync Skill 维护。每次会话结束时更新，每次会话开始时读取。




<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: template-meta -->
> last_verified: 2026-06-17 16:53 | sync_progress.py
<!-- ⚠️ AUTO-GENERATED SECTION END: template-meta -->