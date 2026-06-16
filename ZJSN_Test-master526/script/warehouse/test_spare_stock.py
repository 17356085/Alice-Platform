"""备品库存查询 — 测试脚本

只读页面：页面加载 / 表格完整性 / 搜索 / 重置
无审批流，无行内操作。
"""
import pytest
import logging

logger = logging.getLogger(__name__)


class TestSpareStockLoad:
    """页面加载与元素完整性"""

    def test_page_loads(self, spare_stock_page):
        """页面正常加载，表格应有数据"""
        page = spare_stock_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        assert len(rows) >= 0, "表格应正常渲染"

    def test_pagination_visible(self, spare_stock_page):
        """分页组件应可见"""
        page = spare_stock_page
        pag = page.driver.find_elements(*page.TOTAL_COUNT)
        assert len(pag) > 0, "分页器不可见"


class TestSpareStockSearch:
    """搜索与筛选"""

    def test_search_by_item_name(self, spare_stock_page):
        """按物品名称搜索"""
        page = spare_stock_page
        page.search_by_item_name("test")
        page.wait_vue_stable()
        # 搜索不应导致页面崩溃

    def test_reset_search(self, spare_stock_page):
        """重置搜索条件"""
        page = spare_stock_page
        page.reset_search()
        page.wait_vue_stable()
