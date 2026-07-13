# -*- coding: utf-8 -*-
"""BrowserUse Driver - AI-driven browser operation base class.

Built on browser-use open-source library (MIT). Provides NL-driven browser
automation for AITest Platform. Complementary to Selenium BasePage:

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
  BASE_URL          — SUT base URL (default: http://localhost:8081/)
  DEFAULT_USERNAME  — Login username (default: admin)
  DEFAULT_PASSWORD  — Login password (default: empty)

Location: aitest/integrations/bu_driver.py (platform-owned, no ZJSN dependency)

Usage:
    import asyncio
    from aitest.integrations.bu_driver import BrowserUseDriver

    async def main():
        async with BrowserUseDriver(headless=False) as bu:
            await bu.login()
            result = await bu.run_task('navigate to hazard item page')
            logger.info(result)
    asyncio.run(main())
"""

import asyncio
import logging
import sys
import warnings
from pathlib import Path

from aitest.config import config

# ── Configuration (env-var driven via unified config) ─────────────────
BASE_URL = config.base_url
DEFAULT_USERNAME = config.default_username
DEFAULT_PASSWORD = config.default_password

logger = logging.getLogger(__name__)


# ── MiMo output fixers ──────────────────────────────────────────────
# MiMo has two output format issues that break browser-use's Pydantic
# validation:
#   1. Wraps JSON in ```json fences
#   2. Outputs bare strings for nested object fields (e.g.
#      {"evaluate": "code"} instead of {"evaluate": {"code": "code"}})
#
# Both are fixed in the monkey-patched get_client() in _create_mimo_llm().

def _strip_json_fence(text: str) -> str:
    """Extract clean JSON from model output that may contain fences or preamble.

    Handles patterns:
    1. Entire text is a single fenced block: ```json\n{...}\n```
    2. Text with preamble + fenced block: "Some text...\n```json\n{...}\n```"
    3. Multiple fenced blocks: extracts the last one (usually the actual JSON)
    4. Text with preamble but no fence: "Looking at...\n{...}" — extracts JSON object
    """
    import re
    text = text.strip()

    # Pattern 1: entire text is one fenced block
    m = re.match(r'^```(?:json)?\s*\n?(.*?)\n?\s*```\s*$', text, re.DOTALL)
    if m:
        return m.group(1).strip()

    # Pattern 2/3: extract the LAST ```json ... ``` block in the text
    blocks = re.findall(r'```(?:json)?\s*\n(.*?)\n\s*```', text, re.DOTALL)
    if blocks:
        return blocks[-1].strip()

    # Pattern 4: no fences — try to extract the first JSON object from the text.
    # MiMo often outputs "Looking at...\n{...}" where {...} is the actual payload.
    # Find the first { that starts a JSON object and match to its closing }.
    brace_start = text.find('{')
    if brace_start >= 0:
        depth = 0
        for i in range(brace_start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    candidate = text[brace_start:i+1]
                    # Validate it's actually parseable JSON
                    import json as _json
                    try:
                        _json.loads(candidate)
                        return candidate
                    except _json.JSONDecodeError:
                        pass  # Not valid JSON, keep looking
                    break  # Found matching brace but not valid JSON — stop

    return text


# Fields that browser-use expects as nested objects but MiMo may output
# as bare strings. Map: field_name → wrapper_key
_MIMO_NESTED_FIELDS = {
    "evaluate": "code",
    "write_file": "content",     # WriteFileAction: {file_name, content, ...}
    "replace_file": "content",
    "read_file": None,           # ReadFileAction just has file_name, no wrapping needed
}


def _fix_mimo_action_schema(text: str) -> str:
    """Fix MiMo's common schema mistakes in browser-use AgentOutput JSON.

    Handles multiple MiMo output patterns:
    1. Bare string action fields: {"evaluate": "code"} → {"evaluate": {"code": "code"}}
    2. Invalid action like {"screenshot": {}} → replace with {"wait": {"seconds": 1}}
    3. Raw data without action field: {"page_title": "..."} → wrap in done action
    4. action is not a list: "action": "done" → "action": [{"done": {"text": "...", "success": true}}]
    """
    import json as _json

    try:
        data = _json.loads(text)
    except _json.JSONDecodeError:
        return text

    if not isinstance(data, dict):
        return text

    # Pattern 3: No "action" field — MiMo returned raw data (page observation, etc.)
    # Wrap it in a done action so the agent can complete.
    if "action" not in data:
        # Check if it looks like page observation data
        if any(k in data for k in ("page_title", "search_fields", "table_columns", "diagnostics", "menu_items")):
            done_action = {"done": {"text": _json.dumps(data, ensure_ascii=False), "success": True}}
            wrapped = {"current_state": {"evaluation_previous_goal": "Success", "memory": "", "next_goal": "Task complete"}, "action": [done_action]}
            return _json.dumps(wrapped, ensure_ascii=False)
        return text

    actions = data["action"]

    # Pattern 4: action is not a list — wrap in list
    if isinstance(actions, str):
        if actions in ("done", "complete", "finish"):
            data["action"] = [{"done": {"text": "Task completed", "success": True}}]
            return _json.dumps(data, ensure_ascii=False)
        return text

    if not isinstance(actions, list):
        return text

    fixed = False
    cleaned_actions = []
    for action in actions:
        if not isinstance(action, dict):
            cleaned_actions.append(action)
            continue

        # Pattern 2: Invalid action like {"screenshot": {}} — replace with wait
        if "screenshot" in action and len(action) == 1:
            action = {"wait": {"seconds": 1}}
            fixed = True

        # Pattern 1: Bare string action fields
        for field, wrapper_key in _MIMO_NESTED_FIELDS.items():
            if field in action and isinstance(action[field], str):
                if wrapper_key:
                    action[field] = {wrapper_key: action[field]}
                    fixed = True
            if field in action and isinstance(action[field], dict) and wrapper_key:
                keys = list(action[field].keys())
                if wrapper_key not in keys and len(keys) == 1 and isinstance(action[field][keys[0]], str):
                    action[field] = {wrapper_key: action[field][keys[0]]}
                    fixed = True

        cleaned_actions.append(action)

    if fixed:
        data["action"] = cleaned_actions
        return _json.dumps(data, ensure_ascii=False)
    return text


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
        base_url: str = None,
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
            base_url: Override SUT base URL (default: env BASE_URL)
        """
        self.headless = headless
        self.max_steps = max_steps
        self._provider_name = provider or config.bu_llm_provider

        # Per-instance base URL override for SUT navigation
        if base_url:
            self.BASE_URL = base_url

        if self._provider_name not in self._PROVIDER_DEFAULTS:
            raise ValueError(
                f"Unknown BU_LLM_PROVIDER: '{self._provider_name}'. "
                f"Available: {list(self._PROVIDER_DEFAULTS.keys())}"
            )

        cfg = self._PROVIDER_DEFAULTS[self._provider_name]
        provider_cfg = config.get_provider_config(self._provider_name)
        self.model = model or provider_cfg["model"]

        # Vision: only enable if provider explicitly supports multimodal input.
        # MiMo text-only endpoints do NOT support image input — forcing vision
        # causes 404 errors on every Agent step. Use DOM text mode by default.
        if use_vision:
            if self._provider_name in ("claude", "gemini"):
                self.use_vision = True
            elif self._provider_name == "mimo":
                if model and ("vision" in model.lower() or "omni" in model.lower()):
                    self.use_vision = True
                    logger.info("MiMo vision mode: using multimodal model %s", self.model)
                else:
                    logger.warning(
                        "MiMo provider does not support image input with model '%s'. "
                        "Use DOM text mode instead. Set BU_LLM_PROVIDER=claude for vision.",
                        self.model,
                    )
                    self.use_vision = False
        else:
            self.use_vision = False

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
        """Launch browser + LLM instance (provider selected by BU_LLM_PROVIDER).

        Idempotent: if browser already exists, skips creation to preserve session.
        """
        if self._llm is None:
            self._llm = self._create_llm()

        # ── Ensure screenshots directory resilience ──
        self._ensure_screenshot_dir_resilience()

        if self._browser is None:
            from browser_use import Browser
            self._browser = Browser(headless=self.headless, keep_alive=True)
            await self._browser.start()
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

    def __del__(self):
        """Fallback cleanup: warn if browser was not explicitly closed.

        A leaked Browser process can consume 200-500 MB RSS. This does NOT
        close the browser (no async in __del__), but emits a loud warning
        so the leak is visible in logs and can be traced to its call site.
        """
        if self._browser is not None:
            warnings.warn(
                f"BrowserUseDriver.__del__: browser was not closed! "
                f"Provider={self._provider_name}, model={self.model}. "
                f"Always use 'async with BrowserUseDriver()' or call await driver.close(). "
                f"This leaks a Chromium process (~200-500 MB RSS).",
                ResourceWarning,
                stacklevel=2,
            )
            # Best-effort: try to schedule close on the event loop if one is running.
            # This is a last-resort fallback and may not work in all contexts.
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    loop.create_task(self.close())
            except RuntimeError:
                pass  # No running loop — nothing we can do

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
        provider_cfg = config.get_provider_config(self._provider_name)
        key = provider_cfg.get("api_key")
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

        MiMo-V2.5:     310B, omnimodal (text+image+audio+video), 1.05M ctx
        MiMo-V2.5-Pro: 1.02T MoE, text-only, 1.05M ctx, $0.435/$0.87 per 1M

        Uses _MiMoChatOpenAI — a ChatOpenAI subclass that strips ```json
        fences from API responses before browser-use parses them.
        """
        from browser_use import ChatOpenAI

        base_url = config.mimo_base_url
        if not base_url:
            raise RuntimeError(
                "MIMO_BASE_URL not set. Add MiMo API endpoint to .env.\n"
                "Examples:\n"
                "  Xiaomi official: https://api.xiaomimimo.com/v1\n"
                "  OpenRouter:      https://openrouter.ai/api/v1\n"
                "  Self-hosted:     http://your-server:8000/v1"
            )

        logger.info("MiMo LLM: model=%s base_url=%s", self.model, base_url)

        llm = ChatOpenAI(
            model=self.model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.0,
            add_schema_to_system_prompt=True,
            dont_force_structured_output=True,  # Schema in prompt, NOT response_format
        )

        # Monkey-patch to strip ```json fences from MiMo responses.
        # Strategy: patch get_client() to intercept raw API responses and clean
        # them BEFORE browser-use's ainvoke processes them.
        _orig_get_client = llm.get_client

        def _patched_get_client():
            client = _orig_get_client()
            _orig_create = client.chat.completions.create

            async def _stripped_create(**kwargs):
                response = await _orig_create(**kwargs)
                if response and response.choices:
                    for choice in response.choices:
                        if choice.message and choice.message.content:
                            raw = choice.message.content
                            content = _strip_json_fence(raw)
                            content = _fix_mimo_action_schema(content)
                            if content != raw:
                                logger.debug("MiMo output patched: %d→%d chars", len(raw), len(content))
                            choice.message.content = content
                return response

            client.chat.completions.create = _stripped_create
            return client

        llm.get_client = _patched_get_client

        # Additional safety: patch ainvoke to catch and fix any remaining
        # validation failures (e.g. if get_client patch didn't fire).
        _orig_ainvoke = llm.ainvoke

        async def _patched_ainvoke(messages, output_format=None, **kwargs):
            try:
                return await _orig_ainvoke(messages, output_format=output_format, **kwargs)
            except Exception as e:
                err_msg = str(e)
                if output_format is not None and ('json_invalid' in err_msg or 'Invalid JSON' in err_msg):
                    logger.warning("MiMo JSON validation failed, attempting recovery: %s", err_msg[:200])
                    # Re-call without output_format to get raw text, then clean and validate
                    try:
                        raw_result = await _orig_ainvoke(messages, output_format=None, **kwargs)
                        raw_text = raw_result.completion if hasattr(raw_result, 'completion') else str(raw_result)
                        cleaned = _strip_json_fence(raw_text)
                        cleaned = _fix_mimo_action_schema(cleaned)
                        parsed = output_format.model_validate_json(cleaned)
                        from browser_use.llm.views import ChatInvokeCompletion
                        logger.info("MiMo recovery successful")
                        return ChatInvokeCompletion(
                            completion=parsed,
                            usage=getattr(raw_result, 'usage', None),
                            stop_reason=getattr(raw_result, 'stop_reason', None),
                        )
                    except Exception as inner_e:
                        logger.debug("MiMo recovery also failed: %s", inner_e)
                raise

        llm.ainvoke = _patched_ainvoke
        return llm

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
        """Login using JavaScript DOM injection — no LLM credential guessing.

        Strategy:
        1. Navigate to base URL via Browser
        2. JavaScript: find password field → login page detected
        3. JavaScript: fill username + password + click submit (deterministic)
        4. JavaScript: check for error message or sidebar → result
        """
        username = username or self.DEFAULT_USERNAME
        password = password or self.DEFAULT_PASSWORD

        if not password:
            raise ValueError("DEFAULT_PASSWORD is empty, set it in .env")

        if self._logged_in:
            logger.info("Already logged in — skipping login flow")
            return True

        # ── Stage 1: Navigate to base URL + detect login page ──
        logger.info("Login: navigating to %s", self.BASE_URL)
        await self._browser.navigate_to(self.BASE_URL)

        # Wait for page DOM readiness — SPA can take 8s+ (poll up to 18s)
        #
        # Generic readiness check (framework-agnostic):
        #   Any SPA eventually renders standard HTML elements (input, button,
        #   a[href]). Skeletons use fake elements or zero-dimension placeholders.
        #   So: check that at least one interactive element exists AND has
        #   non-zero dimensions (offsetWidth/offsetHeight > 0).
        #   This works for Element Plus, Ant Design, Vuetify, MUI, etc.
        #
        #   Fallback: if no interactive elements at all (rare), check that
        #   body.innerText has meaningful length (>15 chars).
        import asyncio
        _READY_JS = """() => {
            const els = document.querySelectorAll(
                'input, button, select, textarea, a[href], [role=button], [role=menuitem], [role=link], [role=tab]'
            );
            for (const el of els) {
                if (el.offsetWidth > 0 || el.offsetHeight > 0) return true;
            }
            // Fallback: meaningful text content (not just "加载中...")
            const txt = (document.body.innerText || '').trim();
            return txt.length > 10;
        }"""

        page_ready = False
        for retry in range(2):  # up to 2 attempts: initial + 1 reload
            for _ in range(12):
                await asyncio.sleep(1.5)
                try:
                    page = await self._browser.get_current_page()
                    if page and await page.evaluate(_READY_JS):
                        page_ready = True
                        break
                except Exception:
                    pass
            if page_ready:
                break
            # First attempt failed — reload and retry
            if retry == 0:
                logger.warning("Page DOM not ready after 18s — reloading and retrying")
                try:
                    page = await self._browser.get_current_page()
                    if page:
                        await page.reload(wait_until="domcontentloaded", timeout=15000)
                except Exception:
                    await self._browser.navigate_to(self.BASE_URL)
        if not page_ready:
            logger.warning("Page DOM not ready after 36s — proceeding anyway")

        # JavaScript: detect login page by looking for password field or login form.
        # Element Plus wraps inputs in components, so input[type=password] may not
        # exist in the DOM. Also check for placeholders containing login keywords.
        detect_js = """() => {
            // Try multiple selectors for password field
            let pwds = document.querySelectorAll('input[type=password]');
            if (pwds.length === 0) {
                // Broader check: any input with password-related placeholder
                const allInputs = document.querySelectorAll('input');
                const pwdByPlaceholder = Array.from(allInputs).filter(i => {
                    const ph = (i.placeholder || '').toLowerCase();
                    return ph.includes('密码') || ph.includes('password') || ph.includes('pass');
                });
                if (pwdByPlaceholder.length > 0) pwds = pwdByPlaceholder;
            }
            if (pwds.length === 0) {
                // Still no password field. Check for login button as indicator.
                const buttons = document.querySelectorAll('button, [role=button]');
                const loginBtn = Array.from(buttons).some(b => {
                    const txt = (b.textContent || '').trim();
                    return txt === '登 录' || txt === '登录' || txt === 'Login' || txt === 'Sign In';
                });
                if (loginBtn) {
                    // Has login button but no password field — still a login page
                    return JSON.stringify({is_login_page: true, already_authenticated: false});
                }
                // No password field. Check URL first — if it looks like a
                // login page, the password field just hasn't rendered yet.
                const url = location.href;
                if (/login|signin|auth/i.test(url)) {
                    return JSON.stringify({is_login_page: true, already_authenticated: false});
                }
                // Check page text for login indicators (works even before form renders).
                // SPAs may render text content before interactive elements.
                const bodyText = (document.body.innerText || '').toLowerCase();
                if (bodyText.includes('登录') || bodyText.includes('login') ||
                    bodyText.includes('请输入账号') || bodyText.includes('请输入密码') ||
                    bodyText.includes('sign in') || bodyText.includes('管理系统')) {
                    // Page has login-related text but no form yet — treat as login page
                    return JSON.stringify({is_login_page: true, already_authenticated: false});
                }
                // No password field AND not a login URL — check for real nav items.
                const navItems = document.querySelectorAll('[role=menuitem], [role=treeitem], .el-menu-item, .el-submenu__title');
                return JSON.stringify({is_login_page: false, already_authenticated: navItems.length > 2});
            }
            // Find username field — look for text/email input near password
            const pwd = pwds[0];
            const form = pwd.closest('form') || pwd.parentElement;
            const textInputs = (form || document).querySelectorAll('input[type=text], input[type=email], input[type=tel], input:not([type])');
            let userField = null;
            if (textInputs.length > 0) userField = textInputs[0];
            // Find submit button
            const buttons = (form || document).querySelectorAll('button, input[type=submit], input[type=button]');
            let submitBtn = null;
            for (const b of buttons) {
                const txt = (b.textContent || b.value || '').trim();
                if (txt && txt.length < 10) { submitBtn = b; break; }
            }
            return JSON.stringify({
                is_login_page: true,
                user_selector: userField ? (userField.id ? '#'+userField.id : userField.className ? '.'+userField.className.split(' ')[0] : userField.tagName) : null,
                pwd_selector: pwd.id ? '#'+pwd.id : pwd.className ? '.'+pwd.className.split(' ')[0] : pwd.tagName,
                btn_selector: submitBtn ? (submitBtn.id ? '#'+submitBtn.id : submitBtn.className ? '.'+submitBtn.className.split(' ')[0] : submitBtn.tagName) : null,
            });
        }"""

        detect_data = None
        import json as _json
        for _detect_attempt in range(3):  # retry up to 3 times for SPA rendering
            try:
                page = await self._browser.get_current_page()
                result_str = await page.evaluate(detect_js)
                detect_data = _json.loads(result_str)
                logger.info("Login detection (attempt %d): %s", _detect_attempt + 1, result_str[:200])
            except Exception as e:
                logger.warning("Login detection JS failed: %s — will attempt injection anyway", e)
                detect_data = {"is_login_page": True}
                break

            # If we got a definitive answer, stop retrying
            if detect_data.get("is_login_page") or detect_data.get("already_authenticated"):
                break
            # Inconclusive — SPA might still be rendering, wait and retry
            if _detect_attempt < 2:
                logger.info("Login detection inconclusive — waiting 3s for SPA to render (attempt %d/3)", _detect_attempt + 1)
                await asyncio.sleep(3)

        if detect_data.get("already_authenticated"):
            logger.info("Already authenticated (no password field found, nav visible)")
            self._logged_in = True
            return True

        if not detect_data.get("is_login_page"):
            # Detection still inconclusive after retries — attempt injection anyway.
            logger.info("Login detection inconclusive after retries — attempting injection anyway")
            # Fall through to Stage 2

        # ── Stage 2: Inject credentials via JavaScript ──
        logger.info("Login: injecting credentials for user=%s", username)
        # Escape special chars for JS string
        _esc_user = username.replace("\\", "\\\\").replace("'", "\\'")
        _esc_pwd = password.replace("\\", "\\\\").replace("'", "\\'")

        inject_js = f"""() => {{
            // Find password field — try type=password first, then placeholder
            let pwds = document.querySelectorAll('input[type=password]');
            if (pwds.length === 0) {{
                const allInputs = document.querySelectorAll('input');
                pwds = Array.from(allInputs).filter(i => {{
                    const ph = (i.placeholder || '').toLowerCase();
                    return ph.includes('密码') || ph.includes('password') || ph.includes('pass');
                }});
            }}
            if (pwds.length === 0) return JSON.stringify({{success: false, error: 'no_password_field'}});
            const pwd = pwds[0];
            const form = pwd.closest('form') || pwd.parentElement;

            // Find username field — text/email/tel input before password in DOM order
            const inputs = (form || document).querySelectorAll('input');
            let userInput = null;
            let seenPwd = false;
            // Try: find input right before password
            for (let i = 0; i < inputs.length; i++) {{
                if (inputs[i] === pwd && i > 0) {{
                    userInput = inputs[i-1];
                    break;
                }}
            }}
            if (!userInput) {{
                // Fallback: first text/email/tel input in form
                for (const inp of inputs) {{
                    if (inp !== pwd && (inp.type === 'text' || inp.type === 'email' || inp.type === 'tel' || !inp.type)) {{
                        userInput = inp;
                        break;
                    }}
                }}
            }}
            if (!userInput) return JSON.stringify({{success: false, error: 'no_username_field'}});

            // Find submit button
            const buttons = (form || document).querySelectorAll('button, input[type=submit], input[type=button], a.btn, [role=button]');
            let submitBtn = null;
            for (const b of buttons) {{
                const txt = (b.textContent || b.value || '').trim().toLowerCase();
                if (txt && txt.length < 15 && !/(reset|cancel|forgot|忘记|重置|取消)/i.test(txt)) {{
                    submitBtn = b;
                    break;
                }}
            }}
            if (!submitBtn) return JSON.stringify({{success: false, error: 'no_submit_button'}});

            // Fill fields — use native setter to trigger Vue/React bindings
            const nativeSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            nativeSetter.call(userInput, '{_esc_user}');
            userInput.dispatchEvent(new Event('input', {{bubbles: true}}));
            nativeSetter.call(pwd, '{_esc_pwd}');
            pwd.dispatchEvent(new Event('input', {{bubbles: true}}));

            // Click submit
            submitBtn.click();

            return JSON.stringify({{success: true, user_tag: userInput.tagName, pwd_tag: pwd.tagName, btn_text: (submitBtn.textContent||'').trim().slice(0,20)}});
        }}"""
        try:
            page = await self._browser.get_current_page()
            inject_result_str = await page.evaluate(inject_js)
            inject_result = _json.loads(inject_result_str)
            logger.info("Credential injection: %s", inject_result_str[:200])
        except Exception as e:
            logger.error("Credential injection JS failed: %s", e)
            self._logged_in = False
            return False

        if not inject_result.get("success"):
            error = inject_result.get("error", "unknown")
            # no_password_field may mean we're already authenticated (e.g. token
            # still valid from previous session). Verify before giving up.
            if error == "no_password_field":
                logger.info("No password field found — checking if already authenticated")
                try:
                    page = await self._browser.get_current_page()
                    # First check URL — if on a login page, we're NOT authenticated
                    on_login = await page.evaluate(
                        "() => /login|signin|auth/i.test(location.href)"
                    )
                    if on_login:
                        logger.warning("No password field but URL is login page — page may still be loading")
                        self._logged_in = False
                        return False
                    has_nav = await page.evaluate(
                        "() => document.querySelectorAll('[role=menuitem], [role=treeitem], .el-menu-item, .el-submenu__title').length > 2"
                    )
                    if has_nav:
                        logger.info("Navigation found — treating as authenticated")
                        self._logged_in = True
                        return True
                except Exception:
                    pass
            logger.error("Login injection failed: %s", error)
            self._logged_in = False
            return False

        # ── Stage 3: Wait and verify result ──
        await asyncio.sleep(3)

        verify_js = """() => {
            // Check for error messages
            const errors = document.querySelectorAll('.el-message--error, .el-notification--error, .ant-message-error, .toast-error, [class*=error], [class*=alert], .login-error, .el-alert--error');
            for (const e of errors) {
                const txt = (e.textContent || '').trim();
                if (txt && txt.length > 2 && txt.length < 500) {
                    return JSON.stringify({success: false, error_message: txt.slice(0, 200)});
                }
            }
            // Check for login page indicators (password field still visible)
            const pwds = document.querySelectorAll('input[type=password]');
            const pwdsVisible = Array.from(pwds).some(p => p.offsetParent !== null);
            // Check for navigation/sidebar (indicates success)
            const nav = document.querySelector('nav, .sidebar, .el-menu, .ant-menu, [class*=sidebar], [class*=top-menu], .navbar');
            const hasNav = !!nav && nav.offsetParent !== null;
            const url = location.href;
            const isLoginUrl = /login|signin|auth/i.test(url);

            return JSON.stringify({
                success: hasNav || (!pwdsVisible && !isLoginUrl),
                has_navigation: hasNav,
                still_on_login: pwdsVisible && isLoginUrl,
                url: url,
                page_title: document.title,
                error_message: pwdsVisible && isLoginUrl ? 'Still on login page' : ''
            });
        }"""
        try:
            page = await self._browser.get_current_page()
            verify_result_str = await page.evaluate(verify_js)
            verify_result = _json.loads(verify_result_str)
            logger.info("Login verification: %s", verify_result_str[:200])

            if verify_result.get("success"):
                self._logged_in = True
                logger.info("Login successful — page: %s", verify_result.get("url", "?"))
                return True
            else:
                error = verify_result.get("error_message", "Unknown error")
                logger.warning("Login failed: %s", error)
                self._logged_in = False
                return False
        except Exception as e:
            logger.warning("Login verification JS failed: %s — assuming login state unknown", e)
            # Fallback: check if password field is gone
            self._logged_in = True  # optimistic
            return True

    async def ensure_logged_in(self):
        """Ensure logged in — verify actual browser state, not just flag.

        The _logged_in flag can be stale if:
        - Browser was closed and reopened
        - Session cookies expired
        - Another driver instance was created with a fresh Browser
        """
        if not self._logged_in:
            await self.login()
            return

        # Verify the page is actually authenticated (not on a login page)
        try:
            page = await self._browser.get_current_page()
            if page is None:
                self._logged_in = False
                await self.login()
                return
            on_login = await page.evaluate(
                "() => /login|signin|auth/i.test(location.href)"
            )
            if on_login:
                logger.info("ensure_logged_in: flag=True but on login page — re-authenticating")
                self._logged_in = False
                await self.login()
        except Exception:
            # Can't verify — assume logged in and let run_task handle failures
            pass

    async def evaluate_js(self, js_code: str) -> str:
        """Execute JavaScript in the current browser page.

        Returns string result from JS evaluation.
        """
        page = await self._browser.get_current_page()
        return await page.evaluate(js_code)

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

    @staticmethod
    def _ensure_screenshot_dir_resilience():
        """Monkey-patch ScreenshotService to survive missing screenshots/ dir."""
        try:
            from browser_use.screenshots.service import ScreenshotService

            _orig_store = ScreenshotService.store_screenshot

            async def _robust_store(self, screenshot_b64: str, step_number: int) -> str:
                # Ensure screenshots dir exists (defense against intermittent mkdir failure)
                self.screenshots_dir.mkdir(parents=True, exist_ok=True)
                return await _orig_store(self, screenshot_b64, step_number)

            ScreenshotService.store_screenshot = _robust_store
            logger.debug("ScreenshotService.store_screenshot patched for dir resilience")
        except Exception:
            pass  # Non-critical — native behavior works ~95% of the time

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
