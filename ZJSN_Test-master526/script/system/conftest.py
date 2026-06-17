"""系统管理模块共享 fixtures

driver_setup（module 级）：
  - 每个 test_*.py 文件独立浏览器（与原各文件内 session fixture 行为一致）
  - 自动按模块名导航到对应系统管理页面
  - 用户/人员管理模块在结束时尝试清理测试用户

使用方式（与改造前相同）：
    def test_xxx(self, driver_setup):
        page = UserManagePage(driver_setup)
        ...

可选 Page Object fixture（已导航，直接操作）：
    def test_xxx(self, dict_page):
        dict_page.click_search()
"""
import logging
import time

import pytest

from base.browser_driver import BaseDriver, ensure_logged_in
from page.system_page.ApiManagePage import ApiManagePage
from page.system_page.DictManagePage import DictManagePage
from page.system_page.LoginLogPage import LoginLogPage
from page.system_page.MenuManagePage import MenuManagePage
from page.system_page.MonitorManagePage import MonitorManagePage
from page.system_page.NoticeManagePage import NoticeManagePage
from page.system_page.OperationLogPage import OperationLogPage
from page.system_page.OrgManagePage import OrgManagePage
from page.system_page.ParamsManagePage import ParamsManagePage
from page.system_page.SystemLogPage import SystemLogPage
from page.system_page.TimedTaskPage import TimedTaskPage
from page.system_page.UserListPage import UserListPage
from page.system_page.UserManagePage import UserManagePage

logger = logging.getLogger(__name__)


class DriverProxy:
    """参数设置模块专用：支持 invalid session 后 restart"""

    def __init__(self):
        self._base = BaseDriver()
        self._driver = None

    def start(self):
        self._driver = self._base.open_browser()
        ensure_logged_in(self._driver)
        ParamsManagePage(self._driver).navigate_to_params_settings()
        return self

    def restart(self):
        try:
            self._base.close_browser()
        except Exception:
            pass
        self._driver = self._base.open_browser()
        ensure_logged_in(self._driver)
        ParamsManagePage(self._driver).navigate_to_params_settings()

    def close(self):
        self._base.close_browser()

    def __getattr__(self, item):
        return getattr(self._driver, item)


def _navigate_for_module(driver, module):
    """按测试模块导航到目标页面（使用 JS hash 直接跳转）"""
    from base.sidebar_navigator import SidebarNavigator

    name = module.__name__.split(".")[-1]

    if name == "test_params_management":
        return
    if name == "test_login":
        return  # 登录页不需要导航

    # href 直接映射 — 最可靠（绕过侧边栏折叠问题）
    href_map = {
        "test_dict_management":         "#/system/dict",
        "test_login_log_management":    "#/system/log/login-log",
        "test_user_list":               "#/system/user",
        "test_user_management":         "#/system/user",
        "test_timed_task_management":   "#/system/job",
        "test_system_log_management":   "#/system/log/system-log",
        "test_personnel_management":    "#/system/user",
        "test_org_management":          "#/system/dept",
        "test_operation_log_management":"#/system/log/oper-log",
        "test_notice_management":       "#/system/notice",
        "test_menu_management":         "#/system/menu",
        "test_api_management":          "#/system/api",
        "test_monitor_management":      "#/system/monitor",
        "test_system_e2e":              None,  # e2e 测试自行导航
    }

    href = href_map.get(name)
    if href:
        logger.info("系统模块导航: %s → %s", name, href)
        nav = SidebarNavigator(driver)
        nav._navigate_by_js_hash(href, name)
    else:
        logger.warning("未配置系统模块导航: %s", name)


def _teardown_user_module(driver, module):
    """用户/人员管理：清理本轮创建的测试用户"""
    username = getattr(module, "CREATED_USERNAME", None)
    if not username:
        return
    logger.info("用户数据后置清理: %s", username)
    try:
        user_manage = UserManagePage(driver)
        user_manage.navigate_to_user_management()
        user_manage.click_reset_button()
        user_manage.input_search_username(username)
        user_manage.click_search_button()
        if user_manage.is_username_present(username):
            user_manage.click_more_user(username)
            user_manage.click_more_delete()
            user_manage.confirm_delete_message_box()
            time.sleep(1)
    except Exception as exc:
        logger.warning("用户后置清理失败: %s", exc)


def _teardown_for_module(driver, module):
    name = module.__name__.split(".")[-1]
    if name in ("test_user_management", "test_personnel_management"):
        _teardown_user_module(driver, module)


@pytest.fixture(scope="module")
def driver_setup(request):
    """Module 级：登录 + 按当前测试文件导航（兼容原 driver_setup 参数名）"""
    name = request.module.__name__.split(".")[-1]

    if name == "test_params_management":
        proxy = DriverProxy().start()
        try:
            yield proxy
        finally:
            proxy.close()
        return

    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)
        _navigate_for_module(driver, request.module)
        yield driver
    finally:
        _teardown_for_module(driver, request.module)
        base.close_browser()


# ==================================================================
#  页面级 fixtures（返回 Page Object，依赖 driver_setup 已完成导航）
# ==================================================================
@pytest.fixture(scope="module")
def dict_page(driver_setup):
    return DictManagePage(driver_setup)


@pytest.fixture(scope="module")
def user_list_page(driver_setup):
    return UserListPage(driver_setup)


@pytest.fixture(scope="module")
def user_page(driver_setup):
    return UserManagePage(driver_setup)


@pytest.fixture(scope="module")
def api_manage_page(driver_setup):
    return ApiManagePage(driver_setup)


@pytest.fixture(scope="module")
def monitor_manage_page(driver_setup):
    return MonitorManagePage(driver_setup)


# ==================================================================
#  登录测试 fixture（不预先登录，每个用例独立浏览器）
# ==================================================================
@pytest.fixture(scope="function")
def login_driver_setup():
    """Function 级：打开浏览器到登录页（不登录），每个用例独立浏览器

    登录测试必须从空白浏览器开始，不能使用已登录的 driver_setup。
    各 test_login 用例通过此 fixture 获取 driver 和 page 实例。
    """
    from page.system_page.LoginPage import LoginPage

    base = BaseDriver()
    driver = base.open_browser()
    try:
        page = LoginPage(driver)
        page.wait_login_form_ready()
        yield {"driver": driver, "page": page, "base": base}
    finally:
        base.close_browser()


# ══════════════════════════════════════════════════════════════════════
#  双/三浏览器 fixtures（从 conftest_dual.py 注册）
#  供 test_rbac_instant_effect / test_workflow_e2e 使用
#  ⚠️ pytest_plugins 已迁移至顶层 conftest.py (pytest >= 8 要求)
# ══════════════════════════════════════════════════════════════════════
