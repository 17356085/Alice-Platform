"""ReviewTrigger — 审查触发器。"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ReviewTrigger:
    def __init__(self, governance_path: str | Path = None):
        self.governance = Path(governance_path) if governance_path else None

    def should_review(self, module: str, phase: str, result: dict) -> bool:
        if result.get("status") == "failed":
            return True
        if len(result.get("quality_issues", [])) > 0:
            return True
        return False
