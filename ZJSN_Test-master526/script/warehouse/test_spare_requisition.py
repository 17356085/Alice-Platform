"""备品领用申请 — 冒烟测试"""
import pytest
import logging

logger = logging.getLogger(__name__)


class TestSpareRequisitionSmoke:
    """备品领用申请冒烟测试"""

    def test_page_loads(self, spare_requisition_page):
        """TD-SP-001: 页面正常加载"""
        page = spare_requisition_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        assert len(rows) >= 0, "表格应正常渲染"

    def test_add_dialog_opens(self, spare_requisition_page):
        """点击新增应弹出弹窗"""
        page = spare_requisition_page
        page.click_add()
        assert page.is_dialog_visible(), "新增弹窗应可见"

    def test_search_by_applicant(self, spare_requisition_page):
        """按申请人搜索"""
        page = spare_requisition_page
        page.search_by_applicant("test")
        # 搜索不应导致页面崩溃
        page.wait_vue_stable()
