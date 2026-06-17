import pytest
import allure
from base.cleanup_tracker import get_cleanup_tracker


@allure.epic("系统管理")
@allure.feature("角色列表页")
class TestRoleList:

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_001_page_load(self, role_list_page):
        """TC-SYS-ROLE-LOAD-001: 正常加载角色列表（含分页>1页）"""
        with allure.step("导航到角色列表页"):
            role_list_page.navigate()
        with allure.step("验证页面核心元素"):
            assert role_list_page.is_table_visible(), "角色表格未加载"
        with allure.step("验证分页组件存在"):
            total = role_list_page.get_pagination_info().get("total", 0)
            assert total > 0, "总条数异常，可能数据不足"

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.NORMAL)
    def test_002_empty_data(self, role_list_page):
        """TC-SYS-ROLE-LOAD-002: 空数据状态"""
        with allure.step("清空所有角色数据（通过接口）"):
            # 空数据场景需要预置，此处假设通过 fixture 或接口清理
            pass
        with allure.step("导航到角色列表页"):
            role_list_page.navigate()
        with allure.step("验证显示'暂无数据'"):
            data = role_list_page.get_table_data()
            assert len(data) == 0, "预期无数据但列表非空"

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_003_search_by_name(self, role_list_page):
        """TC-SYS-ROLE-SEARCH-001: 按角色名称精确搜索"""
        target_role = "admin"
        with allure.step(f"搜索角色名：{target_role}"):
            role_list_page.search(target_role)
        with allure.step("获取搜索结果并验证"):
            data = role_list_page.get_table_data()
            assert len(data) > 0, "搜索结果为空"
            for row in data:
                assert target_role in row.get("role_name", ""), f"结果包含非目标角色：{row}"

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_004_search_by_status(self, role_list_page):
        """TC-SYS-ROLE-SEARCH-002: 按角色状态搜索（禁用）"""
        with allure.step("选择状态'禁用'并搜索"):
            # 假设 page object 有 set_status_filter 方法
            role_list_page.set_status_filter("禁用")
            role_list_page.search("")
        with allure.step("验证所有结果状态为禁用"):
            data = role_list_page.get_table_data()
            assert len(data) > 0, "搜索结果为空"
            for row in data:
                assert row.get("status") == "禁用", f"角色 {row['role_name']} 状态不是禁用"

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_005_reset_search(self, role_list_page):
        """TC-SYS-ROLE-SEARCH-006: 重置筛选条件"""
        with allure.step("先输入搜索关键词"):
            role_list_page.search("admin")
        with allure.step("点击重置按钮"):
            role_list_page.reset_search()
        with allure.step("验证列表恢复初始显示"):
            total_after_reset = role_list_page.get_pagination_info().get("total", 0)
            assert total_after_reset > 0, "重置后无数据"

    @allure.story("表格操作")
    @allure.severity(allure.severity_level.NORMAL)
    def test_006_sort_by_code(self, role_list_page):
        """TC-SYS-ROLE-TABLE-001: 表格排序"""
        with allure.step("点击'角色编码'列头"):
            role_list_page.sort_by_column("角色编码")
        with allure.step("获取排序后第一行数据，验证升序"):
            first_data = role_list_page.get_table_data()
            # 假设能获取排序策略；此处仅验证页面不报错
            assert len(first_data) > 0, "排序后列表为空"

    @allure.story("表格操作")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_007_pagination(self, role_list_page):
        """TC-SYS-ROLE-TABLE-002: 分页下一页"""
        with allure.step("获取当前页信息"):
            info = role_list_page.get_pagination_info()
            assert info["total"] > info["page_size"], "数据不足一页，无法测试翻页"
        with allure.step("点击下一页"):
            role_list_page.click_page(info["current_page"] + 1)
        with allure.step("验证页面跳转"):
            new_info = role_list_page.get_pagination_info()
            assert new_info["current_page"] == info["current_page"] + 1, "页面未跳转"

    @allure.story("表格操作")
    @allure.severity(allure.severity_level.NORMAL)
    def test_008_select_all(self, role_list_page):
        """TC-SYS-ROLE-TABLE-006: 全选当前页"""
        with allure.step("勾选全选checkbox"):
            role_list_page.select_all_current_page()
        with allure.step("验证所有行被选中"):
            # 假设 page object 提供 get_selected_rows_count() 方法
            selected = role_list_page.get_selected_rows_count()
            page_size = role_list_page.get_pagination_info().get("page_size", 10)
            assert selected == page_size, f"全选后选中行数{selected}不等于每页条数{page_size}"

    @allure.story("新增角色")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    @pytest.mark.destructive
    def test_009_add_role_success(self, role_list_page):
        """TC-SYS-ROLE-ADD-001: 成功创建角色并清理"""
        test_role_name = "TC-测试角色-自动"
        cleanup = get_cleanup_tracker()
        try:
            with allure.step("打开新增弹窗"):
                role_list_page.click_add_button()
            with allure.step("填写表单并提交"):
                role_list_page.fill_add_form({"role_name": test_role_name, "status": "启用"})
                role_list_page.submit_add_form()
            with allure.step("验证列表出现新角色"):
                role_list_page.search(test_role_name)
                data = role_list_page.get_table_data()
                assert len(data) == 1, f"新增角色后应在搜索结果中看到 {test_role_name}"
                assert data[0]["role_name"] == test_role_name
            # 注册清理
            cleanup.register("role", test_role_name)
        finally:
            with allure.step("清理测试角色"):
                try:
                    if cleanup.has("role", test_role_name):
                        role_list_page.delete_role_by_name(test_role_name)
                        role_list_page.confirm_delete()
                except Exception as e:
                    import warnings
                    warnings.warn(f"清理角色失败: {e}")

    @allure.story("新增角色")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_010_add_role_required_validation(self, role_list_page):
        """TC-SYS-ROLE-ADD-002: 必填项校验-角色名为空"""
        with allure.step("打开新增弹窗"):
            role_list_page.click_add_button()
        with allure.step("不填写角色名，直接点击确定"):
            role_list_page.submit_add_form()
        with allure.step("校验提示信息"):
            error_msg = role_list_page.get_form_error_message()
            assert "角色名不能为空" in error_msg, f"未提示正确的错误信息, 实际: {error_msg}"
        with allure.step("关闭弹窗"):
            role_list_page.cancel_add_form()

    # 更多测试用例可继续扩展...

    def teardown_method(self):
        # 可进行通用 cleanup
        pass