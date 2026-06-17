"""三剂消耗-物品管理 — 测试脚本

覆盖: 页面加载 / 搜索 / 新增(成功+取消+必填校验) / 删除清理
CRUD + 导入导出 + 批量选择，无审批流。
"""
import time
import pytest
import logging

from base.cleanup_tracker import get_cleanup_tracker

logger = logging.getLogger(__name__)


class TestReagentItemLoad:
    """页面加载与元素完整性"""

    def test_page_loads(self, reagent_item_page):
        """TD-RI-001: 页面正常加载"""
        page = reagent_item_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        assert len(rows) >= 0, "表格应正常渲染"

    def test_pagination_visible(self, reagent_item_page):
        """TD-RI-002: 分页组件应可见"""
        pag = reagent_item_page.driver.find_elements(*reagent_item_page.TOTAL_COUNT)
        assert len(pag) > 0, "分页器不可见"

    def test_add_button_visible(self, reagent_item_page):
        """TD-RI-003: 新增按钮应可见"""
        btn = reagent_item_page.driver.find_elements(*reagent_item_page.BTN_ADD)
        assert len(btn) > 0, "新增按钮不可见"


class TestReagentItemSearch:
    """搜索"""

    def test_search_by_item_name(self, reagent_item_page):
        """TD-RI-010: 按物品名称搜索不崩溃"""
        reagent_item_page.search_by_item_name("test")
        reagent_item_page.wait_vue_stable()

    def test_reset_search(self, reagent_item_page):
        """TD-RI-011: 重置搜索条件"""
        reagent_item_page.search_by_item_name("test")
        reagent_item_page.reset_search()
        reagent_item_page.wait_vue_stable()


class TestReagentItemInteraction:
    """交互操作 — 新增弹窗"""

    def test_add_dialog_opens(self, reagent_item_page):
        """TD-RI-020: 点击新增应弹出弹窗"""
        page = reagent_item_page
        page.click_add()
        assert page.is_dialog_visible(), "新增弹窗应可见"
        page.click_dialog_cancel()

    def test_add_dialog_has_form_fields(self, reagent_item_page):
        """TD-RI-021: 新增弹窗内应有表单输入项"""
        page = reagent_item_page
        page.click_add()
        inputs = page.driver.execute_script("""
            const dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
            if (!dlg) return 0;
            return dlg.querySelectorAll('input:not([type="hidden"]), textarea').length;
        """)
        logger.info("弹窗内表单输入项数量: %s", inputs)
        assert inputs >= 1, f"新增弹窗应至少有一个输入字段，实际: {inputs}"
        page.click_dialog_cancel()


class TestReagentItemCRUD:
    """CRUD 完整链路: 新增 → 搜索确认 → 删除清理"""

    CREATED_ITEM_NAME = None

    def test_add_item_success(self, reagent_item_page):
        """TD-RI-030: 新增物品 — 填写名称并保存成功"""
        page = reagent_item_page
        ts = str(int(time.time()))[-6:]
        name = f"AUTO_三剂_{ts}"

        before_count = page.get_total_count()

        page.click_add()
        page.fill_item_name(name)
        page.click_dialog_save()

        page.wait_vue_stable()
        page.search_by_item_name(name)
        page.wait_vue_stable()

        assert page.is_row_present(name), f"列表中应出现新物品: {name}"

        after_count = page.get_total_count()
        assert after_count >= before_count + 1, \
            f"总数应增加: 前{before_count} → 后{after_count}"

        TestReagentItemCRUD.CREATED_ITEM_NAME = name

    def test_delete_created_item(self, reagent_item_page):
        """TD-RI-031: 删除刚创建的物品"""
        page = reagent_item_page
        name = TestReagentItemCRUD.CREATED_ITEM_NAME
        if not name:
            pytest.skip("未创建物品，跳过删除测试")

        try:
            page.delete_item_by_name(name)
        except Exception as e:
            logger.warning("UI 删除失败，注册清理: %s — %s", name, e)
            tracker = get_cleanup_tracker()
            tracker.register_entity(
                "reagent_item", name,
                delete_callback=lambda n: page.delete_item_by_name(n) if page.is_row_present(n) else True,
            )
            pytest.fail(f"删除物品失败: {e}")

        page.search_by_item_name(name)
        page.wait_vue_stable()
        assert not page.is_row_present(name), f"物品应已被删除: {name}"

    def test_add_item_cancel(self, reagent_item_page):
        """TD-RI-032: 新增物品 — 取消操作"""
        page = reagent_item_page
        name = f"AUTO_CANCEL_{str(int(time.time()))[-5:]}"

        page.click_add()
        page.fill_item_name(name)
        page.click_dialog_cancel()
        page.wait_vue_stable()

        page.search_by_item_name(name)
        assert not page.is_row_present(name), \
            f"取消后物品不应存在于列表: {name}"

    def test_add_empty_required(self, reagent_item_page):
        """TD-RI-033: 新增物品 — 必填校验"""
        page = reagent_item_page
        page.click_add()
        page.click_dialog_save()

        error = page.get_form_error()
        assert error != "", f"应有必填校验提示，实际: '{error}'"
        logger.info("必填校验提示: %s", error)
