"""JS-based role assignment — bypasses Selenium click interception"""
import sys, time
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.UserManagePage import UserManagePage
from page.system_page.RoleManagePage import RoleManagePage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

mapping = [
    ('rbac_test_sys',   'RBAC-SYS-ONLY'),
    ('rbac_test_equip', 'RBAC-EQUIP-ONLY'),
    ('rbac_test_mix',   'RBAC-MIXED'),
    ('rbac_test_ro',    'RBAC-READONLY'),
]

for uname, rname in mapping:
    print('=== %s -> %s ===' % (uname, rname))

    # Search for user
    up.click_reset_button()
    time.sleep(0.5)
    up.input_search_username(uname)
    up.click_search_button()
    time.sleep(2)

    if up.get_table_row_count() == 0:
        print('  SKIP: user not found')
        continue

    # Click "更多" using JS (bypass ElementClickIntercepted)
    clicked = d.execute_script('''
        var username = arguments[0];
        var rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
        for (var i = 0; i < rows.length; i++) {
            var txt = (rows[i].textContent || '').trim();
            if (txt.indexOf(username) !== -1) {
                // Find the "更多" button in this row
                var btns = rows[i].querySelectorAll('button, .el-button, .el-dropdown-link');
                for (var j = 0; j < btns.length; j++) {
                    var bt = (btns[j].textContent || '').trim();
                    if (bt.indexOf('更多') !== -1 || bt === '...' || bt === '') {
                        btns[j].scrollIntoView({block: 'center'});
                        btns[j].click();
                        return 'clicked_more';
                    }
                }
                // Fallback: click last button in row
                var lastBtn = rows[i].querySelector('td:last-child button');
                if (lastBtn) {
                    lastBtn.scrollIntoView({block: 'center'});
                    lastBtn.click();
                    return 'clicked_last';
                }
            }
        }
        return 'not_found';
    ''', uname)
    print('  More button: %s' % clicked)
    time.sleep(1)

    # Click "分配角色" in the dropdown menu
    clicked2 = d.execute_script('''
        var items = document.querySelectorAll('.el-dropdown-menu__item, .el-popper li, .el-dropdown-menu li');
        for (var i = 0; i < items.length; i++) {
            var txt = (items[i].textContent || '').trim();
            if (txt.indexOf('分配角色') !== -1 || txt.indexOf('角色') !== -1) {
                items[i].click();
                return 'clicked_' + txt;
            }
        }
        // Try to find by visible dropdown
        var all = document.querySelectorAll('*');
        for (var j = 0; j < all.length; j++) {
            if (all[j].textContent && all[j].textContent.trim() === '分配角色' && all[j].offsetParent !== null) {
                all[j].click();
                return 'clicked_visible';
            }
        }
        return 'not_found_dropdown';
    ''')
    print('  Assign role: %s' % clicked2)
    time.sleep(2)

    # In the dialog, find and click the role checkbox
    clicked3 = d.execute_script('''
        var roleName = arguments[0];
        // Find the role dialog
        var dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
        if (!dlg) {
            var dialogs = document.querySelectorAll('.el-dialog');
            for (var i = 0; i < dialogs.length; i++) {
                if (dialogs[i].offsetParent !== null) { dlg = dialogs[i]; break; }
            }
        }
        if (!dlg) return 'no_dialog';

        // Find checkbox label containing role name
        var labels = dlg.querySelectorAll('.el-checkbox__label, .el-checkbox, label');
        for (var j = 0; j < labels.length; j++) {
            var t = (labels[j].textContent || '').trim();
            if (t.indexOf(roleName) !== -1) {
                // Click the checkbox inner
                var cb = labels[j].closest('.el-checkbox');
                if (cb) {
                    var inner = cb.querySelector('.el-checkbox__inner');
                    if (inner) { inner.click(); return 'checked'; }
                }
                labels[j].click();
                return 'clicked_label';
            }
        }
        return 'role_not_found_in_dialog';
    ''', rname)
    print('  Select role: %s' % clicked3)
    time.sleep(0.5)

    # Click confirm in dialog
    d.execute_script('''
        var dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
        if (!dlg) return;
        var btns = dlg.querySelectorAll('button.el-button--primary');
        for (var i = 0; i < btns.length; i++) {
            if ((btns[i].textContent || '').trim().indexOf('取消') === -1) {
                btns[i].click();
                return;
            }
        }
        // Fallback
        var footer = dlg.querySelector('.el-dialog__footer');
        if (footer) {
            var fb = footer.querySelector('button.el-button--primary');
            if (fb) fb.click();
        }
    ''')
    time.sleep(2)
    print('  Saved')

# Clear cache
print('\n=== Clear cache ===')
nav._navigate_by_js_hash('#/system/role', 'c')
time.sleep(3)
rp = RoleManagePage(d)
rp.wait_vue_stable()
rp.click_clear_cache()
time.sleep(1)
print('Cache cleared')

d.quit()
print('Done')
