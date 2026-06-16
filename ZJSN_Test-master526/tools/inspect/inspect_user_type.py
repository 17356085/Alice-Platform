"""Debug: what values does the 用户类型 (userType) select field accept?"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.UserManagePage import UserManagePage

base = BaseDriver()
driver = None
try:
    driver = base.open_browser()
    ensure_logged_in(driver)

    nav = SidebarNavigator(driver)
    nav.navigate_to("系统管理", "用户管理")
    time.sleep(3)

    up = UserManagePage(driver)
    up.click_reset_button()
    up.click_add_user_button()
    time.sleep(2)

    # Open the 用户类型 dropdown to see options
    result = driver.execute_script("""
        var dlg = document.querySelector('.el-dialog');
        if (!dlg) return 'NO DIALOG';

        // Find form item with label "用户类型" or similar
        var items = dlg.querySelectorAll('.el-form-item');
        var target = null;
        items.forEach(function(item) {
            var label = item.querySelector('.el-form-item__label');
            if (label && label.innerText.indexOf('用户类型') !== -1) {
                target = item;
            }
        });
        if (!target) return 'NO userType ITEM';

        // Click the select to open dropdown
        var select = target.querySelector('.el-select');
        if (!select) return 'NO SELECT IN userType';
        select.querySelector('.el-select__wrapper, .el-select__selection').click();

        // Wait for options
        setTimeout(function() {}, 500);
        return 'opened';
    """)
    print(f"Click select: {result}")
    time.sleep(1.5)

    options = driver.execute_script("""
        var options = [];
        // Look for the active popper with select dropdown items
        var poppers = document.querySelectorAll('.el-popper');
        poppers.forEach(function(p) {
            p.querySelectorAll('.el-select-dropdown__item, li[class*="item"]').forEach(function(li) {
                var t = (li.innerText || '').trim();
                var val = li.getAttribute('value') || '';
                if (t) options.push({text: t, value: val});
            });
        });
        return options;
    """)
    print(f"UserType options: {options}")

    # Close dialog
    driver.execute_script("""
        var dlg = document.querySelector('.el-dialog');
        if (dlg) {
            var cancel = dlg.querySelector('.el-dialog__footer button:not(.el-button--primary)');
            if (cancel) cancel.click();
        }
    """)
    time.sleep(1)

finally:
    if driver:
        try: driver.quit()
        except: pass
