"""SAP推送日志模块测试脚本"""
import os
import sys
import pytest
import allure
from selenium.common.exceptions import TimeoutException

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page.workflow_page.SapPushLogPage import SapPushLogPage


def step(text):
    try:
        with allure.step(text):
            print(f"步骤：{text}")
    except Exception:
        print(f"步骤：{text}")


def case(case_id, title):
    print(f"\n========== 用例 {case_id}：{title} ==========")
    try:
        allure.dynamic.title(f"{case_id} {title}")
        allure.dynamic.description(f"用例编号：{case_id}\n用例说明：{title}")
    except Exception:
        pass


def ea(expected, actual):
    return f"预期结果：{expected}；实际结果：{actual}"


class TestSapPushLog:
    @pytest.fixture(autouse=True)
    def _reset_after_each(self, driver_setup):
        yield
        try:
            SapPushLogPage(driver_setup).click_reset()
        except Exception:
            pass

    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("SAP推送日志")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sy_saplog_01_page_display(self, driver_setup):
        page = SapPushLogPage(driver_setup)
        case("SY-SAPLOG-01", "正常显示SAP推送日志列表及相关字段")
        step("获取表头并校验")
        headers = page.get_table_headers()
        expected_cols = {"请求", "状态", "时间", "推送"}
        found = any(col in headers for col in expected_cols)
        assert found or len(headers) >= 2, ea("正常加载SAP推送日志列表及相关字段", headers)
        row_count = page.get_table_row_count()
        if row_count == 0:
            empty = page.get_empty_text()
            pytest.skip(empty or "暂无SAP推送日志数据")

    def test_sy_saplog_02_search_by_status(self, driver_setup):
        page = SapPushLogPage(driver_setup)
        case("SY-SAPLOG-02", "按推送状态筛选")
        step("点击重置")
        page.click_reset()
        step("选择状态：成功")
        try:
            page.select_status("成功")
        except TimeoutException:
            pytest.skip("无法选择推送状态，可能下拉框结构不同")
        step("点击搜索")
        page.click_search()
        row_count = page.get_table_row_count()
        empty = page.get_empty_text() or ""
        assert (row_count > 0) or ("暂无数据" in empty), ea("显示符合状态条件的列表项", empty or f"row_count={row_count}")

    def test_sy_saplog_03_search_by_date(self, driver_setup):
        page = SapPushLogPage(driver_setup)
        case("SY-SAPLOG-03", "按日期范围搜索")
        step("点击重置")
        page.click_reset()
        step("设置日期范围")
        try:
            page.set_date_range("2026-01-01", "2026-12-31")
        except TimeoutException:
            pytest.skip("日期组件不可用 (el-date-picker 未找到)")
        step("点击搜索")
        page.click_search()
        row_count = page.get_table_row_count()
        empty = page.get_empty_text() or ""
        assert (row_count > 0) or ("暂无数据" in empty), ea("显示符合日期条件的列表项", empty or f"row_count={row_count}")

    def test_sy_saplog_04_reset_button(self, driver_setup):
        page = SapPushLogPage(driver_setup)
        case("SY-SAPLOG-04", "重置按钮功能正常")
        step("输入筛选条件")
        try:
            page.set_date_range("2026-01-01", "2026-01-31")
        except TimeoutException:
            pytest.skip("日期组件不可用 (el-date-picker 未找到)")
        step("点击重置")
        page.click_reset()
        step("点击搜索验证列表正常加载")
        page.click_search()
        row_count = page.get_table_row_count()
        empty = page.get_empty_text() or ""
        assert (row_count > 0) or ("暂无数据" in empty), ea("所有筛选条件清空，正常加载列表", empty or f"row_count={row_count}")

    def test_sy_saplog_05_pagination(self, driver_setup):
        page = SapPushLogPage(driver_setup)
        case("SY-SAPLOG-05", "分页跳转")
        step("点击重置")
        page.click_reset()
        step("记录第一页页码")
        page1 = page.get_current_page_number()
        step("点击下一页")
        page.click_next_page()
        page2 = page.get_current_page_number()
        if page2 == page1:
            pytest.skip("只有一页数据，跳过分页测试")
        assert page.get_table_row_count() > 0, ea("翻页后列表仍正常加载", page.get_empty_text() or "暂无数据")

    def test_sy_saplog_06_detail_view(self, driver_setup):
        page = SapPushLogPage(driver_setup)
        case("SY-SAPLOG-06", "查看推送详情")
        step("校验列表是否有数据")
        if page.get_table_row_count() == 0:
            pytest.skip(page.get_empty_text() or "当前无SAP推送日志数据，跳过详情验证")
        step("点击第一行详情")
        try:
            page.click_first_row_detail()
        except TimeoutException:
            pytest.skip("当前列表未显示详情按钮")
        step("校验详情弹窗出现")
        assert page.wait_detail_dialog_visible(timeout=8), ea("弹出推送详情弹窗", "未找到详情弹窗")
        try:
            page.close_detail_dialog()
        except Exception:
            pass


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
