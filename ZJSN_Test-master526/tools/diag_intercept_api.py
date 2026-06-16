"""Intercept page's real API calls to find approval chain endpoints"""
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
    # Install fetch interceptor BEFORE navigating
    driver.execute_script("""
        window.__captured_requests = [];
        const origFetch = window.fetch;
        window.fetch = function(...args) {
            const url = typeof args[0] === 'string' ? args[0] : args[0].url;
            if (url && url.includes('/api/')) {
                return origFetch.apply(this, args).then(r => {
                    const clone = r.clone();
                    clone.text().then(t => {
                        window.__captured_requests.push({
                            method: args[1]?.method || 'GET',
                            url: url,
                            status: r.status,
                            response_preview: t.substring(0, 500)
                        });
                    });
                    return r;
                });
            }
            return origFetch.apply(this, args);
        };
    """)

    ensure_logged_in(driver)
    nav = SidebarNavigator(driver)
    nav._navigate_by_js_hash("#/system/workflow/approval-chain", "diag-intercept")
    time.sleep(5)

    # Get captured requests
    requests = driver.execute_script("return window.__captured_requests;")
    print("\n=== Captured API requests ===")
    for req in requests:
        print(f"  {req['method']} {req['url']} -> {req['status']}")
        if req['response_preview']:
            print(f"    response: {req['response_preview'][:200]}")

    # Now try: get token and call the SAME endpoint the page uses
    token = driver.execute_script("""
        const c = document.cookie.split(';').find(c => c.trim().startsWith('authorized-token='));
        if (!c) return null;
        return JSON.parse(decodeURIComponent(c.split('=')[1])).accessToken;
    """)

    # Find the list endpoint from captured requests
    list_url = None
    for req in requests:
        if 'chain' in req.get('url', '') or 'approval' in req.get('url', ''):
            list_url = req['url']
            break

    if list_url and token:
        print(f"\n=== Re-calling list endpoint ===")
        print(f"URL: {list_url}")
        resp = driver.execute_script("""
            return fetch(arguments[0], {
                headers: {'Authorization': 'Bearer ' + arguments[1]}
            }).then(r => r.json());
        """, list_url, token)
        print(json.dumps(resp, ensure_ascii=False, indent=2)[:3000])

finally:
    base.close_browser()
