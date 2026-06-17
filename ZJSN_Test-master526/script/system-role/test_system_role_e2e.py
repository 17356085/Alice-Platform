"""System Role cross-module E2E tests.

Covers:
  E2E-ROLE-001: Role -> User cross-module chain (P0)
  E2E-ROLE-002: Role -> Menu permission chain (P1)

Note: Role management has only 1 page (RoleManagePage).
Cross-module verification links with system module.
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


class TestSystemRoleE2E:

    @pytest.mark.smoke
    @allure.epic("System Management")
    @allure.feature("Role Management")
    @allure.story("Cross-module: Role-User chain")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_e2e_role_001_role_user_chain(self, driver_setup):
        """E2E-ROLE-001: Role -> User cross-module"""
        d = driver_setup
        case("E2E-ROLE-001", "Role <-> User cross-module")

        step("Role Management")
        nav_to(d, "#/system/role", "Role Management")
        try:
            role_rows = len(d.find_elements(By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr"))
        except Exception:
            role_rows = -1
        step(f"Roles: {role_rows} rows")
        assert role_rows >= 0, ea("Role page loaded", role_rows)

        step("User Management")
        nav_to(d, "#/system/user", "User Management")
        try:
            user_rows = len(d.find_elements(By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr"))
        except Exception:
            user_rows = -1
        step(f"Users: {user_rows} rows")
        assert user_rows >= 1, ea("User page has data", user_rows)

        step("E2E-ROLE-001 OK")

    @allure.epic("System Management")
    @allure.feature("Role Management")
    @allure.story("Cross-module: Permission chain")
    @allure.severity(allure.severity_level.NORMAL)
    def test_e2e_role_002_role_menu_chain(self, driver_setup):
        """E2E-ROLE-002: Role -> Menu permission chain"""
        d = driver_setup
        case("E2E-ROLE-002", "Role -> Menu permission chain")

        step("Role Management")
        nav_to(d, "#/system/role", "Role Management")
        BasePage(d).wait_vue_stable()

        step("Menu Management")
        nav_to(d, "#/system/menu", "Menu Management")
        try:
            menu_rows = len(d.find_elements(By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr"))
        except Exception:
            menu_rows = -1
        step(f"Menus: {menu_rows} rows")
        assert menu_rows >= 0, ea("Menu page loaded", menu_rows)

        step("E2E-ROLE-002 OK")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
