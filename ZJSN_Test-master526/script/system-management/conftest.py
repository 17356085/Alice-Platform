"""系统运维管理模块共享 fixtures

system-management 是虚拟模块，页面和测试实际分布在 system/ 和 workflow/ 下。
此 conftest 提供 module-scope driver_setup，支持独立运行本目录测试。
"""
import logging
import time
import pytest

from base.browser_driver import BaseDriver, ensure_logged_in
from base.base_page import BasePage
from base.sidebar_navigator import SidebarNavigator

logger = logging.getLogger(__name__)

_MODULE_HASH_ROUTES = {
    "test_menu_management":         "#/system/menu",
    "test_approval_todo":           "#/system/workflow/todo",
    "test_approval_history":        "#/system/workflow/history",
    "test_my_application":          "#/system/workflow/my-applications",
    "test_approval_chain":          "#/system/workflow/approval-chain",
    "test_sap_push_log":            "#/system/workflow/sap-push-log",
    "test_api_management":          "#/system/api",
    "test_monitor_management":      "#/system/monitor",
    "test_system_management_smoke": None,  # smoke 测试自行导航
}


def _navigate_for_module(driver, module):
    name = module.__name__.split(".")[-1]
    href = _MODULE_HASH_ROUTES.get(name)
    if href:
        logger.info("系统运维模块导航: %s -> %s", name, href)
        nav = SidebarNavigator(driver)
        nav._navigate_by_js_hash(href, name)
    else:
        logger.info("系统运维模块: %s 自行导航", name)


@pytest.fixture(scope="module")
def driver_setup(request):
    time.sleep(0.5)
    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)
        from selenium.webdriver.support.ui import WebDriverWait
        try:
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script(
                    "return document.querySelectorAll('.el-menu-item, .el-sub-menu__title').length > 5"
                )
            )
        except Exception:
            time.sleep(3)
        _navigate_for_module(driver, request.module)
        yield driver
    finally:
        base.close_browser()
        time.sleep(0.5)
