"""Use UserManagePage PO methods to edit user and assign role"""
import sys, time
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.UserManagePage import UserManagePage
from page.system_page.RoleManagePage import RoleManagePage
from page.system_page.LoginPage import LoginPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

base = BaseDriver()
d = base.open_browser()
d.maximize_window()
ensure_logged_in(d)
time.sleep(2)

# Navigate to user management
nav = SidebarNavigator(d)
nav._navigate_by_js_hash('#/system/user', 'user')
time.sleep(3)
up = UserManagePage(d)
up.wait_vue_stable()

# Search for rbac_test_sys
print("Searching rbac_test_sys...")
up.click_reset_button()
time.sleep(0.5)
up.input_search_username("rbac_test_sys")
up.click_search_button()
time.sleep(2)

count = up.get_table_row_count()
print("Rows found: %d" % count)
if count == 0:
    print("User not found!")
    d.quit()
    sys.exit(1)

# Click edit
print("Clicking edit...")
up.click_edit_user("rbac_test_sys")
time.sleep(2)

# Select role in edit dialog
print("Selecting role RBAC-SYS-ONLY...")
up.select_role_in_dialog("RBAC-SYS-ONLY")
time.sleep(1)

# Click confirm
print("Confirming...")
up.click_dialog_confirm()
time.sleep(2)

# Check for toast
try:
    toast = up.wait_for_toast_text(timeout=5)
    print("Edit toast: %s" % (toast or "no toast"))
except:
    print("No toast")

# Clear cache
print("Clearing cache...")
nav._navigate_by_js_hash('#/system/role', 'role')
time.sleep(3)
rp = RoleManagePage(d)
rp.wait_vue_stable()
rp.click_clear_cache()
time.sleep(2)
print("Cache cleared")

# Logout and login as rbac_test_sys
print("Logging in as rbac_test_sys...")
d.get("https://aiwechatminidemo.cimc-digital.com/")
time.sleep(3)
lp = LoginPage(d)
lp.input_username("rbac_test_sys")
lp.input_password("Ajyl@2026")
btns = d.find_elements(By.XPATH, "//button[.//span[contains(.,'登')]]")
if btns:
    btns[0].click()
else:
    d.execute_script("document.querySelector('.el-button--primary').click();")
try:
    WebDriverWait(d, 15).until(lambda x: "#/login" not in (x.current_url or ""))
except:
    pass
lp.wait_vue_stable()
time.sleep(3)

# Check sidebar
menus = d.execute_script('''
    var m=[];
    document.querySelectorAll('.el-menu > li.el-sub-menu > .el-sub-menu__title span')
        .forEach(function(s){var t=(s.innerText||'').trim();if(t)m.push(t);});
    document.querySelectorAll('.el-menu > li.el-menu-item span')
        .forEach(function(s){var t=(s.innerText||'').trim();if(t)m.push(t);});
    return m;
''')
print("SIDEBAR (%d): %s" % (len(menus), menus))

if len(menus) > 0:
    print("\n*** SUCCESS! Sidebar has menus! ***")
else:
    print("\n*** Sidebar still empty ***")

d.quit()
