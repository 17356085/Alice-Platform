"""script 级共享 fixtures — 浏览器 session 统一入口 + 数据自动清理

子目录约定：
  - system/、lab/ 使用 session_logged_in_browser（整目录共享一个浏览器）
  - person/ 使用 person/conftest.py 中的 module 级 driver_setup（每个测试文件独立浏览器）
"""
import logging

import pytest

from base.browser_driver import BaseDriver, ensure_logged_in
from base.cleanup_tracker import get_cleanup_tracker
from config.cleanup import CLEANUP_CONFIG

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def session_logged_in_browser():
    """Session 级：启动浏览器并完成登录（system / lab 模块共享）"""
    import time
    from base.base_page import BasePage

    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)
        try:
            BasePage(driver).wait_vue_stable(timeout=10)
        except Exception:
            pass
        time.sleep(1)
        logger.info("session_logged_in_browser: 登录完成，页面已稳定")
        yield driver
    finally:
        base.close_browser()
        logger.info("session_logged_in_browser: 浏览器已关闭")


# ── 数据自动清理 ──────────────────────────────────────────────
# 清理逻辑已统一到 base/cleanup_tracker.py 的 _CleanupTracker.cleanup_all()
# 本文件仅保留 autouse fixture 作为触发器


@pytest.fixture(autouse=True)
def _data_cleanup():
    """每条用例执行后自动清理注册的脏数据（即使断言失败也执行）。

    委托给 _CleanupTracker.cleanup_all() — 支持 API/Callback/UI 三种清理方式。
    dcs 模块的 register_entity() / cleanup_all() 调用也走同一路径。
    """
    yield  # ← 用例执行在这里
    if not CLEANUP_CONFIG.get("enabled", True):
        return
    tracker = get_cleanup_tracker()
    if tracker.pending_count == 0:
        return
    tracker.cleanup_all(warn_only=True)
