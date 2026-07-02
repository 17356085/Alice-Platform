"""QALoop — QA 循环。"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class QALoop:
    def __init__(self, max_iterations: int = 3):
        self.max_iterations = max_iterations
        self.iteration = 0

    def run(self, check_fn, fix_fn, context: dict = None) -> dict:
        for i in range(self.max_iterations):
            self.iteration = i + 1
            result = check_fn(context or {})
            if result.get("passed"):
                return {"passed": True, "iterations": self.iteration}
            fix_fn(result, context or {})
        return {"passed": False, "iterations": self.max_iterations}
