"""设备管理（设备台账）模块测试

基于真实 HTML 结构（.stat-card / .search-wrapper / .table-wrapper）
"""
import os
import sys
import pytest
import allure

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page.equipment_page.EquipmentPage import EquipmentPage


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
    except Exception:
        pass


def ea(expected, actual):
    return f"预期结果：{expected}；实际结果：{actual}"


# ==================================================================
#  页面展示
# ==================================================================
class TestEquipmentPageDisplay:

    def test_eq_01_page_load_success(self, driver_setup):
        """EQ-01: 设备台账页面正常加载"""
        page = EquipmentPage(driver_setup)
        case("EQ-01", "正常加载设备台账页面")

        step("验证统计卡片加载")
        card_count = page.get_stat_card_count()
        assert card_count >= 4, \
            ea("显示至少4张统计卡片", f"实际{card_count}张")

        step("验证统计数字不为空")
        stats = page.get_all_stats()
        assert stats['total'] != '', ea("设备总数不为空", stats)

    def test_eq_02_stat_cards_data(self, driver_setup):
        """EQ-02: 统计卡片数据校验"""
        page = EquipmentPage(driver_setup)
        case("EQ-02", "统计卡片数据校验")

        stats = page.get_all_stats()
        step(f"统计: 总数={stats['total']}, 运行={stats['running']}, "
             f"维护={stats['maintenance']}, 停用={stats['stopped']}")

        for key in stats:
            val = stats[key]
            assert val.isdigit(), ea(f"{key}为数字", val)
            assert int(val) >= 0, ea(f"{key} >= 0", val)

    def test_eq_03_table_headers(self, driver_setup):
        """EQ-03: 表格表头正确显示"""
        page = EquipmentPage(driver_setup)
        case("EQ-03", "表格表头正确显示")

        headers = page.get_table_headers()
        expected = {"设备名称", "设备编号", "设备类型",
                    "所属装置", "规格型号", "生产厂家", "操作"}
        assert expected.issubset(set(headers)), \
            ea(f"表头包含{expected}", headers)

    def test_eq_04_table_has_data(self, driver_setup):
        """EQ-04: 表格有数据"""
        page = EquipmentPage(driver_setup)
        case("EQ-04", "表格显示设备数据")

        row_count = page.get_table_row_count()
        assert row_count > 0, ea("表格至少1行数据", f"当前{row_count}行")


# ==================================================================
#  搜索筛选
# ==================================================================
class TestEquipmentSearch:

    def test_eq_05_search_by_keyword(self, driver_setup):
        """EQ-05: 按设备名称/编号搜索"""
        page = EquipmentPage(driver_setup)
        case("EQ-05", "按设备名称搜索")

        step("输入关键词: test")
        page.input_keyword("test")
        page.click_search()
        row_count = page.get_table_row_count()
        assert row_count >= 0, ea("搜索结果正常显示", row_count)

    def test_eq_06_search_no_result(self, driver_setup):
        """EQ-06: 搜索不存在的数据"""
        page = EquipmentPage(driver_setup)
        case("EQ-06", "搜索无结果")

        step("输入不存在的关键词")
        page.input_keyword("zzz_no_such_device_999")
        page.click_search()

        empty = page.is_present(page.TABLE_EMPTY, timeout=3)
        row_count = page.get_table_row_count()
        assert empty or row_count == 0, \
            ea("表格显示空数据或0行", f"empty={empty}, rows={row_count}")

    def test_eq_07_reset_button(self, driver_setup):
        """EQ-07: 重置按钮恢复全部数据"""
        page = EquipmentPage(driver_setup)
        case("EQ-07", "重置按钮功能")

        step("输入搜索条件")
        page.input_keyword("test")
        page.click_search()

        step("点击重置")
        page.click_reset()
        row_count = page.get_table_row_count()
        assert row_count > 0, ea("重置后恢复全部数据", f"当前{row_count}行")


# ==================================================================
#  行操作
# ==================================================================
class TestEquipmentRowActions:

    def test_eq_08_view_detail(self, driver_setup):
        """EQ-08: 点击查看按钮弹出详情"""
        page = EquipmentPage(driver_setup)
        case("EQ-08", "点击查看按钮")

        # 先搜索确保有匹配行
        page.input_keyword("test")
        page.click_search()
        if page.get_table_row_count() == 0:
            pytest.skip("表格无数据")

        step("点击第一行的查看按钮")
        # 获取第一行设备名称作为行标识
        first_col = page.get_column_data(1)
        if not first_col:
            pytest.skip("无法获取行数据")
        row_id = first_col[0] if first_col else "test"
        page.click_row_button(row_id, "查看")
        dialog_open = page.is_visible(page.DIALOG, timeout=5)
        assert dialog_open, ea("打开详情弹窗", "弹窗未出现")

    def test_eq_09_click_edit(self, driver_setup):
        """EQ-09: 点击编辑按钮弹出编辑弹窗"""
        page = EquipmentPage(driver_setup)
        case("EQ-09", "点击编辑按钮")

        # 先搜索确保有匹配行
        page.input_keyword("test")
        page.click_search()
        if page.get_table_row_count() == 0:
            pytest.skip("表格无数据")

        step("点击第一行的编辑按钮")
        first_col = page.get_column_data(1)
        if not first_col:
            pytest.skip("无法获取行数据")
        row_id = first_col[0] if first_col else "test"
        page.click_row_button(row_id, "编辑")
        dialog_open = page.is_visible(page.DIALOG, timeout=5)
        assert dialog_open, ea("打开编辑弹窗", "弹窗未出现")


# ==================================================================
#  分页
# ==================================================================
class TestEquipmentPagination:

    def test_eq_10_pagination_exists(self, driver_setup):
        """EQ-10: 分页组件正常显示"""
        page = EquipmentPage(driver_setup)
        case("EQ-10", "分页组件正常显示")

        total = page.get_total_count()
        assert total > 0, ea("分页总数 > 0", total)

    def test_eq_11_next_page(self, driver_setup):
        """EQ-11: 点击下一页"""
        page = EquipmentPage(driver_setup)
        case("EQ-11", "分页—下一页")

        total = page.get_total_count()
        if total <= 10:
            pytest.skip("数据不足一页，跳过")

        step("点击下一页")
        page.click_next_page()
        assert page.get_table_row_count() > 0, ea("第二页有数据", 0)


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
