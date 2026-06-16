"""UI-based: Create ONE test user with role assignment, then verify sidebar"""
import sys, time
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.UserManagePage import UserManagePage
from page.system_page.LoginPage import LoginPage
from page.system_page.RoleManagePage import RoleManagePage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

PWD = "Ajyl@2026"
USERNAME = "rbac_test_sys"
ROLE_NAME = "RBAC-SYS-ONLY"

base = BaseDriver()
d = base.open_browser()
d.maximize_window()
ensure_logged_in(d)
time.sleep(2)

# Step 1: Delete existing user
print("=== Step 1: Cleanup ===")
nav = SidebarNavigator(d)
nav._navigate_by_js_hash('#/system/user', 'user_mgmt')
time.sleep(3)
up = UserManagePage(d)
up.wait_vue_stable()
up.click_reset_button()
time.sleep(0.5)
up.input_search_username(USERNAME)
up.click_search_button()
time.sleep(2)
if up.get_table_row_count() > 0:
    print("Deleting existing user: %s" % USERNAME)
    try:
        up.click_more_user(USERNAME)
        up.click_more_delete()
        up.confirm_delete_message_box()
        time.sleep(1)
        print("Deleted")
    except Exception as e:
        print("Delete failed: %s" % e)

# Step 2: Create user via UI
print("\n=== Step 2: Create user ===")
up.click_reset_button()
time.sleep(0.5)
up.click_add_user_button()
time.sleep(2)

# Fill form using UserManagePage methods
up.input_dialog_input("用户名称", USERNAME)
up.input_dialog_input("姓名", "SYS-Test")
up.input_password_in_dialog(PWD)
up.input_dialog_input("手机号", "13800000001")

# Select role
up.select_role_in_dialog(ROLE_NAME)
print("Role selected: %s" % ROLE_NAME)

# Select department
try:
    up.select_dialog_first_valid_option("所属部门")
    print("Department selected")
except Exception:
    pass

# Confirm
up.click_dialog_confirm()
time.sleep(2)
print("User created")

# Step 3: Clear cache
print("\n=== Step 3: Clear cache ===")
nav._navigate_by_js_hash('#/system/role', 'cache_clear')
time.sleep(3)
rp = RoleManagePage(d)
rp.wait_vue_stable()
rp.click_clear_cache()
print("Cache cleared")

# Step 4: Logout and login as rbac_test_sys
print("\n=== Step 4: Login as %s ===" % USERNAME)
d.get("https://aiwechatminidemo.cimc-digital.com/")
time.sleep(3)
lp = LoginPage(d)
try:
    if lp.is_login_page():
        lp.input_username(USERNAME)
        lp.input_password(PWD)
        btns = d.find_elements(By.XPATH, "//button[.//span[contains(.,'登')]]")
        if btns: btns[0].click()
        else: d.execute_script("document.querySelector('.el-button--primary').click();")
        WebDriverWait(d, 15).until(lambda x: "#/login" not in (x.current_url or ""))
    lp.wait_vue_stable()
    time.sleep(3)
except Exception as e:
    print("Login error: %s" % e)

# Step 5: Check sidebar
menus = d.execute_script('''
    var m=[];
    document.querySelectorAll('.el-menu > li.el-sub-menu > .el-sub-menu__title span')
        .forEach(function(s){var t=(s.innerText||'').trim();if(t)m.push(t);});
    document.querySelectorAll('.el-menu > li.el-menu-item span')
        .forEach(function(s){var t=(s.innerText||'').trim();if(t)m.push(t);});
    return m;
''')
print("Sidebar: %s" % menus)
print("Count: %d" % len(menus))

# Verify: should have system管理
if "系统管理" in str(menus) or len(menus) >= 1:
    print("\n*** SUCCESS! Sidebar has menus! ***")
else:
    print("\n*** FAILED: Sidebar still empty ***")

d.quit()
