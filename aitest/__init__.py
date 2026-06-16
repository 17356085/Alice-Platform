"""aitest — AI 自动化测试平台工具包

P0 重构 (2026-06-12): 加入 AgentLoop，从伪 Agent 升级为真 Agent 循环。
"""
__version__ = "0.2.0"

from aitest.agent_runner import (
    AgentLoop,
    AgentState,
    Observation,
    AGENT_SKILL_MAP,
    run_skill,
    run_agent,
    list_agents,
)
from aitest.llm.provider import (
    LLMResponse,
    LLMProvider,
    get_provider,
    list_providers,
)
# P1-1: 追踪模块
from aitest.trace import (
    TraceEvent,
    TraceContext,
    write_trace_event,
    query_trace_events,
    get_trace_summary,
)
# P1-2: 评估模块
from aitest.evaluator import (
    EvalRunner,
    EvalMetric,
    EvalRun,
    _score_response,
)
# P1-3: A/B 测试模块
from aitest.ab_test import (
    ABTestRunner,
    ABTestResult,
)
# P1-4: 回归测试模块
from aitest.regression import (
    RegressionRunner,
    RegressionResult,
)
