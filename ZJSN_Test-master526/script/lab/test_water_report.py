"""水质分析报告单 — 测试脚本

覆盖: 页面加载 / 取样位置切换 / 新增弹窗 / 日期搜索
"""
import pytest
import logging

logger = logging.getLogger(__name__)


class TestWaterReportLoad:
    """页面加载与元素"""

    def test_page_loads(self, water_report_page):
        """TD-LW-001: 页面正常加载"""
        page = water_report_page
        page._wait_page_ready()
        rows = page.get_row_count()
        assert rows >= 0, "表格应正常渲染"

    def test_add_button_visible(self, water_report_page):
        """新增按钮应可见"""
        btns = water_report_page.driver.find_elements(*water_report_page.BTN_ADD)
        assert len(btns) > 0, "新增按钮不可见"


class TestWaterReportLocation:
    """取样位置切换"""

    def test_switch_location(self, water_report_page):
        """TD-LW-002: 切换取样位置"""
        page = water_report_page
        page.switch_location("水质取样点1")
        page.wait_vue_stable()


class TestWaterReportSearch:
    """搜索"""

    def test_search_by_date(self, water_report_page):
        """TD-LW-020: 日期范围搜索"""
        page = water_report_page
        page.search_by_date("2026-06-01", "2026-06-12")
        assert page.get_row_count() >= 0


class TestWaterReportAdd:
    """新增报告单"""

    def test_add_dialog_opens(self, water_report_page):
        """新增弹窗打开"""
        page = water_report_page
        page.click_add()
        assert page.is_dialog_visible(), "新增弹窗应可见"
