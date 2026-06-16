"""设备管理模块共享 fixtures

driver_setup（module 级）：
  - 每个 test_*.py 文件独立浏览器
  - 自动按模块名导航到对应设备管理页面

使用方式：
    def test_xxx(self, driver_setup):
        page = UnitManagePage(driver_setup)
        ...

可选 Page Object fixture（已导航，直接操作）：
    def test_xxx(self, unit_page):
        unit_page.click_search()
"""
import logging
import time

import pytest

from base.browser_driver import BaseDriver, ensure_logged_in
from page.equipment_page.UnitManagePage import UnitManagePage
from page.equipment_page.EquipmentPage import EquipmentPage
from page.equipment_page.SensorManagePage import SensorManagePage
from page.equipment_page.MaintenancePage import MaintenancePage
from page.equipment_page.CameraManagePage import CameraManagePage
from page.equipment_page.KeyParamPage import KeyParamPage
from page.equipment_page.AlarmConfigPage import AlarmConfigPage

logger = logging.getLogger(__name__)


def _navigate_for_module(driver, module):
    """按测试模块导航到目标设备管理页面"""
    from base.sidebar_navigator import SidebarNavigator
    from base.base_page import BasePage

    name = module.__name__.split(".")[-1]
    bp = BasePage(driver)
    nav = SidebarNavigator(driver)

    # unit_management: app 端路由 #/equipment/unit 会被重定向到传感器页面，
    # 必须通过侧边栏 DOM 点击（展开父菜单 + 点击叶子菜单项）
    if name == "test_unit_management":
        logger.info("设备模块导航: %s → 侧边栏: 设备管理→装置台账", name)
        # 直接用 JS 展开设备管理子菜单 + 点击装置台账，绕过 Selenium EC 竞态
        clicked = driver.execute_script("""
            var items = document.querySelectorAll('.el-menu-item, li[role="menuitem"], .el-sub-menu .el-menu-item');
            for (var i = 0; i < items.length; i++) {
                if (items[i].textContent.indexOf('装置台账') !== -1) {
                    // 先确保父级 submenu 展开
                    var submenu = items[i].closest('.el-sub-menu');
                    if (submenu && !submenu.classList.contains('is-opened')) {
                        var title = submenu.querySelector('.el-sub-menu__title');
                        if (title) title.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                    }
                    items[i].dispatchEvent(new MouseEvent('click', {bubbles: true}));
                    return true;
                }
            }
            return false;
        """)
        if clicked:
            logger.info("装置台账: JS 侧边栏点击成功")
        else:
            logger.warning("装置台账: JS 侧边栏点击未找到目标，回退 hash")
            nav._navigate_by_js_hash("#/equipment/unit", "unit-fallback")
        bp.wait_vue_stable()
        bp._wait_loading_gone(timeout=15)
        return

    _MODULE_HASH_ROUTES = {
        "test_equipment_management":   "#/equipment/device",
        "test_sensor_management":      "#/equipment/sensor",
        "test_maintenance_management": "#/equipment/maintenance",
        "test_camera_management":      "#/equipment/camera",
        "test_key_param":              "#/equipment/key-param",
        "test_alarm_config":           "#/equipment/alarm-config",
    }

    href = _MODULE_HASH_ROUTES.get(name)
    if href:
        logger.info("设备模块导航: %s → %s", name, href)
        nav._navigate_by_js_hash(href, name)
        bp.wait_vue_stable()
        bp._wait_loading_gone(timeout=15)
        # maintenance 页面有 3 个 el-table，需调用 PO 的专用等待方法
        if name == "test_maintenance_management":
            MaintenancePage(driver).navigate_to_maintenance()
    else:
        logger.warning("未配置设备模块导航: %s", name)


@pytest.fixture(scope="module")
def driver_setup(request):
    """Module 级：登录 + 按当前测试文件导航到设备管理页面

    P0 优化：每个模块启动前增加短暂延迟，确保前一个 chromedriver 进程完全退出。
    """
    # 短暂延迟确保前一个模块的浏览器进程完全清理
    time.sleep(0.5)

    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)
        # 等待侧边栏渲染完成
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
        time.sleep(0.5)  # 确保浏览器进程完全退出


# ==================================================================
#  页面级 fixtures（返回已导航的 Page Object 实例）
# ==================================================================
@pytest.fixture(scope="module")
def unit_page(driver_setup):
    """装置台账页面 fixture — 已登录并导航到装置台账"""
    return UnitManagePage(driver_setup)


@pytest.fixture(scope="module")
def equipment_page(driver_setup):
    """设备台账页面 fixture — 已登录并导航到设备台账"""
    return EquipmentPage(driver_setup)


@pytest.fixture(scope="module")
def sensor_page(driver_setup):
    """传感器管理页面 fixture — 已登录并导航到传感器管理"""
    return SensorManagePage(driver_setup)


@pytest.fixture(scope="module")
def maintenance_page(driver_setup):
    """设备维保页面 fixture — 已登录并导航到设备维保"""
    page = MaintenancePage(driver_setup)
    page.navigate_to_maintenance()
    return page


@pytest.fixture(scope="module")
def camera_page(driver_setup):
    """摄像头管理页面 fixture — 已登录并导航到摄像头管理"""
    return CameraManagePage(driver_setup)


@pytest.fixture(scope="module")
def key_param_page(driver_setup):
    """关键参数监控页面 fixture — 已登录并导航到关键参数监控"""
    return KeyParamPage(driver_setup)


@pytest.fixture(scope="module")
def alarm_config_page(driver_setup):
    """设备报警配置页面 fixture — 已登录并导航到设备报警配置"""
    page = AlarmConfigPage(driver_setup)
    page._wait_page_ready()
    return page
