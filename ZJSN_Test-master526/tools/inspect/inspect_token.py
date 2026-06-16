"""Inspect what token/credential keys exist in browser storage after login"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in

base = BaseDriver()
driver = None
try:
    driver = base.open_browser()
    ensure_logged_in(driver)

    # Check localStorage
    ls = driver.execute_script("""
        var result = {};
        for (var i = 0; i < localStorage.length; i++) {
            var key = localStorage.key(i);
            var val = localStorage.getItem(key);
            if (typeof val === 'string' && val.length > 100) val = val.substring(0, 80) + '...(' + val.length + ' chars)';
            result[key] = val || '(empty)';
        }
        return result;
    """)
    print("localStorage keys:")
    for k, v in ls.items():
        print(f"  {k} = {v}")

    # Check sessionStorage
    ss = driver.execute_script("""
        var result = {};
        for (var i = 0; i < sessionStorage.length; i++) {
            var key = sessionStorage.key(i);
            var val = sessionStorage.getItem(key);
            if (typeof val === 'string' && val.length > 100) val = val.substring(0, 80) + '...(' + val.length + ' chars)';
            result[key] = val || '(empty)';
        }
        return result;
    """)
    print("\nsessionStorage keys:")
    for k, v in ss.items():
        print(f"  {k} = {v}")

    # Check cookies
    cookies = driver.get_cookies()
    print(f"\nCookies ({len(cookies)}):")
    for c in cookies:
        print(f"  {c['name']} = {c['value'][:60] if len(c['value'])>60 else c['value']}")

    # Check if there's a Pinia store
    pinia = driver.execute_script("return window.__pinia || document.querySelector('#pinia') || '';")
    print(f"\nPinia store: {pinia}")

finally:
    if driver:
        try: driver.quit()
        except: pass
