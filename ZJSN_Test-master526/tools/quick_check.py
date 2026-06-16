"""Quick check: what users exist right now?"""
import sys, time, json
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in

base = BaseDriver()
d = base.open_browser()
d.maximize_window()
ensure_logged_in(d)
time.sleep(2)

def api(path):
    d.set_script_timeout(15)
    return d.execute_script('''
        return fetch("https://aiwechatminidemo.cimc-digital.com''' + path + '''", {
            headers: { "Authorization": "Bearer " + JSON.parse(
                decodeURIComponent(document.cookie.split("authorized-token=")[1].split(";")[0])
            ).accessToken }
        }).then(function(r) { return r.json(); });
    ''')

# Users
resp = api("/api/system/user/list?pageNum=1&pageSize=100")
recs = resp.get("data", resp).get("records", [])
rbac_users = [u for u in recs if "rbac" in (u.get("username", "") or "").lower()]
print("RBAC users (%d):" % len(rbac_users))
for u in rbac_users:
    print("  %s (id=%s) roleIds=%s" % (u["username"], u["id"], u.get("roleIds", "?")))

# Roles
resp2 = api("/api/system/role/list?pageNum=1&pageSize=20")
roles = resp2.get("data", resp2).get("records", [])
print("\nRBAC roles:")
for r in roles:
    rn = r.get("roleName", "")
    if "RBAC" in rn or "rbac" in r.get("roleCode", ""):
        print("  %s (id=%s) code=%s" % (rn, r["id"], r.get("roleCode", "")))

d.quit()
