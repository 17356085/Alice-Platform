"""通过 UI 为 RBAC 用户分配角色"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.UserManagePage import UserManagePage

PAIRS = [
    ("rbac_test_full",   "RBAC-全权限"),
    ("rbac_test_sys",    "RBAC-仅系统管理"),
    ("rbac_test_equip",  "RBAC-仅设备管理"),
    ("rbac_test_hr",     "RBAC-仅人员管理"),
    ("rbac_test_mix",    "RBAC-混合权限"),
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

    for username, role_name in PAIRS:
        print(f"\n{username} -> {role_name}", end=" ")

        # Search user
        up.click_reset_button()
        up.input_search_username(username)
        up.click_search_button()
        time.sleep(1.5)
        if up.get_table_row_count() == 0:
            print("NOT FOUND")
            continue

        # Click 分配角色
        up.click_assign_role_user(username)
        time.sleep(2.5)

        # Uncheck all, check target
        driver.execute_script(f"""
            var dlg = document.querySelector('.el-dialog');
            if (!dlg) return;
            // Uncheck all
            dlg.querySelectorAll('label.el-checkbox.is-checked').forEach(function(cb){{cb.click();}});
            setTimeout(function(){{}}, 300);
            // Check target
            dlg.querySelectorAll('label.el-checkbox').forEach(function(cb){{
                var t = (cb.innerText||'').trim();
                if(t.indexOf('{role_name}')!==-1 && !cb.classList.contains('is-checked')){{cb.click();}}
            }});
        """)
        time.sleep(1)

        # Confirm
        driver.execute_script("""
            var dlg = document.querySelector('.el-dialog');
            if (dlg) {
                var btn = dlg.querySelector('.el-dialog__footer button.el-button--primary');
                if (btn) btn.click();
            }
        """)
        time.sleep(1.5)

        # Check toast
        toast = driver.execute_script("""
            var t = document.querySelector('.el-message__content');
            return t ? t.innerText : '';
        """)
        print(toast or "(no toast)")
        time.sleep(1)

    print("\nDone!")

finally:
    if driver:
        try: base.close_browser()
        except: pass
