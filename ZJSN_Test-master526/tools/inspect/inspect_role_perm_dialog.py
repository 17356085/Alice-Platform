"""Extract permission dialog structure from role management page"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from selenium.webdriver.support.ui import WebDriverWait

OUT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def save_json(data, filename):
    path = os.path.join(OUT_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [saved] {path}")

def main():
    base = BaseDriver()
    driver = None
    try:
        driver = base.open_browser()
        ensure_logged_in(driver)
        driver.get('https://aiwechatminidemo.cimc-digital.com/#/system/role')
        time.sleep(3)
        WebDriverWait(driver, 15).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        time.sleep(2)

        # Find a non-super-admin role to click
        roles = driver.execute_script("""
            var names = [];
            document.querySelectorAll('tr.el-table__row td:nth-child(2) .cell').forEach(function(c) {
                names.push(c.innerText.trim());
            });
            return names;
        """)
        print("Available roles:", roles[:10])

        target = None
        for r in roles:
            if r not in ('超级管理员', '管理员') and 'admin' not in r.lower():
                target = r
                break
        if not target:
            target = roles[2] if len(roles) > 2 else roles[0]
        print(f"Target role: {target}")

        # Click the permission button
        result = driver.execute_script(f"""
            var rows = document.querySelectorAll('tr.el-table__row');
            for (var i = 0; i < rows.length; i++) {{
                if (rows[i].innerText.indexOf('{target}') !== -1) {{
                    var btns = rows[i].querySelectorAll('button');
                    for (var k = 0; k < btns.length; k++) {{
                        if (btns[k].innerText.indexOf('权限') !== -1) {{
                            btns[k].click();
                            return 'clicked row ' + i;
                        }}
                    }}
                }}
            }}
            return 'NOT FOUND';
        """)
        print(f"Click result: {result}")
        time.sleep(3)

        # ── Extract ALL permission dialog data ──
        all_data = driver.execute_script(r'''
        function T(el) { if (!el) return ''; return (el.innerText || el.textContent || '').trim(); }

        var result = {};

        // Find visible dialog/drawer
        var dlg = null;
        var isDrawer = false;
        var candidates = document.querySelectorAll('.el-dialog, .el-drawer');
        for (var i = 0; i < candidates.length; i++) {
            var c = candidates[i];
            var style = getComputedStyle(c);
            if (style.display !== 'none' && style.visibility !== 'hidden' && c.offsetParent !== null) {
                dlg = c;
                isDrawer = c.classList.contains('el-drawer');
                break;
            }
        }
        // Fallback: check for visibility differently
        if (!dlg) {
            for (var i = 0; i < candidates.length; i++) {
                if (candidates[i].offsetWidth > 0 && candidates[i].offsetHeight > 0) {
                    dlg = candidates[i];
                    isDrawer = candidates[i].classList.contains('el-drawer');
                    break;
                }
            }
        }
        if (!dlg) { result.error = 'NO_DIALOG'; return result; }
        result.isDrawer = isDrawer;

        // Title
        var titleEl = dlg.querySelector('.el-dialog__title, .el-drawer__title');
        result.title = titleEl ? T(titleEl) : '';

        // Tabs
        var tabs = [];
        var tabEls = dlg.querySelectorAll('.el-tabs__item');
        tabEls.forEach(function(tab, i) {
            tabs.push({
                index: i,
                id: tab.id || '',
                text: T(tab),
                isActive: tab.classList.contains('is-active') || (tab.parentElement && tab.parentElement.classList.contains('is-active'))
            });
        });
        result.tabs = tabs;

        // For EACH tab, extract the content
        result.tabContents = {};

        // First, get the currently active tab's content
        function extractActivePane(dialog) {
            var pane = dialog.querySelector('.el-tab-pane.is-active');
            if (!pane) {
                var panes = dialog.querySelectorAll('.el-tab-pane');
                for (var i = 0; i < panes.length; i++) {
                    if (panes[i].offsetHeight > 0) { pane = panes[i]; break; }
                }
            }
            if (!pane) return null;

            var data = {};

            // Tree nodes
            var treeNodes = [];
            pane.querySelectorAll('.el-tree-node').forEach(function(node, ni) {
                var label = node.querySelector('.el-tree-node__label');
                var checkbox = node.querySelector('.el-checkbox');
                var isExpanded = node.classList.contains('is-expanded');
                var isLeaf = !node.querySelector('.el-tree-node__children');
                var indent = 0;
                var p = node.parentElement;
                while (p) {
                    if (p.classList.contains('el-tree-node')) indent++;
                    p = p.parentElement;
                }
                treeNodes.push({
                    index: ni,
                    label: label ? T(label) : '',
                    indent: indent,
                    isLeaf: isLeaf,
                    isExpanded: isExpanded,
                    checked: checkbox ? checkbox.classList.contains('is-checked') : false,
                    indeterminate: checkbox ? checkbox.classList.contains('is-indeterminate') : false
                });
            });
            data.treeNodes = treeNodes;

            // Radios
            var radios = [];
            pane.querySelectorAll('.el-radio').forEach(function(r, i) {
                radios.push({
                    index: i,
                    text: T(r),
                    isChecked: r.classList.contains('is-checked')
                });
            });
            if (radios.length > 0) data.radios = radios;

            // Checkbox groups
            var checkboxGroups = [];
            pane.querySelectorAll('.el-checkbox-group').forEach(function(g, i) {
                var items = [];
                g.querySelectorAll('.el-checkbox').forEach(function(cb) {
                    items.push({
                        text: T(cb),
                        isChecked: cb.classList.contains('is-checked')
                    });
                });
                checkboxGroups.push(items);
            });
            if (checkboxGroups.length > 0) data.checkboxGroups = checkboxGroups;

            // Summary
            data.summary = {
                totalNodes: treeNodes.length,
                checkedNodes: treeNodes.filter(function(n) { return n.checked; }).length,
                leafNodes: treeNodes.filter(function(n) { return n.isLeaf; }).length,
                maxDepth: treeNodes.length > 0 ? Math.max.apply(null, treeNodes.map(function(n) { return n.indent; })) : 0
            };

            return data;
        }

        // Extract active tab
        result.tabContents['_active'] = extractActivePane(dlg);

        // Footer buttons
        var footerBtns = [];
        var footer = dlg.querySelector('.el-dialog__footer');
        if (footer) {
            footer.querySelectorAll('button').forEach(function(b) {
                footerBtns.push({
                    text: T(b),
                    primary: b.classList.contains('el-button--primary'),
                    disabled: b.classList.contains('is-disabled')
                });
            });
        }
        result.footerButtons = footerBtns;

        return result;
        ''')

        print(f"\nTitle: {all_data.get('title','')}")
        print(f"isDrawer: {all_data.get('isDrawer', False)}")
        print(f"\nTabs ({len(all_data.get('tabs',[]))}):")
        for t in all_data.get('tabs', []):
            active = " <-- ACTIVE" if t.get('isActive') else ""
            print(f"  [{t['index']}] id={t.get('id','')}  {t['text']}{active}")

        active = all_data.get('tabContents', {}).get('_active', {})
        print(f"\nActive Tab Tree Summary: {active.get('summary', {})}")
        print(f"Tree Nodes ({len(active.get('treeNodes',[]))}):")
        for node in active.get('treeNodes', []):
            indent = "  " * node['indent']
            cb = "[X]" if node['checked'] else ("[-]" if node['indeterminate'] else "[ ]")
            leaf = " (leaf)" if node['isLeaf'] else ""
            print(f"  {indent}{cb} {node['label']}{leaf}")

        if active.get('radios'):
            print(f"\nRadios:")
            for r in active['radios']:
                print(f"  [{'X' if r['isChecked'] else ' '}] {r['text']}")

        print(f"\nFooter: {all_data.get('footerButtons',[])}")
        save_json(all_data, 'page_structure_role_perm_dialog.json')

        # ── Click each other tab and extract ──
        for tab in all_data.get('tabs', []):
            if tab.get('isActive'): continue
            tabText = tab['text']
            print(f"\n--- Switching to tab: {tabText} ---")

            clicked = driver.execute_script(f"""
                var tabs = document.querySelectorAll('.el-tabs__item');
                for (var i = 0; i < tabs.length; i++) {{
                    if (tabs[i].innerText.indexOf('{tabText}') !== -1) {{
                        tabs[i].click();
                        return 'ok';
                    }}
                }}
                return 'fail';
            """)
            time.sleep(2)

            tabContent = driver.execute_script(r'''
            function T(el) { if (!el) return ''; return (el.innerText || el.textContent || '').trim(); }
            var pane = document.querySelector('.el-tab-pane.is-active');
            if (!pane) { return {error: 'no active pane'}; }
            var treeNodes = [];
            pane.querySelectorAll('.el-tree-node').forEach(function(node, ni) {
                var label = node.querySelector('.el-tree-node__label');
                var checkbox = node.querySelector('.el-checkbox');
                var indent = 0;
                var p = node.parentElement;
                while (p) { if (p.classList.contains('el-tree-node')) indent++; p = p.parentElement; }
                treeNodes.push({
                    index: ni, label: label ? T(label) : '', indent: indent,
                    isLeaf: !node.querySelector('.el-tree-node__children'),
                    checked: checkbox ? checkbox.classList.contains('is-checked') : false
                });
            });
            var radios = [];
            pane.querySelectorAll('.el-radio').forEach(function(r, i) {
                radios.push({index: i, text: T(r), isChecked: r.classList.contains('is-checked')});
            });
            return {treeNodes: treeNodes, radios: radios, totalNodes: treeNodes.length};
            ''')

            print(f"  Nodes: {tabContent.get('totalNodes',0)}")
            for node in tabContent.get('treeNodes', [])[:15]:
                indent = "    " + "  " * node['indent']
                cb = "[X]" if node['checked'] else "[ ]"
                print(f"{indent}{cb} {node['label']}")
            if tabContent.get('totalNodes',0) > 15:
                print(f"    ... +{tabContent['totalNodes']-15} more")
            if tabContent.get('radios'):
                print(f"  Radios: {[r['text'] for r in tabContent['radios']]}")

            all_data['tabContents'][tabText] = tabContent

        save_json(all_data, 'page_structure_role_perm_dialog.json')
        print("\nDone! All data saved.")

    finally:
        if driver:
            try: driver.quit()
            except: pass

if __name__ == '__main__':
    main()
