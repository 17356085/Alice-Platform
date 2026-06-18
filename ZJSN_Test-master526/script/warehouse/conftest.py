"""库管管理模块共享 fixtures

driver_setup（module 级）：
  - 每个 test_*.py 文件独立浏览器实例
  - 使用 JS hash 导航（window.location.hash）直接跳转目标路由

使用方式：
    def test_xxx(self, driver_setup):
        page = HazardItemPage(driver_setup)
"""
import logging
import time

import pytest

from base.browser_driver import BaseDriver, ensure_logged_in
from base.base_page import BasePage
from base.sidebar_navigator import SidebarNavigator
from page.warehouse_page.HazardItemPage import HazardItemPage
from page.warehouse_page.HazardIORecordPage import HazardIORecordPage
from page.warehouse_page.HazardInOrderPage import HazardInOrderPage
from page.warehouse_page.HazardStockPage import HazardStockPage
from page.warehouse_page.ReagentItemPage import ReagentItemPage
from page.warehouse_page.ReagentFillPage import ReagentFillPage
from page.warehouse_page.SpareItemPage import SpareItemPage
from page.warehouse_page.SpareIORecordPage import SpareIORecordPage
from page.warehouse_page.SpareInOrderPage import SpareInOrderPage
from page.warehouse_page.SpareOutOrderPage import SpareOutOrderPage
from page.warehouse_page.SpareRequisitionPage import SpareRequisitionPage
from page.warehouse_page.SpareStockPage import SpareStockPage
from page.warehouse_page.SpareStocktakePage import SpareStocktakePage
from page.warehouse_page.SpareStockAdjustPage import SpareStockAdjustPage

logger = logging.getLogger(__name__)

# 测试文件 → 页面 hash 路由映射
_MODULE_HASH_ROUTES = {
    "test_hazard_in_order": "#/warehouse/hazard/in_order",
    "test_hazard_io_record": "#/warehouse/hazard/io_record",
    "test_hazard_item": "#/warehouse/hazard/item",
    "test_hazard_stock": "#/warehouse/hazard/stock",
    "test_reagent_fill": "#/warehouse/reagent/fill",
    "test_reagent_item": "#/warehouse/reagent/item",
    "test_spare_in_order": "#/warehouse/spare/in_order",
    "test_spare_io_record": "#/warehouse/spare/io_record",
    "test_spare_item": "#/warehouse/spare/item",
    "test_spare_out_order": "#/warehouse/spare/out_order",
    "test_spare_requisition": "#/warehouse/spare/requisition",
    "test_spare_stock": "#/warehouse/spare/stock",
    "test_spare_stock_adjust": "#/warehouse/spare/stock_adjust",
    "test_spare_stocktake": "#/warehouse/spare/stocktake",
    "test_warehouse_e2e": "#/warehouse",
    "test_warehouse_workflow_e2e": "#/warehouse",
}


@pytest.fixture(scope="module")
def driver_setup(request):
    """模块级浏览器实例，自动导航到测试路由"""
    driver = BaseDriver().driver
    ensure_logged_in(driver)

    try:
        _navigate_for_module(driver, request.module)
    except Exception as e:
        logger.error("导航失败: %s", e)
        driver.quit()
        raise

    yield driver

    try:
        _teardown_for_module(driver, request.module)
    except Exception as e:
        logger.warning("后置清理失败: %s", e)

    driver.quit()


def _navigate_for_module(driver, module):
    """使用 JS hash 导航到目标路由"""
    name = module.__name__.split(".")[-1]
    route = _MODULE_HASH_ROUTES.get(name)

    if route:
        logger.info("导航: %s → %s", name, route)
        nav = SidebarNavigator(driver)
        nav._navigate_by_js_hash(route, name)
        BasePage(driver).wait_vue_stable()
    else:
        logger.warning("未配置导航: %s", name)


def _teardown_for_module(driver, module):
    """模块结束时的数据清理"""
    pass


# PageObject fixtures — 每个页面一个 fixture
@pytest.fixture
def hazard_item_page(driver_setup):
    return HazardItemPage(driver_setup)


@pytest.fixture
def hazard_io_record_page(driver_setup):
    return HazardIORecordPage(driver_setup)


@pytest.fixture
def hazard_in_order_page(driver_setup):
    return HazardInOrderPage(driver_setup)


@pytest.fixture
def hazard_stock_page(driver_setup):
    return HazardStockPage(driver_setup)


@pytest.fixture
def reagent_item_page(driver_setup):
    return ReagentItemPage(driver_setup)


@pytest.fixture
def reagent_fill_page(driver_setup):
    return ReagentFillPage(driver_setup)


@pytest.fixture
def spare_item_page(driver_setup):
    return SpareItemPage(driver_setup)


@pytest.fixture
def spare_io_record_page(driver_setup):
    return SpareIORecordPage(driver_setup)


@pytest.fixture
def spare_in_order_page(driver_setup):
    return SpareInOrderPage(driver_setup)


@pytest.fixture
def spare_out_order_page(driver_setup):
    return SpareOutOrderPage(driver_setup)


@pytest.fixture
def spare_requisition_page(driver_setup):
    return SpareRequisitionPage(driver_setup)


@pytest.fixture
def spare_stock_page(driver_setup):
    return SpareStockPage(driver_setup)


@pytest.fixture
def spare_stocktake_page(driver_setup):
    return SpareStocktakePage(driver_setup)


@pytest.fixture
def spare_stock_adjust_page(driver_setup):
    return SpareStockAdjustPage(driver_setup)
