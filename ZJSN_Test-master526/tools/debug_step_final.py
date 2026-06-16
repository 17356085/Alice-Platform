"""Final debug: wait longer, monitor hash changes, try clicking icon inside button"""
import os, sys, json, time, io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

base = BaseDriver()
driver = base.open_browser()
try:
    ensure_logged_in(driver)
    nav = SidebarNavigator(driver)
    nav._navigate_by_js_hash("#/system/workflow/approval-chain", "debug-final")
    time.sleep(4)

    # Install hash change listener
    driver.execute_script("window.__hash_changes = []; window.addEventListener('hashchange', () => window.__hash_changes.push(window.location.hash));")

    # Try clicking the ICON inside the button
    print("Trying to click icon inside '步骤配置' button...")
    icon_clicked = driver.execute_script("""
        const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
        const cells = rows[0].querySelectorAll('td .cell');
        const lastCell = cells[cells.length - 1];
        const firstBtn = lastCell.querySelector('button');
        // Try clicking the SVG/icon inside
        const icon = firstBtn.querySelector('i, svg, .el-icon');
        if (icon) {
            icon.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            return 'clicked_icon';
        }
        return 'no_icon';
    """)
    print(f"  Icon click: {icon_clicked}")
    time.sleep(3)

    hash_changes = driver.execute_script("return window.__hash_changes;")
    print(f"  Hash changes: {hash_changes}")
    print(f"  Current URL: {driver.current_url}")

    # Check if new content appeared
    body_len = driver.execute_script("return document.body.textContent.length;")
    print(f"  Body length: {body_len}")

    # Try mousedown + mouseup instead of click
    print("\nTrying mousedown+mouseup on '步骤配置' button...")
    driver.execute_script("""
        const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
        const cells = rows[0].querySelectorAll('td .cell');
        const lastCell = cells[cells.length - 1];
        const btn = lastCell.querySelectorAll('button')[0];
        btn.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true}));
        btn.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true}));
    """)
    time.sleep(3)
    print(f"  Current URL: {driver.current_url}")
    print(f"  Body length: {driver.execute_script('return document.body.textContent.length;')}")

    # Also check if there's a different page for steps
    # Try navigating to step config URL patterns
    print("\nTrying navigation to potential step config URLs...")
    for code in ['contractor_entry', 'wh_hazard_in']:
        for suffix in ['', '/steps', '/step', '/config', '/detail']:
            url = f"#/system/workflow/approval-chain/{code}{suffix}"
            driver.execute_script(f"window.location.hash = '{url}';")
            time.sleep(2)
            body = driver.execute_script("return document.body.textContent.trim().substring(0, 150);")
            has_table = 'el-table' in driver.page_source[:2000]
            print(f"  {url}: has_table={has_table}, body={body[:80]}")

finally:
    base.close_browser()
