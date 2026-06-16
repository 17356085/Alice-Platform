"""Clean seed: ALL UI — roles, permissions, users"""
import sys, time, json
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.RoleManagePage import RoleManagePage
from page.system_page.UserManagePage import UserManagePage
from page.system_page.LoginPage import LoginPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

PWD = "Ajyl@2026"

def api(method, path, body=None):
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

# ====== Phase 1: Clean ======
print("Phase 1: Clean")
# Delete ALL RBAC roles and users
rl = api("GET", "/api/system/role/list?pageNum=1&pageSize=200")
deleted_roles = 0
for r in rl.get("data", rl).get("records", []):
    rn = r.get("roleName", "")
    rc = r.get("roleCode", "")
    if rn.startswith("RBAC-") or rc.startswith("rbac_"):
        resp = api("DELETE", "/api/system/role/%s" % r["id"])
        deleted_roles += 1
        print("  Deleted role: %s (code=%s)" % (rn, resp.get("code")))
ul = api("GET", "/api/system/user/list?pageNum=1&pageSize=50&username=rbac_test")
for u in ul.get("data", ul).get("records", []):
    api("DELETE", "/api/system/user/%s" % u["id"])
    print("  Deleted user: %s" % u["username"])
print("Clean done — deleted %d roles" % deleted_roles)

# ====== Phase 2: Create role ======
print("Phase 2: Create role")
nav = SidebarNavigator(d)
nav._navigate_by_js_hash('#/system/role', 'role'); time.sleep(3)
rp = RoleManagePage(d); rp.wait_vue_stable()

# Verify on correct page
headers = rp.get_table_headers()
print("Page headers: %s" % (headers[:3] if headers else 'NONE'))

rp.click_add()
time.sleep(3)
# Check dialog opened and its title
dlg_info = d.execute_script("""
var dlg = document.querySelector('.el-dialog:not([style*=\"display: none\"])');
if (!dlg) { var ds=document.querySelectorAll('.el-dialog'); for(var i=0;i<ds.length;i++){if(ds[i].offsetParent){dlg=ds[i];break}} }
if (!dlg) return 'no_dlg';
var title = dlg.querySelector('.el-dialog__title');
var inputs = dlg.querySelectorAll('input');
var placeholders = [];
for (var i=0; i<inputs.length; i++) { if (inputs[i].placeholder) placeholders.push(inputs[i].placeholder); }
return JSON.stringify({title: title?title.textContent.trim():'no_title', inputs: inputs.length, placeholders: placeholders});
""")
print("Dialog: %s" % dlg_info)

# Direct JS fill - PO's selectors don't match dialog's placeholder
d.execute_script("""
var dlg = document.querySelector('.el-dialog:not([style*=\"display: none\"])');
if (!dlg) return;
var inputs = dlg.querySelectorAll('input');
var ns = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
for (var i=0; i<inputs.length; i++) {
    var ph = inputs[i].placeholder || '';
    // The create role dialog uses placeholder='如：日报审批流程' for name
    if (ph.indexOf('日报')!==-1 || ph.indexOf('请输入角色名称')!==-1 || ph.indexOf('角色名称')!==-1) {
        ns.call(inputs[i], 'RBAC-SYS-ONLY');
        inputs[i].dispatchEvent(new Event('input',{bubbles:true}));
        inputs[i].dispatchEvent(new Event('change',{bubbles:true}));
    } else if (ph.indexOf('DAILY')!==-1 || ph.indexOf('如：')!==-1 || ph.indexOf('角色编码')!==-1) {
        ns.call(inputs[i], 'rbac_sys_test');
        inputs[i].dispatchEvent(new Event('input',{bubbles:true}));
        inputs[i].dispatchEvent(new Event('change',{bubbles:true}));
    }
}
""")
print("Role fields filled via JS")
rp.input_dialog_order(91)
rp.select_dialog_status("启用")
time.sleep(0.5)

# Check button state before confirm
btn = d.execute_script("""
var dlg = document.querySelector('.el-dialog:not([style*=\"display: none\"])');
if (!dlg) return 'no_dlg';
var b = dlg.querySelector('button.el-button--primary');
return b ? ('disabled=' + b.disabled + ' text=' + (b.textContent||'').trim()) : 'no_btn';
""")
print("Confirm btn: %s" % btn)

rp.click_dialog_confirm()
msg = rp.wait_for_toast_text(timeout=8)
print("Role create toast: %s" % (msg or "no toast"))
# Verify role exists — wait for API cache to update
time.sleep(3)
# Check on the actual page (bypass API cache)
rp.click_reset(); time.sleep(0.5)
rp.input_role_name("RBAC-SYS-ONLY"); rp.click_search(); rp.wait_table_ready(timeout=8)
table_count = rp.get_table_row_count()
# Also try getting column data with JS
col2 = d.execute_script("""
var cells = document.querySelectorAll('.el-table__body-wrapper tbody tr td:nth-child(2) .cell');
var names = [];
for (var i=0; i<Math.min(cells.length, 5); i++) { names.push((cells[i].textContent||'').trim()); }
return names;
""")
print("Table rows after search: %d, first names: %s" % (table_count, col2))
rl_check = api("GET", "/api/system/role/list?pageNum=1&pageSize=50")
found = False
for r in rl_check.get("data", rl_check).get("records", []):
    if r.get("roleName") == "RBAC-SYS-ONLY":
        found = True
        print("Verified: role %s exists (id=%s)" % (r["roleName"], r["id"]))
        break
if not found:
    # Fuzzy search — maybe name was garbled
    for r in rl_check.get("data", rl_check).get("records", []):
        rn = r.get("roleName", "")
        if "RBAC" in rn and "SYS" in rn:
            print("  Fuzzy match: %s (id=%s)" % (rn, r["id"]))
    # Try to find newly created role by code
    for r in rl_check.get("data", rl_check).get("records", []):
        if r.get("roleCode", "").startswith("rbac_sys"):
            print("  Code match: %s -> %s (id=%s)" % (r["roleName"], r["roleCode"], r["id"]))
    all_rn = [r.get("roleName","")[:20] for r in rl_check.get("data", rl_check).get("records", [])]
    print("  All: %s" % all_rn)
    print("WARNING: RBAC-SYS-ONLY not found!")

# ====== Phase 3: Permissions ======
print("Phase 3: Permissions")
rp.click_reset(); time.sleep(0.5)
rp.input_role_name("RBAC-SYS-ONLY"); rp.click_search(); rp.wait_table_ready(timeout=8)
rp.click_permission_by_role_name("RBAC-SYS-ONLY"); time.sleep(2)
rp.click_permission_tab_pc(); time.sleep(2)

# Expand all groups via JS
n = d.execute_script("""
var arrows = document.querySelectorAll('.perm-group__arrow');
var c = 0;
for (var i=0; i<arrows.length; i++) { if (arrows[i].offsetParent) { arrows[i].click(); c++; } }
return c;
""")
print("Expanded %d groups" % (n or 0))
time.sleep(1)

# Click real permission checkboxes via Selenium (skip value="on")
from selenium.webdriver.common.by import By
all_cbs = d.find_elements(By.CSS_SELECTOR, '.el-dialog .el-checkbox')
clicked = 0
for cb in all_cbs:
    if clicked >= 15: break
    try:
        inp = cb.find_element(By.CSS_SELECTOR, 'input[type="checkbox"]')
        val = inp.get_attribute('value') or ''
        if val == 'on': continue
        if 'is-checked' in (cb.get_attribute('class') or ''): continue
        inner = cb.find_element(By.CSS_SELECTOR, '.el-checkbox__inner')
        if inner.is_displayed():
            d.execute_script("arguments[0].scrollIntoView({block:'center'});", inner)
            inner.click()
            clicked += 1
            time.sleep(0.15)
    except: continue
print("Checked %d perms" % clicked)

rp.click_permission_confirm()
msg = rp.wait_for_toast_text(timeout=6)
print("Permissions saved: %s" % (msg or "no toast"))

# ====== Phase 4: Create user via API (permissions already set via UI) ======
print("Phase 4: Create user via API")
dl = api("GET", "/api/system/dept/list")
dd = dl.get("data", dl)
dept_id = dd[0].get("deptId") or dd[0].get("id", 1) if isinstance(dd, list) and dd else 1

# Get role ID - search all roles
rl2 = api("GET", "/api/system/role/list?pageNum=1&pageSize=50")
rid = None
all_names = []
for r in rl2.get("data", rl2).get("records", []):
    rn = r.get("roleName", "")
    all_names.append(rn)
    if rn == "RBAC-SYS-ONLY" or "RBAC-SYS" in rn:
        rid = r["id"]
        print("MATCH: %s -> id=%s" % (rn, rid))
print("All roles: %s" % all_names[:15])
print("Role ID: %s" % rid)

now = int(time.time())
resp = api("POST", "/api/system/user", {
    "username": "rbac_test_sys", "name": "SYS-Test", "realName": "SYS-Test",
    "password": PWD, "confirmPassword": PWD,
    "phone": "138%s" % str(now)[-8:], "phonenumber": "138%s" % str(now)[-8:],
    "deptId": dept_id, "status": "1", "userType": "1", "roleIds": [rid]
})
print("Create user: code=%s" % resp.get("code"))

# Assign user to role via PUT
uid = None
ul2 = api("GET", "/api/system/user/list?pageNum=1&pageSize=5&username=rbac_test_sys")
for u in ul2.get("data", ul2).get("records", []):
    uid = u["id"]
print("User ID: %s" % uid)
if uid and rid:
    api("PUT", "/api/system/role/%s/users" % rid, [uid])
    print("Role assigned")
if not msg or "成功" not in str(msg):
    print("WARNING: User creation may have failed!")

# ====== Phase 5: Clear cache ======
print("Phase 5: Clear cache")
nav._navigate_by_js_hash('#/system/role', 'cache'); time.sleep(3)
rp = RoleManagePage(d); rp.wait_vue_stable()
rp.click_clear_cache(); time.sleep(2)
print("Cache cleared")

# ====== Phase 6: Verify (fresh browser) ======
print("Phase 6: Verify")
d.quit()  # close admin browser

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
print("*** SUCCESS ***" if len(menus) > 0 else "*** EMPTY ***")

d2.quit()
