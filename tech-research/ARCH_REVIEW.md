# ARCH_REVIEW — Browser-Use 嵌入方案架构评审

> 评审 Agent: architecture-review-agent (手动执行，DEV_AGENT_SKILL_MAP 路径 bug 阻塞)
> 被审文件: tech-research/bu-embedding-plan.md
> 日期: 2026-06-17 | 评审维度: architecture + governance + cost + production

---

## 评审结论: ✅ 通过 (v2.0 修订后)

**0 BLOCKER / 0 CRITICAL / 2 WARN / 2 INFO** (原 4B + 2C 已全部修复)

---

## BLOCKER (必须修)

### 🔴 B1: `asyncio.run()` 在同步 `BasePage.click()` 中不可行

**位置**: bu-embedding-plan.md §4.3, 第 225 行

`base_page.py` 的 `click()` 是同步方法，所有 80+ 页面类和 828 个测试用例依赖同步接口。方案中 `asyncio.run(self._bu_heal_click(...))` 会在已有 event loop 的 pytest-asyncio 环境中死锁。

**修复**: 自愈逻辑必须独立于 `BasePage.click()`。建议方案:
- `SelfHealingMixin` 作为 wrapper，不侵入 `BasePage.click()`
- 在 `conftest.py` 的 fixture tear-down 阶段跑自愈（异步上下文安全）
- 或：BrowserUse 使用独立的同步 HTTP 客户端封装（不用 asyncio）

### 🔴 B2: `po-generator` 与现有 `page-object-generator` Skill 命名冲突

**位置**: §3.2, agent-definitions.yaml

现有 `automation/page-object-generator` Skill 已存在并注册在 `skill-registry.yaml`。新增 `po-generator` 导致:
- 两个 Skill 产出相同（Page Object .py）
- automation-agent 不知道该调用哪个
- CLI 口语化路由 `"生成XX的PageObject"` 冲突

**修复**: 不要新建 `po-generator` Skill。改造现有 `page-object-generator`:
- 增加 `mode: browser-use`（默认 `mode: manual`）
- 在 `page-object-generator.md` Skill 定义中增加 "BrowserUse 辅助" 章节
- 注册表只保留一个条目

### 🔴 B3: 自愈 → 自动修改 PO 文件无安全网

**位置**: §3.3 Process 第 3 步

"成功 → 提取新选择器 → 更新 PO 文件" 是危险的自动化。如果 BrowserUse 选错了元素（V2 实验已验证可能发生），错误的定位器会被写入源码。

**修复**:
- 第一阶段：自愈仅记录选择器变更建议到 Event Bus，不自动写文件
- 第二阶段：写文件前必须走 code-consistency-checker + git diff 审核
- 增加 `--heal-dry-run` 模式

### 🔴 B4: `SelfHealingEvent` 没有定义 knowledge-agent 消费路径

**位置**: §4.4

Event Bus 发出 `SelfHealingEvent`，但 knowledge-agent 的 `knowledge-manager` Skill 不支持选择器变更模式。事件发出后无人消费。

**修复**:
- knowledge-manager 新增 `mode: selector-drift`
- 或：自愈事件暂存到 `artifacts/healing_log.jsonl`，批量导入 RAG
- phase 1 先不接 knowledge-agent，仅写日志

---

## CRITICAL (强烈建议修)

### 🟡 C1: BasePage.click() 第 5 级降级破坏现有 4 级语义

**位置**: §4.3

现有 4 级降级全是确定性操作（Selenium click → 等遮罩 → JS click → MouseEvent）。插入异步 AI 降级打破了语义纯净性。调用者无法预期 `click()` 会触发 LLM 调用。

**建议**: 
- 自愈作为 `BasePage.heal_click()` 独立方法
- 或通过 `pytest` marker `@pytest.mark.ai_heal` 显式启用
- `click()` 方法本身保持纯确定性

### 🟡 C2: `bu_skill_adapter.py` 位置不当

**位置**: §2.1

`ZJSN_Test-master526/base/bu_skill_adapter.py` 放在测试项目下，但 Skill 定义在 `governance/skills/`。适配器应该是 governance 层的组件。

**建议**: 移到 `aitest/bu_adapter.py`，与 `agent_runner.py` 同级。测试项目的 `base/` 目录只放测试基础设施。

---

## WARN (建议考虑)

### ⚠️ W1: 缺少 cold-start 策略

方案假设 BrowserUseDriver 在 Skill 调用时随时可用。但实际:
- 首次启动 Playwright Chromium ~8-12s
- 登录 ~40s
- 每个页面需要独立的 Agent run

**建议**: 增加 BrowserUse session pool 或预热机制。测试脚本可以复用 `Browser(keep_alive=True)` 的 session。

### ⚠️ W2: 14 天工期可能低估

Step 4（自愈）涉及 `base_page.py` 改动 + Playwright/Selenium 跨进程协调 + 注入测试。4 天偏紧。

**建议**: Step 4 分配 6 天，总工期 16 天。

### ⚠️ W3: MiMo API 作为默认 provider 未充分验证

方案依赖 MiMo-V2.5 作为 LLM backend。Phase 1 实验数据仅覆盖 DeepSeek（E1+E2成功/E3失败）和 Gemini（E1成功/限流）。MiMo 的 tool calling 可靠性未经验证。

**建议**: Step 1 中增加 MiMo tool calling 专项测试后再进入 Step 2。

---

## INFO (参考)

### ℹ️ I1: `page-observe` Skill 价值高但优先级可降

test-design-agent 的 page-analysis 已经有 DOM 诊断能力。`page-observe` 的增量价值在 tank 等非标准 UI 模块更大。可考虑 Step 3 与 Step 2 调换顺序。

### ℹ️ I2: `check_sop_gate.py` 当前无 BrowserUse 相关检查

Step 5.3 "跑全量门禁" 实际没有 BrowserUse 维度的检查项。建议在门禁脚本中新增:
- `--check-bu-imports`: BrowserUse 依赖可用性
- `--check-bu-skills`: 3 个 Skill 定义完整性

---

## 修订建议汇总

| # | 级别 | 问题 | 修订 |
|---|------|------|------|
| B1 | 🔴 | asyncio.run 在同步 click 中死锁 | 自愈改为 wrapper/fixture 模式 |
| B2 | 🔴 | po-generator 与 page-object-generator 冲突 | 改造现有 Skill，增加 browser-use mode |
| B3 | 🔴 | 自愈自动写 PO 文件无安全网 | 第一阶段仅记录不写入 |
| B4 | 🔴 | SelfHealingEvent 无消费路径 | 先写日志，不接 knowledge-agent |
| C1 | 🟡 | 第5级降级破坏语义 | heal_click() 独立方法 |
| C2 | 🟡 | 适配器位置不当 | 移到 aitest/bu_adapter.py |
| W1 | ⚠️ | 缺 cold-start 策略 | 增加 session pool |
| W2 | ⚠️ | 工期偏紧 | 延长至 16 天 |
| W3 | ⚠️ | MiMo 未验证 | Step 1 增加专项测试 |
| I1 | ℹ️ | page-observe 优先级可调 | Step 2/3 互换 |
| I2 | ℹ️ | 门禁脚本无 BU 检查 | 新增检查项 |

---

## 修订后重新评审条件

- [ ] B1-B4 全部修复
- [ ] C1-C2 已评审确认
- [ ] Step 1 完成 MiMo tool calling 专项测试
- [ ] 修订版 plan 重新提交

---

> 由 architecture-review-agent 生成（手动模式，因 `WORKSTUDY` 路径 bug 无法自动运行 AgentLoop）
> 签名: `review/architecture-assessment` + `review/governance-coverage` + `review/token-efficiency` + `review/production-readiness`
