"""Direct JS clicks on buttons by visible text — bypasses PO index issues"""
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

def click_row_button(driver, username, button_text):
    """Click a specific button in a user's row by matching visible text exactly"""
    return driver.execute_script(f"""
        var rows = document.querySelectorAll('tr.el-table__row');
        for (var i = 0; i < rows.length; i++) {{
            if (rows[i].innerText.indexOf('{username}') === -1) continue;
            var btns = rows[i].querySelectorAll('button');
            for (var k = 0; k < btns.length; k++) {{
                var s = btns[k].querySelector('span');
                var t = (s ? s.innerText : btns[k].innerText) || '';
                t = t.replace(/\\s+/g, '');
                if (t === '{button_text}') {{
                    btns[k].click();
                    return 'clicked button[' + k + ']: ' + t;
                }}
            }}
        }}
        return 'NOT FOUND';
    """)

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
    result.bodyHTML = dlg.querySelector('.el-dialog__body') ? dlg.querySelector('.el-dialog__body').innerHTML.substring(0, 5000) : '';

    // Form fields
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
        var ph = ''; var val = ''; var disabled = false;
        if (input) { ph = input.placeholder || ''; val = input.value || ''; disabled = input.disabled || input.readOnly; }
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

    // Checkboxes (for assign-role dialog)
    var checkboxes = [];
    dlg.querySelectorAll('label.el-checkbox').forEach(function(cb) {
        checkboxes.push({text: T(cb), checked: cb.classList.contains('is-checked')});
    });
    result.checkboxes = checkboxes;

    // Footer
    var fbs = [];
    var footer = dlg.querySelector('.el-dialog__footer');
    if (footer) footer.querySelectorAll('button').forEach(function(b) {
        fbs.push({text: T(b), primary: b.classList.contains('el-button--primary')});
    });
    result.footerButtons = fbs;

    return result;
    """)

def close_dialog(driver):
    driver.execute_script("""
        document.querySelectorAll('.el-dialog').forEach(function(d){
            if(d.offsetWidth>0){
                var c = d.querySelector('.el-dialog__footer button:not(.el-button--primary)');
                if(c) c.click();
                else { var anyBtn = d.querySelector('.el-dialog__footer button');
                    if(anyBtn) anyBtn.click(); }
            }
        });
    """)
    time.sleep(1.5)

def main():
    base = BaseDriver()
    driver = None
    try:
        driver = base.open_browser()
        ensure_logged_in(driver)

        nav = SidebarNavigator(driver)
        nav.navigate_to("系统管理", "用户管理")
        time.sleep(4)

        # Pick a specific target and search for it first
        target = "szj"
        print(f"Target: {target}")

        # Search first to ensure the row is visible
        from page.system_page.UserManagePage import UserManagePage
        page = UserManagePage(driver)
        page.click_reset_button()
        time.sleep(1)
        page.input_search_username(target)
        page.click_search_button()
        time.sleep(2)
        print(f"  Search result rows: {page.get_table_row_count()}")

        # ===== 1. VIEW DIALOG =====
        print("\n" + "=" * 60)
        print("Phase 1: 查看 (VIEW)")
        r = click_row_button(driver, target, "查看")
        print(f"  Click result: {r}")
        time.sleep(2.5)
        v = extract_dialog(driver)
        save(v, 'user_form_view_dialog.json')
        print(f"  Title: {v.get('title')}  Width: {v.get('width')}")
        print(f"  Fields: {len(v.get('formItems',[]))}  Checkboxes: {len(v.get('checkboxes',[]))}  Footer: {v.get('footerButtons')}")
        close_dialog(driver)

        # ===== 2. EDIT DIALOG =====
        print("\n" + "=" * 60)
        print("Phase 2: 编辑 (EDIT)")
        r = click_row_button(driver, target, "编辑")
        print(f"  Click result: {r}")
        time.sleep(2.5)
        e = extract_dialog(driver)
        save(e, 'user_form_edit_dialog.json')
        print(f"  Title: {e.get('title')}  Width: {e.get('width')}")
        print(f"  Fields: {len(e.get('formItems',[]))}")
        for f in e.get('formItems', []):
            flags = []
            if f['disabled']: flags.append('DISABLED')
            print(f"    [{f['type']:15s}] {f['label']:10s} {' '.join(flags):12s} val={f['currentValue'][:40]}")
        print(f"  Footer: {e.get('footerButtons')}")
        close_dialog(driver)

        # ===== 3. ASSIGN ROLE DIALOG =====
        print("\n" + "=" * 60)
        print("Phase 3: 分配角色 (ASSIGN ROLE)")
        r = click_row_button(driver, target, "分配角色")
        print(f"  Click result: {r}")
        time.sleep(2.5)
        ar = extract_dialog(driver)
        save(ar, 'user_form_assign_role_dialog.json')
        print(f"  Title: {ar.get('title')}  Width: {ar.get('width')}")
        print(f"  Checkboxes: {len(ar.get('checkboxes',[]))}")
        for cb in ar.get('checkboxes', [])[:15]:
            print(f"    [{'X' if cb['checked'] else ' '}] {cb['text']}")
        if ar.get('checkboxes') and len(ar['checkboxes']) > 15:
            print(f"    ... +{len(ar['checkboxes'])-15} more")
        # Also show bodyHTML snippet to understand structure
        if ar.get('bodyHTML'):
            print(f"  bodyHTML (first 500 chars): {ar['bodyHTML'][:500]}")
        print(f"  Footer: {ar.get('footerButtons')}")
        close_dialog(driver)

        # ===== 4. COMPARE VIEW vs EDIT =====
        print("\n" + "=" * 60)
        print("Phase 4: VIEW vs EDIT vs ADD 对比")
        add_path = os.path.join(OUT_DIR, 'user_form_add_dialog.json')
        with open(add_path, 'r', encoding='utf-8') as f:
            add_data = json.load(f)

        add_map = {f['label']: f for f in add_data.get('formItems', [])}
        edit_map = {f['label']: f for f in e.get('formItems', [])} if not e.get('error') else {}
        view_map = {f['label']: f for f in v.get('formItems', [])} if not v.get('error') else {}
        all_labels = sorted(set(list(add_map.keys()) + list(edit_map.keys()) + list(view_map.keys())))

        print(f"  {'Field':10s} | {'ADD':40s} | {'EDIT':40s} | {'VIEW':40s}")
        print(f"  {'-'*10}-+-{'-'*40}-+-{'-'*40}-+-{'-'*40}")
        for label in all_labels:
            a = add_map.get(label, None)
            ed = edit_map.get(label, None)
            vi = view_map.get(label, None)
            a_s = f"[{a['type']}] val={a.get('currentValue','')[:20]}" if a else '---'
            e_s = f"[{ed['type']}] val={ed.get('currentValue','')[:20]}" if ed else '---'
            if ed and ed.get('disabled'): e_s += ' DISABLED'
            v_s = f"[{vi['type']}] val={vi.get('currentValue','')[:20]}" if vi else '---'
            print(f"  {label:10s} | {a_s:40s} | {e_s:40s} | {v_s:40s}")

        print("\nDone!")

    finally:
        if driver:
            try: driver.quit()
            except: pass

if __name__ == '__main__':
    main()
