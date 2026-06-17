# Skill: review/memory-quality

### 目标
评估 Claude Memory 质量：是否过期、是否矛盾、是否冗余。输出清理建议。

### 输入
- `C:\Users\17356\.claude\projects\d--Desktop-WorkStudy\memory\` — Memory 目录
- `MEMORY.md` — Memory 索引
- CLAUDE.md — 项目上下文（比对是否重复）

### 输出
- `MEMORY_REVIEW.md`：Memory 质量评分、过期/矛盾/冗余清单

### 规则
- 评估维度：
  1. **过期检测** — Memory 中提到的状态是否仍然成立（如 "Phase 6" 但实际已完成）
  2. **矛盾检测** — 两个 Memory 是否对同一事实有不同说法
  3. **冗余检测** — Memory 是否与 CLAUDE.md 或 governance 文件重复
  4. **链接完整性** — Memory 中 `[[links]]` 是否指向存在的文件
  5. **价值评估** — Memory 是否仍然有参考价值
- 过期标记: content_quality = "outdated" / "superseded"
- 矛盾标记: 两个文件都声明同一事实但值不同

### 依赖
- 需要读取 Memory 目录中的所有文件
- 需要 CLAUDE.md 做冗余对比

### 边界
- 不修改 Memory 文件
- 不删除 Memory 文件
- 只评估不执行清理

### 产出物
- 文件路径: `governance/artifacts/reviews/{{module}}/MEMORY_REVIEW-{{date}}.md`

---

## Prompt 模板

```text
你是一个知识管理专家，专精于 AI Agent Memory 系统的质量维护。

## Memory 清单

### Memory 索引
```
{{MEMORY_INDEX}}
```

### Memory 文件内容摘要
```
{{MEMORY_SUMMARIES}}
```

### 项目 CLAUDE.md 关键事实
```
{{CLAUDE_MD_FACTS}}
```

## 任务

### 1. 过期检测
- 对比 Memory 中的状态与当前项目实际状态
- 标记不匹配的 Memory
- 例如: Memory 说 "Phase 5 进行中" 但项目已到 Phase 7

### 2. 矛盾检测
- 两个 Memory 对同一事物是否有矛盾描述
- 检查 example: "baseline 62.4%" vs "baseline 80%" 

### 3. 冗余检测
- Memory 中是否有 CLAUDE.md 已包含的信息
- Memory 中是否有 governance 文件已包含的信息

### 4. 链接完整性
- `[[link-name]]` 是否指向存在的 Memory 文件
- 是否有 broken link

### 5. 价值评估
- 每个 Memory 是否仍然提供独特价值
- 哪些 Memory 可以合并

## 输出格式

```markdown
# Memory Quality Review — {{DATE}}

## Executive Summary
**Total Memories:** {{N}} | **Healthy:** {{N}} | **Outdated:** {{N}} | **Contradictory:** {{N}} | **Redundant:** {{N}}

## Outdated Memories

| File | Claimed State | Actual State | Action |
|------|--------------|-------------|--------|
| ... | Phase 5 | Phase 7+ | Update or delete |

## Contradictions

| File A | Claim A | File B | Claim B | Resolution |
|--------|---------|--------|---------|------------|
| ... | ... | ... | ... | ... |

## Redundant Memories

| File | Duplicates | Suggested Action |
|------|-----------|-----------------|
| ... | CLAUDE.md section X | Delete (already in CLAUDE.md) |

## Broken Links

| File | Broken Link | Suggested Fix |
|------|------------|---------------|
| ... | [[missing-file]] | Create or remove reference |

## Value Assessment

| File | Unique Value | Recommendation |
|------|-------------|----------------|
| ... | high / medium / low | keep / merge / delete |
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | review | synced 2026-06-17 16:53

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->