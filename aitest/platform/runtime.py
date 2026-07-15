"""Platform runtime compatibility exports and composition registration."""

from aitest.runtime.base import (
    PageStructure,
    Runtime,
    register_capability_factory,
    register_page_executor,
)
from aitest.runtime.browser import BrowserRuntime, RemoteBrowserRuntime

from .capabilities.browser_adapter import register_browser_capabilities
from .page_execution import execute_page_config

# Keep the public platform runtime behavior while the implementation and
# contract live in the dependency-neutral runtime package.
register_capability_factory(register_browser_capabilities)
register_page_executor(execute_page_config)

__all__ = [
    "Runtime",
    "PageStructure",
    "BrowserRuntime",
    "RemoteBrowserRuntime",
]
