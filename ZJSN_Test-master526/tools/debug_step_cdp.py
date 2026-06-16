"""Try CDP Input.dispatchMouseEvent for real native click"""
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
    nav._navigate_by_js_hash("#/system/workflow/approval-chain", "debug-cdp")
    time.sleep(4)

    # Get button position
    rect = driver.execute_script("""
        const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
        const cells = rows[0].querySelectorAll('td .cell');
        const lastCell = cells[cells.length - 1];
        const btn = lastCell.querySelectorAll('button')[0];
        const r = btn.getBoundingClientRect();
        return {x: r.left + r.width/2, y: r.top + r.height/2, width: r.width, height: r.height};
    """)
    print(f"Button position: {json.dumps(rect)}")

    # Install monitors
    driver.execute_script("""
        window.__hash_changes = [];
        window.addEventListener('hashchange', () => window.__hash_changes.push(window.location.hash));
    """)

    # Use CDP to send real mouse events
    print("Sending CDP mouse events...")
    try:
        # mousePressed
        driver.execute_cdp_cmd('Input.dispatchMouseEvent', {
            'type': 'mousePressed',
            'x': rect['x'],
            'y': rect['y'],
            'button': 'left',
            'clickCount': 1
        })
        time.sleep(0.1)
        # mouseReleased
        driver.execute_cdp_cmd('Input.dispatchMouseEvent', {
            'type': 'mouseReleased',
            'x': rect['x'],
            'y': rect['y'],
            'button': 'left',
            'clickCount': 1
        })
        print("  CDP click sent")
    except Exception as e:
        print(f"  CDP failed: {e}")

        # Fallback: try pyautogui-style coordinate click via JS
        print("\n  Fallback: pointerEvent via JS...")
        driver.execute_script("""
            const rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
            const btn = rows[0].querySelectorAll('td .cell')[6].querySelectorAll('button')[0];
            const rect = btn.getBoundingClientRect();
            // Create and dispatch PointerEvent (what real touch/mouse actually sends)
            const ptrDown = new PointerEvent('pointerdown', {
                bubbles: true, cancelable: true,
                clientX: rect.left + rect.width/2,
                clientY: rect.top + rect.height/2,
                pointerId: 1, pointerType: 'mouse',
                isPrimary: true, button: 0, buttons: 1
            });
            const ptrUp = new PointerEvent('pointerup', {
                bubbles: true, cancelable: true,
                clientX: rect.left + rect.width/2,
                clientY: rect.top + rect.height/2,
                pointerId: 1, pointerType: 'mouse',
                isPrimary: true, button: 0, buttons: 0
            });
            btn.dispatchEvent(ptrDown);
            btn.dispatchEvent(ptrUp);
        """)

    time.sleep(3)

    # Check what happened
    result = driver.execute_script("""
        return {
            url: window.location.href,
            hash: window.location.hash,
            hash_changes: window.__hash_changes,
            dialogs: document.querySelectorAll('.el-dialog:not([style*="display: none"])').length,
            drawers: document.querySelectorAll('.el-drawer:not([style*="display: none"])').length,
            // Check for any visible modal/panel
            panels: Array.from(document.querySelectorAll('[class*="step"], [class*="panel"], [class*="drawer"]'))
                .filter(el => el.offsetParent !== null)
                .map(el => el.className.substring(0, 80)),
            body_snippet: document.body.textContent.trim().substring(0, 300)
        };
    """)
    print(f"\nResult: {json.dumps(result, ensure_ascii=False, indent=2)}")

    # Also check if there's a route-level change
    # maybe the Vue Router pushed to a new route
    vue_route = driver.execute_script("""
        const app = document.querySelector('#app');
        if (app && app.__vue__) return JSON.stringify(app.__vue__.$route);
        if (app && app.__vue_app__) return 'has_vue_app';
        return 'no_vue_found';
    """)
    print(f"Vue route: {vue_route}")

finally:
    base.close_browser()
