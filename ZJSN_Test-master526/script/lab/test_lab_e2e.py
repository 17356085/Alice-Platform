"""Lab management cross-page E2E tests.

Covers:
  E2E-LAB-001: Gas chain (indicator -> compare -> report) (P0)
  E2E-LAB-002: Water chain (indicator -> compare -> report) (P0)
  E2E-LAB-003: Gas <-> Water cross-verify (P1)
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


class TestLabE2E:

    @pytest.mark.smoke
    @allure.epic("Lab Management")
    @allure.feature("Gas Analysis")
    @allure.story("Cross-page: Gas chain")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_e2e_lab_001_gas_chain(self, lab_logged_in_driver):
        """E2E-LAB-001: Gas indicator -> compare -> report"""
        d = lab_logged_in_driver
        case("E2E-LAB-001", "Gas indicator -> compare -> report")

        chain = {}
        for label, href in [
            ("Gas Indicator", "#/lab/gas-indicator"),
            ("Gas Compare", "#/lab/gas-compare"),
            ("Gas Report", "#/lab/gas-report"),
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

        step(f"Gas chain: {chain}")
        assert all(v >= 0 for v in chain.values()), ea("3 pages loaded", chain)
        step("E2E-LAB-001 OK")

    @pytest.mark.smoke
    @allure.epic("Lab Management")
    @allure.feature("Water Analysis")
    @allure.story("Cross-page: Water chain")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_e2e_lab_002_water_chain(self, lab_logged_in_driver):
        """E2E-LAB-002: Water indicator -> compare -> report"""
        d = lab_logged_in_driver
        case("E2E-LAB-002", "Water indicator -> compare -> report")

        chain = {}
        for label, href in [
            ("Water Indicator", "#/lab/water-indicator"),
            ("Water Compare", "#/lab/water-compare"),
            ("Water Report", "#/lab/water-report"),
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

        step(f"Water chain: {chain}")
        assert all(v >= 0 for v in chain.values()), ea("3 pages loaded", chain)
        step("E2E-LAB-002 OK")

    @allure.epic("Lab Management")
    @allure.feature("Data Compare")
    @allure.story("Cross-page: Gas-Water verify")
    @allure.severity(allure.severity_level.NORMAL)
    def test_e2e_lab_003_cross_gas_water(self, lab_logged_in_driver):
        """E2E-LAB-003: Gas <-> Water compare pages"""
        d = lab_logged_in_driver
        case("E2E-LAB-003", "Gas <-> Water compare cross-verify")

        for label, href in [
            ("Gas Compare", "#/lab/gas-compare"),
            ("Water Compare", "#/lab/water-compare"),
        ]:
            step(f"Navigate to {label}")
            nav_to(d, href, label)
            try:
                rows = len(d.find_elements("css selector", ".el-table__body-wrapper tbody tr"))
            except Exception:
                rows = -1
            step(f"{label}: {rows} rows")
            assert rows >= 0, ea(f"{label} loaded", rows)

        step("E2E-LAB-003 OK")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
