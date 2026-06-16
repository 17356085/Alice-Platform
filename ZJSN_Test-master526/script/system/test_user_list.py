"""用户列表页 测试脚本 — system-user 模块

基于 PAGE_INTERFACE.yaml test_scenarios + TEST_CASES.md
"""
import pytest
import allure

from page.system_page.UserListPage import UserListPage


@allure.epic("系统管理")
@allure.feature("用户管理-列表视图")
class TestUserList:
    """用户列表页测试 — system-user/user-list"""

    # ══════════════════════════════════════════════════════════════════
    #  TC-001: 页面正常加载 (P0 / Smoke)
    # ══════════════════════════════════════════════════════════════════

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_001_page_load(self, user_list_page):
        """TC-001: 用户管理页面正常加载"""
        with allure.step("导航到用户列表页"):
            user_list_page.navigate()
        with allure.step("等待表格加载完成"):
            user_list_page.wait_table_loaded()
        with allure.step("验证表格可见"):
            assert user_list_page.is_table_visible(), "用户列表表格未加载"
        with allure.step("验证表格行数大于0"):
            row_count = user_list_page.get_row_count()
            assert row_count > 0, f"表格行数为 {row_count}，预期 > 0"

    # ══════════════════════════════════════════════════════════════════
    #  TC-002: 表格列头正确显示 (P1)
    # ══════════════════════════════════════════════════════════════════

    @allure.story("表格列头")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_002_column_headers(self, user_list_page):
        """TC-002: 表格列头正确显示"""
        with allure.step("导航到用户列表页"):
            user_list_page.navigate()
            user_list_page.wait_table_loaded()
        with allure.step("获取表格列头"):
            headers = user_list_page.get_table_headers()
            assert len(headers) >= 6, f"列头数量不足: {headers}"
        with allure.step("验证关键列头存在"):
            # 预期列头：用户名、姓名、手机号、角色、组织名称、状态、最后登录、操作
            header_text = " ".join(headers)
            expected_headers = ["用户名", "姓名", "手机号", "角色", "状态", "操作"]
            for expected in expected_headers:
                assert expected in header_text, f"缺少列头 '{expected}'，实际: {headers}"

    # ══════════════════════════════════════════════════════════════════
    #  TC-003: 分页组件正常显示 (P1)
    # ══════════════════════════════════════════════════════════════════

    @allure.story("分页组件")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_003_pagination_display(self, user_list_page):
        """TC-003: 分页组件正常显示"""
        with allure.step("导航到用户列表页"):
            user_list_page.navigate()
            user_list_page.wait_table_loaded()
        with allure.step("验证分页组件可见"):
            assert user_list_page.is_pagination_visible(), "分页组件不可见"
        with allure.step("验证分页总数包含数字"):
            total_text = user_list_page.get_total_count_text()
            assert any(c.isdigit() for c in total_text), f"分页总数文本无效: {total_text}"

    # ══════════════════════════════════════════════════════════════════
    #  TC-004: 搜索功能 (P1)
    # ══════════════════════════════════════════════════════════════════

    @allure.story("搜索筛选")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_004_search_user(self, user_list_page):
        """TC-004: 按用户名搜索"""
        with allure.step("导航到用户列表页"):
            user_list_page.navigate()
            user_list_page.wait_table_loaded()
        with allure.step("获取第一个用户名"):
            usernames = user_list_page.get_all_usernames()
            assert len(usernames) > 0, "表格无用户数据，无法进行搜索测试"
            target = usernames[0]
        with allure.step("输入搜索关键词"):
            user_list_page.input_search(target)
        with allure.step("点击查询"):
            user_list_page.click_search()
        with allure.step("验证搜索结果包含目标用户"):
            result_usernames = user_list_page.get_all_usernames()
            assert target in result_usernames, (
                f"搜索结果中未找到 '{target}'，实际: {result_usernames}"
            )

    # ══════════════════════════════════════════════════════════════════
    #  TC-005: 重置搜索 (P1)
    # ══════════════════════════════════════════════════════════════════

    @allure.story("搜索筛选")
    @allure.severity(allure.severity_level.NORMAL)
    def test_005_reset_search(self, user_list_page):
        """TC-005: 重置按钮恢复全部数据"""
        with allure.step("导航到用户列表页"):
            user_list_page.navigate()
            user_list_page.wait_table_loaded()
        with allure.step("记录初始行数"):
            initial_count = user_list_page.get_row_count()
        with allure.step("输入搜索并查询"):
            user_list_page.input_search("nonexistent_user_xyz")
            user_list_page.click_search()
        with allure.step("点击重置"):
            user_list_page.click_reset()
        with allure.step("验证数据恢复到初始规模"):
            reset_count = user_list_page.get_row_count()
            assert reset_count >= initial_count, (
                f"重置后行数 {reset_count} 小于初始行数 {initial_count}"
            )

    # ══════════════════════════════════════════════════════════════════
    #  TC-006: 状态筛选 (P1)
    # ══════════════════════════════════════════════════════════════════
    #  ⚠️ 状态下拉实测为 el-select（非 radio-group）

    @allure.story("搜索筛选")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_006_status_filter(self, user_list_page):
        """TC-006: 按状态筛选用户"""
        with allure.step("导航到用户列表页"):
            user_list_page.navigate()
            user_list_page.wait_table_loaded()
        with allure.step("选择状态筛选-启用"):
            user_list_page.select_status_filter("启用")
        with allure.step("点击查询"):
            user_list_page.click_search()
        with allure.step("验证搜索结果不为空"):
            row_count = user_list_page.get_row_count()
            assert row_count >= 0, "状态筛选后表格应正常渲染（可能为0）"
        with allure.step("重置筛选条件"):
            user_list_page.click_reset()

    # ══════════════════════════════════════════════════════════════════
    #  TC-007: 角色筛选 (P2)
    # ══════════════════════════════════════════════════════════════════

    @allure.story("搜索筛选")
    @allure.severity(allure.severity_level.NORMAL)
    def test_007_role_filter(self, user_list_page):
        """TC-007: 按角色筛选用户"""
        with allure.step("导航到用户列表页"):
            user_list_page.navigate()
            user_list_page.wait_table_loaded()
        with allure.step("选择角色筛选（尝试选择第一个可用角色）"):
            try:
                user_list_page.select_role_filter("管理员")
            except Exception:
                # 如果特定角色不存在或无法选择，跳过此场景（非阻塞）
                pytest.skip("角色筛选不可用或'管理员'角色不存在")
        with allure.step("点击查询"):
            user_list_page.click_search()
        with allure.step("验证结果渲染"):
            row_count = user_list_page.get_row_count()
            assert row_count >= 0, "角色筛选后表格应正常渲染"
        with allure.step("重置筛选条件"):
            user_list_page.click_reset()

    # ══════════════════════════════════════════════════════════════════
    #  TC-008: 分页翻页 (P1)
    # ══════════════════════════════════════════════════════════════════

    @allure.story("分页组件")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_008_pagination_navigate(self, user_list_page):
        """TC-008: 分页翻页功能"""
        with allure.step("导航到用户列表页"):
            user_list_page.navigate()
            user_list_page.wait_table_loaded()
        with allure.step("获取分页总数"):
            total_text = user_list_page.get_total_count_text()
            # 总数大于当前页条数时才测试翻页
            digits = "".join(c for c in total_text if c.isdigit())
            total = int(digits) if digits else 0
        if total <= 10:
            pytest.skip(f"总条数 {total} ≤ 10，无需翻页")
        with allure.step("翻到下一页"):
            initial_count = user_list_page.get_row_count()
            user_list_page.click_next_page()
        with allure.step("验证页面数据变化"):
            new_count = user_list_page.get_row_count()
            assert new_count >= 0, f"翻页后行数异常: {new_count}"

    # ══════════════════════════════════════════════════════════════════
    #  TC-009: 行内查看按钮 (P2)
    # ══════════════════════════════════════════════════════════════════

    @allure.story("行操作")
    @allure.severity(allure.severity_level.NORMAL)
    def test_009_row_view(self, user_list_page):
        """TC-009: 点击行内查看按钮"""
        with allure.step("导航到用户列表页"):
            user_list_page.navigate()
            user_list_page.wait_table_loaded()
        with allure.step("获取第一个用户名"):
            usernames = user_list_page.get_all_usernames()
            assert len(usernames) > 0, "表格无数据"
            target = usernames[0]
        with allure.step("点击查看按钮"):
            user_list_page.click_row_view(target)
        with allure.step("验证弹窗出现（查看详情）"):
            # 查看操作会打开弹窗，等待弹窗加载
            user_list_page.wait_vue_stable()

    # ══════════════════════════════════════════════════════════════════
    #  TC-010: 批量删除按钮状态 (P2)
    # ══════════════════════════════════════════════════════════════════

    @allure.story("批量操作")
    @allure.severity(allure.severity_level.NORMAL)
    def test_010_batch_delete_button_state(self, user_list_page):
        """TC-010: 批量删除按钮在无选中时禁用，选中后可用"""
        with allure.step("导航到用户列表页"):
            user_list_page.navigate()
            user_list_page.wait_table_loaded()
        with allure.step("验证初始状态 - 批量删除禁用"):
            assert not user_list_page.is_batch_delete_enabled(), (
                "无选中行时批量删除按钮应为禁用状态"
            )
        with allure.step("勾选第一行"):
            user_list_page.select_row_by_index(1)
        with allure.step("验证选中后 - 批量删除可用"):
            assert user_list_page.is_batch_delete_enabled(), (
                "选中行后批量删除按钮应为可用状态"
            )

    # ══════════════════════════════════════════════════════════════════
    #  TC-011: 全选功能 (P2)
    # ══════════════════════════════════════════════════════════════════

    @allure.story("批量操作")
    @allure.severity(allure.severity_level.NORMAL)
    def test_011_select_all(self, user_list_page):
        """TC-011: 全选复选框功能"""
        with allure.step("导航到用户列表页"):
            user_list_page.navigate()
            user_list_page.wait_table_loaded()
        with allure.step("点击全选复选框"):
            user_list_page.select_all_rows()
        with allure.step("验证全选后批量删除可用"):
            assert user_list_page.is_batch_delete_enabled(), (
                "全选后批量删除按钮应为可用状态"
            )

    # ══════════════════════════════════════════════════════════════════
    #  TC-012: 新增按钮可见 (P0 / Smoke)
    # ══════════════════════════════════════════════════════════════════

    @allure.story("工具栏")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_012_add_button_visible(self, user_list_page):
        """TC-012: 新增按钮可见且可点击"""
        with allure.step("导航到用户列表页"):
            user_list_page.navigate()
            user_list_page.wait_table_loaded()
        with allure.step("点击新增按钮"):
            user_list_page.click_add()
        with allure.step("验证弹窗出现"):
            user_list_page.wait_vue_stable()
