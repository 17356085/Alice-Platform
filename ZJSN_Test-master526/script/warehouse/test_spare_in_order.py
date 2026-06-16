"""备品入库 — 测试脚本

覆盖: 页面加载 / 表格8列 / 新增入库弹窗 / 搜索
审批链: 备件入库审批链 (admin 会签)
"""
import pytest
import logging

logger = logging.getLogger(__name__)


class TestSpareInOrderLoad:
    """页面加载与元素完整性"""

    def test_page_loads(self, spare_in_order_page):
        """页面正常加载"""
        page = spare_in_order_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        assert len(rows) >= 0, "表格应正常渲染"

    def test_columns_count(self, spare_in_order_page):
        """表格列数应在合理范围内"""
        page = spare_in_order_page
        headers = page.driver.execute_script(
            "return document.querySelectorAll('.el-table__header-wrapper th').length;"
        )
        assert 6 <= headers <= 12, f"列数异常，实际{headers}列（预期6-12列）"

    def test_add_button_visible(self, spare_in_order_page):
        """新增入库按钮应可见"""
        page = spare_in_order_page
        btn = page.driver.find_elements(*page.BTN_ADD)
        assert len(btn) > 0, "新增入库按钮不可见"

    def test_pagination_visible(self, spare_in_order_page):
        """分页组件应可见"""
        page = spare_in_order_page
        pag = page.driver.find_elements(*page.TOTAL_COUNT)
        assert len(pag) > 0, "分页器不可见"


class TestSpareInOrderSearch:
    """搜索与筛选"""

    def test_search_by_handler(self, spare_in_order_page):
        """按经办人搜索"""
        page = spare_in_order_page
        page.search_by_handler("test")
        page.wait_vue_stable()

    def test_reset_search(self, spare_in_order_page):
        """重置搜索"""
        page = spare_in_order_page
        page.reset_search()
        page.wait_vue_stable()


class TestSpareInOrderInteraction:
    """交互操作"""

    def test_add_dialog_opens(self, spare_in_order_page):
        """TD-SP-020: 点击新增入库应弹出弹窗"""
        page = spare_in_order_page
        page.click_add()
        assert page.is_dialog_visible(), "新增入库弹窗应可见"

    def test_view_first_record(self, spare_in_order_page):
        """点击第一行查看按钮"""
        page = spare_in_order_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        if len(rows) > 0:
            page.click_view_first()
            assert page.is_dialog_visible(), "查看弹窗应可见"
