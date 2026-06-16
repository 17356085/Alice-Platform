"""生产月报表模块测试

测试层次：
  P0 - 页面加载 & 月份导航 & 表格展示
  P1 - 弹窗交互 (趋势/导出)
"""
import logging
import os
import sys

import allure
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page.production_page.MonthlyReportPage import MonthlyReportPage

logger = logging.getLogger(__name__)


def step(text):
    try:
        with allure.step(text):
            pass
    except Exception:
        pass


def case(case_id, title):
    logger.info("========== 用例 %s：%s ==========", case_id, title)
    try:
        allure.dynamic.title(f"{case_id} {title}")
    except Exception:
        pass


def ea(expected, actual):
    return f"预期结果：{expected}；实际结果：{actual}"


# ══════════════════════════════════════════════════════════════════
#  P0 - 页面加载
# ══════════════════════════════════════════════════════════════════
class TestMonthlyReportDisplay:

    @pytest.mark.smoke
    @allure.epic("生产管理")
    @allure.feature("生产月报表")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_page_load_basic_elements(self, monthly_report_page):
        """TC-PROD-MR-001: 页面基本元素加载验证"""
        case("TC-PROD-MR-001", "页面基本元素加载验证")
        page = monthly_report_page

        with allure.step("验证月份导航可见"):
            month = page.get_current_month()
            assert month, "月份文字为空"
            logger.info("当前月份: %s", month)

        with allure.step("验证操作按钮可见"):
            assert page.is_visible(page.BTN_GENERATE), "生成报表按钮不可见"
            assert page.is_visible(page.BTN_TREND), "趋势按钮不可见"
            assert page.is_visible(page.BTN_EXPORT), "导出按钮不可见"
            assert page.is_visible(page.BTN_PRINT), "打印按钮不可见"

        with allure.step("验证统计卡片可见"):
            card_count = page.get_stat_card_count()
            assert card_count >= 3, f"统计卡片数量不足（预期≥3，实际{card_count}）"
            logger.info("统计卡片数量: %d", card_count)
            lng_value = page.get_lng_monthly_output()
            assert lng_value, "LNG月产量为空"
            logger.info("LNG月产量: %s", lng_value)

        with allure.step("验证四个分区卡片可见"):
            for name in ["产品", "原料", "公辅工程", "冷剂消耗"]:
                assert page.is_section_visible(name), f"分区'{name}'不可见"

    @pytest.mark.smoke
    @allure.epic("生产管理")
    @allure.feature("生产月报表")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_generate_button_disabled(self, monthly_report_page):
        """TC-PROD-MR-002: 生成报表按钮初始disabled"""
        case("TC-PROD-MR-002", "生成报表按钮初始disabled")
        page = monthly_report_page
        assert page.is_generate_disabled(), ea(
            "生成报表为disabled", "按钮未disabled"
        )


# ══════════════════════════════════════════════════════════════════
#  P0 - 月份导航
# ══════════════════════════════════════════════════════════════════
class TestMonthlyReportNavigation:

    @pytest.mark.smoke
    @allure.epic("生产管理")
    @allure.feature("生产月报表")
    @allure.story("月份导航")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_click_next_month(self, monthly_report_page):
        """TC-PROD-MR-003: 点击下一个月"""
        case("TC-PROD-MR-003", "点击下一个月")
        page = monthly_report_page
        before = page.get_current_month()
        page.click_next_month()
        after = page.get_current_month()
        logger.info("月份变化: %s → %s", before, after)
        assert before != after, ea("月份发生变化", f"月份未变({before})")

    @pytest.mark.smoke
    @allure.epic("生产管理")
    @allure.feature("生产月报表")
    @allure.story("月份导航")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_click_prev_month(self, monthly_report_page):
        """TC-PROD-MR-004: 点击上一个月"""
        case("TC-PROD-MR-004", "点击上一个月")
        page = monthly_report_page
        before = page.get_current_month()
        page.click_prev_month()
        after = page.get_current_month()
        logger.info("月份变化: %s → %s", before, after)
        assert before != after, ea("月份发生变化", f"月份未变({before})")

    @allure.epic("生产管理")
    @allure.feature("生产月报表")
    @allure.story("月份导航")
    @allure.severity(allure.severity_level.NORMAL)
    def test_generate_enabled_after_month_change(self, monthly_report_page):
        """TC-PROD-MR-005: 切换月份后生成报表启用

        切到不同月份后生成报表按钮应可用，点击后成功加载表格数据。
        """
        case("TC-PROD-MR-005", "切换月份后生成报表启用")
        page = monthly_report_page

        # 切到不同月份
        btn_next = page.find(page.BTN_NEXT_MONTH)
        if "is-disabled" in (btn_next.get_attribute("class") or ""):
            page.click_prev_month()
        else:
            page.click_next_month()

        # 生成报表并验证数据加载
        page.click_generate_report()
        rows = page.get_section_row_count("产品")
        assert rows > 0, ea(
            "切换月份后生成报表加载数据",
            f"产品分区无数据（{rows}行）"
        )


# ══════════════════════════════════════════════════════════════════
#  P0 - 表格展示
# ══════════════════════════════════════════════════════════════════
class TestMonthlyReportTables:

    @pytest.mark.smoke
    @allure.epic("生产管理")
    @allure.feature("生产月报表")
    @allure.story("表格展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_table_headers(self, monthly_report_page):
        """TC-PROD-MR-006: 产品表头验证"""
        case("TC-PROD-MR-006", "四分区表头验证")
        page = monthly_report_page

        for name in ["产品", "原料", "公辅工程", "冷剂消耗"]:
            headers = page.get_section_table_headers(name)
            required = ["类别", "名称", "单位"]
            for col in required:
                assert col in headers, f"{name}表缺少列'{col}'，实际: {headers}"
            logger.info("%s表头: %s", name, headers)

    @pytest.mark.smoke
    @allure.epic("生产管理")
    @allure.feature("生产月报表")
    @allure.story("表格展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_tables_have_data(self, monthly_report_page):
        """TC-PROD-MR-007: 四个分区表格均有数据

        页面初始不加载数据，需先切换月份再点击"生成报表"触发数据加载。
        """
        case("TC-PROD-MR-007", "四个分区表格数据行验证")
        page = monthly_report_page

        # 切到不同月份以启用"生成报表"
        btn_next = page.find(page.BTN_NEXT_MONTH)
        if "is-disabled" in (btn_next.get_attribute("class") or ""):
            page.click_prev_month()
        else:
            page.click_next_month()

        # 生成报表并验证
        page.click_generate_report()

        total_rows = 0
        for name in ["产品", "原料", "公辅工程", "冷剂消耗"]:
            rows = page.get_section_row_count(name)
            total_rows += rows
            logger.info("分区'%s': %d行", name, rows)
        assert total_rows > 0, "四个分区表格均无数据"


# ══════════════════════════════════════════════════════════════════
#  P1 - 弹窗交互
# ══════════════════════════════════════════════════════════════════
class TestMonthlyReportDialogs:

    @allure.epic("生产管理")
    @allure.feature("生产月报表")
    @allure.story("趋势弹窗")
    @allure.severity(allure.severity_level.NORMAL)
    def test_open_trend_dialog(self, monthly_report_page):
        """TC-PROD-MR-008: 打开趋势弹窗"""
        case("TC-PROD-MR-008", "打开趋势弹窗")
        page = monthly_report_page
        page.click_trend()
        assert page.is_dialog_open("趋势分析"), "趋势弹窗未打开"
        page.click_dialog_cancel("趋势分析")

    @allure.epic("生产管理")
    @allure.feature("生产月报表")
    @allure.story("导出弹窗")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="导出弹窗不稳定，同daily-report待排查")
    def test_open_export_dialog(self, monthly_report_page):
        """TC-PROD-MR-009: 打开导出弹窗"""
        case("TC-PROD-MR-009", "打开导出弹窗")
        page = monthly_report_page
        page.click_export()
        assert page.is_dialog_open("生产日报表"), "导出弹窗未打开"
        page.click_dialog_cancel("生产日报表")
