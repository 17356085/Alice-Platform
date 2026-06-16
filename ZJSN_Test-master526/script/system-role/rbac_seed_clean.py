#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RBAC seed data V2 — Clean old test data then recreate roles, users, permissions.

Architecture:
  1. API: delete old RBAC test roles and users
  2. API: create 7 fresh test roles
  3. UI (Selenium): assign permissions to each role
  4. API: create 7 fresh test users
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PWD = "Ajyl@2026"

ROLES = [
    ("RBAC-ALL",        "rbac_full",    90),
    ("RBAC-SYS-ONLY",   "rbac_sys",     91),
    ("RBAC-EQUIP-ONLY", "rbac_equip",   92),
    ("RBAC-HR-ONLY",    "rbac_hr",      93),
    ("RBAC-MIXED",      "rbac_mix",     94),
    ("RBAC-NONE",       "rbac_none",    95),
    ("RBAC-READONLY",   "rbac_readonly",96),
]

USERS = [
    ("rbac_test_full",   "RBAC-ALL-Test",       "RBAC-ALL"),
    ("rbac_test_sys",    "RBAC-SYS-Test",       "RBAC-SYS-ONLY"),
    ("rbac_test_equip",  "RBAC-EQUIP-Test",     "RBAC-EQUIP-ONLY"),
    ("rbac_test_hr",     "RBAC-HR-Test",        "RBAC-HR-ONLY"),
    ("rbac_test_mix",    "RBAC-MIXED-Test",     "RBAC-MIXED"),
    ("rbac_test_none",   "RBAC-NONE-Test",      "RBAC-NONE"),
    ("rbac_test_ro",     "RBAC-READONLY-Test",  "RBAC-READONLY"),
]


def fetch(driver, method, path, body=None):
    """Browser fetch API call (bypasses CORS/auth)"""
    driver.set_script_timeout(60)
    js_body = ("body: JSON.stringify(%s)" % json.dumps(body, ensure_ascii=False)) if body else ""
    return driver.execute_script("""
        return Promise.race([
            fetch('https://aiwechatminidemo.cimc-digital.com%s', {
                method: '%s',
                headers: { 'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + JSON.parse(
                        decodeURIComponent(document.cookie.split('authorized-token=')[1].split(';')[0])
                    ).accessToken },
                %s
            }).then(function(r) { return r.json(); }),
            new Promise(function(_,reject) {
                setTimeout(function() { reject(new Error('timeout')); }, 45000);
            })
        ]);
    """ % (path, method, js_body))


def get_records(resp):
    data = resp.get('data', resp)
    if isinstance(data, dict):
        return data.get('records', data.get('rows', []))
    if isinstance(data, list):
        return data
    return []


def nav_to_role_page(driver):
    from base.sidebar_navigator import SidebarNavigator
    nav = SidebarNavigator(driver)
    nav._navigate_by_js_hash('#/system/role', 'seed')
    time.sleep(3)


# ================================================================
base = BaseDriver()
driver = base.open_browser()
try:
    ensure_logged_in(driver)
    time.sleep(2)

    # ── Phase 1: Cleanup ────────────────────────────────────────
    print("=" * 50)
    print("[Phase 1] Cleaning old RBAC test data")
    print("=" * 50)

    rl = fetch(driver, "GET", "/api/system/role/list?pageNum=1&pageSize=200")
    for r in get_records(rl):
        rid = r.get('id')
        rname = r.get('roleName', '')
        rcode = r.get('roleCode', '')
        if rname.startswith('RBAC-') or rcode.startswith('rbac_'):
            resp = fetch(driver, "DELETE", "/api/system/role/%s" % rid)
            print("  DEL role [%s] %s -> code=%s" % (rid, rname, resp.get('code')))
            time.sleep(0.3)

    ul = fetch(driver, "GET", "/api/system/user/list?pageNum=1&pageSize=50&username=rbac_test")
    for u in get_records(ul):
        uid = u.get('id')
        uname = u.get('username', '')
        resp = fetch(driver, "DELETE", "/api/system/user/%s" % uid)
        print("  DEL user  [%s] %s -> code=%s" % (uid, uname, resp.get('code')))
        time.sleep(0.3)

    # ── Phase 2: Create roles ───────────────────────────────────
    print()
    print("=" * 50)
    print("[Phase 2] Creating roles")
    print("=" * 50)

    role_ids = {}
    for rname, rcode, rorder in ROLES:
        body = {"roleName": rname, "roleSort": rorder, "status": "1",
                "remark": "RBAC test for %s" % rcode}
        resp = fetch(driver, "POST", "/api/system/role", body)
        if resp.get('code') in (200, 0):
            print("  [OK] Role created: %s" % rname)
            time.sleep(0.5)
        else:
            print("  [FAIL] Role create %s: %s" % (rname, resp.get('message','')))

    time.sleep(1)
    rl2 = fetch(driver, "GET", "/api/system/role/list?pageNum=1&pageSize=200")
    for r in get_records(rl2):
        rname = r.get('roleName', '')
        for iname, _, _ in ROLES:
            if rname == iname:
                role_ids[iname] = r.get('id')
                print("  Role ID [%s] = %s" % (r.get('id'), rname))
                break

    if not role_ids:
        print("[FATAL] No role IDs found. Aborting.")
        raise SystemExit(1)

    # ── Phase 3: Assign permissions via UI ──────────────────────
    print()
    print("=" * 50)
    print("[Phase 3] Assigning permissions via UI")
    print("=" * 50)

    from page.system_role_page.RoleManagePage import RoleManagePage
    role_page = RoleManagePage(driver)
    nav_to_role_page(driver)

    for iname, (rname, _, _) in zip(role_ids.keys(), ROLES):
        print("\n  Role: %s" % rname)

        role_page.click_reset()
        time.sleep(0.5)
        role_page.input_role_name(rname)
        role_page.click_search()
        time.sleep(2)

        if role_page.get_table_row_count() == 0:
            print("  [SKIP] Role not found: %s" % rname)
            continue

        try:
            role_page.click_permission_by_role_name(rname)
        except Exception as e:
            print("  [FAIL] Cannot open permission dialog: %s" % e)
            continue
        time.sleep(2)

        if not role_page.click_permission_tab_pc():
            print("  [FAIL] Cannot switch to PC tab")
            role_page.click_permission_cancel()
            continue

        time.sleep(1)
        role_page.select_first_two_permission_checkboxes_in_active_tab()
        role_page.click_permission_confirm()
        print("  [OK] Permissions saved")
        time.sleep(1)

    # ── Phase 4: Create users ───────────────────────────────────
    print()
    print("=" * 50)
    print("[Phase 4] Creating users")
    print("=" * 50)

    dl = fetch(driver, "GET", "/api/system/dept/list")
    ddata = dl.get('data', dl)
    dept_id = 1
    if isinstance(ddata, list) and ddata:
        dept_id = ddata[0].get('deptId') or ddata[0].get('id', 1)

    for username, name, role_name in USERS:
        now = int(time.time())
        body = {
            "username": username,
            "name": name,
            "realName": name,
            "password": PWD,
            "confirmPassword": PWD,
            "phone": "138%s" % str(now)[-8:],
            "phonenumber": "138%s" % str(now)[-8:],
            "deptId": dept_id,
            "status": "1",
            "userType": "1",
        }
        rid = role_ids.get(role_name)
        if rid:
            body["roleIds"] = [rid]

        resp = fetch(driver, "POST", "/api/system/user", body)
        code = resp.get('code', -1)
        print("  %s %s (code=%s)" % ("[OK]" if code in (200,0) else "[FAIL]", username, code))
        time.sleep(0.5)

    print()
    print("=" * 50)
    print("[DONE] RBAC seed data created")
    print("  Roles: %d" % len(role_ids))
    print("  Users: %d" % len(USERS))
    print("=" * 50)

finally:
    if driver:
        try: driver.quit()
        except: pass
