"""Login as rbac_test_sys and call menu/routes API manually"""
import sys, time, json
sys.path.insert(0, '.')
from base.browser_driver import BaseDriver
from page.system_page.LoginPage import LoginPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

base = BaseDriver()
d = base.open_browser()
d.maximize_window()
d.get("https://aiwechatminidemo.cimc-digital.com/")
WebDriverWait(d, 10).until(lambda x: x.execute_script("return document.readyState") == "complete")
time.sleep(2)

lp = LoginPage(d)
lp.input_username("rbac_test_sys")
lp.input_password("Ajyl@2026")
btns = d.find_elements(By.XPATH, "//button[.//span[contains(.,'登')]]")
if btns: btns[0].click()
else: d.execute_script("document.querySelector('.el-button--primary').click();")
WebDriverWait(d, 15).until(lambda x: "#/login" not in (x.current_url or ""))
lp.wait_vue_stable()
time.sleep(2)

# Manually call menu/routes
routes = d.execute_script("""
    return fetch("https://aiwechatminidemo.cimc-digital.com/api/system/menu/routes", {
        headers: {
            "Authorization": "Bearer " + JSON.parse(
                decodeURIComponent(document.cookie.split("authorized-token=")[1].split(";")[0])
            ).accessToken
        }
    }).then(function(r) { return r.json(); });
""")
data = routes.get("data", routes)
count = len(data) if isinstance(data, list) else 0
print("Routes count: %d" % count)
for item in (data if isinstance(data, list) else [])[:5]:
    title = item.get("meta", {}).get("title", "?")
    children = len(item.get("children", [])) if item.get("children") else 0
    print("  %s (+%d children)" % (title, children))

# Also check what sidebar actually shows
menus = d.execute_script("""
    var m = [];
    document.querySelectorAll('.el-menu > li.el-sub-menu > .el-sub-menu__title span')
        .forEach(function(s) { var t = (s.innerText || '').trim(); if (t) m.push(t); });
    document.querySelectorAll('.el-menu > li.el-menu-item span')
        .forEach(function(s) { var t = (s.innerText || '').trim(); if (t) m.push(t); });
    return m;
""")
print("Actual sidebar: %d items -> %s" % (len(menus), menus))

d.quit()
