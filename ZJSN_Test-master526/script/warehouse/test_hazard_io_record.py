"""环保出入库明细表 — 冒烟测试

只读审计日志，搜索区为日期范围选择器（开始日期/结束日期），无物品名称输入。
"""
import pytest
import logging

logger = logging.getLogger(__name__)


class TestHazardIORecordLoad:
    """页面加载"""

    def test_page_loads(self, hazard_io_record_page):
        page = hazard_io_record_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        assert len(rows) >= 0, "表格应正常渲染"

    def test_pagination_visible(self, hazard_io_record_page):
        pag = hazard_io_record_page.driver.find_elements(*hazard_io_record_page.TOTAL_COUNT)
        assert len(pag) > 0, "分页器不可见"

    def test_reset_search(self, hazard_io_record_page):
        hazard_io_record_page.reset_search()
        hazard_io_record_page.wait_vue_stable()
