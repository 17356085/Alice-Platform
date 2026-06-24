"""aitest — AI 自动化测试平台工具包

v1.0: Architecture Complete — Design Freeze.
  5 layers (Platform Core / Agent Runtime / Infrastructure / Domain / Experimental)
  12 agents with capability enforcement + phase-aware model tiering.
"""
__version__ = "1.6.0"

from aitest.agents.agent_runner import (
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
from aitest.infra.trace import (
    TraceEvent,
    TraceContext,
    write_trace_event,
    query_trace_events,
    get_trace_summary,
)
# P1-2: 评估模块
from aitest.testing.evaluator import (
    EvalRunner,
    EvalMetric,
    EvalRun,
    _score_response,
)
# P1-3: A/B 测试模块
from aitest.agents.ab_test import (
    ABTestRunner,
    ABTestResult,
)
# P1-4: 回归测试模块
from aitest.testing.regression import (
    RegressionRunner,
    RegressionResult,
)
