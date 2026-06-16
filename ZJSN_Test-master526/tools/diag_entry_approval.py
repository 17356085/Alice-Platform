"""Quick diagnosis: dump all input placeholders on entry-approval page"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.browser_driver import BaseDriver, ensure_logged_in
from base.base_page import BasePage

base = BaseDriver()
driver = base.open_browser()
try:
    ensure_logged_in(driver)
    bp = BasePage(driver)
    time.sleep(2)
    driver.execute_script("window.location.hash = '#/personnel/contractor/approval';")
    time.sleep(2)
    bp.wait_vue_stable()
    bp._wait_loading_gone(timeout=15)
    time.sleep(1)

    # All inputs with placeholders
    inputs = driver.execute_script("""
        var all = document.querySelectorAll('input');
        var r = [];
        all.forEach(function(el) {
            r.push({placeholder: el.getAttribute('placeholder') || '', type: el.getAttribute('type') || 'text', visible: el.offsetParent !== null});
        });
        return r;
    """)
    print("ALL INPUTS:")
    for i in inputs:
        print(f"  placeholder='{i['placeholder']}' type={i['type']} visible={i['visible']}")

    # All select labels
    selects = driver.execute_script("""
        var sels = document.querySelectorAll('.el-select');
        var r = [];
        sels.forEach(function(el) {
            var label = el.closest('.el-form-item');
            var labelText = label ? label.querySelector('.el-form-item__label') : null;
            var current = el.querySelector('.el-select__placeholder, .el-select__selected-item, .el-tooltip__trigger span');
            r.push({label: labelText ? labelText.textContent.trim() : '', current: current ? current.textContent.trim() : ''});
        });
        return r;
    """)
    print("\nALL SELECTS:")
    for s in selects:
        print(f"  label='{s['label']}' current='{s['current']}'")

    # All button texts
    buttons = driver.execute_script("""
        var btns = document.querySelectorAll('button:not(.el-pagination button)');
        var r = [];
        btns.forEach(function(el) {
            var t = el.textContent.trim();
            if (t && t.length <= 10 && r.indexOf(t) === -1) r.push(t);
        });
        return r;
    """)
    print(f"\nBUTTONS: {buttons}")

finally:
    base.close_browser()
