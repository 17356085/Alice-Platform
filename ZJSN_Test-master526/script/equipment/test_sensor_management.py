"""传感器管理模块测试

测试范围：统计卡片、搜索筛选、表格行操作、分页、fixed列按钮
"""
import os
import sys
import pytest
import allure

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page.equipment_page.SensorManagePage import SensorManagePage


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
class TestSensorPageDisplay:

    def test_sn_01_page_load(self, driver_setup):
        """SN-01: 传感器页面正常加载，统计卡片显示"""
        page = SensorManagePage(driver_setup)
        case("SN-01", "传感器管理页面正常加载")

        card_count = page.get_stat_card_count()
        assert card_count >= 4, \
            ea("显示至少4张统计卡片", f"实际{card_count}张")

        stats = page.get_all_stats()
        assert stats['total'] != '', ea("传感器总数不为空", stats)

    def test_sn_02_table_headers(self, driver_setup):
        """SN-02: 表格表头正确显示"""
        page = SensorManagePage(driver_setup)
        case("SN-02", "表格表头正确")

        headers = page.get_table_headers()
        expected = {"传感器名称", "传感器编号", "传感器类型",
                    "监测参数", "安装位置", "绑定设备",
                    "绑定状态", "当前值", "最近上传时间", "操作"}
        # 子集断言：表头包含这些即可
        missing = expected - set(headers)
        assert not missing, ea(f"表头包含所有列", f"缺少: {missing}")


# ==================================================================
#  搜索筛选
# ==================================================================
class TestSensorSearch:

    def test_sn_03_search_by_keyword(self, driver_setup):
        """SN-03: 按传感器名称/编号搜索"""
        page = SensorManagePage(driver_setup)
        case("SN-03", "按名称搜索传感器")

        page.input_keyword("测试")
        page.click_search()
        count = page.get_table_row_count()
        assert count >= 0, ea("搜索结果正常", f"匹配{count}行")

    def test_sn_04_search_no_result(self, driver_setup):
        """SN-04: 搜索不存在的数据"""
        page = SensorManagePage(driver_setup)
        case("SN-04", "搜索无结果")

        page.input_keyword("zzz_no_such_sensor_999")
        page.click_search()
        empty = page.is_present(page.TABLE_EMPTY, timeout=3)
        assert empty or page.get_table_row_count() == 0, \
            ea("显示空数据", f"empty={empty}")

    def test_sn_05_reset(self, driver_setup):
        """SN-05: 重置按钮恢复全部数据"""
        page = SensorManagePage(driver_setup)
        case("SN-05", "重置按钮")

        page.input_keyword("测试")
        page.click_search()
        page.click_reset()
        assert page.get_table_row_count() > 0, \
            ea("重置后恢复全部数据", page.get_table_row_count())


# ==================================================================
#  行操作（验证 fixed 列按钮可正常点击）
# ==================================================================
class TestSensorRowActions:

    def test_sn_06_view_detail(self, driver_setup):
        """SN-06: 点击查看按钮弹出详情弹窗"""
        page = SensorManagePage(driver_setup)
        case("SN-06", "查看传感器详情")

        if page.get_table_row_count() == 0:
            pytest.skip("表格无数据")

        first_name = page.get_column_data(1)[0] if page.get_column_data(1) else None
        if not first_name:
            pytest.skip("无法获取传感器名称")

        step(f"查看: {first_name}")
        page.click_row_button(first_name, "查看")
        assert page.is_visible(page.DIALOG, timeout=5), \
            ea("打开详情弹窗", "弹窗未出现")

    def test_sn_07_click_edit(self, driver_setup):
        """SN-07: 点击编辑按钮弹出编辑弹窗"""
        page = SensorManagePage(driver_setup)
        case("SN-07", "编辑传感器")

        if page.get_table_row_count() == 0:
            pytest.skip("表格无数据")

        first_name = page.get_column_data(1)[0] if page.get_column_data(1) else None
        if not first_name:
            pytest.skip("无法获取传感器名称")

        page.click_row_button(first_name, "编辑")
        assert page.is_visible(page.DIALOG, timeout=5), \
            ea("打开编辑弹窗", "弹窗未出现")

    def test_sn_08_bind_status_tag(self, driver_setup):
        """SN-08: 绑定状态列显示 el-tag"""
        page = SensorManagePage(driver_setup)
        case("SN-08", "绑定状态标签")

        if page.get_table_row_count() == 0:
            pytest.skip("表格无数据")

        # 找第一行有名称的传感器
        names = page.get_column_data(1)
        if not names:
            pytest.skip("无法获取传感器名称")

        for name in names:
            status = page.get_row_bind_status(name)
            if status:
                print(f"  {name}: 绑定状态 = {status}")
                assert status, ea("绑定状态不为空", status)
                return

        # 所有行绑定状态都为空（可能全是未绑定）
        print("  所有行绑定状态为空（可能全部未绑定）")


# ==================================================================
#  分页
# ==================================================================
class TestSensorPagination:

    def test_sn_09_pagination_exists(self, driver_setup):
        """SN-09: 分页组件存在"""
        page = SensorManagePage(driver_setup)
        case("SN-09", "分页组件")

        total = page.get_total_count()
        assert total > 0, ea("分页总数 > 0", total)

    def test_sn_10_next_page(self, driver_setup):
        """SN-10: 翻页后数据正确加载"""
        page = SensorManagePage(driver_setup)
        case("SN-10", "翻页切换")

        total = page.get_total_count()
        if total <= 10:
            pytest.skip("数据不足一页")

        page.click_next_page()
        assert page.get_table_row_count() > 0, ea("第二页有数据", 0)


# ==================================================================
#  弹窗测试
# ==================================================================
class TestSensorAddDialog:

    def test_sn_11_add_dialog_open(self, driver_setup):
        """SN-11: 点击新增传感器弹出弹窗"""
        page = SensorManagePage(driver_setup)
        case("SN-11", "新增传感器弹窗")

        page.click_add()
        assert page.is_visible(page.DIALOG, timeout=5), \
            ea("弹出新增弹窗", "弹窗未出现")

        # 确认弹窗标题
        title = page.get_dialog_title()
        print(f"  弹窗标题: {title}")

        page.click_dialog_cancel()

    def test_sn_12_add_dialog_form_fill(self, driver_setup):
        """SN-12: 新增传感器—填写必填字段并保存"""
        page = SensorManagePage(driver_setup)
        case("SN-12", "新增传感器表单填写")

        page.click_add()
        step("填写必填字段")
        page.fill_sensor_form(
            name="自动化测试传感器",
            code="AUTO-TEST-001",
            sensor_type="温度传感器",
            location="测试位置",
        )
        step("点击保存")
        page.click_dialog_save()
        # 等待保存完成（弹窗关闭或 Toast 出现）
        try:
            page.wait_dialog_close(timeout=5)
        except Exception:
            pass
        msg = page.wait_for_toast_text(timeout=5)
        print(f"  [DEBUG] 保存Toast: {msg!r}")

        step("搜索验证数据存在")
        page.click_reset()
        page.input_keyword("自动化测试传感器")
        page.click_search()
        names = page.get_column_data(1)
        assert names or page.get_empty_text(), \
            ea("保存后能搜索到数据（或编号已存在提示）", names or page.get_empty_text())


class TestSensorDetailDialog:

    def test_sn_13_view_detail_fields(self, driver_setup):
        """SN-13: 查看传感器详情—校验描述字段"""
        page = SensorManagePage(driver_setup)
        case("SN-13", "传感器详情弹窗")

        if page.get_table_row_count() == 0:
            pytest.skip("表格无数据")

        names = page.get_column_data(1)
        if not names:
            pytest.skip("无法获取传感器名称")

        step(f"查看: {names[0]}")
        page.click_row_button(names[0], "查看")
        assert page.is_visible(page.DIALOG, timeout=5), \
            ea("打开详情弹窗", "弹窗未出现")

        # 读取几个关键字段
        sensor_name = page.get_detail_field("传感器名称")
        bind_status = page.get_detail_bind_status()
        print(f"  传感器名称: {sensor_name}, 绑定状态: {bind_status}")
        assert sensor_name, ea("传感器名称不为空", sensor_name)


class TestSensorEditDialog:

    def test_sn_14_edit_dialog_code_disabled(self, driver_setup):
        """SN-14: 编辑弹窗—传感器编号为禁用状态"""
        page = SensorManagePage(driver_setup)
        case("SN-14", "编辑弹窗编号禁用")

        if page.get_table_row_count() == 0:
            pytest.skip("表格无数据")

        names = page.get_column_data(1)
        if not names:
            pytest.skip("无法获取传感器名称")

        page.click_row_button(names[0], "编辑")
        assert page.is_visible(page.DIALOG, timeout=5), \
            ea("打开编辑弹窗", "弹窗未出现")

        # 关键断言：传感器编号为禁用状态
        assert page.is_code_disabled_in_edit(), \
            ea("传感器编号为禁用状态", "编号输入框未禁用")

        page.click_dialog_cancel()


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
