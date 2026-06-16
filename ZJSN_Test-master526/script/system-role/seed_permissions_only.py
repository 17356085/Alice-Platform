"""仅为角色配置页面权限 — 用户说他已经手动分配了角色"""
import sys, time
sys.path.insert(0, 'd:/Desktop/WorkStudy/ZJSN_Test-master526')

from selenium.webdriver.common.by import By
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_role_page.RoleManagePage import RoleManagePage

CONFIG = {
    "RBAC-全权限":    "__ALL__",
    "RBAC-仅系统管理": ["系统管理"],
    "RBAC-仅设备管理": ["设备管理"],
    "RBAC-仅人员管理": ["人员管理"],
    "RBAC-混合权限":   ["用户管理","角色管理","设备台账","客户管理"],
}

base = BaseDriver()
driver = None
try:
    driver = base.open_browser()
    driver.maximize_window()
    ensure_logged_in(driver)
    nav = SidebarNavigator(driver)
    nav.navigate_to("系统管理", "角色管理")
    time.sleep(3)
    rp = RoleManagePage(driver)

    for role_name, perm_groups in CONFIG.items():
        print(f"\n{role_name}:")

        # Search
        rp.click_reset()
        rp.input_role_name(role_name)
        rp.click_search()
        time.sleep(2)
        if rp.get_table_row_count() == 0:
            print(f"  NOT FOUND")
            continue

        # Click 权限
        rp.click_permission_by_role_name(role_name)
        time.sleep(2.5)

        # PC Tab
        rp.click_permission_tab_pc()
        time.sleep(2)

        # Expand all groups by clicking headers
        driver.execute_script("""
            document.querySelectorAll('.perm-group__header, .perm-group__arrow').forEach(function(el){
                try{ el.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true})); }catch(e){}
            });
        """)
        time.sleep(2)

        # Debug: count visible vs total checkboxes
        debug_counts = driver.execute_script("""
            var p=document.querySelector('.el-tab-pane.is-active');
            if(!p) return {err:'no pane'};
            var total=p.querySelectorAll('label.el-checkbox').length;
            var inputs=p.querySelectorAll('.el-checkbox__original').length;
            return {totalCheckboxes: total, totalInputs: inputs};
        """)
        print(f"  DEBUG: {debug_counts}")

        # Click checkboxes
        if perm_groups == "__ALL__":
            cnt = driver.execute_script("""
                var c=0,p=document.querySelector('.el-tab-pane.is-active');
                if(p) p.querySelectorAll('label.el-checkbox:not(.is-checked)').forEach(function(cb){
                    var inp=cb.querySelector('.el-checkbox__original');
                    if(inp){inp.click();c++;}
                });
                return c;
            """)
            print(f"  ALL: {cnt} checked")
        else:
            for gn in perm_groups:
                cnt = driver.execute_script(f"""
                    var c=0,p=document.querySelector('.el-tab-pane.is-active');
                    if(!p) return 0;
                    p.querySelectorAll('div.perm-group').forEach(function(g){{
                        var n=g.querySelector('.perm-group__name');
                        if(!n) return;
                        if(((n.innerText||'').trim()).indexOf('{gn}')===-1) return;
                        g.querySelectorAll('label.el-checkbox:not(.is-checked)').forEach(function(cb){{
                            var inp=cb.querySelector('.el-checkbox__original');
                            if(inp){{inp.click();c++;}}
                        }});
                    }});
                    return c;
                """)
                print(f"  {gn}: {cnt} checked")
                time.sleep(0.5)

        # Save
        rp.click_permission_confirm()
        t = rp.wait_for_toast_text(8)
        print(f"  Saved: {t}")
        time.sleep(1.5)

    print("\nDone! Permissions configured.")

finally:
    if driver:
        try: base.close_browser()
        except: pass
