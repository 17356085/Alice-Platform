"""Verify menus have type=3 IDs, assign user to role, test sidebar"""
import sys, time, json
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.RoleManagePage import RoleManagePage
from page.system_page.LoginPage import LoginPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

PWD = "Ajyl@2026"

base = BaseDriver()
d = base.open_browser()
d.maximize_window()
ensure_logged_in(d)
time.sleep(2)

def api(method, path, body=None):
    d.set_script_timeout(20)
    js = ''
    if body is not None:
        js = 'body: JSON.stringify(%s),' % json.dumps(body, ensure_ascii=False)
    return d.execute_script('''
        return fetch("https://aiwechatminidemo.cimc-digital.com''' + path + '''", {
            method: "''' + method + '''",
            headers: { "Content-Type": "application/json",
                "Authorization": "Bearer " + JSON.parse(
                    decodeURIComponent(document.cookie.split("authorized-token=")[1].split(";")[0])
                ).accessToken },
            ''' + js + '''
        }).then(function(r) { return r.json(); });
    ''')

# Get RBAC-SYS-ONLY menus and count type=3
rl = api("GET", "/api/system/role/list?pageNum=1&pageSize=50")
rid = uid = None
for r in rl.get("data", rl).get("records", []):
    if r.get("roleName") == "RBAC-SYS-ONLY":
        rid = r["id"]
        break

# Get all menus for mapping
mr = api("GET", "/api/system/menu/list?pageNum=1&pageSize=500")
all_menus = mr.get("data", mr).get("records", [])

# Get role's saved menu IDs
role_menus = api("GET", "/api/system/role/%s/menus" % rid)
saved_ids = role_menus.get("data", role_menus)
type_counts = {"1": 0, "2": 0, "3": 0}
for m in all_menus:
    if m["id"] in saved_ids:
        t = str(m.get("menuType", "?"))
        type_counts[t] = type_counts.get(t, 0) + 1
print("RBAC-SYS-ONLY menus: total=%d, type1=%d, type2=%d, type3=%d" % (
    len(saved_ids), type_counts.get("1", 0), type_counts.get("2", 0), type_counts.get("3", 0)))

# Get/Create user
ul = api("GET", "/api/system/user/list?pageNum=1&pageSize=5&username=rbac_test_sys")
for u in ul.get("data", ul).get("records", []):
    uid = u["id"]
if not uid:
    print("rbac_test_sys not found, creating...")
    dl = api("GET", "/api/system/dept/list")
    dd = dl.get("data", dl)
    dept_id = dd[0].get("deptId") or dd[0].get("id", 1) if isinstance(dd, list) and dd else 1
    now = int(time.time())
    resp = api("POST", "/api/system/user", {
        "username": "rbac_test_sys", "name": "SYS", "realName": "SYS",
        "password": PWD, "confirmPassword": PWD,
        "phone": "138%s" % str(now)[-8:], "phonenumber": "138%s" % str(now)[-8:],
        "deptId": dept_id, "status": "1", "userType": "1", "roleIds": [rid]
    })
    print("Create user: code=%s" % resp.get("code"))
    time.sleep(0.5)
    ul2 = api("GET", "/api/system/user/list?pageNum=1&pageSize=5&username=rbac_test_sys")
    for u in ul2.get("data", ul2).get("records", []):
        uid = u["id"]

print("User ID: %s, Role ID: %s" % (uid, rid))

# Assign user to role (in case not already)
resp = api("PUT", "/api/system/role/%s/users" % rid, [uid])
print("Assign: code=%s" % resp.get("code"))

# Clear cache via UI
nav = SidebarNavigator(d)
nav._navigate_by_js_hash('#/system/role', 'cache')
time.sleep(3)
rp = RoleManagePage(d)
rp.wait_vue_stable()
rp.click_clear_cache()
time.sleep(2)
print("Cache cleared")

# Login as rbac_test_sys
d.get("https://aiwechatminidemo.cimc-digital.com/")
time.sleep(3)
lp = LoginPage(d)
lp.input_username("rbac_test_sys")
lp.input_password(PWD)
btns = d.find_elements(By.XPATH, "//button[.//span[contains(.,'登')]]")
if btns: btns[0].click()
else: d.execute_script("document.querySelector('.el-button--primary').click();")
try: WebDriverWait(d, 15).until(lambda x: "#/login" not in (x.current_url or ""))
except: pass
lp.wait_vue_stable()
time.sleep(3)

menus = d.execute_script("""
var m = [];
document.querySelectorAll('.el-menu > li.el-sub-menu > .el-sub-menu__title span')
    .forEach(function(s) { var t = (s.innerText || '').trim(); if (t) m.push(t); });
    document.querySelectorAll('.el-menu > li.el-menu-item span')
    .forEach(function(s) { var t = (s.innerText || '').trim(); if (t) m.push(t); });
return m;
""")
print("SIDEBAR (%d): %s" % (len(menus), menus))

# Check routes API
routes = d.execute_script("""
return fetch("https://aiwechatminidemo.cimc-digital.com/api/system/menu/routes", {
    headers: { "Authorization": "Bearer " + JSON.parse(
        decodeURIComponent(document.cookie.split("authorized-token=")[1].split(";")[0])
    ).accessToken }
}).then(function(r) { return r.json(); });
""")
data = routes.get("data", routes)
count = len(data) if isinstance(data, list) else 0
print("Routes API: %d items" % count)

d.quit()
