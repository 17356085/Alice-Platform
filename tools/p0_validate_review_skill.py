"""
P0 Validation: Run review/architecture-assessment skill against current AITest Platform.
Tests whether the review skill produces actionable findings.
"""
import sys
sys.path.insert(0, "d:/Desktop/WorkStudy")

from aitest.agent_runner import run_skill

USER_INPUT = """请评估 AITest Platform 的当前系统架构。

## 项目概述
AITest Platform 是一个 AI 驱动的自动化测试平台，被测对象是"鞍集涂源管理系统"(Vue 3 + Element Plus)。
平台包含两条工作线:
1. 测试自动化 (8 Agent SOP): project→requirement→test-design→automation→execution→bug-analysis→report→knowledge
2. 平台开发 (9 Agent SOP): pm→req→arch→design→frontend/backend→review→test→debug→build

## 架构关键组件
- Agent Runner (agent_runner.py, 2046行): AgentLoop 执行引擎, Perceive→Plan→Act→Observe→Update
- LangGraph Orchestration (graphs/sop_graph.py): SOP 流程编排 + SQLite checkpoint
- Skill Registry: 24 test skills + 32 dev skills, 版本化管理
- Governance Layer: State Auditor (7 checks), SOP Auditor (7 checks), Cost Auditor (4 checks), Regression Gate
- Event Bus: 文件持久化事件系统, Knowledge Agent 订阅消费
- Knowledge Agent: 事件驱动知识沉淀
- Server: FastAPI + chat.html 测试工作台

## 已知问题
- 测试基线 62.4%, 仍在修bug
- Governance validation sprint 发现 16 个真实治理问题
- 部分模块 (tank) 使用自定义 UI 框架, BasePage 通用定位器不可用
- workflow-pages 搜索字段是"工厂代码"不是"标题", PO 编写前必须诊断 DOM

## 近期审计发现
- 全量 SOP 828 tests baseline 62.4%
- equipment unit + personnel exam 0 ERROR (已修复)

请从 6 个维度评估架构并输出评审报告: 组件边界、数据流、耦合度、扩展性、一致性、技术债务。"""

print("=" * 60)
print("P0 Validation: review/architecture-assessment")
print("=" * 60)

response = run_skill(
    skill_id="review/architecture-assessment",
    user_input=USER_INPUT,
    provider="claude",
    max_tokens=8192,
)

print("\n--- LLM Response ---\n")
print(response.content[:8000] if len(response.content) > 8000 else response.content)
print(f"\n--- Token Usage: {response.token_usage} ---")
print(f"--- Model: {response.model} ---")
print(f"--- Finish Reason: {response.finish_reason} ---")
