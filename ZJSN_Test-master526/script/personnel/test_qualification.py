"""
test_personnel_qualification.py

资质管理页面测试脚本
对应模块: personnel (人员管理)
页面类型: 列表页 + 弹窗表单

基于: QualificationManagePage, TEST_CASES.md
"""

import pytest
import allure
import logging

logger = logging.getLogger(__name__)


@allure.epic("人员管理")
@allure.feature("资质管理")
class TestQualificationManage:
    """资质管理页面测试类"""

    # ==================== 页面加载 ====================

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_001_page_load(self, qualification_manage_page):
        """TD-QUAL-001: 正常加载页面"""
        with allure.step("导航到资质管理页面"):
            qualification_manage_page.navigate()
        with allure.step("验证表格可见"):
            assert qualification_manage_page.is_table_visible(), "资质管理表格未加载"
        with allure.step("验证分页组件可见"):
            assert qualification_manage_page.is_pagination_visible(), "分页组件未加载"
        with allure.step("验证搜索区元素"):
            assert qualification_manage_page.is_search_area_visible(), "搜索区元素未加载"

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_002_page_elements_completeness(self, qualification_manage_page):
        """TD-QUAL-004: 页面各区域元素完整性"""
        with allure.step("导航到资质管理页面"):
            qualification_manage_page.navigate()
        with allure.step("验证搜索按钮可见"):
            assert qualification_manage_page.is_element_visible(
                qualification_manage_page.SEARCH_BUTTON
            ), "搜索按钮不可见"
        with allure.step("验证重置按钮可见"):
            assert qualification_manage_page.is_element_visible(
                qualification_manage_page.RESET_BUTTON
            ), "重置按钮不可见"
        with allure.step("验证表格存在"):
            assert qualification_manage_page.is_element_visible(
                qualification_manage_page.TABLE_QUALIFICATION
            ), "资质表格不存在"

    # ==================== 搜索与筛选 ====================

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_003_search_by_name(self, qualification_manage_page, test_qualification_data):
        """TD-QUAL-005: 单条件搜索 - 按资质名称搜索"""
        # 创建测试数据
        test_name = test_qualification_data["name"]
        with allure.step("导航到资质管理页面"):
            qualification_manage_page.navigate()
        with allure.step(f"输入搜索关键词: {test_name}"):
            qualification_manage_page.search(name=test_name)
        with allure.step("验证搜索结果"):
            data = qualification_manage_page.get_table_data()
            # 检查返回数据均包含搜索词
            if data:
                for row in data:
                    # 表格数据字段名称与页面一致，列索引0对应资质名称
                    name_cell = row.get("资质名称") or row.get(0, "")
                    assert test_name in str(name_cell), (
                        f"搜索结果中预期包含关键词 '{test_name}'，实际值: '{name_cell}'"
                    )
            else:
                logger.warning("搜索 '%s' 无返回数据", test_name)

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_004_combined_search(self, qualification_manage_page, test_qualification_data):
        """TD-QUAL-006: 组合搜索 - 名称+类型+状态"""
        test_name = test_qualification_data["name"]
        test_type = test_qualification_data.get("type", "学历证书")
        test_status = test_qualification_data.get("status", "有效")
        with allure.step("导航到资质管理页面"):
            qualification_manage_page.navigate()
        with allure.step(f"组合搜索: name='{test_name}', type='{test_type}', status='{test_status}'"):
            qualification_manage_page.search(name=test_name, q_type=test_type, status=test_status)
        with allure.step("验证搜索结果"):
            data = qualification_manage_page.get_table_data()
            assert len(data) > 0, (
                f"组合搜索 name='{test_name}', type='{test_type}', status='{test_status}' 结果为空"
            )

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_005_reset_search(self, qualification_manage_page):
        """TD-QUAL-007: 重置筛选条件"""
        with allure.step("导航到资质管理页面"):
            qualification_manage_page.navigate()
        with allure.step("输入搜索条件并搜索"):
            initial_data = qualification_manage_page.get_table_data()
            initial_count = len(initial_data)
            # 使用一个不存在的关键词搜索
            qualification_manage_page.search(name="__NON_EXISTENT_KEYWORD__")
        with allure.step("点击重置按钮"):
            qualification_manage_page.reset_search()
        with allure.step("验证表格恢复完整数据"):
            reset_data = qualification_manage_page.get_table_data()
            assert len(reset_data) == initial_count, (
                f"重置后数据条数 {len(reset_data)} 与初始 {initial_count} 不一致"
            )

    # ==================== 表格操作 ====================

    @allure.story("表格操作")
    @allure.severity(allure.severity_level.NORMAL)
    def test_006_pagination(self, qualification_manage_page, test_multiple_qualifications):
        """TD-QUAL-010: 分页操作完整链路"""
        with allure.step("导航到资质管理页面"):
            qualification_manage_page.navigate()
        with allure.step("切换到第2页"):
            qualification_manage_page.go_to_page(2)
        with allure.step("验证当前页码"):
            assert qualification_manage_page.get_current_page() == 2, "未成功切换到第2页"
        with allure.step("切换每页条数为20"):
            qualification_manage_page.set_page_size(20)
        with allure.step("验证每页条数更新"):
            assert qualification_manage_page.get_page_size() == 20, "每页条数未更新为20"

    @allure.story("表格操作")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_007_click_view_button(self, qualification_manage_page, test_qualification_data):
        """TD-QUAL-009: 点击查看详情按钮"""
        with allure.step("导航到资质管理页面"):
            qualification_manage_page.navigate()
        with allure.step("点击第1行的【查看详情】"):
            qualification_manage_page.click_view(0)
        with allure.step("验证查看弹窗打开"):
            assert qualification_manage_page.is_dialog_open(), "查看详情弹窗未打开"
        with allure.step("关闭弹窗"):
            qualification_manage_page.close_dialog()

    # ==================== 新增操作 ====================

    @allure.story("新增资质")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_008_add_qualification_success(self, qualification_manage_page):
        """TD-QUAL-013: 新增成功提交"""
        with allure.step("导航到资质管理页面"):
            qualification_manage_page.navigate()
        with allure.step("点击【新增资质】按钮"):
            qualification_manage_page.click_add()
        with allure.step("填写必填项"):
            qual_name = "TC-自动化测试-安全工程师证书"
            qual_type = "职业资格"
            qual_issuer = "国家应急管理部"
            qualification_manage_page.set_dialog_name(qual_name)
            qualification_manage_page.set_dialog_type(qual_type)
            qualification_manage_page.set_dialog_issuer(qual_issuer)
        with allure.step("点击保存"):
            qualification_manage_page.click_dialog_save()
        with allure.step("验证弹窗关闭"):
            assert not qualification_manage_page.is_dialog_open(), "新增弹窗未关闭"
        with allure.step("验证成功提示"):
            success_msg = qualification_manage_page.get_el_message_text()
            assert "成功" in success_msg, f"预期成功提示，实际值: '{success_msg}'"
        with allure.step("验证表格刷新"):
            data = qualification_manage_page.get_table_data()
            found = any(qual_name in (row.get("资质名称") or str(row)) for row in data)
            assert found, f"未找到新增的资质记录: {qual_name}"

    @allure.story("新增资质")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_009_add_qualification_validation(self, qualification_manage_page):
        """TD-QUAL-012: 打开新增弹窗与必填项校验"""
        with allure.step("导航到资质管理页面"):
            qualification_manage_page.navigate()
        with allure.step("点击【新增资质】按钮"):
            qualification_manage_page.click_add()
        with allure.step("验证弹窗标题"):
            title = qualification_manage_page.get_dialog_title()
            assert title in ["新增资质", "新增资质信息"], f"弹窗标题不正确: '{title}'"
        with allure.step("不填写内容直接保存"):
            qualification_manage_page.click_dialog_save()
        with allure.step("验证必填项校验提示"):
            error_msgs = qualification_manage_page.get_validation_messages()
            assert len(error_msgs) >= 3, (
                f"预期至少3个校验错误，实际获取 {len(error_msgs)}: {error_msgs}"
            )

    @allure.story("新增资质")
    @allure.severity(allure.severity_level.NORMAL)
    def test_010_prevent_duplicate_submission(self, qualification_manage_page):
        """TD-QUAL-014: 重复提交防止"""
        with allure.step("导航到资质管理页面"):
            qualification_manage_page.navigate()
        with allure.step("点击【新增资质】按钮"):
            qualification_manage_page.click_add()
        with allure.step("填写表单"):
            qualification_manage_page.set_dialog_name("TC-防重复提交测试")
            qualification_manage_page.set_dialog_type("学历证书")
            qualification_manage_page.set_dialog_issuer("测试大学")
        with allure.step("多次点击保存按钮"):
            qualification_manage_page.click_dialog_save()
            # 第二次点击 - 应被禁用
            qualification_manage_page.click_dialog_save()
        with allure.step("验证按钮在首次点击后变成loading状态"):
            assert qualification_manage_page.is_save_button_loading(), "保存按钮未进入loading状态"
        with allure.step("验证接口仅调用一次"):
            # 通过判断只出现一次成功提示来间接验证
            # 注意: 多次成功时可能出现多个toast消息
            success_count = qualification_manage_page.count_el_messages_by_text("成功")
            assert success_count <= 1, f"预期最多1次成功提示，实际出现 {success_count} 次"

    # ==================== 编辑操作 ====================

    @allure.story("编辑资质")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.destructive
    def test_011_edit_qualification(self, qualification_manage_page, test_qualification_data):
        """TD-QUAL: 编辑资质信息 (假设场景)"""
        with allure.step("导航到资质管理页面"):
            qualification_manage_page.navigate()
        with allure.step("点击第1行【编辑】按钮"):
            qualification_manage_page.click_edit(0)
        with allure.step("验证编辑弹窗打开"):
            assert qualification_manage_page.is_dialog_open(), "编辑弹窗未打开"
        with allure.step("修改资质名称"):
            new_name = f"TC-编辑测试-{test_qualification_data['name']}"
            qualification_manage_page.set_dialog_name(new_name)
        with allure.step("点击保存"):
            qualification_manage_page.click_dialog_save()
        with allure.step("验证成功提示"):
            msg = qualification_manage_page.get_el_message_text()
            assert "成功" in msg, f"编辑成功提示预期包含'成功'，实际: '{msg}'"

    # ==================== 删除操作 ====================

    @allure.story("删除资质")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.destructive
    def test_012_delete_single_qualification(self, qualification_manage_page, test_qualification_data):
        """TD-QUAL: 单行删除资质 (假设场景)"""
        with allure.step("导航到资质管理页面"):
            qualification_manage_page.navigate()
        with allure.step("获取删除前数据行数"):
            before_count = len(qualification_manage_page.get_table_data())
        with allure.step("点击第1行【删除】按钮并确认"):
            qualification_manage_page.click_delete(0)
        with allure.step("验证删除成功提示"):
            msg = qualification_manage_page.get_el_message_text()
            assert "成功" in msg, f"删除成功提示预期包含'成功'，实际: '{msg}'"
        with allure.step("验证表格数据减少一行"):
            after_count = len(qualification_manage_page.get_table_data())
            assert after_count == before_count - 1, (
                f"删除后行数 {after_count} 预期为 {before_count - 1}"
            )

    # ==================== 权限与边界 ====================

    @allure.story("权限验证")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_013_add_button_visibility_with_permission(self, qualification_manage_page):
        """TD-QUAL: 有新增权限时按钮可见 (假设场景)"""
        with allure.step("导航到资质管理页面"):
            qualification_manage_page.navigate()
        with allure.step("验证新增按钮可见"):
            assert qualification_manage_page.is_element_visible(
                qualification_manage_page.ADD_BUTTON
            ), "有权限时【新增资质】按钮不可见"

    @allure.story("分页边界")
    @allure.severity(allure.severity_level.NORMAL)
    def test_014_pagination_boundary_last_page(self, qualification_manage_page, test_multiple_qualifications):
        """TD-QUAL: 分页-最后一页翻页禁用 (假设场景)"""
        with allure.step("导航到资质管理页面"):
            qualification_manage_page.navigate()
        with allure.step("跳转到最后一页"):
            qualification_manage_page.go_to_last_page()
        with allure.step("验证下一页按钮被禁用"):
            assert qualification_manage_page.is_next_page_disabled(), "在最后一页时下一页按钮应被禁用"