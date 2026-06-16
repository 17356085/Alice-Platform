"""Debug: test POST API call directly"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in

base = BaseDriver()
driver = None
try:
    driver = base.open_browser()
    ensure_logged_in(driver)

    # Test POST API via browser fetch
    result = driver.execute_script("""
        return fetch('https://aiwechatminidemo.cimc-digital.com/api/system/role', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + JSON.parse(
                    decodeURIComponent(
                        document.cookie.split('authorized-token=')[1].split(';')[0]
                    )
                ).accessToken
            },
            body: JSON.stringify({
                roleName: 'test-api-debug',
                roleCode: 'test_api_debug_' + Date.now(),
                roleSort: 99,
                status: '1'
            })
        }).then(function(r) { return r.json(); }).then(function(d) {
            return JSON.stringify(d);
        }).catch(function(e) { return 'ERROR: ' + e.message; });
    """)
    print("POST result:")
    print(result)

    # Clean up: delete the test role
    role_name = "test-api-debug"
    print(f"\nAttempting to delete {role_name} via UI later...")

finally:
    if driver:
        try: driver.quit()
        except: pass
