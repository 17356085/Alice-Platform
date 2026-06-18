# -*- coding: utf-8 -*-
"""
测试脚本：我的档案模块
Module: personnel
Page: my-archive

基于 PAGE_CONTEXT.md 和 PageObject 生成的测试脚本。
覆盖：页面加载、Tab切换、搜索筛选、编辑基本信息、修改密码等核心场景。
"""

import pytest
import allure
from page.personnel_page.MyArchivePage import MyArchivePage


@allure.epic("人事管理")
@allure.feature("我的档案")
class TestMyArchive:
    """我的档案页面测试类"""

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_001_page_load(self, my_archive_page: MyArchivePage):
        """TC-ARCH-001: 页面正常加载，基本信息 Tab 默认激活"""
        with allure.step("进入我的档案页面"):
            my_archive_page.navigate()

        with allure.step("验证页面标题存在"):
            page_title = my_archive_page.get_title()
            assert "我的档案" in page_title, f"页面标题不包含'我的档案'，实际标题：{page_title}"

        with allure.step("验证基本信息 Tab 默认激活"):
            assert my_archive_page.is_basic_info_tab_active(), "基本信息 Tab 未默认激活"

        with allure.step("验证个人头像可见"):
            assert my_archive_page.is_element_visible(MyArchivePage.SIDEBAR_AVATAR), "侧边栏头像不可见"

    # ---------- Tab 切换 ----------

    @allure.story("Tab 切换")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.smoke
    def test_002_switch_to_archive_tab(self, my_archive_page: MyArchivePage):
        """TC-ARCH-002: 切换到档案变更记录 Tab"""
        with allure.step("点击档案变更记录 Tab"):
            my_archive_page.switch_to_archive_tab()

        with allure.step("验证筛选区出现"):
            assert my_archive_page.is_element_visible(MyArchivePage.CHANGE_TYPE_SELECTOR), \
                "档案变更记录 Tab 下筛选区未显示"

        with allure.step("验证表格存在"):
            assert my_archive_page.is_element_visible(MyArchivePage.CHANGE_TABLE), \
                "档案变更记录 Tab 下表格未显示"

    # ---------- 搜索与重置 ----------

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_003_search_by_change_type(self, my_archive_page: MyArchivePage):
        """TC-ARCH-003: 按变更类型搜索（假设存在数据）"""
        with allure.step("切换到档案变更记录 Tab"):
            my_archive_page.switch_to_archive_tab()

        with allure.step("选择变更类型为'修改'"):
            my_archive_page.select_change_type("修改")

        with allure.step("点击查询"):
            my_archive_page.click_search()

        with allure.step("验证表格数据更新（至少有一行）"):
            rows = my_archive_page.get_table_rows()
            assert len(rows) > 0, "搜索后表格无数据，可能无匹配记录或页面未加载"

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_004_search_by_date_range(self, my_archive_page: MyArchivePage):
        """TC-ARCH-004: 按日期范围搜索（使用历史日期）"""
        with allure.step("切换到档案变更记录 Tab"):
            my_archive_page.switch_to_archive_tab()

        with allure.step("输入日期范围：上个月至今"):
            my_archive_page.input_date_range("2026-05-01", "2026-06-18")

        with allure.step("点击查询"):
            my_archive_page.click_search()

        with allure.step("验证表格数据加载"):
            rows = my_archive_page.get_table_rows()
            # 不强制要求有数据，但至少无报错
            assert my_archive_page.is_element_visible(MyArchivePage.CHANGE_TABLE), \
                "日期搜索后表格不可见"

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_005_reset_filter(self, my_archive_page: MyArchivePage):
        """TC-ARCH-005: 重置筛选条件后恢复全部数据"""
        with allure.step("切换到档案变更记录 Tab"):
            my_archive_page.switch_to_archive_tab()

        with allure.step("设置筛选条件：类型=修改，日期范围=近一周"):
            my_archive_page.select_change_type("修改")
            my_archive_page.input_date_range("2026-06-11", "2026-06-18")

        with allure.step("点击重置"):
            my_archive_page.click_reset()

        with allure.step("验证筛选条件已清空（类型默认'全部'，日期为空）"):
            assert my_archive_page.get_change_type_value() is None or my_archive_page.get_change_type_value() == "", \
                "重置后变更类型未清空"
            # 验证日期输入框为空（可通过 get_attribute('value') 判断）
            date_value = my_archive_page.get_date_range_value()
            assert date_value is None or date_value == "", f"重置后日期未清空，实际值：{date_value}"

    # ---------- 表格数据验证 ----------

    @allure.story("表格数据")
    @allure.severity(allure.severity_level.NORMAL)
    def test_006_verify_table_column_format(self, my_archive_page: MyArchivePage):
        """TC-ARCH-006: 验证表格列数据格式（时间格式、操作人姓名）"""
        with allure.step("切换到档案变更记录 Tab"):
            my_archive_page.switch_to_archive_tab()

        with allure.step("获取第一行数据"):
            first_row = my_archive_page.get_first_row_data()
            assert first_row is not None, "表格无数据，无法验证格式"

        with allure.step("验证变更时间格式为 YYYY-MM-DD HH:mm:ss"):
            time_text = first_row.get("变更时间", "")
            assert len(time_text) == 19, f"时间格式不符合要求：{time_text}（长度={len(time_text)}）"
            assert time_text[4] == '-' and time_text[7] == '-' and time_text[10] == ' ', \
                f"时间分隔符错误：{time_text}"

        with allure.step("验证操作人列不为空"):
            operator = first_row.get("操作人", "")
            assert operator != "", "操作人列为空"

    # ---------- 编辑基本信息（破坏性） ----------

    @allure.story("编辑基本信息")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.destructive
    def test_007_edit_basic_info(self, my_archive_page: MyArchivePage):
        """TC-ARCH-007: 编辑基本信息并保存"""
        with allure.step("点击编辑基本信息按钮"):
            my_archive_page.click_edit_basic_info()

        with allure.step("在弹窗中修改邮箱为测试邮箱"):
            my_archive_page.edit_email("test_update@company.com")

        with allure.step("保存修改"):
            my_archive_page.save_edit_dialog()

        with allure.step("等待弹窗消失"):
            assert not my_archive_page.is_element_present(MyArchivePage.EDIT_INFO_DIALOG), \
                "编辑弹窗未关闭"

        with allure.step("验证页面上邮箱已更新"):
            displayed_email = my_archive_page.get_field_value("email")
            assert displayed_email == "test_update@company.com", \
                f"邮箱更新失败，页面显示：{displayed_email}"

    @allure.story("编辑基本信息")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.destructive
    def test_008_edit_basic_info_cancel(self, my_archive_page: MyArchivePage):
        """TC-ARCH-008: 编辑基本信息时取消，数据不变"""
        with allure.step("获取当前邮箱"):
            original_email = my_archive_page.get_field_value("email")

        with allure.step("点击编辑，修改邮箱为临时值"):
            my_archive_page.click_edit_basic_info()
            my_archive_page.edit_email("will_be_canceled@company.com")

        with allure.step("点击取消"):
            my_archive_page.cancel_edit_dialog()

        with allure.step("验证邮箱未变化"):
            current_email = my_archive_page.get_field_value("email")
            assert current_email == original_email, \
                f"取消后邮箱被修改，期望 {original_email}，实际 {current_email}"

    # ---------- 修改密码（破坏性） ----------

    @allure.story("修改密码")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.destructive
    def test_009_change_password_success(self, my_archive_page: MyArchivePage):
        """TC-ARCH-009: 正常修改密码（需提供正确旧密码）"""
        with allure.step("点击修改密码快捷入口"):
            my_archive_page.click_change_password()

        with allure.step("输入旧密码和新密码"):
            my_archive_page.input_old_password("Test1234!")   # 假设已知旧密码
            my_archive_page.input_new_password("NewTest5678!")

        with allure.step("保存修改"):
            my_archive_page.save_password_dialog()

        with allure.step("验证弹窗关闭，无错误提示"):
            assert not my_archive_page.is_element_present(MyArchivePage.PASSWORD_DIALOG), \
                "密码修改弹窗未关闭"

        with allure.step("恢复密码（确保下次用例可用）"):
            # 直接通过 API 或 再次修改回旧密码（这里使用界面方式还原）
            my_archive_page.click_change_password()
            my_archive_page.input_old_password("NewTest5678!")
            my_archive_page.input_new_password("Test1234!")
            my_archive_page.save_password_dialog()

    @allure.story("修改密码")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.destructive
    def test_010_change_password_wrong_old(self, my_archive_page: MyArchivePage):
        """TC-ARCH-010: 输入错误旧密码，应报错且不关闭弹窗"""
        with allure.step("点击修改密码"):
            my_archive_page.click_change_password()

        with allure.step("输入错误旧密码并保存"):
            my_archive_page.input_old_password("WrongOldPass1!")
            my_archive_page.input_new_password("AnyNewPass2@")
            my_archive_page.save_password_dialog()

        with allure.step("验证错误提示出现（假设有 toast 或弹窗内提示）"):
            error_msg_element = my_archive_page.get_error_message()
            assert error_msg_element is not None, "未看到错误提示"
            assert "旧密码错误" in error_msg_element or "密码不正确" in error_msg_element, \
                f"错误提示内容不符合预期：{error_msg_element}"

        with allure.step("关闭弹窗"):
            my_archive_page.cancel_password_dialog()

    # ---------- 分页 ----------

    @allure.story("分页功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_011_pagination(self, my_archive_page: MyArchivePage):
        """TC-ARCH-011: 分页切换每页条数"""
        with allure.step("切换到档案变更记录 Tab"):
            my_archive_page.switch_to_archive_tab()

        with allure.step("将每页条数改为 20"):
            my_archive_page.set_page_size(20)

        with allure.step("验证分页信息更新"):
            page_info = my_archive_page.get_pagination_info()
            assert "20 条/页" in page_info or "20条/页" in page_info, \
                f"分页信息未包含'20条/页'，实际：{page_info}"

    # ---------- 编辑基本信息 - 必填校验 ----------

    @allure.story("表单校验")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.destructive
    def test_012_edit_basic_info_required_validation(self, my_archive_page: MyArchivePage):
        """TC-ARCH-012: 编辑基本信息时清空必填字段，验证错误提示"""
        with allure.step("点击编辑"):
            my_archive_page.click_edit_basic_info()

        with allure.step("清空姓名输入框"):
            my_archive_page.clear_field_in_dialog("name")

        with allure.step("点击保存"):
            my_archive_page.save_edit_dialog()

        with allure.step("验证弹窗未关闭（因为有校验错误）"):
            assert my_archive_page.is_element_present(MyArchivePage.EDIT_INFO_DIALOG), \
                "弹窗不应在必填字段为空时关闭"

        with allure.step("取消编辑，恢复页面状态"):
            my_archive_page.cancel_edit_dialog()

    # ---------- 空状态 ----------

    @allure.story("空状态")
    @allure.severity(allure.severity_level.NORMAL)
    def test_013_empty_state(self, my_archive_page: MyArchivePage):
        """TC-ARCH-013: 查询条件不匹配时显示空状态"""
        with allure.step("切换到档案变更记录 Tab"):
            my_archive_page.switch_to_archive_tab()

        with allure.step("选择一个不可能匹配的日期（如未来日期）"):
            my_archive_page.input_date_range("2099-01-01", "2099-12-31")

        with allure.step("点击查询"):
            my_archive_page.click_search()

        with allure.step("验证表格显示'暂无数据'"):
            empty_text = my_archive_page.get_empty_table_text()
            assert empty_text is not None and "暂无数据" in empty_text, \
                f"空状态文本不符合预期：{empty_text}"

        with allure.step("验证分页显示共0条"):
            pagination_info = my_archive_page.get_pagination_info()
            assert "0 条" in pagination_info or "共0条" in pagination_info, \
                f"分页信息未显示0条：{pagination_info}"


# ⚠️ 注意：
#   - 本测试类假设 conftest.py 提供了 my_archive_page  fixture（module scope）
#   - test_007 ~ test_010 为破坏性测试，需要在执行后清理数据。
#     当前清理在 fixture teardown 中并未实现具体清理逻辑（见 conftest.py 中 my_archive_page fixture 的 yield 后提示）。
#     实际运行时需要补充 API 清理或使用专用测试账号，避免影响其他测试。
#   - 本文中使用了 PageObject 中的假定方法（如 select_change_type, input_date_range 等），
#     实际编写时需要确保 PageObject 提供了对应方法，或根据现有方法组合。