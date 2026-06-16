"""通过 UI 最终分配角色 — 使用 ActionChains 原生点击"""

import sys, time
sys.path.insert(0, 'd:/Desktop/WorkStudy/ZJSN_Test-master526')

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator

PAIRS = [
    ("rbac_test_full", "RBAC-全权限"),
    ("rbac_test_sys", "RBAC-仅系统管理"),
    ("rbac_test_equip", "RBAC-仅设备管理"),
    ("rbac_test_hr", "RBAC-仅人员管理"),
    ("rbac_test_mix", "RBAC-混合权限"),
]

def step(text):
    print(f"  -> {text}")

base = BaseDriver()
driver = None
try:
    driver = base.open_browser()
    driver.maximize_window()
    ensure_logged_in(driver)
    nav = SidebarNavigator(driver)
    nav.navigate_to("系统管理", "用户管理")
    time.sleep(3)

    for username, role_name in PAIRS:
        step(f"{username} -> {role_name}")

        # 搜索用户
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH,
                "//input[contains(@placeholder, '搜索')]"))
        )
        search_input.clear()
        search_input.send_keys(username)
        time.sleep(0.5)

        driver.find_element(By.XPATH,
            "//button[.//span[contains(., '查询')]]").click()
        time.sleep(2)

        # 点击行内的「分配角色」按钮 (第3个按钮)
        rows = driver.find_elements(By.CSS_SELECTOR, "tr.el-table__row")
        found = False
        for row in rows:
            if username in row.text:
                btns = row.find_elements(By.CSS_SELECTOR, "button")
                for btn in btns:
                    if btn.text.strip() == '分配角色':
                        ActionChains(driver).move_to_element(btn).click(btn).perform()
                        found = True
                        break
                break
        if not found:
            step(f"  BUTTON NOT FOUND")
            continue
        time.sleep(3)

        # 确认弹窗标题
        title = driver.execute_script(
            "return document.querySelector('.el-dialog .el-dialog__title')?.innerText||''")
        step(f"  Dialog: {title}")

        if '分配角色' not in title:
            step(f"  WRONG DIALOG - closing")
            cancel = driver.find_element(By.XPATH,
                "//button[.//span[contains(., '取消')]]")
            cancel.click()
            time.sleep(1)
            continue

        # 用原生点击勾选目标角色
        try:
            # 找到目标角色的 checkbox label
            checkbox_label = driver.find_element(By.XPATH,
                f"//div[contains(@class,'el-dialog')]//label[contains(@class,'el-checkbox')]" +
                f"[.//span[text()='{role_name}']]")

            # 获取实际 input 元素
            checkbox_input = checkbox_label.find_element(
                By.CSS_SELECTOR, ".el-checkbox__original")

            step(f"  Found checkbox input, checked={checkbox_input.is_selected()}")

            # 用原生 Selenium 点击 INPUT（这应该触发 Vue 的 change 事件）
            if not checkbox_input.is_selected():
                ActionChains(driver).move_to_element(checkbox_input).click(checkbox_input).perform()
                time.sleep(1)
                step(f"  Clicked input")
        except Exception as e:
            step(f"  CHECKBOX ERROR: {e}")

        # 点击确定
        confirm = driver.find_element(By.XPATH,
            "//div[contains(@class,'el-dialog')]//button[.//span[contains(., '确定')]]")
        ActionChains(driver).move_to_element(confirm).click(confirm).perform()
        time.sleep(2)

        toast = driver.execute_script(
            "return document.querySelector('.el-message__content')?.innerText||''")
        step(f"  Toast: {toast}")
        time.sleep(1.5)

    # 验证
    result = driver.execute_script("""
        var token = JSON.parse(decodeURIComponent(
            document.cookie.split('authorized-token=')[1].split(';')[0])).accessToken;
        return fetch('https://aiwechatminidemo.cimc-digital.com/api/system/user/list?pageNum=1&pageSize=50',{
            headers:{'Authorization':'Bearer '+token}
        }).then(r=>r.json());
    """)
    print("\nVerification:")
    for u in result.get('data',{}).get('records',[]):
        un = u.get('username','')
        if 'rbac_test_' in un:
            print(f"  {un:20s} roleIds={u.get('roleIds',[])}")

    print("\nDone!")

finally:
    if driver:
        try: base.close_browser()
        except: pass
