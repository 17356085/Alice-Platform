"""Dump all dialog form labels on contractor-unit and contractor-personnel pages"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.base_page import BasePage

def dump_dialog(driver, bp, label):
    """Click add button, dump dialog form labels"""
    # Find and click add button
    driver.execute_script("""
        var btns = document.querySelectorAll('button');
        for (var i = 0; i < btns.length; i++) {
            if (btns[i].textContent.includes('新增')) {
                btns[i].click();
                return;
            }
        }
    """)
    time.sleep(2)
    try:
        bp.wait_dialog_open(timeout=10)
    except:
        pass
    time.sleep(1)

    form_items = driver.execute_script("""
        var items = document.querySelectorAll('.el-dialog .el-form-item__label');
        var results = [];
        items.forEach(function(el) {
            results.push(el.textContent.trim());
        });
        return results;
    """)
    title = driver.execute_script("""
        var t = document.querySelector('.el-dialog__title');
        return t ? t.textContent.trim() : '';
    """)
    print(f"[{label}] dialog title: '{title}'")
    print(f"[{label}] form labels: {form_items}")

    # Close dialog
    driver.execute_script("""
        var btns = document.querySelectorAll('.el-dialog button');
        for (var i = 0; i < btns.length; i++) {
            if (btns[i].textContent.includes('取消') || btns[i].textContent.includes('关闭')) {
                btns[i].click();
                return;
            }
        }
        // fallback: click overlay
        var overlay = document.querySelector('.el-overlay');
        if (overlay) overlay.click();
    """)
    time.sleep(1)
    return form_items

def main():
    base = BaseDriver()
    driver = base.open_browser()
    results = {}
    try:
        ensure_logged_in(driver)
        bp = BasePage(driver)
        time.sleep(3)

        # 1. contractor-unit page
        driver.execute_script("window.location.hash = '#/personnel/contractor';")
        time.sleep(2)
        bp.wait_vue_stable()
        bp._wait_loading_gone(timeout=15)
        time.sleep(1)
        results['contractor-unit'] = dump_dialog(driver, bp, 'contractor-unit')

        # 2. contractor-personnel — click nest-menu tab
        clicked = driver.execute_script("""
            var items = document.querySelectorAll('.el-menu-item, .nest-menu .el-menu-item');
            for (var i = 0; i < items.length; i++) {
                if (items[i].textContent.indexOf('承包商人员') !== -1) {
                    items[i].click();
                    return true;
                }
            }
            return false;
        """)
        print(f"Switched to contractor-personnel: {clicked}")
        time.sleep(2)
        bp.wait_vue_stable()
        time.sleep(1)
        results['contractor-personnel'] = dump_dialog(driver, bp, 'contractor-personnel')

    finally:
        base.close_browser()

    out = os.path.join(os.path.dirname(__file__), "dialog_labels.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {out}")

if __name__ == "__main__":
    main()
