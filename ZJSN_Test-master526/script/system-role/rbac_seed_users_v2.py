"""创建 RBAC 测试用户 — 已知 deptId=200 (人力行政部)"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in

PWD = "Ajyl@2026"
USERS = [
    ("rbac_test_full",   "RBAC全权限测试",   "rbac_full"),
    ("rbac_test_sys",    "RBAC系统管理测试", "rbac_sys"),
    ("rbac_test_equip",  "RBAC设备管理测试", "rbac_equip"),
    ("rbac_test_hr",     "RBAC人员管理测试", "rbac_hr"),
    ("rbac_test_mix",    "RBAC混合权限测试", "rbac_mix"),
    ("rbac_test_none",   "RBAC零权限测试",   "rbac_none"),
    ("rbac_test_ro",     "RBAC只读权限测试", "rbac_readonly"),
]

base = BaseDriver()
driver = base.open_browser()
ensure_logged_in(driver)
time.sleep(2)

# Get token
for c in driver.get_cookies():
    if c['name'] == 'authorized-token':
        import urllib.parse
        td = json.loads(urllib.parse.unquote(c['value']))
        token = td.get('accessToken')
        break

# Get role ID mapping
rl = driver.execute_script(f"""
    return fetch('https://aiwechatminidemo.cimc-digital.com/api/system/role/list',{{
        headers:{{'Authorization':'Bearer {token}'}}
    }}).then(r=>r.json());
""")
records = rl.get('data',{}).get('records',[])
role_ids = {r.get('roleCode'): (r.get('roleId') or r.get('id')) for r in records
            if r.get('roleCode','').startswith('rbac_')}
print(f"Role IDs: {role_ids}")

def api_post(path, data):
    return driver.execute_script(f"""
        return fetch('https://aiwechatminidemo.cimc-digital.com{path}',{{
            method:'POST',
            headers:{{'Content-Type':'application/json','Authorization':'Bearer {token}'}},
            body:JSON.stringify({json.dumps(data, ensure_ascii=False)})
        }}).then(r=>r.json());
    """)

# Create users
for username, name, role_code in USERS:
    print(f"User: {username}", end=" ")
    body = {
        "username": username, "name": name,
        "password": PWD, "confirmPassword": PWD,
        "phone": "138" + str(int(time.time()))[-8:],
        "deptId": 200,  # 人力行政部
        "status": "1"
    }
    rid = role_ids.get(role_code)
    if rid:
        body["roleIds"] = [rid]

    r = api_post("/api/system/user", body)
    code = r.get('code', -1)
    msg = r.get('message', r.get('msg', ''))
    if code in (200, 0):
        print(f"OK")
    elif "已存在" in msg or "已存在" in str(r):
        print(f"EXISTS")
    else:
        print(f"FAIL: {msg}")
        print(f"  {json.dumps(body, ensure_ascii=False)[:200]}")
        # Try with userType
        if "用户类型" in msg:
            body["userType"] = "员工"
            r2 = api_post("/api/system/user", body)
            print(f"  +userType: {r2.get('code')} {r2.get('message','')}")
    time.sleep(0.5)

print("\nDone!")
driver.quit()
