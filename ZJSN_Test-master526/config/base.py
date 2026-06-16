"""项目配置 — 基础配置（所有环境共享）"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── 浏览器配置 ────────────────────────────────────────────────────
BROWSER_CONFIG = {
    "page_load_strategy": "eager",
    "headless": os.getenv("HEADLESS", "false").lower() == "true",
    "maximize": True,
    "implicit_wait": 0,
    "page_load_timeout": 60,
}

# ── 超时配置（按场景分层）──────────────────────────────────────────
TIMEOUT_CONFIG = {
    "explicit_wait": 10,
    "poll_frequency": 0.5,
    "page_load": 30,
    "login_form": 30,
    "dialog_open": 10,
    "dialog_close": 5,
    "toast": 5,
    "message_box": 8,
    "table_render": 10,
    "dropdown_option": 5,
    "search_result": 5,
    "overlay_gone": 10,
    "vue_stable": 5,
    "micro_wait": 0.2,
    "animate_wait": 0.3,
}

# ── 日志配置 ──────────────────────────────────────────────────────
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "[%(asctime)s] [%(levelname)-7s] [%(name)s] %(message)s",
    "datefmt": "%Y-%m-%d %H:%M:%S",
}
