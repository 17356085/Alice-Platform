"""Debug v3: try ActionChains + check for popconfirm + monitor network"""
import os, sys, json, time, io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait

base = BaseDriver()
driver = base.open_browser()
try:
    ensure_logged_in(driver)
    nav = SidebarNavigator(driver)
    nav._navigate_by_js_hash("#/system/workflow/approval-chain", "debug-v3")
    time.sleep(4)

    # Get more detail about the button
    btn_info = driver.execute_script("""
        const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
        const cells = rows[0].querySelectorAll('td .cell');
        const lastCell = cells[cells.length - 1];
        const btns = lastCell.querySelectorAll('button');

        const result = {};
        btns.forEach((b, i) => {
            result['btn_' + i] = {
                text: b.textContent.trim(),
                outerHTML: b.outerHTML.substring(0, 300),
                dataset: JSON.parse(JSON.stringify(b.dataset)),
                attributes: Array.from(b.attributes).map(a => a.name + '=' + a.value)
            };
        });

        // Check parent elements
        const parent = btns[0].parentElement;
        result['parent_tag'] = parent.tagName;
        result['parent_class'] = parent.className;
        result['parent_outerHTML'] = parent.outerHTML.substring(0, 400);

        // Check for popconfirm
        result['popconfirm_on_page'] = document.querySelectorAll('.el-popconfirm').length;

        return result;
    """)
    print("Button details:")
    print(json.dumps(btn_info, ensure_ascii=False, indent=2))

    # Try clicking with ActionChains
    print("\nTrying ActionChains click on '步骤配置'...")
    step_btn = driver.find_elements(By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr:first-child td:last-child button")[0]
    print(f"  Found button: {step_btn.text}")

    actions = ActionChains(driver)
    actions.move_to_element(step_btn).click().perform()
    time.sleep(3)

    # Check result
    after = driver.execute_script("""
        return {
            url: window.location.href,
            dialogs: document.querySelectorAll('.el-dialog:not([style*="display: none"])').length,
            drawers: document.querySelectorAll('.el-drawer:not([style*="display: none"])').length,
            popconfirm: document.querySelectorAll('.el-popconfirm').length,
            overlays: document.querySelectorAll('.el-overlay').length
        };
    """)
    print(f"  After ActionChains: {json.dumps(after, ensure_ascii=False)}")

    # If still nothing, check if there's a loading state or page transition
    body_html = driver.execute_script("return document.body.innerHTML.substring(0, 500);")
    print(f"  Body start: {body_html[:200]}")

    # Check for any iframe or new window
    handles = driver.window_handles
    print(f"  Window handles: {handles}")

finally:
    base.close_browser()
