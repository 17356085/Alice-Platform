"""FailureAttributor — 失败归因分析。"""

import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FailureCategory:
    category: str = ""
    confidence: float = 0.0
    detail: str = ""


_PATTERNS = [
    ("prompt", [r"prompt.*too long", r"context.*exceeded", r"token.*limit"]),
    ("tool_desc", [r"tool.*not found", r"function.*not available"]),
    ("schema", [r"json.*invalid", r"schema.*mismatch", r"validation.*error"]),
    ("context_pollution", [r"hallucination", r"made up", r"fabricat"]),
    ("retrieval", [r"no.*relevant", r"search.*empty", r"knowledge.*missing"]),
    ("env_permission", [r"permission.*denied", r"access.*forbidden", r"auth.*fail"]),
]


def attribute_failure(observation, response_content: str = "") -> FailureCategory:
    content = response_content or getattr(observation, "raw_output_full", "") or ""
    if not content:
        return FailureCategory(category="unknown", confidence=0.0)

    content_lower = content.lower()
    for category, patterns in _PATTERNS:
        for pattern in patterns:
            if re.search(pattern, content_lower):
                return FailureCategory(category=category, confidence=0.8, detail=pattern)

    return FailureCategory(category="unknown", confidence=0.0)
