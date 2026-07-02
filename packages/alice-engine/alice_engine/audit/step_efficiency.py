"""StepEfficiency — 步骤效率分析。"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StepMetrics:
    skill_id: str = ""
    elapsed_seconds: float = 0.0
    tokens_used: int = 0
    retry_count: int = 0
    status: str = ""


class StepEfficiencyAnalyzer:
    def __init__(self):
        self.metrics: list[StepMetrics] = []

    def record(self, skill_id: str, elapsed: float, tokens: int, retries: int, status: str) -> None:
        self.metrics.append(StepMetrics(
            skill_id=skill_id, elapsed_seconds=elapsed,
            tokens_used=tokens, retry_count=retries, status=status,
        ))

    def analyze(self) -> dict:
        if not self.metrics:
            return {"total_steps": 0}
        return {
            "total_steps": len(self.metrics),
            "avg_elapsed": sum(m.elapsed_seconds for m in self.metrics) / len(self.metrics),
            "total_tokens": sum(m.tokens_used for m in self.metrics),
            "total_retries": sum(m.retry_count for m in self.metrics),
        }
