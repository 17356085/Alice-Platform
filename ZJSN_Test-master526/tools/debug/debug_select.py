# -*- coding: utf-8 -*-
"""逐步调试关联试卷下拉框"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from base.browser_driver import BaseDriver, ensure_logged_in
from page.personnel_page.ExamManagePage import ExamManagePage

base = BaseDriver()
driver = base.open_browser()
try:
    ensure_logged_in(driver)
    time.sleep(2)
    page = ExamManagePage(driver)
    page.navigate_to_exam_management()
    time.sleep(2)

    # 点击新增
    page.click_add()
    time.sleep(1.5)

    # 输入考试名称
    page.input_dialog_field("考试名称", "debug_test")

    # 1. 查看所有 form-item label
    labels = driver.find_elements(By.XPATH, '//div[contains(@class,"el-dialog")]//label[contains(@class,"el-form-item__label")]')
    print("=== 所有表单label ===")
    for lb in labels:
        print(f"  label: '{lb.text.strip()}'")

    # 2. 查看"关联试卷"form item的完整HTML
    item = driver.find_element(By.XPATH,
        '//div[contains(@class,"el-dialog")]//div[contains(@class,"el-form-item")][.//label[contains(.,"关联试卷")]]')
    print("\n=== '关联试卷' form item HTML ===")
    print(item.get_attribute("outerHTML"))

    # 3. 查看form item内所有子元素
    print("\n=== 所有子元素 ===")
    all_els = item.find_elements(By.XPATH, './/*')
    for el in all_els:
        tag = el.tag_name
        cls = el.get_attribute("class") or ""
        visible = el.is_displayed() if el.tag_name != "script" else True
        rect = driver.execute_script("var r=arguments[0].getBoundingClientRect(); return {top:r.top,left:r.left,width:r.width,height:r.height};", el)
        print(f"  <{tag}> class='{cls}' visible={visible} rect={rect}")

    # 4. 尝试不同的点击方式
    print("\n=== 尝试点击 el-select__wrapper (JS click) ===")
    try:
        wrapper = item.find_element(By.XPATH, './/div[contains(@class,"el-select__wrapper")]')
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", wrapper)
        time.sleep(0.2)
        driver.execute_script("arguments[0].click();", wrapper)
        time.sleep(1)
        options = driver.find_elements(By.XPATH, '//li[contains(@class,"el-select-dropdown__item")]')
        print(f"  选项数: {len(options)}")
        expanded = wrapper.get_attribute("aria-expanded") or "N/A"
        print(f"  aria-expanded: {expanded}")
    except Exception as e:
        print(f"  Error: {e}")

    # 5. 尝试点击 el-select__input
    print("\n=== 尝试点击 el-select__input (ActionChains) ===")
    try:
        inp = item.find_element(By.XPATH, './/input[contains(@class,"el-select__input")]')
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", inp)
        time.sleep(0.2)
        ActionChains(driver).move_to_element(inp).click().perform()
        time.sleep(1)
        options = driver.find_elements(By.XPATH, '//li[contains(@class,"el-select-dropdown__item")]')
        print(f"  选项数: {len(options)}")
        expanded = inp.get_attribute("aria-expanded") or "N/A"
        print(f"  aria-expanded: {expanded}")
    except Exception as e:
        print(f"  Error: {e}")

    # 6. 查看页面所有 el-popper / select-dropdown
    print("\n=== 所有 el-popper (可能显示下拉) ===")
    poppers = driver.find_elements(By.XPATH, '//div[contains(@class,"el-popper")]')
    print(f"  数量: {len(poppers)}")
    for p in poppers:
        html = p.get_attribute("outerHTML")[:300]
        visible = p.is_displayed() if p.is_displayed() else "checking..."
        print(f"  visible={p.is_displayed()}, html={html}")

    # 7. 检查页面上所有的 el-select__popper
    select_poppers = driver.find_elements(By.XPATH, '//div[contains(@class,"el-select__popper")]')
    print(f"\n=== el-select__popper: {len(select_poppers)} ===")
    for p in select_poppers:
        html = p.get_attribute("outerHTML")[:500]
        print(f"  html: {html}")

    # 8. 看 dialog 的 z-index 和 overlay
    print("\n=== 弹窗 overlay ===")
    overlays = driver.find_elements(By.XPATH, '//div[contains(@class,"el-overlay")]')
    for o in overlays:
        style = o.get_attribute("style") or ""
        z = o.value_of_css_property("z-index") if False else "see style"
        print(f"  style='{style}'")

    driver.save_screenshot("debug_select.png")
    print("\n截图: debug_select.png")
finally:
    input("\n按回车关闭...")
    driver.quit()
