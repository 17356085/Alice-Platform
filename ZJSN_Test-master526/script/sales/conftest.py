"""销售管理模块共享 fixtures

Fixture 层级：
  - contract_page (function 级)：每个测试函数独立 Page Object
  - driver_setup (module 级)：每个 test_*.py 文件独立浏览器实例
  - session_logged_in_browser (session 级)：整目录共享（如需）

使用方式：
    def test_xxx(self, contract_page):
        page = contract_page
        page.search(contract_no="HT20260527")

    # 或使用原始 driver
    def test_xxx(self, driver_setup):
        from page.sales_page.ContractPage import ContractPage
        page = ContractPage(driver_setup)
"""
import logging
import os

import pytest
import yaml

from base.browser_driver import BaseDriver, ensure_logged_in
from page.sales_page.ContractPage import ContractPage
from page.sales_page.CustomerPage import CustomerPage
from page.sales_page.SalesOrderPage import SalesOrderPage
from page.sales_page.DailyReportPage import DailyReportPage

logger = logging.getLogger(__name__)

_FIXTURES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "fixtures"
)

# ── 模块 → Page Object 工厂（支持前缀匹配：test_contract_search → test_contract）──
_MODULE_PAGE_FACTORIES = {
    "test_contract":    lambda d: ContractPage(d),
    "test_customer":    lambda d: CustomerPage(d),
    "test_sales_order": lambda d: SalesOrderPage(d),
    "test_daily_report": lambda d: DailyReportPage(d),
}


def _navigate_for_module(driver, module):
    """按测试模块导航到目标页面（JS hash 直接跳转，绕过侧边栏）"""
    from base.sidebar_navigator import SidebarNavigator

    name = module.__name__.split(".")[-1]

    # JS hash 路由映射（最可靠的方式）
    _MODULE_HASH_ROUTES = {
        "test_contract":              "#/sales/contract",
        "test_contract_display":      "#/sales/contract",
        "test_contract_search":       "#/sales/contract",
        "test_contract_pagination":   "#/sales/contract",
        "test_contract_workflow":     "#/sales/contract",
        "test_customer":              "#/sales/customer",
        "test_customer_cdp":          "#/sales/customer",
        "test_customer_cdp_fetch":    "#/sales/customer",
        "test_customer_pagination":   "#/sales/customer",
        "test_sales_order":           "#/sales/order",
        "test_sales_order_search":    "#/sales/order",
        "test_sales_order_display":   "#/sales/order",
        "test_sales_order_crud":      "#/sales/order",
        "test_daily_report":          "#/sales/measurement",
        "test_daily_report_display":  "#/sales/measurement",
        "test_daily_report_search":   "#/sales/measurement",
        "test_daily_report_pagination":"#/sales/measurement",
        "test_daily_report_boundary": "#/sales/measurement",
        "test_daily_report_data_integrity": "#/sales/measurement",
    }

    # 前缀匹配
    href = _MODULE_HASH_ROUTES.get(name)
    if not href:
        for key, h in _MODULE_HASH_ROUTES.items():
            if name.startswith(key):
                href = h
                break

    if href:
        logger.info("销售模块导航: %s → %s", name, href)
        nav = SidebarNavigator(driver)
        nav._navigate_by_js_hash(href, name)
    else:
        logger.warning("未配置销售模块导航: %s", name)


def _teardown_for_module(driver, module):
    """模块结束时的数据清理"""
    name = module.__name__.split(".")[-1]
    if name == "test_customer":
        _teardown_customer(driver, module)
    elif name == "test_contract":
        _teardown_contract(driver, module)
    elif name == "test_sales_order":
        _teardown_order(driver, module)


def _teardown_customer(driver, module):
    """清理客户管理模块创建的测试数据"""
    customer_name = getattr(module, "CREATED_CUSTOMER_NAME", None)
    if not customer_name:
        return
    logger.info("客户管理模块后置清理: %s", customer_name)
    try:
        page = CustomerPage(driver)
        page.navigate()
        page.search_by_keyword(customer_name)
        if page.is_row_present(customer_name):
            logger.info("客户 %s 存在于列表中，尝试清理", customer_name)
    except Exception as exc:
        logger.warning("客户后置清理失败: %s", exc)


def _teardown_contract(driver, module):
    """清理合同管理模块创建的测试数据（只读模块，通常无需清理）"""
    contract_no = getattr(module, "CREATED_CONTRACT_NO", None)
    if not contract_no:
        return
    logger.info("合同管理模块后置清理: %s", contract_no)
    try:
        page = ContractPage(driver)
        page.navigate()
        page.click_reset()
        page.input_contract_no(contract_no)
        page.click_search()
        # 合同管理为只读页面（仅展示/跳转），无需删除
        # 如有删除逻辑，在此处实现
        if page.is_contract_present(contract_no):
            logger.info("合同 %s 仍存在于列表中（只读模块，跳过清理）", contract_no)
    except Exception as exc:
        logger.warning("合同后置清理失败: %s", exc)


def _teardown_order(driver, module):
    """清理销售订单模块创建的测试数据"""
    order_no = getattr(module, "CREATED_ORDER_NO", None)
    order_plate = getattr(module, "CREATED_ORDER_PLATE", None)
    if not order_no and not order_plate:
        return
    identifier = order_no or order_plate
    logger.info("销售订单模块后置清理: %s", identifier)
    try:
        page = SalesOrderPage(driver)
        page.navigate()
        page.click_reset()
        if order_no:
            page.search(order_no=order_no)
        else:
            page.search(customer=order_plate)
        # 查找测试数据是否存在（验证清理对象）
        if page.is_order_present(identifier):
            logger.info("测试数据 %s 存在于列表中", identifier)
        else:
            logger.info("测试数据 %s 未找到，可能已被清理", identifier)
    except Exception as exc:
        logger.warning("订单后置清理失败: %s", exc)


# ==================================================================
#  Module 级 Fixture: 独立浏览器 + 自动导航
# ==================================================================
@pytest.fixture(scope="module")
def driver_setup(request):
    """Module 级：每个测试文件一个浏览器实例，自动导航到目标页面"""
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
#  Function 级 Fixture: 合同页面 Page Object
# ==================================================================
@pytest.fixture(scope="function")
def contract_page(driver_setup):
    """每个测试函数获取已初始化的 ContractPage

    自动确保页面已加载，每个用例从一致的状态开始。

    使用：
        def test_xxx(contract_page):
            contract_page.click_reset()  # 从干净状态开始
            contract_page.search(contract_no="HT20260527")
    """
    page = ContractPage(driver_setup)
    # module 级已导航，这里等待页面就绪（含 loading gone + vue stable + table ready）
    page._wait_page_ready(timeout=15)

    # 表格无数据时重新导航一次
    try:
        if page.get_table_row_count() == 0:
            logger.warning("表格无数据行，尝试重新导航")
            page.navigate()
            page._wait_page_ready(timeout=15)
    except Exception:
        logger.warning("获取表格行数异常，尝试重新导航")
        page.navigate()
        page._wait_page_ready(timeout=15)

    # 重置到干净状态，等 Vue 重新渲染完成
    try:
        page.click_reset()
        page.wait_vue_stable()
    except Exception:
        logger.info("重置按钮不可用（可能已在初始状态），继续执行")

    # 预热搜索：确保 API 通道畅通
    try:
        if page.get_table_row_count() > 0:
            page.click_search()
            page.wait_vue_stable()
            logger.info("预热搜索完成: %d行数据就绪", page.get_table_row_count())
    except Exception:
        logger.debug("预热跳过")
    return page


# ==================================================================
#  Function 级 Fixture: 日报表页面 Page Object
# ==================================================================
@pytest.fixture(scope="function")
def daily_report_page(driver_setup):
    """每个测试函数获取已初始化的 DailyReportPage

    自动确保页面已加载，每个用例从一致的状态开始。

    使用：
        def test_xxx(self, daily_report_page):
            page = daily_report_page
            page.click_reset()  # 从干净状态开始
            page.query_date_range("2026-05-01", "2026-05-31")
    """
    page = DailyReportPage(driver_setup)

    # __init__ 已做 _wait_page_ready(15)，此处仅补充短等待
    page._wait_loading_gone(timeout=3)
    page.wait_vue_stable()

    # 表格无数据时等待额外渲染
    try:
        row_count = page.get_table_row_count()
    except Exception:
        row_count = 0

    if row_count == 0:
        logger.info("表格暂无数据行，等待额外渲染...")
        try:
            page._wait_table_ready(timeout=15)
        except Exception:
            logger.warning("表格仍不可用，继续执行（测试中会自行skip或等待）")

    # 尝试重置到干净状态（不强制要求成功）
    try:
        page.click_reset()
    except Exception:
        logger.info("日报表重置按钮不可用（可能已在初始状态），继续执行")

    return page


# ==================================================================
#  Session 级 Fixture: 整目录共享（可选，用于需要跨模块的用例）
# ==================================================================
@pytest.fixture(scope="session")
def session_logged_in_browser():
    """Session 级：启动浏览器并完成登录，所有模块共享"""
    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)
        logger.info("Sales session: 登录完成")
        yield driver
    finally:
        base.close_browser()
        logger.info("Sales session: 浏览器已关闭")


@pytest.fixture(scope="session")
def contract_test_data():
    """Session 级：从 YAML 文件加载合同管理测试数据，整个会话共享一份。"""
    yaml_path = os.path.join(_FIXTURES_DIR, "sales_contract.yaml")
    with open(yaml_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def daily_report_test_data():
    """Session 级：从 YAML 文件加载日报表测试数据，整个会话共享一份。"""
    yaml_path = os.path.join(_FIXTURES_DIR, "sales_daily_report.yaml")
    with open(yaml_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ==================================================================
#  测试数据准备：创建客户 + 合同，供销售订单 CRUD 测试使用
# ==================================================================
def prepare_sales_order_test_data(driver):
    """获取测试所需的客户和合同（使用已有数据，不创建新数据）

    流程：
      1. SalesOrderPage → 获取已有客户名称
      2. ContractPage   → 获取已有合同编号
      3. 导航回 SalesOrderPage

    若获取失败，返回 (None, None)。
    """
    customer_name = None
    contract_name = None

    logger.info("=== 获取测试数据（已有客户+合同）===")

    # ── Step 1: 从销售订单页面的已有数据获取客户名 ──
    try:
        order_page = SalesOrderPage(driver)
        customers = order_page.get_column_data(order_page.COL_CUSTOMER)
        contracts = order_page.get_column_data(order_page.COL_CONTRACT)
        if customers:
            customer_name = customers[0]
        if contracts:
            contract_name = contracts[0]
        logger.info("从销售订单获取: 客户=%s, 合同=%s", customer_name, contract_name)
    except Exception as e:
        logger.warning("从销售订单获取数据失败: %s", e)

    # ── Fallback: 从合同页面获取 ──
    if not contract_name:
        try:
            contract_page = ContractPage(driver)
            contract_page.navigate()
            if contract_page.get_table_row_count() > 0:
                contract_nos = contract_page.get_column_data(contract_page.COL_CONTRACT_NO)
                if contract_nos:
                    contract_name = contract_nos[0]
                    logger.info("从合同页面获取: %s", contract_name)
        except Exception as e:
            logger.warning("从合同页面获取失败: %s", e)

    # ── 回到销售订单页面 ──
    try:
        SalesOrderPage(driver).navigate()
    except Exception:
        pass

    logger.info("=== 数据获取完成: 客户=%s, 合同=%s ===", customer_name, contract_name)
    return customer_name, contract_name


@pytest.fixture(scope="module")
def sales_test_data(driver_setup):
    """Module 级：为销售订单 CRUD 测试准备客户+合同数据

    返回:
        dict: {"customer": str, "contract": str}
        若准备失败，返回 {"customer": None, "contract": None}
    """
    customer, contract = prepare_sales_order_test_data(driver_setup)
    return {"customer": customer, "contract": contract}
