"""化验室取样模块共享 fixtures"""
import pytest


@pytest.fixture(scope="session")
def lab_logged_in_driver(session_logged_in_browser):
    """Session 级 fixture：已登录的浏览器驱动"""
    yield session_logged_in_browser


@pytest.fixture(scope="session")
def gas_report_page(lab_logged_in_driver):
    """气体分析报告单"""
    from page.lab_page.GasAnalysisReportPage import GasAnalysisReportPage
    page = GasAnalysisReportPage(lab_logged_in_driver)
    page.navigate()
    return page


@pytest.fixture(scope="function")
def gas_indicator_page(lab_logged_in_driver):
    """气体分析设计指标"""
    from page.lab_page.LabIndicatorPage import LabIndicatorPage
    page = LabIndicatorPage(lab_logged_in_driver, sub="gas")
    page.navigate()
    return page


@pytest.fixture(scope="function")
def water_indicator_page(lab_logged_in_driver):
    """水质分析设计指标"""
    from page.lab_page.LabIndicatorPage import LabIndicatorPage
    page = LabIndicatorPage(lab_logged_in_driver, sub="water")
    page.navigate()
    return page


@pytest.fixture(scope="function")
def gas_compare_page(lab_logged_in_driver):
    """气体分析对比"""
    from page.lab_page.LabComparePage import LabComparePage
    page = LabComparePage(lab_logged_in_driver, sub="gas")
    page.navigate()
    return page


@pytest.fixture(scope="function")
def water_compare_page(lab_logged_in_driver):
    """水质分析对比"""
    from page.lab_page.LabComparePage import LabComparePage
    page = LabComparePage(lab_logged_in_driver, sub="water")
    page.navigate()
    return page


@pytest.fixture(scope="function")
def water_report_page(lab_logged_in_driver):
    """水质分析报告单"""
    from page.lab_page.WaterAnalysisReportPage import WaterAnalysisReportPage
    page = WaterAnalysisReportPage(lab_logged_in_driver)
    page.navigate()
    return page
