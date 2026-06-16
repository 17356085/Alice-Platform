"""Comprehensive page inspection: find all buttons and dialog structure"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from base.browser_driver import BaseDriver, ensure_logged_in
from page.personnel_page.TrainPlanPage import TrainPlanPage

base = BaseDriver()
driver = base.open_browser()
ensure_logged_in(driver)

page = TrainPlanPage(driver)
page.navigate_to_train_plan()
time.sleep(1)
page.click_add_button()
time.sleep(2)

# Find ALL buttons on the page
all_buttons = driver.find_elements(By.XPATH, '//button')
print(f"\n=== ALL buttons on page ({len(all_buttons)}) ===")
for i, btn in enumerate(all_buttons):
    try:
        text = btn.text.strip() or '[empty]'
        classes = (btn.get_attribute('class') or '')[:60]
        visible = btn.is_displayed()
        tag = btn.tag_name
        # Show parent structure
        parent = btn.find_element(By.XPATH, '..')
        parent_class = (parent.get_attribute('class') or '')[:50]
        grandparent = parent.find_element(By.XPATH, '..')
        gp_class = (grandparent.get_attribute('class') or '')[:50]
        print(f"  [{i}] text='{text}' visible={visible} class='{classes}'")
        print(f"       parent: <{parent.tag_name} class='{parent_class}'>")
        print(f"       gp:     <{grandparent.tag_name} class='{gp_class}'>")
    except Exception as e:
        print(f"  [{i}] Error: {e}")

# Find all el-dialog related elements
all_dialogs = driver.find_elements(By.XPATH, '//*[contains(@class,"el-dialog")]')
print(f"\n=== All el-dialog related elements ({len(all_dialogs)}) ===")
for i, d in enumerate(all_dialogs):
    try:
        tag = d.tag_name
        classes = (d.get_attribute('class') or '')[:80]
        style = (d.get_attribute('style') or '')[:60]
        visible = d.is_displayed()
        title_els = d.find_elements(By.XPATH, './/*[contains(@class,"el-dialog__title")]')
        title = title_els[0].text.strip() if title_els else '[no title]'
        print(f"  [{i}] <{tag} class='{classes}' visible={visible} title='{title}'")
        print(f"       style='{style}'")
    except Exception as e:
        print(f"  [{i}] Error: {e}")

input("\nPress Enter to close...")
base.close_browser()
