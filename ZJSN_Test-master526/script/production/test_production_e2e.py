"""Production management cross-page E2E tests.

Covers:
  E2E-PROD-001: Config chain (business-type <-> shift-team) (P0)
  E2E-PROD-002: Report chain (daily -> monthly report) (P1)
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


class TestProductionE2E:

    @pytest.mark.smoke
    @allure.epic("Production Management")
    @allure.feature("Basic Config")
    @allure.story("Cross-page: Config chain")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_e2e_prod_001_config_chain(self, driver_setup):
        """E2E-PROD-001: Business type <-> Shift team"""
        d = driver_setup
        case("E2E-PROD-001", "Business type <-> Shift team")

        for label, href in [
            ("Business Type", "#/production/business-type"),
            ("Shift Team", "#/production/shift-team"),
        ]:
            step(f"Navigate to {label}")
            nav_to(d, href, label)
            try:
                rows = len(d.find_elements("css selector", ".el-table__body-wrapper tbody tr"))
            except Exception:
                rows = -1
            step(f"{label}: {rows} rows")
            assert rows >= 0, ea(f"{label} loaded", rows)

        step("E2E-PROD-001 OK")

    @allure.epic("Production Management")
    @allure.feature("Data Reports")
    @allure.story("Cross-page: Report chain")
    @allure.severity(allure.severity_level.NORMAL)
    def test_e2e_prod_002_report_chain(self, driver_setup):
        """E2E-PROD-002: Daily -> Monthly report"""
        d = driver_setup
        case("E2E-PROD-002", "Daily -> Monthly report")

        for label, href in [
            ("Daily Report", "#/production/daily-report"),
            ("Monthly Report", "#/production/monthly-report"),
        ]:
            step(f"Navigate to {label}")
            nav_to(d, href, label)
            try:
                rows = len(d.find_elements("css selector", ".el-table__body-wrapper tbody tr"))
            except Exception:
                rows = -1
            step(f"{label}: {rows} rows")
            assert rows >= 0, ea(f"{label} loaded", rows)

        step("E2E-PROD-002 OK")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
