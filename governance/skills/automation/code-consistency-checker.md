# Skill: code-consistency-checker

> **P2-7 (2026-06-13): 双模式明确化**
> 
> 本 Skill 有两种执行模式，由调用方决定:
> 
> | Mode | 执行方式 | Token | 用途 |
> |------|---------|:-----:|------|
> | `mechanical` (默认) | grep 扫描，不调 LLM | 0 | 快速检查 8 条红线，CI/pre-commit 用 |
> | `review` | LLM 对抗性审查 | ~2K | 深度审查定位器稳定性、等待策略、断言充分性 |
> 
> `AgentLoop` 在 `automation-agent` 的 `observe()` 阶段默认执行 `mechanical` 模式。
> `review` 模式由 LangGraph 编排层按需调用（如 `automation_review` 节点）。

## 目标
检查 Page Object 和测试脚本是否遵循 `PROJECT_CONTEXT.md` 中的编码强制规范，输出逐项合规报告和自动修复建议。

## 输入
- Page Object 文件（`.py`）或测试脚本文件路径
- `PROJECT_CONTEXT.md`（§ 编码强制规范 + § 禁止模式 + § Element Plus 已知坑位清单）

## 输出
- 逐项合规检查表（✅/❌/⚠️）
- 违规项的具体位置（文件名:行号）
- 自动修复建议代码
- 总体合规度评分（0-100%）

## 规则
- 所有检查项来源于 `PROJECT_CONTEXT.md`，不在本 Skill 中重复定义规则
- 对每个违规项必须给出"当前代码 → 修复后代码"对比
- 检查结果分三级：✅ 通过 / ⚠️ 警告（不影响运行但不符合最佳实践） / ❌ 违规（阻塞合并）
- 若文件不存在或无法解析，输出错误信息而非空报告

## 依赖
- `governance/context/projects/web-automation/coding-standards.md`（8 条红线 + PageObject 规范 + 测试脚本规范 + 禁止模式）
- `governance/context/projects/web-automation/element-plus-pitfalls.md`（EP 坑位快速索引）
- `governance/context/projects/web-automation/test-data-policy.md`（数据清理规范：谁创建谁清理、注册胜于遗忘、清理失败不阻塞、可识别前缀）
- `ZJSN_Test-master526/base/base_page.py`（参考 BasePage API）
- `ZJSN_Test-master526/config/cleanup.py`（CLEANUP_CONFIG：batch_clean_urls, max_residual_allowed, skip_patterns）

## 边界
- 本 Skill 只做合规检查，不修改代码（修改由人工或 code-generation Skill 执行）
- 不检查业务逻辑正确性
- 不检查 Page Object 的定位器是否仍然有效（那是 bug-analysis 的职责）

---

## Prompt 模板

### 单文件合规检查

```text
你是自动化测试代码规范审查专家。严格按照 coding-standards.md 逐项检查以下代码。

## 检查项来源
Read `governance/context/projects/web-automation/coding-standards.md` — 所有检查项（8 条红线 + PageObject 规范 8 项 + 测试脚本规范 6 项 + 禁止模式 6 项）来源于此文件。
Read `governance/context/projects/web-automation/element-plus-pitfalls.md` — 对照 EP 坑位清单检查代码是否涉及受影响组件。

## 待检查代码
```python
{{粘贴待检查的 Page Object 或测试脚本}}
```

## 任务
输出完整的合规检查报告：

### 1. Page Object 规范检查（仅对 Page Object 文件，8 项参见 coding-standards.md §Page Object 规范）
### 2. 测试脚本规范检查（仅对测试脚本，6 项参见 coding-standards.md §测试脚本规范）
### 3. 禁止模式检查（6 项参见 coding-standards.md §禁止模式）
### 4. Element Plus 坑位检查（对照 element-plus-pitfalls.md 快速索引）
### 5. 数据清理合规性检查（对照 test-data-policy.md + config/cleanup.py）
   - **❌ 红线: 无清理逻辑** — 测试脚本有写操作（`.create()` / `.add()` / `.insert()` / `.post()` / `.save()` / `page.xxx_form.submit()`）但无 `from base.cleanup_tracker import get_cleanup_tracker` 或 `tracker.register()` 调用
   - **⚠️ 警告: 清理失败抛异常** — `tracker.register()` 在 try/except 中，except 块 `raise` 而非 `logger.warning`
   - mechanical 快速扫描: `grep -L "get_cleanup_tracker" $(grep -l "\.\(create\|add\|insert\|post\|save\)(" script/*/test_*.py) 2>/dev/null`
### 6. 合规度总评（通过/警告/违规 + 百分比）
### 7. 修复建议（每个 ❌ 违规项给出"当前代码→问题说明→修复代码"）
```

---

## 检查清单

- [ ] Page Object 规范 8 项全部检查
- [ ] 测试脚本规范 6 项全部检查（如适用）
- [ ] 禁止模式 6 项全部检查
- [ ] Element Plus 坑位清单已对照
- [ ] **数据清理红线检查**（无清理逻辑 + 清理失败抛异常）
- [ ] 每个 ❌ 违规项有"当前代码→修复代码"对比
- [ ] 合规度评分计算正确
- [ ] 检查结果可直接作为 code-review 评论使用

## 产出物
→ 合规检查报告（Markdown），可直接粘贴到 PR comment 或作为修复任务输入。
→ 规范来源参见 `PROJECT_CONTEXT.md` § 编码强制规范。
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | automation | synced 2026-06-17 16:53

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->