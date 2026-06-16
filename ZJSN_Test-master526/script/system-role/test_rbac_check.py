"""RBAC 权限检查 — 测试现有数据，不自动创建数据"""
import sys, os, json, pytest, allure
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from base.browser_driver import BaseDriver, ensure_logged_in
from page.system_page.LoginPage import LoginPage
from config import DEFAULT_USERNAME, DEFAULT_PASSWORD
from base.base_page import BasePage

PWD = "Ajyl@2026"

TEST_CASES = [
    ("rbac_test_full",   "RBAC-全权限",     ["系统管理","设备管理","储罐管理","DCS数据","化验室取样","人员管理","生产管理","销售管理"]),
    ("rbac_test_sys",    "RBAC-仅系统管理",  ["系统管理"]),
    ("rbac_test_equip",  "RBAC-仅设备管理",  ["设备管理"]),
    ("rbac_test_hr",     "RBAC-仅人员管理",  ["人员管理"]),
    ("rbac_test_none",   "RBAC-零权限",     []),
]

def step(text):
    print(f"  -> {text}")
    try: allure.step(text)
    except: pass

def get_sidebar(driver):
    return driver.execute_script("""
        var m=[];
        document.querySelectorAll('.el-menu > li.el-sub-menu > .el-sub-menu__title span')
            .forEach(function(s){var t=(s.innerText||'').trim();if(t)m.push(t);});
        document.querySelectorAll('.el-menu > li.el-menu-item span')
            .forEach(function(s){var t=(s.innerText||'').trim();if(t)m.push(t);});
        return m;
    """)

def login_as(driver, u, p=PWD):
    driver.get("https://aiwechatminidemo.cimc-digital.com/")
    lp = LoginPage(driver)
    try:
        if lp._is_already_logged_in():
            cur = driver.execute_script("return window.location.hash;")
            if "#/login" not in cur: return True
    except: pass
    for _ in range(3):
        try:
            driver.get("https://aiwechatminidemo.cimc-digital.com/")
            lp = LoginPage(driver)
            if lp.is_login_page():
                lp.input_username(u)
                lp.input_password(p)
                btns = driver.find_elements(By.XPATH, "//button[.//span[contains(.,'登')]]")
                if btns: btns[0].click()
                else: driver.execute_script("document.querySelector('.el-button--primary').click();")
                WebDriverWait(driver, 15).until(lambda d: "#/login" not in (d.current_url or ""))
                lp.wait_vue_stable()
                return True
            if lp._is_already_logged_in(): return True
        except Exception as e:
            if _ < 2:
                try:
                    WebDriverWait(driver, 5).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
                except: pass
            else: raise e
    return False

def user_exists(driver, username):
    token = None
    for c in driver.get_cookies():
        if c['name'] == 'authorized-token':
            import urllib.parse; td = json.loads(urllib.parse.unquote(c['value']))
            token = td.get('accessToken'); break
    if not token: return False
    try:
        result = driver.execute_script(f"""
            return fetch('https://aiwechatminidemo.cimc-digital.com/api/system/user/list?pageNum=1&pageSize=1&username={username}',{{
                headers:{{'Authorization':'Bearer {token}'}}
            }}).then(function(r){{return r.json();}});
        """)
        records = result.get('data',{}).get('records',[]) if isinstance(result.get('data'), dict) else []
        return any(u.get('username')==username for u in records)
    except: return False

@pytest.fixture(scope="module")
def check_data():
    base = BaseDriver()
    driver = base.open_browser()
    ensure_logged_in(driver)
    bp = BasePage(driver)
    bp.wait_vue_stable()

    existing = []
    for username, role_name, _ in TEST_CASES:
        if user_exists(driver, username):
            existing.append(username)
            print(f"  [OK] {username} exists")
        else:
            print(f"  [MISS] {username} NOT found")
    driver.quit()

    if not existing:
        pytest.skip("No RBAC test users found. Run seed script first.")
    return existing

@pytest.mark.smoke
@allure.epic("权限管理")
@allure.feature("RBAC权限矩阵")
@allure.story("侧边栏可见性")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.parametrize("username,role_name,expected", TEST_CASES,
    ids=[c[1] for c in TEST_CASES])
def test_sidebar_menu(check_data, username, role_name, expected):
    driver = BaseDriver().open_browser()
    try:
        assert login_as(driver, username, PWD), f"Login failed: {username}"
        lp = LoginPage(driver)
        lp.wait_vue_stable()
        menus = get_sidebar(driver)
        full = set(expected + ["首页"])
        step(f"User: {username}")
        step(f"Expected: {sorted(full)}")
        step(f"Actual: {sorted(menus)}")
        for m in full:
            assert m in menus, f"Missing '{m}', have: {sorted(menus)}"
        if role_name == "RBAC-零权限":
            assert len(menus) <= 1, f"Zero-permission user sees extra menus: {sorted(menus)}"
    finally:
        try: driver.quit()
        except: pass

if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
