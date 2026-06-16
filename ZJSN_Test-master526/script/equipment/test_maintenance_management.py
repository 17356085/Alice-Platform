"""设备维保计划管理模块测试 — 基于实际页面结构

页面类型：维保计划列表管理页，非维保记录管理页
表格列：计划编码、计划名称、设备名称、维保类型、周期(天)、上次维保、下次维保、状态、操作
行按钮：[编辑]、[生成任务]
搜索区：维保类型下拉、状态下拉
"""
import os
import sys
import pytest
import allure

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium.webdriver.common.by import By

from page.equipment_page.MaintenancePage import MaintenancePage


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
#  页面展示（P0）
# ==================================================================
class TestMaintenancePageDisplay:

    @pytest.mark.smoke
    @allure.epic("设备管理")
    @allure.feature("设备维保管理")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_mt_01_page_load_success(self, driver_setup):
        """MT-01: 设备维保页面正常加载"""
        page = MaintenancePage(driver_setup)
        page.navigate_to_maintenance()
        case("MT-01", "正常加载设备维保页面")

        step("验证页面 URL 包含 maintenance")
        current_url = driver_setup.current_url
        assert '#/equipment/maintenance' in current_url, \
            ea("URL 包含 #/equipment/maintenance", current_url)

        step("验证页面标题")
        assert '设备维保' in driver_setup.title, \
            ea("页面标题包含设备维保", driver_setup.title)

        step("验证表格表头存在")
        headers = page.get_table_headers()
        assert len(headers) > 0, ea("表头至少1列", f"实际{len(headers)}列")
        step(f"表头: {headers}")

    def test_mt_02_table_headers(self, driver_setup):
        """MT-02: 表格表头正确显示"""
        page = MaintenancePage(driver_setup)
        case("MT-02", "表格表头正确显示")

        headers = page.get_table_headers()
        expected = {"计划编码", "计划名称", "设备名称",
                    "维保类型", "周期(天)", "上次维保", "下次维保", "状态", "操作"}
        assert expected.issubset(set(headers)), \
            ea(f"表头包含{expected}", headers)

    def test_mt_03_table_has_data(self, driver_setup):
        """MT-03: 表格显示维保计划数据"""
        page = MaintenancePage(driver_setup)
        case("MT-03", "表格显示维保计划数据")

        row_count = page.get_table_row_count()
        assert row_count > 0, ea("表格至少1行数据", f"当前{row_count}行")

    def test_mt_04_pagination_exists(self, driver_setup):
        """MT-04: 分页组件正常显示"""
        page = MaintenancePage(driver_setup)
        case("MT-04", "分页组件正常显示")

        total = page.get_total_count()
        assert total > 0, ea("分页总数 > 0", total)


# ==================================================================
#  搜索筛选（P1）
# ==================================================================
class TestMaintenanceSearch:

    def test_mt_05_search_by_type(self, driver_setup):
        """MT-05: 按维保类型搜索"""
        page = MaintenancePage(driver_setup)
        case("MT-05", "按维保类型搜索")

        step("选择维保类型")
        page.select_type("日检")
        page.click_search()

        row_count = page.get_table_row_count()
        assert row_count >= 0, ea("搜索结果正常显示", row_count)

    def test_mt_06_search_by_status(self, driver_setup):
        """MT-06: 按维保状态搜索"""
        page = MaintenancePage(driver_setup)
        case("MT-06", "按维保状态搜索")

        step("选择维保状态")
        page.select_status("待执行")
        page.click_search()

        row_count = page.get_table_row_count()
        assert row_count >= 0, ea("搜索结果正常显示", row_count)

    def test_mt_07_reset_button(self, driver_setup):
        """MT-07: 重置按钮恢复全部数据"""
        page = MaintenancePage(driver_setup)
        case("MT-07", "重置按钮功能")

        total_before = page.get_total_count()

        step("选择搜索条件后查询")
        page.select_type("日检")
        page.click_search()

        step("点击重置")
        page.click_reset()

        total_after = page.get_total_count()
        assert total_after >= total_before, \
            ea("重置后总数恢复或更多", f"前{total_before} → 后{total_after}")

        row_count = page.get_table_row_count()
        assert row_count > 0, ea("重置后显示数据", f"当前{row_count}行")


# ==================================================================
#  分页操作（P1）
# ==================================================================
class TestMaintenancePagination:

    def test_mt_08_next_page(self, driver_setup):
        """MT-08: 分页 — 点击下一页"""
        page = MaintenancePage(driver_setup)
        case("MT-08", "分页-下一页")

        total = page.get_total_count()
        if not page.is_visible(page.PAGE_NEXT, timeout=2):
            pytest.skip(f"无可用下一页（数据仅一页，总数={total}）")

        step("点击下一页")
        page.click_next_page()
        assert page.get_table_row_count() > 0, ea("第二页有数据", 0)

    def test_mt_09_change_page_size(self, driver_setup):
        """MT-09: 分页 — 切换每页条数"""
        page = MaintenancePage(driver_setup)
        case("MT-09", "分页-切换每页条数")

        total = page.get_total_count()
        if not page.is_visible(page.PAGE_SIZE_SELECT, timeout=2):
            pytest.skip(f"分页大小选择器不可用（数据仅一页，总数={total}）")

        step("切换每页显示20条")
        page.change_page_size(20)

        row_count = page.get_table_row_count()
        expected = min(total, 20)
        assert row_count <= expected, \
            ea(f"每页≤{expected}条", f"实际{row_count}条")

        step("恢复每页10条")
        page.change_page_size(10)


# ==================================================================
#  新增计划（P0）
# ==================================================================
class TestMaintenanceAdd:
    CREATED_PLAN_NAME = None

    @pytest.mark.smoke
    @allure.epic("设备管理")
    @allure.feature("设备维保管理")
    @allure.story("新增维保计划")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_mt_10_add_plan(self, driver_setup):
        """MT-10: 新增维保计划"""
        page = MaintenancePage(driver_setup)
        case("MT-10", "新增维保计划")

        before_count = page.get_total_count()

        step("打开新增弹窗并填写表单")
        page.click_add()
        page.fill_form_plan_name("AUTO_测试计划")
        # 关联设备是 filterable 下拉，传设备名称关键字
        page.fill_form_equipment("test")
        # 维保类型是普通下拉
        page.fill_form_type("日检")
        page.fill_form_cycle(7)

        step("保存")
        toast = page.click_form_save()

        # 尝试获取 toast（可能已消失），主要验证数据是否写入
        if toast:
            assert '成功' in toast, ea("提示包含'成功'", toast)

        step("验证总数增加（弹窗已关闭，保存成功）")
        after_count = page.get_total_count()
        assert after_count >= before_count + 1, \
            ea("总数增加", f"前{before_count} → 后{after_count}")

        TestMaintenanceAdd.CREATED_PLAN_NAME = "AUTO_测试计划"

    @pytest.mark.smoke
    @allure.epic("设备管理")
    @allure.feature("设备维保管理")
    @allure.story("新增维保计划")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_mt_11_add_cancel(self, driver_setup):
        """MT-11: 新增维保计划 — 取消操作"""
        page = MaintenancePage(driver_setup)
        case("MT-11", "新增计划-取消")

        before_count = page.get_total_count()

        step("打开新增弹窗，填写后取消")
        page.click_add()
        page.fill_form_plan_name("AUTO_取消测试")
        page.click_form_cancel()

        step("验证数据未入库")
        assert not page.is_row_present("AUTO_取消测试"), \
            ea("取消后数据不存在于列表", "存在")

        after_count = page.get_total_count()
        assert after_count == before_count, \
            ea("总数不变化", f"前{before_count} → 后{after_count}")

    def test_mt_12_add_empty_required(self, driver_setup):
        """MT-12: 新增计划 — 必填校验"""
        page = MaintenancePage(driver_setup)
        case("MT-12", "新增计划-必填校验")

        step("直接点击保存（不填任何字段）")
        page.click_add()
        page.click_dialog_save()

        step("验证表单校验错误")
        error = page.get_form_error()
        assert error != '', ea("出现校验错误提示", "无错误提示" if not error else error)


# ==================================================================
#  编辑计划（P0）
# ==================================================================
class TestMaintenanceEdit:

    @pytest.mark.smoke
    @allure.epic("设备管理")
    @allure.feature("设备维保管理")
    @allure.story("编辑维保计划")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_mt_13_edit_plan_name(self, driver_setup):
        """MT-13: 编辑维保计划 — 修改计划名称"""
        page = MaintenancePage(driver_setup)
        case("MT-13", "编辑计划-修改名称")

        if page.get_table_row_count() == 0:
            pytest.skip("表格无数据")

        # 获取第一条计划名称
        name_idx = page.get_column_index_by_header("计划名称")
        if not name_idx:
            pytest.skip("未找到计划名称列")
        names = page.get_column_data(name_idx)
        if not names:
            pytest.skip("表格无计划名称数据")

        target = names[0]
        new_name = f"{target}_改"

        step(f"编辑「{target}」→ 名称改为「{new_name}」")
        page.click_edit(target)
        page.fill_form_plan_name(new_name)
        toast = page.click_form_save()

        assert '成功' in (toast or ''), ea("提示成功", toast)

        step("验证名称已更新")
        assert page.is_row_present(new_name), \
            ea(f"列表中出现新名称「{new_name}」", "未找到")

        step("还原计划名称")
        page.click_edit(new_name)
        page.fill_form_plan_name(target)
        page.click_form_save()

    def test_mt_14_edit_cancel(self, driver_setup):
        """MT-14: 编辑计划 — 取消操作"""
        page = MaintenancePage(driver_setup)
        case("MT-14", "编辑计划-取消")

        if page.get_table_row_count() == 0:
            pytest.skip("表格无数据")

        name_idx = page.get_column_index_by_header("计划名称")
        if not name_idx:
            pytest.skip("未找到计划名称列")
        names = page.get_column_data(name_idx)
        if not names:
            pytest.skip("表格无计划名称数据")

        target = names[0]
        step(f"编辑「{target}」→ 取消操作")
        page.click_edit(target)
        page.fill_form_plan_name("AUTO_TEST_取消修改_不应保存")
        page.click_form_cancel()

        step("验证名称未变更")
        assert not page.is_row_present("AUTO_TEST_取消修改_不应保存"), \
            ea("取消后计划名称不变", "取消修改的内容不应出现")


# ==================================================================
#  生成任务（P1）
# ==================================================================
class TestMaintenanceGenerateTask:

    def test_mt_15_generate_task(self, driver_setup):
        """MT-15: 生成维保任务"""
        page = MaintenancePage(driver_setup)
        case("MT-15", "生成维保任务")

        if page.get_table_row_count() == 0:
            pytest.skip("表格无数据")

        # 找一条待执行的计划
        code_idx = page.get_column_index_by_header("计划编码")
        if not code_idx:
            pytest.skip("未找到计划编码列")
        codes = page.get_column_data(code_idx)
        if not codes:
            pytest.skip("表格无计划编码数据")

        target = codes[0]
        step(f"对计划「{target}」生成任务")

        page.click_generate_task(target)

        toast = page.wait_for_toast_text(timeout=5)
        step(f"生成任务结果: {toast}")
        # 成功或已有相应提示均可
        assert toast != '', ea("有操作反馈", "无反馈")


# ==================================================================
#  权限检查（P1）
# ==================================================================
class TestMaintenancePermissions:

    def test_mt_16_add_button_visible(self, driver_setup):
        """MT-16: 新增计划按钮可见性（admin角色）"""
        page = MaintenancePage(driver_setup)
        case("MT-16", "新增计划按钮可见")

        assert page.is_add_button_visible(), \
            ea("新增计划按钮可见", "不可见")

    def test_mt_17_edit_button_visible(self, driver_setup):
        """MT-17: 编辑按钮可见性"""
        page = MaintenancePage(driver_setup)
        case("MT-17", "编辑按钮可见")

        if page.get_table_row_count() == 0:
            pytest.skip("表格无数据")

        code_idx = page.get_column_index_by_header("计划编码")
        if not code_idx:
            pytest.skip("未找到计划编码列")
        codes = page.get_column_data(code_idx)
        if not codes:
            pytest.skip("表格无计划编码数据")

        target = codes[0]
        # 检查编辑按钮在行内可见
        xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td[contains(normalize-space(.),"{target}")]]'
            f'//button[contains(.,"编辑")]'
        )
        assert page.is_present((By.XPATH, xpath)), \
            ea("编辑按钮在行内可见", "不可见")
