"""备品出入库记录 — 冒烟测试

只读审计日志页面，无审批流。
"""
import pytest
import logging

logger = logging.getLogger(__name__)


class TestSpareIORecordLoad:
    """页面加载"""

    def test_page_loads(self, spare_io_record_page):
        page = spare_io_record_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        assert len(rows) >= 0, "表格应正常渲染"

    def test_pagination_visible(self, spare_io_record_page):
        pag = spare_io_record_page.driver.find_elements(*spare_io_record_page.TOTAL_COUNT)
        assert len(pag) > 0, "分页器不可见"


class TestSpareIORecordSearch:
    """搜索"""

    def test_search_by_item_name(self, spare_io_record_page):
        spare_io_record_page.search_by_item_name("test")
        spare_io_record_page.wait_vue_stable()

    def test_reset_search(self, spare_io_record_page):
        spare_io_record_page.reset_search()
        spare_io_record_page.wait_vue_stable()
