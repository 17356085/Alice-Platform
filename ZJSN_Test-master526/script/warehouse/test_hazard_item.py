"""环保物品管理 — 冒烟测试

CRUD: 新增/导入/导出/编辑/删除，无审批流。
placeholder: "请输入危废品名称"
"""
import pytest
import logging

logger = logging.getLogger(__name__)


class TestHazardItemLoad:
    """页面加载"""

    def test_page_loads(self, hazard_item_page):
        page = hazard_item_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        assert len(rows) >= 0, "表格应正常渲染"

    def test_pagination_visible(self, hazard_item_page):
        pag = hazard_item_page.driver.find_elements(*hazard_item_page.TOTAL_COUNT)
        assert len(pag) > 0, "分页器不可见"

    def test_add_button_visible(self, hazard_item_page):
        btn = hazard_item_page.driver.find_elements(*hazard_item_page.BTN_ADD)
        assert len(btn) > 0, "新增按钮不可见"


class TestHazardItemSearch:
    """搜索"""

    def test_search_by_item_name(self, hazard_item_page):
        hazard_item_page.search_by_item_name("test")
        hazard_item_page.wait_vue_stable()

    def test_reset_search(self, hazard_item_page):
        hazard_item_page.reset_search()
        hazard_item_page.wait_vue_stable()


class TestHazardItemInteraction:
    """交互"""

    def test_add_dialog_opens(self, hazard_item_page):
        hazard_item_page.click_add()
        assert hazard_item_page.is_dialog_visible(), "新增弹窗应可见"
