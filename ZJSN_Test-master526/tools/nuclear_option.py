"""Nuclear option: click el-select -> find teleported dropdown in body -> click option"""
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

# Navigate and find user
nav = SidebarNavigator(d)
nav._navigate_by_js_hash('#/system/user', 'u')
time.sleep(3)
up = UserManagePage(d)
up.wait_vue_stable()
up.click_reset_button(); time.sleep(0.5)
up.input_search_username("rbac_test_sys"); up.click_search_button(); time.sleep(2)
print("Found:", up.get_table_row_count())

# Click edit - opens dialog with role pre-selected (or not)
up.click_edit_user("rbac_test_sys")
time.sleep(3)
print("Edit open")

# Step 1: Click ANY el-select inside the dialog to open it AND focus it
d.execute_script("""
var dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
if (!dlg) { var ds = document.querySelectorAll('.el-dialog'); for (var i=0; i<ds.length; i++) { if (ds[i].offsetParent) { dlg = ds[i]; break; } } }
if (!dlg) return;
// Click the first el-select in the dialog
var sel = dlg.querySelector('.el-select__wrapper');
if (!sel) sel = dlg.querySelector('.el-select');
if (!sel) sel = dlg.querySelector('.el-input__wrapper');
if (!sel) sel = dlg.querySelector('input');
if (sel) {
    sel.scrollIntoView({block: 'center'});
    sel.focus();
    sel.click();
    // Also focus the input inside
    var inp = sel.querySelector('input');
    if (inp) { inp.focus(); setTimeout(function() { inp.click(); }, 300); }
}
""")
time.sleep(2)
print("Select opened + focused")

# Step 2: Use keyboard to filter and select in the dropdown
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

actions = ActionChains(d)
# Small pause then type role name
actions.pause(0.5).send_keys("RBAC-SYS-ONLY").pause(1).send_keys(Keys.ENTER).perform()
time.sleep(1)
print("Role selected via keyboard")

# Verify: re-read the selected value from the el-select
selected = d.execute_script("""
var dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
if (!dlg) return 'no_dialog';
var sel = dlg.querySelector('.el-select');
if (!sel) return 'no_select';
var input = sel.querySelector('input');
if (input) return input.value || '(empty)';
// Try reading from el-select internal state
var tag = sel.querySelector('.el-select__selected-item, .el-tag');
if (tag) return tag.textContent.trim();
return 'unknown';
""")
print("Current role value:", selected)

# Step 3: Click confirm in dialog
d.execute_script("""
var dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
if (!dlg) return;
var btns = dlg.querySelectorAll('button.el-button--primary');
for (var i=0; i<btns.length; i++) {
    var t = (btns[i].textContent || '').trim();
    if (t && t.indexOf('取消') === -1) { btns[i].click(); return; }
}
""")
time.sleep(3)
print("Saved")

# Step 4: Verify - open new window and login as rbac_test_sys
from base.browser_driver import BaseDriver as BD
b2 = BD()
d2 = b2.open_browser()
d2.maximize_window()
d2.get("https://aiwechatminidemo.cimc-digital.com/")
WebDriverWait(d2, 10).until(lambda x: x.execute_script("return document.readyState") == "complete")
time.sleep(2)

lp = LoginPage(d2)
lp.input_username("rbac_test_sys"); lp.input_password(PWD)
btns = d2.find_elements(By.XPATH, "//button[.//span[contains(.,'登')]]")
if btns: btns[0].click()
else: d2.execute_script("document.querySelector('.el-button--primary').click();")
try: WebDriverWait(d2, 15).until(lambda x: "#/login" not in (x.current_url or ""))
except: pass
lp.wait_vue_stable(); time.sleep(3)

menus = d2.execute_script("""
var m = [];
document.querySelectorAll('.el-menu > li.el-sub-menu > .el-sub-menu__title span')
    .forEach(function(s) { var t = (s.innerText || '').trim(); if (t) m.push(t); });
document.querySelectorAll('.el-menu > li.el-menu-item span')
    .forEach(function(s) { var t = (s.innerText || '').trim(); if (t) m.push(t); });
return m;
""")
print("SIDEBAR (%d): %s" % (len(menus), menus))

d.quit(); d2.quit()
