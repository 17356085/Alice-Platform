"""快速创建 RBAC 测试用户 — 使用 PO 的 _add_user 方法（已验证）"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.UserManagePage import UserManagePage
from selenium.webdriver.common.by import By

PWD = "Ajyl@2026"

PAIRS = [
    ("rbac_test_full",   "RBAC全权限测试",   "RBAC-全权限"),
    ("rbac_test_sys",    "RBAC系统管理测试", "RBAC-仅系统管理"),
    ("rbac_test_equip",  "RBAC设备管理测试", "RBAC-仅设备管理"),
    ("rbac_test_hr",     "RBAC人员管理测试", "RBAC-仅人员管理"),
]

base = BaseDriver()
driver = None
try:
    driver = base.open_browser()
    driver.maximize_window()
    ensure_logged_in(driver)
    nav = SidebarNavigator(driver)
    nav.navigate_to("系统管理", "用户管理")
    time.sleep(3)
    up = UserManagePage(driver)

    for username, name, role_name in PAIRS:
        print(f"\nCreating {username} ({name}) -> {role_name}")

        # Check if exists
        up.click_reset_button()
        up.input_search_username(username)
        up.click_search_button()
        time.sleep(1.5)
        if up.get_table_row_count() > 0:
            print(f"  EXISTS - skip")
            continue

        # Open add dialog
        up.click_reset_button()
        up.click_add_user_button()
        up.input_dialog_input("用户名", username)
        up.input_dialog_input("姓名", name)
        up.input_password_in_dialog(PWD)

        # Select department via the standard PO method
        print("  Selecting department...")
        try:
            up.select_dialog_option_by_text("部门", "人力行政部")
            print("  OK department selected")
        except Exception as e:
            print(f"  Dept select failed: {e}")

        # Select role
        if role_name:
            try:
                up.select_dialog_option_by_text("角色", role_name)
                print(f"  OK role '{role_name}' selected")
            except Exception as e:
                print(f"  Role select failed: {e}")

        # Phone
        try:
            up.input_dialog_input("手机号", "138" + str(int(time.time()))[-8:])
        except: pass

        # Submit
        up.click_dialog_confirm()
        toast = ""
        for _ in range(20):
            try:
                el = driver.find_element(By.CSS_SELECTOR, ".el-message__content")
                toast = el.text
                if toast: break
            except: pass
            time.sleep(0.5)

        if toast:
            print(f"  OK: {toast}")
        else:
            err = driver.execute_script("""
                var e = document.querySelector('.el-form-item__error');
                return e ? e.innerText : 'no error';
            """)
            print(f"  FAIL: {err}")
            try: up.click_dialog_cancel()
            except: pass

        time.sleep(1)

    print("\nDone!")

finally:
    if driver:
        try: base.close_browser()
        except: pass
