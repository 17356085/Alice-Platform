# =====================================================================
# 测试: 水质分析设计指标页面 (WaterIndicatorPage)
# 模块: lab (化验室取样)
# 特性: 只读展示型页面，无搜索、无分页、无增删改操作
# =====================================================================
import pytest
import allure

# 基础冒烟测试 - WI-01 (P0)
@allure.epic("化验室取样")
@allure.feature("水质分析设计指标")
@allure.story("页面加载与基础展示")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.smoke
def test_001_page_load(water_indicator_page):
    """WI-01: 正常显示水质分析设计指标列表及相关字段"""
    with allure.step("验证页面已加载，表格可见"):
        table_body = water_indicator_page.driver.find_element(*water_indicator_page.TABLE_BODY)
        assert table_body.is_displayed(), "水质分析设计指标页面表格未显示，页面加载失败"

    with allure.step("验证表格存在数据行"):
        row_count = water_indicator_page.get_table_row_count()
        assert row_count > 0, f"表格数据行为空 (row_count={row_count})，期望至少有一行数据。"

    with allure.step("验证表格核心列 (指标名称、分类、单位) 数据不为空"):
        # 假设 col_index: 指标名称=2, 分类=3, 单位=4 (根据PAGE_CONTEXT)
        indicator_names = water_indicator_page.get_column_data(2)
        assert len(indicator_names) == row_count, f"指标名称列数据行数 ({len(indicator_names)}) 与表格行数 ({row_count}) 不符"
        assert all(name.strip() for name in indicator_names), "指标名称列存在空数据"

        categories = water_indicator_page.get_column_data(3)
        assert all(cat.strip() for cat in categories), "分类列存在空数据"

        units = water_indicator_page.get_column_data(4)
        assert all(unit.strip() for unit in units), "单位列存在空数据"


# 关键功能验证 - WI-02 (P1)
@allure.epic("化验室取样")
@allure.feature("水质分析设计指标")
@allure.story("表格数据完整性")
@allure.severity(allure.severity_level.CRITICAL)
def test_002_table_display(water_indicator_page):
    """WI-02: 表格列数据可读，包含所有预期列"""
    with allure.step("获取表格当前行数"):
        row_count = water_indicator_page.get_table_row_count()
        assert row_count == 22, f"期望表格显示22行数据，实际获取到 {row_count} 行。"

    with allure.step("验证表头列信息完整"):
        headers = water_indicator_page.get_table_headers()
        expected_headers = ["序号", "指标名称", "分类", "单位", "规则", "阈值", "备注"]
        missing_headers = [col for col in expected_headers if col not in headers]
        assert not missing_headers, f"表头缺少以下期望列: {missing_headers}"

    with allure.step("验证特定列 (阈值) 数据不为空"):
        threshold_values = water_indicator_page.get_column_data(6)
        assert len(threshold_values) > 0, "阈值列数据为空"
        # 可选: 验证阈值列包含数字或范围格式 (如"6.5-8.5", "100")
        # 通过简单检查第一个非空值来验证格式
        first_threshold = threshold_values[0]
        assert first_threshold and any(c.isdigit() for c in first_threshold), \
            f"阈值列第一个值格式异常: '{first_threshold}', 期望包含数字"

    with allure.step("验证序号列 (第1列) 为连续整数"):
        serial_numbers = water_indicator_page.get_column_data(1)
        assert len(serial_numbers) == row_count, f"序号列行数 ({len(serial_numbers)}) 与表格行数 ({row_count}) 不匹配"
        expected_seq = [str(i) for i in range(1, row_count + 1)]
        assert serial_numbers == expected_seq, \
            f"序号列数据不连续: 实际数据前5个为 {serial_numbers[:5]}, 期望为 {expected_seq[:5]}"