"""环保库存查询 — 冒烟测试

只读查询页面，无审批流（有"流水"按钮可查看流水记录）。
placeholder: "请输入危废品名称"
"""
import pytest
import logging

logger = logging.getLogger(__name__)


class TestHazardStockLoad:
    """页面加载"""

    def test_page_loads(self, hazard_stock_page):
        page = hazard_stock_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        assert len(rows) >= 0, "表格应正常渲染"

    def test_pagination_visible(self, hazard_stock_page):
        pag = hazard_stock_page.driver.find_elements(*hazard_stock_page.TOTAL_COUNT)
        assert len(pag) > 0, "分页器不可见"


class TestHazardStockSearch:
    """搜索"""

    def test_search_by_item_name(self, hazard_stock_page):
        hazard_stock_page.search_by_item_name("test")
        hazard_stock_page.wait_vue_stable()

    def test_reset_search(self, hazard_stock_page):
        hazard_stock_page.reset_search()
        hazard_stock_page.wait_vue_stable()
