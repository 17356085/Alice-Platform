"""Runtime data types — shared structures used across runtime implementations.

These are pure data classes with no business logic, used by:
  - runtime implementations (BrowserRuntime, APIRuntime)
  - discovery strategies (BrowserUseDiscovery)
  - capabilities (browser_adapter)

Moved from platform.runtime to eliminate circular dependency:
  runtime → platform.runtime.PageStructure ❌
  runtime → runtime.types.PageStructure ✅
"""

from dataclasses import dataclass, field


@dataclass
class PageStructure:
    """Standardized page observation result — runtime-agnostic.

    Used by Runtime.observe() to return structured page information
    regardless of the underlying automation technology (BrowserUse, Playwright, etc.).
    """
    page_title: str = ""
    search_fields: list[dict] = field(default_factory=list)
    action_buttons: list[dict] = field(default_factory=list)
    table_columns: list[str] = field(default_factory=list)
    has_pagination: bool = False
    has_checkbox_column: bool = False
    raw_html_snapshot: str = ""
    screenshot_base64: str = ""
