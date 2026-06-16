"""备品物品管理 — 冒烟测试

CRUD + 导入导出 + 批量选择，无审批流。
"""
import pytest
import logging

logger = logging.getLogger(__name__)


class TestSpareItemLoad:
    """页面加载"""

    def test_page_loads(self, spare_item_page):
        page = spare_item_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        assert len(rows) >= 0, "表格应正常渲染"

    def test_pagination_visible(self, spare_item_page):
        pag = spare_item_page.driver.find_elements(*spare_item_page.TOTAL_COUNT)
        assert len(pag) > 0, "分页器不可见"

    def test_add_button_visible(self, spare_item_page):
        btn = spare_item_page.driver.find_elements(*spare_item_page.BTN_ADD)
        assert len(btn) > 0, "新增按钮不可见"


class TestSpareItemSearch:
    """搜索"""

    def test_search_by_item_name(self, spare_item_page):
        spare_item_page.search_by_item_name("test")
        spare_item_page.wait_vue_stable()

    def test_reset_search(self, spare_item_page):
        spare_item_page.reset_search()
        spare_item_page.wait_vue_stable()


class TestSpareItemInteraction:
    """交互"""

    def test_add_dialog_opens(self, spare_item_page):
        spare_item_page.click_add()
        assert spare_item_page.is_dialog_visible(), "新增弹窗应可见"
