"""OnlineMonitor — 执行在线监控。"""

import json
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class RunMetrics:
    agent_name: str = ""
    module: str = ""
    page: str = ""
    total_steps: int = 0
    completed_skills: int = 0
    failed_skills: int = 0
    elapsed_seconds: float = 0.0
    total_tokens: int = 0
    success: bool = False


class OnlineMonitor:
    def __init__(self, data_dir: str | Path = None):
        self.data_dir = Path(data_dir) if data_dir else Path(".") / "kpi" / "online"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def record_run(self, module: str, metrics: RunMetrics) -> None:
        date_str = datetime.now().strftime("%Y-%m-%d")
        filepath = self.data_dir / f"online-{module}-{date_str}.jsonl"
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(metrics), ensure_ascii=False) + "\n")

    def analyze(self, module: str, days: int = 7) -> dict:
        return {"module": module, "days": days, "runs": 0}


def collect_run_metrics(state) -> RunMetrics:
    return RunMetrics(
        agent_name=getattr(state, "agent_name", ""),
        module=getattr(state, "module", ""),
        page=getattr(state, "page", ""),
        total_steps=getattr(state, "step", 0),
        completed_skills=len(getattr(state, "completed_skills", [])),
        failed_skills=len(getattr(state, "failed_skills", {})),
        success=getattr(state, "success", False),
    )
