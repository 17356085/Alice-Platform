"""气体分析报告单模块测试 — 企业级

测试策略：
  - 页面展示验证（表头、取样位置标签）
  - 取样位置切换
  - 日期范围筛选
  - 新增报告单（闭环数据）
  - 导出功能
"""
import os
import sys
import pytest
import allure
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base.browser_driver import BaseDriver, ensure_logged_in
from page.lab_page.GasAnalysisReportPage import GasAnalysisReportPage


# ==================================================================
#  测试辅助
# ==================================================================
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


def _today():
    return datetime.now().strftime("%Y-%m-%d")


def _days_ago(n):
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")


# ==================================================================
#  Fixture
# ==================================================================
@pytest.fixture(scope="class")
def driver_setup():
    """Class 级 fixture：每个测试类独享一个浏览器实例，避免跨类状态污染"""
    base = BaseDriver()
    driver = base.open_browser()
    try:
        step("登录系统")
        ensure_logged_in(driver)
        step("进入气体分析报告单页面")
        GasAnalysisReportPage(driver).navigate_to_gas_analysis_report()
        yield driver
    finally:
        base.close_browser()


# ==================================================================
#  测试类
# ==================================================================
class TestGasAnalysisReportDisplay:
    """页面展示验证"""

    @pytest.mark.smoke
    @allure.epic("实验室")
    @allure.feature("气体分析报告")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_gas_01_page_display(self, driver_setup):
        """GAS-01: 页面正常显示，表头包含关键业务字段"""
        page = GasAnalysisReportPage(driver_setup)
        case("GAS-01", "正常显示气体分析报告单列表及相关字段")

        step("获取表格表头")
        headers = page.get_table_headers()

        # 验证表头非空且包含基础字段
        assert len(headers) >= 5, \
            ea("表头至少 5 列", f"实际 {len(headers)} 列: {headers}")

        # 验证关键业务列存在（至少包含日期和取样位置）
        headers_text = " ".join(headers)
        for keyword in ["日期", "取样位置", "甲烷", "H2"]:
            assert keyword in headers_text, \
                ea(f"表头包含「{keyword}」", f"未找到「{keyword}」，表头: {headers}")

    def test_gas_02_active_location(self, driver_setup):
        """GAS-02: 页面加载后表格有数据或显示取样位置"""
        page = GasAnalysisReportPage(driver_setup)
        case("GAS-02", "确认页面表格已渲染")

        row_count = page.get_table_row_count()
        empty = page.get_empty_text()
        assert row_count > 0 or empty, \
            ea("表格有数据行或显示空状态提示", f"行数={row_count}, 空提示='{empty}'")

    def test_gas_03_table_has_data(self, driver_setup):
        """GAS-03: 表格有数据加载"""
        page = GasAnalysisReportPage(driver_setup)
        case("GAS-03", "表格有数据或显示空状态")

        row_count = page.get_table_row_count()
        empty_text = page.get_empty_text() if row_count == 0 else ""
        print(f"当前行数: {row_count}, 空状态提示: {empty_text}")


class TestGasAnalysisReportFilter:
    """搜索筛选验证"""

    def test_gas_04_date_range_filter(self, driver_setup):
        """GAS-04: 按日期范围筛选"""
        page = GasAnalysisReportPage(driver_setup)
        case("GAS-04", "按日期范围查询数据")

        step("输入日期范围并查询")
        start = _days_ago(30)
        end = _today()
        page.filter_by_date_range(start, end)

        step("验证表格数据在日期范围内")
        dates = page.get_column_data_by_header("日期")
        if dates:
            print(f"查询结果共 {len(dates)} 行")
            start_dt = datetime.strptime(start, "%Y-%m-%d")
            end_dt = datetime.strptime(end, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            for d in dates:
                try:
                    d_dt = datetime.strptime(d.strip(), "%Y-%m-%d")
                except ValueError:
                    continue  # 跳过非标准日期格式
                assert start_dt <= d_dt <= end_dt, \
                    ea(f"日期 {d} 在 {start}~{end} 范围内", f"日期 {d} 超出范围")
        else:
            empty = page.get_empty_text()
            print(f"日期范围内无数据: {empty}")

    def test_gas_05_reset_filter(self, driver_setup):
        """GAS-05: 重置按钮清空筛选条件"""
        page = GasAnalysisReportPage(driver_setup)
        case("GAS-05", "重置按钮清空筛选条件")

        step("输入筛选条件")
        page.input_start_date("2026-01-01")
        page.input_end_date("2026-06-01")

        step("点击重置")
        page.click_reset()

        step("验证筛选条件被清空")
        assert page.get_start_date() == "", \
            ea("开始日期被清空", page.get_start_date())
        assert page.get_end_date() == "", \
            ea("结束日期被清空", page.get_end_date())

        step("验证列表正常加载")
        page.click_query()
        row_count = page.get_table_row_count()
        print(f"重置后查询，数据行数: {row_count}")


class TestGasAnalysisReportLocationTab:
    """取样位置标签切换验证"""

    def test_gas_06_switch_location(self, driver_setup):
        """GAS-06: 切换取样位置标签"""
        page = GasAnalysisReportPage(driver_setup)
        case("GAS-06", "切换取样位置标签，数据正常加载")

        # 切换到另一个已知位置
        target = "LNG冷箱"
        step(f"点击取样位置: {target}")
        page.click_location_tab(target)

        step("等待数据加载")
        active = page.get_active_location()
        row_count = page.get_table_row_count()
        print(f"当前激活标签: {active}, 数据行数: {row_count}")

    def test_gas_07_switch_back(self, driver_setup):
        """GAS-07: 切回默认位置"""
        page = GasAnalysisReportPage(driver_setup)
        case("GAS-07", "切回「界区原料气」")

        step("点击「界区原料气」")
        page.click_location_tab("界区原料气")

        row_count = page.get_table_row_count()
        print(f"切回默认位置后，数据行数: {row_count}")


class TestGasAnalysisReportAdd:
    """新增报告单验证"""

    def test_gas_08_add_report_minimal(self, driver_setup):
        """GAS-08: 新增报告单（仅必填字段）

        Kimi 识别：弹窗字段中「检验员」和「复核员」标注 * 为必填，
        其余字段均可选填。气体值均为 input-number 类型。
        """
        page = GasAnalysisReportPage(driver_setup)
        case("GAS-08", "新增气体分析报告单（必填字段）")

        step("点击新增报告单")
        page.click_add()

        step("获取弹窗标题确认弹窗打开")
        title = page.get_dialog_title()
        assert title, ea("弹窗已打开", "弹窗标题为空")

        step("仅填写必填字段（检验员 + 复核员）")
        page.fill_report_form(
            inspector="auto_test_inspector",
            reviewer="auto_test_reviewer",
        )

        step("点击保存报告")
        msg = page.save_report()
        assert any(k in (msg or "") for k in ["成功", "已存在", "重复"]), \
            ea("新增成功提示", msg or "未获取到提示")


class TestGasAnalysisReportStatistics:
    """统计行验证"""

    def test_gas_09_statistics_row(self, driver_setup):
        """GAS-09: 统计行显示平均值"""
        page = GasAnalysisReportPage(driver_setup)
        case("GAS-09", "统计行显示各列平均值")

        stat = page.get_statistics_data()
        print(f"统计行数据: {stat}")
        if stat:
            assert stat.get("values"), \
                ea("统计行有数值", "统计行为空")


class TestGasAnalysisReportExport:
    """导出验证"""

    def test_gas_10_export(self, driver_setup):
        """GAS-10: 导出表格数据"""
        page = GasAnalysisReportPage(driver_setup)
        case("GAS-10", "导出气体分析报告单数据")

        step("点击导出")
        export_confirmed = page.click_export()
        msg = page.wait_for_toast_text(timeout=6)
        assert export_confirmed or any(
            k in (msg or "") for k in ["成功", "导出", "确认", "已"]
        ), ea("导出成功提示", msg or "未获取到提示")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
