"""诊断 entry-confirm 入场确认页面 DOM 结构

用法: cd ZJSN_Test-master526 && python tools/diagnose_entry_confirm.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
from base.browser_driver import BaseDriver, ensure_logged_in
from base.base_page import BasePage

PAGE = ("entry-confirm", "#/personnel/contractor/confirm")

def diagnose_page(driver, page_id, href):
    print(f"\n{'='*60}")
    print(f"[DIAG] {page_id}  ->  {href}")
    print(f"{'='*60}")

    bp = BasePage(driver)

    # JS hash 导航（sidebar_navigator 可能未注册该路由）
    driver.execute_script(f"window.location.hash = '{href}';")
    time.sleep(2)
    bp.wait_vue_stable()
    bp._wait_loading_gone(timeout=15)
    time.sleep(1)

    # 1. all input placeholders
    inputs = driver.execute_script("""
        var inputs = document.querySelectorAll('input[placeholder]');
        var results = [];
        inputs.forEach(function(el) {
            var ph = el.getAttribute('placeholder');
            if (ph && results.indexOf(ph) === -1) results.push(ph);
        });
        return results;
    """)
    print(f"  [inputs] {inputs}")

    # 2. all button texts on page (deduped, <=15 chars)
    buttons = driver.execute_script("""
        var btns = document.querySelectorAll('button');
        var texts = [];
        btns.forEach(function(el) {
            var t = el.textContent.trim();
            if (t && t.length <= 15 && texts.indexOf(t) === -1) texts.push(t);
        });
        return texts;
    """)
    print(f"  [buttons] {buttons}")

    # 3. table column count
    col_count = driver.execute_script(
        "return document.querySelectorAll('.el-table__header-wrapper th').length;"
    )
    print(f"  [columns] {col_count}")

    # 4. table headers text
    headers = driver.execute_script("""
        var ths = document.querySelectorAll('.el-table__header-wrapper th .cell');
        var results = [];
        ths.forEach(function(el) {
            results.push(el.textContent.trim());
        });
        return results;
    """)
    print(f"  [headers] {headers}")

    # 5. row count
    row_count = driver.execute_script(
        "return document.querySelectorAll('.el-table__body-wrapper tbody tr').length;"
    )
    print(f"  [rows] {row_count}")

    # 6. select dropdowns
    selects = driver.execute_script("""
        var sels = document.querySelectorAll('.el-select');
        var results = [];
        sels.forEach(function(el) {
            var input = el.querySelector('.el-select__input, input');
            var ph = input ? input.getAttribute('placeholder') : '';
            var label = el.closest('.el-form-item');
            var labelText = label ? label.querySelector('.el-form-item__label') : null;
            results.push({
                placeholder: ph || '',
                label: labelText ? labelText.textContent.trim() : ''
            });
        });
        return results;
    """)
    print(f"  [selects] {selects}")

    # 7. dialog presence
    dialogs = driver.execute_script("""
        var dlg = document.querySelectorAll('.el-dialog, .el-drawer');
        var results = [];
        dlg.forEach(function(el) {
            var title = el.querySelector('.el-dialog__title, .el-drawer__title');
            results.push({
                visible: el.style.display !== 'none',
                title: title ? title.textContent.trim() : ''
            });
        });
        return results;
    """)
    print(f"  [dialogs] {dialogs}")

    # 8. pagination
    pagination = driver.execute_script("""
        var pg = document.querySelector('.el-pagination');
        if (!pg) return null;
        return {
            total: pg.querySelector('.el-pagination__total') ? pg.querySelector('.el-pagination__total').textContent.trim() : '',
            sizes: pg.querySelector('.el-pagination__sizes') ? true : false
        };
    """)
    print(f"  [pagination] {pagination}")

    # 9. form items (if any)
    form_items = driver.execute_script("""
        var items = document.querySelectorAll('.el-form-item__label');
        var results = [];
        items.forEach(function(el) {
            results.push(el.textContent.trim());
        });
        return results;
    """)
    print(f"  [form_labels] {form_items}")

    # 10. tag/status elements
    tags = driver.execute_script("""
        var els = document.querySelectorAll('.el-tag, .el-tag--light, .el-tag--dark');
        var texts = [];
        els.forEach(function(el) {
            var t = el.textContent.trim();
            if (t && texts.indexOf(t) === -1) texts.push(t);
        });
        return texts;
    """)
    print(f"  [tags] {tags}")

    # 11. Page title or header
    page_title = driver.execute_script("""
        var h = document.querySelector('h1, h2, h3, .page-title, .title, .header-title');
        return h ? h.textContent.trim() : '';
    """)
    print(f"  [page_title] '{page_title}'")

    return {
        "page_id": page_id,
        "href": href,
        "page_title": page_title,
        "placeholders": inputs,
        "buttons": buttons,
        "columns": col_count,
        "headers": headers,
        "rows": row_count,
        "selects": selects,
        "dialogs": dialogs,
        "pagination": pagination,
        "form_labels": form_items,
        "tags": tags,
    }


def main():
    results = []
    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)
        from selenium.webdriver.support.ui import WebDriverWait
        try:
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script(
                    "return document.querySelectorAll('.el-menu-item, .el-sub-menu__title').length > 5"
                )
            )
        except Exception:
            time.sleep(3)

        page_id, href = PAGE
        try:
            r = diagnose_page(driver, page_id, href)
            results.append(r)
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()
            results.append({"page_id": page_id, "error": str(e)})

    finally:
        base.close_browser()

    out_path = os.path.join(os.path.dirname(__file__), "entry_confirm_diagnosis.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
