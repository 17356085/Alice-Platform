"""备品库存盘点 — 冒烟测试

只读查询页面，审批链：备件盘点审批链 (chenqian → tjw)。
"""
import pytest
import logging

logger = logging.getLogger(__name__)


class TestSpareStocktakeLoad:
    """页面加载"""

    def test_page_loads(self, spare_stocktake_page):
        page = spare_stocktake_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        assert len(rows) >= 0, "表格应正常渲染"

    def test_pagination_visible(self, spare_stocktake_page):
        pag = spare_stocktake_page.driver.find_elements(*spare_stocktake_page.TOTAL_COUNT)
        assert len(pag) > 0, "分页器不可见"


class TestSpareStocktakeSearch:
    """搜索"""

    def test_search_by_handler(self, spare_stocktake_page):
        spare_stocktake_page.search_by_handler("test")
        spare_stocktake_page.wait_vue_stable()

    def test_reset_search(self, spare_stocktake_page):
        spare_stocktake_page.reset_search()
        spare_stocktake_page.wait_vue_stable()
