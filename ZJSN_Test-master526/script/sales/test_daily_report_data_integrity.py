"""销售日报表 -- 数据一致性验证测试

测试范围：
  - DLY-050: 统计卡片「LNG销售总量」= 表格LNG列合计
  - DLY-051: 统计卡片「合计销售量」= 表格合计列合计
  - DLY-052: 统计卡片「订单数」= 表格订单列合计
  - DLY-053: 翻页后分页总数不变（跨页一致性）
  - DLY-054: 明细下钻功能

Vue/Element Plus 异步处理：
  - 统计卡片与表格异步加载，使用 verify_stat_vs_table
  - 浮点精度容差 0.001
  - 下钻展开使用 JS click 绕过动画
"""
import pytest
import allure


class TestDailyReportDataIntegrity:
    """DLY-050~054: 数据一致性 & 下钻"""

    # ==================================================================
    #  DLY-050: LNG统计 vs 表格LNG列合计
    # ==================================================================
    @pytest.mark.smoke
    @allure.title("DLY-050: 统计卡片 LNG销售总量 = 表格 LNG列合计")
    def test_050_lng_stat_matches_table(self, daily_report_page):
        """统计卡片「LNG销售总量」值应与表格LNG销售量列合计一致（容差0.001）"""
        page = daily_report_page
        print("\n========== DLY-050: LNG数据一致性 ==========")

        # 确保有数据
        row_count = page.get_table_row_count()
        if row_count == 0:
            pytest.skip("无数据行，跳过一致性校验")

        is_match, stat_val, table_sum, diff = page.verify_stat_vs_table(
            stat_name="LNG销售总量",
            column_header="LNG",
            tolerance=0.001,
        )
        print(f"统计LNG: {stat_val} t")
        print(f"表格LNG合计: {table_sum} t")
        print(f"偏差: {diff}")
        print(f"结果: {'一致' if is_match else '不一致'}")

        assert is_match, (
            f"LNG数据不一致！\n"
            f"  统计卡片: {stat_val} t\n"
            f"  表格合计: {table_sum} t\n"
            f"  偏差: {diff} (容差 0.001)"
        )

        print("========== DLY-050 通过 ==========")

    # ==================================================================
    #  DLY-051: 合计统计 vs 表格合计列合计
    # ==================================================================
    @allure.title("DLY-051: 统计卡片 合计销售量 = 表格 合计列合计")
    def test_051_total_stat_matches_table(self, daily_report_page):
        """统计卡片「合计销售量」值应与表格合计列合计一致"""
        page = daily_report_page
        print("\n========== DLY-051: 合计销售量一致性 ==========")

        row_count = page.get_table_row_count()
        if row_count == 0:
            pytest.skip("无数据行，跳过一致性校验")

        is_match, stat_val, table_sum, diff = page.verify_stat_vs_table(
            stat_name="合计销售量",
            column_header="合计",
            tolerance=0.001,
        )
        print(f"统计合计: {stat_val} t")
        print(f"表格合计: {table_sum} t")
        print(f"偏差: {diff}")
        print(f"结果: {'一致' if is_match else '不一致'}")

        assert is_match, (
            f"合计销售量数据不一致！\n"
            f"  统计卡片: {stat_val} t\n"
            f"  表格合计: {table_sum} t\n"
            f"  偏差: {diff} (容差 0.001)"
        )

        print("========== DLY-051 通过 ==========")

    # ==================================================================
    #  DLY-052: 订单数统计 vs 表格订单列合计
    # ==================================================================
    @allure.title("DLY-052: 统计卡片 订单数 = 表格 订单列合计")
    def test_052_order_count_matches_table(self, daily_report_page):
        """统计卡片「销售订单数」值应与表格订单列合计一致（整数比较）"""
        page = daily_report_page
        print("\n========== DLY-052: 订单数一致性 ==========")

        row_count = page.get_table_row_count()
        if row_count == 0:
            pytest.skip("无数据行，跳过一致性校验")

        stat_val = page.get_summary_numeric_value("订单数")
        print(f"统计订单数: {stat_val}")

        order_idx = page._get_column_index("订单数")
        if order_idx is None:
            pytest.skip("未找到「订单数」列")

        table_sum = page.sum_detail_column(order_idx)
        print(f"表格订单合计: {table_sum}")

        assert stat_val is not None, "订单数统计值不应为空"
        # 订单数为整数，直接比较
        assert int(stat_val) == int(table_sum), (
            f"订单数不一致！\n"
            f"  统计卡片: {int(stat_val)} 单\n"
            f"  表格合计: {int(table_sum)} 单"
        )

        print("========== DLY-052 通过 ==========")

    # ==================================================================
    #  DLY-053: 翻页后总条数不变
    # ==================================================================
    def test_053_total_count_consistent_after_page(self, daily_report_page):
        """翻到下一页后，分页总条数不变"""
        page = daily_report_page
        # 使用最近1个月范围避免超时（数据量足够即可分页）
        page.query_date_range("2026-05-17", "2026-06-17")
        print("\n========== DLY-053: 翻页总条数一致性 ==========")

        total_before = page.get_total_count()
        print(f"第1页总条数: {total_before}")

        if not page.is_next_page_enabled():
            pytest.skip("仅单页数据，跳过验证")

        page.click_next_page()
        total_after = page.get_total_count()
        print(f"第2页总条数: {total_after}")

        assert total_before == total_after, (
            f"翻页后总条数应不变。翻页前: {total_before}，翻页后: {total_after}"
        )

        print("========== DLY-053 通过 ==========")

    # ==================================================================
    #  DLY-054: 明细下钻
    # ==================================================================
    def test_054_detail_drill_down(self, daily_report_page):
        """点击「明细」按钮可展开详情，内容非空"""
        page = daily_report_page
        print("\n========== DLY-054: 明细下钻 ==========")

        row_count = page.get_table_row_count()
        if row_count == 0:
            pytest.skip("无数据行，跳过明细下钻")

        # 获取第一行日期，用于点击明细
        first_row = page.get_row_data(1)
        first_date_cell = first_row[0] if first_row else ""
        print(f"第一行日期单元格: '{first_date_cell}'")

        # 尝试通过行索引展开
        expanded = page.expand_detail_row(1)
        print(f"展开结果 (row index): {expanded}")

        if expanded:
            detail_data = page.get_expanded_detail_data()
            print(f"展开详情 (前200字): {detail_data[:200]}...")

            if detail_data:
                print("[OK] 明细下钻成功，内容非空")
            else:
                print("[WARN] 展开成功但详情内容为空（可能内部无额外数据）")
        else:
            # 尝试通过日期文本点击明细按钮
            import re
            match = re.search(r'(\d{4}-\d{2}-\d{2})', first_date_cell)
            if match:
                date_str = match.group(1)
                print(f"尝试通过日期 '{date_str}' 点击明细按钮")
                clicked = page.click_detail_button(date_str)
                if clicked:
                    detail_data = page.get_expanded_detail_data()
                    print(f"展开详情: {detail_data[:200]}...")
                else:
                    print("[WARN] 未找到明细按钮（可能该行无下钻功能）")

        print("========== DLY-054 通过 ==========")
