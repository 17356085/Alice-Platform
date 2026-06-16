"""JS-based role assignment V2 — use edit dialog to change role"""
import sys, time
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.UserManagePage import UserManagePage
from page.system_page.RoleManagePage import RoleManagePage

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

    # Search
    up.click_reset_button(); time.sleep(0.5)
    up.input_search_username(uname); up.click_search_button(); time.sleep(2)
    if up.get_table_row_count() == 0:
        print('  SKIP: not found'); continue

    # Click "编辑" button directly (opens edit dialog with role selector)
    clicked = d.execute_script('''
        var username = arguments[0];
        var rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
        for (var i = 0; i < rows.length; i++) {
            var txt = (rows[i].textContent || '').trim();
            if (txt.indexOf(username) !== -1) {
                // Find "编辑" button in the action column
                var btns = rows[i].querySelectorAll('td:last-child button, td:last-child span');
                for (var j = 0; j < btns.length; j++) {
                    var t = (btns[j].textContent || '').trim();
                    if (t === '编辑' || t.indexOf('编辑') !== -1) {
                        btns[j].scrollIntoView({block: 'center'});
                        btns[j].click();
                        return 'clicked_edit';
                    }
                }
            }
        }
        return 'not_found';
    ''', uname)
    print('  Edit: %s' % clicked)
    time.sleep(2)

    # In the edit dialog, select the role
    result = d.execute_script('''
        var roleName = arguments[0];
        var dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
        if (!dlg) {
            var ds = document.querySelectorAll('.el-dialog');
            for (var i = 0; i < ds.length; i++) {
                if (ds[i].offsetParent !== null) { dlg = ds[i]; break; }
            }
        }
        if (!dlg) return 'no_dialog';

        // Method 1: Find role select and click to open dropdown
        var selects = dlg.querySelectorAll('.el-select');
        var roleSelect = null;
        for (var s = 0; s < selects.length; s++) {
            // Check if this select is near a "角色" label
            var formItem = selects[s].closest('.el-form-item');
            if (formItem) {
                var label = formItem.querySelector('.el-form-item__label');
                if (label && (label.textContent || '').indexOf('角色') !== -1) {
                    roleSelect = selects[s];
                    break;
                }
            }
        }
        if (!roleSelect) {
            // Fallback: try all selects
            for (var s = 0; s < selects.length; s++) {
                if (selects[s].offsetParent !== null) {
                    roleSelect = selects[s];
                    break;
                }
            }
        }
        if (!roleSelect) return 'no_role_select';

        // Open the dropdown
        var wrapper = roleSelect.querySelector('.el-select__wrapper, .select-trigger');
        if (wrapper) wrapper.click();
        else roleSelect.click();

        return 'opened_select';
    ''', rname)
    print('  Open select: %s' % result)
    time.sleep(1)

    # Select the role from dropdown
    result2 = d.execute_script('''
        var roleName = arguments[0];
        // Find visible dropdown options
        var options = document.querySelectorAll('.el-select-dropdown__item:not(.is-disabled), .el-select-dropdown__item');
        var visible = [];
        for (var i = 0; i < options.length; i++) {
            if (options[i].offsetParent !== null) { visible.push(options[i]); }
        }
        // Try visible first, then all
        var candidates = visible.length > 0 ? visible : options;

        for (var j = 0; j < candidates.length; j++) {
            var t = (candidates[j].textContent || '').trim();
            if (t.indexOf(roleName) !== -1) {
                candidates[j].scrollIntoView({block: 'center'});
                candidates[j].click();
                return 'selected_' + t.substring(0, 30);
            }
        }
        return 'option_not_found_in_' + candidates.length + '_items';
    ''', rname)
    print('  Select role: %s' % result2)
    time.sleep(0.5)

    # Click confirm
    d.execute_script('''
        var dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
        if (!dlg) return;
        var btns = dlg.querySelectorAll('button.el-button--primary');
        for (var i = 0; i < btns.length; i++) {
            var t = (btns[i].textContent || '').trim();
            if (t.indexOf('取消') === -1 && t !== '') {
                btns[i].click();
                return;
            }
        }
    ''')
    time.sleep(2)
    print('  Saved')

# Clear cache
print('\n=== Clear cache ===')
nav._navigate_by_js_hash('#/system/role', 'c'); time.sleep(3)
rp = RoleManagePage(d); rp.wait_vue_stable()
rp.click_clear_cache(); time.sleep(1)
print('Done')
d.quit()
