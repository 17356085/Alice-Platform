---
name: continue
description: 恢复工作 — 新会话启动后输入 /continue 即可自动发现进度并接手。扫描 SOP_STATUS 找到最近未完成模块，自动定位中断点。
disable-model-invocation: false
---

# /continue — 恢复工作

自动发现上次做到哪了，给出下一步行动建议。不需要你记住模块名或 Phase。

## 步骤

### Step 1: 扫描 SOP_STATUS（主要恢复路径）

按优先级扫描以下路径（ADR-001 `.tlo/` 优先）:

1. Glob `{project_root}/.tlo/runtime/sop-status/SOP_STATUS_*.json`（新 .tlo/ 项目）
2. Glob `governance/artifacts/sop-status/{project_id}/SOP_STATUS_*.json`（per-project legacy）
3. Glob `governance/artifacts/sop-status/SOP_STATUS_*.json`（legacy flat，仅 web-automation）

对每个文件，Read 并提取:
- `module`: 模块名
- `status`: completed | in_progress | failed | completed_with_issues
- `completed_phases`: 已完成的规范 PhaseName 列表
- `updated_at`: 最后更新时间
- `next_steps`: 如果有

按 `updated_at` 倒序排列。筛选 `status != "completed"` 的模块 → 这些是"未完成的"。

筛选 `status == "completed"` 但 `completed_phases` 缺少某些 Phase 的 → 这些是"有缺口的"。

### Step 2: 对比规范 Phase 列表

规范 Phase 顺序（与 `aitest/graphs/state.py` CANONICAL_PHASES 一致）:
```
Project Init → Requirement → Test Design → Automation → Execute & Debug
  → Bug Analysis → Data Sanitization → Report → Knowledge
```

对每个未完成模块，判断:
- 下一个应执行的 Phase = CANONICAL_PHASES 中第一个不在 `completed_phases` 中的
- 推荐命令: `/full-sop module=<module> mode=resume`（会从断点继续）
- 或者: 直接调用对应的单个 Agent

### Step 3: 输出恢复建议

```
📋 发现 <N> 个可恢复的模块:

🔴 未完成:
  <module> — 停在 <current_phase>，下一步: <next_phase>
  → /full-sop module=<module> mode=resume

🟡 有缺口:
  <module> — 已完成 <N>/9 Phase，缺: <missing_phases>
  → /full-sop module=<module>

🟢 已完成:
  <module> — 全部 9 Phase 完成
  → /full-sop module=<module> (补充缺失 Phase) 或 /full-sop module=<module> mode=resume (回归)
```

如果有 `next_steps` 字段，直接引用原文。

### Step 4: 兜底 — Memory 文件

如果 `governance/artifacts/sop-status/` 下无文件或全部为空:
- 读 `memory/self-hosted-chat-agent-status.md`（测试工作台状态）
- 读 `memory/dev-agent-ecosystem-phase1.md`（开发 Agent 体系）
- 基于 Memory 内容给出建议

## 边界

- ✅ 扫描 SOP_STATUS，自动定位中断点
- ✅ 推断下一步操作，给出可直接执行的命令
- ❌ 不自动执行（等你确认）
- ❌ 不修改任何文件

## 产出物

→ 终端输出: 模块恢复建议 + 可复制粘贴的命令。
