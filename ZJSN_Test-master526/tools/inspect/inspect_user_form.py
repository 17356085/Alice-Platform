"""Extract ALL user management dialogs: add, edit, view, assign-role, more-menu"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

OUT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def save(data, name):
    path = os.path.join(OUT_DIR, name)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [saved] {path}")

def extract_dialog_fields(driver):
    """Extract all form fields from the current visible dialog"""
    return driver.execute_script(r"""
    function T(el) { if (!el) return ''; return (el.innerText || el.textContent || '').trim(); }

    // Find visible dialog
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
        var treeSelect = item.querySelector('.el-tree-select');
        var cascader = item.querySelector('.el-cascader');
        var radioGroup = item.querySelector('.el-radio-group');
        var switchEl = item.querySelector('.el-switch');
        var selectInput = select ? select.querySelector('input') : null;

        var type = 'unknown';
        var placeholder = '';
        var currentVal = '';
        var disabled = false;
        var isRequired = !!(item.querySelector('.is-required, .asterisk-left, .required') ||
                           (label && (label.getAttribute('class')||'').indexOf('is-required') !== -1));

        if (textarea) {
            type = 'textarea';
            placeholder = textarea.placeholder || '';
            currentVal = textarea.value || '';
        } else if (input && !selectInput) {
            type = input.type === 'password' ? 'password' : (input.type === 'number' ? 'number' : 'input');
            placeholder = input.placeholder || '';
            currentVal = input.value || '';
            disabled = input.disabled || input.readOnly;
        } else if (treeSelect) {
            type = 'tree-select';
            var sel = treeSelect.querySelector('.el-select__selected-item:not(.el-select__placeholder)');
            if (sel) currentVal = T(sel);
        } else if (cascader) {
            type = 'cascader';
            var ci = cascader.querySelector('input');
            if (ci) { placeholder = ci.placeholder || ''; currentVal = ci.value || ''; }
        } else if (select) {
            type = 'select';
            // Check for multi-select (tags mode)
            var selectedItems = select.querySelectorAll('.el-select__selected-item:not(.el-select__placeholder)');
            if (selectedItems.length > 1) type = 'select(multi)';
            var vals = [];
            selectedItems.forEach(function(si) { vals.push(T(si)); });
            currentVal = vals.join(', ');
            if (!currentVal && selectInput) {
                placeholder = selectInput.placeholder || '';
            }
        } else if (switchEl) {
            type = 'switch';
            currentVal = switchEl.classList.contains('is-checked') ? 'on' : 'off';
        } else if (radioGroup) {
            type = 'radio-group';
            var checked = radioGroup.querySelector('.is-checked span');
            currentVal = checked ? T(checked) : '';
        }

        formItems.push({
            label: labelText,
            type: type,
            required: isRequired,
            disabled: disabled,
            placeholder: placeholder,
            currentValue: currentVal
        });
    });
    result.formItems = formItems;

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

    // Dialog body raw HTML (first 3000 chars for reference)
    result.bodyHTML_sample = dlg.querySelector('.el-dialog__body') ? dlg.querySelector('.el-dialog__body').innerHTML.substring(0, 3000) : '';

    return result;
    """)

def main():
    base = BaseDriver()
    driver = None
    try:
        driver = base.open_browser()
        ensure_logged_in(driver)

        nav = SidebarNavigator(driver)
        nav.navigate_to("系统管理", "用户管理")
        time.sleep(4)

        # =========================================================
        # Phase 1: 新增用户弹窗
        # =========================================================
        print("=" * 60)
        print("Phase 1: 新增用户弹窗")
        driver.execute_script("""
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].innerText && btns[i].innerText.trim() === '新增') {
                    btns[i].click(); return;
                }
            }
        """)
        time.sleep(2.5)

        add_data = extract_dialog_fields(driver)
        save(add_data, 'user_form_add_dialog.json')
        print(f"  Title: {add_data.get('title')}")
        print(f"  Width: {add_data.get('width')}")
        print(f"  Fields ({len(add_data.get('formItems',[]))}):")
        for f in add_data.get('formItems', []):
            flags = []
            if f['required']: flags.append('*')
            if f['disabled']: flags.append('[disabled]')
            print(f"    [{f['type']:15s}] {f['label']:10s} {' '.join(flags):12s} ph={f['placeholder'][:30]:30s} val={f['currentValue'][:30]}")
        print(f"  Footer: {add_data.get('footerButtons')}")

        # Close dialog
        driver.execute_script("""
            var dlgs = document.querySelectorAll('.el-dialog');
            for (var i=0;i<dlgs.length;i++) {
                if (dlgs[i].offsetWidth>0) {
                    var cancel = dlgs[i].querySelector('.el-dialog__footer button:not(.el-button--primary)');
                    if (cancel) cancel.click();
                }
            }
        """)
        time.sleep(1.5)

        # =========================================================
        # Phase 2: 编辑用户弹窗
        # =========================================================
        print("\n" + "=" * 60)
        print("Phase 2: 编辑用户弹窗")

        # Find a user to edit (not admin, not test_*)
        users = driver.execute_script("""
            var names = [];
            document.querySelectorAll('tr.el-table__row td:nth-child(2) .cell').forEach(function(c) {
                var t = c.innerText.trim();
                if (t && t !== 'admin' && t.indexOf('test_') !== 0) names.push(t);
            });
            return names;
        """)
        target = users[0] if users else 'szj'
        print(f"  Target user: {target}")

        # Click edit button for this user
        driver.execute_script(f"""
            var rows = document.querySelectorAll('tr.el-table__row');
            for (var i=0;i<rows.length;i++) {{
                if (rows[i].innerText.indexOf('{target}') !== -1) {{
                    var btns = rows[i].querySelectorAll('button');
                    for (var k=0;k<btns.length;k++) {{
                        if (btns[k].innerText.trim() === '编辑') {{
                            btns[k].click(); return;
                        }}
                    }}
                }}
            }}
        """)
        time.sleep(2.5)

        edit_data = extract_dialog_fields(driver)
        save(edit_data, 'user_form_edit_dialog.json')
        print(f"  Title: {edit_data.get('title')}")
        print(f"  Fields ({len(edit_data.get('formItems',[]))}):")
        for f in edit_data.get('formItems', []):
            flags = []
            if f['required']: flags.append('*')
            if f['disabled']: flags.append('[disabled]')
            print(f"    [{f['type']:15s}] {f['label']:10s} {' '.join(flags):12s} ph={f['placeholder'][:30]:30s} val={f['currentValue'][:30]}")

        # Close
        driver.execute_script("""
            var dlgs = document.querySelectorAll('.el-dialog');
            for (var i=0;i<dlgs.length;i++) {
                if (dlgs[i].offsetWidth>0) {
                    var cancel = dlgs[i].querySelector('.el-dialog__footer button:not(.el-button--primary)');
                    if (cancel) cancel.click();
                }
            }
        """)
        time.sleep(1.5)

        # =========================================================
        # Phase 3: 查看用户弹窗
        # =========================================================
        print("\n" + "=" * 60)
        print("Phase 3: 查看用户弹窗")
        driver.execute_script(f"""
            var rows = document.querySelectorAll('tr.el-table__row');
            for (var i=0;i<rows.length;i++) {{
                if (rows[i].innerText.indexOf('{target}') !== -1) {{
                    var btns = rows[i].querySelectorAll('button');
                    for (var k=0;k<btns.length;k++) {{
                        if (btns[k].innerText.trim() === '查看') {{
                            btns[k].click(); return;
                        }}
                    }}
                }}
            }}
        """)
        time.sleep(2.5)

        view_data = extract_dialog_fields(driver)
        save(view_data, 'user_form_view_dialog.json')
        print(f"  Title: {view_data.get('title')}")
        print(f"  Fields ({len(view_data.get('formItems',[]))}):")
        for f in view_data.get('formItems', []):
            print(f"    [{f['type']:15s}] {f['label']:10s} val={f['currentValue'][:50]}")
        print(f"  Footer: {view_data.get('footerButtons')}")

        # Close
        driver.execute_script("""
            var dlgs = document.querySelectorAll('.el-dialog');
            for (var i=0;i<dlgs.length;i++) {
                if (dlgs[i].offsetWidth>0) {
                    var cancel = dlgs[i].querySelector('.el-dialog__footer button:not(.el-button--primary)');
                    if (cancel) cancel.click();
                }
            }
        """)
        time.sleep(1.5)

        # =========================================================
        # Phase 4: 分配角色弹窗
        # =========================================================
        print("\n" + "=" * 60)
        print("Phase 4: 分配角色弹窗")
        driver.execute_script(f"""
            var rows = document.querySelectorAll('tr.el-table__row');
            for (var i=0;i<rows.length;i++) {{
                if (rows[i].innerText.indexOf('{target}') !== -1) {{
                    var btns = rows[i].querySelectorAll('button');
                    for (var k=0;k<btns.length;k++) {{
                        if (btns[k].innerText.trim() === '分配角色') {{
                            btns[k].click(); return;
                        }}
                    }}
                }}
            }}
        """)
        time.sleep(2.5)

        role_data = driver.execute_script(r"""
        function T(el) { if (!el) return ''; return (el.innerText || el.textContent || '').trim(); }

        var dlg = null;
        document.querySelectorAll('.el-dialog').forEach(function(d) {
            if (d.offsetWidth > 0 && d.offsetHeight > 0) dlg = d;
        });
        if (!dlg) return {error: 'NO_VISIBLE_DIALOG'};

        var result = {};
        result.title = T(dlg.querySelector('.el-dialog__title'));

        // Checkbox group
        var checkboxes = [];
        dlg.querySelectorAll('label.el-checkbox').forEach(function(cb) {
            checkboxes.push({
                text: T(cb),
                checked: cb.classList.contains('is-checked'),
                disabled: cb.classList.contains('is-disabled')
            });
        });
        result.checkboxes = checkboxes;
        result.checkboxCount = checkboxes.length;

        // Footer
        var fbs = [];
        var footer = dlg.querySelector('.el-dialog__footer');
        if (footer) {
            footer.querySelectorAll('button').forEach(function(b) {
                fbs.push({text: T(b), primary: b.classList.contains('el-button--primary')});
            });
        }
        result.footerButtons = fbs;

        // Role list from checkboxes
        result.roleNames = checkboxes.map(function(c) { return c.text; }).filter(function(t) { return t; });

        return result;
        """)
        save(role_data, 'user_form_assign_role_dialog.json')
        print(f"  Title: {role_data.get('title')}")
        print(f"  Available roles ({role_data.get('checkboxCount',0)}):")
        for cb in role_data.get('checkboxes', [])[:10]:
            status = "[X]" if cb['checked'] else "[ ]"
            print(f"    {status} {cb['text']}")
        if role_data.get('checkboxCount',0) > 10:
            print(f"    ... +{role_data['checkboxCount']-10} more")

        # Close
        driver.execute_script("""
            var dlgs = document.querySelectorAll('.el-dialog');
            for (var i=0;i<dlgs.length;i++) {
                if (dlgs[i].offsetWidth>0) {
                    var cancel = dlgs[i].querySelector('.el-dialog__footer button:not(.el-button--primary)');
                    if (cancel) cancel.click();
                }
            }
        """)
        time.sleep(1)

        # =========================================================
        # Phase 5: 更多菜单
        # =========================================================
        print("\n" + "=" * 60)
        print("Phase 5: 更多下拉菜单")
        driver.execute_script(f"""
            var rows = document.querySelectorAll('tr.el-table__row');
            for (var i=0;i<rows.length;i++) {{
                if (rows[i].innerText.indexOf('{target}') !== -1) {{
                    var btns = rows[i].querySelectorAll('button');
                    for (var k=0;k<btns.length;k++) {{
                        if (btns[k].innerText.trim() === '更多') {{
                            btns[k].click(); return;
                        }}
                    }}
                }}
            }}
        """)
        time.sleep(1.5)

        menu_items = driver.execute_script(r"""
        function T(el) { if (!el) return ''; return (el.innerText || el.textContent || '').trim(); }
        var items = [];
        document.querySelectorAll('.el-popper').forEach(function(p) {
            if (getComputedStyle(p).display === 'none') return;
            p.querySelectorAll('.el-dropdown-menu__item, li').forEach(function(li) {
                var t = T(li);
                if (t) items.push(t);
            });
        });
        return items;
        """)
        print(f"  Menu items: {menu_items}")

        # =========================================================
        # Phase 6: 对比新增 vs 编辑差异
        # =========================================================
        print("\n" + "=" * 60)
        print("Phase 6: 新增 vs 编辑 差异对比")

        add_fields = {f['label']: f for f in add_data.get('formItems', [])}
        edit_fields = {f['label']: f for f in edit_data.get('formItems', [])}
        view_fields = {f['label']: f for f in view_data.get('formItems', [])}

        all_labels = sorted(set(list(add_fields.keys()) + list(edit_fields.keys()) + list(view_fields.keys())))

        print(f"  {'Field':12s} {'Add':25s} {'Edit':25s} {'View':25s}")
        print(f"  {'-'*12} {'-'*25} {'-'*25} {'-'*25}")
        for label in all_labels:
            a = add_fields.get(label, {})
            e = edit_fields.get(label, {})
            v = view_fields.get(label, {})

            a_str = f"[{a.get('type','?'):10s}] val={a.get('currentValue','')[:15]}" if a else '(not present)'
            e_str = f"[{e.get('type','?'):10s}] val={e.get('currentValue','')[:15]}" if e else '(not present)'
            v_str = f"[{v.get('type','?'):10s}] val={v.get('currentValue','')[:15]}" if v else '(not present)'

            if e.get('disabled'): e_str += ' DISABLED'
            print(f"  {label:12s} {a_str:25s} {e_str:25s} {v_str:25s}")

        print("\nDone! All data saved.")

    finally:
        if driver:
            try: driver.quit()
            except: pass

if __name__ == '__main__':
    main()
