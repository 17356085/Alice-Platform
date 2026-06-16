"""RBAC种子数据 — 使用浏览器 fetch API 创建角色和用户"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from page.system_page.UserManagePage import UserManagePage

PWD = "Ajyl@2026"

ROLES = [
    ("RBAC-全权限",    "rbac_full",    90, "RBAC测试-全权限"),
    ("RBAC-仅系统管理", "rbac_sys",     91, "RBAC测试-仅系统管理"),
    ("RBAC-仅设备管理", "rbac_equip",   92, "RBAC测试-仅设备管理"),
    ("RBAC-仅人员管理", "rbac_hr",      93, "RBAC测试-仅人员管理"),
    ("RBAC-混合权限",   "rbac_mix",     94, "RBAC测试-混合权限"),
    ("RBAC-零权限",    "rbac_none",    95, "RBAC测试-零权限"),
    ("RBAC-只读",      "rbac_readonly",96, "RBAC测试-只读"),
]

USERS = [
    ("rbac_test_full",   "RBAC全权限测试",   "rbac_full"),
    ("rbac_test_sys",    "RBAC系统管理测试", "rbac_sys"),
    ("rbac_test_equip",  "RBAC设备管理测试", "rbac_equip"),
    ("rbac_test_hr",     "RBAC人员管理测试", "rbac_hr"),
    ("rbac_test_mix",    "RBAC混合权限测试", "rbac_mix"),
    ("rbac_test_none",   "RBAC零权限测试",   "rbac_none"),
    ("rbac_test_ro",     "RBAC只读权限测试", "rbac_readonly"),
]

def fetch(driver, method, path, body=None):
    """通过浏览器 fetch 执行 API 调用（带超时）"""
    # Increase script timeout
    driver.set_script_timeout(60)
    if body:
        b = json.dumps(body, ensure_ascii=False)
        body_js = f"body: JSON.stringify({b})"
    else:
        body_js = ""
    return driver.execute_script(f"""
        return Promise.race([
            fetch('https://aiwechatminidemo.cimc-digital.com{path}', {{
                method: '{method}',
                headers: {{ 'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + JSON.parse(
                        decodeURIComponent(document.cookie.split('authorized-token=')[1].split(';')[0])
                    ).accessToken }},
                {body_js}
            }}).then(function(r) {{ return r.json(); }}),
            new Promise(function(_,reject) {{
                setTimeout(function() {{ reject(new Error('timeout')); }}, 45000);
            }})
        ]);
    """)

import json
import time

base = BaseDriver()
driver = None
try:
    driver = base.open_browser()
    ensure_logged_in(driver)
    time.sleep(2)

    # 1. Get existing roles
    rl = fetch(driver, "GET", "/api/system/role/list")
    data = rl.get('data', rl)
    records = data.get('records', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    existing_roles = {r.get('roleCode',''): (r.get('roleId') or r.get('id')) for r in records if isinstance(r, dict)}
    print(f"Existing: {list(existing_roles.keys())}")

    # 2. Create missing roles
    for name, code, order, desc in ROLES:
        if code in existing_roles:
            print(f"  OK {code} (id={existing_roles[code]})")
            continue
        r = fetch(driver, "POST", "/api/system/role", {
            "roleName": name, "roleCode": code, "roleSort": order, "remark": desc, "status": "1"
        })
        status = r.get('code', -1)
        print(f"  {'OK' if status in (200,0) else 'FAIL'} {code}: {r.get('message','')}")
        time.sleep(2)  # Avoid rate limiting

    # 3. Re-fetch role IDs
    rl2 = fetch(driver, "GET", "/api/system/role/list")
    data2 = rl2.get('data', rl2)
    records2 = data2.get('records', []) if isinstance(data2, dict) else (data2 if isinstance(data2, list) else [])
    role_ids = {r.get('roleCode',''): (r.get('roleId') or r.get('id')) for r in records2 if isinstance(r, dict)
                and r.get('roleCode','').startswith('rbac_')}
    print(f"Role IDs: {role_ids}")

    # 4. Get first deptId
    dl = fetch(driver, "GET", "/api/system/dept/list")
    ddata = dl.get('data', dl)
    dept_id = None
    if isinstance(ddata, dict):
        # Might be nested like {"group": [{"deptId": 1}, ...]}
        for v in ddata.values():
            if isinstance(v, list) and v and isinstance(v[0], dict) and v[0].get('deptId'):
                dept_id = v[0]['deptId']
                break
    if not dept_id and isinstance(ddata, list):
        for d in ddata:
            if d.get('deptId'):
                dept_id = d['deptId']
                break
    if not dept_id:
        # Try with records
        for v in ddata.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                for item in v:
                    if item.get('deptId'):
                        dept_id = item['deptId']
                        break
                if dept_id: break
    if not dept_id: dept_id = 1
    print(f"Dept ID: {dept_id}")

    # 5. Create users
    for username, name, role_code in USERS:
        # Check exists
        ul = fetch(driver, "GET", f"/api/system/user/list?username={username}&pageNum=1&pageSize=1")
        ud = ul.get('data', {})
        urecs = ud.get('records', []) if isinstance(ud, dict) else []
        if any(u.get('username') == username for u in urecs):
            print(f"  OK {username} (exists)")
            continue

        body = {"username": username, "name": name, "password": PWD, "confirmPassword": PWD,
                "phone": "138" + str(int(time.time()))[-8:], "deptId": dept_id, "status": "1",
                "realName": name, "userType": "员工"}
        rid = role_ids.get(role_code)
        if rid:
            body["roleIds"] = [rid]

        r = fetch(driver, "POST", "/api/system/user", body)
        status = r.get('code', -1)
        msg = r.get('message', r.get('msg', ''))
        print(f"  {'OK' if status in (200,0) else 'FAIL'} {username}: {msg}")
        if status not in (200, 0):
            print(f"    body: {json.dumps(body, ensure_ascii=False)[:200]}")
        time.sleep(0.5)

    print(f"\nDone! Roles: {list(role_ids.keys())}, Users: {[u[0] for u in USERS]}")

finally:
    if driver:
        try: driver.quit()
        except: pass
