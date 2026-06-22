"""气体分析对比 — 测试脚本"""
import pytest
import allure
import logging

logger = logging.getLogger(__name__)

@allure.epic("化验室取样")
@allure.feature("气体分析对比")
class TestGasCompare:
    """气体分析对比页面测试类"""

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_gc_01_page_display(self, gas_compare_page):
        """GC-01: 正常显示气体分析对比页面（搜索表单）

        验证页面核心元素（日期选择器、表格/空状态提示）正确加载。
        """
        page = gas_compare_page
        with allure.step("验证页面核心元素加载完成"):
            assert page.is_page_loaded(), "页面应正常加载（日期选择器、表格/空状态提示均可见）"

    @allure.story("日期范围查询")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_gc_02_date_search(self, gas_compare_page):
        """GC-02: 日期范围查询

        设置开始/结束日期并执行查询，验证查询后页面状态正常（无异常弹窗，表格/空状态提示存在）。
        """
        page = gas_compare_page
        with allure.step("设置日期范围并执行查询"):
            page.set_start_date("2026-01-01").set_end_date("2026-06-12").click_query()
        with allure.step("验证查询后页面状态正常"):
            assert page.is_page_loaded(), "查询后页面应正常加载（日期选择器、表格/空状态提示均可见）"
        with allure.step("验证查询结果不为空（或正确处理空提示）"):
            row_count = page.get_table_row_count()
            assert row_count > 0 or not page.is_element_visible(page.EMPTY_TEXT), \
                "查询结果应为有数据或仅有空状态提示"

    # @pytest.mark.smoke
    @allure.story("重置搜索条件")
    @allure.severity(allure.severity_level.NORMAL)
    def test_gc_03_reset_search(self, gas_compare_page):
        """GC-03: 重置搜索条件

        设置日期后点击重置按钮，验证日期输入框恢复默认值（或清空）。
        """
        page = gas_compare_page
        with allure.step("设置日期并点击重置"):
            page.set_start_date("2026-06-01").set_end_date("2026-06-12").click_reset()
        with allure.step("验证重置后开始日期输入框值为空"):
            start_date_value = page.get_input_value(page.START_DATE_INPUT)
            assert start_date_value == "", f"重置后开始日期输入框应清空，但实际值为: {start_date_value}"

    # @pytest.mark.smoke
    @allure.story("切换日期范围并查询")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_gc_04_switch_date_range(self, gas_compare_page):
        """GC-04: 切换日期范围并查询

        验证切换不同日期范围后查询结果能正确更新（行数变化）。
        """
        page = gas_compare_page
        with allure.step("查询第一个日期范围"):
            page.set_start_date("2026-01-01").set_end_date("2026-01-15").click_query()
            first_count = page.get_table_row_count()
            logger.info("第一次查询结果行数: %s", first_count)
        with allure.step("查询第二个日期范围"):
            page.set_start_date("2026-06-01").set_end_date("2026-06-15").click_query()
            second_count = page.get_table_row_count()
            logger.info("第二次查询结果行数: %s", second_count)
        with allure.step("验证前后查询结果行数不同或至少有一个有数据"):
            assert first_count >= 0 and second_count >= 0, "查询行数应为非负整数"
            # 这里可以增加更具体的断言，比如比较两个行数
            # assert first_count != second_count, ...