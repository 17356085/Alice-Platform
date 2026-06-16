"""Just login as rbac_test_63104 and check sidebar"""
import sys, time, json
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver
from page.system_page.LoginPage import LoginPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# Get the latest test user
USERNAME = "rbac_test_64387"
PWD = "Ajyl@2026"

base = BaseDriver()
d = base.open_browser()
d.maximize_window()
d.get("https://aiwechatminidemo.cimc-digital.com/")
WebDriverWait(d, 10).until(lambda x: x.execute_script("return document.readyState") == "complete")
time.sleep(2)

lp = LoginPage(d)
print("On login page: %s" % lp.is_login_page())

lp.input_username(USERNAME)
lp.input_password(PWD)
d.execute_script("document.querySelector('.el-button--primary').click();")
WebDriverWait(d, 20).until(lambda x: "#/login" not in (x.current_url or ""))
lp.wait_vue_stable()
time.sleep(3)

menus = d.execute_script("""
var m = [];
document.querySelectorAll('.el-menu > li.el-sub-menu > .el-sub-menu__title span')
    .forEach(function(s) { var t=(s.innerText||'').trim(); if(t)m.push(t); });
document.querySelectorAll('.el-menu > li.el-menu-item span')
    .forEach(function(s) { var t=(s.innerText||'').trim(); if(t)m.push(t); });
return m;
""")
print("SIDEBAR(%d): %s" % (len(menus), menus))

# Routes API
routes = d.execute_script("""
return fetch("https://aiwechatminidemo.cimc-digital.com/api/system/menu/routes", {
    headers: { "Authorization": "Bearer " + JSON.parse(
        decodeURIComponent(document.cookie.split("authorized-token=")[1].split(";")[0])
    ).accessToken }
}).then(function(r) { return r.json(); });
""")
rdata = routes.get("data", routes)
rcount = len(rdata) if isinstance(rdata, list) else 0
print("Routes: %d" % rcount)

d.quit()
