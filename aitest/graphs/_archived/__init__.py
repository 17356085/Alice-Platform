"""
P0-1 架构统一 (2026-06-13): 已归档的 LangGraph SubGraph 文件。

这些文件曾是独立的 LangGraph SubGraph，各自实现了
perceive→plan→act→observe→update 循环。

P0-1 重构后，这些循环统一由 AgentLoop (agent_runner.py) 执行。
LangGraph 仅做顶层 Phase 编排，通过 make_agent_loop_node() 调用 AgentLoop。

保留 bug_analysis_graph.py（HITL + 循环逻辑）和 execution_graph.py
（EventBus 处理 + RAG 索引）在主目录中，因为它们有 AgentLoop 无法替代的独特逻辑。

如需恢复: 将这些文件移回 ../ 并恢复 sop_graph.py 的 git 历史。
"""

# 阻止意外导入 — 这些模块不应再被直接引用
raise ImportError(
    "P0-1: 此 SubGraph 已归档。"
    "Skill 链执行已统一到 AgentLoop (aitest.agents.agent_runner.AgentLoop)。"
    "LangGraph 通过 make_agent_loop_node() 调用 AgentLoop。"
    "如需恢复，请将文件移回 ../ 目录。"
)
