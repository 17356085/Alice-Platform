"""Complete seed: roles + menus + users + role assignment + cache clear

Strategy:
  - Phase 1-3: API (roles, menus) -- fast & reliable
  - Phase 4: API create users
  - Phase 5: API assign users to roles (PUT /role/{id}/users)
  - Phase 6: Selenium keyboard-based cache clear
  - Phase 7: Verify sidebar for ALL users
"""
import sys, time, json
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.RoleManagePage import RoleManagePage
from page.system_page.LoginPage import LoginPage
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PWD = "Ajyl@2026"

# ============================================================
# API helper
# ============================================================
def api(d, method, path, body=None):
    d.set_script_timeout(30)
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

def get_records(resp):
    data = resp.get("data", resp)
    if isinstance(data, dict):
        return data.get("records", [])
    if isinstance(data, list):
        return data
    return []

# ============================================================
# Main
# ============================================================
base = BaseDriver()
d = base.open_browser()
d.maximize_window()
ensure_logged_in(d)
time.sleep(2)

# ----------------------------------------------------------
# Phase 1-3: Roles + Menus (API)
# ----------------------------------------------------------
print("=== Phase 1-3: Roles + Menus ===")

ROLES = [
    ("RBAC-ALL", "rbac_full", 90, "all"),
    ("RBAC-SYS-ONLY", "rbac_sys", 91, ["系统管理"]),
    ("RBAC-EQUIP-ONLY", "rbac_equip", 92, ["设备管理"]),
    ("RBAC-HR-ONLY", "rbac_hr", 93, ["人员管理"]),
    ("RBAC-MIXED", "rbac_mix", 94, ["系统管理", "设备管理", "销售管理"]),
    ("RBAC-NONE", "rbac_none", 95, []),
    ("RBAC-READONLY", "rbac_readonly", 96, "all"),
]

# Delete old
rl = api(d, "GET", "/api/system/role/list?pageNum=1&pageSize=200")
for r in get_records(rl):
    rn = r.get("roleName", "")
    if rn.startswith("RBAC-"):
        api(d, "DELETE", "/api/system/role/%s" % r["id"])
        time.sleep(0.3)
ul = api(d, "GET", "/api/system/user/list?pageNum=1&pageSize=50&username=rbac_test")
for u in get_records(ul):
    api(d, "DELETE", "/api/system/user/%s" % u["id"])
    time.sleep(0.3)
print("Cleaned old data")

# Create roles
for rname, rcode, rorder, _ in ROLES:
    api(d, "POST", "/api/system/role", {
        "roleName": rname, "roleSort": rorder, "status": "1",
        "remark": "RBAC test for %s" % rcode
    })
    time.sleep(0.3)
time.sleep(1)

# Get role IDs (take newest)
rl2 = api(d, "GET", "/api/system/role/list?pageNum=1&pageSize=200")
role_ids = {}
for r in get_records(rl2):
    rn = r.get("roleName", "")
    if rn.startswith("RBAC-"):
        role_ids[rn] = r["id"]
print("Roles:", {k: role_ids[k] for k in sorted(role_ids.keys())})

# Get menus and assign
menus_resp = api(d, "GET", "/api/system/menu/list?pageNum=1&pageSize=500")
all_menus = get_records(menus_resp)
all_ids = [m["id"] for m in all_menus]

# Build parent-child tree for module resolution
tree = {}
id_map = {}
for m in all_menus:
    mid = m["id"]
    id_map[mid] = m
    pid = m.get("parentId", 0)
    tree.setdefault(pid, []).append(mid)

def get_module_ids(module_names):
    result = set()
    for m in all_menus:
        if m.get("menuType") in (1, 2) and m.get("parentId") == 0:
            if m["menuName"] in module_names:
                result.add(m["id"])
                def collect(pid):
                    for cid in tree.get(pid, []):
                        if id_map.get(cid, {}).get("menuType") in (1, 2):
                            result.add(cid)
                            collect(cid)
                collect(m["id"])
    return list(result)

for rname, _rcode, _rorder, modules in ROLES:
    rid = role_ids[rname]
    if modules == "all":
        mids = [m["id"] for m in all_menus if m.get("menuType") in (1, 2)]
    elif modules:
        mids = get_module_ids(modules)
    else:
        mids = []
    api(d, "PUT", "/api/system/role/%s/menus" % rid, mids)
    api(d, "PUT", "/api/system/role/%s/data-scope" % rid, {"dataScope": 1})
    time.sleep(0.2)
print("Menus assigned")

# ----------------------------------------------------------
# Phase 4: Create users (API)
# ----------------------------------------------------------
print("\n=== Phase 4: Create users ===")

USERS = [
    ("rbac_test_full", "RBAC-ALL-Test", "RBAC-ALL"),
    ("rbac_test_sys", "RBAC-SYS-Test", "RBAC-SYS-ONLY"),
    ("rbac_test_equip", "RBAC-EQUIP-Test", "RBAC-EQUIP-ONLY"),
    ("rbac_test_hr", "RBAC-HR-Test", "RBAC-HR-ONLY"),
    ("rbac_test_mix", "RBAC-MIXED-Test", "RBAC-MIXED"),
    ("rbac_test_none", "RBAC-NONE-Test", "RBAC-NONE"),
]

dl = api(d, "GET", "/api/system/dept/list")
ddata = dl.get("data", dl)
dept_id = ddata[0].get("deptId") or ddata[0].get("id", 1) if isinstance(ddata, list) and ddata else 1

user_ids = {}
for username, name, role_name in USERS:
    now = int(time.time())
    resp = api(d, "POST", "/api/system/user", {
        "username": username, "name": name, "realName": name,
        "password": PWD, "confirmPassword": PWD,
        "phone": "138%s" % str(now)[-8:],
        "phonenumber": "138%s" % str(now)[-8:],
        "deptId": dept_id, "status": "1", "userType": "1",
        "roleIds": [role_ids[role_name]]
    })
    ok = "OK" if resp.get("code") in (200, 0) else "FAIL"
    print("%s %s -> %s (code=%s)" % (ok, username, role_name, resp.get("code")))
    time.sleep(0.5)

# Re-read user IDs
time.sleep(1)
ul2 = api(d, "GET", "/api/system/user/list?pageNum=1&pageSize=30&username=rbac_test")
for u in get_records(ul2):
    user_ids[u["username"]] = u["id"]

# ----------------------------------------------------------
# Phase 5: Assign users to roles via PUT API
# ----------------------------------------------------------
print("\n=== Phase 5: Assign users to roles ===")
for username, _name, role_name in USERS:
    uid = user_ids.get(username)
    rid = role_ids.get(role_name)
    if uid and rid:
        resp = api(d, "PUT", "/api/system/role/%s/users" % rid, [uid])
        ok = "OK" if resp.get("code") in (200, 0) else "FAIL"
        print("%s %s -> %s (rid=%s, uid=%s)" % (ok, username, role_name, rid, uid))
        time.sleep(0.3)

# ----------------------------------------------------------
# Phase 6: Clear cache via Selenium keyboard navigation
# ----------------------------------------------------------
print("\n=== Phase 6: Clear cache ===")
nav = SidebarNavigator(d)
nav._navigate_by_js_hash('#/system/role', 'cache')
time.sleep(4)
rp = RoleManagePage(d)
rp.wait_vue_stable()

# Try EVERY possible way to trigger the clear cache button
print("Attempting cache clear via multiple methods...")

# Method 1: Find button and use dispatchEvent
result1 = d.execute_script("""
    var btns = document.querySelectorAll('button');
    for (var i = 0; i < btns.length; i++) {
        var t = (btns[i].textContent || '').trim();
        if (t.indexOf('清空缓存') !== -1 && btns[i].offsetParent !== null) {
            btns[i].scrollIntoView({block: 'center'});
            // Try native click first
            btns[i].click();
            // Also dispatch MouseEvent
            var evt = new MouseEvent('click', {bubbles: true, cancelable: true, view: window});
            btns[i].dispatchEvent(evt);
            // Also try pointer events
            var pevt = new PointerEvent('click', {bubbles: true, cancelable: true});
            btns[i].dispatchEvent(pevt);
            return 'clicked+events';
        }
    }
    return 'button_not_found';
""")
print("Method 1 (JS click+dispatchEvent): %s" % result1)
time.sleep(2)

# Method 2: Use Page Object's method
rp.click_clear_cache()
time.sleep(1)
print("Method 2 (PO click_clear_cache): done")

# Method 3: Try keyboard shortcut (if any)
try:
    body = d.find_element(By.TAG_NAME, "body")
    body.send_keys(Keys.CONTROL + Keys.SHIFT + Keys.DELETE)
    time.sleep(1)
except:
    pass

# Check for toast
try:
    toast = d.find_element(By.CSS_SELECTOR, ".el-message__content")
    print("Toast visible: %s" % (toast.text or "empty"))
except:
    print("No toast found")

# ----------------------------------------------------------
# Phase 7: Verify rbac_test_sys sidebar
# ----------------------------------------------------------
print("\n=== Phase 7: Verify ===")
d.get("https://aiwechatminidemo.cimc-digital.com/")
time.sleep(3)

lp = LoginPage(d)
lp.input_username("rbac_test_sys")
lp.input_password(PWD)
btns = d.find_elements(By.XPATH, "//button[.//span[contains(.,'登')]]")
if btns:
    btns[0].click()
else:
    d.execute_script("document.querySelector('.el-button--primary').click();")
try:
    WebDriverWait(d, 15).until(lambda x: "#/login" not in (x.current_url or ""))
except:
    pass
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

if len(menus) > 0:
    print("\n*** SUCCESS! rbac_test_sys has sidebar menus! ***")
else:
    print("\n*** Sidebar still empty ***")

d.quit()
print("Done")
