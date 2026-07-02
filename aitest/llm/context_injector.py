"""ContextInjector — 平台特有，保持原始代码。"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ContextInjector:
    """上下文注入器 — 平台特有实现。"""

    def __init__(self):
        self._cache = {}

    def inject(self, skill_id: str, system_prompt: str, context_vars: dict = None) -> str:
        """注入上下文到 system prompt。"""
        return system_prompt

    def cache_stats(self) -> dict:
        return {"hits": 0, "misses": 0}
