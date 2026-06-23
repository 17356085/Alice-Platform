"""
Discovery Layer — discovers application structure and outputs standardized .discovery/ directory.

Strategies:
  BrowserUseDiscovery — AI-driven sidebar scan + page observation
  ManualDiscovery — from project.yaml navigation config
  VueSourceDiscovery — parse Vue router.ts (Phase C)
  ReactSourceDiscovery — parse React router (Phase C)

All strategies output the same format:
  .discovery/pages.json     — [{id, title, route, menu_path, elements, ...}]
  .discovery/menu_tree.json — [{label, children: [{label, route, ...}]}]

Skills and agents read from .discovery/, never from raw directory structure.
"""

from .base import BaseDiscovery, DiscoveryIndex, PageRecord, MenuNode
from .browser_use import BrowserUseDiscovery

__all__ = [
    "BaseDiscovery",
    "DiscoveryIndex",
    "PageRecord",
    "MenuNode",
    "BrowserUseDiscovery",
]
