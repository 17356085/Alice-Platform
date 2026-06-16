"""Inspect the "分配用户" dialog from role management page"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator

OUT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def save(data, name):
    path = os.path.join(OUT_DIR, name)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [saved] {path}")

def main():
    base = BaseDriver()
    driver = None
    try:
        driver = base.open_browser()
        ensure_logged_in(driver)
        nav = SidebarNavigator(driver)
        nav.navigate_to("系统管理", "角色管理")
        time.sleep(4)

        # Pick a non-admin role
        roles = driver.execute_script("""
            var names = [];
            document.querySelectorAll('tr.el-table__row td:nth-child(2) .cell').forEach(function(c){
                var t = c.innerText.trim();
                if (t && t.indexOf('超级管理员')===-1 && t.indexOf('管理员')===-1) names.push(t);
            });
            return names;
        """)
        target = roles[0] if roles else '人员培训管理员'
        print(f"Target role: {target}")

        # Click "分配用户" button
        r = driver.execute_script(f"""
            var rows = document.querySelectorAll('tr.el-table__row');
            for (var i=0;i<rows.length;i++){{
                if (rows[i].innerText.indexOf('{target}') !== -1) {{
                    var btns = rows[i].querySelectorAll('button');
                    for (var k=0;k<btns.length;k++){{
                        var s = btns[k].querySelector('span');
                        var t = (s?s.innerText:btns[k].innerText)||'';
                        if (t.indexOf('分配用户')!==-1) {{ btns[k].click(); return 'clicked btn['+k+']'; }}
                    }}
                }}
            }}
            return 'NOT FOUND';
        """)
        print(f"Click: {r}")
        time.sleep(3)

        # Extract dialog structure
        data = driver.execute_script(r"""
        function T(el) { if (!el) return ''; return (el.innerText || el.textContent || '').trim(); }
        var dlg = null;
        document.querySelectorAll('.el-dialog').forEach(function(d) {
            if (d.offsetWidth > 0 && d.offsetHeight > 0) dlg = d;
        });
        if (!dlg) return {error: 'NO_VISIBLE_DIALOG'};

        var result = {};
        result.title = T(dlg.querySelector('.el-dialog__title'));
        result.width = dlg.style.width || getComputedStyle(dlg).width;
        result.fullText = T(dlg).substring(0, 600);

        // Check for Transfer component
        var transfer = dlg.querySelector('.el-transfer');
        result.hasTransfer = !!transfer;

        // Get left/right panel buttons
        var transferBtns = [];
        dlg.querySelectorAll('.el-transfer__button').forEach(function(b) {
            transferBtns.push({text: T(b), disabled: b.classList.contains('is-disabled')});
        });
        result.transferButtons = transferBtns;

        // Get left panel items
        var leftItems = [];
        var leftPanel = dlg.querySelector('.el-transfer__panel:first-child');
        if (leftPanel) {
            leftPanel.querySelectorAll('.el-transfer-panel__item, .el-checkbox').forEach(function(item) {
                leftItems.push({text: T(item).substring(0, 40), checked: item.classList.contains('is-checked')});
            });
        }
        result.leftPanelItems = leftItems.slice(0, 20);
        result.leftPanelCount = leftItems.length;

        // Get right panel items (already assigned)
        var rightItems = [];
        var rightPanel = dlg.querySelectorAll('.el-transfer__panel')[1];
        if (rightPanel) {
            rightPanel.querySelectorAll('.el-transfer-panel__item, .el-checkbox').forEach(function(item) {
                rightItems.push({text: T(item).substring(0, 40), checked: item.classList.contains('is-checked')});
            });
        }
        result.rightPanelItems = rightItems.slice(0, 20);
        result.rightPanelCount = rightItems.length;

        // Panel headers
        var leftHeader = leftPanel ? T(leftPanel.querySelector('.el-transfer-panel__header')) : '';
        var rightHeader = rightPanel ? T(rightPanel.querySelector('.el-transfer-panel__header')) : '';
        result.leftHeader = leftHeader;
        result.rightHeader = rightHeader;

        // Footer
        var fbs = [];
        var footer = dlg.querySelector('.el-dialog__footer');
        if (footer) footer.querySelectorAll('button').forEach(function(b) {
            fbs.push({text: T(b), primary: b.classList.contains('el-button--primary')});
        });
        result.footerButtons = fbs;

        // All dialog-level buttons (including clear)
        var allDlgBtns = [];
        dlg.querySelectorAll('button').forEach(function(b) {
            var t = T(b);
            if (t) allDlgBtns.push(t);
        });
        result.allButtons = allDlgBtns;

        // Check for any form items
        var formItems = [];
        dlg.querySelectorAll('.el-form-item').forEach(function(item) {
            var label = item.querySelector('.el-form-item__label');
            formItems.push(T(label || item));
        });
        result.formItems = formItems;

        // Body HTML sample
        result.bodyHTML = dlg.querySelector('.el-dialog__body') ? dlg.querySelector('.el-dialog__body').innerHTML.substring(0, 3000) : '';

        return result;
        """)

        save(data, 'role_assign_user_dialog.json')

        print(f"\nTitle: {data.get('title')}")
        print(f"Width: {data.get('width')}")
        print(f"Has Transfer: {data.get('hasTransfer')}")
        print(f"Left panel ({data.get('leftPanelCount',0)}): {data.get('leftHeader','')}")
        for it in data.get('leftPanelItems', [])[:10]:
            print(f"  [{'X' if it['checked'] else ' '}] {it['text']}")
        if data.get('leftPanelCount',0) > 10:
            print(f"  ... +{data['leftPanelCount']-10} more")
        print(f"Right panel ({data.get('rightPanelCount',0)}): {data.get('rightHeader','')}")
        for it in data.get('rightPanelItems', [])[:10]:
            print(f"  [{'X' if it['checked'] else ' '}] {it['text']}")
        if data.get('rightPanelCount',0) > 10:
            print(f"  ... +{data['rightPanelCount']-10} more")
        print(f"Transfer buttons: {data.get('transferButtons')}")
        print(f"Footer: {data.get('footerButtons')}")
        print(f"All buttons in dialog: {data.get('allButtons')}")
        print(f"Form items: {data.get('formItems')}")
        print(f"\nFull text preview: {data.get('fullText','')[:300]}")

        print("\nDone!")

    finally:
        if driver:
            try: driver.quit()
            except: pass

if __name__ == '__main__':
    main()
