"""Debug: find the actual permission dialog/drawer structure"""
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

        # Debug: what roles are available?
        roles_raw = driver.execute_script("""
            var rows = document.querySelectorAll('tr.el-table__row');
            var result = [];
            rows.forEach(function(r, i) {
                var name = r.querySelector('td:nth-child(2) .cell');
                var code = r.querySelector('td:nth-child(3) .cell');
                var btns = [];
                r.querySelectorAll('button').forEach(function(b) { btns.push(b.innerText.trim()); });
                result.push({
                    row: i,
                    name: name ? name.innerText.trim() : '',
                    code: code ? code.innerText.trim() : '',
                    buttons: btns
                });
            });
            return result;
        """)
        print("All roles with buttons:")
        for r in roles_raw:
            print(f"  Row{r['row']}: {r['name']} ({r['code']}) btns={r['buttons']}")

        # Pick a non-admin role that should have permissions
        target = None
        for r in roles_raw:
            if r['name'] not in ('超级管理员', '管理员', 'TEST-001') and r['buttons']:
                target = r['name']
                break
        if not target:
            for r in roles_raw:
                if r['buttons']:
                    target = r['name']
                    break
        print(f"\nTarget: {target}")

        # Click permission button for this role
        driver.execute_script(f"""
            var rows = document.querySelectorAll('tr.el-table__row');
            for (var i = 0; i < rows.length; i++) {{
                if (rows[i].innerText.indexOf('{target}') !== -1) {{
                    var btns = rows[i].querySelectorAll('button');
                    for (var k = 0; k < btns.length; k++) {{
                        if (btns[k].innerText.indexOf('权限') !== -1) {{
                            btns[k].click();
                            return;
                        }}
                    }}
                }}
            }}
        """)
        time.sleep(4)  # Wait longer for dialog/drawer animation

        # Debug: what's visible now?
        debug_info = driver.execute_script(r"""
        var result = {};

        // Check ALL overlays/modal-ish elements
        result.allOverlays = [];
        document.querySelectorAll('.el-overlay, .el-dialog, .el-dialog__wrapper, .el-drawer, .el-drawer__wrapper, .el-popper, .v-modal').forEach(function(el) {
            var style = getComputedStyle(el);
            result.allOverlays.push({
                tag: el.tagName,
                classes: (el.className || '').substring(0, 100),
                display: style.display,
                visibility: style.visibility,
                width: el.offsetWidth,
                height: el.offsetHeight,
                id: el.id || ''
            });
        });

        // Find any element that might be the permission container
        result.possibleContainers = [];
        var keywords = ['权限', '菜单', 'permission', 'menu', 'tab'];
        // Check for elements with title-like text
        var allDivs = document.querySelectorAll('div[class], section[class], aside[class]');
        allDivs.forEach(function(div) {
            var text = (div.innerText || '').trim();
            if (text.length > 5 && text.length < 100) {
                for (var k = 0; k < keywords.length; k++) {
                    if (text.indexOf(keywords[k]) !== -1) {
                        result.possibleContainers.push({
                            tag: div.tagName,
                            classes: (div.className || '').substring(0, 80),
                            text: text.substring(0, 80)
                        });
                        break;
                    }
                }
            }
        });

        // Also check body children for large modal-like elements
        result.bodyChildren = [];
        document.body.querySelectorAll(':scope > div, :scope > section').forEach(function(child) {
            if (child.id === 'app') return;
            var style = getComputedStyle(child);
            var text = (child.innerText || '').trim().substring(0, 60);
            result.bodyChildren.push({
                tag: child.tagName,
                id: child.id || '',
                classes: (child.className || '').substring(0, 80),
                display: style.display,
                text: text
            });
        });

        return result;
        """)

        print("\nDebug - overlays found:")
        for o in debug_info.get('allOverlays', []):
            if o['display'] != 'none' and o['width'] > 0:
                print(f"  VISIBLE: {o['tag']} [{o['classes'][:80]}] {o['width']}x{o['height']}")

        print("\nDebug - possible containers with permission keywords:")
        for c in debug_info.get('possibleContainers', [])[:5]:
            print(f"  {c['tag']} [{c['classes'][:60]}] text={c['text'][:60]}")

        print("\nDebug - body children (non-app):")
        for c in debug_info.get('bodyChildren', []):
            if c['display'] != 'none':
                print(f"  {c['tag']}#{c['id']} [{c['classes'][:60]}] text={c['text']}")

        # Now try a more comprehensive extraction
        perm_data = driver.execute_script(r"""
        function T(el) { if (!el) return ''; return (el.innerText || el.textContent || '').trim(); }

        var result = {};

        // Strategy 1: Find el-drawer
        var drawers = document.querySelectorAll('.el-drawer');
        for (var i = 0; i < drawers.length; i++) {
            if (drawers[i].offsetWidth > 0 && drawers[i].offsetHeight > 0) {
                result.type = 'drawer';
                result.container = 'el-drawer';
                var d = drawers[i];
                result.title = T(d.querySelector('.el-drawer__title'));
                result.width = d.style.width || getComputedStyle(d).width;

                // Tabs
                var tabs = [];
                d.querySelectorAll('.el-tabs__item').forEach(function(t, i) {
                    tabs.push({index: i, id: t.id||'', text: T(t), active: t.classList.contains('is-active')});
                });
                result.tabs = tabs;

                // Tree nodes in active pane
                var pane = d.querySelector('.el-tab-pane.is-active');
                if (pane) {
                    var nodes = [];
                    pane.querySelectorAll('.el-tree-node').forEach(function(n) {
                        var label = n.querySelector('.el-tree-node__label');
                        var cb = n.querySelector('.el-checkbox');
                        var depth = 0;
                        var p = n.parentElement;
                        while (p) { if (p.classList.contains('el-tree-node')) depth++; p = p.parentElement; }
                        nodes.push({
                            label: label ? T(label) : '',
                            depth: depth,
                            leaf: !n.querySelector('.el-tree-node__children'),
                            checked: cb ? cb.classList.contains('is-checked') : false,
                            indeterminate: cb ? cb.classList.contains('is-indeterminate') : false
                        });
                    });
                    result.treeNodes = nodes;
                    result.nodeCount = nodes.length;
                }

                // Footer
                var fbs = [];
                var footer = d.querySelector('.el-drawer__footer, .el-dialog__footer');
                if (footer) {
                    footer.querySelectorAll('button').forEach(function(b) {
                        fbs.push({text: T(b), primary: b.classList.contains('el-button--primary')});
                    });
                }
                result.footerButtons = fbs;

                return result;
            }
        }

        // Strategy 2: Find el-dialog
        var dialogs = document.querySelectorAll('.el-dialog');
        for (var i = 0; i < dialogs.length; i++) {
            var d = dialogs[i];
            if (d.offsetWidth > 0 && d.offsetHeight > 0) {
                result.type = 'dialog';
                result.container = 'el-dialog';
                result.title = T(d.querySelector('.el-dialog__title'));
                result.width = d.style.width || getComputedStyle(d).width;

                var tabs = [];
                d.querySelectorAll('.el-tabs__item').forEach(function(t, i) {
                    tabs.push({index: i, id: t.id||'', text: T(t), active: t.classList.contains('is-active')});
                });
                result.tabs = tabs;

                var pane = d.querySelector('.el-tab-pane.is-active');
                if (pane) {
                    var nodes = [];
                    pane.querySelectorAll('.el-tree-node').forEach(function(n) {
                        var label = n.querySelector('.el-tree-node__label');
                        var cb = n.querySelector('.el-checkbox');
                        var depth = 0;
                        var p = n.parentElement;
                        while (p) { if (p.classList.contains('el-tree-node')) depth++; p = p.parentElement; }
                        nodes.push({
                            label: label ? T(label) : '',
                            depth: depth,
                            leaf: !n.querySelector('.el-tree-node__children'),
                            checked: cb ? cb.classList.contains('is-checked') : false,
                            indeterminate: cb ? cb.classList.contains('is-indeterminate') : false
                        });
                    });
                    result.treeNodes = nodes;
                    result.nodeCount = nodes.length;
                }

                var fbs = [];
                var footer = d.querySelector('.el-dialog__footer');
                if (footer) {
                    footer.querySelectorAll('button').forEach(function(b) {
                        fbs.push({text: T(b), primary: b.classList.contains('el-button--primary')});
                    });
                }
                result.footerButtons = fbs;

                return result;
            }
        }

        // Strategy 3: Check for any element positioned fixed at right (drawer pattern)
        var allFixed = document.querySelectorAll('[style*="position"], .el-drawer, .el-dialog');
        result.foundNone = true;
        result.allChecked = allFixed.length;
        return result;
        """)

        print(f"\nPermission dialog data:")
        print(f"  type: {perm_data.get('type', 'unknown')}")
        print(f"  title: {perm_data.get('title', 'N/A')}")
        print(f"  tabs: {perm_data.get('tabs', [])}")
        print(f"  nodeCount: {perm_data.get('nodeCount', 0)}")
        print(f"  footerButtons: {perm_data.get('footerButtons', [])}")

        if perm_data.get('treeNodes'):
            print(f"\n  Tree nodes ({perm_data['nodeCount']}):")
            for n in perm_data['treeNodes'][:30]:
                indent = "  " * n['depth']
                cb = "[X]" if n['checked'] else ("[-]" if n['indeterminate'] else "[ ]")
                leaf = " *" if n['leaf'] else ""
                print(f"  {indent}{cb} {n['label']}{leaf}")

        save_json(perm_data, 'page_structure_role_perm_dialog.json')
        print("\nDone!")

    finally:
        if driver:
            try: driver.quit()
            except: pass

if __name__ == '__main__':
    main()
