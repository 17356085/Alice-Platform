"""Minimal verify: use existing RBAC-SYS-ONLY, assign perms, create user, check sidebar"""
import sys, time, json
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.RoleManagePage import RoleManagePage
from page.system_page.LoginPage import LoginPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

PWD = "Ajyl@2026"

def api(d, method, path, body=None):
    d.set_script_timeout(15)
    js = '' if body is None else 'body: JSON.stringify(%s),' % json.dumps(body, ensure_ascii=False)
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

base = BaseDriver()
d = base.open_browser()
d.maximize_window()
ensure_logged_in(d)
time.sleep(2)

# ====== Create role via API ======
# Delete old
rl = api(d, "GET", "/api/system/role/list?pageNum=1&pageSize=50")
for r in rl.get("data", rl).get("records", []):
    if r.get("roleName") == "RBAC-SYS-ONLY":
        api(d, "DELETE", "/api/system/role/%s" % r["id"])
        print("Deleted old role")

resp = api(d, "POST", "/api/system/role", {
    "roleName": "RBAC-SYS-ONLY", "roleSort": 91, "status": "1", "remark": "test"
})
time.sleep(1)

rl2 = api(d, "GET", "/api/system/role/list?pageNum=1&pageSize=50")
rid = None
for r in rl2.get("data", rl2).get("records", []):
    if r.get("roleName") == "RBAC-SYS-ONLY":
        rid = r["id"]
        print("Created RBAC-SYS-ONLY id=%s" % rid)
        break

if not rid:
    print("ERROR: role creation failed! Response: %s" % str(resp)[:200])
    d.quit()
    sys.exit(1)

# API: assign menus (all system管理 descendants including type=3)
menus_resp = api(d, "GET", "/api/system/menu/list?pageNum=1&pageSize=500")
all_menus = menus_resp.get("data", menus_resp).get("records", [])
tree = {}; id_map = {}
for m in all_menus:
    mid = m["id"]; id_map[mid] = m
    tree.setdefault(m.get("parentId", 0), []).append(mid)

def collect(pid, result):
    for cid in tree.get(pid, []):
        result.append(cid); collect(cid, result)

sys_mids = []
for m in all_menus:
    if m.get("menuName") == "系统管理" and m.get("menuType") == 1 and m.get("parentId") == 0:
        sys_mids.append(m["id"]); collect(m["id"], sys_mids)

api(d, "PUT", "/api/system/role/%s/menus" % rid, sys_mids)
api(d, "PUT", "/api/system/role/%s/data-scope" % rid, {"dataScope": 1})
print("API menus: %d IDs" % len(sys_mids))

# ====== UI: open permission dialog + save (triggers cache invalidation) ======
nav = SidebarNavigator(d)
nav._navigate_by_js_hash('#/system/role', 'role'); time.sleep(3)
rp = RoleManagePage(d); rp.wait_vue_stable()

# ====== Assign permissions via UI ======
rp.click_reset(); time.sleep(0.5)
rp.input_role_name("RBAC-SYS-ONLY"); rp.click_search(); rp.wait_table_ready(timeout=8)
rp.click_permission_by_role_name("RBAC-SYS-ONLY"); time.sleep(2)
rp.click_permission_tab_pc(); time.sleep(2)

# Expand and check
d.execute_script("""
var arrows = document.querySelectorAll('.perm-group__arrow');
for (var i=0; i<arrows.length; i++) { if (arrows[i].offsetParent) arrows[i].click(); }
""")
time.sleep(1)

cbs = d.find_elements(By.CSS_SELECTOR, '.el-dialog .el-checkbox')
clicked = 0
for cb in cbs:
    if clicked >= 15: break
    try:
        inp = cb.find_element(By.CSS_SELECTOR, 'input[type="checkbox"]')
        val = inp.get_attribute('value') or ''
        if val == 'on': continue
        if 'is-checked' in (cb.get_attribute('class') or ''): continue
        inner = cb.find_element(By.CSS_SELECTOR, '.el-checkbox__inner')
        if inner.is_displayed():
            d.execute_script("arguments[0].scrollIntoView({block:'center'});", inner)
            inner.click(); clicked += 1; time.sleep(0.15)
    except: continue
print("Checked %d perms" % clicked)

rp.click_permission_confirm()
msg = rp.wait_for_toast_text(timeout=6)
print("Perms saved: %s" % (msg or "no toast"))

# ====== Create user via API ======
dl = api(d, "GET", "/api/system/dept/list")
dd = dl.get("data", dl)
dept_id = dd[0].get("deptId") or dd[0].get("id", 1) if isinstance(dd, list) and dd else 1
now = int(time.time())

# Delete old user
ul = api(d, "GET", "/api/system/user/list?pageNum=1&pageSize=5&username=rbac_test_sys")
for u in ul.get("data", ul).get("records", []):
    api(d, "DELETE", "/api/system/user/%s" % u["id"])

resp = api(d, "POST", "/api/system/user", {
    "username": "rbac_test_sys", "name": "SYS", "realName": "SYS",
    "password": PWD, "confirmPassword": PWD,
    "phone": "138%s" % str(now)[-8:], "phonenumber": "138%s" % str(now)[-8:],
    "deptId": dept_id, "status": "1", "userType": "1", "roleIds": [rid]
})
print("Create user: code=%s" % resp.get("code"))

time.sleep(1)
ul2 = api(d, "GET", "/api/system/user/list?pageNum=1&pageSize=5&username=rbac_test_sys")
uid = None
for u in ul2.get("data", ul2).get("records", []):
    uid = u["id"]
api(d, "PUT", "/api/system/role/%s/users" % rid, [uid])
print("User %s -> Role %s" % (uid, rid))

# ====== Clear cache ======
rp.click_clear_cache(); time.sleep(2)
print("Cache cleared")

# ====== Verify (fresh browser) ======
d.quit()
from base.browser_driver import BaseDriver as BD
b2 = BD(); d2 = b2.open_browser(); d2.maximize_window()
d2.get("https://aiwechatminidemo.cimc-digital.com/")
WebDriverWait(d2, 10).until(lambda x: x.execute_script("return document.readyState") == "complete")
time.sleep(2)

lp = LoginPage(d2)
lp.input_username("rbac_test_sys"); lp.input_password(PWD)
btns = d2.find_elements(By.XPATH, "//button[.//span[contains(.,'登')]]")
if btns: btns[0].click()
else: d2.execute_script("document.querySelector('.el-button--primary').click();")
WebDriverWait(d2, 15).until(lambda x: "#/login" not in (x.current_url or ""))
lp.wait_vue_stable(); time.sleep(3)

menus = d2.execute_script("""
var m = [];
document.querySelectorAll('.el-menu > li.el-sub-menu > .el-sub-menu__title span')
    .forEach(function(s) { var t=(s.innerText||'').trim(); if(t)m.push(t); });
document.querySelectorAll('.el-menu > li.el-menu-item span')
    .forEach(function(s) { var t=(s.innerText||'').trim(); if(t)m.push(t); });
return m;
""")
print("SIDEBAR (%d): %s" % (len(menus), menus))
d2.quit()
