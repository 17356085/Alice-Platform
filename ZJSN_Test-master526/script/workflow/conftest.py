"""工作流管理模块共享 fixtures

driver_setup（module 级）：
  - 每个 test_*.py 文件独立浏览器
  - 自动按模块名导航到对应工作流页面

使用方式：
    def test_xxx(self, driver_setup):
        page = ApprovalTodoPage(driver_setup)
        ...

可选 Page Object fixture（已导航，直接操作）：
    def test_xxx(self, approval_todo_page):
        approval_todo_page.click_search()
"""
import logging
import time

import pytest

from base.browser_driver import BaseDriver, ensure_logged_in
from page.workflow_page.ApprovalChainPage import ApprovalChainPage
from page.workflow_page.ApprovalHistoryPage import ApprovalHistoryPage
from page.workflow_page.ApprovalTodoPage import ApprovalTodoPage
from page.workflow_page.MyApplicationPage import MyApplicationPage
from page.workflow_page.SapPushLogPage import SapPushLogPage

logger = logging.getLogger(__name__)


def _navigate_for_module(driver, module):
    """按测试模块导航到目标页面（使用 JS hash 直接跳转）"""
    from base.sidebar_navigator import SidebarNavigator

    name = module.__name__.split(".")[-1]

    href_map = {
        "test_approval_todo":    "#/system/workflow/todo",
        "test_approval_history": "#/system/workflow/history",
        "test_my_application":   "#/system/workflow/my-applications",
        "test_approval_chain":   "#/system/workflow/approval-chain",
        "test_sap_push_log":     "#/system/workflow/sap-push-log",
        "test_workflow_e2e":     None,  # e2e 测试自行导航
    }

    href = href_map.get(name)
    if href:
        logger.info("工作流模块导航: %s → %s", name, href)
        nav = SidebarNavigator(driver)
        nav._navigate_by_js_hash(href, name)
    elif name == "test_workflow_e2e":
        logger.info("工作流E2E测试: 跳过自动导航，由测试自行控制")
    else:
        logger.warning("未配置工作流模块导航: %s", name)


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
#  页面级 fixtures（返回 Page Object，依赖 driver_setup 已完成导航）
# ==================================================================
@pytest.fixture(scope="module")
def approval_todo_page(driver_setup):
    return ApprovalTodoPage(driver_setup)


@pytest.fixture(scope="module")
def approval_history_page(driver_setup):
    return ApprovalHistoryPage(driver_setup)


@pytest.fixture(scope="module")
def my_application_page(driver_setup):
    return MyApplicationPage(driver_setup)


@pytest.fixture(scope="module")
def approval_chain_page(driver_setup):
    return ApprovalChainPage(driver_setup)


@pytest.fixture(scope="module")
def sap_push_log_page(driver_setup):
    return SapPushLogPage(driver_setup)
