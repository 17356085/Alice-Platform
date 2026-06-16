"""储罐管理模块共享 fixtures

driver_setup（module 级）：
  - 每个 test_*.py 文件独立浏览器
  - 使用 SidebarNavigator 自动导航到对应页面

使用方式：
    def test_xxx(self, driver_setup):
        page = TankMonitorPage(driver_setup)
        ...

    def test_xxx(self, tank_monitor_page):
        tank_monitor_page.search("LNG").reset_search()
"""
import logging
import time

import pytest

from base.browser_driver import BaseDriver, ensure_logged_in
from page.tank_page.TankMonitorPage import TankMonitorPage
from page.tank_page.TankReportPage import TankReportPage
from page.tank_page.TankAlarmConfigPage import TankAlarmConfigPage

logger = logging.getLogger(__name__)


def _navigate_for_module(driver, module):
    """按测试模块导航到对应储罐管理页面"""
    name = module.__name__.split(".")[-1]

    navigators = {
        "test_tank_monitor": lambda d: TankMonitorPage(d).navigate(),
        "test_tank_report": lambda d: TankReportPage(d).navigate(),
        "test_tank_alarm_config": lambda d: TankMonitorPage(d).navigate(),  # alarm-config 通过 monitor 触发
    }
    nav = navigators.get(name)
    if nav:
        logger.info("储罐模块导航: %s", name)
        nav(driver)
    else:
        logger.warning("未配置储罐模块导航: %s", name)


@pytest.fixture(scope="module")
def driver_setup(request):
    """Module 级：登录 + 按当前测试文件导航到对应页面"""
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


@pytest.fixture(scope="module")
def tank_monitor_page(driver_setup):
    """储罐监控页面 fixture — 已登录并导航"""
    return TankMonitorPage(driver_setup)


@pytest.fixture(scope="module")
def tank_report_page(driver_setup):
    """储罐日报表页面 fixture — 已登录并导航"""
    return TankReportPage(driver_setup)


@pytest.fixture(scope="function")
def fresh_driver():
    """每用例独立浏览器（未登录），由用例自行 login_as()

    用于权限测试（多账号切换）和弹窗测试（需隔离浏览器状态）。
    不做自动登录，不做自动导航。
    """
    time.sleep(0.3)

    base = BaseDriver()
    driver = base.open_browser()
    yield driver
    try:
        base.close_browser()
    except Exception:
        pass
    time.sleep(0.3)
