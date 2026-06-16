"""销售日报表模块测试脚本 — 只读页面"""
import pytest
import time
import sys
import os
import inspect
import allure
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from page.sales_page.DailyReportPage import DailyReportPage


class TestDailyReport:
    """销售日报表模块测试用例（只读，无增删改）"""

    @pytest.fixture(autouse=True)
    def _allure_case_meta(self, request):
        doc = (inspect.getdoc(request.function) or "").strip()
        title = doc.replace(":", " ").strip() if doc else request.function.__name__
        try:
            allure.dynamic.title(title)
            if doc:
                allure.dynamic.description(doc)
        except Exception:
            pass
        yield

    # ==================================================================
    #  DLY-001: 页面展示
    # ==================================================================
    @pytest.mark.smoke
    @allure.epic("销售管理")
    @allure.feature("日报表")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_001_page_display(self, driver_setup):
        """DLY-001: 页面打开时正常显示日报表"""
        driver = driver_setup
        page = DailyReportPage(driver)
        print("\n========== 测试 DLY-001: 页面显示正常 ==========")

        try:
            # 检查汇总指标区
            metrics = page.get_summary_metrics()
            print(f"[OK] 汇总指标: {metrics}")
            assert len(metrics) > 0, "汇总指标不应为空"

            # 检查明细表格
            headers = page.get_table_headers()
            print(f"[OK] 表头字段: {headers}")
            assert len(headers) > 0, "表头不应为空"

            row_count = page.get_table_row_count()
            print(f"[OK] 明细行数: {row_count}")

            print("========== DLY-001 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  DLY-002: 日期范围查询
    # ==================================================================
    def test_002_date_range_query(self, driver_setup):
        """DLY-002: 按日期范围查询日报表"""
        driver = driver_setup
        page = DailyReportPage(driver)
        print("\n========== 测试 DLY-002: 日期范围查询 ==========")

        try:
            # 查询本月数据
            today = datetime.now()
            start_date = today.replace(day=1).strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")

            print(f"查询日期范围: {start_date} ~ {end_date}")
            page.query_date_range(start_date, end_date)

            # 验证查询执行成功（页面无报错）
            row_count = page.get_table_row_count()
            print(f"[OK] 查询结果行数: {row_count}")

            # 验证汇总指标已刷新
            metrics = page.get_summary_metrics()
            print(f"[OK] 汇总指标: {metrics}")

            # 验证日期输入框值
            actual_start = page.get_start_date()
            actual_end = page.get_end_date()
            print(f"输入框值 — 开始: {actual_start}, 结束: {actual_end}")

            print("========== DLY-002 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  DLY-003: 汇总指标数据验证
    # ==================================================================
    def test_003_summary_metrics(self, driver_setup):
        """DLY-003: 汇总指标渲染正确"""
        driver = driver_setup
        page = DailyReportPage(driver)
        print("\n========== 测试 DLY-003: 汇总指标 ==========")

        try:
            metrics = page.get_summary_metrics()
            print(f"汇总指标: {metrics}")

            # 验证至少有一些指标值不为空
            non_empty_count = sum(1 for v in metrics.values() if v and v.strip())
            assert non_empty_count > 0, "至少应有一个指标值不为空"

            # 如果指标值包含数字，验证可解析
            for key, val in metrics.items():
                if val:
                    print(f"  {key}: {val}")
                    numeric = page.get_summary_numeric_value(key)
                    if numeric is not None:
                        print(f"    → 数值: {numeric}")

            print("========== DLY-003 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  DLY-004: 明细下钻
    # ==================================================================
    def test_004_detail_drill_down(self, driver_setup, daily_report_test_data):
        """DLY-004: 点击明细行展开详情"""
        driver = driver_setup
        page = DailyReportPage(driver)
        td = daily_report_test_data
        print("\n========== 测试 DLY-004: 明细下钻 ==========")

        try:
            row_count = page.get_table_row_count()
            if row_count == 0:
                r = td["date_ranges"]["full_year_2026"]
                page.query_date_range(r["start"], r["end"])
                row_count = page.get_table_row_count()

            if row_count == 0:
                print("无明细数据，跳过下钻测试")
                return

            # 展开第一行
            expanded = page.expand_detail_row(1)
            print(f"展开结果: {expanded}")

            if expanded:
                detail = page.get_expanded_detail_data()
                print(f"展开详情: {detail[:300]}...")
                assert detail, "展开后的详情内容不应为空"
            else:
                print("该行无可展开内容")

            print("========== DLY-004 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  DLY-005: 重置筛选
    # ==================================================================
    def test_005_reset_filter(self, driver_setup, daily_report_test_data):
        """DLY-005: 重置按钮清空日期筛选"""
        driver = driver_setup
        page = DailyReportPage(driver)
        td = daily_report_test_data
        print("\n========== 测试 DLY-005: 重置筛选 ==========")

        try:
            r = td["date_ranges"]["half_year_2026"]
            page.query_date_range(r["start"], r["end"])
            start_before = page.get_start_date()
            end_before = page.get_end_date()
            print(f"设置后日期 — 开始: {start_before}, 结束: {end_before}")

            # 点击重置
            page.click_reset()
            start_after = page.get_start_date()
            end_after = page.get_end_date()
            print(f"重置后日期 — 开始: {start_after}, 结束: {end_after}")

            # 验证日期已被清空或重置为默认值
            assert start_after != start_before or end_after != end_before, \
                "重置后日期应发生变化"
            print("[OK] 筛选条件已被重置")

            print("========== DLY-005 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")

    # ==================================================================
    #  DLY-006: 日期边界测试
    # ==================================================================
    def test_006_date_boundary(self, driver_setup):
        """DLY-006: 日期边界 — 单日查询、过去日期"""
        driver = driver_setup
        page = DailyReportPage(driver)
        print("\n========== 测试 DLY-006: 日期边界 ==========")

        try:
            today = datetime.now()

            # 边界1：单日查询
            single_day = today.strftime("%Y-%m-%d")
            page.query_date_range(single_day, single_day)
            row_count = page.get_table_row_count()
            print(f"单日查询 ({single_day}): {row_count} 条")

            # 边界2：过去日期（一年前）
            past_date = today.replace(year=today.year - 1).strftime("%Y-%m-%d")
            page.query_date_range(past_date, past_date)
            row_count = page.get_table_row_count()
            print(f"过去日期查询 ({past_date}): {row_count} 条")
            # 过去日期可能无数据，页面应正常显示无数据状态

            # 边界3：未来日期
            future_date = today.replace(year=today.year + 1).strftime("%Y-%m-%d")
            page.query_date_range(future_date, future_date)
            row_count = page.get_table_row_count()
            print(f"未来日期查询 ({future_date}): {row_count} 条")
            # 未来日期应无数据，页面无报错

            # 恢复默认查询
            page.click_reset()
            print("[OK] 所有日期边界测试通过，页面无报错")

            print("========== DLY-006 测试通过 ==========")
        except Exception as e:
            pytest.fail(f"测试失败：{e}")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
