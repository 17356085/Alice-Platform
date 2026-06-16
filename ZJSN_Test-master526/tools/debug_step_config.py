"""Mini diagnostic: debug what "步骤配置" button does"""
import os, sys, json, time, io

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator

base = BaseDriver()
driver = base.open_browser()
try:
    ensure_logged_in(driver)
    nav = SidebarNavigator(driver)
    nav._navigate_by_js_hash("#/system/workflow/approval-chain", "debug-step")
    time.sleep(4)

    print("Current URL:", driver.current_url)
    print("Page title:", driver.title)

    # Check what elements exist on the page
    info = driver.execute_script("""
        const result = {};
        result.table_rows = document.querySelectorAll('.el-table__body-wrapper tbody tr').length;
        result.dialogs_visible = document.querySelectorAll('.el-dialog:not([style*="display: none"])').length;
        result.drawers_visible = document.querySelectorAll('.el-drawer:not([style*="display: none"])').length;

        // Get first row buttons
        const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
        if (rows.length > 0) {
            const cells = rows[0].querySelectorAll('td .cell');
            const lastCell = cells[cells.length - 1];
            result.first_row_last_cell_html = lastCell.innerHTML.substring(0, 500);
            result.first_row_buttons = Array.from(lastCell.querySelectorAll('button'))
                .map(b => ({text: b.textContent.trim(), class: b.className, onclick: b.onclick ? 'has_onclick' : 'none'}));
        }
        return result;
    """)
    print("\nPage state before click:")
    print(json.dumps(info, ensure_ascii=False, indent=2))

    # Click "步骤配置" on first row using Selenium native click
    print("\nClicking '步骤配置' on row 1 (Selenium native)...")
    from selenium.webdriver.common.by import By
    btns = driver.find_elements(By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr:first-child td:last-child button")
    for btn in btns:
        if '步骤配置' in btn.text:
            btn.click()
            print(f"  Clicked button: {btn.text}")
            break

    time.sleep(2)

    # Check console errors
    logs = driver.execute_script("""
        const toasts = document.querySelectorAll('.el-message, .el-notification, .el-alert');
        const msgs = [];
        toasts.forEach(t => msgs.push(t.textContent.trim().substring(0, 200)));
        return msgs;
    """)
    print(f"  After step-config click - messages: {logs}")

    # Also try clicking "编辑" to verify approach works
    print("\nAlso clicking '编辑' on row 1 for comparison...")
    from selenium.webdriver.common.by import By
    driver.find_element(By.XPATH, "//button[contains(text(),'编辑')]").click()
    time.sleep(2)

    # What happened?
    after = driver.execute_script("""
        const result = {};
        result.url = window.location.href;
        result.hash = window.location.hash;
        result.dialogs_visible = document.querySelectorAll('.el-dialog:not([style*="display: none"])').length;
        result.drawers_visible = document.querySelectorAll('.el-drawer:not([style*="display: none"])').length;

        const allDialogs = document.querySelectorAll('.el-dialog');
        allDialogs.forEach((dlg, i) => {
            const style = dlg.getAttribute('style') || '';
            result['dialog_' + i] = {
                visible: dlg.offsetParent !== null,
                style: style.substring(0, 50),
                title: (dlg.querySelector('.el-dialog__title') || {}).textContent || ''
            };
        });
        return result;
    """)
    print("\nAfter 编辑 click:")
    print(json.dumps(after, ensure_ascii=False, indent=2))

    # Save screenshot
    driver.save_screenshot(os.path.join(os.path.dirname(__file__), "debug_step_config.png"))
    print("\nScreenshot saved to debug_step_config.png")

finally:
    base.close_browser()
