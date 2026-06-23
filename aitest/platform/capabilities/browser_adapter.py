"""
BrowserCapabilityAdapters — thin wrappers over BrowserRuntime.

These adapters implement Capability ABCs by delegating to BrowserRuntime.
Zero business logic — pure delegation. BrowserRuntime is unchanged.

Each adapter is a single-responsibility wrapper around the corresponding
aspect of BrowserRuntime.
"""

from typing import Any

from .abc import Navigator, Observer, Interactor, Authenticator, CapabilityRegistry

# Lazy import to avoid circular dependency
def _get_runtime_types():
    from aitest.platform.runtime import BrowserRuntime, PageStructure
    return BrowserRuntime, PageStructure


class BrowserNavigatorAdapter(Navigator):
    """Navigator → BrowserRuntime.navigate() / .back() / .refresh()"""

    def __init__(self, runtime):
        self._rt = runtime

    async def goto(self, target: str) -> None:
        await self._rt.navigate(target)

    async def back(self) -> None:
        await self._rt.execute("Go back to the previous page")

    async def refresh(self) -> None:
        await self._rt.execute("Refresh the current page")

    async def current_url(self) -> str:
        # BrowserRuntime doesn't expose this directly — use execute
        try:
            result = await self._rt.execute("What is the current page URL? Return ONLY the URL string.")
            return str(result).strip()
        except Exception:
            return ""


class BrowserObserverAdapter(Observer):
    """Observer → BrowserRuntime.observe() / .screenshot()"""

    def __init__(self, runtime):
        self._rt = runtime

    async def snapshot(self):
        _, PageStructure = _get_runtime_types()
        return await self._rt.observe()

    async def screenshot(self) -> bytes:
        return await self._rt.screenshot()

    async def dom(self) -> str:
        try:
            result = await self._rt.execute("Return the FULL HTML source of the current page.")
            return str(result)
        except Exception:
            return ""

    async def console_logs(self) -> list[str]:
        try:
            result = await self._rt.execute("Return all browser console log messages as a JSON array of strings.")
            import json
            return json.loads(str(result)) if isinstance(result, str) else []
        except Exception:
            return []

    async def network_trace(self) -> list[dict]:
        try:
            result = await self._rt.execute(
                "Return all network requests made by this page as a JSON array. "
                "Each entry: {url, method, status, type}. Return ONLY the JSON."
            )
            import json
            return json.loads(str(result)) if isinstance(result, str) else []
        except Exception:
            return []


class BrowserInteractorAdapter(Interactor):
    """Interactor → BrowserRuntime.execute() for NL-driven interaction"""

    def __init__(self, runtime):
        self._rt = runtime

    async def click(self, description: str) -> bool:
        try:
            await self._rt.execute(f"Click on: {description}")
            return True
        except Exception:
            return False

    async def type(self, field: str, value: str) -> bool:
        try:
            await self._rt.execute(
                f"Find the input field matching '{field}' and type '{value}' into it"
            )
            return True
        except Exception:
            return False

    async def select(self, field: str, value: str) -> bool:
        try:
            await self._rt.execute(
                f"Find the dropdown/select matching '{field}' and select '{value}'"
            )
            return True
        except Exception:
            return False

    async def wait(self, condition: str) -> None:
        await self._rt.execute(f"Wait until: {condition}")

    async def execute(self, action: str) -> Any:
        return await self._rt.execute(action)


class BrowserAuthenticatorAdapter(Authenticator):
    """Authenticator → BrowserRuntime.login()"""

    def __init__(self, runtime):
        self._rt = runtime
        self._logged_in = False

    async def login(self, credentials: dict) -> bool:
        username = credentials.get("username", "")
        password = credentials.get("password", "")
        result = await self._rt.login(credentials={
            "username": username,
            "password": password,
        })
        self._logged_in = result
        return result

    async def logout(self) -> None:
        try:
            await self._rt.execute("Log out of the application. Click the logout/user menu button.")
            self._logged_in = False
        except Exception:
            pass

    async def is_authenticated(self) -> bool:
        return self._logged_in


# ── Convenience: register all browser capabilities ───────────────────────

def register_browser_capabilities(runtime) -> CapabilityRegistry:
    """
    Register all 4 Browser capability adapters for a BrowserRuntime.

    Usage:
        rt = BrowserRuntime(base_url="...")
        rt._capabilities = register_browser_capabilities(rt)
    """
    registry = CapabilityRegistry()
    registry.register(Navigator, BrowserNavigatorAdapter(runtime))
    registry.register(Observer, BrowserObserverAdapter(runtime))
    registry.register(Interactor, BrowserInteractorAdapter(runtime))
    registry.register(Authenticator, BrowserAuthenticatorAdapter(runtime))
    return registry
