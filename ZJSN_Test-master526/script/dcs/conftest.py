"""DCS 数据监控模块共享 fixtures

模块路由：
  - 关键参数监控  #/monitor
  - 全部点位      #/all-data
  - 常用点位      #/common-data
  - 点位配置      #/point-config
  - 上传日志      #/upload-log

使用方式：
    def test_xxx(self, monitor_page):
        monitor_page.search("xxx")
    def test_xxx(self, driver_setup):
        page = DcsMonitorPage(driver_setup)
        ...
"""
import logging
import time

import pytest

from base.browser_driver import BaseDriver, ensure_logged_in
from page.dcs_page.MonitorPage import DcsMonitorPage
from page.dcs_page.CommonDataPage import CommonDataPage
from page.dcs_page.PointConfigPage import PointConfigPage
from page.dcs_page.AllDataPage import AllDataPage
from page.dcs_page.UploadLogPage import UploadLogPage

logger = logging.getLogger(__name__)

_MODULE_HASH_ROUTES = {
    "test_monitor": "#/monitor",
    "test_all_data": "#/all-data",
    "test_common_data": "#/common-data",
    "test_point_config": "#/point-config",
    "test_upload_log": "#/upload-log",
}


@pytest.fixture(scope="module")
def driver_setup(request):
    """Module 级：登录 + 按路由导航到对应 DCS 页面"""
    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)

        name = request.module.__name__.split(".")[-1]
        route = _MODULE_HASH_ROUTES.get(name)
        if route:
            logger.info("导航: %s → %s", name, route)
            driver.execute_script(f"window.location.hash = '{route}';")
            time.sleep(2)
        else:
            logger.warning("未配置 DCS 模块导航: %s", name)

        yield driver
    finally:
        base.close_browser()


# ══════════════════════════════════════════════════════════════════
#  页面级 fixtures（返回已导航的 Page Object 实例）
# ══════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def monitor_page(driver_setup):
    """监控管理页面 fixture — 已登录并导航"""
    return DcsMonitorPage(driver_setup)


@pytest.fixture(scope="module")
def common_data_page(driver_setup):
    """常用数据页面 fixture — 已登录并导航"""
    return CommonDataPage(driver_setup)


@pytest.fixture(scope="module")
def point_config_page(driver_setup):
    """点位配置页面 fixture — 已登录并导航"""
    return PointConfigPage(driver_setup)


@pytest.fixture(scope="module")
def all_data_page(driver_setup):
    """全部点位页面 fixture — 已登录并导航"""
    return AllDataPage(driver_setup)


@pytest.fixture(scope="module")
def upload_log_page(driver_setup):
    """上传日志页面 fixture — 已登录并导航"""
    return UploadLogPage(driver_setup)


# ══════════════════════════════════════════════════════════════════
#  数据清理 fixtures
# ══════════════════════════════════════════════════════════════════

@pytest.fixture(scope="function")
def cleanup():
    """数据清理 fixture — autouse _data_cleanup 已自动执行，此处为显式触发标记"""
    from base.cleanup_tracker import get_cleanup_tracker
    yield
    tracker = get_cleanup_tracker()
    if tracker.pending_count > 0:
        tracker.cleanup_all(warn_only=True)


@pytest.fixture(scope="function")
def cleanup_tracker():
    """返回 CleanupTracker 实例，测试可调用 register() / register_entity()"""
    from base.cleanup_tracker import get_cleanup_tracker
    return get_cleanup_tracker()


@pytest.fixture(scope="function")
def setup_cleanup_test_point(point_config_page: "PointConfigPage"):
    """创建测试点并在 teardown 中删除"""
    point_name = "TC-编辑测试点"
    point_data = {
        "name": point_name,
        "type": "模拟量",
        "unit": "℃",
        "description": "自动化测试编辑/删除用"
    }
    # Setup: create test point
    point_config_page.click_add_button()
    point_config_page.fill_point_form(point_data)
    point_config_page.submit()
    logger.info("setup_cleanup_test_point: 已创建测试点 '%s'", point_name)
    yield point_name
    # Teardown: delete the test point
    try:
        point_config_page.search(point_name)
        import time
        time.sleep(0.5)
        if point_config_page.is_row_exists(point_name):
            point_config_page.select_row(point_name)
            point_config_page.click_delete_button()
            point_config_page.confirm_delete()
            logger.info("setup_cleanup_test_point: 已清理测试点 '%s'", point_name)
    except Exception as e:
        logger.warning("setup_cleanup_test_point: 清理失败 '%s': %s", point_name, e)
