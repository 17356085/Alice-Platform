"""Try hover-first + full MouseEvent with coordinates to trigger Vue handler"""
import os, sys, json, time, io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

base = BaseDriver()
driver = base.open_browser()
try:
    ensure_logged_in(driver)
    nav = SidebarNavigator(driver)
    nav._navigate_by_js_hash("#/system/workflow/approval-chain", "debug-hover")
    time.sleep(4)

    # Install hash change monitor
    driver.execute_script("""
        window.__hash_changes = [];
        window.addEventListener('hashchange', () => window.__hash_changes.push(window.location.hash));
        window.__clicks_detected = 0;
        // Also monitor for any DOM changes
        new MutationObserver(() => { window.__clicks_detected++; }).observe(document.body, {childList: true, subtree: true});
    """)

    # Approach 1: Hover over row first, then button, then click with ActionChains
    print("Approach 1: Hover row -> hover button -> click...")
    row = driver.find_element(By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr:first-child")
    btn = driver.find_elements(By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr:first-child td:last-child button")[0]
    print(f"  Row: {row.tag_name}, Btn: {btn.text}")

    actions = ActionChains(driver)
    actions.move_to_element(row).pause(0.5)
    actions.move_to_element(btn).pause(0.5)
    actions.click().perform()
    time.sleep(3)

    after1 = driver.execute_script("""
        return {
            url: window.location.href,
            hash_changes: window.__hash_changes,
            dom_mutations: window.__clicks_detected,
            dialogs: document.querySelectorAll('.el-dialog:not([style*="display: none"])').length,
            drawers: document.querySelectorAll('.el-drawer:not([style*="display: none"])').length,
        };
    """)
    print(f"  Result: {json.dumps(after1, ensure_ascii=False)}")

    # Approach 2: dispatch full MouseEvent with coordinates
    print("\nApproach 2: Full MouseEvent with coordinates...")
    driver.execute_script("""
        const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
        const cells = rows[0].querySelectorAll('td .cell');
        const lastCell = cells[cells.length - 1];
        const btn = lastCell.querySelectorAll('button')[0];
        const rect = btn.getBoundingClientRect();
        const cx = rect.left + rect.width / 2;
        const cy = rect.top + rect.height / 2;

        // Full event sequence
        ['mouseover', 'mouseenter', 'mousedown', 'mouseup', 'click'].forEach(evtType => {
            btn.dispatchEvent(new MouseEvent(evtType, {
                bubbles: true, cancelable: true, view: window,
                clientX: cx, clientY: cy,
                screenX: cx, screenY: cy,
                button: 0, buttons: 1
            }));
        });
    """)
    time.sleep(3)
    after2 = driver.execute_script("""
        return {
            url: window.location.href,
            hash_changes: window.__hash_changes,
            dom_mutations: window.__clicks_detected,
            dialogs: document.querySelectorAll('.el-dialog:not([style*="display: none"])').length,
            drawers: document.querySelectorAll('.el-drawer:not([style*="display: none"])').length,
        };
    """)
    print(f"  Result: {json.dumps(after2, ensure_ascii=False)}")

    # Approach 3: Click via the button's __vue__ event handlers
    print("\nApproach 3: Vue event trigger...")
    driver.execute_script("""
        const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
        const cells = rows[0].querySelectorAll('td .cell');
        const lastCell = cells[cells.length - 1];
        const btn = lastCell.querySelectorAll('button')[0];

        // Try accessing Vue instance
        const vueInstance = btn.__vue__ || btn.__vueParentComponent || btn._vnode;
        if (vueInstance) {
            return 'vue_found: ' + Object.keys(vueInstance).join(',');
        }
        // Try finding Vue event listeners
        const listeners = btn.__events || btn._listeners || btn.__listeners;
        if (listeners) {
            return 'listeners: ' + JSON.stringify(listeners);
        }
        return 'no_vue_found';
    """)
    after3 = driver.execute_script("return {url: window.location.href, hash_changes: window.__hash_changes};")
    print(f"  Result: {json.dumps(after3, ensure_ascii=False)}")

    # Check if we have any URL/routing change at all
    current_hash = driver.execute_script("return window.location.hash;")
    print(f"\n  Final hash: {current_hash}")
    print(f"  All hash changes: {driver.execute_script('return window.__hash_changes;')}")

    # Final approach: just check if there's a network tab or console error
    print("\nChecking browser console for errors...")
    try:
        logs = driver.get_log('browser')
        for entry in logs[-10:]:
            print(f"  [{entry['level']}] {entry['message'][:200]}")
    except:
        print("  (no browser log access)")

finally:
    base.close_browser()
