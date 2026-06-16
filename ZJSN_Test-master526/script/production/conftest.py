"""生产管理模块共享 fixtures

模块路由：
  - 日报表管理          #/production/daily-report
  - 交接班日报表        #/production/shift-report
  - 生产月报表          #/production/monthly-report
  - 班次班组配置        #/production/shift-team-config
  - 业务类型配置        #/production/business-type-config
"""
import logging

import pytest

from base.browser_driver import BaseDriver, ensure_logged_in
from page.production_page.DailyReportPage import DailyReportPage
from page.production_page.MonthlyReportPage import MonthlyReportPage
from page.production_page.ShiftTeamConfigPage import ShiftTeamConfigPage
from page.production_page.BusinessTypeConfigPage import BusinessTypeConfigPage

logger = logging.getLogger(__name__)

_MODULE_HASH_ROUTES = {
    "test_daily_report": "#/production/daily-report",
    "test_shift_report": "#/production/shift-report",
    "test_monthly_report": "#/production/monthly-report",
    "test_shift_team_config": "#/production/shift-team-config",
    "test_business_type_config": "#/production/business-type-config",
}


@pytest.fixture(scope="module")
def driver_setup(request):
    """Module 级：登录并返回 browser driver

    导航职责已下沉到各 page fixture（daily_report_page / monthly_report_page 等），
    避免双重 hash 设置触发 Vue Router 竞态。
    """
    base = BaseDriver()
    driver = base.open_browser()
    try:
        ensure_logged_in(driver)
        yield driver
    finally:
        base.close_browser()


@pytest.fixture(scope="function")
def daily_report_page(driver_setup):
    """日报表管理页面 — 已导航并等待渲染完成"""
    page = DailyReportPage(driver_setup)
    page.navigate_to_daily_report()
    yield page
    # 测试后清理：关闭所有可能残留的弹窗（按 Escape 键关闭 el-dialog）
    try:
        driver_setup.execute_script("""
            // 关闭所有可见的 el-dialog
            var dialogs = document.querySelectorAll('.el-dialog');
            dialogs.forEach(function(d) {
                if (d.offsetParent !== null) {
                    var closeBtn = d.querySelector('.el-dialog__headerbtn');
                    if (closeBtn) closeBtn.click();
                }
            });
            // 关闭所有遮罩
            var overlays = document.querySelectorAll('.el-overlay');
            overlays.forEach(function(o) {
                if (o.offsetParent !== null) o.click();
            });
        """)
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.by import By
        body = driver_setup.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.ESCAPE)
    except Exception:
        pass  # 清理失败不影响测试结果


@pytest.fixture(scope="function")
def monthly_report_page(driver_setup):
    """生产月报表页面 — 已导航并等待渲染完成"""
    page = MonthlyReportPage(driver_setup)
    page.navigate_to_monthly_report()
    yield page
    # 测试后清理
    try:
        driver_setup.execute_script("""
            var dialogs = document.querySelectorAll('.el-dialog');
            dialogs.forEach(function(d) {
                if (d.offsetParent !== null) {
                    var closeBtn = d.querySelector('.el-dialog__headerbtn');
                    if (closeBtn) closeBtn.click();
                }
            });
            var overlays = document.querySelectorAll('.el-overlay');
            overlays.forEach(function(o) {
                if (o.offsetParent !== null) o.click();
            });
        """)
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.by import By
        body = driver_setup.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.ESCAPE)
    except Exception:
        pass


@pytest.fixture(scope="function")
def shift_team_config_page(driver_setup):
    """班次班组配置页面 — 已导航并等待渲染完成"""
    page = ShiftTeamConfigPage(driver_setup)
    page.navigate_to_page()
    yield page
    try:
        driver_setup.execute_script("""
            var dialogs = document.querySelectorAll('.el-dialog');
            dialogs.forEach(function(d) {
                if (d.offsetParent !== null) {
                    var closeBtn = d.querySelector('.el-dialog__headerbtn');
                    if (closeBtn) closeBtn.click();
                }
            });
        """)
        from selenium.webdriver.common.keys import Keys
        driver_setup.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    except Exception:
        pass


@pytest.fixture(scope="function")
def business_type_config_page(driver_setup):
    """业务类型配置页面 — 已导航并等待渲染完成"""
    page = BusinessTypeConfigPage(driver_setup)
    page.navigate_to_page()
    yield page
    try:
        driver_setup.execute_script("""
            var dialogs = document.querySelectorAll('.el-dialog');
            dialogs.forEach(function(d) {
                if (d.offsetParent !== null) {
                    var closeBtn = d.querySelector('.el-dialog__headerbtn');
                    if (closeBtn) closeBtn.click();
                }
            });
        """)
        from selenium.webdriver.common.keys import Keys
        driver_setup.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    except Exception:
        pass
