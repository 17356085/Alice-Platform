"""Minimal test: just create one role"""
import sys, time
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.RoleManagePage import RoleManagePage

base = BaseDriver()
d = base.open_browser()
d.maximize_window()
ensure_logged_in(d)
time.sleep(2)

nav = SidebarNavigator(d)
nav._navigate_by_js_hash('#/system/role', 'role')
time.sleep(3)
rp = RoleManagePage(d)
rp.wait_vue_stable()

# Test search with known role
rp.click_reset()
time.sleep(0.5)
rp.input_role_name("admin")
rp.click_search()
rp.wait_table_ready(timeout=8)
print("Search 'admin' - rows:", rp.get_table_row_count())

rp.click_reset()
time.sleep(0.5)
rp.input_role_name("RBAC-SYS-ONLY")
rp.click_search()
rp.wait_table_ready(timeout=8)
print("Search 'RBAC-SYS-ONLY' - rows:", rp.get_table_row_count())

d.quit()
