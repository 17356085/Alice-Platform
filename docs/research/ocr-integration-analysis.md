# Open Code Review (OCR) × Alice 集成调研

> 调研日期: 2026-07-06
> 项目: https://github.com/alibaba/open-code-review
> 许可: Apache-2.0 | Stars: 10k+ | 语言: Go + TypeScript

---

## 一、OCR 是什么

阿里巴巴开源的 AI 代码审查 CLI 工具，核心架构是 **"确定性工程 × Agent" 混合驱动**：

| 层 | 职责 | 技术 |
|----|------|------|
| 确定性工程层 | 精准文件筛选、智能打包分组、模板规则匹配、评论定位+反思 | Go 实现，硬约束 |
| Agent 层 | 场景化提示词、审查工具集、动态上下文检索 | LLM tool calling |

**核心命令**:
- `ocr review` — 基于 Git diff 的行级精度审查（支持分支对比、单 commit、工作区变更）
- `ocr scan` — 全文件扫描（审计陌生代码库、迁移前扫描）
- `ocr viewer` — WebUI 查看器 (localhost:5483)

**内置规则**: NPE、线程安全、XSS、SQL 注入等，四层优先级链（CLI → 项目 → 全局 → 系统默认）

**Benchmark**: 50 仓库 × 200 PR × 10 语言，相比通用 Agent（Claude Code）Precision 和 F1 显著更高，仅消耗 ~1/9 token，但 Recall 较低（刻意取舍：精准度 > 召回率）。

---

## 二、Alice 现有 Review 能力盘点

### 2.1 测试侧（aitest 平台）

| 模块 | 位置 | 能力 |
|------|------|------|
| `DiffFirstReviewAdapter` | `aitest/audit_engine/diff_first_review_adapter.py` | Git diff 提取 → 混合策略（diff优先 + 大文件全文降级）→ 构建 Review Prompt |
| `ReviewTrigger` (audit) | `aitest/audit_engine/review_trigger.py` | 事件阈值检查 → 自动排队架构/成本/治理评审 |
| `ReviewTrigger` (engine) | `packages/alice-engine/.../review_trigger.py` | 简单的失败/质量问题触发判断 |

### 2.2 开发侧（Dev SOP Phase 7）

| 能力 | 说明 |
|------|------|
| `review-agent` | 10-Phase Dev SOP 中的第 7 阶段，执行代码审查 |
| 4 个 Skill | `source-code-reviewer` / `consistency-enforcer` / `performance-analyzer` / `security-scanner` |
| 门禁联动 | `review_has_issues` → 决定是否触发 Phase 9 (Debug & Fix) |
| 输出物 | CODE_REVIEW.md / PERFORMANCE_REPORT.md / SECURITY_REPORT.md / CONSISTENCY_REPORT.md |

### 2.3 CI/CD

| 流水线 | 触发 | 内容 |
|--------|------|------|
| `ci.yml` | Push/PR | Lint → Test (3.10-3.12) → Build Docker |
| `agent-quality-gate.yml` | — | Agent 质量门禁 |
| `tlo-ci.yml` | — | .tlo/ CI |

**当前 CI 无代码审查步骤** — 只有测试和构建。

---

## 三、整合可行性分析

### 3.1 ✅ 强适配点

#### A. CI/CD 集成 — 补 Alice 最大缺口

Alice 的 CI 目前 **零代码审查**。OCR 的 `ocr review --from origin/main --to HEAD --format json` 可以直接作为 GitHub Actions step 插入，JSON 输出可被后续 step 解析。

```yaml
# 可行方案: 新增 .github/workflows/code-review.yml
- name: AI Code Review
  run: |
    npm install -g @alibaba-group/open-code-review
    ocr review --from "origin/${{ github.base_ref }}" --to "HEAD" --format json > review.json
```

**价值**: PR 级别的自动审查，零人工介入，输出结构化 JSON 可对接 Alice 的门禁系统。

#### B. 确定性工程层 — 弥补 Alice Review 的最大弱点

Alice 的 `DiffFirstReviewAdapter` 做了 diff 提取，但没有：
- **智能文件打包**（OCR 会把中英文 properties 文件、关联组件合并为一个审查单元）
- **内置规则引擎**（NPE/XSS/SQL 注入等硬规则，不依赖 LLM 判断）
- **评论定位+反思模块**（OCR 有独立的位置校正和内容反思，减少 LLM 的定位漂移）

这些恰好是 Alice 当前 Review 全靠 LLM 判断的薄弱环节。

#### C. Token 效率 — 与 Alice 的省流方向一致

Alice 已经做了 diff-first 省流（`DiffFirstReviewAdapter`）。OCR 的 benchmark 表明同等模型下仅消耗 ~1/9 token，它的打包策略和提示词优化值得 Alice 学习。

#### D. 规则系统 — 可复用

OCR 的四层规则优先级链（CLI → 项目 → 全局 → 系统默认）与 Alice 的 governance 分层理念一致。OCR 的内置规则（NPE、XSS、SQL 注入等）可以直接作为 Alice `review-agent` 的补充规则源。

### 3.2 ⚠️ 需要注意的点

#### A. 技术栈差异

OCR 是 Go + TypeScript CLI 工具，Alice 是 Python 平台。集成方式只能是：
- **CLI 调用**（subprocess）— 最简单，但需要安装 Node.js 或下载二进制
- **JSON 输出解析** — `ocr review --format json` → Alice 门禁系统消费
- **不建议**深度嵌入 Python 代码（Go 核心无法直接 import）

#### B. LLM Provider 复用

OCR 支持 OpenAI/Anthropic 协议，Alice 也用这些。可以共享 `.env` 中的 API Key，但需要分别配置（OCR 有自己的 config 体系）。

#### C. Recall 取舍

OCR 设计上牺牲 Recall 换 Precision。对于 Alice 的测试自动化场景：
- **开发侧（Dev SOP）**: 高 Precision 低 Recall 可接受 — 少误报比少漏报重要
- **测试侧**: 可能需要更高 Recall — 需要评估是否与 Alice 的测试质量目标冲突

#### D. MCP Server

OCR 支持 MCP 协议，Alice 的 `aitest/infra/mcp_server.py` 曾存在（已删除）。如果未来恢复 MCP 支持，OCR 可以作为 MCP tool 直接被 Alice Agent 调用。

### 3.3 ❌ 不适合直接替换的部分

| Alice 现有能力 | OCR 能否替代 | 原因 |
|---------------|-------------|------|
| `source-code-reviewer` Skill | ❌ 不能 | Skill 是 LLM prompt，OCR 是 CLI 工具，层次不同 |
| `consistency-enforcer` | ❌ 不能 | 前后端一致性检查是业务层面，OCR 无此能力 |
| `ReviewTrigger` 事件驱动 | ❌ 不能 | OCR 是被动调用，Alice 的触发器是主动事件驱动 |
| `DiffFirstReviewAdapter` | ⚠️ 可增强 | 不替换，但可以借鉴 OCR 的打包策略和规则引擎 |

---

## 四、推荐集成方案

### 方案 A: CI/CD 侧集成（推荐，投入最小，收益最大）

```
PR 提交 → GitHub Actions → ocr review --format json → 解析结果
  ├─ 0 critical → ✅ 通过
  └─ >0 critical → ❌ 阻断 + 评论到 PR
```

**新增文件**: `.github/workflows/code-review.yml`
**投入**: 1-2 天
**效果**: 每个 PR 自动 AI 审查，结构化结果可回传到 PR 评论

### 方案 B: Dev SOP Phase 7 增强（中等投入）

在 `review-agent` 的 Skill 链中，**前置**一个 OCR 扫描步骤：

```
Phase 7 执行流:
  1. ocr scan --path <module> --format json  ← 新增: 确定性规则扫描
  2. code-review/source-code-reviewer         ← 现有: LLM 深度审查
  3. code-review/consistency-enforcer          ← 现有: 一致性检查
  ...
```

OCR 的规则扫描结果作为 LLM Review 的**前置输入**，让 LLM 专注于规则引擎无法覆盖的逻辑错误和业务问题。

**投入**: 3-5 天
**效果**: Review 质量提升（硬规则 + LLM 软判断双重覆盖）

### 方案 C: Alice Agent 内调用（长期）

通过 subprocess 调用 `ocr review`，将 JSON 输出解析为 Alice 的 review 事件格式，注入 Observation Bus。

**投入**: 1 周
**效果**: Alice Agent 可以在任意时刻触发 OCR 审查，结果自动进入事件系统

---

## 五、结论

| 维度 | 评估 |
|------|------|
| **是否值得集成** | ✅ 值得，尤其是 CI/CD 侧 |
| **最佳切入点** | 方案 A（CI/CD）→ 方案 B（Dev SOP 增强）渐进式 |
| **核心价值** | 确定性规则引擎 + Token 效率 + 结构化输出 |
| **最大风险** | 技术栈差异（Go/TS vs Python），只能 CLI 集成 |
| **与 Alice 理念一致性** | 高 — 确定性工程 × Agent 混合架构与 Alice 的 governance + LLM 理念吻合 |

**一句话**: OCR 不替代 Alice 的 Review 能力，而是**补强** Alice 在确定性规则审查和 CI/CD 自动审查上的空白。推荐先从 CI/CD 侧集成开始，再逐步嵌入 Dev SOP。
