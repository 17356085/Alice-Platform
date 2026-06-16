"""UI-based batch user creation for RBAC testing (uses UserManagePage)"""
import sys, time
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.UserManagePage import UserManagePage
from page.system_page.RoleManagePage import RoleManagePage

PWD = "Ajyl@2026"

USERS = [
    ("rbac_test_full",   "RBAC-Full-Test",    "RBAC-ALL"),
    ("rbac_test_sys",    "RBAC-SYS-Test",     "RBAC-SYS-ONLY"),
    ("rbac_test_equip",  "RBAC-EQUIP-Test",   "RBAC-EQUIP-ONLY"),
    ("rbac_test_hr",     "RBAC-HR-Test",      "RBAC-HR-ONLY"),
    ("rbac_test_mix",    "RBAC-MIXED-Test",   "RBAC-MIXED"),
    ("rbac_test_none",   "RBAC-NONE-Test",    "RBAC-NONE"),
]

base = BaseDriver()
d = base.open_browser()
d.maximize_window()
ensure_logged_in(d)
time.sleep(2)

nav = SidebarNavigator(d)
nav._navigate_by_js_hash('#/system/user', 'user_mgmt')
time.sleep(3)
up = UserManagePage(d)
up.wait_vue_stable()

for username, name, role_name in USERS:
    print("\n--- Creating: %s -> %s ---" % (username, role_name))

    # Delete existing
    up.click_reset_button()
    time.sleep(0.5)
    up.input_search_username(username)
    up.click_search_button()
    time.sleep(1.5)
    if up.get_table_row_count() > 0:
        print("  Deleting existing...")
        try:
            up.click_more_user(username)
            up.click_more_delete()
            up.confirm_delete_message_box()
            time.sleep(1)
        except Exception as e:
            print("  Delete failed: %s" % e)
    else:
        print("  No existing user")

    # Create new
    up.click_reset_button()
    time.sleep(0.5)
    up.click_add_user_button()
    time.sleep(2)

    try:
        up.input_dialog_input("用户名称", username)  # 用户名称
        up.input_dialog_input("姓名", name)                   # 姓名
        up.input_password_in_dialog(PWD)
        up.input_dialog_input("手机号", "13800000001")   # 手机号
        up.select_role_in_dialog(role_name)
        print("  Form filled")
    except Exception as e:
        print("  Form error: %s" % e)

    up.click_dialog_confirm()
    time.sleep(2)
    print("  Created")

# Clear cache
print("\n--- Clearing cache ---")
nav._navigate_by_js_hash('#/system/role', 'cache')
time.sleep(3)
rp = RoleManagePage(d)
rp.wait_vue_stable()
rp.click_clear_cache()
print("Cache cleared")

d.quit()
print("\nDone! %d users created" % len(USERS))
