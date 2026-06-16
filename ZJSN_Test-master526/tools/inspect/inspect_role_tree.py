"""Deep-dive into the permission dialog's tab pane content to find tree/checkbox structure"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.RoleManagePage import RoleManagePage

OUT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

        # Click permission for "人员培训管理员"
        page.click_permission_by_role_name("人员培训管理员")
        time.sleep(4)

        # DEEP inspection of the dialog's active tab pane
        deep = driver.execute_script(r"""
        function T(el) { if (!el) return ''; return (el.innerText || el.textContent || '').trim(); }

        var result = {};

        // Find the visible dialog
        var dlg = null;
        document.querySelectorAll('.el-dialog').forEach(function(d) {
            if (d.offsetWidth > 0 && d.offsetHeight > 0) dlg = d;
        });
        if (!dlg) { result.error = 'NO_DIALOG'; return result; }

        result.dialogTitle = T(dlg.querySelector('.el-dialog__title'));

        // Find ALL tab panes in the dialog
        var panes = [];
        dlg.querySelectorAll('.el-tab-pane').forEach(function(pane, i) {
            var isActive = pane.classList.contains('is-active');
            var label = pane.getAttribute('aria-labelledby') || pane.getAttribute('id') || '';
            var children = [];
            // Get ALL child elements recursively (depth 1)
            for (var c = 0; c < pane.children.length; c++) {
                var child = pane.children[c];
                children.push({
                    tag: child.tagName,
                    class: (child.className || '').toString().substring(0, 120),
                    childCount: child.children.length,
                    text: T(child).substring(0, 200)
                });
            }
            // Also get deeper content summary
            var allCheckboxes = pane.querySelectorAll('.el-checkbox');
            var allTreeNodes = pane.querySelectorAll('.el-tree-node, [class*="tree"]');
            var allLabels = pane.querySelectorAll('label');
            var allDivs = pane.querySelectorAll('div[class]');
            var uniqueClasses = {};
            allDivs.forEach(function(d) {
                var cls = (d.className || '').toString().split(' ')[0];
                if (cls && cls.indexOf('el-') === 0) uniqueClasses[cls] = (uniqueClasses[cls] || 0) + 1;
            });

            panes.push({
                index: i,
                isActive: isActive,
                label: label,
                children: children,
                checkboxes: allCheckboxes.length,
                treeNodes: allTreeNodes.length,
                labels: allLabels.length,
                uniqueElClasses: uniqueClasses
            });
        });
        result.tabPanes = panes;

        // Also dump the full HTML (first 5000 chars) of the active pane
        var activePane = dlg.querySelector('.el-tab-pane.is-active');
        if (activePane) {
            result.activePaneHTML = activePane.innerHTML.substring(0, 8000);
            result.activePaneText = T(activePane).substring(0, 2000);

            // Find ALL clickable/interactive elements in active pane
            var interactive = [];
            activePane.querySelectorAll('input, button, label, .el-checkbox, .el-checkbox__inner, [class*="checkbox"], [class*="check"]').forEach(function(el) {
                interactive.push({
                    tag: el.tagName,
                    class: (el.className || '').toString().substring(0, 100),
                    text: T(el).substring(0, 80),
                    type: el.type || '',
                    checked: el.checked || false
                });
            });
            result.activePaneInteractive = interactive.slice(0, 50);
        }

        return result;
        """)

        with open(os.path.join(OUT_DIR, 'perm_tree_deep.json'), 'w', encoding='utf-8') as f:
            json.dump(deep, f, ensure_ascii=False, indent=2)

        print(f"Dialog title: {deep.get('dialogTitle','')}")
        print(f"Tab panes: {len(deep.get('tabPanes',[]))}")
        for p in deep.get('tabPanes', []):
            active = " <-- ACTIVE" if p.get('isActive') else ""
            print(f"  Pane[{p['index']}]: id={p['label']}  checkboxes={p['checkboxes']}  treeNodes={p['treeNodes']}  labels={p['labels']}{active}")
            if p.get('isActive'):
                print(f"    Top children: {[c['tag']+'.'+c['class'][:30] for c in p.get('children',[])]}")
                print(f"    Unique el-* classes: {p.get('uniqueElClasses',{})}")

        if deep.get('activePaneInteractive'):
            print(f"\nInteractive elements in active pane ({len(deep['activePaneInteractive'])}):")
            for el in deep['activePaneInteractive'][:20]:
                print(f"  {el['tag']} [{el['class'][:60]}] text={el['text'][:60]} checked={el['checked']}")

        if deep.get('activePaneText'):
            print(f"\nActive pane text (first 500 chars):")
            print(deep['activePaneText'][:500])

        print("\nDone! Full data in perm_tree_deep.json")

    finally:
        if driver:
            try: driver.quit()
            except: pass

if __name__ == '__main__':
    main()
