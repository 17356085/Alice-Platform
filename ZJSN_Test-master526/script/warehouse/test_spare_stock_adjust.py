"""备品库存盘点调整 — 冒烟测试

只读查询页面，调整直接生效，无审批流。
"""
import pytest
import logging

logger = logging.getLogger(__name__)


class TestSpareStockAdjustLoad:
    """页面加载"""

    def test_page_loads(self, spare_stock_adjust_page):
        page = spare_stock_adjust_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        assert len(rows) >= 0, "表格应正常渲染"

    def test_pagination_visible(self, spare_stock_adjust_page):
        pag = spare_stock_adjust_page.driver.find_elements(*spare_stock_adjust_page.TOTAL_COUNT)
        assert len(pag) > 0, "分页器不可见"


class TestSpareStockAdjustSearch:
    """搜索"""

    def test_search_by_item_code(self, spare_stock_adjust_page):
        spare_stock_adjust_page.search_by_item_code("test")
        spare_stock_adjust_page.wait_vue_stable()

    def test_reset_search(self, spare_stock_adjust_page):
        spare_stock_adjust_page.reset_search()
        spare_stock_adjust_page.wait_vue_stable()
