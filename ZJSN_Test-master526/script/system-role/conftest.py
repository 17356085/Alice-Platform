"""角色职权分配模块 (system-role) 共享 fixtures

driver_setup（module 级）：
  - 每个 test_*.py 文件独立浏览器
  - 自动导航到角色管理页面

使用方式：
    def test_xxx(self, driver_setup):
        page = RoleManagePage(driver_setup)
        ...
"""
import logging

import pytest

from base.browser_driver import BaseDriver, ensure_logged_in
from page.system_role_page.RoleManagePage import RoleManagePage

logger = logging.getLogger(__name__)


def _navigate_for_module(driver, module):
    """按测试模块导航到角色管理页面"""
    from base.sidebar_navigator import SidebarNavigator

    name = module.__name__.split(".")[-1]

    href_map = {
        "test_role_management":    "#/system/role",
        "test_rbac_check":         "#/system/role",
        "test_rbac_permission":    "#/system/role",
        "test_rbac_instant_effect": None,  # e2e 测试自行导航
    }

    href = href_map.get(name)
    if href:
        logger.info("角色管理模块导航: %s → %s", name, href)
        nav = SidebarNavigator(driver)
        nav._navigate_by_js_hash(href, name)
    elif name == "test_rbac_instant_effect":
        logger.info("RBAC即时生效测试: 跳过自动导航，由测试自行控制")
    else:
        logger.warning("未配置角色管理模块导航: %s", name)


@pytest.fixture(scope="module")
def driver_setup(request):
    """Module 级：登录 + 按当前测试文件导航"""
    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)
        _navigate_for_module(driver, request.module)
        yield driver
    finally:
        base.close_browser()


# ==================================================================
#  页面级 fixtures
# ==================================================================
@pytest.fixture(scope="module")
def role_page(driver_setup):
    return RoleManagePage(driver_setup)
