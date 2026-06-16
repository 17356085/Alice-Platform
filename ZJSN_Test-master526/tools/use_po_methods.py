"""Use existing UserManagePage methods for role assignment"""
import sys, time
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.UserManagePage import UserManagePage
from page.system_page.LoginPage import LoginPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

PWD = "Ajyl@2026"

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

# Search
up.click_reset_button(); time.sleep(0.5)
up.input_search_username("rbac_test_sys"); up.click_search_button(); time.sleep(2)
print("Found:", up.get_table_row_count())

# Open edit dialog
up.click_edit_user("rbac_test_sys")
time.sleep(3)
print("Edit open")

# Use the EXISTING PO methods
print("Opening role select...")
up.open_dialog_select("角色")
time.sleep(1.5)

print("Selecting RBAC-SYS-ONLY...")
up.select_dialog_option_by_text("角色", "RBAC-SYS-ONLY")
time.sleep(1)

print("Confirming...")
up.click_dialog_confirm()
time.sleep(3)
print("Saved")

# Verify
d.get("https://aiwechatminidemo.cimc-digital.com/")
time.sleep(3)
lp = LoginPage(d)
lp.input_username("rbac_test_sys"); lp.input_password(PWD)
btns = d.find_elements(By.XPATH, "//button[.//span[contains(.,'登')]]")
if btns: btns[0].click()
else: d.execute_script("document.querySelector('.el-button--primary').click();")
try: WebDriverWait(d, 15).until(lambda x: "#/login" not in (x.current_url or ""))
except: pass
lp.wait_vue_stable(); time.sleep(3)

menus = d.execute_script("""
var m = [];
document.querySelectorAll('.el-menu > li.el-sub-menu > .el-sub-menu__title span')
    .forEach(function(s) { var t = (s.innerText || '').trim(); if (t) m.push(t); });
document.querySelectorAll('.el-menu > li.el-menu-item span')
    .forEach(function(s) { var t = (s.innerText || '').trim(); if (t) m.push(t); });
return m;
""")
print("SIDEBAR (%d): %s" % (len(menus), menus))

d.quit()
