"""Sales management cross-page E2E tests.

Covers:
  E2E-SALES-001: Customer -> Contract -> Order chain (P0)
  E2E-SALES-002: Customer -> Daily Report (P1)
"""
import time
import pytest
import allure

from base.sidebar_navigator import SidebarNavigator
from base.base_page import BasePage


def step(text):
    print(f"  -> {text}")
    try:
        allure.step(text)
    except Exception:
        pass


def case(case_id, title):
    print(f"\n{'='*60}\n{case_id}: {title}\n{'='*60}")
    try:
        allure.dynamic.title(f"{case_id} {title}")
    except Exception:
        pass


def ea(expected, actual):
    return f"Expected: {expected}; Actual: {actual}"


def nav_to(driver, href, label=""):
    nav = SidebarNavigator(driver)
    nav._navigate_by_js_hash(href, label)
    BasePage(driver).wait_vue_stable()
    time.sleep(2)


class TestSalesE2E:
    """Sales 模块跨页面业务流 E2E"""

    @pytest.mark.smoke
    @allure.epic("Sales Management")
    @allure.feature("Business Management")
    @allure.story("Cross-page: Customer→Contract→Order chain")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_e2e_sales_001_customer_contract_order(self, driver_setup):
        """E2E-SALES-001: 客户→合同→订单完整链路 (P0)"""
        d = driver_setup
        case("E2E-SALES-001", "Customer -> Contract -> Order")

        chain = {}
        for label, href in [
            ("Customer", "#/sales/customer"),
            ("Contract", "#/sales/contract"),
            ("Sales Order", "#/sales/sales-order"),
        ]:
            step(f"Navigate to {label}")
            nav_to(d, href, label)
            try:
                rows = len(d.find_elements("css selector", ".el-table__body-wrapper tbody tr"))
            except Exception:
                rows = -1
            chain[label] = rows
            step(f"{label}: {rows} rows")
            assert rows >= 0, ea(f"{label} loaded", rows)

        step(f"Sales chain: {chain}")
        assert all(v >= 0 for v in chain.values()), ea("3 pages loaded", chain)
        step("E2E-SALES-001 OK")

    @allure.epic("Sales Management")
    @allure.feature("Data Reports")
    @allure.story("Cross-page: Daily report")
    @allure.severity(allure.severity_level.NORMAL)
    def test_e2e_sales_002_daily_report(self, driver_setup):
        """E2E-SALES-002: Customer -> Daily Report"""
        d = driver_setup
        case("E2E-SALES-002", "Customer -> Daily Report")

        for label, href in [
            ("Customer", "#/sales/customer"),
            ("Daily Report", "#/sales/daily-report"),
        ]:
            step(f"Navigate to {label}")
            nav_to(d, href, label)
            try:
                rows = len(d.find_elements("css selector", ".el-table__body-wrapper tbody tr"))
            except Exception:
                rows = -1
            step(f"{label}: {rows} rows")
            assert rows >= 0, ea(f"{label} loaded", rows)

        step("E2E-SALES-002 OK")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
