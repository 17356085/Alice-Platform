"""化验室取样模块 conftest — 水质分析对比

提供 module-scope driver 和 Page Object fixture。
"""

import pytest
import allure
from selenium import webdriver
from base.browser_driver import BaseDriver
from page.lab_page.LabComparePage import LabComparePage as WaterComparePage


@pytest.fixture(scope="module")
def driver_setup():
    """Module-scope 浏览器驱动，确保统一登录与页面准备"""
    base_driver = BaseDriver()
    driver = base_driver.open_browser()
    try:
        base_driver.ensure_logged_in(driver)
        yield driver
    finally:
        driver.quit()


@pytest.fixture(scope="module")
def water_compare_page(driver_setup):
    """水质分析对比 Page Object fixture，自动导航到页面"""
    driver = driver_setup
    page = WaterComparePage(driver=driver)
    page.navigate()
    yield page
    # 数据清理：查询操作不产生数据，无清理逻辑
    # 若后续增加增删改操作，请在此处添加清理逻辑
    # try:
    #     page.click_reset()
    # except Exception as e:
    #     print(f"[WARNING] 清理失败: {e}")