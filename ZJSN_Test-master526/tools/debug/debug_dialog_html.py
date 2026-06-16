# -*- coding: utf-8 -*-
"""调试新增考试弹窗 — 使用框架登录，分析关联试卷下拉框结构"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from base.browser_driver import BaseDriver, ensure_logged_in
from page.personnel_page.ExamManagePage import ExamManagePage

base = BaseDriver()
driver = base.open_browser()
try:
    # 1. 登录 + 导航到考试管理
    ensure_logged_in(driver)
    time.sleep(2)
    page = ExamManagePage(driver)
    page.navigate_to_exam_management()
    time.sleep(2)

    # 2. 截图当前列表
    driver.save_screenshot("debug_list.png")

    # 3. 点击新增考试
    page.click_add()
    time.sleep(1.5)
    driver.save_screenshot("debug_dialog.png")

    # 4. 获取弹窗完整 HTML
    dialogs = driver.find_elements(By.XPATH, '//div[contains(@class,"el-dialog")]')
    print(f"\n弹窗数: {len(dialogs)}")
    for i, d in enumerate(dialogs):
        print(f"\n=== 弹窗 {i+1} 完整 HTML ===")
        html = d.get_attribute("outerHTML")
        print(html)

    # 5. 找到"关联试卷"表单项
    item_xpath = '//div[contains(@class,"el-dialog")]//div[contains(@class,"el-form-item")][.//label[contains(.,"关联试卷")]]'
    items = driver.find_elements(By.XPATH, item_xpath)
    print(f"\n\n=== '关联试卷' 表单项: {len(items)} 个 ===")
    for idx, item in enumerate(items):
        print(f"\n--- 第{idx+1}个 ---")
        html = item.get_attribute("outerHTML")
        print(html)

        # 列出所有子元素
        print("\n子元素 (2层):")
        children = item.find_elements(By.XPATH, './/*')
        for c in children:
            tag = c.tag_name
            cls = c.get_attribute("class") or ""
            _id = c.get_attribute("id") or ""
            style = c.get_attribute("style") or ""
            print(f"  <{tag}> class='{cls}' id='{_id}' style='{style[:80]}'")

    # 6. 检查所有 el-select__wrapper
    wrappers = driver.find_elements(By.XPATH, '//div[contains(@class,"el-select")]')
    print(f"\n=== 所有 el-select 相关元素 ({len(wrappers)}) ===")
    for w in wrappers:
        html = w.get_attribute("outerHTML")
        print(f"  {html[:300]}\n")

    # 7. 检查是否有原生 select
    native_selects = driver.find_elements(By.XPATH, '//select')
    print(f"\n=== 原生 <select> 元素: {len(native_selects)} ===")
    for s in native_selects:
        html = s.get_attribute("outerHTML")
        print(f"  {html}")

    # 8. 检查 el-autocomplete
    autos = driver.find_elements(By.XPATH, '//div[contains(@class,"el-autocomplete")]')
    print(f"\n=== el-autocomplete: {len(autos)} ===")
    for a in autos:
        html = a.get_attribute("outerHTML")
        print(f"  {html[:300]}")

    # 9. 尝试手动点击"关联试卷"下拉并调试
    print("\n\n=== 调试：手动触发下拉框 ===")
    form_item = items[0] if items else None
    if form_item:
        # 尝试点击各种可能的目标
        click_targets = [
            ('.//div[contains(@class,"el-select__wrapper")]', "el-select__wrapper"),
            ('.//div[contains(@class,"el-select")]', "el-select"),
            ('.//input', "input"),
            ('.//div[contains(@class,"el-input")]', "el-input"),
        ]
        for xp, name in click_targets:
            els = form_item.find_elements(By.XPATH, xp)
            print(f"\n{name} ({len(els)}):")
            for el in els:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                    time.sleep(0.2)
                    print(f"  visible={el.is_displayed()}, enabled={el.is_enabled()}")
                    driver.execute_script("arguments[0].click();", el)
                    time.sleep(0.5)
                    # 检查是否有弹出层
                    popups = driver.find_elements(By.XPATH,
                        '//li[contains(@class,"el-select-dropdown__item") and not(contains(@style,"display: none"))]')
                    print(f"  点击后可见选项数: {len(popups)}")
                    for p in popups[:5]:
                        print(f"    选项: '{p.text.strip()}'")
                    if popups:
                        # 点击第一个
                        driver.execute_script("arguments[0].click();", popups[0])
                        time.sleep(0.3)
                        print("  已选择第一个选项")
                        break
                except Exception as ex:
                    print(f"  Error: {ex}")

    # 10. 截图操作后的状态
    driver.save_screenshot("debug_after_select.png")
    print("\n截图已保存: debug_list.png, debug_dialog.png, debug_after_select.png")

finally:
    input("\n按回车关闭浏览器...")
    driver.quit()
