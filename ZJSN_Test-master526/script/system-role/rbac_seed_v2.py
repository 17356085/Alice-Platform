"""RBAC数据种子 — 纯 UI 创建角色+权限+用户（复用已验证的 PO 方法）

从第一个 test_run 的 rbac_setup fixture 提取，独立运行
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_role_page.RoleManagePage import RoleManagePage
from page.system_page.UserManagePage import UserManagePage

PWD = "Ajyl@2026"

TEST_ROLES = [
    {"name": "RBAC-全权限",     "code": "rbac_full",    "order": 90, "desc": "RBAC-全权限",     "perm": "__ALL__"},
    {"name": "RBAC-仅系统管理",  "code": "rbac_sys",     "order": 91, "desc": "RBAC-仅系统管理",  "perm": ["系统管理"]},
    {"name": "RBAC-仅设备管理",  "code": "rbac_equip",   "order": 92, "desc": "RBAC-仅设备管理",  "perm": ["设备管理"]},
    {"name": "RBAC-仅人员管理",  "code": "rbac_hr",      "order": 93, "desc": "RBAC-仅人员管理",  "perm": ["人员管理"]},
    {"name": "RBAC-混合权限",    "code": "rbac_mix",     "order": 94, "desc": "RBAC-混合权限",
     "perm": ["用户管理","角色管理","设备台账","客户管理"]},
    {"name": "RBAC-零权限",     "code": "rbac_none",    "order": 95, "desc": "RBAC-零权限",     "perm": []},
    {"name": "RBAC-只读",       "code": "rbac_readonly","order": 96, "desc": "RBAC-只读",       "perm": "__ALL__"},
]

TEST_USERS = [
    ("rbac_test_full",   "RBAC全权限测试",   "rbac_full"),
    ("rbac_test_sys",    "RBAC系统管理测试", "rbac_sys"),
    ("rbac_test_equip",  "RBAC设备管理测试", "rbac_equip"),
    ("rbac_test_hr",     "RBAC人员管理测试", "rbac_hr"),
    ("rbac_test_mix",    "RBAC混合权限测试", "rbac_mix"),
    ("rbac_test_none",   "RBAC零权限测试",   "rbac_none"),
    ("rbac_test_ro",     "RBAC只读权限测试", "rbac_readonly"),
]

def step(text):
    print(f"  -> {text}")

def search_role(rp, name):
    rp.click_reset()
    rp.input_role_name(name)
    rp.click_search()
    time.sleep(2)

def search_user(up, username):
    up.click_reset_button()
    up.input_search_username(username)
    up.click_search_button()
    time.sleep(2)

def expand_all_groups(driver):
    """在权限弹窗中展开所有 perm-group"""
    driver.execute_script("""
        // Try perm-group arrows first
        var arrows = document.querySelectorAll('.perm-group__arrow, .perm-group__header i');
        arrows.forEach(function(a) {
            try { a.click(); } catch(e) {}
        });
        // Also try any el-icon in the pane
        setTimeout(function() {}, 500);
    """)
    time.sleep(1.5)
    # Verify by checking if checkboxes are now visible
    cnt = driver.execute_script("""
        var p = document.querySelector('.el-tab-pane.is-active');
        if (!p) return -1;
        return p.querySelectorAll('label.el-checkbox').length;
    """)
    return cnt

def check_all_checkboxes(driver):
    """勾选当前tab-pane中所有未勾选的checkbox"""
    return driver.execute_script("""
        var c=0,p=document.querySelector('.el-tab-pane.is-active');
        if(!p) return 0;
        p.querySelectorAll('label.el-checkbox:not(.is-checked)').forEach(function(cb){cb.click();c++;});
        return c;
    """)

def check_group(driver, group_name):
    """勾选指定权限分类的所有checkbox"""
    return driver.execute_script("""
        var c=0,p=document.querySelector('.el-tab-pane.is-active');
        if(!p) return 0;
        p.querySelectorAll('div.perm-group').forEach(function(g){
            var n=g.querySelector('.perm-group__name');
            if(!n) return;
            if(((n.innerText||'').trim()).indexOf('{g}')===-1) return;
            // try header checkbox first
            var hcb=g.querySelector('.perm-group__header label.el-checkbox:not(.is-checked)');
            if(hcb){hcb.click();c++;}
            g.querySelectorAll('div.perm-group__body label.el-checkbox:not(.is-checked)').forEach(function(cb){cb.click();c++;});
        });
        return c;
    """.replace('{g}', group_name))

def main():
    base = BaseDriver()
    driver = None
    try:
        driver = base.open_browser()
        driver.maximize_window()
        ensure_logged_in(driver)
        nav = SidebarNavigator(driver)

        # ── Create Roles ──
        print("\n" + "=" * 60)
        print("Phase 1: Create Roles (UI)")
        nav.navigate_to("系统管理", "角色管理")
        time.sleep(3)
        rp = RoleManagePage(driver)

        for rd in TEST_ROLES:
            step(f"Role: {rd['name']} ({rd['code']})")
            search_role(rp, rd['name'])
            if rp.get_table_row_count() > 0:
                step(f"  Exists, skip")
                continue

            rp.click_add()
            rp.input_dialog_role_name(rd['name'])
            rp.input_dialog_role_code(rd['code'])
            rp.input_dialog_order(rd['order'])
            rp.input_dialog_remark(rd['desc'])
            rp.click_dialog_confirm()
            t = rp.wait_for_toast_text(8)
            step(f"  Created: {t}")
            time.sleep(1)

        # ── Assign Permissions ──
        print("\n" + "=" * 60)
        print("Phase 2: Assign Permissions (UI)")

        for rd in TEST_ROLES:
            step(f"Permissions: {rd['name']}")
            search_role(rp, rd['name'])
            if rp.get_table_row_count() == 0:
                step(f"  Role not found, skip")
                continue

            rp.click_permission_by_role_name(rd['name'])
            time.sleep(2.5)

            # Switch to PC tab
            rp.click_permission_tab_pc()
            time.sleep(2)

            # Expand all groups
            total_cb = expand_all_groups(driver)
            step(f"  Checkboxes visible: {total_cb}")

            if rd['perm'] == "__ALL__":
                cnt = check_all_checkboxes(driver)
                step(f"  All checked: {cnt}")
            elif rd['perm']:
                for gn in rd['perm']:
                    cnt = check_group(driver, gn)
                    step(f"  {gn}: {cnt} checked")
                    time.sleep(0.5)

            rp.click_permission_confirm()
            t = rp.wait_for_toast_text(8)
            step(f"  Saved: {t}")
            time.sleep(1.5)

        # ── Create Users ──
        print("\n" + "=" * 60)
        print("Phase 3: Create Users (UI)")
        nav.navigate_to("系统管理", "用户管理")
        time.sleep(3)
        up = UserManagePage(driver)

        for username, name, role_code in TEST_USERS:
            step(f"User: {username}")
            search_user(up, username)
            if up.get_table_row_count() > 0:
                step(f"  Exists, skip")
                continue

            role_name = None
            for rd in TEST_ROLES:
                if rd['code'] == role_code:
                    role_name = rd['name']
                    break

            up.click_reset_button()
            up.click_add_user_button()
            up.input_dialog_input("用户名", username)
            up.input_dialog_input("姓名", name)
            up.input_password_in_dialog(PWD)
            try:
                up.select_dialog_option_by_text("部门", "人力行政部")
            except:
                try:
                    up.select_dialog_first_valid_option("部门")
                except:
                    step("  WARN: dept selection failed")
            if role_name:
                try:
                    up.select_dialog_option_by_text("角色", role_name)
                except:
                    try:
                        up.select_dialog_first_valid_option("角色")
                    except:
                        step("  WARN: role selection failed")
            try:
                up.input_dialog_input("手机号", "138" + str(int(time.time()))[-8:])
            except:
                pass
            up.click_dialog_confirm()
            t = up.get_toast_text(8)
            step(f"  Created: {t}")
            time.sleep(1)

        # ── Assign Roles to Users ──
        print("\n" + "=" * 60)
        print("Phase 4: Assign Roles to Users")
        nav.navigate_to("系统管理", "用户管理")
        time.sleep(3)

        for username, name, role_code in TEST_USERS:
            role_name = None
            for rd in TEST_ROLES:
                if rd['code'] == role_code:
                    role_name = rd['name']
                    break
            if not role_name:
                continue

            step(f"Assign role '{role_name}' to {username}")
            search_user(up, username)
            if up.get_table_row_count() == 0:
                step(f"  User not found")
                continue

            up.click_assign_role_user(username)
            time.sleep(2.5)

            # Uncheck all, then check target
            driver.execute_script("""
                var dlg=document.querySelector('.el-dialog');
                if(dlg){
                    dlg.querySelectorAll('label.el-checkbox.is-checked').forEach(function(cb){cb.click();});
                    dlg.querySelectorAll('label.el-checkbox').forEach(function(cb){
                        var t=(cb.innerText||'').trim();
                        if(t.indexOf('{r}')!==-1){if(!cb.classList.contains('is-checked'))cb.click();}
                    });
                }
            """.replace('{r}', role_name))
            time.sleep(1)

            # Confirm
            driver.execute_script("""
                var dlg=document.querySelector('.el-dialog');
                if(dlg){var b=dlg.querySelector('.el-dialog__footer button.el-button--primary');if(b)b.click();}
            """)
            t = up.get_toast_text(6)
            step(f"  Result: {t}")
            time.sleep(1)

        print(f"\nDone! {len(TEST_ROLES)} roles, {len(TEST_USERS)} users created/verified.")

    finally:
        if driver:
            try: base.close_browser()
            except: pass

if __name__ == '__main__':
    main()
