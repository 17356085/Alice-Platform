"""项目配置入口 — 按 ENV 环境变量加载对应环境配置

用法:
    from config import BASE_URL, TIMEOUT_CONFIG, ...

环境切换:
    ENV=dev   → config/dev.py
    ENV=test  → config/test.py  (默认)
    ENV=staging → config/staging.py
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── 基础配置（所有环境共享）───────────────────────────────────────
from .base import BROWSER_CONFIG, TIMEOUT_CONFIG, LOGGING_CONFIG

# ── 环境选择 ──────────────────────────────────────────────────────
_env = os.getenv("ENV", "test").lower()

_env_modules = {
    "dev": ".dev",
    "test": ".test",
    "staging": ".staging",
}

_module = _env_modules.get(_env, ".test")

if _module == ".dev":
    from .dev import BASE_URL, DEFAULT_USERNAME, DEFAULT_PASSWORD
elif _module == ".test":
    from .test import BASE_URL, DEFAULT_USERNAME, DEFAULT_PASSWORD
elif _module == ".staging":
    from .staging import BASE_URL, DEFAULT_USERNAME, DEFAULT_PASSWORD

# ── .env 覆盖（优先级：.env > 环境配置 > 默认值）─────────────────
BASE_URL = os.getenv("BASE_URL", BASE_URL)
DEFAULT_USERNAME = os.getenv("DEFAULT_USERNAME", DEFAULT_USERNAME)
DEFAULT_PASSWORD = os.getenv("DEFAULT_PASSWORD", DEFAULT_PASSWORD)

from .cleanup import CLEANUP_CONFIG
