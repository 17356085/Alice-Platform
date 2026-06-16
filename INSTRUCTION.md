# AITest Platform — Claude Code 使用指南

> 被测: 鞍集涂源管理系统 (Vue 3 + Element Plus) | 测试框架: Selenium + pytest | v2.0

## 架构

```
你在 Claude Code 里说 "/full-sop module=equipment"
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

**不是 Claude 调 Claude。** 编排引擎是 Python LangGraph。Claude Code 只做一层：解析你的意图 → 调 Bash → 展示结果。

---

## 斜杠命令

| 命令 | 做什么 | 什么时候用 |
|------|--------|-----------|
| `/full-sop module=X` | 一键全流程 (9 Phase) | 新模块、继续之前的工作 |
| `/continue` | 自动发现上次中断点 | 新会话开始，不知道做到哪了 |
| `/project-agent` | 项目初始化、上下文管理、卫生检查 | 刚接手项目、定期审计 |
| `/requirement-agent module=X` | 模块建模、需求分析 | 分析一个新模块 |
| `/test-design-agent module=X page=Y` | 页面分析、风险建模、用例设计 | 分析一个页面 |
| `/automation-agent module=X pageName=Y` | PO + 测试脚本生成、合规检查 | 写自动化代码 |
| `/automation-agent module=X mode=fix` | 修复失败的自动化代码 | 测试挂了修代码 |
| `/execution-agent module=X` | 运行测试、收集 Allure 报告 | 跑回归 |
| `/bug-analysis-agent module=X` | 失败根因分析 | 分析为什么挂了 |
| `/report-agent module=X` | 测试总结、Excel 导出 | 出报告 |
| `/knowledge-agent source=test-cycle module=X` | 知识沉淀、已知问题库更新 | 测试周期结束 |

---

## 三种使用方式

### 1. `/full-sop` — 一键全流程 (最常用)

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

**执行流程**:

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

### 2. 单个 Agent — 精准补位

```
/requirement-agent module=tank                        # 只做模块建模
/test-design-agent module=equipment page=alarm-config  # 只分析一个页面
/automation-agent module=tank pageName=monitor         # 只写一个页面的代码
/automation-agent module=tank mode=fix                 # 只修代码
/execution-agent module=lab                            # 只管跑测试
/report-agent module=warehouse                         # 只管出报告
/project-agent                                         # 卫生检查 + 文档审计
```

每个 Agent 启动时自动跑门禁检查 (`check_sop_gate.py`)，上游文档缺失会提示。

### 3. 终端 CLI — 完整 LangGraph 能力

```bash
aitest graph run --module=equipment                    # 交互模式 (有 HITL)
aitest graph run --module=equipment --non-interactive  # 非交互模式 (CC 用)
aitest graph run --module=equipment --mode=resume      # 断点续跑
aitest agent run project-agent --module=tank           # 单 Agent
```

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
  扫描 7 个 SOP_STATUS → 发现 warehouse 停在 Execute & Debug
  → "warehouse: 4/9 Phase 完成，下一步 Execute & Debug"
  → "/full-sop module=warehouse mode=resume"
```

### 代码写好了，检查质量

```
你: /automation-agent module=tank pageName=monitor

自动执行:
  1. TECH_ANALYSIS → AUTO_STRATEGY
  2. 生成 TankMonitorPage.py + test_tank_monitor.py
  3. code-consistency-checker (mechanical, 0 token):
     ✅ 继承 BasePage    ✅ 无绝对 XPath    ✅ 无 time.sleep
     ❌ print('debug') at line 47
  4. code-consistency-checker (LLM review, ~2K token, 默认开启):
     发现: CSS 选择器含动态 class → 建议 data-testid
     发现: el-dialog 内缺 Teleport 等待
  5. 报告 → artifacts/code-review/tank/monitor/
```

### 测试挂了修 Bug

```
你: /bug-analysis-agent module=equipment

自动:
  1. allure-results → 3 个失败用例
  2. RAG 搜索 known-issues.yaml → 匹配已知坑位
  3. 根因分析 → 自动修复 → 重跑验证
```

### 定期卫生检查

```
你: /project-agent

自动执行 4 个 Skill:
  project-context-manager → 项目上下文更新
  context-sync            → 进度同步
  hygiene-check           → 重复文件/废弃文件/大文件/孤儿引用/格式漂移/Token预算
  completeness-check      → 文档完整性审计
```

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

## 自然语言

不需要记命令。直接说人话：

| 你说的 | 自动执行 |
|--------|---------|
| "帮我完成 equipment 模块" | `/full-sop module=equipment` |
| "继续 tank 的 monitor 页面" | `/automation-agent module=tank pageName=monitor` |
| "继续之前的工作" | `/continue` → 自动定位 |
| "为什么 test_alarm_config 挂了" | `/bug-analysis-agent module=equipment` |
| "出个 equipment 的报告" | `/report-agent module=equipment` |
| "检查下项目" | `/project-agent` |
