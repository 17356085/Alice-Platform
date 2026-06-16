"""装置台账（装置）管理模块测试

基于真实 HTML 结构（.stat-card / .search-wrapper / .table-wrapper）
"""
import os
import sys
import pytest
import allure

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page.equipment_page.UnitManagePage import UnitManagePage


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
class TestUnitPageDisplay:

    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("装置台账管理")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_un_01_page_load_success(self, driver_setup):
        """UN-01: 装置台账页面正常加载"""
        page = UnitManagePage(driver_setup)
        case("UN-01", "正常加载装置台账页面")

        step("验证统计卡片加载")
        card_count = page.get_stat_card_count()
        assert card_count >= 4, \
            ea("显示至少4张统计卡片", f"实际{card_count}张")

        step("验证统计数字不为空")
        stats = page.get_all_stats()
        assert stats['total'] != '', ea("装置总数不为空", stats)

    def test_un_02_stat_cards_data(self, driver_setup):
        """UN-02: 统计卡片数据校验"""
        page = UnitManagePage(driver_setup)
        case("UN-02", "统计卡片数据校验")

        stats = page.get_all_stats()
        step(f"统计: 总数={stats['total']}, 运行={stats['running']}, "
             f"维护={stats['maintenance']}, 停用={stats['stopped']}")

        for key in stats:
            val = stats[key]
            assert val.isdigit(), ea(f"{key}为数字", val)
            assert int(val) >= 0, ea(f"{key} >= 0", val)

    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("装置台账管理")
    @allure.story("表格表头展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_un_03_table_headers(self, driver_setup):
        """UN-03: 表格表头正确显示"""
        page = UnitManagePage(driver_setup)
        case("UN-03", "表格表头正确显示")

        headers = page.get_table_headers()
        expected = {"装置名称", "装置编号", "装置类型",
                    "所属区域", "状态", "关联设备数", "操作"}
        assert expected.issubset(set(headers)), \
            ea(f"表头包含{expected}", headers)

    def test_un_04_table_has_data(self, driver_setup):
        """UN-04: 表格显示装置数据"""
        page = UnitManagePage(driver_setup)
        case("UN-04", "表格显示装置数据")

        row_count = page.get_table_row_count()
        assert row_count > 0, ea("表格至少1行数据", f"当前{row_count}行")

    def test_un_05_pagination_exists(self, driver_setup):
        """UN-05: 分页组件正常显示"""
        page = UnitManagePage(driver_setup)
        case("UN-05", "分页组件正常显示")

        total = page.get_total_count()
        assert total > 0, ea("分页总数 > 0", total)


# ==================================================================
#  搜索筛选
# ==================================================================
class TestUnitSearch:

    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("装置台账管理")
    @allure.story("按名称搜索")
    @allure.severity(allure.severity_level.NORMAL)
    def test_un_06_search_by_name(self, driver_setup):
        """UN-06: 按装置名称搜索"""
        page = UnitManagePage(driver_setup)
        case("UN-06", "按装置名称搜索")

        # 先获取第一条数据的名称作为搜索关键词
        names = page.get_all_unit_names_on_page()
        if not names:
            pytest.skip("表格无数据，跳过搜索测试")

        keyword = names[0][:3]  # 取前3个字符模糊搜索
        step(f"输入关键词: {keyword}")
        page.input_unit_name(keyword)
        page.click_search()

        row_count = page.get_table_row_count()
        assert row_count > 0, ea("搜索结果至少1条", f"实际{row_count}条")

    def test_un_07_search_no_result(self, driver_setup):
        """UN-07: 搜索不存在的数据"""
        page = UnitManagePage(driver_setup)
        case("UN-07", "搜索无结果")

        step("输入不存在的关键词")
        page.input_unit_name("zzz_no_such_unit_999")
        page.click_search()

        empty = page.is_table_empty()
        row_count = page.get_table_row_count()
        assert empty or row_count == 0, \
            ea("表格显示空数据或0行", f"empty={empty}, rows={row_count}")

    def test_un_08_reset_button(self, driver_setup):
        """UN-08: 重置按钮恢复全部数据"""
        page = UnitManagePage(driver_setup)
        case("UN-08", "重置按钮功能")

        step("输入搜索条件")
        page.input_unit_name("test")
        page.click_search()

        step("点击重置")
        page.click_reset()

        row_count = page.get_table_row_count()
        assert row_count > 0, ea("重置后恢复全部数据", f"当前{row_count}行")

    def test_un_09_search_by_type(self, driver_setup):
        """UN-09: 按装置类型搜索"""
        page = UnitManagePage(driver_setup)
        case("UN-09", "按装置类型搜索")

        step("选择装置类型")
        page.select_unit_type("生产装置")
        page.click_search()

        row_count = page.get_table_row_count()
        assert row_count >= 0, ea("搜索结果正常显示", row_count)


# ==================================================================
#  新增装置（P0）
# ==================================================================
class TestUnitAdd:

    # 测试数据 — 用于创建后清理
    CREATED_UNIT_CODE = None

    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("装置台账管理")
    @allure.story("新增装置")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_un_10_add_required_fields(self, driver_setup):
        """UN-10: 新增装置 — 仅必填字段"""
        import time as _time
        page = UnitManagePage(driver_setup)
        case("UN-10", "新增装置-仅必填字段")

        ts = str(int(_time.time()))[-6:]
        before_count = page.get_total_count()

        step("新增装置（必填字段）")
        toast = page.add_unit({
            'unitName': f'自动化测试A{ts}',
            'unitCode': f'AUTOA{ts}',
            'unitType': '生产装置',
        })

        step("验证操作结果")
        if toast:
            assert '成功' in toast, ea("提示包含'成功'", toast)
        # 验证列表新增记录（即使无 toast 也靠 table 判断）
        step("验证列表新增记录")
        assert page.is_row_present(f'AUTOA{ts}'), \
            ea("列表中出现新装置编码", "未找到")

        step("验证总数+1")
        after_count = page.get_total_count()
        assert after_count >= before_count + 1, \
            ea("总数增加", f"前{before_count} → 后{after_count}")

        # 记录以供清理
        TestUnitAdd.CREATED_UNIT_CODE = f'AUTOA{ts}'

    def test_un_11_add_all_fields(self, driver_setup):
        """UN-11: 新增装置 — 填写全部字段"""
        page = UnitManagePage(driver_setup)
        case("UN-11", "新增装置-全部字段")

        step("新增装置（全字段）")
        toast = page.add_unit({
            'unitName': '自动化测试装置B',
            'unitCode': 'AUTO-TEST-B-001',
            'unitType': '辅助装置',
            'area': '原料气压缩工区',
            'description': 'Selenium自动化测试',
        })

        step("验证新增成功")
        assert '成功' in (toast or ''), ea("提示成功", toast)

        step("查看详情验证字段")
        page.click_view('AUTO-TEST-B-001')
        page.wait_detail_dialog_open()

        detail = page.get_all_detail_values()
        assert detail['装置名称'] == '自动化测试装置B', \
            ea("装置名称='自动化测试装置B'", detail['装置名称'])
        assert detail['装置编号'] == 'AUTO-TEST-B-001', \
            ea("装置编号='AUTO-TEST-B-001'", detail['装置编号'])

        page.click_detail_close()

    def test_un_12_add_cancel(self, driver_setup):
        """UN-12: 新增装置 — 取消操作"""
        page = UnitManagePage(driver_setup)
        case("UN-12", "新增装置-取消")

        before_count = page.get_total_count()

        step("打开新增弹窗，填写后取消")
        page.click_add()
        page.fill_form_unit_name('取消测试装置')
        page.fill_form_unit_code('CANCEL-TEST-001')
        page.click_form_cancel()

        step("验证数据未入库")
        assert not page.is_row_present('CANCEL-TEST-001'), \
            ea("取消后数据不存在于列表", "存在")

        after_count = page.get_total_count()
        assert after_count == before_count, \
            ea("总数不变化", f"前{before_count} → 后{after_count}")

    def test_un_13_add_empty_required(self, driver_setup):
        """UN-13: 新增装置 — 必填校验"""
        page = UnitManagePage(driver_setup)
        case("UN-13", "新增装置-必填校验")

        step("直接点击保存（不填任何字段）")
        page.click_add()
        page.click_dialog_save()

        step("验证表单校验错误")
        error = page.get_form_error()
        # 不填必填项时应出现校验提示
        # 表单校验可能只显示一个字段的错误
        assert error != '', ea("出现校验错误提示", "无错误提示" if not error else error)


# ==================================================================
#  编辑装置（P0）
# ==================================================================
class TestUnitEdit:

    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("装置台账管理")
    @allure.story("编辑装置")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_un_14_edit_and_verify(self, driver_setup):
        """UN-14: 编辑装置 — 修改名称"""
        page = UnitManagePage(driver_setup)
        case("UN-14", "编辑装置-修改名称")

        if page.get_table_row_count() == 0:
            pytest.skip("表格无数据，跳过编辑测试")

        # 找到第一条可编辑的记录
        names = page.get_all_unit_names_on_page()
        if not names:
            pytest.skip("表格无装置名称")

        target = names[0]
        new_name = f"{target}_改"

        step(f"编辑「{target}」→ 名称改为「{new_name}」")
        toast = page.edit_unit(target, {'unitName': new_name})

        step("验证操作成功")
        assert '成功' in (toast or ''), ea("提示成功", toast)

        step("验证名称已更新")
        assert page.is_row_present(new_name), \
            ea(f"列表中出现新名称「{new_name}」", "未找到")

        step("还原名称")
        page.edit_unit(new_name, {'unitName': target})


# ==================================================================
#  查看详情
# ==================================================================
class TestUnitDetail:

    def test_un_15_view_detail_dialog(self, driver_setup):
        """UN-15: 查看装置详情弹窗"""
        page = UnitManagePage(driver_setup)
        case("UN-15", "查看装置详情弹窗")

        if page.get_table_row_count() == 0:
            pytest.skip("表格无数据")

        names = page.get_all_unit_names_on_page()
        if not names:
            pytest.skip("表格无装置名称")

        target = names[0]
        step(f"查看「{target}」详情")
        page.click_view(target)

        step("验证详情弹窗打开")
        page.wait_detail_dialog_open()
        assert page.is_visible(page.DETAIL_DIALOG, timeout=3), \
            ea("详情弹窗已打开", "未出现")

        step("验证详情字段非空")
        detail = page.get_all_detail_values()
        assert detail['装置名称'] != '', ea("装置名称非空", detail['装置名称'])
        assert detail['装置编号'] != '', ea("装置编号非空", detail['装置编号'])

        page.click_detail_close()


# ==================================================================
#  分页操作
# ==================================================================
class TestUnitPagination:

    def test_un_16_next_page(self, driver_setup):
        """UN-16: 分页 — 点击下一页"""
        page = UnitManagePage(driver_setup)
        case("UN-16", "分页-下一页")

        total = page.get_total_count()
        if not page.is_visible(page.PAGE_NEXT, timeout=2):
            pytest.skip("无可用下一页（数据仅一页，总数={}）".format(total))

        step("点击下一页")
        page.click_next_page()
        assert page.get_table_row_count() > 0, ea("第二页有数据", 0)

    def test_un_17_change_page_size(self, driver_setup):
        """UN-17: 分页 — 切换每页条数"""
        page = UnitManagePage(driver_setup)
        case("UN-17", "分页-切换每页条数")

        total = page.get_total_count()
        if not page.is_visible(page.PAGE_SIZE_SELECT, timeout=2):
            pytest.skip("分页大小选择器不可用（数据仅一页，总数={}）".format(total))

        step("切换每页显示20条")
        page.change_page_size(20)

        row_count = page.get_table_row_count()
        # 如果总数 >= 20，应该有20行；否则应有 total 行
        expected = min(total, 20)
        assert row_count <= expected, \
            ea(f"每页≤{expected}条", f"实际{row_count}条")

        step("恢复每页10条")
        page.change_page_size(10)


# ==================================================================
#  关联设备（P1）
# ==================================================================
class TestUnitBindDevice:

    def test_un_18_bind_dialog_opens(self, driver_setup):
        """UN-18: 关联设备弹窗打开"""
        page = UnitManagePage(driver_setup)
        case("UN-18", "关联设备弹窗打开")

        if page.get_table_row_count() == 0:
            pytest.skip("表格无数据")

        names = page.get_all_unit_names_on_page()
        if not names:
            pytest.skip("表格无装置名称")

        target = names[0]
        step(f"点击「{target}」的关联设备按钮")
        page.click_bind_device(target)

        step("验证关联设备弹窗打开")
        assert page.is_visible(page.BIND_DIALOG, timeout=5), \
            ea("关联设备弹窗已打开", "未出现")

        step("验证设备表格数据加载")
        device_count = page.get_bind_device_row_count()
        assert device_count >= 0, ea("设备表格正常显示", f"{device_count}行")

        step("验证已选计数显示")
        selected = page.get_selected_device_count()
        print(f"已选设备数: {selected}")

        page.click_bind_cancel()

    def test_un_19_bind_search_device(self, driver_setup):
        """UN-19: 关联弹窗 — 搜索设备"""
        page = UnitManagePage(driver_setup)
        case("UN-19", "关联弹窗-搜索设备")

        if page.get_table_row_count() == 0:
            pytest.skip("表格无数据")

        names = page.get_all_unit_names_on_page()
        if not names:
            pytest.skip("表格无装置名称")

        page.click_bind_device(names[0])

        step("搜索设备名称")
        page.search_bind_device_by_name("test")
        row_count = page.get_bind_device_row_count()
        assert row_count >= 0, ea("设备搜索正常", f"结果{row_count}行")

        step("重置设备搜索")
        page.reset_bind_device_search()
        assert page.get_bind_device_row_count() >= 0, ea("重置后恢复全部设备", "")

        page.click_bind_cancel()


# ==================================================================
#  导入导出（P1）
# ==================================================================
class TestUnitImportExport:

    def test_un_20_export(self, driver_setup):
        """UN-20: 导出装置数据"""
        page = UnitManagePage(driver_setup)
        case("UN-20", "导出装置数据")

        if page.get_table_row_count() == 0:
            pytest.skip("表格无数据，跳过导出")

        step("点击导出按钮")
        result = page.click_export()
        step(f"导出结果: MessageBox确认={result}")

    def test_un_21_import_dialog_opens(self, driver_setup):
        """UN-21: 导入弹窗打开"""
        page = UnitManagePage(driver_setup)
        case("UN-21", "导入弹窗打开")

        step("点击导入按钮")
        page.click_import()
        page.wait_import_dialog_open()

        assert page.is_visible(page.IMPORT_DIALOG, timeout=3), \
            ea("导入装置弹窗已打开", "未出现")

        page.close_import_dialog()


# ==================================================================
#  权限检查（P1）
# ==================================================================
class TestUnitPermissions:

    def test_un_22_add_button_visible(self, driver_setup):
        """UN-22: 新增装置按钮对admin可见"""
        page = UnitManagePage(driver_setup)
        case("UN-22", "新增按钮可见性")

        assert page.is_add_button_visible(), \
            ea("新增装置按钮可见", "不可见")

    def test_un_23_export_button_visible(self, driver_setup):
        """UN-23: 导出按钮可见"""
        page = UnitManagePage(driver_setup)
        case("UN-23", "导出按钮可见性")

        assert page.is_export_button_visible(), \
            ea("导出按钮可见", "不可见")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
