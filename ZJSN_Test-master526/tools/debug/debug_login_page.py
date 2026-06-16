"""诊断 Selenium 实际打开的登录页 DOM。

运行：
    python debug_login_page.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from base.browser_driver import BaseDriver
from page.system_page.LoginPage import LoginPage


def print_elements(driver, label):
    print(f"\n===== {label} =====")
    print(f"current_url: {driver.current_url}")
    print(f"title: {driver.title}")
    print(f"body text preview: {driver.find_element(By.TAG_NAME, 'body').text[:500]!r}")

    inputs = driver.find_elements(By.XPATH, "//input")
    print(f"input count: {len(inputs)}")
    for index, item in enumerate(inputs, start=1):
        print(
            f"  input[{index}] "
            f"id={item.get_attribute('id')!r} "
            f"type={item.get_attribute('type')!r} "
            f"placeholder={item.get_attribute('placeholder')!r} "
            f"class={item.get_attribute('class')!r} "
            f"displayed={item.is_displayed()}"
        )

    buttons = driver.find_elements(By.XPATH, "//button")
    print(f"button count: {len(buttons)}")
    for index, item in enumerate(buttons, start=1):
        print(
            f"  button[{index}] "
            f"text={item.text!r} "
            f"id={item.get_attribute('id')!r} "
            f"class={item.get_attribute('class')!r} "
            f"displayed={item.is_displayed()}"
        )

    iframes = driver.find_elements(By.XPATH, "//iframe")
    print(f"iframe count: {len(iframes)}")
    for index, item in enumerate(iframes, start=1):
        print(
            f"  iframe[{index}] "
            f"id={item.get_attribute('id')!r} "
            f"name={item.get_attribute('name')!r} "
            f"src={item.get_attribute('src')!r}"
        )

    for name, locator in (
        ("USERNAME_INPUT", LoginPage.USERNAME_INPUT),
        ("PASSWORD_INPUT", LoginPage.PASSWORD_INPUT),
        ("LOGIN_BUTTON", LoginPage.LOGIN_BUTTON),
    ):
        try:
            matches = driver.find_elements(*locator)
            print(f"{name} matches: {len(matches)}")
        except Exception as exc:
            print(f"{name} locator error: {exc}")


def main():
    base = BaseDriver()
    driver = None
    try:
        driver = base.open_browser()
        try:
            WebDriverWait(driver, 60, poll_frequency=1).until(
                lambda item: item.find_elements(By.XPATH, "//input|//button")
                or item.title != "加载中..."
            )
        except Exception:
            print("[WARN] 等待 60 秒后页面仍未渲染出表单元素")
        time.sleep(2)

        print_elements(driver, "default content")

        iframes = driver.find_elements(By.XPATH, "//iframe")
        for index, iframe in enumerate(iframes, start=1):
            driver.switch_to.default_content()
            driver.switch_to.frame(iframe)
            print_elements(driver, f"iframe {index}")

        driver.switch_to.default_content()
        driver.save_screenshot("login_debug.png")
        with open("login_debug.html", "w", encoding="utf-8") as file:
            file.write(driver.page_source)
        print("\n已保存 login_debug.png 和 login_debug.html")
    finally:
        if driver is not None:
            base.close_browser()


if __name__ == "__main__":
    main()
