"""Final: extract permission dialog structure using correct selectors (checkbox + expandable sections)"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.RoleManagePage import RoleManagePage

OUT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def save(data, name):
    path = os.path.join(OUT_DIR, name)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path

def main():
    base = BaseDriver()
    driver = None
    try:
        driver = base.open_browser()
        ensure_logged_in(driver)

        page = RoleManagePage(driver)
        nav = SidebarNavigator(driver)
        nav.navigate_to("系统管理", "角色管理")
        time.sleep(4)

        # Use a role with many permissions — "人员培训管理员" has substantial permissions
        target = "人员培训管理员"
        print(f"Opening permission dialog for: {target}")
        page.click_permission_by_role_name(target)
        time.sleep(4)

        # === TAB 1: PC操作权限 (active by default) ===
        print("\n=== Extracting PC操作权限 tab ===")
        pc_data = driver.execute_script(r"""
        function T(el) { if (!el) return ''; return (el.innerText || el.textContent || '').trim(); }
        function safeCls(el) { try { return (el.className||'').toString(); } catch(e) { return ''; } }

        var result = {};

        // Find the active tab pane within the visible dialog
        var panes = document.querySelectorAll('.el-tab-pane');
        var activePane = null;
        for (var i = 0; i < panes.length; i++) {
            if (panes[i].classList.contains('is-active')) { activePane = panes[i]; break; }
        }
        if (!activePane) {
            // fallback: find any el-tab-pane inside a visible dialog
            var dialogs = document.querySelectorAll('.el-dialog');
            for (var d = 0; d < dialogs.length; d++) {
                if (dialogs[d].offsetWidth > 0) {
                    var ps = dialogs[d].querySelectorAll('.el-tab-pane');
                    for (var p = 0; p < ps.length; p++) {
                        if (ps[p].offsetHeight > 0) { activePane = ps[p]; break; }
                    }
                    if (activePane) break;
                }
            }
        }
        if (!activePane) { result.error = 'NO_ACTIVE_PANE'; return result; }

        result.paneHTML_sample = activePane.innerHTML.substring(0, 3000);

        // Extract ALL checkboxes in the active pane
        var checkboxes = [];
        activePane.querySelectorAll('label.el-checkbox').forEach(function(cb, i) {
            var isChecked = cb.classList.contains('is-checked');
            var isIndeterminate = cb.classList.contains('is-indeterminate');
            var span = cb.querySelector('.el-checkbox__label');
            var text = span ? T(span) : T(cb);

            // Determine nesting level by checking parent hierarchy
            var depth = 0;
            var parent = cb.closest('li, div[class]');
            // Try to find depth from nested lists or indentation
            var listAncestors = [];
            var p = cb.parentElement;
            while (p && p !== activePane) {
                if (p.tagName === 'UL' || p.tagName === 'OL') listAncestors.push(p);
                p = p.parentElement;
            }
            depth = listAncestors.length;

            checkboxes.push({
                index: i,
                text: text,
                depth: depth,
                checked: isChecked,
                indeterminate: isIndeterminate
            });
        });
        result.checkboxes = checkboxes;
        result.checkboxCount = checkboxes.length;

        // Extract all expandable rows (with arrow icons)
        var expandables = [];
        activePane.querySelectorAll('.el-icon-arrow-right, .el-icon-right, [class*="arrow-right"]').forEach(function(icon, i) {
            var row = icon.closest('div, li, tr');
            var text = row ? T(row) : '';
            expandables.push({index: i, text: text.substring(0, 80), parentClass: safeCls(row).substring(0, 60)});
        });
        result.expandableCount = expandables.length;
        result.expandables = expandables.slice(0, 10);

        // Get all text content organized by sections
        var sections = [];
        // Look for section headers (bold text, category labels)
        activePane.querySelectorAll('.el-checkbox-group, [class*="category"], [class*="section"], [class*="group"]').forEach(function(g) {
            sections.push({class: safeCls(g).substring(0, 60), text: T(g).substring(0, 200)});
        });
        result.sections = sections;

        // Extract unique structural classes
        var classCounts = {};
        activePane.querySelectorAll('[class]').forEach(function(el) {
            var cls = safeCls(el).split(' ').filter(function(c) { return c.indexOf('el-') === 0; });
            cls.forEach(function(c) { classCounts[c] = (classCounts[c] || 0) + 1; });
        });
        result.elClassCounts = classCounts;

        return result;
        """)

        path = save(pc_data, 'perm_tab_pc.json')
        print(f"Saved: {path}")
        print(f"Checkboxes: {pc_data.get('checkboxCount',0)}")
        print(f"Expandable arrows: {pc_data.get('expandableCount',0)}")
        print(f"El-* classes found: {pc_data.get('elClassCounts',{})}")

        # Show first 20 checkboxes
        for cb in pc_data.get('checkboxes', [])[:20]:
            indent = "  " * cb['depth']
            flags = []
            if cb['checked']: flags.append('X')
            if cb['indeterminate']: flags.append('-')
            flag = f"[{','.join(flags)}]" if flags else "[ ]"
            print(f"  {indent}{flag} {cb['text']}")

        # Show expandable items
        if pc_data.get('expandables'):
            print(f"\nExpandable items (first 10):")
            for e in pc_data['expandables']:
                print(f"  [{e['parentClass'][:40]}] {e['text']}")

        # Show section headers
        if pc_data.get('sections'):
            print(f"\nSections:")
            for s in pc_data['sections']:
                print(f"  [{s['class']}] {s['text'][:80]}")

        # === TAB 3: 数据权限 ===
        print("\n=== Switching to 数据权限 tab ===")
        page.click_permission_tab_data_scope()
        time.sleep(2)

        ds_data = driver.execute_script(r"""
        function T(el) { if (!el) return ''; return (el.innerText || el.textContent || '').trim(); }
        var result = {};

        var panes = document.querySelectorAll('.el-tab-pane');
        var activePane = null;
        for (var i = 0; i < panes.length; i++) {
            if (panes[i].classList.contains('is-active')) { activePane = panes[i]; break; }
        }
        if (!activePane) { result.error = 'NO_ACTIVE_PANE'; return result; }

        // Find all radio buttons
        var radios = [];
        activePane.querySelectorAll('.el-radio').forEach(function(r, i) {
            radios.push({
                index: i,
                text: T(r),
                checked: r.classList.contains('is-checked')
            });
        });
        result.radios = radios;

        // Check for any tree/checkbox structure
        var checkboxes = [];
        activePane.querySelectorAll('label.el-checkbox').forEach(function(cb) {
            checkboxes.push({
                text: T(cb),
                checked: cb.classList.contains('is-checked')
            });
        });
        result.checkboxes = checkboxes;

        // Also get el-tree if present
        var treeNodes = [];
        activePane.querySelectorAll('.el-tree-node').forEach(function(n) {
            var label = n.querySelector('.el-tree-node__label');
            treeNodes.push({label: label ? T(label) : ''});
        });
        result.treeNodes = treeNodes;

        result.fullText = T(activePane).substring(0, 500);
        return result;
        """)

        path = save(ds_data, 'perm_tab_datascope.json')
        print(f"Saved: {path}")
        print(f"Radios: {ds_data.get('radios',[])}")
        print(f"Checkboxes: {ds_data.get('checkboxes',[])}")
        print(f"TreeNodes: {ds_data.get('treeNodes',[])}")
        print(f"Full text: {ds_data.get('fullText','')[:300]}")

        print("\nDone! All data saved.")

    finally:
        if driver:
            try: driver.quit()
            except: pass

if __name__ == '__main__':
    main()
