# Skill: hygiene-check

> 目录/文件级卫生检查 — project-agent 的第 4 个 Skill。覆盖重复检测、废弃标记、大文件告警、孤儿引用、格式漂移、Token 预算。
> 创建: 2026-06-15 | 基于 SOP 体系审计 + Context Cost 审计的经验沉淀

## 目标
扫描项目目录和治理文件，识别文件级卫生问题。与 `completeness-check`（内容完整性）互补——本 Skill 关注文件本身的健康度，不关注内容质量。

## 输入
- 项目根目录（默认 `d:\Desktop\WorkStudy`）
- 可选 `--module=<m>` 限定范围
- 可选 `--check=<c>` 指定单项检查

## 输出
- `governance/artifacts/audits/HYGIENE_REPORT_<timestamp>.md` — 完整卫生报告
- 每项检查有 PASS/FAIL/WARN 状态
- Token 预算排名 TOP 10

## 六项检查

### 1. 重复文件检测
- 扫描 `governance/skills/`、`governance/agents/`、`.claude/skills/`
- 规则: 同名文件在不同目录 → 标记；bit-for-bit 完全相同 → 严重
- 排除: `_archived/`、`_deprecated/`（已知历史存档）

### 2. 废弃文件识别
- 规则: `_deprecated/` 目录中的文件 → WARN（超过 14 天建议删除）
- 规则: 超过 30 天未修改且不在任何 registry 中引用的 `.md` → WARN
- 规则: `.workflow.js` 文件但不在 workflow-registry.yaml 中 → WARN

### 3. 大文件告警
- 规则: Skill 文件 > 10K chars → FAIL（应拆分）
- 规则: PAGE_INTERFACE.yaml > PAGE_CONTEXT.md → WARN（优化失效）
- 规则: Template 文件 > 5K chars → WARN
- 规则: 任何 `.md` > 50K chars → FAIL（应归档或拆分）

### 4. 孤儿引用清理
- 规则: `skill-registry.yaml` 中 `file:` 指向不存在的路径 → FAIL
- 规则: `workflow-registry.yaml` 中 `artifacts:` 指向不存在的路径 → WARN
- 规则: `.claude/skills/*/SKILL.md` 中 `source:` 引用不存在的文件 → WARN
- 规则: `agent-definitions.yaml` 中 `skills:` 引用的 skill ID 不在 registry 中 → FAIL

### 5. 格式漂移检测
- 规则: `SOP_STATUS_*.json` 的 `completed_phases` 包含非规范 PhaseName → FAIL
- 规则: `PAGE_INTERFACE.yaml` 的 `meta.module` 值与文件路径不一致 → WARN
- 规则: SOP_STATUS 同时存在于 `artifacts/sop-status/` 和 `modules/` → FAIL
- 规则: `CANONICAL_PHASES` 在 `state.py` 和 `sop_validator.py` 中不一致 → FAIL

### 6. Token 预算报告
- 统计 `CLAUDE.md` + Memory 文件（自动注入层）
- 统计 `.claude/skills/` 总计（按需加载层）
- 统计 `governance/skills/` 按 category 分类统计
- 统计 `PAGE_INTERFACE.yaml` vs `PAGE_CONTEXT.md` 对比
- 输出 TOP 10 Token 消耗源

## 依赖
- `governance/skills/skill-registry.yaml`
- `governance/workflows/workflow-registry.yaml`
- `governance/agents/agent-definitions.yaml`
- `governance/context/source-of-truth.md`
- `aitest/graphs/state.py` (CANONICAL_PHASES)

## 边界
- 本 Skill 只检查文件级问题，不检查内容质量（那是 `completeness-check` 的职责）
- 不自动修复问题（修复需人工判断）
- 不删除文件（仅标记建议）

---

## Prompt 模板

### 全项目卫生检查

```text
你是项目文件卫生审计专家。对 AITest Platform 项目执行全面卫生检查。

## 项目根目录
d:\Desktop\WorkStudy

## 检查步骤

### Step 1: 重复文件检测
Glob 扫描 `governance/skills/` 和 `governance/skills/_deprecated/`：
- 列出所有同名文件（出现在不同目录中）
- 对同名文件对，Read 前 500 chars 比较 — 如果内容相同，标记为 SEVERE

### Step 2: 废弃文件识别
- Glob `governance/agents/_deprecated/` 和 `governance/skills/_deprecated/` — 统计文件数和总大小
- Glob `*.workflow.js` 文件，对比 `governance/workflows/workflow-registry.yaml` — 列出未注册的

### Step 3: 大文件告警
- Bash: `find governance/skills -name "*.md" -exec wc -c {} + | sort -rn | head -20`
- 标记超过 10,000 chars 的 skill 文件
- 对于每个 PAGE_INTERFACE.yaml，与其同级 PAGE_CONTEXT.md 比较大小

### Step 4: 孤儿引用
- Read `governance/skills/skill-registry.yaml` — 逐条检查 `file:` 路径是否存在
- Read `governance/agents/agent-definitions.yaml` — 逐 Agent 检查 `skills:` 列表是否都在 registry 中注册

### Step 5: 格式漂移
- Read `aitest/graphs/state.py` 提取 CANONICAL_PHASES
- Read `governance/validators/sop_validator.py` 提取 CANONICAL_PHASES
- 比较是否一致
- 对每个 `governance/artifacts/sop-status/SOP_STATUS_*.json`，检查 `completed_phases` 中的名称是否都在 CANONICAL_PHASES 中

### Step 6: Token 预算
- 统计 `CLAUDE.md` 的字符数
- 统计 `.claude/skills/*/SKILL.md` 的总字符数
- 统计 `governance/skills/**/*.md` 按子目录分类的字符数
- 统计所有 `PAGE_INTERFACE.yaml` 的总字符数和平均大小
- 统计所有 `PAGE_CONTEXT.md` 的总字符数和平均大小
- 输出 TOP 10

## 输出格式

```markdown
# Hygiene Check Report — <timestamp>

## Summary
| Check | Status | Issues |
|-------|--------|--------|
| 1. Duplicate files | PASS/FAIL | N issues |
| 2. Stale files | PASS/FAIL | N issues |
| 3. Oversized files | PASS/FAIL | N issues |
| 4. Orphan references | PASS/FAIL | N issues |
| 5. Format drift | PASS/FAIL | N issues |
| 6. Token budget | INFO | TOP 10 |

## 1. Duplicate Files
...

## 6. Token Budget
| Rank | File | Chars | ~Tokens | Load Frequency |
|------|------|-------|---------|---------------|
```

完成后汇报 JSON:
```json
{
  "checks": {
    "duplicates": {"status": "pass|fail", "issues": 0},
    "stale": {"status": "pass|fail", "issues": 0},
    "oversized": {"status": "pass|fail", "issues": 0},
    "orphans": {"status": "pass|fail", "issues": 0},
    "format_drift": {"status": "pass|fail", "issues": 0},
    "token_budget": {"total_chars": 0, "top10": []}
  },
  "report_path": "governance/artifacts/audits/HYGIENE_REPORT_<timestamp>.md"
}
```
```

### 单模块快速检查

```text
对 {{module}} 模块执行快速卫生检查。

## 检查范围
1. `governance/context/projects/web-automation/modules/{{module}}/` 下:
   - 是否有 SOP_STATUS 残留（应在 artifacts/sop-status/）
   - PAGE_INTERFACE.yaml 是否比 PAGE_CONTEXT.md 更大
2. `governance/artifacts/sop-status/SOP_STATUS_{{module}}.json`:
   - completed_phases 是否使用规范名称
   - 是否有空的 completed_phases

输出: 简短报告 + 建议修复项
```

---

## 检查清单
- [ ] 重复文件: 同名文件已比较内容，bit-for-bit 相同已标记 SEVERE
- [ ] 废弃文件: _deprecated/ 统计完成，超过 14 天的已标记可删除
- [ ] 大文件: >10K skill / >5K template / >50K md 已标记
- [ ] 孤儿引用: registry → file 路径全部验证
- [ ] 格式漂移: CANONICAL_PHASES 一致性、SOP_STATUS 规范性已检查
- [ ] Token 预算: TOP 10 已输出，含加载频率估算
- [ ] 报告已写入 `governance/artifacts/audits/HYGIENE_REPORT_<timestamp>.md`

## 产出物
→ `governance/artifacts/audits/HYGIENE_REPORT_<timestamp>.md`
→ 报告包含 6 项检查的 PASS/FAIL 状态 + 具体问题清单 + Token 预算 TOP 10
