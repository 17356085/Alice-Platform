# AITest Platform — 使用指南

> 被测: 鞍集涂源管理系统 (Vue 3 + Element Plus) | 测试框架: Selenium + pytest | v2.0

## 架构

```
你说 "/full-sop module=equipment"
        │
        ▼
   full-sop.workflow.js → Bash: aitest graph run --module=equipment --non-interactive
        │
        ▼
   Python LangGraph (sop_graph.py) — 9-Phase 状态机
     ├─ AgentLoop → run_skill() → Anthropic API (实际 LLM 调用)
     ├─ checkpoint SQLite (断点续跑)
     ├─ check_sop_gate.py (门禁)
     └─ code-consistency: grep + LLM review
        │
        ▼
   返回 JSON 结果 → 展示给你
```

**不是 Claude 调 Claude。** 编排引擎是 Python LangGraph。Claude Code 只做一层：解析意图 → 调 Bash → 展示结果。

---

## 两种使用方式

| 方式 | 适用场景 | 入口 |
|------|---------|------|
| **Claude Code** | 日常交互、一键全流程、自然语言驱动 | `/full-sop`、`/continue`、自然语言 |
| **Bash / CLI** | 脚本化、CI/CD、精细控制、单步操作 | `aitest sop run`、`aitest agent run` 等 |

---

# 方式一：Claude Code

## 斜杠命令

平台注册了 **2 个斜杠命令**：

| 命令 | 做什么 | 示例 |
|------|--------|------|
| `/full-sop module=X` | 一键全流程 (9 Phase)，从建模到报告 | `/full-sop module=equipment` |
| `/continue` | 扫描 SOP_STATUS 自动发现中断点，恢复工作 | `/continue` |

### `/full-sop` 参数

```
/full-sop module=equipment                    # 新模块从头开始
/full-sop module=tank mode=from-automation    # 设计文档已有，直接写代码
/full-sop module=lab mode=resume              # 上次中断了，继续
/full-sop module=lab mode=status              # 看看进度
/full-sop module=production pages=daily-report,monthly-report   # 只测指定页面
```

| mode | 跳过 |
|------|------|
| `full` (默认) | — |
| `from-requirement` | Project Init |
| `from-test-design` | Project Init + Requirement |
| `from-automation` | 前 3 Phase，直接自动化 |
| `resume` | 自动从 checkpoint 恢复 |
| `status` | 仅显示进度，不执行 |

### 执行流程

```
Preflight (文件扫描, 0 token)
  → Project Init (如需)
  → Requirement → MODULE_CONTEXT.md
  → Test Design (per page) → PAGE_CONTEXT, RISK_MODEL, TEST_CASES
  → Automation (per page) → TECH_ANALYSIS, PageObject.py, test_*.py
      └─ code-consistency: grep 8红线 + LLM 深度审查 (自动)
  → Execute & Debug → pytest + allure
  → [仅失败时] Bug Analysis → 根因 + auto-fix → retry (≤3轮)
  → Data Sanitization → 清理残留数据
  → Report → TEST_SUMMARY.md
  → Knowledge → known-issues.yaml 更新
```

---

## 自然语言驱动

不需要记命令。直接说人话，Claude Code 自动映射到对应 Agent：

| 你说的 | 自动执行 |
|--------|---------|
| "帮我完成 equipment 模块" | `/full-sop module=equipment` |
| "继续之前的工作" | `/continue` → 自动定位中断点 |
| "继续 tank 的 monitor 页面" | 调 `automation-agent` 续写 PO + test |
| "分析一下 warehouse 模块" | 调 `requirement-agent` 做模块建模 |
| "给 alarm-config 页面设计用例" | 调 `test-design-agent` 做页面分析 |
| "为什么 test_alarm_config 挂了" | 调 `bug-analysis-agent` 做根因分析 |
| "跑一下 lab 的回归" | 调 `execution-agent` 运行 pytest |
| "出个 equipment 的报告" | 调 `report-agent` 生成报告 |
| "检查下项目卫生" | 调 `project-agent` 做 hygiene check |

### 8 个测试 Agent

| Agent | 阶段 | 做什么 |
|-------|------|--------|
| `project-agent` | 0 | 项目初始化、上下文管理、卫生检查 |
| `requirement-agent` | 0.5~0.8 | 模块建模、需求分析 |
| `test-design-agent` | 1~2.5 | 页面分析、风险建模、用例设计 |
| `automation-agent` | 3~4 | PO 生成、测试脚本生成、合规检查 |
| `execution-agent` | 4.5~7 | 运行测试、收集 Allure 报告 |
| `bug-analysis-agent` | 4.5~7 | 失败根因分析、自动修复 |
| `report-agent` | 8~9 | 测试总结、Excel 导出 |
| `knowledge-agent` | 横向 | 知识沉淀、已知问题库更新 |

每个 Agent 启动时自动跑门禁检查 (`check_sop_gate.py`)，上游文档缺失会提示。

---

## 典型场景

### 新模块从零到测试完成

```
你: /full-sop module=warehouse

系统自动:
  发现 16 个页面 → 逐页分析 → 生成 PO + test → 跑测试 → 出报告
  最终: 68 passed, 0 failed
        SOP_STATUS_warehouse.json 写入
        ZJSN_Test-master526/page/warehouse_page/  ← 14 个 PageObject
        ZJSN_Test-master526/script/warehouse/     ← 13 个 test_*.py
```

### 新会话继续工作

```
你: /continue

系统自动:
  扫描 SOP_STATUS → 发现 warehouse 停在 Execute & Debug
  → "warehouse: 4/9 Phase 完成，下一步 Execute & Debug"
  → 自动 resume
```

### 代码写好了，检查质量

```
你: 检查 tank monitor 页面的代码质量

自动执行:
  1. TECH_ANALYSIS → AUTO_STRATEGY
  2. 生成 TankMonitorPage.py + test_tank_monitor.py (如需)
  3. code-consistency-checker (mechanical, 0 token):
     ✅ 继承 BasePage    ✅ 无绝对 XPath    ✅ 无 time.sleep
     ❌ print('debug') at line 47
  4. code-consistency-checker (LLM review, ~2K token):
     发现: CSS 选择器含动态 class → 建议 data-testid
     发现: el-dialog 内缺 Teleport 等待
  5. 报告 → artifacts/code-review/tank/monitor/
```

### 测试挂了修 Bug

```
你: 为什么 equipment 的测试挂了

自动:
  1. allure-results → 3 个失败用例
  2. RAG 搜索 known-issues.yaml → 匹配已知坑位
  3. 根因分析 → 自动修复 → 重跑验证 (≤3轮)
```

### 定期卫生检查

```
你: 检查下项目

自动执行 4 个 Skill:
  project-context-manager → 项目上下文更新
  context-sync            → 进度同步
  hygiene-check           → 重复文件/废弃文件/大文件/孤儿引用/格式漂移/Token预算
  completeness-check      → 文档完整性审计
```

---

# 方式二：Bash / CLI

直接调用 Python CLI，适合脚本化、CI/CD、精细控制。

## 安装

```bash
pip install -e .
```

## 核心命令

### `aitest sop` — SOP 全流程 (推荐入口)

```bash
aitest sop run --module=equipment                    # 交互模式 (有 HITL)
aitest sop run --module=equipment --non-interactive  # 非交互 (CI/CD 用)
aitest sop run --module=equipment --mode=resume      # 断点续跑
aitest sop run --module=lab --mode=from-automation   # 从自动化阶段开始
aitest sop status --module=equipment                 # 查看进度
aitest sop list                                      # 列出所有模块状态
aitest sop cleanup --module=equipment                # 清理残留数据
```

`aitest graph` 是 `aitest sop` 的别名，参数相同。

### `aitest agent` — 单 Agent 执行

```bash
aitest agent run project-agent --module=tank         # 运行单个 Agent
aitest agent run automation-agent --module=tank --page=monitor
aitest agent check --module=equipment                # 门禁检查
aitest agent next --module=equipment                 # 显示下一步该做什么
```

### `aitest skill` — 单 Skill 执行

```bash
aitest skill run page-analysis --module=equipment --page=alarm-config
aitest skill run code-consistency-checker --module=tank
aitest skill list                                    # 列出所有 Skill
```

### `aitest check` — 代码质量

```bash
aitest check --module=equipment                      # 模块代码检查
aitest check --staged                                # 检查暂存区变更
aitest check --json                                  # JSON 输出
aitest check --consistency                           # 一致性检查
```

### `aitest run` — 直接跑 pytest

```bash
aitest run equipment                                 # 全模块测试
aitest run equipment --smoke                         # 冒烟测试
aitest run equipment --parallel                      # 并行执行
```

### `aitest report` — 报告

```bash
aitest report summary --module=equipment             # 测试摘要
aitest report progress --module=equipment             # 进度报告
aitest report excel --module=equipment               # Excel 导出
```

### `aitest status` — 状态

```bash
aitest status                                        # 全局状态
aitest status --module=equipment                     # 模块状态
```

---

## 全部 CLI 命令速查

| 命令 | 用途 |
|------|------|
| `aitest sop` | SOP 全流程编排 (推荐) |
| `aitest graph` | 同 sop，LangGraph 编排 |
| `aitest agent` | 单 Agent 调度 |
| `aitest skill` | 单 Skill 执行 |
| `aitest workflow` | 工作流引擎 |
| `aitest check` | 代码质量 + 一致性检查 |
| `aitest run` | 直接跑 pytest |
| `aitest status` | 项目/模块状态 |
| `aitest sync` | 会话同步 (读/写 CURRENT_TASK) |
| `aitest report` | 报告生成 |
| `aitest rag` | RAG 检索/索引 |
| `aitest bug` | Bug 历史记录 |
| `aitest bus` | 事件总线 |
| `aitest dashboard` | 平台概览面板 |
| `aitest server` | 服务管理 (FastAPI) |
| `aitest errors` | 结构化错误跟踪 |
| `aitest trace` | 全链路追踪 |
| `aitest eval` | Skill 评估框架 |
| `aitest ab` | A/B 测试 Prompt 变体 |
| `aitest regression` | 回归测试 / golden test 基线 |
| `aitest kpi` | 治理 KPI 仪表板 |
| `aitest testcase` | 测试用例导出为 Excel |

---

## CLI 典型用法

```bash
# CI/CD 一键全流程
aitest sop run --module=equipment --non-interactive

# 断点续跑
aitest sop run --module=warehouse --mode=resume --non-interactive

# 只跑门禁检查
aitest agent check --module=tank --json

# 单 Skill 生成 PO
aitest skill run page-object-generator --module=tank --page=monitor

# 跑冒烟测试
aitest run equipment --smoke -v

# RAG 搜索已知问题
aitest rag search "el-dialog Teleport 超时" --module=equipment

# 查看全链路追踪
aitest trace summary --module=equipment

# 导出测试用例
aitest testcase equipment alarm-config --output=alarm_cases.xlsx

# 治理 KPI
aitest kpi audit-all --json
```

---

## 两种方式对比

| | Claude Code | Bash / CLI |
|------|-------------|------------|
| **交互模式** | 对话式，自然语言 | 命令行参数 |
| **断点续跑** | `/continue` 自动发现 | `--mode=resume` |
| **HITL 审批** | 内置在对话流中 | 终端交互 |
| **适合谁** | 日常开发、探索性测试 | CI/CD、脚本、批量操作 |
| **自动修复** | 对话中自动修 + 解释 | 静默执行，输出 JSON |
| **底层** | 都调 `aitest graph run --non-interactive` | 直接调 Python |

---

## 核心能力

| 能力 | 状态 |
|------|:--:|
| 9-Phase 状态机自动遍历 | ✅ |
| SQLite checkpoint 断点续跑 | ✅ |
| Gate 门禁 (每 Phase 入口验证) | ✅ |
| code-consistency: grep 8红线 + LLM 深度审查 | ✅ |
| Bug Analysis → auto-fix → retry (≤3轮) | ✅ |
| Data Sanitization (残留数据清理) | ✅ |
| mtime 缓存 TTL | ✅ |
| HITL 审批 (终端交互模式) | ✅ |
| `/continue` 自动发现中断点 | ✅ |
| 21 个 CLI 命令 + 8 Agent + 24 Skill | ✅ |
