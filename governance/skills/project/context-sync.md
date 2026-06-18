# Skill: context-sync

## 目标
在协作结束后完成事实更新建议、产物归档建议和待办同步。

## 输入
- 本轮会话记录
- 新增事实
- 新增分析文档
- 新增脚本或配置

## 输出
- 建议更新的上下文文件
- 应归档的产物
- 下一步待办

## 规则
- 稳定事实进入 context/
- 过程产物进入 artifacts/
- 迁移动作进入 docs/integration/MIGRATION_MAP.md

---

## Prompt 模板

> 以下 Prompt 可直接复制到 AI 对话中使用。替换 `{{ }}` 占位符即可。

### 会话开始 — 上下文恢复

```text
我正在继续 {{模块名}} 的测试工作。

## 第 1 步：读取 CURRENT_TASK（如果有）
→ 读取 governance/context/projects/web-automation/modules/{{module}}/CURRENT_TASK.md
→ 如果存在，自动恢复：当前 Phase / 已完成步骤 / 阻塞项 / 关键决策 / 产出文件清单

## 第 2 步：按需加载 Context
根据 CURRENT_TASK 中的"下一会话恢复指南"，按需加载需要的文档：
→ PROJECT_CONTEXT（如需要 BasePage API / 编码规范）
→ MODULE_CONTEXT（模块边界 + 业务流程）
→ PAGE_CONTEXT / RISK_MODEL / TEST_DESIGN / TEST_CASES（根据当前 Phase）

## 第 3 步：确认理解
1. 总结你对当前模块/页面的理解（确认理解正确）
2. 列出 CURRENT_TASK 中记录的已完成 Phase
3. 确认当前 Phase 的下一步操作
4. 等我确认后继续

## 兜底：如果没有 CURRENT_TASK
```
我在继续 {{模块}} 的工作，需求是 {{描述}}。请先阅读以下上下文：
1. PROJECT_CONTEXT: {{粘贴}}
2. MODULE_CONTEXT: {{粘贴}}（如有）
3. 当前进度: Phase {{N}} — {{描述}}
```
```

### 会话结束 — 上下文同步 + CURRENT_TASK 写回

```text
本次会话即将结束，请帮我做上下文同步。

## 本次变更摘要
- 新增/修改文件：
  - {{contexts/equipment/pages/alarm-config/PAGE_CONTEXT.md}} — 补充了搜索区元素
  - {{contexts/equipment/pages/alarm-config/TEST_DESIGN.md}} — 新增15条测试设计
- Phase 进展：{{Phase 1 → Phase 2 完成}}
- 关键决策：{{如：搜索区使用模糊匹配而非精确匹配}}
- 遗留问题：{{如：弹窗中的动态下拉框定位器待确认}}

## 任务
1. **写入/更新 CURRENT_TASK.md**（路径：`governance/context/projects/.../modules/{{module}}/CURRENT_TASK.md`）
   - 使用模板：`governance/templates/current-task.template.md`
   - 必填：当前 Phase / 已完成步骤 / 阻塞项 / 下一会话恢复指南
2. 更新 `测试进度追踪.md` 中对应模块的状态
3. 更新 `MODULE_CONTEXT.md` 中的页面状态标记（✅/🔄/⏳）
4. 生成本次会话的上下文摘要（用于下次会话自动恢复）
5. 区分：稳定事实 → context/ | 过程产物 → artifacts/

## CURRENT_TASK 写回规则
- 每个模块最多一个 CURRENT_TASK.md
- 必须包含"下一会话恢复指南"段落（1句话描述上次操作 + 1句话描述下一步 + 需要的文件列表）
- 阻塞项必须标注严重度（🔴/🟡/🟢）
- 关键决策含原因和影响范围
```

---

## 检查清单

### 会话开始
- [ ] PROJECT_CONTEXT → MODULE_CONTEXT → PAGE_CONTEXT 逐级加载
- [ ] 已确认当前 Phase 和已完成产出
- [ ] 已确认用户意图后再继续
- [ ] 理解了上次会话的遗留问题和关键决策

### 会话结束
- [ ] 新增/修改文件清单完整
- [ ] Phase 进展已记录
- [ ] 关键决策已记录（含原因）
- [ ] 遗留问题已标注（含责任人/预期解决时间）
- [ ] 进度追踪和 MODULE_CONTEXT 状态已更新
- [ ] 稳定事实 vs 过程产物已分流
- [ ] 下次会话建议入口已产出

---

## 产出物
→ 上下文更新建议 + 归档建议 + 待办清单。
→ 输出格式参见 `templates/session-sync.template.md`。
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | project | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->