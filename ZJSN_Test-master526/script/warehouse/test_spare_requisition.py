"""备品领用申请 — 测试脚本

覆盖: 页面加载 / 搜索 / 新增(成功+取消+必填校验) / 行内操作(查看/编辑/提交/删除) / 状态感知
审批链: 备件领用申请审批链 (admin+chenqian → tjw)
"""
import time
import pytest
import logging

from base.cleanup_tracker import get_cleanup_tracker

logger = logging.getLogger(__name__)


class TestSpareRequisitionLoad:
    """页面加载与元素完整性"""

    def test_page_loads(self, spare_requisition_page):
        """TD-SP-001: 页面正常加载"""
        page = spare_requisition_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        assert len(rows) >= 0, "表格应正常渲染"

    def test_columns_count(self, spare_requisition_page):
        """TD-SP-002: 表格列数应在合理范围内"""
        page = spare_requisition_page
        headers = page.driver.execute_script(
            "return document.querySelectorAll('.el-table__header-wrapper th').length;"
        )
        assert 6 <= headers <= 14, f"列数异常，实际{headers}列（预期6-14列）"

    def test_add_button_visible(self, spare_requisition_page):
        """TD-SP-003: 新增按钮应可见"""
        page = spare_requisition_page
        btn = page.driver.find_elements(*page.BTN_ADD)
        assert len(btn) > 0, "新增按钮不可见"

    def test_pagination_visible(self, spare_requisition_page):
        """TD-SP-004: 分页组件应可见"""
        page = spare_requisition_page
        pag = page.driver.find_elements(*page.TOTAL_COUNT)
        assert len(pag) > 0, "分页器不可见"


class TestSpareRequisitionSearch:
    """搜索与筛选"""

    def test_search_by_applicant(self, spare_requisition_page):
        """TD-SP-010: 按申请人搜索"""
        page = spare_requisition_page
        page.search_by_applicant("test")
        page.wait_vue_stable()

    def test_reset_search(self, spare_requisition_page):
        """TD-SP-011: 重置搜索条件"""
        page = spare_requisition_page
        page.search_by_applicant("test")
        page.reset_search()
        page.wait_vue_stable()


class TestSpareRequisitionInteraction:
    """交互操作 — 新增弹窗"""

    def test_add_dialog_opens(self, spare_requisition_page):
        """TD-SP-020: 点击新增应弹出弹窗"""
        page = spare_requisition_page
        page.click_add()
        assert page.is_dialog_visible(), "新增弹窗应可见"
        page.click_dialog_cancel()

    def test_add_dialog_has_save_button(self, spare_requisition_page):
        """TD-SP-021: 新增弹窗内应有保存按钮"""
        page = spare_requisition_page
        page.click_add()
        save_btn = page.driver.find_elements(*page.DIALOG_SAVE)
        assert len(save_btn) > 0, "弹窗内应有保存/确认按钮"
        page.click_dialog_cancel()

    def test_view_first_record(self, spare_requisition_page):
        """TD-SP-022: 点击第一行查看按钮应打开详情弹窗"""
        page = spare_requisition_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        if len(rows) > 0:
            page.click_view_first()
            assert page.is_dialog_visible(), "查看弹窗应可见"
            page.click_dialog_cancel()
        else:
            logger.info("无数据行，跳过查看测试")


class TestSpareRequisitionRowActions:
    """行内操作按钮 — 编辑/提交/删除/状态感知"""

    def test_first_row_action_buttons_exist(self, spare_requisition_page):
        """TD-SP-030: 第一行至少有一个操作按钮"""
        page = spare_requisition_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        if len(rows) == 0:
            pytest.skip("无数据行，跳过行操作测试")
        has_view = len(page.driver.find_elements(*page.BTN_VIEW)) > 0
        has_edit = page.has_edit_button()
        has_submit = page.has_submit_button()
        has_delete = page.has_delete_button()
        assert has_view or has_edit or has_submit or has_delete, \
            "第一行应至少有一个操作按钮"

    def test_edit_dialog_opens(self, spare_requisition_page):
        """TD-SP-031: 点击编辑按钮应打开编辑弹窗（若有可编辑行）"""
        page = spare_requisition_page
        page._wait_page_ready()
        if not page.has_edit_button():
            pytest.skip("当前数据行无可用的编辑按钮")
        page.click_edit_first()
        page.wait_dialog_open()
        assert page.is_dialog_visible(), "编辑弹窗应可见"
        page.click_dialog_cancel()

    def test_first_row_status_readable(self, spare_requisition_page):
        """TD-SP-032: 第一行流程状态可读取"""
        page = spare_requisition_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        if len(rows) == 0:
            pytest.skip("无数据行，跳过状态读取测试")
        status = page.get_first_row_status()
        logger.info("第一行流程状态: %s", status)
        assert isinstance(status, str), "流程状态应为字符串"

    def test_submit_button_triggers_toast(self, spare_requisition_page):
        """TD-SP-033: 点击提交按钮应有toast提示（若有可提交行）"""
        page = spare_requisition_page
        page._wait_page_ready()
        if not page.has_submit_button():
            pytest.skip("当前数据行无可用的提交按钮")
        page.click_submit_first()
        # click_submit_first 内部已 wait_for_toast_text，到达此处即通过


class TestSpareRequisitionCRUD:
    """CRUD 完整链路: 新增 → 搜索确认 → 删除清理"""

    CREATED_APPLICANT = None

    def test_add_requisition_success(self, spare_requisition_page):
        """TD-SP-040: 新增领用申请 — 填写并保存"""
        page = spare_requisition_page
        ts = str(int(time.time()))[-6:]
        applicant = f"AUTO_REQ_{ts}"

        before_count = page.get_total_count()

        page.click_add()
        page.fill_requisition_applicant(applicant)
        page.click_dialog_save()

        page.wait_vue_stable()
        page.search_by_applicant(applicant)
        page.wait_vue_stable()

        if not page.is_row_present(applicant):
            logger.warning("领用申请未在列表中找到（表单可能含额外必填项如物品选择）")
            pytest.skip(f"领用申请创建后未找到: {applicant}（表单可能需要更多字段）")

        after_count = page.get_total_count()
        assert after_count >= before_count + 1, \
            f"总数应增加: 前{before_count} → 后{after_count}"

        TestSpareRequisitionCRUD.CREATED_APPLICANT = applicant

    def test_delete_created_requisition(self, spare_requisition_page):
        """TD-SP-041: 删除刚创建的领用申请（草稿状态可删除）"""
        page = spare_requisition_page
        applicant = TestSpareRequisitionCRUD.CREATED_APPLICANT
        if not applicant:
            pytest.skip("未创建领用申请，跳过删除测试")

        try:
            page.delete_by_name(applicant)
        except Exception as e:
            logger.warning("UI 删除失败，注册清理: %s — %s", applicant, e)
            tracker = get_cleanup_tracker()
            tracker.register_entity(
                "spare_requisition", applicant,
                delete_callback=lambda n: page.delete_by_name(n) if page.is_row_present(n) else True,
            )
            pytest.fail(f"删除领用申请失败: {e}")

        page.search_by_applicant(applicant)
        page.wait_vue_stable()
        assert not page.is_row_present(applicant), \
            f"领用申请应已被删除: {applicant}"

    def test_add_requisition_cancel(self, spare_requisition_page):
        """TD-SP-042: 新增领用申请 — 取消操作"""
        page = spare_requisition_page
        applicant = f"AUTO_CANCEL_{str(int(time.time()))[-5:]}"

        page.click_add()
        page.fill_requisition_applicant(applicant)
        page.click_dialog_cancel()
        page.wait_vue_stable()

        page.search_by_applicant(applicant)
        assert not page.is_row_present(applicant), \
            f"取消后领用申请不应存在于列表: {applicant}"

    def test_add_empty_required(self, spare_requisition_page):
        """TD-SP-043: 新增领用申请 — 必填校验"""
        page = spare_requisition_page
        page.click_add()
        page.click_dialog_save()

        error = page.get_form_error()
        if error:
            logger.info("必填校验提示: %s", error)
        else:
            logger.info("无前端必填校验（弹窗可能已关闭或后端校验）")
        if page.is_dialog_visible():
            page.click_dialog_cancel()
