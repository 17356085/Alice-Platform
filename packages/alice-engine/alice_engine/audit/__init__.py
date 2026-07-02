"""Audit — 审计能力。

已迁移到 runtime/observability/ 的模块:
  - safety_auditor → runtime.observability
  - failure_attributor → runtime.observability

已迁移到 extensions/ 的模块:
  - online_monitor → extensions/monitor
  - cost_auditor → extensions/cost
  - diff_extractor → extensions/diff

保留在 audit/ 的模块 (平台特有):
  - governance_kpi
  - qa_loop
  - review_trigger
  - scheduled_audit
  - step_efficiency
"""

# 向后兼容: 从新位置导入
from alice_engine.runtime.observability import (  # noqa: F401
    SafetyFlag,
    FailureCategory,
    check_output_safety,
    attribute_failure,
)

from alice_engine.extensions.diff import extract_diff  # noqa: F401
from alice_engine.extensions.monitor import OnlineMonitor, RunMetrics  # noqa: F401
from alice_engine.extensions.cost import CostAuditor  # noqa: F401

# 保留的模块
from alice_engine.audit.governance_kpi import KPICollector  # noqa: F401
from alice_engine.audit.qa_loop import QALoop  # noqa: F401
from alice_engine.audit.review_trigger import ReviewTrigger  # noqa: F401
from alice_engine.audit.scheduled_audit import run_all_audits  # noqa: F401
from alice_engine.audit.step_efficiency import StepEfficiencyAnalyzer  # noqa: F401

__all__ = [
    # 从 runtime.observability 导入
    "SafetyFlag",
    "FailureCategory",
    "check_output_safety",
    "attribute_failure",
    # 从 extensions 导入
    "extract_diff",
    "OnlineMonitor",
    "RunMetrics",
    "CostAuditor",
    # 保留的模块
    "KPICollector",
    "QALoop",
    "ReviewTrigger",
    "run_all_audits",
    "StepEfficiencyAnalyzer",
]
