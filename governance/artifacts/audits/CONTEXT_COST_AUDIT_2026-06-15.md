# 🔍 Context Cost Audit — AITest Platform

> 审计日期: 2026-06-15 | 审计范围: CLAUDE.md / .claude/ / governance/ | Token 估算: chars/3 (中英混合平均)

---

## 一、全貌总览

```
═══════════════════════════════════════════════════════════════
                    全项目 Token 资产地图
═══════════════════════════════════════════════════════════════

🟢 每会话自动注入      ~3,100 tokens  (CLAUDE.md + Memory)
🟡 按需 Skill 调用     ~78,600 tokens  (.claude 11 + test 36 + dev 42)
🟡 Agent 定义层        ~11,000 tokens  (agent-definitions + README + stubs)
🟠 模块/页面上下文      ~479,000 tokens (402 files, 按模块/页面加载)
🟠 参考文档            ~108,000 tokens (27 docs, 极少加载)
🔵 其他治理文件        ~88,000 tokens  (templates/workflows/knowledge/archived)

═══════════════════════════════════════════════════════════════
  总计 (全部文件):     ~767,000 tokens (532 files)
  每会话实际消耗:       3,000 ~ 30,000+ tokens (取决于加载深度)
═══════════════════════════════════════════════════════════════
```

---

## 二、CLAUDE.md 分析

### 根 CLAUDE.md

`CLAUDE.md` — 57 行 / 1,850 字符 / ~616 tokens

| 维度 | 评分 | 说明 |
|------|------|------|
| 长度 | 🟢 优秀 | 仅 57 行，远低于典型的 200+ 行 |
| 目录速查 | 🟢 合理 | 7 个目录项，快速导航 |
| 两条工作线 | 🟢 合理 | 清晰区分测试 vs 开发 |
| 启动命令 | 🟢 合理 | 3 条常用命令 |
| Token 估算 | 🟢 ~616 | 已从 6/14 评估的 ~2,299 tokens 大幅缩减 |

**重复度检查**: 与 `governance/README.md`（56 行/2,920 chars）有 ~10% 内容重叠（项目名、目录引用），但用途不同 — CLAUDE.md 是快捷索引，README 是状态仪表盘。**无需去重。**

### .claude/skills/ (11 个 SKILL.md)

| 文件 | 行数 | 字符数 | ~Tokens | 评级 |
|------|------|--------|---------|------|
| page-interface-generator | 126 | 4,331 | 1,443 | 🟡 偏大但必要（完整 schema 定义） |
| full-sop | 60 | 3,649 | 1,216 | 🟢 编排器合理 |
| automation-agent | 63 | 2,763 | 921 | 🟢 包含 8 条红线（核心安全规则） |
| test-design-agent | 54 | 2,004 | 668 | 🟢 |
| knowledge-agent | 51 | 1,728 | 576 | 🟢 |
| report-agent | 48 | 1,679 | 559 | 🟢 |
| bug-analysis-agent | 46 | 1,588 | 529 | 🟢 |
| project-agent | 45 | 1,485 | 495 | 🟢 |
| execution-agent | 48 | 1,442 | 480 | 🟢 |
| requirement-agent | 42 | 1,405 | 468 | 🟢 |
| continue | 32 | 1,327 | 442 | 🟢 |

**结论**: `.claude/skills/` 整体健康。平均 710 tokens/skill，全部按需加载。

---

## 三、Skills 分析 (governance/skills/ + skills-dev/)

### 测试 Skills (36 files)

| 指标 | 数值 |
|------|------|
| 总字符数 | 147,512 |
| 总 Token 估算 | ~49,170 |
| 平均 | 4,097 chars (~1,365 tokens) |
| 中位数 | ~4,000 chars |
| 标准差 | 很大（从 328 到 22,819） |

### 开发 Skills (42 files)

| 指标 | 数值 |
|------|------|
| 总字符数 | 64,919 |
| 总 Token 估算 | ~21,639 |
| 平均 | 1,545 chars (~515 tokens) |
| 中位数 | ~1,400 chars |

> 📊 **Dev skills 比 Test skills 精简 62%** — 说明测试 skills 有显著优化空间。

---

## 四、Top 10 Token 大户

| # | 文件 | 字符数 | ~Tokens | 加载频率 | 严重度 |
|---|------|--------|---------|----------|--------|
| 🔴 1 | **PAGE_INTERFACE.yaml (57 文件)** | 380,262 | 126,750 | 每页面 | 🔴 关键 |
| 🔴 2 | **excel-exporter.md** | 22,819 | 7,606 | 每次报表 | 🔴 高 |
| 🔴 3 | **AI_TEST_PLATFORM_ARCHITECTURE_OPTIMIZATION.md** | 69,762 | 23,254 | 极低（参考） | 🟡 低 |
| 🟠 4 | **known-issues.yaml** | 16,965 | 5,655 | 诊断时 | 🟡 中 |
| 🟠 5 | **IMPLEMENTATION_PLAN_PLATFORM_INDEPENDENCE.md** | 37,053 | 12,351 | 极低 | 🟡 低 |
| 🟠 6 | **knowledge-manager.md** | 9,378 | 3,126 | 阶段 9 | 🟡 中 |
| 🟠 7 | **artifacts/archive/ (6 files)** | 81,805 | 27,268 | 几乎不 | 🟢 低 |
| 🟠 8 | **agent-definitions.yaml** | 11,605 | 3,868 | Agent 启动时 | 🟡 中 |
| 🟡 9 | **templates/ (13 files)** | 42,543 | 14,181 | 按需复制 | 🟢 低 |
| 🟡 10 | **bug-analysis.md** | 7,139 | 2,379 | Bug 分析时 | 🟡 中 |

---

## 五、重复注入分析

### 🔴 严重重复

#### 1. PAGE_INTERFACE.yaml — 虚假的"Token 优化"

```
page-interface-generator SKILL.md 声称:
  "automation-agent 优先消费 YAML (~200 tokens) 而非通读 Markdown (~2000 tokens)"

实际数据:
  PAGE_INTERFACE.yaml 平均: 6,671 chars → ~2,223 tokens
  PAGE_INTERFACE.yaml 最大: 13,694 chars → ~4,564 tokens

对比同页面 PAGE_CONTEXT.md:
  15/15 个检查案例中，PAGE_INTERFACE.yaml 均 LARGER THAN PAGE_CONTEXT.md
  water-report:  INTERFACE 10,166c vs CONTEXT 1,081c (9.4× 更大!)
  paper:        INTERFACE 10,971c vs CONTEXT 1,778c (6.2× 更大!)
```

**结论**: PAGE_INTERFACE.yaml 不是优化，是 **Token 膨胀器**。57 个文件共 380KB，平均每个比对应的 PAGE_CONTEXT.md 大 3-10 倍。

#### 2. Agent/Pipeline 4 重定义

同一套 Agent pipeline (Phase 0→9) 被维护在 4 个地方:

| 文件 | 大小 | 内容 |
|------|------|------|
| agents/agent-definitions.yaml | 11,605 chars | 完整 Agent 定义 + Skills + 边界 |
| agents/README.md | 7,889 chars | Agent 全景图 + 架构流程 |
| project-index.yaml | ~4,000 chars (agents段) | Agent→Phase→Skill 映射 |
| full-sop SKILL.md | ~1,500 chars (pipeline表) | Phase 0→9 流水线 |

**重复 Tokens**: ~25,000 chars → **~8,300 tokens 的等效信息被维护 4 次。**

`agent-definitions.yaml` 声称为"单一事实源"，但其他 3 个文件独立维护各自的 pipeline 副本。

#### 3. Deprecated 文件与 Active 文件 100% 重复

4 个 Skill 文件在 `_deprecated/` 和 active 目录下 **bit-for-bit 完全相同**:

| 文件 | 大小 | 同时存在于 |
|------|------|-----------|
| knowledge-extractor.md | 4,426 chars | skills/knowledge/ + skills/_deprecated/ |
| knowledge-precipitation.md | 2,180 chars | skills/knowledge/ + skills/_deprecated/ |
| progress-report.md | 1,692 chars | skills/reporting/ + skills/_deprecated/ |
| test-summary.md | 2,006 chars | skills/reporting/ + skills/_deprecated/ |

**浪费**: 10,304 chars (~3,435 tokens) 纯冗余。这些文件标为 deprecated 但仍保留在 active 目录中。

#### 4. SOP_STATUS JSON 双份存储

状态文件同时存在于两个位置:
- `governance/artifacts/sop-status/SOP_STATUS_<module>.json`
- `governance/context/projects/web-automation/modules/<module>/SOP_STATUS_<module>.json`

### 🟡 中度重复

#### 5. 循环源引用

```
所有 .claude/skills/*/SKILL.md 声明:
  source: governance/agents/agent-definitions.yaml

agent-definitions.yaml 声明:
  .claude/skills/<name>/SKILL.md → 从此文件生成
  governance/agents/<name>.md → 从此文件生成

实际情况:
  agent-definitions.yaml ≠ SKILL.md 的来源（内容完全不同）
  governance/agents/*.md = 3 行 stubs（没有内容）
```

"单一事实源"声明不成立。

#### 6. 8 条代码红线

仅出现在 automation-agent SKILL.md 中，在 coding-standards.md 中被完整定义。这是正确的引用模式 — **不是重复，但引用链需要维护。**

---

## 六、隐藏浪费

### 🟠 大型孤立文件

| 文件 | 大小 | 说明 |
|------|------|------|
| RBAC_TEST_PLAN.md | 25,338 chars / 434 行 | 放在 modules/ 根层级，非标准命名 |
| CURRENT_TASK.md (system-management) | 20,921 chars / 410 行 | 单个模块的 CURRENT_TASK 过大 |
| ANALYSIS.md (user-list) | 26,097 chars / 399 行 | 非标准产物类型 |
| ANALYSIS.md (role-list) | 22,683 chars / 241 行 | 同上 |

### 🟠 Deprecated 僵尸文件

```
governance/agents/_deprecated/      12,404 chars (4 agents) — 永不加载
governance/skills/_deprecated/      15,890 chars (8 skills) — 永不加载
governance/_archived/               61,426 chars (10 files) — 永不加载
─────────────────────────────────────────────────────────
僵尸文件合计:                       89,720 chars → ~29,900 tokens
```

### 🟢 大文件但极少加载

```
governance/docs/                    325,762 chars → ~108,000 tokens
governance/artifacts/archive/        81,805 chars → ~27,000 tokens
governance/templates/                42,543 chars → ~14,000 tokens
─────────────────────────────────────────────────────────
低频加载合计:                       450,110 chars → ~150,000 tokens
```

这些是参考/模板/归档 — 只要不被意外读取，不构成成本问题。

### 🟢 trace_log.jsonl

`governance/.traces/trace_log.jsonl` — **5,652,899 chars (5.6MB)**。不在上下文中加载，但需要确保 `.gitignore` 已覆盖且 AI 不会意外读取。

---

## 七、预计优化空间

| 优化项 | 当前 Token 消耗 | 优化后 | 节省 | ROI |
|--------|---------------|--------|------|-----|
| **P1: 修复 PAGE_INTERFACE.yaml** | 平均 2,223 tok/页 | 目标 200 tok/页 | ~2,000 tok/页 (90%) | 🔴 极高 |
| **P2: 清理 Deprecated 重复文件** | 10,304 chars 纯冗余 | 0 | ~3,435 tokens | 🟠 高 |
| **P3: Agent pipeline 单一事实源** | ~8,300 tokens 等效信息 | ~3,000 tokens | ~5,000 tokens | 🟠 高 |
| **P4: excel-exporter.md 拆分** | 7,606 tokens/调用 | ~3,000 tokens | ~4,600 tokens/调用 | 🟡 中 |
| **P5: SOP_STATUS 去重** | 两份 JSON | 一份 | ~1,500 tokens | 🟡 中 |
| **P6: knowledge-manager.md 精简** | 3,126 tokens | ~1,800 tokens | ~1,300 tokens | 🟢 低 |
| **P7: 归档僵尸文件** | 不影响实时成本 | (清理磁盘) | N/A | 🟢 清理 |

**每模块/页面节省估算**（P1 实现后）:
- 每个页面节省 ~2,000 tokens（读 PAGE_INTERFACE 而非 PAGE_CONTEXT 时）
- 每个模块按 5 个页面计 → **每模块节省 ~10,000 tokens**
- 全项目 14 个模块 → **全项目节省 ~140,000 tokens 每次全量遍历**

---

## 八、建议

### ✅ 建议保留
- **CLAUDE.md** — 已优化到 57 行，非常精简
- **Memory 文件** — 5 个活跃文件，合理
- **.claude/skills/*/SKILL.md** — 结构合理，按需加载
- **Dev skills (42 文件)** — 平均 515 tokens，设计良好
- **coding-standards.md** — 正确的单一引用点
- **known-issues.yaml** — RAG 索引的知识库，合理大小

### ✂️ 建议拆分
1. **excel-exporter.md** (22,819 chars) → 拆为: 核心指令 (~5KB) + 示例表格 (外置文件引用)
2. **knowledge-manager.md** (9,378 chars) → 合并后未精简，两条知识操作可分离
3. **AI_TEST_PLATFORM_ARCHITECTURE_OPTIMIZATION.md** (69,762 chars) → 拆为多个子文档按需读取

### 🗑️ 建议移除
1. **`governance/skills/knowledge/knowledge-extractor.md`** — 已在 `_deprecated/` 中存在，从 active 目录删除
2. **`governance/skills/knowledge/knowledge-precipitation.md`** — 同上
3. **`governance/skills/reporting/progress-report.md`** — 同上
4. **`governance/skills/reporting/test-summary.md`** — 同上
5. **`governance/agents/_deprecated/` 4 个文件** — 已归档超过 2 周，可彻底删除
6. **`governance/skills/_deprecated/` 中未引用的文件** — 同上

### 🔧 建议修复
1. **PAGE_INTERFACE.yaml 生成逻辑** — 当前 generator 产出的 YAML 比原始 Markdown 还大。需要修改 `page-interface-generator` skill 的提取规则，限制 elements/test_scenarios 的数量（如每个最多 5 条），或者移除这个生成步骤，直接读 PAGE_CONTEXT.md
2. **Agent 定义单一事实源** — 将 agent-definitions.yaml 设为真正的主源，agents/README.md 和 project-index.yaml 的 agent 段改为自动生成的摘要
3. **SOP_STATUS 位置统一** — 只保留 `governance/artifacts/sop-status/` 一处

---

## 九、与上次评估 (2026-06-14) 的对比

| 上次建议 | 状态 | 说明 |
|----------|------|------|
| 拆分长会话 | ⚠️ 行为变更 | 无法从代码检测 |
| 精简 CLAUDE.md 路由表 | ✅ 已完成 | CLAUDE.md 已从 ~2,299 tok 减至 ~616 tok |
| 归档不活跃 Memory | ✅ 已完成 | Memory 从 8 个减到 5 个活跃文件 |
| Skill 门禁去重 | ❌ 未执行 | 上次评估判定为"不推荐" |
| 巨型 Skill 拆分 | ❌ 未执行 | 上次评估判定为"不推荐" |

**新发现**（上次未覆盖）:
- PAGE_INTERFACE.yaml 虚假优化 — **这是本次审计最重要的发现**
- 4-way agent pipeline 重复
- Deprecated/Active 文件 100% 重复
