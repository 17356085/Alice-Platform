"""Use the proven RoleManagePage approach to open and inspect the permission dialog"""
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
        # Use JS hash navigation (proven reliable) + wait for render
        nav = SidebarNavigator(driver)
        nav.navigate_to("系统管理", "角色管理")
        time.sleep(5)  # Wait for table to fully render

        # Click search to ensure data is loaded
        page.click_search()
        time.sleep(2)

        # Use the proven click method
        target = "人员培训管理员"  # A known role with permissions
        print(f"Clicking permission for: {target}")
        page.click_permission_by_role_name(target)
        time.sleep(4)  # Generous wait

        # Now take a screenshot
        driver.save_screenshot(os.path.join(OUT_DIR, 'perm_dialog_debug.png'))
        print("Screenshot saved")

        # More aggressive dialog search (with safer property access)
        data = driver.execute_script(r"""
        function T(el) { if (!el) return ''; return (el.innerText || el.textContent || '').trim(); }
        function safeClass(el) { try { return (el.className || '').toString().substring(0, 100); } catch(e) { return ''; } }

        var result = {};

        // 1. Find ALL tab items anywhere in the DOM
        var allTabs = [];
        document.querySelectorAll('.el-tabs__item').forEach(function(t) {
            allTabs.push({text: T(t), active: t.classList.contains('is-active'), id: t.id || ''});
        });
        result.allTabsAnywhere = allTabs;

        // 2. Find ALL tree nodes anywhere
        var treeNodes = [];
        document.querySelectorAll('.el-tree-node').forEach(function(n) {
            var label = n.querySelector('.el-tree-node__label');
            var cb = n.querySelector('.el-checkbox');
            var depth = 0;
            var p = n.parentElement;
            while (p) { if (p.classList && p.classList.contains('el-tree-node')) depth++; p = p.parentElement; }
            treeNodes.push({
                label: label ? T(label) : '',
                depth: depth,
                leaf: !n.querySelector('.el-tree-node__children'),
                checked: cb ? cb.classList.contains('is-checked') : false,
                indeterminate: cb ? cb.classList.contains('is-indeterminate') : false
            });
        });
        result.treeInfo = {count: treeNodes.length, nodes: treeNodes};

        // 3. Find the dialog/drawer container
        var containers = [];
        ['el-dialog', 'el-drawer', 'el-dialog__wrapper', 'el-drawer__wrapper'].forEach(function(cls) {
            document.querySelectorAll('.' + cls).forEach(function(el, i) {
                var title = el.querySelector('.el-dialog__title, .el-drawer__title');
                containers.push({
                    selector: cls,
                    index: i,
                    visible: el.offsetWidth > 0,
                    width: el.offsetWidth,
                    height: el.offsetHeight,
                    title: title ? T(title) : '',
                    hasTabs: el.querySelectorAll('.el-tabs__item').length,
                    hasTree: el.querySelectorAll('.el-tree-node').length
                });
            });
        });
        result.containers = containers;

        // 4. Find radio buttons in active pane
        var radios = [];
        var activePane = document.querySelector('.el-tab-pane.is-active');
        if (activePane) {
            activePane.querySelectorAll('.el-radio').forEach(function(r) {
                radios.push({text: T(r), checked: r.classList.contains('is-checked')});
            });
        }
        result.radiosInActivePane = radios;

        // 5. Footer buttons
        var footerBtns = [];
        var containers2 = document.querySelectorAll('.el-dialog__footer, .el-drawer__footer');
        containers2.forEach(function(f) {
            f.querySelectorAll('button').forEach(function(b) {
                footerBtns.push({text: T(b), primary: b.classList.contains('el-button--primary')});
            });
        });
        result.footerButtons = footerBtns;

        return result;
        """)

        # Save and read via JSON to avoid encoding issues
        out_file = os.path.join(OUT_DIR, 'perm_dialog_debug.json')
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
        print(f"Data saved to {out_file}")
        print(f"Tabs found: {len(data.get('allTabsAnywhere',[]))}")
        for t in data.get('allTabsAnywhere', []):
            print(f"  Tab: {t}")
        print(f"Tree nodes found: {data.get('treeInfo',{}).get('count',0)}")
        print(f"Containers found: {len(data.get('containers',[]))}")
        for c in data.get('containers', []):
            print(f"  Container: {c}")
        print(f"Radios in active pane: {data.get('radiosInActivePane',[])}")
        print(f"Footer buttons: {data.get('footerButtons',[])}")

    finally:
        if driver:
            try: driver.quit()
            except: pass

if __name__ == '__main__':
    main()
