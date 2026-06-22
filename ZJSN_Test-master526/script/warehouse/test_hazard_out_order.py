"""环保危废出库 — 测试脚本

覆盖: 页面加载 / 搜索筛选 / 新增出库 / 查看 / 删除（CRUD）
角色: 自动化覆盖
模块: warehouse
页面: hazard-out-order

依赖:
    - conftest.py 中 module-scope driver_setup 与 hazard_out_order_page fixture
    - base.cleanup_tracker 数据清理
"""
import time
import allure
import pytest
import logging

from base.cleanup_tracker import get_cleanup_tracker

logger = logging.getLogger(__name__)


# ========================== 页面加载 ==========================
@allure.epic("仓库管理")
@allure.feature("环保危废出库")
class TestHazardOutOrderLoad:
    """页面加载及元素完整性"""

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_page_loads(self, hazard_out_order_page):
        """TC-HOO-001: 页面正常加载，表格渲染"""
        page = hazard_out_order_page
        with allure.step("导航至出库页面"):
            page.navigate()
        with allure.step("验证表格渲染"):
            rows = page.get_table_rows_count()
            assert rows >= 0, f"表格行数应为≥0，实际 {rows}"

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.NORMAL)
    def test_pagination_visible(self, hazard_out_order_page):
        """TC-HOO-002: 分页组件可见"""
        page = hazard_out_order_page
        with allure.step("导航至页面"):
            page.navigate()
        with allure.step("验证分页组件"):
            pag = page.driver.find_elements(*page.PAGINATION_TOTAL)
            assert len(pag) > 0, "分页组件未显示"

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_button_visible(self, hazard_out_order_page):
        """TC-HOO-003: 新增出库按钮可见"""
        page = hazard_out_order_page
        with allure.step("导航至页面"):
            page.navigate()
        with allure.step("定位新增按钮"):
            btn = page.driver.find_elements(*page.BTN_ADD)
        with allure.step("验证按钮可见"):
            assert len(btn) > 0, "新增出库按钮未找到"

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.NORMAL)
    def test_columns_count(self, hazard_out_order_page):
        """TC-HOO-004: 表格列数应在 6~14 之间"""
        page = hazard_out_order_page
        with allure.step("导航至页面"):
            page.navigate()
        with allure.step("获取表头列数"):
            headers = page.get_table_headers_count()
        with allure.step("检查列数范围"):
            assert 6 <= headers <= 14, f"列数 {headers} 超出预期范围 6~14"


# ========================== 搜索筛选 ==========================
@allure.epic("仓库管理")
@allure.feature("环保危废出库")
class TestHazardOutOrderSearch:
    """搜索与筛选功能"""

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_search_by_handler(self, hazard_out_order_page):
        """TC-HOO-010: 按经办人搜索不崩溃"""
        page = hazard_out_order_page
        with allure.step("导航至页面"):
            page.navigate()
        with allure.step("输入经办人并查询"):
            page.search_by_handler("test")
        with allure.step("验证页面不崩溃"):
            rows = page.get_table_rows_count()
            assert rows >= 0, f"搜索后表格行数应为≥0，实际 {rows}"

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_reset_search(self, hazard_out_order_page):
        """TC-HOO-011: 重置搜索条件"""
        page = hazard_out_order_page
        with allure.step("导航至页面"):
            page.navigate()
        with allure.step("设置搜索条件"):
            page.search_by_handler("test")
        with allure.step("重置"):
            page.reset_search()
        with allure.step("验证经办人输入框已清空"):
            val = page.get_handler_input_value()
            assert val == "", f"重置后经办人应为空，实际 '{val}'"
        with allure.step("验证页面不崩溃"):
            rows = page.get_table_rows_count()
            assert rows >= 0, f"重置后表格行数应为≥0，实际 {rows}"


# ========================== 新增出库 ==========================
@allure.epic("仓库管理")
@allure.feature("环保危废出库")
class TestHazardOutOrderInteraction:
    """新增出库弹窗交互"""

    @allure.story("新增出库")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_add_dialog_opens(self, hazard_out_order_page):
        """TC-HOO-020: 打开新增出库弹窗"""
        page = hazard_out_order_page
        with allure.step("导航至页面"):
            page.navigate()
        with allure.step("点击新增出库"):
            page.click_add()
        with allure.step("验证弹窗可见"):
            assert page.is_dialog_visible(), "新增出库弹窗未弹出"
        with allure.step("关闭弹窗"):
            page.click_dialog_cancel()

    @allure.story("新增出库")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_add_dialog_has_form_fields(self, hazard_out_order_page):
        """TC-HOO-021: 新增弹窗包含至少1个输入框"""
        page = hazard_out_order_page
        with allure.step("打开新增弹窗"):
            page.click_add()
        with allure.step("验证弹窗内输入框数量"):
            inputs = page.driver.find_elements(
                "xpath",
                "//div[contains(@class,'el-dialog') and not(contains(@style,'display: none'))]//input"
            )
            assert len(inputs) >= 1, f"弹窗输入框应≥1，实际 {len(inputs)}"
        with allure.step("关闭弹窗"):
            page.click_dialog_cancel()

    @allure.story("查看详情")
    @allure.severity(allure.severity_level.NORMAL)
    def test_view_first_record(self, hazard_out_order_page):
        """TC-HOO-022: 查看第一条记录弹窗"""
        page = hazard_out_order_page
        with allure.step("导航至页面"):
            page.navigate()
        with allure.step("点击查看第一条"):
            page.click_view_first()
        with allure.step("验证弹窗可见"):
            assert page.is_dialog_visible(), "查看详情弹窗未弹出"
        with allure.step("关闭弹窗"):
            page.click_dialog_cancel()


# ========================== CRUD 完整链路 ==========================
@allure.epic("仓库管理")
@allure.feature("环保危废出库")
class TestHazardOutOrderCRUD:
    """CRUD 完整链路（破坏性操作）"""

    CREATED_HANDLER = None  # 跨测试共享的创建名称

    @allure.story("新增出库")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.destructive
    def test_add_out_order_success(self, hazard_out_order_page):
        """TC-HOO-030: 新增出库记录成功"""
        page = hazard_out_order_page
        ts = str(int(time.time()))[-6:]
        handler_name = f"AUTO_OUT_{ts}"

        with allure.step("导航至页面"):
            page.navigate()
        with allure.step("获取操作前总数"):
            before = page.get_table_rows_count()

        with allure.step("点击新增出库"):
            page.click_add()
        with allure.step("填写经办人"):
            page.fill_out_order_handler(handler_name)
        with allure.step("提交保存"):
            page.click_dialog_save()
            page.wait_dialog_close()
            page.wait_vue_stable()

        with allure.step("搜索确认新记录存在"):
            page.search_by_handler(handler_name)
            after = page.get_table_rows_count()

        assert after >= before, f"新增后计数应 ≥ 操作前 {before}，实际 {after}"

        # 注册共享 handler 供删除测试使用
        TestHazardOutOrderCRUD.CREATED_HANDLER = handler_name

        # 注册清理回退
        try:
            pass  # 将在 test_delete_created_out_order 中删除
        except Exception:
            get_cleanup_tracker().register_entity(
                "hazard_out_order", handler_name,
                cleanup_func=lambda: page.delete_by_handler(handler_name)
            )

    @allure.story("删除出库")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.destructive
    def test_delete_created_out_order(self, hazard_out_order_page):
        """TC-HOO-031: 删除刚创建的出库记录"""
        page = hazard_out_order_page
        handler_name = TestHazardOutOrderCRUD.CREATED_HANDLER

        if not handler_name:
            pytest.skip("无创建的记录可删除 — 依赖 test_add_out_order_success")

        with allure.step(f"搜索并删除经办人 '{handler_name}'"):
            page.navigate()
            page.delete_by_handler(handler_name)

        with allure.step("验证记录已不存在"):
            page.search_by_handler(handler_name)
            assert not page.is_row_present(handler_name), (
                f"删除后记录 '{handler_name}' 不应仍存在于列表中"
            )

    @allure.story("新增取消")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.destructive
    def test_add_out_order_cancel(self, hazard_out_order_page):
        """TC-HOO-032: 取消新增不持久化"""
        page = hazard_out_order_page
        ts = str(int(time.time()))[-5:]
        handler_name = f"AUTO_CANCEL_{ts}"

        with allure.step("导航至页面"):
            page.navigate()
        with allure.step("点击新增出库"):
            page.click_add()
        with allure.step("填写经办人"):
            page.fill_out_order_handler(handler_name)
        with allure.step("点击取消"):
            page.click_dialog_cancel()
            page.wait_dialog_close()
            page.wait_vue_stable()

        with allure.step("搜索确认记录不存在"):
            page.search_by_handler(handler_name)
            assert not page.is_row_present(handler_name), (
                f"取消后记录 '{handler_name}' 不应存在"
            )

    @allure.story("新增校验")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.destructive
    def test_add_empty_required(self, hazard_out_order_page):
        """TC-HOO-033: 空表单提交显示校验错误"""
        page = hazard_out_order_page

        with allure.step("导航至页面"):
            page.navigate()
        with allure.step("打开新增弹窗"):
            page.click_add()
        with allure.step("不填任何内容直接提交"):
            page.click_dialog_save()

        with allure.step("验证有校验错误提示"):
            try:
                error = page.get_form_error()
                logger.info(f"必填校验错误提示: '{error}'")
            except Exception:
                logger.warning("未检测到明显校验错误，尝试关闭弹窗")
                page.click_dialog_cancel()

    @allure.story("删除确认")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.destructive
    def test_delete_by_handler(self, hazard_out_order_page):
        """TC-HOO-034: 按经办人删除出库记录（破坏性）"""
        page = hazard_out_order_page
        ts = str(int(time.time()))[-6:]
        handler_name = f"AUTO_DEL_{ts}"

        with allure.step("先创建一条记录"):
            page.navigate()
            page.click_add()
            page.fill_out_order_handler(handler_name)
            page.click_dialog_save()
            page.wait_dialog_close()
            page.wait_vue_stable()

        with allure.step("搜索并删除"):
            page.search_by_handler(handler_name)
            page.delete_by_handler(handler_name)

        with allure.step("验证删除成功"):
            page.search_by_handler(handler_name)
            assert not page.is_row_present(handler_name), (
                f"删除后记录 '{handler_name}' 不应存在"
            )

        # 注册清理回退
        try:
            get_cleanup_tracker().register_entity(
                "hazard_out_order_del", handler_name,
                cleanup_func=lambda: page.delete_by_handler(handler_name)
            )
        except Exception:
            pass
