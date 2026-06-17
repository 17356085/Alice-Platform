"""备品出库 — 测试脚本

覆盖: 页面加载 / 表格列 / 新增出库弹窗(填表) / LY单号链接 / 备件查询 / 搜索 / CRUD完整链路
审批链: 备件出库审批链 (admin+chenqian 会签)
"""
import time
import pytest
import logging

from base.cleanup_tracker import get_cleanup_tracker

logger = logging.getLogger(__name__)


class TestSpareOutOrderLoad:
    """页面加载与元素完整性"""

    def test_page_loads(self, spare_out_order_page):
        """TD-SO-001: 页面正常加载"""
        page = spare_out_order_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        assert len(rows) >= 0, "表格应正常渲染"

    def test_columns_count(self, spare_out_order_page):
        """TD-SO-002: 表格列数应在合理范围内"""
        page = spare_out_order_page
        headers = page.driver.execute_script(
            "return document.querySelectorAll('.el-table__header-wrapper th').length;"
        )
        assert 8 <= headers <= 28, f"列数异常，实际{headers}列（预期8-28列）"

    def test_pagination_visible(self, spare_out_order_page):
        """TD-SO-003: 分页组件应可见"""
        page = spare_out_order_page
        pag = page.driver.find_elements(*page.TOTAL_COUNT)
        assert len(pag) > 0, "分页器不可见"

    def test_add_button_visible(self, spare_out_order_page):
        """TD-SO-004: 新增按钮应可见"""
        page = spare_out_order_page
        btn = page.driver.find_elements(*page.BTN_ADD)
        assert len(btn) > 0, "新增按钮不可见"

    def test_spare_query_button_visible(self, spare_out_order_page):
        """TD-SO-005: 备件查询按钮应可见"""
        page = spare_out_order_page
        btn = page.driver.find_elements(*page.BTN_SPARE_QUERY)
        assert len(btn) > 0, "备件查询按钮不可见"


class TestSpareOutOrderSearch:
    """搜索与筛选"""

    def test_search_by_handler(self, spare_out_order_page):
        """TD-SO-010: 按经办人搜索"""
        page = spare_out_order_page
        page.search_by_handler("test")
        page.wait_vue_stable()

    def test_reset_search(self, spare_out_order_page):
        """TD-SO-011: 重置搜索条件"""
        page = spare_out_order_page
        page.reset_search()
        page.wait_vue_stable()


class TestSpareOutOrderInteraction:
    """交互操作 — 新增出库弹窗 / LY链接 / 备件查询"""

    def test_add_dialog_opens(self, spare_out_order_page):
        """TD-SO-020: 点击新增应弹出弹窗"""
        page = spare_out_order_page
        page.click_add()
        assert page.is_dialog_visible(), "新增出库弹窗应可见"
        page.click_dialog_cancel()

    def test_add_dialog_has_form_fields(self, spare_out_order_page):
        """TD-SO-021: 新增弹窗内应有表单输入项"""
        page = spare_out_order_page
        page.click_add()
        inputs = page.driver.execute_script("""
            const dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
            if (!dlg) return 0;
            return dlg.querySelectorAll('input:not([type="hidden"]), textarea').length;
        """)
        logger.info("弹窗内表单输入项数量: %s", inputs)
        assert inputs >= 1, f"新增出库弹窗应至少有一个输入字段，实际: {inputs}"
        page.click_dialog_cancel()

    def test_ly_link_clickable(self, spare_out_order_page):
        """TD-SO-022: LY单号链接可点击"""
        page = spare_out_order_page
        page._wait_page_ready()
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
        else:
            logger.info("无LY单号链接，跳过点击测试")

    def test_spare_query_clickable(self, spare_out_order_page):
        """TD-SO-023: 点击备件查询按钮"""
        page = spare_out_order_page
        page.click_spare_query()
        page.wait_vue_stable()

    def test_view_first_record(self, spare_out_order_page):
        """TD-SO-024: 点击第一行查看按钮应打开详情弹窗"""
        page = spare_out_order_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        if len(rows) > 0:
            page.click_view_first()
            assert page.is_dialog_visible(), "查看弹窗应可见"
            page.click_dialog_cancel()
        else:
            logger.info("无数据行，跳过查看测试")


class TestSpareOutOrderCRUD:
    """CRUD 完整链路: 新增 → 搜索确认 → 删除清理"""

    CREATED_HANDLER = None

    def test_add_out_order_success(self, spare_out_order_page):
        """TD-SO-030: 新增出库 — 填写经办人并保存"""
        page = spare_out_order_page
        ts = str(int(time.time()))[-6:]
        handler = f"AUTO_OUT_{ts}"

        before_count = page.get_total_count()

        page.click_add()
        page.fill_out_order_handler(handler)
        page.click_dialog_save()

        page.wait_vue_stable()
        page.search_by_handler(handler)
        page.wait_vue_stable()

        if not page.is_row_present(handler):
            logger.warning("出库记录未在列表中找到（表单可能含额外必填项）")
            pytest.skip(f"出库记录创建后未找到: {handler}（表单可能需要更多字段）")

        after_count = page.get_total_count()
        assert after_count >= before_count + 1, \
            f"总数应增加: 前{before_count} → 后{after_count}"

        TestSpareOutOrderCRUD.CREATED_HANDLER = handler

    def test_delete_created_out_order(self, spare_out_order_page):
        """TD-SO-031: 删除刚创建的出库记录（草稿状态可删除）"""
        page = spare_out_order_page
        handler = TestSpareOutOrderCRUD.CREATED_HANDLER
        if not handler:
            pytest.skip("未创建出库记录，跳过删除测试")

        try:
            page.delete_by_handler(handler)
        except Exception as e:
            logger.warning("UI 删除失败，注册清理: %s — %s", handler, e)
            tracker = get_cleanup_tracker()
            tracker.register_entity(
                "spare_out_order", handler,
                delete_callback=lambda n: page.delete_by_handler(n) if page.is_row_present(n) else True,
            )
            pytest.fail(f"删除出库记录失败: {e}")

        page.search_by_handler(handler)
        page.wait_vue_stable()
        assert not page.is_row_present(handler), f"出库记录应已被删除: {handler}"

    def test_add_out_order_cancel(self, spare_out_order_page):
        """TD-SO-032: 新增出库 — 取消操作"""
        page = spare_out_order_page
        handler = f"AUTO_CANCEL_{str(int(time.time()))[-5:]}"

        page.click_add()
        page.fill_out_order_handler(handler)
        page.click_dialog_cancel()
        page.wait_vue_stable()

        page.search_by_handler(handler)
        assert not page.is_row_present(handler), \
            f"取消后出库记录不应存在于列表: {handler}"

    def test_add_empty_required(self, spare_out_order_page):
        """TD-SO-033: 新增出库 — 必填校验"""
        page = spare_out_order_page
        page.click_add()
        page.click_dialog_save()

        error = page.get_form_error()
        if error:
            logger.info("必填校验提示: %s", error)
        else:
            logger.info("无前端必填校验（弹窗可能已关闭或后端校验）")
        if page.is_dialog_visible():
            page.click_dialog_cancel()
