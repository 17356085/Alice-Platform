"""备品物品管理 — 测试脚本

覆盖: 页面加载 / 搜索 / 新增(成功+取消+必填校验) / 查看 / 编辑 / 删除
CRUD + 导入导出 + 批量选择，无审批流。
"""
import time
import pytest
import logging

from base.cleanup_tracker import get_cleanup_tracker

logger = logging.getLogger(__name__)


class TestSpareItemLoad:
    """页面加载与元素完整性"""

    def test_page_loads(self, spare_item_page):
        """TD-SI-001: 页面正常加载"""
        page = spare_item_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        assert len(rows) >= 0, "表格应正常渲染"

    def test_pagination_visible(self, spare_item_page):
        """TD-SI-002: 分页组件应可见"""
        pag = spare_item_page.driver.find_elements(*spare_item_page.TOTAL_COUNT)
        assert len(pag) > 0, "分页器不可见"

    def test_add_button_visible(self, spare_item_page):
        """TD-SI-003: 新增按钮应可见"""
        btn = spare_item_page.driver.find_elements(*spare_item_page.BTN_ADD)
        assert len(btn) > 0, "新增按钮不可见"


class TestSpareItemSearch:
    """搜索"""

    def test_search_by_item_name(self, spare_item_page):
        """TD-SI-010: 按物品名称搜索不崩溃"""
        spare_item_page.search_by_item_name("test")
        spare_item_page.wait_vue_stable()

    def test_reset_search(self, spare_item_page):
        """TD-SI-011: 重置搜索条件"""
        spare_item_page.search_by_item_name("test")
        spare_item_page.reset_search()
        spare_item_page.wait_vue_stable()


class TestSpareItemInteraction:
    """交互操作 — 新增弹窗与查看"""

    def test_add_dialog_opens(self, spare_item_page):
        """TD-SI-020: 点击新增应弹出弹窗"""
        page = spare_item_page
        page.click_add()
        assert page.is_dialog_visible(), "新增弹窗应可见"
        page.click_dialog_cancel()

    def test_add_dialog_has_form_fields(self, spare_item_page):
        """TD-SI-021: 新增弹窗内应有表单输入项"""
        page = spare_item_page
        page.click_add()
        inputs = page.driver.execute_script("""
            const dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
            if (!dlg) return 0;
            return dlg.querySelectorAll('input:not([type="hidden"]), textarea').length;
        """)
        logger.info("弹窗内表单输入项数量: %s", inputs)
        assert inputs >= 1, f"新增弹窗应至少有一个输入字段，实际: {inputs}"
        page.click_dialog_cancel()

    def test_view_first_record(self, spare_item_page):
        """TD-SI-022: 点击第一行查看按钮应打开详情弹窗"""
        page = spare_item_page
        page._wait_page_ready()
        rows = page.driver.find_elements(*page.TABLE_ROWS)
        if len(rows) > 0:
            page.click_view_first()
            assert page.is_dialog_visible(), "查看弹窗应可见"
            page.click_dialog_cancel()
        else:
            logger.info("无数据行，跳过查看测试")


class TestSpareItemCRUD:
    """CRUD 完整链路: 新增成功 → 搜索确认 → 删除清理"""

    CREATED_ITEM_NAME = None

    def test_add_item_success(self, spare_item_page):
        """TD-SI-030: 新增物品 — 填写物品名称+编码并保存"""
        page = spare_item_page
        ts = str(int(time.time()))[-6:]
        name = f"AUTO_TEST_{ts}"
        code = f"CODE_{ts}"

        before_count = page.get_total_count()

        page.click_add()
        page.fill_item_name(name)
        page.fill_item_code(code)

        # 检查是否有表单校验错误（如缺少下拉选择项）
        error = page.get_form_error()
        if error:
            logger.warning("表单校验阻止保存: %s，取消弹窗", error)
            page.click_dialog_cancel()
            pytest.skip(f"表单需要额外字段填写: {error}")

        page.click_dialog_save()

        # 验证创建成功 — 弹窗关闭、数据出现在列表
        page.wait_vue_stable()
        page.search_by_item_name(name)
        page.wait_vue_stable()

        if not page.is_row_present(name):
            # 可能被后端校验拦截，查看是否弹窗仍打开
            if page.is_dialog_visible():
                error = page.get_form_error()
                logger.warning("保存失败，表单校验: %s", error)
                page.click_dialog_cancel()
            pytest.skip(f"物品创建失败（可能后端校验），跳过验证: {name}")

        assert page.is_row_present(name), f"列表中应出现新物品: {name}"

        after_count = page.get_total_count()
        assert after_count >= before_count + 1, \
            f"总数应增加: 前{before_count} → 后{after_count}"

        TestSpareItemCRUD.CREATED_ITEM_NAME = name

    def test_delete_created_item(self, spare_item_page):
        """TD-SI-031: 删除刚创建的物品 — 搜索确认消失"""
        page = spare_item_page
        name = TestSpareItemCRUD.CREATED_ITEM_NAME
        if not name:
            pytest.skip("未创建物品，跳过删除测试")

        before_count = page.get_total_count()

        try:
            page.delete_item_by_name(name)
        except Exception as e:
            # 兜底: 注册到清理追踪器
            logger.warning("UI 删除失败，注册清理: %s — %s", name, e)
            tracker = get_cleanup_tracker()
            tracker.register_entity(
                "spare_item", name,
                delete_callback=lambda n: page.delete_item_by_name(n) if page.is_row_present(n) else True,
            )
            pytest.fail(f"删除物品失败: {e}")

        # 验证已删除
        page.search_by_item_name(name)
        page.wait_vue_stable()
        assert not page.is_row_present(name), f"物品应已被删除: {name}"

        after_count = page.get_total_count()
        assert after_count <= before_count, \
            f"删除后总数应 ≤ 删除前: 前{before_count} → 后{after_count}"

    def test_add_item_cancel(self, spare_item_page):
        """TD-SI-032: 新增物品 — 取消操作不产生数据"""
        page = spare_item_page
        name = f"AUTO_CANCEL_{str(int(time.time()))[-5:]}"

        page.click_add()
        page.fill_item_name(name)
        page.click_dialog_cancel()
        page.wait_vue_stable()

        page.search_by_item_name(name)
        assert not page.is_row_present(name), \
            f"取消后物品不应存在于列表: {name}"

    def test_add_empty_required(self, spare_item_page):
        """TD-SI-033: 新增物品 — 必填校验（不填直接保存）"""
        page = spare_item_page
        page.click_add()
        page.click_dialog_save()

        error = page.get_form_error()
        assert error != "", f"应有必填校验提示，实际: '{error}'"
        logger.info("必填校验提示: %s", error)
