"""Final seed: API everything + keyboard el-select for role assignment"""
import sys, time, json
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.UserManagePage import UserManagePage
from page.system_page.LoginPage import LoginPage
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains

PWD = "Ajyl@2026"

base = BaseDriver()
d = base.open_browser()
d.maximize_window()
ensure_logged_in(d)
time.sleep(2)

def api(method, path, body=None):
    d.set_script_timeout(30)
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
        }).then(r => r.json());
    ''')

# ---- Phase 1: Clean ----
print("Phase 1: Clean old data")
rl = api("GET", "/api/system/role/list?pageNum=1&pageSize=200")
for r in rl.get("data", rl).get("records", []):
    if r.get("roleName", "").startswith("RBAC-"):
        api("DELETE", "/api/system/role/%s" % r["id"]); time.sleep(0.2)
ul = api("GET", "/api/system/user/list?pageNum=1&pageSize=50&username=rbac_test")
for u in ul.get("data", ul).get("records", []):
    api("DELETE", "/api/system/user/%s" % u["id"]); time.sleep(0.2)
print("Clean done")

# ---- Phase 2: Create role + menus ----
print("Phase 2: Create RBAC-SYS-ONLY role + menus")
api("POST", "/api/system/role", {"roleName": "RBAC-SYS-ONLY", "roleSort": 91, "status": "1", "remark": "test"})
time.sleep(1)

rl2 = api("GET", "/api/system/role/list?pageNum=1&pageSize=50")
rid = None
for r in rl2.get("data", rl2).get("records", []):
    if r.get("roleName") == "RBAC-SYS-ONLY":
        rid = r["id"]
print("Role ID: %s" % rid)

# Get system管理 menus
resp = api("GET", "/api/system/menu/list?pageNum=1&pageSize=500")
menus = resp.get("data", resp).get("records", [])
tree = {}; id_map = {}
for m in menus:
    mid = m["id"]; id_map[mid] = m
    tree.setdefault(m.get("parentId", 0), []).append(mid)

def collect(pid, result):
    for cid in tree.get(pid, []):
        if id_map.get(cid, {}).get("menuType") in (1, 2):
            result.append(cid); collect(cid, result)

mids = []
for m in menus:
    if m.get("menuName") == "系统管理" and m.get("menuType") == 1 and m.get("parentId") == 0:
        mids.append(m["id"]); collect(m["id"], mids)
print("Menu IDs: %d" % len(mids))

api("PUT", "/api/system/role/%s/menus" % rid, mids)
api("PUT", "/api/system/role/%s/data-scope" % rid, {"dataScope": 1})
print("Menus saved")

# ---- Phase 3: Create user ----
print("Phase 3: Create rbac_test_sys")
dl = api("GET", "/api/system/dept/list")
dd = dl.get("data", dl)
dept_id = dd[0].get("deptId") or dd[0].get("id", 1) if isinstance(dd, list) and dd else 1
now = int(time.time())
resp = api("POST", "/api/system/user", {
    "username": "rbac_test_sys", "name": "SYS-Test", "realName": "SYS-Test",
    "password": PWD, "confirmPassword": PWD,
    "phone": "138%s" % str(now)[-8:], "phonenumber": "138%s" % str(now)[-8:],
    "deptId": dept_id, "status": "1", "userType": "1",
    "roleIds": [rid]
})
print("Create user: code=%s" % resp.get("code"))

# Get user ID
time.sleep(0.5)
ul2 = api("GET", "/api/system/user/list?pageNum=1&pageSize=5&username=rbac_test_sys")
uid = None
for u in ul2.get("data", ul2).get("records", []):
    uid = u["id"]
print("User ID: %s" % uid)

# ---- Phase 4: UI - Edit user, select role via keyboard ----
print("Phase 4: UI edit user -> select role")
nav = SidebarNavigator(d)
nav._navigate_by_js_hash('#/system/user', 'u')
time.sleep(3)
up = UserManagePage(d)
up.wait_vue_stable()
up.click_reset_button(); time.sleep(0.5)
up.input_search_username("rbac_test_sys"); up.click_search_button(); time.sleep(2)

print("Rows: %d" % up.get_table_row_count())
up.click_edit_user("rbac_test_sys")
time.sleep(3)

# Find the role el-select and interact via keyboard
sel = d.execute_script("""
var dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
if (!dlg) { var ds = document.querySelectorAll('.el-dialog'); for (var i=0; i<ds.length; i++) { if (ds[i].offsetParent) { dlg = ds[i]; break; } } }
if (!dlg) return null;

var items = dlg.querySelectorAll('.el-form-item');
for (var i=0; i<items.length; i++) {
    var lb = items[i].querySelector('.el-form-item__label');
    if (lb && (lb.textContent || '').indexOf('角色') !== -1) {
        var wrapper = items[i].querySelector('.el-select__wrapper');
        if (!wrapper) wrapper = items[i].querySelector('.el-input__wrapper');
        if (!wrapper) wrapper = items[i].querySelector('input');
        if (wrapper) {
            wrapper.scrollIntoView({block: 'center'});
            wrapper.focus();
            return 'found_and_focused';
        }
    }
}
return 'not_found';
""")
print("Select focus: %s" % sel)

if sel == "found_and_focused":
    time.sleep(0.5)
    # Open dropdown with Enter
    ActionChains(d).send_keys(Keys.ENTER).perform()
    time.sleep(1)

    # Type to filter
    ActionChains(d).send_keys("RBAC-SYS-ONLY").perform()
    time.sleep(1)

    # Press Enter to select the first filtered option
    ActionChains(d).send_keys(Keys.ENTER).perform()
    time.sleep(1)
    print("Role selected via keyboard")
else:
    print("WARNING: Could not find role select")

# Click confirm button
d.execute_script("""
var dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
if (!dlg) return;
var btns = dlg.querySelectorAll('button.el-button--primary');
for (var i=0; i<btns.length; i++) {
    var t = (btns[i].textContent || '').trim();
    if (t && t.indexOf('取消') === -1) { btns[i].click(); return; }
}
""")
time.sleep(3)
print("Dialog saved")

# ---- Phase 5: Verify - login as rbac_test_sys ----
print("Phase 5: Verify sidebar")
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
    print("\n*** SUCCESS! ***")
else:
    print("\n*** EMPTY ***")

d.quit()
