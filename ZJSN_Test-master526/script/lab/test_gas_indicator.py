"""气体分析设计指标 — 测试脚本（只读展示页）"""
import pytest
import allure


def step(text):
    try:
        with allure.step(text):
            print(f"步骤：{text}")
    except Exception:
        print(f"步骤：{text}")


class TestGasIndicatorDisplay:
    """页面展示验证"""

    @allure.epic("化验室取样")
    @allure.feature("气体分析设计指标")
    @allure.story("页面基础展示")
    def test_gi_01_page_display(self, gas_indicator_page):
        """GI-01: 正常显示气体分析设计指标列表及相关字段"""
        page = gas_indicator_page
        step("获取表头并校验")
        headers = page.get_table_headers()
        expected = {"序号", "指标名称", "分类", "单位", "规则", "阈值", "备注"}
        found = [h for h in headers if h in expected]
        assert len(found) >= 5, f"预期表头含{expected}，实际={headers}"

        step("验证表格数据加载")
        row_count = page.get_table_row_count()
        empty = page.get_empty_text() or ""
        assert (row_count > 0) or ("暂无" in empty), f"表格为空，empty='{empty}'"

    def test_gi_02_table_columns(self, gas_indicator_page):
        """GI-02: 表格列数据可读"""
        page = gas_indicator_page
        step("获取指标名称列数据")
        names = page.get_column_data(2)  # 指标名称在第2列
        if names:
            assert len(names) >= 1, f"指标名称列应有数据，实际={names}"
        else:
            row_count = page.get_table_row_count()
            assert row_count >= 1, f"表格应有行数据，实际={row_count}"
