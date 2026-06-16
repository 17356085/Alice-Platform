"""Use proven UserManagePage methods to open and inspect all dialogs"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.UserManagePage import UserManagePage

OUT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def save(data, name):
    path = os.path.join(OUT_DIR, name)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [saved] {path}")

def extract_dialog(driver):
    return driver.execute_script(r"""
    function T(el) { if (!el) return ''; return (el.innerText || el.textContent || '').trim(); }
    var dlg = null;
    document.querySelectorAll('.el-dialog').forEach(function(d) {
        if (d.offsetWidth > 0 && d.offsetHeight > 0) dlg = d;
    });
    if (!dlg) return {error: 'NO_VISIBLE_DIALOG'};

    var result = {};
    result.title = T(dlg.querySelector('.el-dialog__title'));
    result.width = dlg.style.width || getComputedStyle(dlg).width;

    var formItems = [];
    dlg.querySelectorAll('.el-form-item').forEach(function(item) {
        var label = item.querySelector('.el-form-item__label');
        var labelText = label ? T(label).replace(/:$|：$/,'').replace(/\s+/g,'') : '';
        if (!labelText) return;
        var input = item.querySelector('input:not([type="hidden"])');
        var textarea = item.querySelector('textarea');
        var select = item.querySelector('.el-select');
        var selectInput = select ? select.querySelector('input') : null;
        var type = textarea ? 'textarea' : (input && !selectInput ? (input.type==='password'?'password':'input') : (select ? 'select' : 'unknown'));
        var ph = '';
        var val = '';
        var disabled = input ? (input.disabled || input.readOnly) : false;
        if (input) { ph = input.placeholder || ''; val = input.value || ''; }
        if (select) {
            var sels = select.querySelectorAll('.el-select__selected-item:not(.el-select__placeholder)');
            if (sels.length > 1) type = 'select(multi)';
            val = Array.from(sels).map(function(s){return T(s);}).join(', ');
            if (!val && selectInput) { ph = selectInput.placeholder || ''; }
        }
        if (textarea) { ph = textarea.placeholder || ''; val = textarea.value || ''; }
        formItems.push({label: labelText, type: type, disabled: disabled, placeholder: ph, currentValue: val});
    });
    result.formItems = formItems;

    var fbs = [];
    var footer = dlg.querySelector('.el-dialog__footer');
    if (footer) footer.querySelectorAll('button').forEach(function(b) {
        fbs.push({text: T(b), primary: b.classList.contains('el-button--primary')});
    });
    result.footerButtons = fbs;
    return result;
    """)

def main():
    base = BaseDriver()
    driver = None
    try:
        driver = base.open_browser()
        ensure_logged_in(driver)

        page = UserManagePage(driver)
        nav = SidebarNavigator(driver)
        nav.navigate_to("系统管理", "用户管理")
        time.sleep(4)

        # Search for a user to use (not admin)
        page.click_reset_button()
        time.sleep(1)
        page.input_search_username("szj")
        page.click_search_button()
        time.sleep(2)

        # ===== EDIT DIALOG =====
        print("=" * 60)
        print("Phase 1: Edit Dialog (via click_edit_user)")
        page.click_edit_user("szj")
        time.sleep(3)

        edit_data = extract_dialog(driver)
        save(edit_data, 'user_form_edit_dialog.json')
        if not edit_data.get('error'):
            print(f"  Title: {edit_data.get('title')}")
            print(f"  Fields ({len(edit_data.get('formItems',[]))}):")
            for f in edit_data.get('formItems', []):
                flags = []
                if f['disabled']: flags.append('[DISABLED]')
                print(f"    [{f['type']:15s}] {f['label']:10s} {' '.join(flags):15s} val={f['currentValue'][:30]}")
        else:
            print(f"  ERROR: {edit_data.get('error')}")
            # Debug: look for ANY dialog
            debug = driver.execute_script("""
                var all = [];
                document.querySelectorAll('.el-dialog, .el-drawer, .el-dialog__wrapper').forEach(function(d,i){
                    all.push({i:i,tag:d.tagName,class:(d.className||'').substring(0,50),w:d.offsetWidth,h:d.offsetHeight});
                });
                return all;
            """)
            print(f"  All dialog elements: {debug}")

        # Close
        driver.execute_script("""
            document.querySelectorAll('.el-dialog').forEach(function(d){
                if(d.offsetWidth>0){var c=d.querySelector('.el-dialog__footer button:not(.el-button--primary)');if(c)c.click();}
            });
        """)
        time.sleep(1.5)

        # ===== VIEW DIALOG =====
        print("\n" + "=" * 60)
        print("Phase 2: View Dialog")
        # Use JS click on the first user row's 查看 button
        driver.execute_script("""
            var rows = document.querySelectorAll('tr.el-table__row');
            for (var i = 0; i < rows.length; i++) {
                if (rows[i].innerText.indexOf('szj') !== -1) {
                    var btns = rows[i].querySelectorAll('button');
                    for (var k = 0; k < btns.length; k++) {
                        var span = btns[k].querySelector('span');
                        var text = (span ? span.innerText : btns[k].innerText) || '';
                        if (text.indexOf('查看') !== -1) { btns[k].click(); return; }
                    }
                }
            }
        """)
        time.sleep(3)

        view_data = extract_dialog(driver)
        save(view_data, 'user_form_view_dialog.json')
        if not view_data.get('error'):
            print(f"  Title: {view_data.get('title')}")
            for f in view_data.get('formItems', []):
                print(f"    [{f['type']:15s}] {f['label']:10s} val={f['currentValue'][:50]}")
        else:
            print(f"  ERROR: {view_data.get('error')}")

        # Close
        driver.execute_script("""
            document.querySelectorAll('.el-dialog').forEach(function(d){
                if(d.offsetWidth>0){var c=d.querySelector('.el-dialog__footer button:not(.el-button--primary)');if(c)c.click();}
            });
        """)
        time.sleep(1.5)

        # ===== ASSIGN ROLE DIALOG =====
        print("\n" + "=" * 60)
        print("Phase 3: Assign Role Dialog")
        page.click_assign_role_user("szj")
        time.sleep(3)

        role_data = driver.execute_script(r"""
        function T(el) { if (!el) return ''; return (el.innerText || el.textContent || '').trim(); }
        var dlg = null;
        document.querySelectorAll('.el-dialog').forEach(function(d) {
            if (d.offsetWidth > 0 && d.offsetHeight > 0) dlg = d;
        });
        if (!dlg) return {error: 'NO_VISIBLE_DIALOG'};
        var result = {};
        result.title = T(dlg.querySelector('.el-dialog__title'));
        var checkboxes = [];
        dlg.querySelectorAll('label.el-checkbox').forEach(function(cb) {
            checkboxes.push({
                text: T(cb),
                checked: cb.classList.contains('is-checked'),
                disabled: cb.classList.contains('is-disabled')
            });
        });
        result.checkboxes = checkboxes;
        result.count = checkboxes.length;
        var fbs = [];
        var footer = dlg.querySelector('.el-dialog__footer');
        if (footer) footer.querySelectorAll('button').forEach(function(b) {
            fbs.push({text: T(b), primary: b.classList.contains('el-button--primary')});
        });
        result.footerButtons = fbs;
        return result;
        """)
        save(role_data, 'user_form_assign_role_dialog.json')
        if not role_data.get('error'):
            print(f"  Title: {role_data.get('title')}")
            print(f"  Roles ({role_data.get('count',0)}):")
            for cb in role_data.get('checkboxes', [])[:15]:
                print(f"    [{'X' if cb['checked'] else ' '}] {cb['text']}")
        else:
            print(f"  ERROR: {role_data.get('error')}")

        # Close
        driver.execute_script("""
            document.querySelectorAll('.el-dialog').forEach(function(d){
                if(d.offsetWidth>0){var c=d.querySelector('.el-dialog__footer button:not(.el-button--primary)');if(c)c.click();}
            });
        """)
        time.sleep(1)

        # ===== COMPARE =====
        print("\n" + "=" * 60)
        print("Phase 4: 新增 vs 编辑 对比")

        # Read add data from earlier run
        add_path = os.path.join(OUT_DIR, 'user_form_add_dialog.json')
        with open(add_path, 'r', encoding='utf-8') as f:
            add_data = json.load(f)

        add_map = {f['label']: f for f in add_data.get('formItems', [])}
        edit_map = {f['label']: f for f in edit_data.get('formItems', [])} if not edit_data.get('error') else {}
        view_map = {f['label']: f for f in view_data.get('formItems', [])} if not view_data.get('error') else {}

        all_labels = sorted(set(list(add_map.keys()) + list(edit_map.keys()) + list(view_map.keys())))

        for label in all_labels:
            a = add_map.get(label, None)
            e = edit_map.get(label, None)
            v = view_map.get(label, None)
            a_str = f"add:[{a['type']}] val={a.get('currentValue','')[:20]}" if a else '---'
            e_str = f"edit:[{e['type']}] val={e.get('currentValue','')[:20]}" if e else '---'
            if e and e.get('disabled'): e_str += ' DISABLED'
            v_str = f"view:[{v['type']}] val={v.get('currentValue','')[:20]}" if v else '---'
            print(f"  {label:10s} | {a_str:45s} | {e_str:45s} | {v_str}")

        print("\nDone!")

    finally:
        if driver:
            try: driver.quit()
            except: pass

if __name__ == '__main__':
    main()
