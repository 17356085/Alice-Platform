"""Try API approach to get approval chain step config + test if button navigates to new route"""
import os, sys, json, time, io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from selenium.webdriver.common.by import By

BASE = 'https://aiwechatminidemo.cimc-digital.com'

base = BaseDriver()
driver = base.open_browser()
try:
    ensure_logged_in(driver)
    nav = SidebarNavigator(driver)
    nav._navigate_by_js_hash("#/system/workflow/approval-chain", "diag-api")
    time.sleep(4)

    # Get token
    token = driver.execute_script("""
        const c = document.cookie.split(';').find(c => c.trim().startsWith('authorized-token='));
        if (!c) return null;
        const v = decodeURIComponent(c.split('=')[1]);
        try { return JSON.parse(v).accessToken; } catch(e) { return null; }
    """)
    print(f"Token found: {bool(token)}")

    # Get approval chain list via API
    chain_list = driver.execute_script("""
        return fetch(arguments[0] + '/api/system/approval/chain/list?pageNum=1&pageSize=20', {
            headers: {'Authorization': 'Bearer ' + arguments[1]}
        }).then(r => r.json());
    """, BASE, token)
    print("\n=== API: Chain list ===")
    print(json.dumps(chain_list, ensure_ascii=False, indent=2)[:2000])

    # Try getting steps for first chain
    records = chain_list.get('data', {}).get('records', [])
    if records:
        first_id = records[0].get('id') or records[0].get('chainId')
        print(f"\nFirst chain id: {first_id}")

        # Try various API patterns
        patterns = [
            f'/api/system/approval/chain/{first_id}',
            f'/api/system/approval/chain/{first_id}/steps',
            f'/api/system/approval/chain/steps/{first_id}',
            f'/api/system/workflow/chain/{first_id}',
            f'/api/system/workflow/chain/{first_id}/steps',
        ]
        for p in patterns:
            resp = driver.execute_script("""
                return fetch(arguments[0] + arguments[1], {
                    headers: {'Authorization': 'Bearer ' + arguments[2]}
                }).then(r => r.json());
            """, BASE, p, token)
            print(f"  {p}: {json.dumps(resp, ensure_ascii=False)[:300]}")

    # Also try navigating directly to potential step config URL
    print("\n=== Try direct URL navigation ===")
    hash_patterns = [
        "#/system/workflow/approval-chain/steps",
        "#/system/workflow/approval-chain/step",
        "#/system/workflow/approval-chain/detail",
    ]
    for hp in hash_patterns:
        driver.get(f"{BASE}/{hp}")
        time.sleep(2)
        body_text = driver.execute_script("return document.body.textContent.substring(0, 200);")
        print(f"  {hp}: {body_text[:100]}")

finally:
    base.close_browser()
