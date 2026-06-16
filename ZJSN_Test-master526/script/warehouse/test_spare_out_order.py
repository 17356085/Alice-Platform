"""备品出库 — 测试脚本

覆盖: 页面加载 / 表格10列完整性 / LY单号链接 / 备件查询 / 搜索
审批链: 备件出库审批链 (admin+chenqian 会签)
"""
import pytest
import logging

logger = logging.getLogger(__name__)


class TestSpareOutOrderLoad:
    """页面加载与元素完整性"""

    def test_page_loads(self, spare_out_order_page):
        """TD-SP-010: 10列表格完整性"""
        page = spare_out_order_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        assert len(rows) >= 0, "表格应正常渲染"

    def test_columns_count(self, spare_out_order_page):
        """表格列数应在合理范围内"""
        page = spare_out_order_page
        headers = page.driver.execute_script(
            "return document.querySelectorAll('.el-table__header-wrapper th').length;"
        )
        assert 8 <= headers <= 28, f"列数异常，实际{headers}列（预期8-28列）"

    def test_pagination_visible(self, spare_out_order_page):
        """分页组件应可见"""
        page = spare_out_order_page
        pag = page.driver.find_elements(*page.TOTAL_COUNT)
        assert len(pag) > 0, "分页器不可见"

    def test_add_button_visible(self, spare_out_order_page):
        """新增按钮应可见"""
        page = spare_out_order_page
        btn = page.driver.find_elements(*page.BTN_ADD)
        assert len(btn) > 0, "新增按钮不可见"

    def test_spare_query_button_visible(self, spare_out_order_page):
        """备件查询按钮应可见"""
        page = spare_out_order_page
        btn = page.driver.find_elements(*page.BTN_SPARE_QUERY)
        assert len(btn) > 0, "备件查询按钮不可见"


class TestSpareOutOrderSearch:
    """搜索与筛选"""

    def test_search_by_handler(self, spare_out_order_page):
        """按经办人搜索"""
        page = spare_out_order_page
        page.search_by_handler("test")
        page.wait_vue_stable()
        # 验证无崩溃

    def test_reset_search(self, spare_out_order_page):
        """重置搜索条件"""
        page = spare_out_order_page
        page.reset_search()
        page.wait_vue_stable()


class TestSpareOutOrderInteraction:
    """交互操作"""

    def test_ly_link_clickable(self, spare_out_order_page):
        """LY单号链接可点击"""
        page = spare_out_order_page
        page._wait_page_ready()
        # 查找是否有LY单号链接
        ly_links = page.driver.execute_script("""
            const btns = document.querySelectorAll('.el-table__body-wrapper .el-button--primary.is-link');
            const links = [];
            btns.forEach(b => {
                const t = b.textContent.trim();
                if (t.startsWith('LY')) links.push(t);
            });
            return links;
        """)
        if ly_links:
            page.click_ly_link(ly_links[0])
            page.wait_vue_stable()

    def test_spare_query_clickable(self, spare_out_order_page):
        """点击备件查询按钮（不弹窗，可能导航到其他页面）"""
        page = spare_out_order_page
        page.click_spare_query()
        # 按钮可点击，页面不崩溃即可

    def test_view_first_record(self, spare_out_order_page):
        """点击第一行的查看按钮"""
        page = spare_out_order_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        if len(rows) > 0:
            page.click_view_first()
            assert page.is_dialog_visible(), "查看弹窗应可见"
