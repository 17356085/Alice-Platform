"""Verify role-user link persistence"""
import sys, json, time
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in

base = BaseDriver()
d = base.open_browser()
ensure_logged_in(d)
time.sleep(2)

def api(m, p, b=None):
    d.set_script_timeout(20)
    js = ''
    if b is not None:
        js = 'body: JSON.stringify(%s),' % json.dumps(b, ensure_ascii=False)
    return d.execute_script('''
        return fetch("https://aiwechatminidemo.cimc-digital.com''' + p + '''", {
            method: "''' + m + '''",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + JSON.parse(
                    decodeURIComponent(document.cookie.split("authorized-token=")[1].split(";")[0])
                ).accessToken
            },
            ''' + js + '''
        }).then(function(r) { return r.json(); });
    ''')

# Get current state
rl = api("GET", "/api/system/role/list?pageNum=1&pageSize=100")
for r in rl.get("data", rl).get("records", []):
    if r.get("roleName") == "RBAC-SYS-ONLY":
        rid = r["id"]
        print("Role RBAC-SYS-ONLY id=%d" % rid)

        # Read users
        resp = api("GET", "/api/system/role/%d/users" % rid)
        print("Users via GET /role/%d/users: code=%d" % (rid, resp.get("code", -1)))
        data = resp.get("data", resp)
        if isinstance(data, list):
            print("  Users: %s" % data)
            if len(data) == 0:
                print("  EMPTY! Role has no users.")
        elif isinstance(data, dict):
            records = data.get("records", [])
            print("  Users (records): %d -> %s" % (len(records), [u.get("username", u.get("userId", "?")) for u in records[:5]]))
        break

# Check user
ul = api("GET", "/api/system/user/list?pageNum=1&pageSize=10&username=rbac_test_sys")
for u in ul.get("data", ul).get("records", []):
    uid = u["id"]
    print("\nUser rbac_test_sys id=%d" % uid)
    # Try to read user detail
    ud = api("GET", "/api/system/user/%d" % uid)
    print("User detail keys: %s" % list(ud.get("data", ud).keys())[:15])
    rd = ud.get("data", ud).get("roleIds", "MISSING")
    print("roleIds: %s" % rd)

d.quit()
