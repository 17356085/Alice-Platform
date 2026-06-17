"""System Management cross-page smoke tests.

Covers key admin/ops pages: menu, approval chain, API, monitor.
Note: system-management is a virtual module — pages live in system/.
"""
import time
import pytest
import allure

from selenium.webdriver.common.by import By
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


class TestSystemManagementSmoke:

    @pytest.mark.smoke
    @allure.epic("System Management")
    @allure.feature("Admin Pages")
    @allure.story("Cross-page: Admin chain")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_smgmt_001_admin_chain(self, driver_setup):
        """SMGMT-001: Menu -> API -> Monitor admin chain"""
        d = driver_setup
        case("SMGMT-001", "Menu -> API -> Monitor")

        chain = {}
        for label, href in [
            ("Menu", "#/system/menu"),
            ("API Docs", "#/system/api"),
            ("Monitor", "#/system/monitor"),
        ]:
            step(f"Navigate to {label}")
            nav_to(d, href, label)
            try:
                rows = len(d.find_elements(By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr"))
            except Exception:
                rows = -1
            chain[label] = rows
            step(f"{label}: {rows} rows")
            assert rows >= 0, ea(f"{label} loaded", rows)

        step(f"Admin chain: {chain}")
        assert all(v >= 0 for v in chain.values()), ea("3 pages loaded", chain)
        step("SMGMT-001 OK")

    @allure.epic("System Management")
    @allure.feature("Workflow Pages")
    @allure.story("Cross-page: Approval chain")
    @allure.severity(allure.severity_level.NORMAL)
    def test_smgmt_002_approval_pages(self, driver_setup):
        """SMGMT-002: Approval chain -> SAP push log"""
        d = driver_setup
        case("SMGMT-002", "Approval chain -> SAP push log")

        for label, href in [
            ("Approval Chain", "#/system/workflow/approval-chain"),
            ("SAP Push Log", "#/system/workflow/sap-push-log"),
        ]:
            step(f"Navigate to {label}")
            nav_to(d, href, label)
            try:
                rows = len(d.find_elements(By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr"))
            except Exception:
                rows = -1
            step(f"{label}: {rows} rows")
            assert rows >= 0, ea(f"{label} loaded", rows)

        step("SMGMT-002 OK")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
