"""Dual-browser: admin API + cache clear, target verify sidebar"""
import sys, time, json
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.RoleManagePage import RoleManagePage
from page.system_page.LoginPage import LoginPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

def api(d, method, path, body=None):
    d.set_script_timeout(20)
    js = ''
    if body is not None:
        js = 'body: JSON.stringify(%s),' % json.dumps(body, ensure_ascii=False)
    return d.execute_script('''
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

# ---- Browser 1: Admin ----
print("Opening admin browser...")
b1 = BaseDriver()
d1 = b1.open_browser()
d1.maximize_window()
ensure_logged_in(d1)
time.sleep(2)
print("[Admin] Logged in")

# API: assign rbac_test_sys to RBAC-SYS-ONLY
rl = api(d1, "GET", "/api/system/role/list?pageNum=1&pageSize=50")
rid = None
for r in rl.get("data", rl).get("records", []):
    if r.get("roleName") == "RBAC-SYS-ONLY":
        rid = r["id"]
        break

ul = api(d1, "GET", "/api/system/user/list?pageNum=1&pageSize=5&username=rbac_test_sys")
uid = None
for u in ul.get("data", ul).get("records", []):
    uid = u["id"]
    break

print("[Admin] Role %s -> User %s" % (rid, uid))

resp = api(d1, "PUT", "/api/system/role/%s/users" % rid, [uid])
print("[Admin] Assign: code=%s" % resp.get("code"))

# Navigate and clear cache
nav = SidebarNavigator(d1)
nav._navigate_by_js_hash('#/system/role', 'cache')
time.sleep(3)
rp = RoleManagePage(d1)
rp.wait_vue_stable()
rp.click_clear_cache()
time.sleep(2)
print("[Admin] Cache cleared")

# ---- Browser 2: rbac_test_sys ----
print("Opening target browser...")
b2 = BaseDriver()
d2 = b2.open_browser()
d2.maximize_window()
d2.get("https://aiwechatminidemo.cimc-digital.com/")
try:
    WebDriverWait(d2, 10).until(lambda x: x.execute_script("return document.readyState") == "complete")
except:
    pass
time.sleep(2)

lp = LoginPage(d2)
lp.input_username("rbac_test_sys")
lp.input_password("Ajyl@2026")
btns = d2.find_elements(By.XPATH, "//button[.//span[contains(.,'登')]]")
if btns:
    btns[0].click()
else:
    d2.execute_script("document.querySelector('.el-button--primary').click();")
try:
    WebDriverWait(d2, 15).until(lambda x: "#/login" not in (x.current_url or ""))
except:
    pass
lp.wait_vue_stable()
time.sleep(3)
print("[Target] Logged in")

# Check sidebar
menus = d2.execute_script("""
    var m = [];
    document.querySelectorAll('.el-menu > li.el-sub-menu > .el-sub-menu__title span')
        .forEach(function(s) { var t = (s.innerText || '').trim(); if (t) m.push(t); });
    document.querySelectorAll('.el-menu > li.el-menu-item span')
        .forEach(function(s) { var t = (s.innerText || '').trim(); if (t) m.push(t); });
    return m;
""")
print("[Target] SIDEBAR (%d): %s" % (len(menus), menus))

# Check JWT
try:
    import base64 as b64
    token = d2.execute_script("""
        var c = document.cookie.split(";").find(function(s) { return s.indexOf("authorized-token") !== -1; });
        if (!c) return null;
        return decodeURIComponent(c.split("=")[1]);
    """)
    if token:
        td = json.loads(token)
        at = td.get("accessToken", "")
        parts = at.split(".")
        if len(parts) >= 2:
            p = parts[1] + "=" * (4 - len(parts[1]) % 4)
            j = json.loads(b64.b64decode(p))
            print("[Target] JWT perms=%d roles=%s" % (len(j.get("permissions", [])), j.get("roles", "MISSING")))
except Exception as e:
    print("[Target] JWT error: %s" % e)

d1.quit()
d2.quit()
print("Done")
