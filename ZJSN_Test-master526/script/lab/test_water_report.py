"""lab 模块共享 conftest（P1-2 合并）"""

import pytest
import allure
from base.browser_driver import BaseDriver
from page.lab_page.WaterAnalysisReportPage import WaterAnalysisReportPage as WaterReportPage


@pytest.fixture(scope="module")
def driver_setup():
    """module scope driver: 打开浏览器 → 登录 → 跳转到 lab 模块首页"""
    bd = BaseDriver()
    driver = bd.open_browser()
    driver.get(bd.base_url + "/#/lab/water/report")
    bd.ensure_logged_in()
    yield driver
    # teardown
    try:
        driver.quit()
    except Exception as e:
        import warnings
        warnings.warn(f"driver teardown failed: {e}")


@pytest.fixture(scope="module")
def water_report_page(driver_setup):
    """WaterReportPage fixture: 实例化并 navigate() 确保页面就绪"""
    page = WaterReportPage(driver_setup)
    page.navigate()
    return page