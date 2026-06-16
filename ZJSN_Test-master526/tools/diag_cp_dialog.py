"""诊断 contractor-personnel 对话框：逐字段填充 + 每步后检查 Vue 稳定性"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.base_page import BasePage
from page.personnel_page.ContractorPersonnelPage import ContractorPersonnelPage

base = BaseDriver()
driver = base.open_browser()
try:
    ensure_logged_in(driver)
    time.sleep(2)

    # Navigate to contractor page + switch to personnel tab
    driver.execute_script("window.location.hash = '#/personnel/contractor';")
    bp = BasePage(driver)
    time.sleep(2)
    bp.wait_vue_stable()
    time.sleep(1)

    # Switch to contractor-personnel tab
    clicked = driver.execute_script("""
        var items = document.querySelectorAll('.el-menu-item, .nest-menu .el-menu-item, li[role="menuitem"]');
        for (var i = 0; i < items.length; i++) {
            if (items[i].textContent.indexOf('承包商人员') !== -1) {
                items[i].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                return true;
            }
        }
        return false;
    """)
    print(f"Tab switch: {clicked}")
    time.sleep(1.5)
    bp.wait_vue_stable()
    time.sleep(1)

    # Open dialog
    page = ContractorPersonnelPage(driver)
    page.click_add_button()
    dialog_title = page.get_dialog_title_text()
    print(f"Dialog title: '{dialog_title}'")

    # Check initial form labels
    labels_before = driver.execute_script("""
        var items = document.querySelectorAll('.el-dialog .el-form-item__label');
        var r = [];
        items.forEach(function(el) { r.push(el.textContent.trim()); });
        return r;
    """)
    print(f"Initial labels: {labels_before}")

    # Now fill fields one by one with stability checks
    fields = [
        ("姓名", "测试员_001"),
        ("身份证号", "110101199001011234"),
        ("手机号码", "13900139000"),
        ("工种", "电工"),
        ("性别", "男"),
    ]

    for label, value in fields:
        try:
            # Check if label is still in DOM before filling
            labels_now = driver.execute_script("""
                var items = document.querySelectorAll('.el-dialog .el-form-item__label');
                var r = [];
                items.forEach(function(el) { r.push(el.textContent.trim()); });
                return r;
            """)
            print(f"\nBefore [{label}]: labels in DOM = {labels_now}")
            print(f"  '{label}' in DOM: {label in labels_now}")

            # Count pending Vue mutations
            vue_pending = driver.execute_script("""
                try {
                    var app = document.querySelector('#app').__vue_app__;
                    return 'vue3 app found';
                } catch(e) { return 'no vue app: ' + e; }
            """)
            print(f"  Vue check: {vue_pending}")

            # Try to find and fill
            page.fill_dialog_input(label, value)
            print(f"  [OK] fill_dialog_input('{label}', '{value}') OK")
        except Exception as e:
            print(f"  [FAIL] fill_dialog_input('{label}') FAILED: {e}")
            # Try fill_dialog_field
            try:
                page.fill_dialog_field(label, value)
                print(f"  [OK] fill_dialog_field('{label}', '{value}') OK (fallback)")
            except Exception as e2:
                print(f"  [FAIL] fill_dialog_field also FAILED: {e2}")

finally:
    print("\n--- Done ---")
    base.close_browser()
