"""Debug: what does the role page show?"""
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

# Get current table data
headers = rp.get_table_headers()
print("Headers:", headers)

# Get first column (role name) data
names = rp.get_column_data(2)  # column 2 = role name
print("Role names in table:", names[:15])

# Now search
rp.click_reset()
time.sleep(0.5)
rp.input_role_name("RBAC-SYS-ONLY")
rp.click_search()
rp.wait_table_ready(timeout=8)

names2 = rp.get_column_data(2)
print("After search - Role names:", names2[:15])
print("Table rows:", rp.get_table_row_count())

d.quit()
