# 结对种子集成方案 — 人工场景注入 + 来源追踪 + 覆盖率指标

> **来源**：cloaks.cn《自动化集成测试框架设计方案》(2026-06-15) 评审 → 提取 3 个本项目可落地概念
> **互补**：与 [HITL_EXPANSION_PLAN.md](HITL_EXPANSION_PLAN.md) 互补——HITL 是"AI 产出后审批"，本方案是"AI 产出前注入人类种子"
> **目标**：交付给独立 AI 会话执行，无需原始对话上下文
> **前提**：执行前请先阅读 `CLAUDE.md`（项目入口）和 `governance/README.md`（治理骨架）

---

## 快速导航

| 任务 | 优先级 | 预计工期 | 预期收益 | 依赖 |
|------|--------|----------|----------|------|
| [任务 A：场景来源追踪](#任务-a场景来源追踪) | **P0** | 1-2 小时 | 所有产出物可审计，零成本 | 无 |
| [任务 B：结对种子 Skill](#任务-b结对种子-skill) | **P0** | 3-4 小时 | 人类注入 2-3 个核心场景，AI 围绕扩展，减少漏测 | 任务 A 完成后更佳 |
| [任务 C：覆盖率指标扩展](#任务-c覆盖率指标扩展) | **P1** | 2-3 小时 | 从"文档完整性"升级到"测试质量度量" | 任务 A 完成后更佳 |
| [任务 D：人机用例合并策略](#任务-d人机用例合并策略) | **P2** | 2-3 小时 | 结对用例优先，AI 补充缺失，去重+冲突裁决 | 任务 B 完成后更佳 |

---

## 背景（给接手 AI 的上下文）

### 文章核心概念 vs 本项目现状

文章提出"结对同学"角色在 AI 测试生成流程中的 4 个关键机制：

| 文章概念 | 本项目现状 | 差距 |
|----------|-----------|------|
| 结对同学预先提供基础测试用例 | test-design-agent 从零生成 TEST_CASES.md | **无人类种子注入**——AI 可能遗漏业务关键场景 |
| 每个用例标注 `source: ai \| pair \| merged` | 无来源标记 | **不可审计**——无法区分 AI 生成 vs 人类提供 |
| 需求覆盖率 >95%, 场景覆盖率 >90% | check_sop_gate.py 只检查文档存在性 | **度量维度缺失**——只知"有没有"，不知"全不全" |
| 结对用例优先 + AI 补充 + 去重合并 | 无合并逻辑 | **冲突无法裁决**——如果人类和 AI 对同一场景有不同设计 |

### 与现有 HITL 方案的关系

```
                    HITL_EXPANSION_PLAN (审批层)
                    ┌─────────────────────────┐
                    │ auto_strategy 审批       │
                    │ P0 testcase 审批         │
                    └──────────┬──────────────┘
                               │ approve/reject
                               ▼
  本方案 (注入层)           AI 生成
  ┌─────────────────┐    ┌──────────────┐
  │ pair-seed Skill  │───▶│ test-design   │
  │ (人类种子场景)    │    │ (AI 围绕扩展) │
  └─────────────────┘    └──────────────┘
         │                      │
         ▼                      ▼
    PAIR_SEEDS.md         TEST_CASES.md
    source: pair          source: ai/merged
```

两层互补：
- **注入层（本方案）**：人类在 AI 生成**之前**提供种子，AI 围绕种子扩展
- **审批层（HITL 方案）**：人类在 AI 生成**之后**审核，通过/驳回/修改

### 关键文件路径

```
governance/
├── context/
│   ├── environments.yaml                          ← 任务 C：新增覆盖率目标配置
│   └── projects/web-automation/modules/{m}/pages/{p}/
│       ├── TEST_CASES.md                          ← 任务 A：增加 source 字段
│       ├── PAIR_SEEDS.md                          ← 任务 B：新文件——人类种子场景
│       ├── PAGE_CONTEXT.md                        ← 任务 A：增加 source 字段
│       └── AUTO_STRATEGY.md                       ← 任务 A：增加 source 字段
├── skills/
│   └── test-design/
│       ├── testcase-design.md                     ← 任务 B：修改——接受 pair_seeds 输入
│       └── pair-seed.md                           ← 任务 B：新 Skill
├── templates/
│   └── pair-seeds.template.md                     ← 任务 B：新模板
├── agents/
│   └── agent-definitions.yaml                     ← 任务 B：test-design-agent 新增 pair-seed Skill
├── docs/plans/
│   ├── PAIR_SEED_INTEGRATION_PLAN.md              ← 你正在读的文件
│   └── HITL_EXPANSION_PLAN.md                     ← 互补方案
└── validators/
    └── coverage-checker.py                        ← 任务 C：新验证器

ZJSN_Test-master526/
└── tools/
    └── check_sop_gate.py                          ← 任务 C：扩展覆盖率检查维度

aitest/
└── graphs/
    └── sop_graph.py                               ← 任务 B：新增 pair_seed 阶段节点
```

---

## 任务 A：场景来源追踪

### 问题

当前所有产出物（TEST_CASES.md、PAGE_CONTEXT.md、AUTO_STRATEGY.md）无来源标记。无法区分：
- 哪些是 AI 全自动生成的
- 哪些是人类提供的
- 哪些是人类种子 + AI 扩展合并的

审核时不知道重点关注什么。

### 方案

在所有文档产出物中增加标准化的 `source` 元数据字段。

#### 步骤 1：定义来源标记规范

在 `governance/context/source-of-truth.md` 中增加来源标记规范：

```markdown
## 产出物来源标记

所有 AI Agent 产出的治理文档必须包含来源标记：

| 标记 | 含义 | 示例场景 |
|------|------|---------|
| `source: ai` | AI 全自动生成 | test-design-agent 从零分析页面生成 |
| `source: pair` | 人类结对同学提供 | PAIR_SEEDS.md 中的种子用例 |
| `source: merged` | AI + 人类合并产物 | TEST_CASES.md 中 AI 围绕人类种子扩展的用例 |
| `source: ai-reviewed` | AI 生成 + 人工审核通过 | 经 HITL 审批后的 AUTO_STRATEGY.md |

格式（YAML front-matter 或 Markdown 元数据块）：

```markdown
---
source: ai
source_agent: test-design-agent
source_timestamp: 2026-06-22T15:30:00+08:00
reviewed_by: null
---
```

或对于单个测试用例（在 TEST_CASES.md 的用例表中）：

```markdown
| TC-001 | 正常登录流程 | P0 | ai | - |
| TC-002 | 登录失败重试限制 | P0 | pair | 结对同学补充 |
| TC-003 | 多因素认证 | P0 | merged | 结对种子 + AI 扩展 |
```
```

#### 步骤 2：修改现有 Skill 以输出 source 标记

需修改的 Skill：

| Skill | 文件 | 改动 |
|-------|------|------|
| testcase-design | `governance/skills/test-design/testcase-design.md` | TEST_CASES.md 模板增加 source 列 |
| page-analysis | `governance/skills/test-design/page-analysis.md` | PAGE_CONTEXT.md 增加 YAML front-matter source |
| auto-strategy | `governance/skills/automation/auto-strategy.md` | AUTO_STRATEGY.md 增加 source |
| tech-analysis | `governance/skills/automation/tech-analysis.md` | TECH_ANALYSIS.md 增加 source |
| risk-modeling | `governance/skills/test-design/risk-modeling.md` | RISK_MODEL.md 增加 source |

改动量：每个 Skill 2-3 行（在输出模板中增加 source 字段）。

#### 步骤 3：向后兼容

- 已有的文档（source 字段缺失）默认视为 `source: ai`（未标记 = AI 生成）
- `check_sop_gate.py` 增加检查项：`source_field_present`（警告级别，不阻塞）

### 验收标准

1. 新生成的 TEST_CASES.md 中每个用例有 `source` 列
2. PAGE_CONTEXT.md / AUTO_STRATEGY.md 包含 YAML front-matter `source` 字段
3. `check_sop_gate.py` 能检测 source 字段是否存在
4. 旧文档不报错（默认 `source: ai`）

---

## 任务 B：结对种子 Skill

### 问题

当前 test-design-agent 从零分析页面生成测试用例。AI 对业务语义理解有限，可能遗漏：
- 业务关键路径（AI 不知道哪些路径是核心业务流程）
- 领域特定的边界条件（如"危化品许可证过期后仍可编辑？"）
- 隐性业务规则（如"同一合同号不能重复提交"）

### 方案

新增 `pair-seed` Skill，让人类结对同学为每个页面提供 2-5 个种子测试场景。AI 围绕种子扩展生成完整用例集。

#### 步骤 1：创建种子模板

新建文件：`governance/templates/pair-seeds.template.md`

```markdown
# {{PAGE_NAME}} — 结对测试种子

> 结对同学：{{PAIR_NAME}} | 日期：{{DATE}} | 需求ID：{{REQUIREMENT_ID}}

## 种子场景

<!-- 提供 2-5 个核心测试场景，AI 将围绕这些场景扩展 -->

### SEED-001：{{场景名称}}

- **优先级**: P0 / P1 / P2
- **类型**: positive / negative / boundary / destructive
- **业务背景**: {{为什么这个场景重要？AI 可能不知道的业务上下文}}
- **前置条件**: {{测试前需要满足的条件}}
- **操作步骤（概要）**:
  1. {{步骤1}}
  2. {{步骤2}}
- **预期结果**: {{期望看到什么}}
- **关键检查点**: {{AI 容易遗漏的验证点}}

### SEED-002：{{场景名称}}
...

## 补充说明

- **特殊业务规则**: {{AI 从页面分析中无法获取的隐性规则}}
- **已知坑点**: {{历史 Bug 或易错点}}
- **不需要测试的场景**: {{明确排除的场景，防止 AI 过度生成}}
```

#### 步骤 2：创建 pair-seed Skill

新建文件：`governance/skills/test-design/pair-seed.md`

```markdown
# pair-seed — 结对种子场景注入

## 触发条件

- 由 human 通过 `/pair-seed --module=<m> --page=<p>` 手动触发
- 或由 SOP 流程在 test-design 阶段前自动检测 `PAIR_SEEDS.md` 是否存在

## 输入

- 结对同学直接在 `PAIR_SEEDS.md` 模板中填写的种子场景
- 或通过 Chat 界面交互式输入种子场景

## 执行流程

### L0：验证种子文件存在性

1. 检查 `governance/context/projects/web-automation/modules/{module}/pages/{page}/PAIR_SEEDS.md`
2. 若不存在 → 提示人类使用模板创建
3. 若存在 → 解析种子场景

### L1：种子场景校验

1. 检查每个 SEED 的必要字段是否完整：
   - 场景名称 (required)
   - 优先级 (required)
   - 类型 (required)
   - 操作步骤 (required, min 1 步)
   - 预期结果 (required)
2. 标记不完整的种子 → 提示人类补充
3. 输出校验报告

### L2：种子注入到 test-design 流程

1. 将有效种子场景写入 structured context
2. 设置 `pipeline_context.pair_seeds = [...]`
3. testcase-design Skill 读取后：
   - 优先采纳种子场景（标记 `source: pair`）
   - 围绕种子扩展补充场景（标记 `source: merged`）
   - 完全 AI 生成的场景标记 `source: ai`
4. 种子场景覆盖的优先级/类型不再重复生成

## 输出

- 校验报告（哪些种子有效/无效/需要补充）
- 注入标记：test-design 流程的上下文中包含 pair_seeds

## 降级规则

- 若 PAIR_SEEDS.md 不存在：正常执行 test-design，所有用例标记 `source: ai`
- 若 PAIR_SEEDS.md 存在但全部校验失败：警告后继续，所有用例标记 `source: ai`
- 若部分种子校验失败：跳过失败的，使用通过的
```

#### 步骤 3：修改 test-design-agent 编排

文件：`governance/agents/agent-definitions.yaml`

在 test-design-agent 的 Skill 链中，在 `page-analysis` 之后、`testcase-design` 之前插入 `pair-seed`：

```yaml
test-design-agent:
  description: 测试设计 Agent
  skills:
    - test-design/page-analysis
    - test-design/pair-seed        # ★ 新增：注入人类种子
    - test-design/risk-modeling
    - test-design/testcase-design
```

#### 步骤 4：sop_graph 新增可选 pair_seed 阶段

文件：`aitest/graphs/sop_graph.py`

在 Test Design phase 内部增加可选种子注入节点：

```python
def pair_seed_node(state: SOPState) -> dict:
    """检测 PAIR_SEEDS.md 存在性，存在则注入种子上下文。"""
    from pathlib import Path

    pages = state.get("pages", [])
    idx = state.get("current_page_index", 0)
    page = pages[idx] if idx < len(pages) else ""

    seed_path = (
        GOVERNANCE / "context" / "projects" / "web-automation" / "modules"
        / state["module"] / "pages" / page / "PAIR_SEEDS.md"
    )

    if seed_path.exists():
        content = seed_path.read_text(encoding="utf-8")
        return {
            "pair_seeds_available": True,
            "pair_seeds_content": content,
        }
    return {"pair_seeds_available": False}
```

此节点通过条件路由：有种子 → 注入后进入 test-design；无种子 → 直接进入 test-design。

### 验收标准

1. 人类能通过模板创建 PAIR_SEEDS.md，填写 2-5 个种子场景
2. 存在 PAIR_SEEDS.md 时，生成的 TEST_CASES.md 包含 `source: pair` 和 `source: merged` 标记
3. 不存在 PAIR_SEEDS.md 时，正常生成所有用例，标记 `source: ai`
4. 种子覆盖的场景类型/优先级，AI 不再重复生成
5. 校验失败时降级不阻塞流程

---

## 任务 C：覆盖率指标扩展

### 问题

`check_sop_gate.py` 当前只检查治理文档**存在性**（PAGE_CONTEXT.md 有没有？TEST_CASES.md 有没有？）。不检查**质量**（用例覆盖了多少需求？P0 场景够不够？）。

### 方案

参考文章的四维覆盖率模型，扩展 gate check：

| 指标 | 文章目标 | 本项目适配 | 检查方式 |
|------|---------|-----------|---------|
| 需求覆盖率 | >95% | 每个页面至少 N 个 P0 用例 | 统计 TEST_CASES.md 中 P0 用例数 |
| 场景覆盖率 | >90% | 覆盖 positive/negative/boundary 三类 | 统计用例类型分布 |
| 接口覆盖率 | >90% | 每个可交互元素至少 1 个用例 | 交叉比对 PAGE_CONTEXT 元素列表 vs 用例覆盖 |
| 端到端覆盖率 | >80% | 模块核心流程有 e2e 用例 | 检测 TEST_CASES.md 中 `type: e2e` 标记 |

#### 步骤 1：environments.yaml 增加覆盖率配置

文件：`governance/context/environments.yaml`

```yaml
coverage:
  targets:
    requirement_coverage: 0.95      # 每个页面 P0 用例 ≥ 1
    scene_type_diversity:           # positive / negative / boundary 至少各 1 个
      min_positive: 1
      min_negative: 1
      min_boundary: 1
    element_coverage: 0.90          # 可交互元素被用例覆盖的比例
    e2e_coverage: 0.80              # 核心流程端到端覆盖
  
  # 按模块覆盖（可选）
  per_module:
    equipment:
      min_p0_cases: 3
      require_e2e: true
    production:
      min_p0_cases: 3
      require_e2e: true
```

#### 步骤 2：扩展 check_sop_gate.py

文件：`ZJSN_Test-master526/tools/check_sop_gate.py`

新增检查维度：

```python
COVERAGE_CHECKS = [
    "p0_case_count",        # P0 用例数 ≥ min_p0_cases
    "scene_type_diversity", # 至少 1 个 positive + 1 个 negative + 1 个 boundary
    "element_coverage",     # 可交互元素被引用的比例 ≥ 0.9
    "source_field_present", # source 字段存在性（任务 A）
    "pair_seeds_exists",    # PAIR_SEEDS.md 存在性（鼓励使用，非阻塞）
]
```

实现 `check_coverage_metrics()` 函数：

```python
def check_coverage_metrics(module_name: str, page_name: str) -> dict:
    """检查单个页面的覆盖率指标。"""
    test_cases_path = get_context_path(module_name, page_name, "TEST_CASES.md")
    page_context_path = get_context_path(module_name, page_name, "PAGE_CONTEXT.md")

    if not test_cases_path.exists():
        return {"status": "fail", "reason": "TEST_CASES.md not found"}

    content = test_cases_path.read_text(encoding="utf-8")
    cases = parse_test_cases(content)  # 解析用例列表

    results = {
        "p0_count": count_priority(cases, "P0"),
        "positive_count": count_type(cases, "positive"),
        "negative_count": count_type(cases, "negative"),
        "boundary_count": count_type(cases, "boundary"),
        "has_source_field": check_source_field(content),
        "has_e2e": count_type(cases, "e2e") > 0,
    }

    # 对照 environments.yaml 中的 targets
    targets = load_coverage_targets(module_name)
    results["pass"] = all([
        results["p0_count"] >= targets.get("min_p0_cases", 1),
        results["positive_count"] >= targets.get("min_positive", 1),
        results["negative_count"] >= targets.get("min_negative", 1),
        results["boundary_count"] >= targets.get("min_boundary", 1),
    ])

    return results
```

#### 步骤 3：新增覆盖率验证器

新建文件：`governance/validators/coverage-checker.py`

```python
"""覆盖率验证器——从 check_sop_gate.py 独立出来，支持 CI 集成。"""
# 核心逻辑同步骤 2，封装为独立模块
# 输出 JSON 格式，供 CI pipeline 消费
```

### 验收标准

1. `check_sop_gate.py --module <m> --check coverage` 输出覆盖率指标
2. 缺失 P0 用例时返回 warning（不阻塞，因为不是所有页面都需要 P0）
3. 缺失负面/边界场景时返回 warning
4. 配置文件驱动阈值，模块可按需覆盖

---

## 任务 D：人机用例合并策略

### 问题

当人类提供了种子用例（PAIR_SEEDS.md）且 AI 也生成了用例，如何合并？
- 同一场景人类和 AI 都有但设计不同 → 谁优先？
- 人类覆盖了 P0 但 AI 也生成了相似的 P0 → 如何去重？
- AI 生成的用例与人类种子冲突 → 如何裁决？

### 方案

定义明确的合并策略，在 testcase-design Skill 中实现。

#### 策略定义

```yaml
# 合并策略（在 testcase-design Skill 中实现）

merge_rules:
  priority:
    - pair_seeds      # 1. 结对种子最高优先级
    - pair_override   # 2. 结对同学覆盖（同场景但不同设计 → 使用结对版本）
    - ai_generated    # 3. AI 补充生成（全新场景）
  
  dedup:
    method: semantic_similarity    # 基于场景名称 + 操作步骤的语义相似度
    threshold: 0.8                 # 相似度 > 0.8 → 视为重复
    action_on_dup: keep_pair       # 重复时保留结对版本，丢弃 AI 版本
  
  conflict_resolution:
    - type: same_scenario_different_steps
      rule: prefer_pair            # 结对版本优先，AI 版本作为备选注释
    - type: same_scenario_different_expected
      rule: flag_for_review        # 标记为待人工审核
    - type: pair_missing_details
      rule: ai_fill                # AI 补充细节（如 pair 只有概要步骤，AI 补全详细步骤）
  
  gap_filling:
    after_merge: true              # 合并后检查覆盖缺口
    check_dimensions:
      - priority_coverage          # 每个优先级至少 1 个用例
      - type_coverage              # positive / negative / boundary 至少各 1
      - element_coverage           # 高风险元素至少 1 个用例
```

#### 步骤 1：在 testcase-design Skill 中实现合并逻辑

文件：`governance/skills/test-design/testcase-design.md`

在 Skill 的流程中增加合并阶段：

```markdown
## 执行流程

### L0：加载输入

1. 读取 PAGE_CONTEXT.md（元素清单）
2. 读取 RISK_MODEL.md（风险模型）
3. 检查 PAIR_SEEDS.md 是否存在
   - 存在 → 进入 L1（合并模式）
   - 不存在 → 进入 L2（纯 AI 生成模式）

### L1：合并模式（PAIR_SEEDS.md 存在时）

1. 解析 PAIR_SEEDS.md 中的种子场景 → `pair_cases`
2. AI 分析页面，生成候选场景 → `ai_candidates`
3. 对 `ai_candidates` 中的每个场景：
   a. 与 `pair_cases` 做语义相似度匹配
   b. 相似度 > 0.8 → 丢弃（结对版本已覆盖）
   c. 相似度 0.5-0.8 → 标记 `source: merged`，合并细节
   d. 相似度 < 0.5 → 保留 `source: ai`
4. `pair_cases` 全部保留，标记 `source: pair`
5. 检查覆盖缺口（按 merge_rules.gap_filling 维度）
6. 如有缺口 → AI 补充生成，标记 `source: ai`

### L2：纯 AI 生成模式（PAIR_SEEDS.md 不存在时）

（现有逻辑，所有用例标记 `source: ai`）

### L3：输出

生成 TEST_CASES.md，每个用例包含 `source` 字段和（如适用）`merged_from` 引用。
```

#### 步骤 2：更新 TEST_CASES.md 模板

文件：`governance/templates/test-cases.template.md`

用例表增加列：

```markdown
| ID | 场景名称 | 优先级 | 类型 | 来源 | 合并来源 | 操作步骤 | 预期结果 |
|----|---------|--------|------|------|---------|---------|---------|
| TC-001 | 正常登录 | P0 | positive | pair | SEED-001 | ... | ... |
| TC-002 | 密码错误 | P1 | negative | merged | SEED-001+AI | ... | ... |
| TC-003 | 超时重试 | P1 | boundary | ai | - | ... | ... |
```

### 验收标准

1. 有 PAIR_SEEDS.md 时，TEST_CASES.md 不包含与种子重复的用例
2. 种子用例标记 `source: pair`，合并用例标记 `source: merged`
3. 无 PAIR_SEEDS.md 时行为与改造前一致
4. 覆盖缺口被 AI 自动填补

---

## 实现顺序

```
1. 任务 A (source tracking)     ← 最快见效，1-2h，零依赖，为 B/C/D 打基础
2. 任务 B (pair-seed Skill)     ← 核心价值，3-4h，依赖 A 的 source 字段
3. 任务 C (coverage metrics)    ← 质量可视化，2-3h，依赖 A
4. 任务 D (merge strategy)      ← 高级特性，2-3h，依赖 B
```

如果时间有限，**只做 A + B** 即可获得最大收益（人类种子注入 + 可审计追溯）。

---

## 与现有架构的一致性

- 复用 `GOVERNANCE` 路径约定（`governance/context/projects/web-automation/modules/{m}/pages/{p}/`）
- 复用 `SOPState` TypedDict（新增 `pair_seeds_available`、`pair_seeds_content` 字段）
- 复用 Skill → Agent 编排模式（pair-seed 作为 test-design-agent 的一个 Skill）
- 复用 `check_sop_gate.py` 的检查框架
- PAIR_SEEDS.md 为**可选文件**——不存在时零影响，完全向后兼容

---

## 风险评估

| 风险 | 影响 | 缓解 |
|------|------|------|
| PAIR_SEEDS.md 格式不规范导致解析失败 | 中 | L1 校验步骤捕获，降级到纯 AI 模式 |
| 语义相似度匹配置信度不足 | 中 | 阈值可配置；冲突场景标记 `flag_for_review` 而非自动裁决 |
| source 字段在旧文档中缺失 | 低 | 默认 `source: ai`，不阻塞 gate check |
| 覆盖率指标误报（P0 用例数为 0 但页面确实不需要） | 低 | 默认为 warning 而非 error；配置文件可按模块覆盖阈值 |
| 合并策略过于复杂导致 Skill Prompt 膨胀 | 中 | 合并逻辑用结构化规则（YAML）定义，AI 只需执行，不需记忆 |

---

## 相关文件索引

| 文件 | 任务 A | 任务 B | 任务 C | 任务 D |
|------|:---:|:---:|:---:|:---:|
| `governance/context/source-of-truth.md` | ✏️ | | | |
| `governance/skills/test-design/testcase-design.md` | ✏️ | ✏️ | | ✏️ |
| `governance/skills/test-design/page-analysis.md` | ✏️ | | | |
| `governance/skills/automation/auto-strategy.md` | ✏️ | | | |
| `governance/skills/automation/tech-analysis.md` | ✏️ | | | |
| `governance/skills/test-design/risk-modeling.md` | ✏️ | | | |
| `governance/templates/pair-seeds.template.md` | | ✨ | | |
| `governance/skills/test-design/pair-seed.md` | | ✨ | | ✏️ |
| `governance/agents/agent-definitions.yaml` | | ✏️ | | |
| `aitest/graphs/sop_graph.py` | | ✏️ | | |
| `governance/context/environments.yaml` | | | ✏️ | |
| `ZJSN_Test-master526/tools/check_sop_gate.py` | ✏️ | | ✏️ | |
| `governance/validators/coverage_checker.py` | | | ✨ | |
| `governance/templates/test-cases.template.md` | ✏️ | | | ✏️ |

> 图例：✏️ = 需编辑 | 📖 = 需阅读理解 | ✨ = 新文件

---

> **给接手 AI 的提示**：按顺序执行任务 A → B → C → D。任务 A 为所有后续任务提供 source 字段基础设施。每个任务完成后运行对应的验收测试。与 [HITL_EXPANSION_PLAN.md](HITL_EXPANSION_PLAN.md) 互补——本方案处理"AI 生成前的种子注入"，HITL 方案处理"AI 生成后的审批把关"。两个方案可并行实施。
