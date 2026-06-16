"""Inspect the add training plan dialog's DOM structure for save button"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

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

# Get the visible dialog
dialogs = driver.find_elements(By.XPATH, '//div[contains(@class,"el-dialog")][not(contains(@style,"display: none"))]')
print(f"\n=== Visible dialogs: {len(dialogs)} ===")
dialog = dialogs[-1]  # last one

# Print the dialog's HTML
html = dialog.get_attribute('outerHTML')
print("\n=== Dialog outerHTML (first 3000 chars) ===")
print(html[:3000])

# Look for buttons specifically
buttons = dialog.find_elements(By.XPATH, './/button')
print(f"\n=== Buttons in dialog: {len(buttons)} ===")
for btn in buttons:
    try:
        text = btn.text.strip()
        class_name = btn.get_attribute('class')
        style = btn.get_attribute('style')
        html2 = btn.get_attribute('outerHTML')[:200]
        print(f"\n  Button text='{text}'")
        print(f"  Class: {class_name[:80]}")
        print(f"  HTML: {html2}")
    except Exception as e:
        print(f"  Error: {e}")

# Check what footer-like elements exist
footers = dialog.find_elements(By.XPATH, './/*[contains(@class, "footer") or self::footer]')
print(f"\n=== Footer elements: {len(footers)} ===")
for f in footers:
    print(f"  Tag: {f.tag_name}, class: {f.get_attribute('class')[:60]}")

# Try the most basic xpath to find "保存" button
try:
    btn = driver.find_element(By.XPATH, '//button[.//span[contains(text(),"保存")]]')
    print(f"\n=== Found '保存' button globally ===")
    print(f"  Text: '{btn.text}'")
    print(f"  Tag: {btn.tag_name}")
    print(f"  Class: {btn.get_attribute('class')}")
    print(f"  OuterHTML: {btn.get_attribute('outerHTML')[:300]}")

    # Find its parent structure
    parent = btn.find_element(By.XPATH, '..')
    print(f"  Parent tag: {parent.tag_name}, class: {parent.get_attribute('class')}")
    grandparent = parent.find_element(By.XPATH, '..')
    print(f"  Grandparent tag: {grandparent.tag_name}, class: {grandparent.get_attribute('class')}")
except Exception as e:
    print(f"\n=== No '保存' button found: {e} ===")

# Also try "确定"
try:
    btn = driver.find_element(By.XPATH, '//button[.//span[contains(text(),"确定")]]')
    print(f"\n=== Found '确定' button globally ===")
    print(f"  Text: '{btn.text}'")
    print(f"  Class: {btn.get_attribute('class')}")
    print(f"  OuterHTML: {btn.get_attribute('outerHTML')[:300]}")
except Exception as e:
    print(f"\n=== No '确定' button found: {e} ===")

input("\n按回车关闭...")
base.close_browser()
