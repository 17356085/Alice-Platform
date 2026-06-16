"""Final: API role+menus, UI permission toggle+save, UI user creation, verify sidebar"""
import sys, time, json, base64
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.LoginPage import LoginPage
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

PWD = "Test1234"
USERNAME = "rbac_test_%d" % int(time.time() % 100000)
print("Username: %s" % USERNAME)

def api(d, method, path, body=None):
    d.set_script_timeout(15)
    js = '' if body is None else 'body: JSON.stringify(%s),' % json.dumps(body, ensure_ascii=False)
    code = '''
        return fetch("https://aiwechatminidemo.cimc-digital.com''' + path + '''", {
            method: "''' + method + '''",
            headers: { "Content-Type": "application/json",
                "Authorization": "Bearer " + JSON.parse(
                    decodeURIComponent(document.cookie.split("authorized-token=")[1].split(";")[0])
                ).accessToken },
            ''' + js + '''
        }).then(function(r) { return r.json(); });
    '''
    return d.execute_script(code)

# ============================================================
b1 = BaseDriver()
d = b1.open_browser()
d.maximize_window()
ensure_logged_in(d)
time.sleep(2)

# ---- Step 1: API create role ----
api(d, "DELETE", "/api/system/role/299")
resp = api(d, "POST", "/api/system/role", {
    "roleName": "RBAC-SYS-ONLY", "roleSort": 91, "status": "1", "remark": "test"
})
time.sleep(1)
rid = None
for r in api(d, "GET", "/api/system/role/list?pageNum=1&pageSize=100").get("data", {}).get("records", []):
    if r.get("roleName") == "RBAC-SYS-ONLY":
        rid = r["id"]
print("Role: %s" % rid)

# ---- Step 2: API assign menus ----
resp = api(d, "GET", "/api/system/menu/list?pageNum=1&pageSize=500")
menus = resp.get("data", resp).get("records", [])
tree = {}
for m in menus:
    tree.setdefault(m.get("parentId", 0), []).append(m["id"])
def collect(pid, result):
    for cid in tree.get(pid, []):
        result.append(cid)
        collect(cid, result)
mids = []
for m in menus:
    if m.get("menuName") == "系统管理" and m.get("menuType") == 1 and m.get("parentId") == 0:
        mids.append(m["id"])
        collect(m["id"], mids)
api(d, "PUT", "/api/system/role/%s/menus" % rid, mids)
api(d, "PUT", "/api/system/role/%s/data-scope" % rid, {"dataScope": 1})
print("Menus: %d" % len(mids))

# ---- Step 3: UI permission dialog - toggle one perm + save ----
nav = SidebarNavigator(d)
nav._navigate_by_js_hash('#/system/role', 'perm')
time.sleep(3)

result = d.execute_script("""
var rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
for (var i=0; i<rows.length; i++) {
    if ((rows[i].textContent||'').indexOf('RBAC-SYS-ONLY')!==-1) {
        var btns = rows[i].querySelectorAll('button, span');
        for (var j=0; j<btns.length; j++) {
            if ((btns[j].textContent||'').indexOf('权限')!==-1) {
                btns[j].scrollIntoView({block:'center'}); btns[j].click(); return 'ok';
            }
        }
    }
}
return 'not_found';
""")
print("Perm dialog: %s" % result)

d.execute_script("var tab=document.querySelector('#tab-operations'); if(tab) tab.click();")
time.sleep(2)

d.execute_script("""
var arrows = document.querySelectorAll('.perm-group__arrow');
for (var i=0; i<3; i++) { if (arrows[i] && arrows[i].offsetParent) arrows[i].click(); }
""")
time.sleep(1)
d.execute_script("""
var cbs = document.querySelectorAll('.el-dialog .el-checkbox');
for (var i=0; i<cbs.length; i++) {
    var inp = cbs[i].querySelector('input[type="checkbox"]');
    if (inp && inp.value !== 'on') {
        var inner = cbs[i].querySelector('.el-checkbox__inner');
        if (inner && inner.offsetParent) { inner.click(); break; }
    }
}
""")
time.sleep(0.5)

d.execute_script("""
var dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
if (!dlg) { var ds=document.querySelectorAll('.el-dialog'); for(var i=0;i<ds.length;i++){if(ds[i].offsetParent){dlg=ds[i];break}} }
if (!dlg) return;
var btns = dlg.querySelectorAll('button.el-button--primary');
for (var i=0; i<btns.length; i++) { btns[i].click(); return; }
""")
time.sleep(2)
toast = d.execute_script("var el=document.querySelector('.el-message__content'); return el?el.textContent.trim():'';")
print("Perm save: %s" % (toast or 'NONE'))

# ---- Step 4: UI create user ----
print("Creating user via UI...")
for u in api(d, "GET", "/api/system/user/list?pageNum=1&pageSize=5&username=" + USERNAME).get("data", {}).get("records", []):
    api(d, "DELETE", "/api/system/user/%s" % u["id"])

nav._navigate_by_js_hash('#/system/user', 'user')
time.sleep(3)

d.execute_script("""
var btns = document.querySelectorAll('button');
for (var i=0; i<btns.length; i++) {
    if ((btns[i].textContent||'').trim()==='新增') { btns[i].click(); break; }
}
""")
time.sleep(3)
print("Add dialog opened")

# Fill form via Selenium
for inp in d.find_elements(By.CSS_SELECTOR, '.el-dialog input'):
    try:
        ph = inp.get_attribute('placeholder') or ''
        if '用户' in ph:
            inp.click(); inp.send_keys(Keys.CONTROL+'a'); inp.send_keys(USERNAME)
        elif '姓名' in ph:
            inp.click(); inp.send_keys(Keys.CONTROL+'a'); inp.send_keys('SYS-Test')
        elif '手机' in ph:
            inp.send_keys('138%08d' % int(time.time() % 100000000))
        elif inp.get_attribute('type') == 'password':
            inp.click()
            # Password fields block CTRL+A, use backspace chain
            for _ in range(30):
                inp.send_keys(Keys.BACKSPACE)
            inp.send_keys(PWD)
    except: pass
time.sleep(0.5)
# Verify filled values
vals = d.execute_script("""
var inps = document.querySelectorAll('.el-dialog input');
var result = [];
for (var i=0; i<inps.length; i++) {
    var ph = inps[i].placeholder || '';
    var type = inps[i].type || '';
    if (type === 'password') result.push('pwd[' + ph.substring(0,10) + ']: len=' + inps[i].value.length);
    else if (ph) result.push(ph.substring(0,10) + '=' + inps[i].value.substring(0,20));
}
return result.join('|');
""")
print("Form values: %s" % vals)

# Handle selects: skip idx=1 (user type), do dept(0) and role(2)
for idx, sel in enumerate(d.find_elements(By.CSS_SELECTOR, '.el-dialog .el-select__wrapper')):
    if idx == 1:
        continue
    try:
        d.execute_script("arguments[0].scrollIntoView({block:'center'});", sel)
        sel.click(); time.sleep(0.8)
        opts = [o for o in d.find_elements(By.CSS_SELECTOR, '.el-select-dropdown__item') if o.is_displayed()]
        if idx == 2:
            for o in opts:
                if 'RBAC-SYS-ONLY' in (o.text or ''):
                    o.click(); print("Role selected"); break
        else:
            if opts:
                opts[0].click()
                print("Dept selected: %s" % (opts[0].text or '')[:20])
        time.sleep(0.5)
    except Exception as e:
        print("Select %d err: %s" % (idx, str(e)[:60]))
print("Selects done")

# Check button state first
btn_info = d.execute_script("""
var dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
if (!dlg) return 'no_dlg';
var btns = dlg.querySelectorAll('button');
var info = [];
for (var i=0; i<btns.length; i++) {
    info.push({
        text: (btns[i].textContent||'').trim(),
        disabled: btns[i].disabled,
        primary: btns[i].classList.contains('el-button--primary')
    });
}
return JSON.stringify(info);
""")
print("Buttons: %s" % btn_info)

# Confirm
d.execute_script("""
var dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
if (!dlg) return;
var btns = dlg.querySelectorAll('button');
for (var i=0; i<btns.length; i++) {
    if ((btns[i].textContent||'').indexOf('确定')!==-1) { btns[i].click(); return; }
}
for (var i=0; i<btns.length; i++) {
    if (btns[i].classList.contains('el-button--primary')) { btns[i].click(); return; }
}
""")
time.sleep(3)
dlg_state = d.execute_script("""
var dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
if (!dlg) return 'closed';
var errors = dlg.querySelectorAll('.el-form-item__error');
for (var i=0; i<errors.length; i++) { if (errors[i].textContent) return errors[i].textContent.trim(); }
return 'open_no_errors';
""")
toast = d.execute_script("var el=document.querySelector('.el-message__content'); return el?el.textContent.trim():'';")
print("User create: dlg=%s toast=%s" % (dlg_state, toast or 'NONE'))

# ---- Step 5: Create API user as control, test if API users can login ----
ctrl_user = "ctrl_test_%d" % int(time.time() % 100000)
dl = api(d, "GET", "/api/system/dept/list")
dd = dl.get("data", dl)
dept = dd[0].get("deptId") or dd[0].get("id", 1) if isinstance(dd, list) and dd else 1

api(d, "POST", "/api/system/user", {
    "username": ctrl_user, "name": "CTRL", "realName": "CTRL",
    "password": PWD, "confirmPassword": PWD,
    "phone": "138%s" % str(int(time.time()))[-8:],
    "phonenumber": "138%s" % str(int(time.time()))[-8:],
    "deptId": dept, "status": "1", "userType": "1"
})
time.sleep(1)

ctrl_login = d.execute_script("""
return fetch("https://aiwechatminidemo.cimc-digital.com/api/auth/login", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: "''' + ctrl_user + '''", password: "''' + PWD + '''" })
}).then(function(r) { return r.json(); });
""")
ctrl_ok = ctrl_login.get("code") == 200
print("API user login: %s" % ("OK" if ctrl_ok else "FAIL - " + str(ctrl_login.get("message",""))))

# Now test UI-created user
ul = api(d, "GET", "/api/system/user/list?pageNum=1&pageSize=5&username=" + USERNAME)
recs = ul.get("data", ul).get("records", [])
if recs:
    u = recs[0]
    # Check if password hash exists
    detail = api(d, "GET", "/api/system/user/" + str(u["id"]))
    ud = detail.get("data", detail)
    has_pwd = bool(ud.get("password"))
    print("UI user: %s (id=%s, status=%s, has_pwd=%s)" % (u.get("username"), u.get("id"), u.get("status"), has_pwd))
else:
    print("UI user NOT FOUND!")

login_resp = d.execute_script("""
return fetch("https://aiwechatminidemo.cimc-digital.com/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: "''' + USERNAME + '''", password: "''' + PWD + '''" })
}).then(function(r) { return r.json(); });
""")
login_resp = d.execute_script("""
return fetch("https://aiwechatminidemo.cimc-digital.com/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: "''' + USERNAME + '''", password: "''' + PWD + '''" })
}).then(function(r) { return r.json(); });
""")
token = login_resp.get("accessToken") or (login_resp.get("data", {}) or {}).get("accessToken", "")
if token:
    routes = d.execute_script("""
    return fetch("https://aiwechatminidemo.cimc-digital.com/api/system/menu/routes", {
        headers: { "Authorization": "Bearer ''' + token + '''" }
    }).then(function(r) { return r.json(); });
    """)
    rdata = routes.get("data", routes)
    rcount = len(rdata) if isinstance(rdata, list) else 0
    print("Login OK | Routes API: %d items" % rcount)

    if rcount > 0:
        print("*** SUCCESS! Menu routes returned! ***")
    else:
        print("*** Routes still 0 ***")
else:
    print("Login failed: %s" % str(login_resp)[:200])

d.quit()
