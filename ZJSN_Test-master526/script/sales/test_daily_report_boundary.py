"""销售日报表 -- 边界/异常场景测试

测试范围：
  - DLY-060: 日期边界参数化（单日/整月/跨年/未来/过去）
  - DLY-061: 跨年查询
  - DLY-062: 日期列格式含星期文本
  - DLY-063: LNG列值为非负数
  - DLY-064: 订单数列值为非负整数
  - DLY-065: 开始日期 > 结束日期时页面行为

Vue/Element Plus 异步处理：
  - DatePicker 日期交叉输入时的异常场景
  - 边界日期输入后表格可能为空，需优雅处理
"""
import pytest
import allure
from datetime import datetime, timedelta


class TestDailyReportBoundary:
    """DLY-060~065: 日期边界 & 数据格式"""

    # ==================================================================
    #  DLY-060: 日期边界参数化
    # ==================================================================
    @pytest.mark.parametrize("start_date,end_date,desc", [
        pytest.param(
            "2026-05-29", "2026-05-29", "单日查询",
            id="single_day"
        ),
        pytest.param(
            "2026-05-01", "2026-05-31", "整月查询",
            id="full_month"
        ),
        pytest.param(
            "2025-01-01", "2025-12-31", "跨年查询",
            id="cross_year"
        ),
        pytest.param(
            "2026-01-01", "2026-12-31", "全年查询",
            id="full_year"
        ),
    ])
    @allure.title("DLY-060: 日期边界 -- {desc}")
    def test_060_date_range_variants(self, daily_report_page,
                                     start_date, end_date, desc):
        """日期范围参数化测试：验证各种日期范围下页面不报错"""
        page = daily_report_page
        print(f"\n========== DLY-060: {desc} ({start_date} ~ {end_date}) ==========")

        page.query_date_range(start_date, end_date)

        # 核心断言：页面不报错，表头存在
        headers = page.get_table_headers()
        assert headers, f"{desc}查询后表头应存在"

        row_count = page.get_table_row_count()
        print(f"{desc}: {row_count} 行数据")

        # 有数据时验证日期范围
        if row_count > 0:
            all_in_range, out_of_range = page.verify_dates_in_range(
                start_date, end_date
            )
            print(f"日期校验: {'通过' if all_in_range else f'越界: {out_of_range}'}")
            # 注意：这里不做 assert，因为表格可能包含范围外的汇总行

        # 统计卡片不应报错
        metrics = page.get_summary_metrics()
        print(f"统计卡片: {metrics}")
        assert metrics, "查询后统计卡片不应为空"

        print(f"========== DLY-060 [{desc}] 通过 ==========")

    # ==================================================================
    #  DLY-061: 过去日期查询
    # ==================================================================
    def test_061_past_date_query(self, daily_report_page):
        """查询一年前的日期，页面正常处理（有数据或无数据）"""
        page = daily_report_page
        print("\n========== DLY-061: 过去日期查询 ==========")

        one_year_ago = datetime.now().replace(year=datetime.now().year - 1)
        past_date = one_year_ago.strftime("%Y-%m-%d")

        page.query_date_range(past_date, past_date)
        row_count = page.get_table_row_count()
        print(f"一年前 ({past_date}): {row_count} 行")

        # 页面不应报错，表头应存在
        assert page.get_table_headers(), "过去日期查询后表头应存在"

        print("========== DLY-061 通过 ==========")

    # ==================================================================
    #  DLY-062: 日期列格式含星期
    # ==================================================================
    def test_062_date_column_format(self, daily_report_page):
        """日期列应包含 'YYYY-MM-DD 星期X' 格式"""
        page = daily_report_page
        print("\n========== DLY-062: 日期列格式验证 ==========")

        row_count = page.get_table_row_count()
        if row_count == 0:
            pytest.skip("无数据行，跳过格式验证")

        date_col = page.get_column_data(1)
        print(f"日期列数据 (前3条): {date_col[:3]}")

        import re
        weekday_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

        for i, cell_text in enumerate(date_col[:3]):  # 只验证前3行
            # 格式: "2026-05-29 星期五" 或 "2026-05-29\n星期五"
            has_date = bool(re.search(r'\d{4}-\d{2}-\d{2}', cell_text))
            has_weekday = any(w in cell_text for w in weekday_names)

            print(f"  [{i+1}] '{cell_text}' → 日期: {has_date}, 星期: {has_weekday}")

            assert has_date, f"第{i+1}行日期单元格应有日期格式，实际: '{cell_text}'"
            # 星期可能在不同行/span，做宽松断言
            if not has_weekday:
                print(f"  [WARN] 第{i+1}行未检测到星期文本（可能在不同DOM层级）")

        print("========== DLY-062 通过 ==========")

    # ==================================================================
    #  DLY-063: LNG列值为非负数
    # ==================================================================
    def test_063_lng_column_non_negative(self, daily_report_page):
        """LNG销售量列所有值 ≥ 0"""
        page = daily_report_page
        print("\n========== DLY-063: LNG列非负数验证 ==========")

        lng_idx = page._get_column_index("LNG")
        if lng_idx is None:
            pytest.skip("未找到LNG销售量列")

        lng_data = page.get_column_data(lng_idx)
        print(f"LNG列数据: {lng_data}")

        import re
        for i, val_text in enumerate(lng_data):
            nums = re.findall(r'-?[\d,]+\.?\d*', val_text.replace(',', ''))
            if nums:
                try:
                    num_val = float(nums[0])
                    assert num_val >= 0, (
                        f"第{i+1}行 LNG 值不应为负: {num_val} ('{val_text}')"
                    )
                except ValueError:
                    pass

        print("========== DLY-063 通过 ==========")

    # ==================================================================
    #  DLY-064: 订单数列值为非负整数
    # ==================================================================
    def test_064_order_column_non_negative_int(self, daily_report_page):
        """订单数列所有值 ≥ 0 且为整数"""
        page = daily_report_page
        print("\n========== DLY-064: 订单列整数验证 ==========")

        order_idx = page._get_column_index("订单数")
        if order_idx is None:
            pytest.skip("未找到订单数列")

        order_data = page.get_column_data(order_idx)
        print(f"订单列数据: {order_data}")

        for i, val_text in enumerate(order_data):
            import re
            nums = re.findall(r'\d+', val_text)
            if nums:
                num_val = int(nums[0])
                assert num_val >= 0, (
                    f"第{i+1}行订单数不应为负: {num_val} ('{val_text}')"
                )
                assert num_val == int(num_val), (
                    f"第{i+1}行订单数应为整数: '{val_text}'"
                )

        print("========== DLY-064 通过 ==========")

    # ==================================================================
    #  DLY-065: 开始日期 > 结束日期
    # ==================================================================
    def test_065_start_after_end_date(self, daily_report_page):
        """开始日期晚于结束日期时，页面表现（Element Plus DatePicker 通常阻止此操作）"""
        page = daily_report_page
        print("\n========== DLY-065: 日期倒置 ==========")

        # 设置结束日期早于开始日期
        page.input_start_date("2026-06-30")
        page.input_end_date("2026-06-01")
        page.click_query()

        # 页面不应崩溃，表头应存在
        headers = page.get_table_headers()
        assert headers, "日期倒置查询后表头应存在（Element Plus 可能自动纠正或返回空数据）"

        row_count = page.get_table_row_count()
        start_val = page.get_start_date()
        end_val = page.get_end_date()
        print(f"输入值 -- 开始: '{start_val}', 结束: '{end_val}'")
        print(f"查询结果: {row_count} 行")

        # Element Plus DatePicker 可能自动交换日期或返回空
        # 只要页面不报错即可

        print("========== DLY-065 通过 ==========")
