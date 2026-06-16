"""清理 system-role 测试产生的脏数据

用法: python script/system/cleanup_test_roles.py
清理所有名称以 'test' 开头的测试角色（通过 UI 操作）
"""
import os, sys, time
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from base.browser_driver import BaseDriver, ensure_logged_in
from page.system_role_page.RoleManagePage import RoleManagePage
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def cleanup():
    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)
        page = RoleManagePage(driver)
        page.navigate_to("系统管理", "角色管理")

        # 重置搜索条件
        page.click_reset()
        time.sleep(1)

        # 搜索所有 test 开头的角色
        page.input_role_name("test")
        page.click_search()

        # 等待表格渲染（用 WebDriverWait 等待行出现或空状态出现）
        try:
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr")) > 0
                or len(d.find_elements(By.CSS_SELECTOR, ".el-table__empty-text")) > 0
            )
        except:
            pass
        time.sleep(1)

        names = page.get_column_data(2)
        test_names = [n for n in names if n.startswith("test")]
        print(f"Found {len(test_names)} test roles: {test_names}")

        deleted = 0
        for name in test_names:
            try:
                print(f"  Deleting: {name}")
                page.search(role_name=name)
                time.sleep(1)
                WebDriverWait(driver, 10).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr")) > 0
                    or len(d.find_elements(By.CSS_SELECTOR, ".el-table__empty-text")) > 0
                )
                page.select_role_checkbox_by_name(name)
                page.click_delete()
                page.confirm_message_box()
                msg = page.wait_for_toast_text(timeout=10)
                print(f"    Toast: {msg}")
                deleted += 1
            except Exception as e:
                print(f"    Failed: {e}")

        print(f"\nCleaned up: {deleted}/{len(test_names)} test roles")
    finally:
        base.close_browser()

if __name__ == "__main__":
    cleanup()
