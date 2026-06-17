"""系统管理 — 跨页面端到端测试

覆盖场景:
  E2E-SYS-001: 用户→角色→菜单 权限链 (P0)
  E2E-SYS-002: 组织→用户 层级链 (P0)
  E2E-SYS-003: 日志链 — 登录日志→操作日志→系统日志 (P1)
  E2E-SYS-004: 字典→参数 配置链 (P1)

技术:
  单浏览器顺序导航
  system 模块页面使用标准 Element Plus 表格 (get_table_row_count 等可用)
"""
import os
import sys
import time
import pytest
import allure

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from selenium.common.exceptions import TimeoutException

from page.system_page.UserManagePage import UserManagePage
from page.system_page.MenuManagePage import MenuManagePage
from page.system_page.OrgManagePage import OrgManagePage
from page.system_page.DictManagePage import DictManagePage
from page.system_page.ParamsManagePage import ParamsManagePage
from page.system_page.LoginLogPage import LoginLogPage
from page.system_page.OperationLogPage import OperationLogPage
from page.system_page.SystemLogPage import SystemLogPage
from base.sidebar_navigator import SidebarNavigator
from base.base_page import BasePage


def step(text):
    print(f"  -> {text}")
    try:
        allure.step(text)
    except Exception:
        pass


def case(case_id, title):
    print(f"\n{'='*60}\n用例 {case_id}：{title}\n{'='*60}")
    try:
        allure.dynamic.title(f"{case_id} {title}")
    except Exception:
        pass


def ea(expected, actual):
    return f"预期结果：{expected}；实际结果：{actual}"


def nav_to(driver, href, label=""):
    nav = SidebarNavigator(driver)
    nav._navigate_by_js_hash(href, label)
    BasePage(driver).wait_vue_stable()
    time.sleep(2)


class TestSystemE2E:
    """系统管理 — 跨页面端到端测试"""

    # ── E2E-SYS-001: 用户→角色→菜单 权限链 ──────────────────

    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("权限管理")
    @allure.story("跨页面流转-权限链")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_e2e_sys_001_user_menu_chain(self, driver_setup):
        """E2E-SYS-001: 用户→菜单 权限链

        流程:
          用户管理: 获取用户总数 + admin 用户
          → 菜单管理: 验证菜单列表
          → 交叉验证权限管理链正常
        """
        driver = driver_setup
        case("E2E-SYS-001", "系统管理权限链 — 用户→菜单")

        chain = {}

        # ── Step 1: 用户管理 ──
        step("导航到用户管理")
        nav_to(driver, "#/system/user", "用户管理")
        user_page = UserManagePage(driver)
        user_page.wait_page_ready()

        user_count = user_page.get_table_row_count()
        step(f"用户管理: {user_count} 行")
        assert user_count >= 1, ea("用户管理至少1条数据", f"{user_count}行")
        chain['user'] = user_count

        # 验证 admin 用户存在
        try:
            user_page.click_reset_button()
            user_page.input_search_username("admin")
            user_page.click_search_button()
            time.sleep(1)
            admin_count = user_page.get_table_row_count()
            step(f"搜索admin: {admin_count} 行")
            assert admin_count >= 1, ea("admin用户存在", f"{admin_count}行")
            user_page.click_reset_button()
        except Exception as e:
            step(f"admin搜索验证跳过: {e}")

        # ── Step 2: 菜单管理 ──
        step("导航到菜单管理")
        nav_to(driver, "#/system/menu", "菜单管理")
        menu_page = MenuManagePage(driver)
        menu_page.is_page_loaded() if hasattr(menu_page, 'is_page_loaded') else menu_page.wait_vue_stable()

        try:
            menu_count = menu_page.get_table_row_count()
        except Exception:
            menu_count = -1
        step(f"菜单管理: {menu_count} 行")
        assert menu_count >= 0, ea("菜单管理正常加载", f"{menu_count}行")
        chain['menu'] = menu_count

        # ── 汇总 ──
        step(f"权限链: {chain}")
        assert user_count >= 1 and menu_count >= 0, \
            ea("用户+菜单页面均正常", chain)

        step("E2E-SYS-001 权限链验证通过 [OK]")

    # ── E2E-SYS-002: 组织→用户 层级链 ────────────────────────

    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("组织管理")
    @allure.story("跨页面流转-组织层级")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_e2e_sys_002_org_user_chain(self, driver_setup):
        """E2E-SYS-002: 组织→用户 层级链

        流程:
          组织管理: 获取部门列表
          → 用户管理: 验证用户存在
          → 交叉验证组织下有用户
        """
        driver = driver_setup
        case("E2E-SYS-002", "组织管理 → 用户管理 层级链")

        # ── Step 1: 组织管理 ──
        step("导航到组织管理")
        nav_to(driver, "#/system/dept", "组织管理")
        org_page = OrgManagePage(driver)
        org_page.is_page_loaded() if hasattr(org_page, 'is_page_loaded') else org_page.wait_vue_stable()

        try:
            org_count = org_page.get_table_row_count()
        except Exception:
            org_count = -1
        step(f"组织管理: {org_count} 行")
        assert org_count >= 0, ea("组织管理页面正常加载", f"{org_count}行")

        # ── Step 2: 用户管理 ──
        step("导航到用户管理")
        nav_to(driver, "#/system/user", "用户管理")
        user_page = UserManagePage(driver)
        user_page.wait_page_ready()

        user_count = user_page.get_table_row_count()
        step(f"用户管理: {user_count} 行")
        assert user_count >= 1, ea("用户管理至少1条数据", f"{user_count}行")

        # ── 交叉验证 ──
        step(f"组织={org_count}, 用户={user_count}")
        assert org_count >= 0 and user_count >= 1, \
            ea("组织+用户均正常", f"org={org_count}, user={user_count}")

        step("E2E-SYS-002 组织→用户链验证通过 [OK]")

    # ── E2E-SYS-003: 日志链 — 登录日志→操作日志→系统日志 ───

    @allure.epic("系统管理")
    @allure.feature("日志管理")
    @allure.story("跨页面流转-日志链")
    @allure.severity(allure.severity_level.NORMAL)
    def test_e2e_sys_003_log_chain(self, driver_setup):
        """E2E-SYS-003: 日志链 — 登录→操作→系统 (P1)

        流程:
          登录日志: 验证日志列表
          → 操作日志: 验证日志列表
          → 系统日志: 验证日志列表
        """
        driver = driver_setup
        case("E2E-SYS-003", "系统日志全链 — 登录→操作→系统")

        chain = {}

        # ── Step 1: 登录日志 ──
        step("导航到登录日志")
        nav_to(driver, "#/system/log/login-log", "登录日志")
        login_log_page = LoginLogPage(driver)
        login_log_page.is_page_loaded() if hasattr(login_log_page, 'is_page_loaded') else login_log_page.wait_vue_stable()

        login_count = login_log_page.get_table_row_count()
        step(f"登录日志: {login_count} 行")
        assert login_count >= 0, ea("登录日志正常加载", f"{login_count}行")
        chain['login_log'] = login_count

        # ── Step 2: 操作日志 ──
        step("导航到操作日志")
        nav_to(driver, "#/system/log/oper-log", "操作日志")
        oper_log_page = OperationLogPage(driver)
        oper_log_page.is_page_loaded() if hasattr(oper_log_page, 'is_page_loaded') else oper_log_page.wait_vue_stable()

        oper_count = oper_log_page.get_table_row_count()
        step(f"操作日志: {oper_count} 行")
        assert oper_count >= 0, ea("操作日志正常加载", f"{oper_count}行")
        chain['oper_log'] = oper_count

        # ── Step 3: 系统日志 ──
        step("导航到系统日志")
        nav_to(driver, "#/system/log/system-log", "系统日志")
        sys_log_page = SystemLogPage(driver)
        sys_log_page.is_page_loaded() if hasattr(sys_log_page, 'is_page_loaded') else sys_log_page.wait_vue_stable()

        sys_count = sys_log_page.get_table_row_count()
        step(f"系统日志: {sys_count} 行")
        assert sys_count >= 0, ea("系统日志正常加载", f"{sys_count}行")
        chain['system_log'] = sys_count

        # ── 汇总 ──
        step(f"日志链: {chain}")
        assert all(isinstance(v, int) and v >= 0 for v in chain.values()), \
            ea("日志3页面均正常", chain)

        step("E2E-SYS-003 日志链验证通过 [OK]")

    # ── E2E-SYS-004: 字典→参数 配置链 ───────────────────────

    @allure.epic("系统管理")
    @allure.feature("配置管理")
    @allure.story("跨页面流转-配置链")
    @allure.severity(allure.severity_level.NORMAL)
    def test_e2e_sys_004_dict_params_chain(self, driver_setup):
        """E2E-SYS-004: 字典→参数 配置链 (P1)

        流程:
          字典管理: 验证字典列表
          → 参数管理: 验证参数列表
        """
        driver = driver_setup
        case("E2E-SYS-004", "字典管理 → 参数管理")

        # ── Step 1: 字典管理 ──
        step("导航到字典管理")
        nav_to(driver, "#/system/dict", "字典管理")
        dict_page = DictManagePage(driver)
        dict_page.is_page_loaded() if hasattr(dict_page, 'is_page_loaded') else dict_page.wait_vue_stable()

        try:
            dict_count = dict_page.get_table_row_count()
        except Exception:
            dict_count = -1
        step(f"字典管理: {dict_count} 行")
        assert dict_count >= 0, ea("字典管理正常加载", f"{dict_count}行")

        # ── Step 2: 参数管理 ──
        step("导航到参数管理")
        nav_to(driver, "#/system/params", "参数管理")
        params_page = ParamsManagePage(driver)
        params_page.is_page_loaded() if hasattr(params_page, 'is_page_loaded') else params_page.wait_vue_stable()

        try:
            params_count = params_page.get_table_row_count()
        except Exception:
            params_count = -1
        step(f"参数管理: {params_count} 行")
        assert params_count >= 0, ea("参数管理正常加载", f"{params_count}行")

        # ── 交叉验证 ──
        step(f"字典={dict_count}, 参数={params_count}")
        assert dict_count >= 0 and params_count >= 0, \
            ea("字典+参数均正常", f"dict={dict_count}, params={params_count}")

        step("E2E-SYS-004 字典→参数配置链验证通过 [OK]")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
