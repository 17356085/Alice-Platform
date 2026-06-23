# Skill: root-cause-analyzer

## 目标
基于多维证据进行 LLM 深度根因分析。超越简单正则匹配，提供结构化根因报告 + 修复建议。

## 触发时机
evidence-collector 完成证据采集后，由 Failure Analyst 调用。

## 输入
- EVIDENCE_BUNDLE.json (evidence-collector 产出)
- 模块 + 页面上下文 (PAGE_CONTEXT.md)
- 已知问题库 (known-issues.yaml)
- 失败测试的代码片段

## 输出
- ROOT_CAUSE_REPORT.md — 根因分析报告
  ```markdown
  ## 根因分析: test_alarm_config.py::test_create_alarm
  
  ### 分类
  - **根因类型**: StaleLocator
  - **自动修复**: ✅ 是
  - **置信度**: 0.92
  
  ### 证据摘要
  - 截图显示 el-dialog 弹窗已打开但元素不可见
  - Console: 无 JS 错误
  - Network: /api/alarm/config 返回 200
  - DOM: `.el-dialog__wrapper` 存在但 `.el-dialog__body` display:none
  
  ### 根因详解
  Element Plus Dialog 的 Teleport 机制导致元素在 DOM 中但未渲染到可视层。
  Dialog 打开后需等待 `el-dialog__wrapper` 的 `display: block` + CSS transition 完成。
  
  ### 修复建议
  1. 定位器改为 `By.CSS_SELECTOR, ".el-dialog__wrapper:not([style*='display: none']) .el-dialog__body"`
  2. 增加显式等待: `WebDriverWait(driver, 5).until(EC.visibility_of_element_located(...))`
  3. 参考 element-plus-pitfalls.md § Teleport/Dialog 陷阱
  
  ### 跨模块影响
  同模式问题可能影响: tank/alarm-config, warehouse/hazard-out-order, system-management/menu-management
  ```

## 分析维度

| 维度 | 检查内容 | 工具 |
|------|---------|------|
| 定位器 | 元素是否存在? ID/Class 是否变化? Teleport? | DOM diff vs PAGE_CONTEXT |
| 时序 | 等待时间是否不足? 动画未完成? 异步加载? | Timeline + Console |
| 数据 | 测试数据是否过期? API 返回值变化? | Network trace |
| 环境 | 服务是否可用? 账号是否有效? | Network status |
| 代码 | 测试脚本是否有逻辑错误? | 代码片段 + AST |

## 分类决策树

```
证据分析
├── DOM 中有元素但不可见 → Teleport/Animation 问题 → TIMING (auto-fix ✅)
├── DOM 中无元素 → 定位器过期 → LOCATOR_STALE (auto-fix ✅)
├── Network 返回 500 → 被测系统故障 → ENV_DOWN (auto-fix ❌ → escalate)
├── Network 返回数据与预期不符 → 数据变更 → DATA_STALE (auto-fix ✅)
├── 步骤全部通过但断言失败 → 预期值过期 → DATA_STALE (auto-fix ✅)
└── 无法归类 → UNKNOWN (auto-fix ❌ → escalate)
```

## 规则
- confidence ≥ 0.7 → 自动采纳分类
- 修复建议必须具体到代码行
- 跨模块影响必须列出具体模块+页面
- 引用 element-plus-pitfalls.md 中的已知陷阱

## 依赖
- skills/diagnosis/evidence-collector.md (阶段 1)
- governance/context/projects/web-automation/element-plus-pitfalls.md
- governance/context/known-issues.yaml
- aitest/knowledge/rag_engine.py (ChromaDB 相似问题搜索)

## 边界
- 不修改测试代码（那是 Automation Developer 的职责）
- 不重新执行测试（那是 Execution Agent 的职责）
- 置信度 <0.5 时标记需要人工分析

---

## Prompt 模板

```text
你是一个资深测试根因分析专家。请基于多维证据分析测试失败的根本原因。

## 证据
- Test ID: {{test_id}}
- 模块/页面: {{module}}/{{page}}
- 截图: {{screenshot_ref}}
- DOM (截断): {{dom_snapshot}}
- Console: {{console_logs}}
- Network: {{network_trace}}
- Timeline: {{timeline}}

## 已知陷阱
{{element_plus_pitfalls}}

## 相似问题
{{similar_issues_from_chromadb}}

## 任务
1. 分析证据，确定根因类型
2. 判断是否可自动修复
3. 给出具体修复建议（代码级）
4. 列出跨模块影响
5. 输出 ROOT_CAUSE_REPORT.md

## 置信度要求
- 证据充分 + 模式匹配 → confidence ≥ 0.8
- 证据部分 + 推理 → confidence 0.5-0.7
- 证据不足 → confidence < 0.5 + 标记需人工
```
