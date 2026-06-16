"""Debug: properly click the department select and see options"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.browser_driver import BaseDriver, ensure_logged_in
from base.sidebar_navigator import SidebarNavigator

base = BaseDriver()
driver = None
try:
    driver = base.open_browser()
    driver.maximize_window()
    ensure_logged_in(driver)
    nav = SidebarNavigator(driver)
    nav.navigate_to("系统管理", "用户管理")
    time.sleep(3)

    # Click 新增
    driver.execute_script("""
        var btns = document.querySelectorAll('button');
        for (var i = 0; i < btns.length; i++) {
            if (btns[i].innerText && btns[i].innerText.trim() === '新增') {
                btns[i].click();
                break;
            }
        }
    """)
    time.sleep(2)

    # Click the department select via Selenium's ActionChains or click
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC

    # Find the dialog and the department select
    dlg = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".el-dialog"))
    )

    # Find all form items, get the one with label "部门"
    form_items = dlg.find_elements(By.CSS_SELECTOR, ".el-form-item")
    dept_item = None
    for item in form_items:
        label = item.find_element(By.CSS_SELECTOR, ".el-form-item__label")
        if "部门" in label.text:
            dept_item = item
            break

    if dept_item:
        print("Found department form item")
        # Click the select wrapper
        select_wrapper = dept_item.find_element(By.CSS_SELECTOR, ".el-select__wrapper, .el-select")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", select_wrapper)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", select_wrapper)
        print("Clicked select wrapper")
        time.sleep(2)

        # Now check for dropdown options
        options = driver.find_elements(By.CSS_SELECTOR, ".el-select-dropdown__item")
        print(f"Options found: {len(options)}")
        for opt in options[:10]:
            print(f"  {opt.text}")

        if len(options) > 0:
            # Pick 人力行政部
            for opt in options:
                if "人力行政部" in opt.text:
                    driver.execute_script("arguments[0].click();", opt)
                    print(f"Selected: {opt.text}")
                    break
            time.sleep(1)
        else:
            # Maybe in a popper
            popper_opts = driver.find_elements(By.CSS_SELECTOR, ".el-popper .el-select-dropdown__item")
            print(f"Popper options: {len(popper_opts)}")
            for opt in popper_opts[:10]:
                print(f"  {opt.text}")
            # Check all visible elements
            all_visible = driver.execute_script("""
                var result = [];
                document.querySelectorAll('.el-select-dropdown__item').forEach(function(item){
                    if(item.offsetWidth > 0 || item.offsetParent !== null) {
                        result.push(item.innerText);
                    }
                });
                return result;
            """)
            print(f"Visible dropdown items: {all_visible}")

            # Also try the popper approach
            popper_items = driver.execute_script("""
                var items = [];
                document.querySelectorAll('.el-popper').forEach(function(p){
                    if(p.offsetWidth > 0) {
                        p.querySelectorAll('.el-select-dropdown__item, li').forEach(function(li){
                            items.push(li.innerText.trim());
                        });
                    }
                });
                return items;
            """)
            print(f"Visible popper items: {popper_items}")

    # Close dialog
    driver.execute_script("""
        var dlg = document.querySelector('.el-dialog');
        if (dlg) {
            var btn = dlg.querySelector('.el-dialog__footer button:not(.el-button--primary)');
            if (btn) btn.click();
        }
    """)
    time.sleep(1)

finally:
    if driver:
        try: driver.quit()
        except: pass
