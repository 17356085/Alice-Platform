"""Final role assignment using PUT /api/system/role/{id}/users"""
import sys, json, time
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in

base = BaseDriver()
d = base.open_browser()
ensure_logged_in(d)
time.sleep(2)

def api(method, path, body=None):
    d.set_script_timeout(20)
    js = ''
    if body is not None:
        js = 'body: JSON.stringify(%s),' % json.dumps(body, ensure_ascii=False)
    try:
        result = d.execute_script('''
            return fetch("https://aiwechatminidemo.cimc-digital.com''' + path + '''", {
                method: "''' + method + '''",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + JSON.parse(
                        decodeURIComponent(document.cookie.split("authorized-token=")[1].split(";")[0])
                    ).accessToken
                },
                ''' + js + '''
            }).then(function(r) { return r.json(); });
        ''')
        return result
    except Exception as e:
        return {"code": -1, "error": str(e)}

# Get role IDs
rl = api("GET", "/api/system/role/list?pageNum=1&pageSize=100")
rm = {}
recs = rl.get("data", rl).get("records", [])
for r in recs:
    rn = r.get("roleName", "")
    if rn.startswith("RBAC-"):
        rm[rn] = r["id"]
print("Roles:", json.dumps(rm, ensure_ascii=False))

# Get user IDs
ul = api("GET", "/api/system/user/list?pageNum=1&pageSize=20&username=rbac_test")
um = {}
for u in ul.get("data", ul).get("records", []):
    um[u["username"]] = u["id"]
print("Users:", list(um.keys()))

# Assign roles
pairs = [
    ("rbac_test_sys", "RBAC-SYS-ONLY"),
    ("rbac_test_full", "RBAC-ALL"),
    ("rbac_test_equip", "RBAC-EQUIP-ONLY"),
    ("rbac_test_mix", "RBAC-MIXED"),
    ("rbac_test_hr", "RBAC-HR-ONLY"),
    ("rbac_test_none", "RBAC-NONE"),
    ("rbac_test_ro", "RBAC-READONLY"),
]

for uname, rname in pairs:
    uid = um.get(uname)
    rid = rm.get(rname)
    if not uid or not rid:
        print("SKIP %s -> %s (uid=%s, rid=%s)" % (uname, rname, uid, rid))
        continue
    resp = api("PUT", "/api/system/role/%s/users" % rid, [uid])
    code = resp.get("code", -1)
    ok = "OK" if code in (200, 0) else "FAIL"
    msg = resp.get("message", "")[:60]
    print("%s %s -> %s (code=%s %s)" % (ok, uname, rname, code, msg))
    time.sleep(0.3)

# Clear cache
from base.sidebar_navigator import SidebarNavigator
from page.system_page.RoleManagePage import RoleManagePage
nav = SidebarNavigator(d)
nav._navigate_by_js_hash('#/system/role', 'cache_clear')
time.sleep(3)
rp = RoleManagePage(d)
rp.wait_vue_stable()
rp.click_clear_cache()
time.sleep(1)
print("Cache cleared")

d.quit()
print("Done")
