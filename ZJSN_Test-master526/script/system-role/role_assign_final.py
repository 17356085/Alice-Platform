"""最终：用 Python requests 分配角色 + 每个角色只用一个 ID"""
import requests, json, time

BASE = 'https://aiwechatminidemo.cimc-digital.com'
s = requests.Session()
r = s.post(f'{BASE}/api/auth/login', json={'username':'admin','password':'Ajyl@2026'}, timeout=30)
token = r.json().get('data',{}).get('accessToken')
h = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# Get roles - pick unique name -> ID mapping (prefer newer IDs)
rl = s.get(f'{BASE}/api/system/role/list', headers=h, timeout=30)
name_to_id = {}
seen_names = set()
for rec in rl.json().get('data',{}).get('records',[]):
    name = rec.get('roleName','')
    rid = rec.get('roleId') or rec.get('id')
    if 'RBAC-' in name:
        name_to_id[name] = rid  # Last write wins = highest ID = newest
        if name in seen_names:
            print(f"  DUPLICATE {name}: keeping id={rid}, will delete old one")
        seen_names.add(name)

print(f"Role IDs (latest): {json.dumps(name_to_id, ensure_ascii=False)}")

# Delete OLD duplicates (keep newest)
for rec in rl.json().get('data',{}).get('records',[]):
    name = rec.get('roleName','')
    rid = rec.get('roleId') or rec.get('id')
    if 'RBAC-' in name and rid != name_to_id[name]:
        resp = s.delete(f'{BASE}/api/system/role/{rid}', headers=h, timeout=30)
        print(f"  Delete old {name}(id={rid}): {resp.json().get('message','')[:50]}")
        time.sleep(1.5)

# Map users to roles
user_role = [
    (386, 47, "rbac_test_full->RBAC-全权限(id=47)"),
    (387, 44, "rbac_test_sys->RBAC-仅系统管理(id=44)"),
    (388, 45, "rbac_test_equip->RBAC-仅设备管理(id=45)"),
    (389, 46, "rbac_test_hr->RBAC-仅人员管理(id=46)"),
    (390, 41, "rbac_test_mix->RBAC-混合权限(id=41)"),
]

print("\nAssigning roles...")
for uid, rid, desc in user_role:
    for attempt in range(3):
        try:
            resp = s.put(f'{BASE}/api/system/user/role',
                        json={'userId': uid, 'roleIds': [rid]},
                        headers=h, timeout=60)
            j = resp.json()
            code = j.get('code', -1)
            msg = j.get('message', '')
            if code in (200, 0):
                print(f"  OK {desc}")
                break
            else:
                print(f"  FAIL {desc}: {msg[:60]} (attempt {attempt+1})")
                from time import sleep as _s; _s(2)
        except Exception as e:
            print(f"  RETRY {desc}: {str(e)[:60]} (attempt {attempt+1})")
            from time import sleep as _s; _s(2)

# Final verification — wait for eventual consistency
from time import sleep as _s; _s(1)
ul = s.get(f'{BASE}/api/system/user/list?pageNum=1&pageSize=50', headers=h, timeout=30)
for u in ul.json().get('data',{}).get('records',[]):
    un = u.get('username','')
    if 'rbac_test_' in un:
        print(f"  {un:20s} roleIds={u.get('roleIds',[])}")
