"""Inspect permission dialog structure AND save HTML for analysis"""
import sys, time
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.RoleManagePage import RoleManagePage

base = BaseDriver()
d = base.open_browser()
d.maximize_window()
ensure_logged_in(d)
time.sleep(2)

nav = SidebarNavigator(d)
nav._navigate_by_js_hash('#/system/role', 'role')
time.sleep(3)
rp = RoleManagePage(d)
rp.wait_vue_stable()

# Search for RBAC-SYS-ONLY and open permission dialog
rp.click_reset()
time.sleep(0.5)
rp.input_role_name("RBAC-SYS-ONLY")
rp.click_search()
rp.wait_table_ready(timeout=8)
print("Found:", rp.get_table_row_count())

rp.click_permission_by_role_name("RBAC-SYS-ONLY")
time.sleep(2)

# Switch to PC tab
ok = rp.click_permission_tab_pc()
print("PC tab:", ok)
time.sleep(1)

# Dump the permission tree structure
info = d.execute_script("""
    var dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
    if (!dlg) {
        var ds = document.querySelectorAll('.el-dialog');
        for (var i = 0; i < ds.length; i++) {
            if (ds[i].offsetParent !== null) { dlg = ds[i]; break; }
        }
    }
    if (!dlg) return JSON.stringify({error: 'no_dialog'});

    // Find ALL elements with perm-group class
    var groups = dlg.querySelectorAll('.perm-group');
    var result = {totalGroups: groups.length, groups: []};

    for (var i = 0; i < Math.min(groups.length, 5); i++) {
        var g = groups[i];
        var name = g.querySelector('.perm-group__name');
        var arrow = g.querySelector('.perm-group__arrow');
        var checkboxes = g.querySelectorAll('.el-checkbox');
        var groupInfo = {
            index: i,
            name: name ? name.textContent.trim() : '(no name)',
            hasArrow: !!arrow,
            checkboxCount: checkboxes.length,
            checkboxes: []
        };
        for (var j = 0; j < Math.min(checkboxes.length, 3); j++) {
            var cb = checkboxes[j];
            var label = cb.querySelector('.el-checkbox__label');
            var input = cb.querySelector('input[type="checkbox"]');
            var isChecked = cb.classList.contains('is-checked');
            groupInfo.checkboxes.push({
                label: label ? label.textContent.trim() : '(no label)',
                value: input ? input.value : '?',
                checked: isChecked
            });
        }
        result.groups.push(groupInfo);
    }

    // Also check if there's an el-tree instead
    var tree = dlg.querySelector('.el-tree, .el-tree--highlight-current');
    if (tree) {
        var nodes = tree.querySelectorAll('.el-tree-node');
        result.elTree = {nodeCount: nodes.length};
    }

    // Check for el-tree-select
    var treeSelect = dlg.querySelector('.el-tree-select');
    if (treeSelect) {
        result.hasTreeSelect = true;
    }

    // Also dump the tab pane content HTML (first 2000 chars)
    var activePane = dlg.querySelector('.el-tab-pane.is-active, .el-tab-pane[style*=""]');
    if (activePane) {
        result.activePaneHTML = activePane.innerHTML.substring(0, 2000);
    }

    return JSON.stringify(result);
""")
print("Permission tree structure:")
print(info)

# Save to file for analysis
with open("tools/perm_dialog_dump.json", "w", encoding="utf-8") as f:
    f.write(info)

rp.click_permission_cancel()
d.quit()
print("Done - saved to tools/perm_dialog_dump.json")
