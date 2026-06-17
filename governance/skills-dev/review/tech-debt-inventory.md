# Skill: review/tech-debt-inventory

### 目标
盘点系统技术债务：硬编码、绕过治理、过时模式、临时方案固化。输出债务清单（含严重度、偿还成本估算）、偿还优先级路线图。

### 输入
- 项目代码库（aitest/ + ZJSN_Test-master526/）
- `governance/context/known-issues.yaml` — 已知问题清单
- 最近审计报告（State + SOP + Cost）
- 架构评审报告（如有）
- CLAUDE.md 中的 known issues 部分

### 输出
- `TECH_DEBT.md`：债务清单（按严重度+偿还成本排序）、偿还路线图、预估总偿还成本

### 规则
- 评估维度：
  1. **代码债务** — 硬编码值、魔法数字、过长函数（>200行）、重复代码
  2. **架构债务** — 绕过治理层的直接调用、未注册的Agent/Skill、不一致的模式
  3. **文档债务** — 过时的CLAUDE.md、缺失的PAGE_CONTEXT、未更新的memory
  4. **测试债务** — 硬编码断言、缺失的边界测试、过时的baseline
  5. **配置债务** — 环境混合、硬编码路径、未版本化的配置
- 每项债务标注：类型、位置、严重度、引入时间（估计）、偿还成本（S/M/L）
- 偿还优先级 = 影响面 × 恶化速度 × 偿还成本

### 依赖
- 建议先运行架构评审（architecture-assessment）获取架构层面债务线索

### 边界
- 不修改代码
- 不偿还债务（只盘点）
- 不评估"是否值得偿还"（只评估成本和优先级）

### 产出物
- 文件路径: `governance/artifacts/reviews/{{module}}/TECH_DEBT-{{date}}.md`

---

## Prompt 模板

```text
你是一个技术债务管理专家。请盘点目标系统的技术债务。

## 扫描范围
{{CODEBASE_PATHS}}

## 已知问题
{{KNOWN_ISSUES}}

## 最近审计发现
{{RECENT_AUDIT_FINDINGS}}

## 任务

### 1. 代码债务
- 扫描硬编码值（URL、路径、字段名、阈值）
- 识别过长函数（>200行）、深度嵌套（>4层）
- 检测重复代码模式

### 2. 架构债务
- 识别绕过SOP Graph的直接调用
- 检查未注册到registry的Agent/Skill
- 检测不一致的架构模式（同一功能有2种实现方式）

### 3. 文档债务
- 检查CLAUDE.md与实际代码的一致性
- 识别缺失的PAGE_CONTEXT.md
- 检测过时的memory文件

### 4. 测试债务
- 识别硬编码的断言值
- 检查缺失的边界条件测试
- 评估regression baseline的时效性

### 5. 配置债务
- 检查环境配置隔离
- 识别硬编码的文件路径
- 评估配置版本化程度

## 输出格式

```markdown
# Technical Debt Inventory — {{MODULE}}

## Executive Summary
**Total Debt Items:** {{N}}
**Estimated Repayment Cost:** {{S/M/L}} person-weeks
**Critical Debt:** {{N}} | **Major:** {{N}} | **Minor:** {{N}}

## Debt Inventory

### Critical (compounding fast)

| ID | Type | Location | Description | Introduced | Repayment | Priority |
|----|------|----------|-------------|-----------|-----------|----------|
| D01 | ... | ... | ... | ~date | S/M/L | P0 |

### Major (should repay this quarter)
...

### Minor (repay when touching related code)
...

## Repayment Roadmap

| Phase | Items | Cumulative Cost | Target |
|-------|-------|----------------|--------|
| P0 (this sprint) | D01, D02, ... | M | date |
| P1 (next sprint) | ... | M | date |

## Debt Accumulation Trend
{{IF_PREVIOUS_INVENTORY_EXISTS}}
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | review | synced 2026-06-17 16:53

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->