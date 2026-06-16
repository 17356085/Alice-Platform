"""诊断 contractor-unit 页面搜索区 + 弹窗表单"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time, json
from base.browser_driver import BaseDriver, ensure_logged_in
from base.base_page import BasePage

def main():
    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)
        time.sleep(3)

        # Navigate
        driver.execute_script("window.location.hash = '#/personnel/contractor';")
        bp = BasePage(driver)
        time.sleep(2)
        bp.wait_vue_stable()
        bp._wait_loading_gone(timeout=15)
        time.sleep(1)

        # 1. All input placeholders
        inputs = driver.execute_script("""
            var inputs = document.querySelectorAll('input[placeholder]');
            var results = [];
            inputs.forEach(function(el) {
                var ph = el.getAttribute('placeholder');
                if (ph && results.indexOf(ph) === -1) results.push(ph);
            });
            return results;
        """)
        print(f"[search_inputs] {inputs}")

        # 2. All select labels
        selects = driver.execute_script("""
            var sels = document.querySelectorAll('.el-select');
            var results = [];
            sels.forEach(function(el) {
                var label = el.closest('.el-form-item');
                var labelText = label ? label.querySelector('.el-form-item__label') : null;
                var inner = el.querySelector('.el-select__placeholder, .el-select__selected-item');
                results.push({
                    label: labelText ? labelText.textContent.trim() : '',
                    selected: inner ? inner.textContent.trim() : ''
                });
            });
            return results;
        """)
        print(f"[search_selects] {selects}")

        # 3. Click "新增" button and check dialog form labels
        add_btn = driver.execute_script("""
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].textContent.includes('新增')) return btns[i];
            }
            return null;
        """)
        if add_btn:
            driver.execute_script("arguments[0].click();", add_btn)
            time.sleep(2)
            bp.wait_dialog_open(timeout=10)
            time.sleep(1)

            form_items = driver.execute_script("""
                var items = document.querySelectorAll('.el-dialog .el-form-item__label');
                var results = [];
                items.forEach(function(el) {
                    results.push(el.textContent.trim());
                });
                return results;
            """)
            print(f"[dialog_form_labels] {form_items}")

            # all input placeholders in dialog
            dialog_inputs = driver.execute_script("""
                var inputs = document.querySelectorAll('.el-dialog input[placeholder]');
                var results = [];
                inputs.forEach(function(el) {
                    results.push(el.getAttribute('placeholder'));
                });
                return results;
            """)
            print(f"[dialog_inputs] {dialog_inputs}")

            # dialog title
            title = driver.execute_script("""
                var t = document.querySelector('.el-dialog__title');
                return t ? t.textContent.trim() : '';
            """)
            print(f"[dialog_title] '{title}'")

        result = {
            "search_inputs": inputs,
            "search_selects": selects,
            "dialog_form_labels": form_items if add_btn else [],
            "dialog_inputs": dialog_inputs if add_btn else [],
            "dialog_title": title if add_btn else '',
        }

    finally:
        base.close_browser()

    out = os.path.join(os.path.dirname(__file__), "cu_diagnosis.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {out}")

if __name__ == "__main__":
    main()
