"""GovernanceKPI — 治理指标收集。"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class KPIDataPoint:
    timestamp: str = ""
    module: str = ""
    metric: str = ""
    value: float = 0.0
    tags: dict = field(default_factory=dict)


class KPICollector:
    def __init__(self, data_dir: str | Path = None):
        self.data_dir = Path(data_dir) if data_dir else Path(".") / "kpi"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.points: list[KPIDataPoint] = []

    def record(self, module: str, metric: str, value: float, tags: dict = None) -> None:
        from datetime import datetime
        point = KPIDataPoint(
            timestamp=datetime.now().isoformat(),
            module=module, metric=metric, value=value, tags=tags or {},
        )
        self.points.append(point)

    def summary(self) -> dict:
        return {"total_points": len(self.points)}
