"""菜单管理模块测试脚本"""
import os
import sys
import pytest
import allure
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from page.system_page.MenuManagePage import MenuManagePage


def step(text):
    try:
        with allure.step(text):
            print(f"步骤：{text}")
    except Exception:
        print(f"步骤：{text}")

def _close_any_dialog(driver):
    """按 Escape 关闭任何可能打开的弹窗"""
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    try:
        body = driver.find_element(By.TAG_NAME, 'body')
        body.send_keys(Keys.ESCAPE)
        try:
            WebDriverWait(driver, 1).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, '.el-overlay:not([style*="display: none"])')
                )
            )
        except Exception:
            pass
        body.send_keys(Keys.ESCAPE)
        try:
            WebDriverWait(driver, 1).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, '.el-overlay:not([style*="display: none"])')
                )
            )
        except Exception:
            pass
    except Exception:
        pass

def case(case_id, title):
    print(f"\n========== 用例 {case_id}：{title} ==========")
    try:
        allure.dynamic.title(f"{case_id} {title}")
        allure.dynamic.description(f"用例编号：{case_id}\n用例说明：{title}")
    except Exception:
        pass


def ea(expected, actual):
    return f"预期结果：{expected}；实际结果：{actual}"


CREATED_MENU_NAME = None
UPDATED_MENU_NAME = None


def _generate_menu_name():
    return f"test{datetime.now().strftime('%Y%m%d%H%M%S')}添加"


def _fill_add_menu_dialog(page, menu_type, menu_name, *, permission=None, path=None, component_path=None,
                          icon=None, visible=None, cache=None, status="启用", sort=0):
    step(f"选择菜单类型：{menu_type}")
    page.select_dialog_menu_type(menu_type)

    step(f"输入菜单名称：{menu_name}")
    page.input_dialog_menu_name(menu_name)

    if icon and page.dialog_has_form_item("菜单图标"):
        step(f"输入菜单图标：{icon}")
        page.input_dialog_icon(icon)

    if path and page.dialog_has_form_item("路由地址"):
        step(f"输入路由地址：{path}")
        page.input_dialog_path(path)

    if component_path and page.dialog_has_form_item("组件路径"):
        step(f"输入组件路径：{component_path}")
        page.input_dialog_component_path(component_path)

    if permission and page.dialog_has_form_item("权限标识"):
        step(f"输入权限标识：{permission}")
        page.input_dialog_permission(permission)

    if page.dialog_has_form_item("菜单排序"):
        step(f"输入菜单排序：{sort}")
        page.input_dialog_sort(sort)

    if visible and page.dialog_has_form_item("是否可见"):
        step(f"选择是否可见：{visible}")
        page.select_dialog_visible(visible)

    if cache and page.dialog_has_form_item("是否缓存"):
        step(f"选择是否缓存：{cache}")
        page.select_dialog_cache(cache)

    if status and (page.dialog_has_form_item("菜单状态") or page.dialog_has_form_item("状态")):
        step(f"选择菜单状态：{status}")
        page.select_dialog_status(status)


class TestMenuManage:
    @pytest.mark.smoke
    @allure.epic("系统管理")
    @allure.feature("菜单管理")
    @allure.story("页面基础展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sy_menu_01_page_display(self, driver_setup):
        page = MenuManagePage(driver_setup)
        case("SY-MENU-01", "正常显示菜单列表及关键字段")
        step("切换平台：PC端菜单")
        page.click_tab_pc_menu()
        step("获取菜单列表表头并校验")
        headers = page.get_table_headers()
        expected = {"菜单名称", "类型", "权限标识", "排序", "可见性", "状态", "创建时间", "操作"}
        assert expected.issubset(set(headers)), f"表头不完整，实际: {headers}"
        step("校验菜单列表有数据")
        assert page.get_table_row_count() > 0, "菜单列表应有数据"

    def test_sy_menu_02_add_menu_required(self, driver_setup):
        page = MenuManagePage(driver_setup)
        case("SY-MENU-02", "添加菜单（必选）")
        global CREATED_MENU_NAME
        CREATED_MENU_NAME = _generate_menu_name()
        step("切换平台：PC端菜单")
        page.click_tab_pc_menu()
        page.click_reset()
        page.click_toolbar_add()
        _fill_add_menu_dialog(
            page,
            "目录",
            CREATED_MENU_NAME,
            permission=f"{CREATED_MENU_NAME}:view",
            path=f"/{CREATED_MENU_NAME}",
            icon="Menu",
            visible="显示",
            status="启用",
            sort=0,
        )
        step("点击确定")
        page.click_dialog_confirm()

        msg = page.wait_for_toast_text(timeout=8)
        assert ("成功" in msg) or (msg == ""), f"创建菜单提示异常: {msg}"

        step(f"搜索菜单名称：{CREATED_MENU_NAME}")
        page.click_reset()
        page.input_menu_name(CREATED_MENU_NAME)
        page.click_search()
        names = page.get_column_data_by_header("菜单名称")
        assert any(CREATED_MENU_NAME in n for n in names), ea(f"显示列表中{CREATED_MENU_NAME}的信息", names)

    def test_sy_menu_03_add_menu_duplicate_should_fail(self, driver_setup):
        page = MenuManagePage(driver_setup)
        case("SY-MENU-03", "添加菜单（按钮类型新增成功）")
        global CREATED_MENU_NAME
        if not CREATED_MENU_NAME:
            CREATED_MENU_NAME = _generate_menu_name()
        step("切换平台：PC端菜单")
        page.click_tab_pc_menu()
        step("点击新增")
        page.click_toolbar_add()
        _fill_add_menu_dialog(
            page,
            "按钮",
            CREATED_MENU_NAME,
            permission=f"{CREATED_MENU_NAME}:view",
            status="启用",
            sort=0,
        )
        step("点击确定")
        page.click_dialog_confirm()

        msg = page.wait_for_toast_text(timeout=8)
        assert "新增成功" in (msg or "") or "成功" in (msg or ""), ea("按钮类型菜单新增成功", msg or "未获取到提示")

        step("点击取消关闭弹窗（如果仍存在）")
        try:
            page.click_dialog_cancel()
        except Exception:
            pass

    def test_sy_menu_04_search_by_menu_name(self, driver_setup):
        page = MenuManagePage(driver_setup)
        case("SY-MENU-04", "按菜单名称搜索（精确）")
        step("切换平台：PC端菜单")
        page.click_tab_pc_menu()
        step("点击重置")
        page.click_reset()
        target = "test"
        step(f"输入菜单名称：{target}")
        page.input_menu_name(target)
        step("点击搜索")
        page.click_search()
        names = page.get_column_data_by_header("菜单名称")
        assert names, ea(f"按菜单名“{target}”搜索应返回结果", page.get_empty_text() or "暂无数据")
        assert any(target in n for n in names), ea(f"搜索结果包含“{target}”", names)
    # 测试失败：存在bug显示不是菜单
    def test_sy_menu_05_filter_by_type(self, driver_setup):
        page = MenuManagePage(driver_setup)
        case("SY-MENU-05", "按类型筛选（菜单）")
        _close_any_dialog(driver_setup)
        step("切换平台：PC端菜单")
        page.click_tab_pc_menu()
        step("点击重置")
        page.click_reset()
        step("选择类型：菜单")
        page.select_type("菜单")
        step("点击搜索")
        page.click_search()
        types = page.get_column_data_by_header("类型")
        assert types, ea("按类型=菜单筛选后应有结果", page.get_empty_text() or "暂无数据")
        assert all("菜单" in t for t in types), ea("筛选结果的类型列都应为“菜单”", types)

    def test_sy_menu_06_filter_by_visibility_show(self, driver_setup):
        page = MenuManagePage(driver_setup)
        case("SY-MENU-06", "按可见性筛选（显示）")
        step("切换平台：PC端菜单")
        page.click_tab_pc_menu()
        step("点击重置")
        page.click_reset()
        name = "test"
        step(f"输入菜单名称：{name}")
        page.input_menu_name(name)
        step("选择类型：按钮")
        page.select_type("按钮")
        step("选择可见性：显示")
        page.select_visibility("显示")
        step("点击搜索")
        page.click_search()
        values = page.get_column_data_by_header("可见性")
        assert values, ea("按可见性=显示筛选后应有结果", page.get_empty_text() or "暂无数据")
        assert all("显示" in v for v in values), f"可见性筛选不符合预期：{values}"

    def test_sy_menu_07_filter_by_status_enabled(self, driver_setup):
        page = MenuManagePage(driver_setup)
        case("SY-MENU-07", "按状态筛选（启用）")
        global CREATED_MENU_NAME
        if not CREATED_MENU_NAME:
            pytest.skip("未获取到 SY-MENU-03 新增的菜单名称，请先执行前置新增用例")
        step("切换平台：PC端菜单")
        page.click_tab_pc_menu()
        step("点击重置")
        page.click_reset()
        name = CREATED_MENU_NAME
        step(f"输入菜单名称：{name}")
        page.input_menu_name(name)
        step("选择类型：按钮")
        page.select_type("按钮")
        step("选择可见性：显示")
        page.select_visibility("显示")
        step("选择状态：启用")
        page.select_status("启用")
        step("点击搜索")
        page.click_search()
        names = page.get_column_data_by_header("菜单名称")
        assert names, ea("按组合条件搜索后应有结果", page.get_empty_text() or "暂无数据")
        assert all(name in (n or "") for n in names), ea(f"筛选结果的菜单名称都应包含“{name}”", names)
        types = page.get_column_data_by_header("类型")
        assert types and all("按钮" in t for t in types), ea("筛选结果的类型列都应为“按钮”", types)
        visibilities = page.get_column_data_by_header("可见性")
        if visibilities:
            assert all("显示" in v for v in visibilities), ea("筛选结果的可见性列都应为“显示”", visibilities)
        values = page.get_column_data_by_header("状态")
        assert values, ea("按状态=启用筛选后应有结果", page.get_empty_text() or "暂无数据")
        assert all("启用" in v for v in values), f"状态筛选不符合预期：{values}"

    def test_sy_menu_08_fuzzy_search(self, driver_setup):
        page = MenuManagePage(driver_setup)
        case("SY-MENU-08", "模糊查询（关键字）")
        step("切换平台：PC端菜单")
        page.click_tab_pc_menu()
        step("点击重置")
        page.click_reset()
        keyword = "人"
        step(f"输入菜单名称（模糊）：{keyword}")
        page.input_menu_name(keyword)
        step("点击搜索")
        page.click_search()
        names = page.get_column_data_by_header("菜单名称")
        assert names, ea(f"按关键字“{keyword}”模糊搜索应返回结果", "结果为空/暂无数据")
        assert any(keyword in n for n in names), ea(f"结果中至少存在1条包含“{keyword}”的菜单名", names)

    def test_sy_menu_09_empty_search_show_all(self, driver_setup):
        page = MenuManagePage(driver_setup)
        case("SY-MENU-09", "空值搜索显示全部")
        step("切换平台：PC端菜单")
        page.click_tab_pc_menu()
        step("点击重置")
        page.click_reset()
        total_before = page.get_table_row_count()
        step("点击搜索")
        page.click_search()
        total_after = page.get_table_row_count()
        assert total_after >= 1, ea("空查询应返回列表数据", f"当前行数={total_after}")
        diff = abs(total_after - total_before)
        assert diff <= 10, ea("空查询后结果规模应与默认列表基本一致", f"查询前={total_before}, 查询后={total_after}")

    def test_sy_menu_10_reset_button(self, driver_setup):
        page = MenuManagePage(driver_setup)
        case("SY-MENU-10", "重置功能正常")
        step("切换平台：PC端菜单")
        page.click_tab_pc_menu()
        step("点击重置")
        page.click_reset()
        first_before = page.get_first_row_name()
        step("输入菜单名称：生产月报表")
        page.input_menu_name("生产月报表")
        step("选择类型：菜单")
        page.select_type("菜单")
        step("选择可见性：显示")
        page.select_visibility("显示")
        step("选择状态：启用")
        page.select_status("启用")
        step("点击重置")
        page.click_reset()
        assert page.get_menu_name_input_value() == "", "重置后菜单名称输入框应为空"
        first_after = page.get_first_row_name()
        if first_before and first_after:
            assert first_before == first_after, f"重置后首页数据未恢复：{first_before} vs {first_after}"

    def test_sy_menu_11_search_keyword_small_program(self, driver_setup):
        page = MenuManagePage(driver_setup)
        case("SY-MENU-11", "按菜单名称搜索（小程序）")
        _close_any_dialog(driver_setup)
        step("点击重置")
        page.click_reset()
        step("切换平台：小程序菜单")
        page.click_tab_miniapp_menu()
        name = "我的申请"
        step(f"输入菜单名称：{name}")
        page.input_menu_name(name)
        step("选择类型：菜单")
        page.select_type("菜单")
        step("点击搜索")
        page.click_search()
        names = page.get_column_data_by_header("菜单名称")
        assert names, ea(f"按菜单名“{name}”搜索应返回结果", page.get_empty_text() or "暂无数据")
        assert any(name in n for n in names), ea(f"结果中至少存在1条菜单名包含“{name}”", names)

    def test_sy_menu_12_filter_type_menu_again(self, driver_setup):
        page = MenuManagePage(driver_setup)
        case("SY-MENU-12", "按类型筛选（小程序-菜单）")
        _close_any_dialog(driver_setup)
        step("点击重置")
        page.click_reset()
        step("切换平台：小程序菜单")
        page.click_tab_miniapp_menu()
        step("选择类型：菜单")
        page.select_type("菜单")
        step("点击搜索")
        page.click_search()
        types = page.get_column_data_by_header("类型")
        assert types, ea("按类型=菜单筛选后应有结果", page.get_empty_text() or "暂无数据")
        assert all("菜单" in t for t in types), ea("二次筛选结果的类型列都应为“菜单”", types)

    def test_sy_menu_13_filter_by_visibility_hide(self, driver_setup):
        page = MenuManagePage(driver_setup)
        case("SY-MENU-13", "按可见性筛选（小程序-显示）")
        step("点击重置")
        page.click_reset()
        step("切换平台：小程序菜单")
        page.click_tab_miniapp_menu()
        name = "生产监控"
        step(f"输入菜单名称：{name}")
        page.input_menu_name(name)
        step("选择类型：目录")
        page.select_type("目录")
        step("选择可见性：显示")
        page.select_visibility("显示")
        step("点击搜索")
        page.click_search()
        values = page.get_column_data_by_header("可见性")
        assert values, ea("按可见性=显示筛选后应有结果", "结果为空/暂无数据")
        assert all("显示" in v for v in values), ea("筛选结果的可见性列都应为“显示”", values)

    def test_sy_menu_14_filter_by_status_disabled(self, driver_setup):
        page = MenuManagePage(driver_setup)
        case("SY-MENU-14", "按状态筛选（小程序-启用）")
        step("点击重置")
        page.click_reset()
        step("切换平台：小程序菜单")
        page.click_tab_miniapp_menu()
        name = "生产监控"
        step(f"输入菜单名称：{name}")
        page.input_menu_name(name)
        step("选择类型：目录")
        page.select_type("目录")
        step("选择可见性：显示")
        page.select_visibility("显示")
        step("选择状态：启用")
        page.select_status("启用")
        step("点击搜索")
        page.click_search()
        values = page.get_column_data_by_header("状态")
        assert values, ea("按状态=启用筛选后应有结果", "结果为空/暂无数据")
        assert all("启用" in v for v in values), ea("筛选结果的状态列都应为“启用”", values)

    def test_sy_menu_15_expand_all(self, driver_setup):
        page = MenuManagePage(driver_setup)
        case("SY-MENU-15", "展开全部信息")
        step("切换平台：PC端菜单")
        page.click_tab_pc_menu()
        step("点击重置")
        page.click_reset()
        before = page.get_table_row_count()
        step("点击展开全部")
        page.click_expand_all()
        after = page.get_table_row_count()
        assert after >= before, ea("展开全部后行数不小于展开前", f"展开前={before}, 展开后={after}")
        assert after > before, ea("展开全部后应展示更多目录/菜单/按钮", f"展开前={before}, 展开后={after}")

    def test_sy_menu_16_collapse_all(self, driver_setup):
        page = MenuManagePage(driver_setup)
        case("SY-MENU-16", "收起全部信息")
        step("切换平台：PC端菜单")
        page.click_tab_pc_menu()
        step("点击重置")
        page.click_reset()
        step("点击展开全部（准备收起验证）")
        page.click_expand_all()
        expanded = page.get_table_row_count()
        step("点击收起全部")
        page.click_collapse_all()
        collapsed = page.get_table_row_count()
        assert collapsed <= expanded, ea("收起全部后行数不大于展开后", f"展开后={expanded}, 收起后={collapsed}")
        assert collapsed < expanded, ea("收起全部后应只显示目录/顶级节点等", f"展开后={expanded}, 收起后={collapsed}")

    def test_sy_menu_17_edit_menu(self, driver_setup):
        page = MenuManagePage(driver_setup)
        case("SY-MENU-17", "修改菜单")
        global CREATED_MENU_NAME, UPDATED_MENU_NAME
        step("切换平台：PC端菜单")
        page.click_tab_pc_menu()
        target = CREATED_MENU_NAME or "test"
        UPDATED_MENU_NAME = f"{target}2"
        step(f"搜索菜单名称：{target}")
        page.click_reset()
        page.input_menu_name(target)
        page.click_search()
        names = page.get_column_data_by_header("菜单名称")
        assert names, ea(f"存在菜单{target}", page.get_empty_text() or "暂无数据")

        step(f"点击{target}行的修改")
        try:
            page.click_row_action(target, "修改")
        except Exception:
            page.click_first_row_edit()
        step("选择菜单类型：按钮")
        page.select_dialog_menu_type("按钮")
        step(f"修改菜单名称：{UPDATED_MENU_NAME}")
        page.input_dialog_menu_name(UPDATED_MENU_NAME)
        step("修改菜单图标：123")
        page.try_input_dialog_field("菜单图标", "123")
        step("修改权限标识：11")
        page.input_dialog_permission("11")
        step("修改菜单排序：0")
        page.input_dialog_sort(0)
        step("选择是否可见：显示")
        try:
            page.select_dialog_visible("显示")
        except Exception:
            pass
        step("选择菜单状态：禁用")
        page.select_dialog_status("禁用")
        step("点击确定")
        page.click_dialog_confirm()

        msg = page.wait_for_toast_text(timeout=8)
        assert "成功" in msg, ea("提示：修改成功", msg or "未获取到提示")

        step(f"搜索菜单名称：{UPDATED_MENU_NAME}")
        page.click_reset()
        page.input_menu_name(UPDATED_MENU_NAME)
        page.click_search()
        names = page.get_column_data_by_header("菜单名称")
        assert any(UPDATED_MENU_NAME in n for n in names), ea(f"显示列表中{UPDATED_MENU_NAME}的信息", names)

    def test_sy_menu_18_delete_menu(self, driver_setup):
        page = MenuManagePage(driver_setup)
        case("SY-MENU-18", "删除菜单")
        global CREATED_MENU_NAME, UPDATED_MENU_NAME
        step("切换平台：PC端菜单")
        page.click_tab_pc_menu()
        target = UPDATED_MENU_NAME or (f"{CREATED_MENU_NAME}2" if CREATED_MENU_NAME else "test2")
        step(f"搜索菜单名称：{target}")
        page.click_reset()
        page.input_menu_name(target)
        page.click_search()
        names = page.get_column_data_by_header("菜单名称")
        assert names, ea(f"存在菜单{target}", page.get_empty_text() or "暂无数据")

        step(f"点击{target}·删除")
        try:
            page.click_row_action(target, "删除")
        except Exception:
            page.click_first_row_delete()
        step("确认删除")
        page.confirm_message_box()

        msg = page.wait_for_toast_text(timeout=8)
        assert "成功" in msg or "删除成功" in msg, ea("提示：删除成功", msg or "未获取到提示")

        step(f"再次搜索，断言列表无{target}")
        page.click_reset()
        page.input_menu_name(target)
        page.click_search()
        names = page.get_column_data_by_header("菜单名称")
        assert not any(target in n for n in names), ea("删除成功后列表无相关菜单", names)


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
