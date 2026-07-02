"""CostAuditor — 成本追踪。"""

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CostRecord:
    agent_name: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    model: str = ""
    cost_usd: float = 0.0


# 每 1000 token 的成本 (USD)
_COST_PER_1K = {
    "claude-sonnet-4-6": {"input": 0.003, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "deepseek-chat": {"input": 0.00014, "output": 0.00028},
}


class CostAuditor:
    def __init__(self, data_dir: str | Path = None):
        self.data_dir = Path(data_dir) if data_dir else Path(".") / "kpi" / "cost"
        self.records: list[CostRecord] = []

    def record_cost(self, agent_name: str, tokens_in: int, tokens_out: int, model: str = "") -> None:
        cost = self._calculate_cost(tokens_in, tokens_out, model)
        record = CostRecord(
            agent_name=agent_name, tokens_in=tokens_in, tokens_out=tokens_out,
            model=model, cost_usd=cost,
        )
        self.records.append(record)

    def _calculate_cost(self, tokens_in: int, tokens_out: int, model: str) -> float:
        rates = _COST_PER_1K.get(model, {"input": 0.003, "output": 0.015})
        return (tokens_in * rates["input"] + tokens_out * rates["output"]) / 1000

    def total_cost(self) -> float:
        return sum(r.cost_usd for r in self.records)


def run_cost_audit(module: str, governance_path: str | Path = None) -> dict:
    return {"module": module, "total_cost": 0.0}
