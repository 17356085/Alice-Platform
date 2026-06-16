# -*- coding: utf-8 -*-
"""调试考试管理弹窗结构"""
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)
try:
    driver.get("http://42.180.131.36:8081")
    time.sleep(3)

    # 登录
    driver.find_element(By.XPATH, '//input[@placeholder="请输入账号"]').send_keys("admin")
    driver.find_element(By.XPATH, '//input[@placeholder="请输入密码"]').send_keys(os.getenv("DEFAULT_PASSWORD"))
    driver.find_element(By.XPATH, "//button[.//span[contains(text(),'登录')]]").click()
    time.sleep(5)

    # 导航到考试管理
    driver.find_element(By.XPATH, '//*[@id="app"]/div/div[2]/div[2]/div[1]/div/ul/li[3]/div/span').click()
    time.sleep(1)
    driver.find_element(By.XPATH, '//*[@id="app"]/div/div[2]/div[2]/div[1]/div/ul/li[3]/ul/li/div/span').click()
    time.sleep(1)

    # 找考试管理菜单
    exam_menus = driver.find_elements(
        By.XPATH, '//*[@id="app"]/div/div[2]/div[2]/div[1]/div/ul/li[3]/ul/li/ul//span[contains(text(),"考试管理")]'
    )
    print(f"考试管理菜单: {len(exam_menus)} 个")
    if exam_menus:
        driver.execute_script("arguments[0].click();", exam_menus[0])
        time.sleep(3)

    # 截图列表页
    driver.save_screenshot("debug_exam_list.png")

    # 点击新增考试
    add_btns = driver.find_elements(By.XPATH, "//button[.//span[contains(text(),'新增')]]")
    print(f"新增按钮数: {len(add_btns)}")
    if add_btns:
        for i, btn in enumerate(add_btns):
            try:
                print(f"  按钮{i}: visible={btn.is_displayed()}, text='{btn.text}'")
            except:
                pass
        driver.execute_script("arguments[0].click();", add_btns[0])
        time.sleep(2)

    # 截图弹窗
    driver.save_screenshot("debug_exam_dialog.png")

    # 弹窗HTML
    dialogs = driver.find_elements(By.XPATH, '//div[contains(@class,"el-dialog")]')
    print(f"\n弹窗数: {len(dialogs)}")
    for i, dialog in enumerate(dialogs):
        print(f"\n=== 弹窗 {i+1} HTML (前2000字符) ===")
        try:
            html = dialog.get_attribute("outerHTML")
            print(html[:2000])
        except Exception as e:
            print(f"  Error: {e}")

    # 查找表单label
    labels = driver.find_elements(
        By.XPATH, '//div[contains(@class,"el-dialog")]//label[contains(@class,"el-form-item__label")]'
    )
    print(f"\n=== 表单Label ({len(labels)}) ===")
    for lb in labels:
        print(f'  label: "{lb.text.strip()}"')

    # 查找所有input
    inputs = driver.find_elements(By.XPATH, '//div[contains(@class,"el-dialog")]//input')
    print(f"\n=== Input ({len(inputs)}) ===")
    for inp in inputs:
        placeholder = inp.get_attribute("placeholder") or ""
        _type = inp.get_attribute("type") or ""
        _class = inp.get_attribute("class") or ""
        print(f'  type={_type}, placeholder="{placeholder}", class="{_class[:60]}"')

    # 查找所有el-select
    selects = driver.find_elements(
        By.XPATH, '//div[contains(@class,"el-dialog")]//div[contains(@class,"el-select")]'
    )
    print(f"\n=== el-select组件 ({len(selects)}) ===")
    for sel in selects:
        try:
            wrapper = sel.find_element(By.XPATH, './/div[contains(@class,"el-select__wrapper")]')
            selected = wrapper.find_element(By.XPATH, './/span[contains(@class,"el-select__selected-item")]')
            print(f'  selected: "{selected.text.strip()}"')
        except:
            try:
                print(f'  html(200): {sel.get_attribute("outerHTML")[:200]}')
            except:
                pass

    print("\n截图已保存: debug_exam_list.png, debug_exam_dialog.png")

finally:
    input("\n按回车关闭浏览器...")
    driver.quit()
