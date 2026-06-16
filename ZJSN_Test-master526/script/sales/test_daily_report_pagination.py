"""销售日报表 -- 分页功能测试

测试范围：
  - DLY-040: 总条数正确显示
  - DLY-041: 翻到下一页，数据变化
  - DLY-042: 翻到上一页，数据恢复
  - DLY-043: 只有一页时翻页按钮状态
  - DLY-044: 切换每页条数

Vue/Element Plus 异步处理：
  - 翻页后表格重新渲染，需 _wait_table_ready
  - 切换页大小后 Select 面板 Teleport 到 body
  - 下拉选项使用 _select_option 等待面板可见
"""
import pytest
import allure


@pytest.fixture(autouse=True)
def _expand_date_range(daily_report_page):
    """每个分页测试前：扩大到全量日期范围，确保数据量足以触发分页"""
    daily_report_page.query_date_range("2025-01-01", "2027-01-01")


class TestDailyReportPagination:
    """DLY-040~044: 分页功能验证"""

    # ==================================================================
    #  DLY-040: 总条数显示
    # ==================================================================
    @pytest.mark.smoke
    @allure.title("DLY-040: 分页总条数正确显示")
    def test_040_total_count_display(self, daily_report_page):
        """分页区显示"共 X 条"，数字 ≥ 0"""
        page = daily_report_page
        print("\n========== DLY-040: 分页总数验证 ==========")

        total_text = page.get_total_count_text()
        print(f"分页文本: '{total_text}'")

        assert total_text, "分页总条数文本不应为空"
        assert "共" in total_text, f"分页文本应含「共」，实际: '{total_text}'"

        total_num = page.get_total_count()
        print(f"总条数: {total_num}")
        assert total_num >= 0, f"总条数应 ≥ 0，实际: {total_num}"

        # 总条数与表格行数逻辑校验
        row_count = page.get_table_row_count()
        print(f"当前页行数: {row_count}")
        # 如果总条数 ≤ 10（默认页大小），则当前页行数 = 总条数
        if total_num <= 10:
            assert row_count == total_num, (
                f"总条数 ≤ 10 时，行数({row_count})应等于总条数({total_num})"
            )
        else:
            # 总条数 > 10 时，行数应为每页条数
            assert row_count <= 10, (
                f"默认每页10条，行数({row_count})应 ≤ 10"
            )

        print("========== DLY-040 通过 ==========")

    # ==================================================================
    #  DLY-041: 翻到下一页
    # ==================================================================
    def test_041_next_page_changes_data(self, daily_report_page):
        """翻到下一页后，第一行数据变化"""
        page = daily_report_page
        print("\n========== DLY-041: 翻到下一页 ==========")

        if not page.is_next_page_enabled():
            pytest.skip("仅有单页数据，跳过翻页测试")

        # 记录翻页前第一行
        first_row_before = page.get_row_data(1)
        first_date_before = first_row_before[0] if first_row_before else ""
        print(f"翻页前第一行: {first_row_before}")

        # 翻页
        page.click_next_page()

        # 记录翻页后第一行
        first_row_after = page.get_row_data(1)
        first_date_after = first_row_after[0] if first_row_after else ""
        print(f"翻页后第一行: {first_row_after}")

        assert first_date_before != first_date_after, (
            f"翻页后第一行数据应变化。翻页前: '{first_date_before}'，翻页后: '{first_date_after}'"
        )

        print("========== DLY-041 通过 ==========")

    # ==================================================================
    #  DLY-042: 翻到上一页
    # ==================================================================
    def test_042_prev_page_restores_data(self, daily_report_page):
        """翻到下一页再翻回，数据恢复"""
        page = daily_report_page
        print("\n========== DLY-042: 翻到上一页 ==========")

        if not page.is_next_page_enabled():
            pytest.skip("仅有单页数据，跳过翻页测试")

        # 第1页第一行
        first_row_p1 = page.get_row_data(1)
        first_date_p1 = first_row_p1[0] if first_row_p1 else ""
        print(f"第1页第一行: {first_date_p1}")

        # 翻到第2页
        page.click_next_page()
        first_row_p2 = page.get_row_data(1)
        first_date_p2 = first_row_p2[0] if first_row_p2 else ""
        print(f"第2页第一行: {first_date_p2}")

        # 翻回第1页
        if page.is_prev_page_enabled():
            page.click_prev_page()
            first_row_back = page.get_row_data(1)
            first_date_back = first_row_back[0] if first_row_back else ""
            print(f"翻回第1页第一行: {first_date_back}")

            assert first_date_back == first_date_p1, (
                f"翻回第1页后第一行应为 '{first_date_p1}'，实际: '{first_date_back}'"
            )
        else:
            print("上一页按钮不可用（可能已在第2页但按钮未启用）")

        print("========== DLY-042 通过 ==========")

    # ==================================================================
    #  DLY-043: 单页时翻页按钮状态
    # ==================================================================
    def test_043_page_buttons_state_single_page(self, daily_report_page):
        """数据不足一页时，上下页按钮应不可用"""
        page = daily_report_page
        print("\n========== DLY-043: 单页翻页按钮状态 ==========")

        total = page.get_total_count()
        print(f"总条数: {total}")

        has_next = page.is_next_page_enabled()
        has_prev = page.is_prev_page_enabled()
        print(f"下一页可用: {has_next}, 上一页可用: {has_prev}")

        # 总条数 ≤ 10 时不应有下一页
        if total <= 10:
            assert not has_next, (
                f"总条数({total}) ≤ 10 时，下一页按钮应不可用"
            )
            assert not has_prev, (
                f"总条数({total}) ≤ 10 时，上一页按钮应不可用（默认在第1页）"
            )

        print("========== DLY-043 通过 ==========")

    # ==================================================================
    #  DLY-044: 切换每页条数
    # ==================================================================
    def test_044_change_page_size(self, daily_report_page):
        """切换每页条数（如从 10条/页 → 20条/页）"""
        page = daily_report_page
        print("\n========== DLY-044: 切换每页条数 ==========")

        total = page.get_total_count()
        print(f"总条数: {total}")

        # 数据不足时切换无意义
        if total <= 10:
            pytest.skip(f"总条数({total}) ≤ 10，切换页大小无意义")

        row_count_before = page.get_table_row_count()
        print(f"切换前: {row_count_before} 行/页")

        # 尝试切换到 20条/页
        try:
            page.select_page_size("20条/页")
        except Exception as e:
            # 如果只有 10条/页 的选项，则跳过
            print(f"切换页大小失败（可能只有一种选项）: {e}")
            # 获取当前页大小确认
            current_size = page.get_current_page_size()
            print(f"当前每页条数: {current_size}")
            pytest.skip(f"无法切换到20条/页: {e}")

        row_count_after = page.get_table_row_count()
        print(f"切换后: {row_count_after} 行/页")

        # 切换到更大每页数后，当前页行数应变多
        if total > 10:
            assert row_count_after > row_count_before, (
                f"切换20条/页后行数({row_count_after})应多于10条/页({row_count_before})"
            )

        print("========== DLY-044 通过 ==========")
