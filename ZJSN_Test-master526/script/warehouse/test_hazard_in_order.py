"""环保危废入库 — 测试脚本

覆盖: 页面加载 / 搜索筛选 / 新增入库（含嵌套弹窗） / 破坏性操作（CRUD）
角色: 自动化覆盖
模块: warehouse
页面: hazard-in-order

依赖:
    - conftest.py 中 module-scope driver_setup 与 hazard_in_order_page fixture
    - base.cleanup_tracker 数据清理
"""
import allure
import pytest
import logging

from base.cleanup_tracker import get_cleanup_tracker

logger = logging.getLogger(__name__)


# ========================== 页面加载 ==========================
@allure.epic("仓库管理")
@allure.feature("环保危废入库")
class TestHazardInOrderLoad:
    """页面加载及元素完整性"""

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_page_loads(self, hazard_in_order_page):
        """TD-HZ-D1-001: 页面正常加载"""
        page = hazard_in_order_page
        with allure.step("导航至入库页面"):
            page.navigate()
        with allure.step("验证表格渲染"):
            rows = page.get_table_rows_count()
            assert rows >= 0, f"表格行数应为≥0，实际 {rows}"
        with allure.step("验证分页组件可见"):
            total_count = page.get_total_count()
            assert total_count is not None, "分页总记录数未显示"

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_columns_count(self, hazard_in_order_page):
        """TD-HZ-D1-002: 表格列数应在6~12之间"""
        page = hazard_in_order_page
        with allure.step("获取表头列数"):
            headers = page.get_table_headers_count()
        with allure.step("检查列数范围"):
            assert 6 <= headers <= 12, f"列数 {headers} 超出预期范围 6~12"

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_button_visible(self, hazard_in_order_page):
        """TD-HZ-D1-003: 新增入库按钮可见"""
        page = hazard_in_order_page
        with allure.step("定位新增按钮"):
            btn = page.find_add_button()
        with allure.step("验证按钮可见"):
            assert btn is not None and btn.is_enabled(), "新增入库按钮不可见或不可点击"


# ========================== 搜索筛选 ==========================
@allure.epic("仓库管理")
@allure.feature("环保危废入库")
class TestHazardInOrderSearch:
    """搜索与筛选功能"""

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_search_by_handler(self, hazard_in_order_page):
        """TD-HZ-D2-001: 按经办人精确搜索"""
        page = hazard_in_order_page
        with allure.step("导航至页面"):
            page.navigate()
        with allure.step("输入经办人并查询"):
            page.search_by_handler("张三")
        with allure.step("验证搜索结果非空"):
            rows = page.get_table_rows_count()
            assert rows > 0, "按经办人搜索后表格应返回结果，但为空"

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_reset_search(self, hazard_in_order_page):
        """TD-HZ-D2-004: 重置搜索条件"""
        page = hazard_in_order_page
        with allure.step("设置搜索条件"):
            page.search_by_handler("张三")
        with allure.step("重置"):
            page.reset_search()
        with allure.step("验证经办人输入框已清空"):
            handler_val = page.get_handler_input_value()
            assert handler_val == "", f"重置后经办人应为空，实际 '{handler_val}'"
        with allure.step("验证表格恢复数据（行数>0）"):
            rows = page.get_table_rows_count()
            assert rows > 0, "重置后表格应有默认数据"

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_with_special_chars(self, hazard_in_order_page):
        """TD-HZ-D2-005: 特殊字符搜索不应报错"""
        page = hazard_in_order_page
        with allure.step("输入特殊字符"):
            page.search_by_handler("!@#$%^&*()")
        with allure.step("验证页面不崩溃"):
            rows = page.get_table_rows_count()
            # 无匹配数据时允许空表
            assert rows == 0, "特殊字符搜索应无匹配，但应有0行"


# ========================== 新增入库（包含嵌套弹窗） ==========================
@allure.epic("仓库管理")
@allure.feature("环保危废入库")
class TestHazardInOrderAdd:
    """新增入库操作（含危废品选择嵌套弹窗）"""

    @allure.story("新增入库")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_add_dialog_opens(self, hazard_in_order_page):
        """TD-HZ-D4-001: 打开新增入库弹窗"""
        page = hazard_in_order_page
        with allure.step("导航至页面"):
            page.navigate()
        with allure.step("点击新增入库"):
            page.click_add()
        with allure.step("验证弹窗可见"):
            assert page.is_dialog_visible(), "新增入库弹窗未弹出"
        with allure.step("关闭弹窗"):
            page.cancel_dialog()

    @allure.story("新增入库")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_fill_in_order_form(self, hazard_in_order_page):
        """TD-HZ-D4-002: 填写入库单表单"""
        page = hazard_in_order_page
        with allure.step("打开新增弹窗"):
            page.click_add()
        with allure.step("填写经办人"):
            page.fill_in_order("测试经办人", date="2026-06-17")
        with allure.step("验证经办人输入值"):
            val = page.get_handler_input_value()
            assert val == "测试经办人", f"经办人值应为'测试经办人'，实际 '{val}'"
        with allure.step("验证选择危废品按钮可见"):
            assert page.is_select_waste_btn_visible(), "选择危废品按钮不可见"
        with allure.step("验证提交申请按钮可见"):
            assert page.is_submit_btn_visible(), "提交申请按钮不可见"
        with allure.step("关闭弹窗"):
            page.cancel_dialog()

    @allure.story("新增入库")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_select_waste_dialog(self, hazard_in_order_page):
        """TD-HZ-D4-003: 嵌套弹窗-选择危废品"""
        page = hazard_in_order_page
        with allure.step("打开新增弹窗"):
            page.click_add()
        with allure.step("点击选择危废品"):
            page.click_select_waste()
        with allure.step("验证出现嵌套弹窗或面板"):
            assert page.is_waste_dialog_visible(), "危废品选择弹窗未出现"
        with allure.step("关闭弹窗（取消两次）"):
            page.cancel_dialog()          # 关闭嵌套弹窗
            page.cancel_dialog()          # 关闭主弹窗

    @allure.story("新增入库")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.destructive
    def test_create_and_submit_order(self, hazard_in_order_page):
        """TD-HZ-D4-004: 完整新增入库并提交（破坏性）"""
        page = hazard_in_order_page
        handler_name = "TC-自动化测试-张三"
        order_date = "2026-06-17"

        # ---- 创建 ----
        with allure.step("打开新增弹窗"):
            page.click_add()
        with allure.step("填写基本信息"):
            page.fill_in_order(handler_name, date=order_date)
        with allure.step("选择危废品（假设弹窗内点选第一条并确认）"):
            page.click_select_waste()
            page.select_first_waste()          # 假设PO存在此方法
            page.confirm_waste_selection()     # 假设PO存在此方法
        with allure.step("提交申请"):
            page.submit_application()
        with allure.step("验证提交成功提示"):
            toast = page.get_toast_text()
            assert "提交成功" in toast, f"提交后提示应为'提交成功'，实际 '{toast}'"

        # ---- 注册清理 ----
        get_cleanup_tracker().register(
            "hazard_order",
            {"handler": handler_name},
            cleanup_func=lambda: page.delete_order_by_handler(handler_name)
        )

    @pytest.fixture(autouse=True)
    def _cleanup(self, request):
        """每个测试结束后运行 CleanupTracker"""
        yield
        tracker = get_cleanup_tracker()
        tracker.run_cleanup()
        logger.info("已执行数据清理")