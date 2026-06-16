"""One shot: API everything + ActionChains physical click clear cache + verify"""
import sys, time, json
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.LoginPage import LoginPage
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

# ---- Browser 1: Admin ----
b1 = BaseDriver()
d1 = b1.open_browser()
d1.maximize_window()
ensure_logged_in(d1)
time.sleep(2)

# ---- Step 1: API create role ----
rl = api(d1, "GET", "/api/system/role/list?pageNum=1&pageSize=100")
for r in rl.get("data", rl).get("records", []):
    if r.get("roleName") == "RBAC-SYS-ONLY":
        api(d1, "DELETE", "/api/system/role/%s" % r["id"])

resp = api(d1, "POST", "/api/system/role", {
    "roleName": "RBAC-SYS-ONLY", "roleSort": 91, "status": "1", "remark": "test"
})
time.sleep(1)

rl2 = api(d1, "GET", "/api/system/role/list?pageNum=1&pageSize=100")
rid = None
for r in rl2.get("data", rl2).get("records", []):
    if r.get("roleName") == "RBAC-SYS-ONLY":
        rid = r["id"]; break
print("Role: %s" % rid)

# ---- Step 2: API assign menus ----
resp3 = api(d1, "GET", "/api/system/menu/list?pageNum=1&pageSize=500")
menus = resp3.get("data", resp3).get("records", [])
tree = {}; id_map = {}
for m in menus:
    mid = m["id"]; id_map[mid] = m
    tree.setdefault(m.get("parentId", 0), []).append(mid)
def collect(pid, r):
    for cid in tree.get(pid, []): r.append(cid); collect(cid, r)
mids = []
for m in menus:
    if m.get("menuName") == "系统管理" and m.get("menuType") == 1 and m.get("parentId") == 0:
        mids.append(m["id"]); collect(m["id"], mids)
api(d1, "PUT", "/api/system/role/%s/menus" % rid, mids)
api(d1, "PUT", "/api/system/role/%s/data-scope" % rid, {"dataScope": 1})
mcount = len(mids)
print("Menus: %d" % mcount)

# ---- Step 3: API create user ----
dl = api(d1, "GET", "/api/system/dept/list")
dd = dl.get("data", dl)
dept = dd[0].get("deptId") or dd[0].get("id", 1) if isinstance(dd, list) and dd else 1
now = int(time.time())

ul = api(d1, "GET", "/api/system/user/list?pageNum=1&pageSize=5&username=rbac_test_sys")
for u in ul.get("data", ul).get("records", []):
    api(d1, "DELETE", "/api/system/user/%s" % u["id"])

api(d1, "POST", "/api/system/user", {
    "username": "rbac_test_sys", "name": "SYS", "realName": "SYS",
    "password": PWD, "confirmPassword": PWD,
    "phone": "138%s" % str(now)[-8:], "phonenumber": "138%s" % str(now)[-8:],
    "deptId": dept, "status": "1", "userType": "1", "roleIds": [rid]
})
time.sleep(1)

ul2 = api(d1, "GET", "/api/system/user/list?pageNum=1&pageSize=5&username=rbac_test_sys")
uid = None
for u in ul2.get("data", ul2).get("records", []): uid = u["id"]
api(d1, "PUT", "/api/system/role/%s/users" % rid, [uid])
print("User: %s -> Role %s" % (uid, rid))

# ---- Step 4: ActionChains physical click "清空缓存" ----
nav = SidebarNavigator(d1)
nav._navigate_by_js_hash('#/system/role', 'cache_clear')
time.sleep(4)

# Find the button element
btn = d1.find_element(By.XPATH, "//button[contains(.,'清空缓存')]")
d1.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
time.sleep(1)

# Physical mouse move + click via ActionChains
actions = ActionChains(d1)
actions.move_to_element(btn).pause(0.5).click().perform()
time.sleep(2)

# Check toast
try:
    toast = WebDriverWait(d1, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".el-message__content"))
    )
    print("Cache toast: %s" % toast.text)
except:
    print("Cache toast: none (may have worked silently)")

# ---- Step 5: Fresh browser verify sidebar ----
d1.quit()
b2 = BaseDriver()
d2 = b2.open_browser()
d2.maximize_window()
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
    .forEach(function(s) { var t = (s.innerText || '').trim(); if (t) m.push(t); });
document.querySelectorAll('.el-menu > li.el-menu-item span')
    .forEach(function(s) { var t = (s.innerText || '').trim(); if (t) m.push(t); });
return m;
""")
print("SIDEBAR (%d): %s" % (len(menus), menus))
d2.quit()
