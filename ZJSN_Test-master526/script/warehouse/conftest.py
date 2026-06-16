"""库管管理模块共享 fixtures

覆盖 3 个子模块 15 个页面。
每个 test_*.py 独立浏览器实例（module scope）。
"""
import logging
import time

import pytest

from base.browser_driver import BaseDriver, ensure_logged_in
from base.base_page import BasePage
from base.sidebar_navigator import SidebarNavigator

# ── Page Object 导入 ──────────────────────────────────────────
from page.warehouse_page.SpareRequisitionPage import SpareRequisitionPage
from page.warehouse_page.SpareOutOrderPage import SpareOutOrderPage
from page.warehouse_page.SpareInOrderPage import SpareInOrderPage
from page.warehouse_page.HazardInOrderPage import HazardInOrderPage
from page.warehouse_page.SpareStockPage import SpareStockPage
from page.warehouse_page.SpareStocktakePage import SpareStocktakePage
from page.warehouse_page.SpareStockAdjustPage import SpareStockAdjustPage
from page.warehouse_page.SpareIORecordPage import SpareIORecordPage
from page.warehouse_page.SpareItemPage import SpareItemPage
from page.warehouse_page.HazardStockPage import HazardStockPage
from page.warehouse_page.HazardIORecordPage import HazardIORecordPage
from page.warehouse_page.HazardItemPage import HazardItemPage
from page.warehouse_page.ReagentItemPage import ReagentItemPage
from page.warehouse_page.ReagentFillPage import ReagentFillPage

logger = logging.getLogger(__name__)

# ── 测试模块 → hash 路由映射 ─────────────────────────────────
_MODULE_HASH_ROUTES = {
    # 备品备件
    "test_spare_requisition":  "#/warehouse/spare/requisition",
    "test_spare_out_order":    "#/warehouse/spare/out-order",
    "test_spare_in_order":     "#/warehouse/spare/in-order",
    "test_spare_stock":        "#/warehouse/spare/stock",
    "test_spare_stocktake":    "#/warehouse/spare/stocktake",
    "test_spare_stock_adjust": "#/warehouse/spare/stock-adjust",
    "test_spare_io_record":    "#/warehouse/spare/io-record",
    "test_spare_item":         "#/warehouse/spare/item",
    # 环保危废
    "test_hazard_in_order":    "#/warehouse/hazard/in-order",
    "test_hazard_out_order":   "#/warehouse/hazard/out-order",
    "test_hazard_stock":       "#/warehouse/hazard/stock",
    "test_hazard_io_record":   "#/warehouse/hazard/io-record",
    "test_hazard_item":        "#/warehouse/hazard/item",
    # 三剂消耗
    "test_reagent_item":       "#/warehouse/reagent/item",
    "test_reagent_fill":       "#/warehouse/reagent/fill",
}


def _navigate_for_module(driver, module):
    """按测试模块名导航到对应仓库管理页面"""
    name = module.__name__.split(".")[-1]
    bp = BasePage(driver)
    nav = SidebarNavigator(driver)

    href = _MODULE_HASH_ROUTES.get(name)
    if href:
        logger.info("仓库模块导航: %s → %s", name, href)
        nav._navigate_by_js_hash(href, name)
        bp.wait_vue_stable()
        bp._wait_loading_gone(timeout=15)
    else:
        logger.warning("未配置仓库模块导航: %s，可用路由: %s",
                       name, list(_MODULE_HASH_ROUTES.keys()))


@pytest.fixture(scope="module")
def driver_setup(request):
    """Module 级 fixture：登录 + 导航到对应仓库页面"""
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


# ══════════════════════════════════════════════════════════════
#  页面级 fixtures
# ══════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def spare_requisition_page(driver_setup):
    return SpareRequisitionPage(driver_setup)


@pytest.fixture(scope="module")
def spare_out_order_page(driver_setup):
    return SpareOutOrderPage(driver_setup)


@pytest.fixture(scope="module")
def spare_in_order_page(driver_setup):
    return SpareInOrderPage(driver_setup)


@pytest.fixture(scope="module")
def spare_stock_page(driver_setup):
    return SpareStockPage(driver_setup)


@pytest.fixture(scope="module")
def spare_stocktake_page(driver_setup):
    return SpareStocktakePage(driver_setup)


@pytest.fixture(scope="module")
def spare_stock_adjust_page(driver_setup):
    return SpareStockAdjustPage(driver_setup)


@pytest.fixture(scope="module")
def spare_io_record_page(driver_setup):
    return SpareIORecordPage(driver_setup)


@pytest.fixture(scope="module")
def spare_item_page(driver_setup):
    return SpareItemPage(driver_setup)


@pytest.fixture(scope="module")
def hazard_stock_page(driver_setup):
    return HazardStockPage(driver_setup)


@pytest.fixture(scope="module")
def hazard_io_record_page(driver_setup):
    return HazardIORecordPage(driver_setup)


@pytest.fixture(scope="module")
def hazard_item_page(driver_setup):
    return HazardItemPage(driver_setup)


@pytest.fixture(scope="module")
def reagent_item_page(driver_setup):
    return ReagentItemPage(driver_setup)


@pytest.fixture(scope="module")
def reagent_fill_page(driver_setup):
    return ReagentFillPage(driver_setup)


@pytest.fixture(scope="module")
def hazard_in_order_page(driver_setup):
    return HazardInOrderPage(driver_setup)
