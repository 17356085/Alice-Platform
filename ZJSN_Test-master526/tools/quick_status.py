"""Quick check: what exists right now?"""
import sys, time, json
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver, ensure_logged_in
from page.system_page.LoginPage import LoginPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

PWD = "Ajyl@2026"

base = BaseDriver()
d = base.open_browser()
d.maximize_window()
ensure_logged_in(d)
time.sleep(2)

def api(path):
    d.set_script_timeout(10)
    return d.execute_script('''
        return fetch("https://aiwechatminidemo.cimc-digital.com''' + path + '''", {
            headers: { "Authorization": "Bearer " + JSON.parse(
                decodeURIComponent(document.cookie.split("authorized-token=")[1].split(";")[0])
            ).accessToken }
        }).then(function(r) { return r.json(); });
    ''')

# Check roles
roles = api("/api/system/role/list?pageNum=1&pageSize=50")
for r in roles.get("data", roles).get("records", []):
    if "RBAC" in r.get("roleName", "") or "rbac" in r.get("roleCode", ""):
        print("Role: %s (id=%s)" % (r["roleName"], r["id"]))

# Check users
users = api("/api/system/user/list?pageNum=1&pageSize=50&username=rbac")
for u in users.get("data", users).get("records", []):
    print("User: %s (id=%s)" % (u["username"], u["id"]))

# Try login as rbac_test_sys
d.get("https://aiwechatminidemo.cimc-digital.com/")
time.sleep(3)
lp = LoginPage(d)
try:
    lp.input_username("rbac_test_sys")
    lp.input_password(PWD)
    btns = d.find_elements(By.XPATH, "//button[.//span[contains(.,'登')]]")
    if btns: btns[0].click()
    else: d.execute_script("document.querySelector('.el-button--primary').click();")
    WebDriverWait(d, 15).until(lambda x: "#/login" not in (x.current_url or ""))
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
except Exception as e:
    print("Login failed: %s" % e)

d.quit()
