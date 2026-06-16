#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Create RBAC test users via UI (reliable password setup).
Run AFTER rbac_seed_clean.py (which creates roles + assigns permissions).
Role names: RBAC-ALL, RBAC-SYS-ONLY, RBAC-EQUIP-ONLY, etc.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator
from page.system_page.UserManagePage import UserManagePage
from selenium.webdriver.common.by import By

PWD = "Ajyl@2026"

USERS = [
    ("rbac_test_full",   "RBAC-ALL-Test",       "RBAC-ALL"),
    ("rbac_test_sys",    "RBAC-SYS-Test",       "RBAC-SYS-ONLY"),
    ("rbac_test_equip",  "RBAC-EQUIP-Test",     "RBAC-EQUIP-ONLY"),
    ("rbac_test_hr",     "RBAC-HR-Test",        "RBAC-HR-ONLY"),
    ("rbac_test_mix",    "RBAC-MIXED-Test",     "RBAC-MIXED"),
    ("rbac_test_none",   "RBAC-NONE-Test",      "RBAC-NONE"),
    ("rbac_test_ro",     "RBAC-READONLY-Test",  "RBAC-READONLY"),
]


def esc(driver):
    from selenium.webdriver.common.keys import Keys
    try:
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        time.sleep(0.5)
    except:
        pass


base = BaseDriver()
driver = None
try:
    driver = base.open_browser()
    driver.maximize_window()
    ensure_logged_in(driver)
    nav = SidebarNavigator(driver)
    nav._navigate_by_js_hash('#/system/user', 'seed')
    time.sleep(3)
    up = UserManagePage(driver)

    print("Creating RBAC test users via UI...")

    for username, name, role_name in USERS:
        print("  User: %s (%s) -> %s" % (username, name, role_name))

        # Check if exists
        up.click_reset_button()
        time.sleep(0.5)
        up.input_search_username(username)
        up.click_search_button()
        time.sleep(1.5)
        if up.get_table_row_count() > 0:
            print("    Already exists, skip")
            continue

        esc(driver)

        # Open Add dialog
        up.click_add_user_button()
        time.sleep(1)

        try:
            up.input_dialog_input("用户名", username)
            up.input_dialog_input("姓名", name)
            up.input_password_in_dialog(PWD)

            # Department (try first available)
            try:
                up.select_dialog_option_by_text("部门", "人力行政部")
            except:
                try:
                    up.select_dialog_first_valid_option("部门")
                except:
                    print("    WARN: dept select failed")

            # Role
            try:
                up.select_dialog_option_by_text("角色", role_name)
            except:
                print("    WARN: role select failed (%s)" % role_name)

            # Phone
            try:
                up.input_dialog_input("手机号", "138" + str(int(time.time()))[-8:])
            except:
                pass

            # Submit
            up.click_dialog_confirm()
            t = up.get_toast_text(timeout=10)
            if t and '成功' in t:
                print("    OK: created")
            else:
                err = up.get_form_error_text(timeout=3)
                print("    WARN: %s / err=%s" % (t, err))
        except Exception as e:
            print("    FAIL: %s" % e)
            esc(driver)

        time.sleep(1)

    print("[DONE] All RBAC test users created!")

finally:
    if driver:
        try: base.close_browser()
        except: pass
