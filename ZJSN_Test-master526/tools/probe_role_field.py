"""Quick probe: find the correct field name for user-role assignment"""
import sys, json, time
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in

base = BaseDriver()
d = base.open_browser()
ensure_logged_in(d)
time.sleep(2)

def api(method, path, body=None):
    d.set_script_timeout(30)
    js_body = ''
    if body:
        js_body = 'body: JSON.stringify(%s),' % json.dumps(body, ensure_ascii=False)
    script = '''
        return fetch("https://aiwechatminidemo.cimc-digital.com''' + path + '''", {
            method: "''' + method + '''",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + JSON.parse(
                    decodeURIComponent(document.cookie.split("authorized-token=")[1].split(";")[0])
                ).accessToken
            },
            ''' + js_body + '''
        }).then(function(r) { return r.json(); });
    '''
    return d.execute_script(script)

# Get dept
dl = api("GET", "/api/system/dept/list")
ddata = dl.get("data", dl)
dept_id = 1
if isinstance(ddata, list) and ddata:
    dept_id = ddata[0].get("deptId") or ddata[0].get("id", 1)

# Find RBAC-SYS-ONLY role ID
rl = api("GET", "/api/system/role/list?pageNum=1&pageSize=50")
for r in rl.get("data", rl).get("records", []):
    if r.get("roleName") == "RBAC-SYS-ONLY":
        rid = r["id"]
        now = int(time.time())

        for role_field in ["roleIds", "roleIdList", "roleList", "roles", "roleId"]:
            body = {
                "username": "rbac_probe_" + role_field,
                "name": "Probe " + role_field,
                "realName": "Probe " + role_field,
                "password": "Ajyl@2026",
                "confirmPassword": "Ajyl@2026",
                "phone": "138" + str(now)[-8:],
                "phonenumber": "138" + str(now)[-8:],
                "deptId": dept_id,
                "status": "1",
                "userType": "1",
            }
            body[role_field] = [rid]

            resp = api("POST", "/api/system/user", body)
            code = resp.get("code", -1)
            msg = resp.get("message", "")
            print("%s: code=%s msg=%s" % (role_field, code, msg[:80]))

            if code in (200, 0):
                time.sleep(1)
                ul = api("GET", "/api/system/user/list?pageNum=1&pageSize=5&username=rbac_probe_" + role_field)
                recs = ul.get("data", ul).get("records", [])
                for u in recs:
                    print("  -> roleIds=%s" % u.get("roleIds", "MISSING"))
                # Cleanup
                for u in recs:
                    api("DELETE", "/api/system/user/%s" % u["id"])
        break

d.quit()
