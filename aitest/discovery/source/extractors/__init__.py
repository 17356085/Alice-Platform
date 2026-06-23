"""Source code extractors — each produces metadata from a specific aspect of source code."""

from .base import BaseExtractor
from .vue_router import VueRouterExtractor
from .vue_component import VueComponentExtractor
from .api_extractor import ApiExtractor

__all__ = [
    "BaseExtractor",
    "VueRouterExtractor",
    "VueComponentExtractor",
    "ApiExtractor",
]
