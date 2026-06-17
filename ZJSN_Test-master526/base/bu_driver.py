# -*- coding: utf-8 -*-
"""BrowserUse Driver - AI-driven browser operation base class.

Built on browser-use open-source library (MIT). Provides NL-driven browser
automation for AITest Platform. Complementary to existing Selenium BasePage:

  - Selenium: deterministic regression (fast, reliable, deterministic)
  - BrowserUse: AI assist (PO generation, self-healing, exploratory testing)

Backend: Playwright Chromium (independent from Selenium ChromeDriver)
LLM:     Multi-provider — MiMo / Claude / Gemini, configured via .env

Env vars:
  BU_LLM_PROVIDER  — "mimo" | "claude" | "gemini" (default: "claude")
  MIMO_API_KEY     — MiMo API key
  MIMO_BASE_URL    — MiMo API base URL (OpenAI-compatible endpoint)
  MIMO_MODEL       — MiMo model name (default: "mimo-v2.5-pro")
  ANTHROPIC_API_KEY — Claude API key (existing)
  GOOGLE_API_KEY    — Gemini API key (existing)

Usage:
    import asyncio
    from base.bu_driver import BrowserUseDriver

    async def main():
        async with BrowserUseDriver(headless=False) as bu:
            await bu.login()
            result = await bu.run_task('navigate to hazard item page')
            print(result)
    asyncio.run(main())
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Ensure project root in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
# Load both project-root and ZJSN .env files (root has API key)
load_dotenv(_PROJECT_ROOT.parent / ".env")
load_dotenv(_PROJECT_ROOT / ".env")

from config import BASE_URL, DEFAULT_USERNAME, DEFAULT_PASSWORD

logger = logging.getLogger(__name__)


class BrowserUseDriver:
    """AI browser driver - wraps browser-use Agent + Browser lifecycle.

    Features:
    - Multi-LLM backend (MiMo / Claude / Gemini, env-driven)
    - Async context manager (async with)
    - Auto-login (NL-driven, adapts to Vue/Element Plus login page)
    - Supports headless/headed modes
    - Per-task token tracking
    """

    BASE_URL = BASE_URL
    DEFAULT_USERNAME = DEFAULT_USERNAME
    DEFAULT_PASSWORD = DEFAULT_PASSWORD

    # Provider defaults
    _PROVIDER_DEFAULTS = {
        "mimo": {
            "model": "mimo-v2.5-pro",
            "api_key_env": "MIMO_API_KEY",
            "base_url_env": "MIMO_BASE_URL",
            "model_env": "MIMO_MODEL",
        },
        "claude": {
            "model": "claude-sonnet-4-6",
            "api_key_env": "ANTHROPIC_API_KEY",
        },
        "gemini": {
            "model": "gemini-2.5-flash",
            "api_key_env": "GOOGLE_API_KEY",
        },
    }

    def __init__(
        self,
        headless: bool = False,
        max_steps: int = 30,
        provider: str = None,
        model: str = None,
        use_vision: bool = False,
    ):
        """Initialize BrowserUseDriver.

        Args:
            headless: Run browser in headless mode
            max_steps: Max agent steps per task (cost control)
            provider: LLM provider — "mimo" | "claude" | "gemini".
                      Default: BU_LLM_PROVIDER env, or "claude"
            model: Override model name. Default: provider's default model.
                   When use_vision=True with MiMo, auto-switches to
                   MIMO_VISION_MODEL or "mimo-v2.5" (full-modal).
            use_vision: Enable screenshot-based vision (MiMo: use mimo-v2.5)
        """
        self.headless = headless
        self.max_steps = max_steps
        self._provider_name = provider or os.getenv("BU_LLM_PROVIDER", "claude")

        # Auto-enable vision for MiMo (2x faster via screenshots vs DOM text)
        if self._provider_name == "mimo":
            self.use_vision = True  # vision is the fast path for MiMo
        else:
            self.use_vision = use_vision

        if self._provider_name not in self._PROVIDER_DEFAULTS:
            raise ValueError(
                f"Unknown BU_LLM_PROVIDER: '{self._provider_name}'. "
                f"Available: {list(self._PROVIDER_DEFAULTS.keys())}"
            )

        cfg = self._PROVIDER_DEFAULTS[self._provider_name]
        self.model = model or os.getenv(cfg.get("model_env", "")) or cfg["model"]

        # Auto-switch to vision model when use_vision=True with MiMo
        if self._provider_name == "mimo" and use_vision and not model:
            vision_model = os.getenv("MIMO_VISION_MODEL", "mimo-v2.5")
            if vision_model != self.model:
                logger.info("Vision mode: switching %s → %s", self.model, vision_model)
                self.model = vision_model

        self._browser = None
        self._llm = None
        self._total_tokens = 0
        self._logged_in = False

    # ═══════════════════════════════════════════════════════════════
    #  Context Manager
    # ═══════════════════════════════════════════════════════════════

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.close()

    # ═══════════════════════════════════════════════════════════════
    #  Lifecycle
    # ═══════════════════════════════════════════════════════════════

    async def start(self):
        """Launch browser + LLM instance (provider selected by BU_LLM_PROVIDER)."""
        self._llm = self._create_llm()

        from browser_use import Browser
        self._browser = Browser(headless=self.headless, keep_alive=True)
        logger.info("BrowserUseDriver started: provider=%s model=%s headless=%s",
                     self._provider_name, self.model, self.headless)

    async def close(self):
        """Close browser and release resources."""
        if self._browser:
            try:
                await self._browser.close()
            except Exception as e:
                logger.debug("Browser close error (ignored): %s", e)
            self._browser = None
        logger.info("BrowserUseDriver closed (total tokens: %d)", self._total_tokens)

    # ═══════════════════════════════════════════════════════════════
    #  LLM Factory
    # ═══════════════════════════════════════════════════════════════

    def _create_llm(self):
        """Create LLM instance based on provider.

        MiMo:   ChatOpenAI + custom base_url (OpenAI-compatible API)
        Claude: ChatAnthropic + ANTHROPIC_API_KEY
        Gemini: ChatGoogle + GOOGLE_API_KEY
        """
        cfg = self._PROVIDER_DEFAULTS[self._provider_name]
        key = os.getenv(cfg["api_key_env"], "")
        if not key:
            raise RuntimeError(
                f"{cfg['api_key_env']} not set. "
                f"Add it to .env file for provider '{self._provider_name}'."
            )

        if self._provider_name == "mimo":
            return self._create_mimo_llm(key, cfg)
        elif self._provider_name == "claude":
            return self._create_claude_llm(key)
        elif self._provider_name == "gemini":
            return self._create_gemini_llm(key)
        else:
            raise RuntimeError(f"Unsupported provider: {self._provider_name}")

    def _create_mimo_llm(self, api_key: str, cfg: dict):
        """MiMo-V2.5 via OpenAI-compatible API.

        MiMo-V2.5-Pro:  1.02T MoE, 42B active, 1M context
        MiMo-V2.5-Flash: 309B MoE, 15B active, 256K context
        MiMo-V2.5-Omni:  Full-modal (vision+text+audio)

        Uses browser-use's built-in ChatOpenAI (not langchain_openai)
        which has the required 'provider' attribute for Agent compatibility.
        """
        from browser_use import ChatOpenAI

        base_url = os.getenv(cfg.get("base_url_env", ""), "")
        if not base_url:
            raise RuntimeError(
                "MIMO_BASE_URL not set. Add MiMo API endpoint to .env.\n"
                "Examples:\n"
                "  Xiaomi official: https://api.xiaomimimo.com/v1\n"
                "  OpenRouter:      https://openrouter.ai/api/v1\n"
                "  Self-hosted:     http://your-server:8000/v1"
            )

        logger.info("MiMo LLM: model=%s base_url=%s", self.model, base_url)

        return ChatOpenAI(
            model=self.model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.0,
            add_schema_to_system_prompt=True,    # MiMo needs schema in prompt to format correctly
            dont_force_structured_output=True,    # MiMo wraps JSON in ``` fences
        )

    def _create_claude_llm(self, api_key: str):
        """Claude via Anthropic native API."""
        from browser_use import ChatAnthropic

        logger.info("Claude LLM: model=%s", self.model)

        return ChatAnthropic(
            model=self.model,
            api_key=api_key,
            temperature=0.0,
        )

    def _create_gemini_llm(self, api_key: str):
        """Gemini via Google native API."""
        from browser_use import ChatGoogle

        logger.info("Gemini LLM: model=%s", self.model)

        return ChatGoogle(
            model=self.model,
            api_key=api_key,
            temperature=0.0,
        )

    # ═══════════════════════════════════════════════════════════════
    #  Login
    # ═══════════════════════════════════════════════════════════════

    async def login(self, username: str = None, password: str = None):
        """AI-driven login flow.

        Uses natural language to guide LLM through login form.
        Adapts to Vue 3 + Element Plus login page.

        Args:
            username: Override default username
            password: Override default password
        """
        from browser_use import Agent

        username = username or self.DEFAULT_USERNAME
        password = password or self.DEFAULT_PASSWORD

        if not password:
            raise ValueError("DEFAULT_PASSWORD is empty, set it in .env")

        task = f"""
Go to {self.BASE_URL}#/login and login.

On the login page:
1. If page shows loading spinner, wait up to 10 seconds for login form to appear.
2. Type "{username}" into username input (placeholder "请输入账号").
3. Type "{password}" into password input (type="password").
4. Click blue "登录" button.
5. Wait. If URL changes to #/welcome → done with success=True.
   If error toast → done with success=False and error message.
"""
        logger.info("Starting AI login: user=%s", username)

        agent = Agent(
            task=task,
            llm=self._llm,
            browser=self._browser,
            use_vision=self.use_vision,
        )

        result = await agent.run()
        self._logged_in = True
        self._total_tokens += self._extract_token_count(result)

        logger.info("AI login completed")
        return result

    async def ensure_logged_in(self):
        """Ensure logged in - perform login if not already done."""
        if not self._logged_in:
            await self.login()

    # ═══════════════════════════════════════════════════════════════
    #  Core: Run Task
    # ═══════════════════════════════════════════════════════════════

    async def run_task(self, task: str, max_steps: int = None):
        """Execute a natural language browser task.

        Args:
            task: Natural language task description
            max_steps: Override default max steps

        Returns:
            Agent final response text
        """
        from browser_use import Agent

        await self.ensure_logged_in()

        steps = max_steps or self.max_steps
        logger.info("Running BrowserUse task (max_steps=%d): %s", steps, task[:200])

        agent = Agent(
            task=task,
            llm=self._llm,
            browser=self._browser,
            use_vision=self.use_vision,
        )

        result = await agent.run()
        self._total_tokens += self._extract_token_count(result)

        logger.info("Task completed")
        return result

    async def navigate_and_observe(self, hash_route: str):
        """Navigate to a hash route and return page observation.

        Used as the first step of Page Object generation.

        Args:
            hash_route: Vue hash route, e.g. '#/warehouse/hazard/item'

        Returns:
            LLM description of page structure
        """
        task = f"""
Navigate to: {self.BASE_URL}{hash_route}

Wait for full page load, then observe and list:
1. Page title / breadcrumb
2. Search/filter fields (input/select/date-picker)
3. Action buttons (add/search/reset/export)
4. Table columns
5. Pagination (present or not)

This is an Element Plus SPA - wait for async components to render.
"""
        return await self.run_task(task)

    # ═══════════════════════════════════════════════════════════════
    #  Utilities
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _extract_token_count(result) -> int:
        """Extract token usage from AgentHistoryList."""
        try:
            total = 0
            if hasattr(result, 'history') and result.history:
                for h in result.history:
                    if hasattr(h, 'metadata') and h.metadata:
                        total += h.metadata.get('input_tokens', 0)
                        total += h.metadata.get('output_tokens', 0)
            return total
        except Exception:
            return 0

    @property
    def total_tokens(self) -> int:
        return self._total_tokens

    @property
    def estimated_cost(self) -> float:
        """Estimated API cost in USD.

        MiMo-V2.5: ~$0.50-1.50/1M tokens (varies by provider)
        Claude Sonnet: $3/$15 per 1M input/output
        Gemini Flash: free tier available
        """
        rate_map = {
            "mimo": 1.0,
            "claude": 5.0,
            "gemini": 0.0,
        }
        rate = rate_map.get(self._provider_name, 5.0)
        return self._total_tokens / 1_000_000 * rate
