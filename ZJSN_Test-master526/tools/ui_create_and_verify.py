"""UI-based single user creation and sidebar verification"""
import sys, time
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.UserManagePage import UserManagePage
from page.system_page.LoginPage import LoginPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

PWD = "Ajyl@2026"

base = BaseDriver()
d = base.open_browser()
d.maximize_window()
ensure_logged_in(d)
time.sleep(2)

# Step 1: Find RBAC-SYS-ONLY role ID via API
d.set_script_timeout(30)
import json
resp = d.execute_script('''
    return fetch("https://aiwechatminidemo.cimc-digital.com/api/system/role/list?pageNum=1&pageSize=50", {
        headers: { "Authorization": "Bearer " + JSON.parse(
            decodeURIComponent(document.cookie.split("authorized-token=")[1].split(";")[0])
        ).accessToken }
    }).then(r => r.json());
''')
role_id = None
for r in resp.get("data",resp).get("records",[]):
    if r.get("roleName") == "RBAC-SYS-ONLY":
        role_id = r["id"]
        print("Found role RBAC-SYS-ONLY: id=%s" % role_id)
        break

if not role_id:
    print("ERROR: RBAC-SYS-ONLY not found")
    d.quit()
    sys.exit(1)

# Step 2: Create test user via API
import json as j2
now = int(time.time())
dept_id = 1
body = {
    "username": "rbac_test_sys",
    "name": "RBAC-SYS-Test",
    "realName": "RBAC-SYS-Test",
    "password": PWD, "confirmPassword": PWD,
    "phone": "138" + str(now)[-8:],
    "phonenumber": "138" + str(now)[-8:],
    "deptId": dept_id, "status": "1", "userType": "1",
    "roleIds": [role_id]
}
resp = d.execute_script('''
    return fetch("https://aiwechatminidemo.cimc-digital.com/api/system/user", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + JSON.parse(
                decodeURIComponent(document.cookie.split("authorized-token=")[1].split(";")[0])
            ).accessToken
        },
        body: JSON.stringify(''' + j2.dumps(body, ensure_ascii=False) + ''')
    }).then(r => r.json());
''')
print("Create user: code=%s msg=%s" % (resp.get("code"), resp.get("message","")[:60]))

# Step 3: Verify menus are saved for the role
resp2 = d.execute_script('''
    return fetch("https://aiwechatminidemo.cimc-digital.com/api/system/role/''' + str(role_id) + '''/menus", {
        headers: { "Authorization": "Bearer " + JSON.parse(
            decodeURIComponent(document.cookie.split("authorized-token=")[1].split(";")[0])
        ).accessToken }
    }).then(r => r.json());
''')
menu_count = len(resp2.get("data", resp2)) if isinstance(resp2.get("data", resp2), list) else "N/A"
print("Role menus: %s" % menu_count)

# Step 4: Clear cache via UI
nav = SidebarNavigator(d)
nav._navigate_by_js_hash('#/system/role', 'cache')
time.sleep(3)
from page.system_page.RoleManagePage import RoleManagePage
rp = RoleManagePage(d)
rp.wait_vue_stable()
rp.click_clear_cache()
print("Clear cache done")

# Step 5: Login as rbac_test_sys on a NEW browser
d2 = BaseDriver().open_browser()
d2.maximize_window()
d2.get("https://aiwechatminidemo.cimc-digital.com/")
try:
    WebDriverWait(d2, 10).until(lambda x: x.execute_script("return document.readyState") == "complete")
except: pass

lp2 = LoginPage(d2)
try:
    if not lp2._is_already_logged_in():
        lp2.wait_login_form_ready()
        lp2.input_username("rbac_test_sys")
        lp2.input_password(PWD)
        btns = d2.find_elements(By.XPATH, "//button[.//span[contains(.,'登')]]")
        if btns: btns[0].click()
        else: d2.execute_script("document.querySelector('.el-button--primary').click();")
        WebDriverWait(d2, 15).until(lambda x: "#/login" not in (x.current_url or ""))
    lp2.wait_vue_stable()
    time.sleep(3)
except Exception as e:
    print("Login error: %s" % e)

menus = d2.execute_script('''
    var m=[];
    document.querySelectorAll('.el-menu > li.el-sub-menu > .el-sub-menu__title span')
        .forEach(function(s){var t=(s.innerText||'').trim();if(t)m.push(t);});
    document.querySelectorAll('.el-menu > li.el-menu-item span')
        .forEach(function(s){var t=(s.innerText||'').trim();if(t)m.push(t);});
    return m;
''')
print("Sidebar: %s" % menus)
print("Count: %d" % len(menus))

d.quit()
try: d2.quit()
except: pass
