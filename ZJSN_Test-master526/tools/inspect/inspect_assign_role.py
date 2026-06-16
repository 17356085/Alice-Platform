"""Debug: assign a single role to rbac_test_full and verify"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.UserManagePage import UserManagePage

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

    # Search for rbac_test_full
    up.click_reset_button()
    up.input_search_username("rbac_test_full")
    up.click_search_button()
    time.sleep(2)
    print(f"Search results: {up.get_table_row_count()}")

    # Click 分配角色
    up.click_assign_role_user("rbac_test_full")
    time.sleep(3)

    # Debug: list what's in the dialog
    dlg_info = driver.execute_script("""
        var dlg = document.querySelector('.el-dialog');
        if (!dlg) return 'NO DIALOG';

        var checkboxes = dlg.querySelectorAll('label.el-checkbox');
        var result = [];
        checkboxes.forEach(function(cb) {
            var text = (cb.innerText || '').trim();
            var isChecked = cb.classList.contains('is-checked');
            if (text) result.push({text: text, checked: isChecked});
        });
        return result;
    """)
    import json
    print(f"\nRole checkboxes in dialog:")
    for cb in dlg_info:
        print(f"  [{'X' if cb['checked'] else ' '}] {cb['text']}")

    # Uncheck all first
    driver.execute_script("""
        var dlg = document.querySelector('.el-dialog');
        if(dlg) dlg.querySelectorAll('label.el-checkbox.is-checked').forEach(function(cb){cb.click();});
    """)
    time.sleep(0.5)

    # Check ONLY "RBAC-全权限"
    result = driver.execute_script("""
        var dlg = document.querySelector('.el-dialog');
        if(!dlg) return 'NO DIALOG';
        var checked = 0;
        dlg.querySelectorAll('label.el-checkbox').forEach(function(cb){
            var t = (cb.innerText||'').trim();
            if(t === 'RBAC-全权限') {
                if(!cb.classList.contains('is-checked')) {
                    cb.click();
                    checked++;
                }
            }
        });
        return 'Checked ' + checked + ' boxes for RBAC-全权限';
    """)
    print(f"\n{result}")

    # Verify check state
    dlg_info2 = driver.execute_script("""
        var dlg = document.querySelector('.el-dialog');
        if(!dlg) return 'NO DIALOG';
        var result = [];
        dlg.querySelectorAll('label.el-checkbox').forEach(function(cb){
            var t = (cb.innerText||'').trim();
            if(t === 'RBAC-全权限') result.push({text: t, checked: cb.classList.contains('is-checked')});
        });
        return result;
    """)
    print(f"Verify: {dlg_info2}")

    # Confirm
    driver.execute_script("""
        var dlg = document.querySelector('.el-dialog');
        if(dlg) {
            var btn = dlg.querySelector('.el-dialog__footer button.el-button--primary');
            if(btn) btn.click();
        }
    """)
    time.sleep(2)

    # Check toast
    toast = driver.execute_script("return document.querySelector('.el-message__content')?.innerText || '';")
    print(f"Toast: {toast}")

    # Verify via API
    verify = driver.execute_script("""
        return fetch('https://aiwechatminidemo.cimc-digital.com/api/system/user/list?pageNum=1&pageSize=20&username=rbac_test_full',{
            headers:{'Authorization':'Bearer '+JSON.parse(decodeURIComponent(document.cookie.split('authorized-token=')[1].split(';')[0])).accessToken}
        }).then(r=>r.json());
    """)
    u = verify.get('data',{}).get('records',[{}])[0]
    print(f"Verify after: roleIds={u.get('roleIds',[])}")

    # Now log in as rbac_test_full and check sidebar
    driver.get("https://aiwechatminidemo.cimc-digital.com/")
    time.sleep(3)
    from page.system_page.LoginPage import LoginPage
    lp = LoginPage(driver)
    if lp.is_login_page():
        lp.input_username("rbac_test_full")
        lp.input_password("Ajyl@2026")
        btns = driver.find_elements("xpath", "//button[.//span[contains(.,'登')]]")
        if btns: btns[0].click()
        time.sleep(4)

    # Check sidebar
    menus = driver.execute_script("""
        var m=[];
        document.querySelectorAll('.el-menu > li').forEach(function(li){
            var title = li.querySelector('.el-sub-menu__title span, .el-menu-item span');
            if(title) m.push(title.innerText.trim());
        });
        return m;
    """)
    print(f"Sidebar after login: {menus}")

finally:
    if driver:
        try: base.close_browser()
        except: pass
