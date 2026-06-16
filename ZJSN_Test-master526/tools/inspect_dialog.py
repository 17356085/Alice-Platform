"""Inspect the edit user dialog structure"""
import sys, time
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.UserManagePage import UserManagePage

base = BaseDriver()
d = base.open_browser()
d.maximize_window()
ensure_logged_in(d)
time.sleep(2)

nav = SidebarNavigator(d)
nav._navigate_by_js_hash('#/system/user', 'u')
time.sleep(3)
up = UserManagePage(d)
up.wait_vue_stable()
up.click_reset_button(); time.sleep(0.5)
up.input_search_username('rbac_test_sys'); up.click_search_button(); time.sleep(2)
print("Rows:", up.get_table_row_count())

up.click_edit_user('rbac_test_sys')
time.sleep(3)
print("Edit dialog open")

# Dump dialog content
html = d.execute_script("""
    var dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
    if (!dlg) {
        var ds = document.querySelectorAll('.el-dialog');
        for (var i = 0; i < ds.length; i++) {
            if (ds[i].offsetParent) { dlg = ds[i]; break; }
        }
    }
    if (!dlg) return 'NO_DIALOG';
    var body = dlg.querySelector('.el-dialog__body');
    if (!body) return 'NO_BODY';
    return body.innerHTML;
""")
print("DIALOG HTML:")
print((html or 'None')[:4000])

d.quit()
