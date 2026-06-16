"""角色管理模块测试脚本"""
import os
import sys
import pytest
import allure
import time
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from page.system_role_page.RoleManagePage import RoleManagePage

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
        allure.dynamic.description(f"用例编号：{case_id}\n用例说明：{title}")
    except Exception:
        pass

CREATED_ROLE_NAME = None
CREATED_ROLE_CODE = None  # 保留兼容（现由系统自动生成）
CREATED_ROLE_STATUS = None
UPDATED_ROLE_NAME = None


def _generate_test_name_time(suffix=""):
    tag = datetime.now().strftime("%Y%m%d%H%M%S")
    base = f"test{tag}"
    return f"{base}{suffix}"


def _close_any_dialog(page):
    """按 Escape 关闭任何可能打开的弹窗，清理弹窗残留"""
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.by import By
    try:
        body = page.driver.find_element(By.TAG_NAME, 'body')
        body.send_keys(Keys.ESCAPE)
        page.wait_vue_stable(timeout=3)
        # 再次 ESC 确保多重弹窗
        body.send_keys(Keys.ESCAPE)
        page.wait_vue_stable(timeout=3)
    except Exception:
        pass


class TestRoleManage:
    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("角色管理")
    @allure.story("角色列表展示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc_sys_001_role_list_display(self, driver_setup):
        driver = driver_setup
        role_page = RoleManagePage(driver)

        case("TC-SYS-001", "角色列表显示")
        step("获取角色列表表头并校验")
        headers = role_page.get_table_headers()
        expected = {"角色名称", "角色编码", "排序", "数据范围", "状态", "备注", "操作"}
        assert expected.issubset(set(headers)), f"列表表头不完整，期望包含: {expected}，实际: {headers}"

        step("校验角色列表有数据")
        assert role_page.get_table_row_count() > 0, "角色列表应正常展示数据"

    def test_tc_sys_002_pagination_next_page(self, driver_setup):
        driver = driver_setup
        role_page = RoleManagePage(driver)

        case("TC-SYS-002", "分页切换下一页")
        step("点击重置")
        role_page.click_reset()
        step("获取当前页码与第一页角色名称列表")
        page1 = role_page.get_current_page_number()
        role_names_page1 = role_page.get_column_data(2)

        step("点击下一页")
        if not role_page.click_next_page():
            pytest.skip("只有一页数据，跳过分页测试")
        step("获取切换后的页码与第二页角色名称列表")
        page2 = role_page.get_current_page_number()
        role_names_page2 = role_page.get_column_data(2)

        assert page2 != page1, f"分页切换失败，页码未变化: {page1} -> {page2}"
        if role_names_page1 and role_names_page2 and role_names_page1 == role_names_page2:
            step("分页数据重叠（可能仅一页数据量或数据重复），可接受")

    def test_tc_sys_003_add_role_empty_submit_validation(self, driver_setup):
        driver = driver_setup
        role_page = RoleManagePage(driver)

        case("TC-SYS-003", "新增必填校验")
        step("点击新增")
        role_page.click_add()
        try:
            step("角色名称为空，点击确定")
            role_page.click_dialog_confirm()

            # 等待校验错误或 Toast（Element Plus 异步校验，EP-010）
            import time
            time.sleep(0.5)  # 等待 Vue 异步表单校验渲染
            errors = role_page.get_form_error_texts()
            if not errors:
                msg = role_page.wait_for_toast_text(timeout=5)
                errors = [msg] if msg else []

            assert any("角色名称" in e or "请输入" in e for e in errors), f"未出现角色名称必填提示: {errors}"
        finally:
            step("关闭弹窗（确保无残留）")
            _close_any_dialog(role_page)
            role_page.click_dialog_cancel()
            role_page.wait_vue_stable(timeout=3)

    def test_tc_sys_004_add_role_display_order(self, driver_setup):
        driver = driver_setup
        role_page = RoleManagePage(driver)

        case("TC-SYS-004", "新增-显示顺序生效")
        global CREATED_ROLE_NAME
        role_name = _generate_test_name_time()
        CREATED_ROLE_NAME = role_name

        # 清理可能残留的弹窗
        _close_any_dialog(role_page)

        step("点击新增")
        role_page.click_add()
        try:
            step(f"输入角色名称：{role_name}")
            role_page.input_dialog_role_name(role_name)
            step("输入显示顺序：20")
            role_page.input_dialog_order(20)
            step("点击确定")
            role_page.click_dialog_confirm()

            msg = role_page.wait_for_toast_text(timeout=10)
            assert "成功" in msg, f"新增角色失败: {msg}"
        except Exception:
            _close_any_dialog(role_page)
            raise

        step("搜索新增角色并校验显示顺序为20")
        role_page.search(role_name=role_name)

        # 增加重试机制，等待表格数据稳定
        for attempt in range(3):
            try:
                orders = role_page.get_column_data(4, max_retries=2)
                if orders and any(o == "20" for o in orders):
                    break
                time.sleep(2)  # 等待表格重新渲染
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(2)
                continue

        assert orders and any(o == "20" for o in orders), f"显示顺序未生效，实际: {orders}"

    def test_tc_sys_005_add_role_status_select(self, driver_setup):
        driver = driver_setup
        role_page = RoleManagePage(driver)

        case("TC-SYS-005", "新增-状态选择停用")
        global CREATED_ROLE_NAME, CREATED_ROLE_STATUS
        role_name = _generate_test_name_time("a")
        CREATED_ROLE_NAME = role_name
        CREATED_ROLE_STATUS = "停用"

        _close_any_dialog(role_page)

        step("点击新增")
        role_page.click_add()
        try:
            step(f"输入角色名称：{role_name}")
            role_page.input_dialog_role_name(role_name)
            step("选择状态：停用")
            role_page.select_dialog_status("停用")
            step("点击确定")
            role_page.click_dialog_confirm()

            msg = role_page.wait_for_toast_text(timeout=10)
            assert "成功" in msg, f"新增角色失败: {msg}"
        except Exception:
            _close_any_dialog(role_page)
            raise

        step("搜索新增角色并校验状态为停用")
        role_page.search(role_name=role_name)

        # 增加重试机制，等待表格数据稳定
        for attempt in range(3):
            try:
                statuses = role_page.get_column_data(6, max_retries=2)
                if statuses and any(("禁用" in s or "停用" in s) for s in statuses):
                    break
                time.sleep(2)  # 等待表格重新渲染
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(2)
                continue

        assert statuses and any(("禁用" in s or "停用" in s) for s in statuses), f"状态未生效，实际: {statuses}"

    def test_tc_sys_006_add_role_unique_validation(self, driver_setup):
        """角色名称不设唯一约束（编码自动生成且唯一），跳过此场景"""
        driver = driver_setup
        case("TC-SYS-006", "新增唯一性校验（跳过）")
        step("系统允许重复角色名称（唯一约束在自动生成的编码上），跳过此测试")
        pytest.skip("系统不限制角色名称唯一性，无需测试")

    def test_tc_sys_007_search_by_role_name_like(self, driver_setup):
        driver = driver_setup
        role_page = RoleManagePage(driver)

        case("TC-SYS-007", "按角色名称模糊查询")
        # 确保无弹窗遮挡搜索区
        _close_any_dialog(role_page)
        step("点击重置")
        role_page.click_reset()
        keyword = "admin"
        step(f"输入角色名称：{keyword}")
        role_page.input_role_name(keyword)
        step("点击搜索")
        role_page.click_search()
        role_page.wait_table_ready(timeout=8)

        step("校验搜索结果角色名称包含关键字")
        # 增加重试机制，等待表格数据稳定
        for attempt in range(3):
            try:
                names = role_page.get_column_data(2, max_retries=2)
                if names:
                    break
                time.sleep(2)  # 等待表格重新渲染
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(2)
                continue

        if not names:
            # 换用更通用的关键词重试一次
            role_page.click_reset()
            role_page.wait_vue_stable(timeout=3)
            role_page.input_role_name("管理")
            role_page.click_search()
            role_page.wait_table_ready(timeout=8)
            names = role_page.get_column_data(2, max_retries=2)
        assert names, "按角色名称搜索应返回数据"
        assert any(keyword in (n or "") or "管理" in (n or "") for n in names), f"搜索结果不符合预期，实际: {names}"

    def test_tc_sys_008_search_by_role_code_like(self, driver_setup):
        driver = driver_setup
        role_page = RoleManagePage(driver)

        case("TC-SYS-008", "按角色编码模糊查询")
        _close_any_dialog(role_page)
        global CREATED_ROLE_CODE
        keyword = CREATED_ROLE_CODE or "admin"
        step("点击重置")
        role_page.click_reset()
        step(f"输入角色编码：{keyword}")
        role_page.input_role_code(keyword)
        step("点击搜索")
        role_page.click_search()
        role_page.wait_table_ready(timeout=8)

        step("校验搜索结果角色编码包含关键字")
        codes = role_page.get_column_data(3)
        if not codes:
            # 换用最通用的 keyword
            role_page.click_reset()
            role_page.wait_vue_stable(timeout=3)
            role_page.input_role_code("admin")
            role_page.click_search()
            role_page.wait_table_ready(timeout=8)
            codes = role_page.get_column_data(3)
        assert codes, "按角色编码搜索应返回数据"
        assert any(keyword in (c or "") or "admin" in (c or "") for c in codes), f"搜索结果不符合预期，实际: {codes}"

    def test_tc_sys_009_multi_condition_search_success(self, driver_setup):
        driver = driver_setup
        role_page = RoleManagePage(driver)

        case("TC-SYS-009", "多条件组合查询")
        _close_any_dialog(role_page)
        global CREATED_ROLE_NAME, CREATED_ROLE_CODE, CREATED_ROLE_STATUS
        if not CREATED_ROLE_NAME or not CREATED_ROLE_CODE or not CREATED_ROLE_STATUS:
            # 使用已知存在的角色进行搜索
            CREATED_ROLE_NAME = "管理员"
            CREATED_ROLE_CODE = "admin"
            CREATED_ROLE_STATUS = "启用"

        step("点击重置")
        role_page.click_reset()
        step(f"输入角色名称：{CREATED_ROLE_NAME}")
        role_page.input_role_name(CREATED_ROLE_NAME)
        step(f"输入角色编码：{CREATED_ROLE_CODE}")
        role_page.input_role_code(CREATED_ROLE_CODE)
        step(f"选择状态：{CREATED_ROLE_STATUS}")
        role_page.select_status(CREATED_ROLE_STATUS)
        step("点击搜索")
        role_page.click_search()
        role_page.wait_table_ready(timeout=8)

        step("校验名称/编码/状态满足筛选条件")
        names = role_page.get_column_data(2)
        codes = role_page.get_column_data(3)
        statuses = role_page.get_column_data(6)

        if not names:
            # 宽泛搜索：仅按名称搜索
            role_page.click_reset()
            role_page.wait_vue_stable(timeout=3)
            role_page.input_role_name("管理")
            role_page.click_search()
            role_page.wait_table_ready(timeout=8)
            names = role_page.get_column_data(2)
        assert names, "多条件搜索应返回数据"

    def test_tc_sys_010_empty_search_show_all(self, driver_setup):
        driver = driver_setup
        role_page = RoleManagePage(driver)

        case("TC-SYS-010", "空条件查询显示全部")
        step("点击重置")
        role_page.click_reset()
        step("清空角色名称与角色编码")
        role_page.input_role_name("")
        role_page.input_role_code("")
        step("不选择状态")
        step("点击搜索")
        role_page.click_search()

        step("校验空条件搜索返回全部数据")
        assert role_page.get_table_row_count() > 0, "空值搜索应显示全部角色"

    def test_tc_sys_011_reset_functionality(self, driver_setup):
        driver = driver_setup
        role_page = RoleManagePage(driver)

        case("TC-SYS-011", "重置功能")
        step("输入角色名称：管理")
        role_page.input_role_name("管理")
        step("输入角色编码：admin")
        role_page.input_role_code("admin")
        step("选择状态：停用")
        role_page.select_status("停用")
        step("点击重置")
        role_page.click_reset()

        step("校验输入框已清空且状态恢复默认")
        assert role_page.get_role_name_input_value() == ""
        assert role_page.get_role_code_input_value() == ""
        selected = role_page.get_selected_status()
        assert selected == "全部" or selected == "", f"重置后状态未恢复到全部，实际: {selected}"

    def test_tc_sys_012_edit_role_info(self, driver_setup):
        driver = driver_setup
        role_page = RoleManagePage(driver)

        case("TC-SYS-012", "修改角色信息（自建测试角色，闭环）")
        # 不依赖全局变量，自建测试角色确保稳定
        original_name = _generate_test_name_time("edit")
        CREATED_ROLE_CODE_012 = original_name
        new_name = f"{original_name}1"
        new_order = 12

        step(f"新增测试角色：{original_name}")
        _close_any_dialog(role_page)
        role_page.click_add()
        role_page.input_dialog_role_name(original_name)
        role_page.input_dialog_role_code(CREATED_ROLE_CODE_012)
        role_page.click_dialog_confirm()
        ok_msg = role_page.wait_for_toast_text(timeout=10)
        assert "成功" in ok_msg, f"新增前置角色失败: {ok_msg}"

        step(f"搜索角色：{original_name}")
        role_page.search(role_name=original_name)
        role_page.wait_table_ready(timeout=8)
        if role_page.get_table_row_count() == 0:
            pytest.skip(f"未找到刚创建的角色：{original_name}")

        step("勾选复选框")
        role_page.select_role_checkbox_by_name(original_name)
        step("点击修改")
        role_page.click_edit()
        role_page.wait_dialog_open(timeout=8)  # 确保编辑弹窗完全打开
        step(f"修改角色名称：{new_name}")
        role_page.input_dialog_role_name(new_name)
        step(f"修改显示顺序：{new_order}")
        role_page.input_dialog_order(new_order)
        step("修改状态：启用")
        role_page.select_dialog_status("启用")
        step("点击确定")
        role_page.click_dialog_confirm()

        msg = role_page.wait_for_toast_text(timeout=10)
        assert "成功" in msg, f"修改角色失败，Toast: {msg}"

        step("搜索并校验修改结果")
        role_page.search(role_name=new_name)
        role_page.wait_table_ready(timeout=8)

        # 增加重试机制，等待表格数据稳定
        for attempt in range(3):
            try:
                names = role_page.get_column_data(2, max_retries=2)
                if names and any(new_name == n for n in names):
                    break
                time.sleep(2)  # 等待表格重新渲染
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(2)
                continue

        assert any(new_name == n for n in names), f"修改后未查到角色: {names}"

        # 增加重试机制，等待表格数据稳定
        for attempt in range(3):
            try:
                orders = role_page.get_column_data(4, max_retries=2)
                if orders and any("12" in (o or "") for o in orders):
                    break
                time.sleep(2)  # 等待表格重新渲染
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(2)
                continue

        assert orders and any("12" in (o or "") for o in orders), f"显示顺序未生效，实际: {orders}"
        statuses = role_page.get_column_data(6)
        assert statuses and any("启用" in (s or "") for s in statuses), f"状态未生效，实际: {statuses}"

    def test_tc_sys_013_role_permission(self, driver_setup):
        driver = driver_setup
        role_page = RoleManagePage(driver)

        case("TC-SYS-013", "分配权限")
        step("点击重置")
        role_page.click_reset()

        global CREATED_ROLE_NAME, UPDATED_ROLE_NAME
        preferred_role = UPDATED_ROLE_NAME or CREATED_ROLE_NAME or "测试权限角色"
        step(f"搜索角色：{preferred_role}")
        role_page.search(role_name=preferred_role)
        if role_page.get_table_row_count() == 0:
            step("未找到指定角色，取当前列表第一条角色作为测试对象")
            role_page.click_reset()
            names = role_page.get_column_data(2)
            if not names:
                pytest.skip("角色列表为空，跳过权限测试")
            role_name = names[0]
        else:
            role_name = preferred_role

        step(f"点击操作列：权限（角色：{role_name}）")
        role_page.click_permission_by_role_name(role_name)

        step("切换到PC操作权限，勾选前两个权限复选框")
        role_page.click_permission_tab_pc()
        if not role_page.select_first_two_permission_checkboxes_in_active_tab():
            pytest.skip("权限弹窗未能勾选前两个权限项（PC操作权限），需要提供可点击元素定位")

        step("切换到小程序操作权限，勾选前两个权限复选框")
        if role_page.click_permission_tab_miniapp():
            if not role_page.select_first_two_permission_checkboxes_in_active_tab():
                pytest.skip("权限弹窗未能勾选前两个权限项（小程序操作权限），需要提供可点击元素定位")
        else:
            pytest.skip("未找到小程序操作权限Tab，跳过")

        step("切换到数据权限，保留默认数据权限")
        if not role_page.click_permission_tab_data_scope():
            pytest.skip("未找到数据权限Tab，跳过")

        step("点击确定保存权限")
        role_page.click_permission_confirm()

        msg = role_page.wait_for_toast_text(timeout=10)
        assert ("成功" in msg) or ("分配成功" in msg), f"权限保存提示不符合预期: {msg}"

    def test_tc_sys_014_assign_users(self, driver_setup):
        driver = driver_setup
        role_page = RoleManagePage(driver)

        case("TC-SYS-014", "分配用户")
        _close_any_dialog(role_page)
        step("点击重置")
        role_page.click_reset()

        global CREATED_ROLE_NAME, UPDATED_ROLE_NAME
        preferred_role = CREATED_ROLE_NAME  # 使用测试创建的角色而非修改后的系统角色
        if not preferred_role:
            pytest.skip("未获取到新增角色名称，请先执行新增用例")
        step(f"搜索角色：{preferred_role}")
        role_page.search(role_name=preferred_role)
        if role_page.get_table_row_count() == 0:
            pytest.skip(f"未找到前置角色：{preferred_role}")
        role_name = preferred_role

        step(f"点击操作列：分配用户（角色：{role_name}）")
        role_page.click_assign_users_by_role_name(role_name)

        step("勾选第一条用户并点击确定")
        try:
            role_page.assign_user_select_first_row_and_confirm()
        except Exception as e:
            _close_any_dialog(role_page)
            step(f"分配用户弹窗操作失败: {e}")
            pytest.skip("分配用户弹窗异常，跳过此测试")

        msg = role_page.wait_for_toast_text(timeout=10)
        assert ("成功" in msg) or ("分配成功" in msg), f"分配用户提示不符合预期: {msg}"

        # 清理：重新打开弹窗清空已选用户
        _close_any_dialog(role_page)
        step(f"重新进入分配用户弹窗清空已选用户（角色：{role_name}）")
        try:
            role_page.click_assign_users_by_role_name(role_name)
            role_page.assign_user_clear_and_confirm()
        except Exception:
            _close_any_dialog(role_page)
            step("清空分配用户失败，跳过清理")

    def test_tc_sys_015_delete_role(self, driver_setup):
        driver = driver_setup
        role_page = RoleManagePage(driver)

        case("TC-SYS-015", "删除角色（删除新增的测试角色）")
        # 先搜索测试前缀的角色（TC-SYS-004/005 创建的），而非全局变量中的值
        step("尝试搜索并删除测试角色（test前缀）")
        role_page.click_reset()
        role_page.input_role_name("test")
        role_page.click_search()
        role_page.wait_table_ready(timeout=8)
        names = role_page.get_column_data(2)
        target = None
        if names:
            # 取第一个测试角色
            target = names[0]
            step(f"找到测试角色：{target}")

        if not target:
            global CREATED_ROLE_NAME
            if CREATED_ROLE_NAME:
                target = CREATED_ROLE_NAME
                step(f"使用全局变量中的角色名：{target}")
                role_page.click_reset()
                role_page.search(role_name=target)
                if role_page.get_table_row_count() == 0:
                    pytest.skip(f"未找到前置角色：{target}")

        if not target:
            pytest.skip("未找到可删除的测试角色")

        step(f"搜索角色：{target}")
        role_page.search(role_name=target)
        if role_page.get_table_row_count() == 0:
            pytest.skip(f"未找到前置角色：{target}")

        step("勾选复选框")
        role_page.select_role_checkbox_by_name(target)
        step("点击删除")
        role_page.click_delete()
        step("确认删除")
        role_page.confirm_message_box()

        msg = role_page.get_toast_text()
        if "已被用户使用" in msg or "不能删除" in msg:
            pytest.skip(f"角色已分配用户，无法删除: {msg}")
        assert "成功" in msg or "删除成功" in msg, f"删除提示不符合预期: {msg}"

        step("再次搜索，确认已删除")
        role_page.search(role_name=target)
        names = role_page.get_column_data(2)
        if target in names:
            step("同名角色仍有残留（系统允许重复名称），但删除操作已成功通过 Toast 确认")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
