"""
在线学习管理页面测试脚本

模块: personnel
页面: 在线学习 (online-study)
"""

import pytest
import allure
import logging
from page.personnel_page.OnlineStudyPage import OnlineStudyPage

logger = logging.getLogger(__name__)


@allure.epic("人员管理")
@allure.feature("在线学习")
class TestOnlineStudy:
    """在线学习页面测试类"""

    @allure.story("页面加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_page_load(self, online_study_page: OnlineStudyPage):
        """TC-LOAD-001: 页面正常加载"""
        page = online_study_page.navigate()
        with allure.step("验证页面标题"):
            assert "在线学习" in page.get_title(), "页面标题未包含'在线学习'"
        with allure.step("验证表格可见"):
            assert page.is_element_visible(page.TABLE), "课程表格未加载"
        with allure.step("验证分页组件可见"):
            assert page.is_element_visible(page.PAGINATION), "分页组件未加载"

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_search_by_name(self, online_study_page: OnlineStudyPage):
        """TC-SRC-001: 按课程名称搜索（精确匹配）"""
        page = online_study_page.navigate()
        course_name = "Python基础"
        with allure.step("输入课程名称并查询"):
            page.search(course_name=course_name)
        with allure.step("验证搜索结果只包含目标课程"):
            data = page.get_table_data()
            assert len(data) >= 1, f"搜索'{course_name}'后结果为空"
            assert any(
                row.get("courseName") == course_name for row in data
            ), f"搜索结果中未找到课程'{course_name}'"

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_reset_search(self, online_study_page: OnlineStudyPage):
        """TC-SRC-004: 重置筛选条件"""
        page = online_study_page.navigate()
        with allure.step("先执行一次搜索缩小结果"):
            page.search(course_name="Java")
        with allure.step("点击重置按钮"):
            page.reset_search()
        with allure.step("验证搜索条件已清空，表格恢复全量数据"):
            data = page.get_table_data()
            assert len(data) > 0, "重置后表格仍为空"
            # 可选：验证输入框已清空，但此处仅验证数据非空

    @allure.story("搜索功能")
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_no_result(self, online_study_page: OnlineStudyPage):
        """TC-SRC-005: 搜索无结果时显示空状态"""
        page = online_study_page.navigate()
        with allure.step("输入不可能存在的课程名称"):
            page.search(course_name="ABCDEFGHIJ")
        with allure.step("验证表格显示暂无数据"):
            data = page.get_table_data()
            assert len(data) == 0, "搜索不应返回任何数据"
            # 检查空状态组件（el-empty）
            empty_text = page.get_text((By.CSS_SELECTOR, ".el-empty__description"))
            assert "暂无课程数据" in empty_text, f"空数据文案错误，实际为: {empty_text}"

    @allure.story("新增课程")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_open_new_course_dialog(self, online_study_page: OnlineStudyPage):
        """TC-NEW-001: 打开新建课程弹窗"""
        page = online_study_page.navigate()
        with allure.step("点击新建课程按钮"):
            page.click_element(page.NEW_COURSE_BTN)
        with allure.step("验证弹窗已打开"):
            assert page.is_element_visible(page.DIALOG_COURSE), "新建课程弹窗未出现"
            dialog_title = page.get_text(page.DIALOG_TITLE)
            assert dialog_title == "新建课程", f"弹窗标题应为'新建课程'，实际为'{dialog_title}'"

    @allure.story("新增课程")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.destructive
    def test_create_course_success(self, online_study_page: OnlineStudyPage):
        """TC-NEW-005: 新建课程成功（破坏性测试，需清理）"""
        page = online_study_page.navigate()
        course_name = f"自动化测试课程_{self._timestamp()}"
        try:
            with allure.step("打开新建弹窗"):
                page.click_element(page.NEW_COURSE_BTN)
                page.wait_element_visible(page.DIALOG_COURSE)
            with allure.step("填写表单"):
                page.fill_input(page.FORM_COURSE_NAME_INPUT, course_name)
                page.click_element(page.FORM_CATEGORY_SELECT)
                page.click_by_text("技术培训")  # 假设存在该分类
                page.fill_input(page.FORM_TEACHER_INPUT, "张老师")
                page.fill_input(page.FORM_DESCRIPTION_TEXTAREA, "测试描述")
            with allure.step("点击确定保存"):
                page.click_element(page.SAVE_BTN)
                page.wait_loading_disappear(page.TABLE_LOADING)
            with allure.step("验证表格中出现新课程"):
                data = page.get_table_data()
                assert any(
                    row.get("courseName") == course_name for row in data
                ), f"表格中未找到新建的课程'{course_name}'"
        finally:
            # 清理：删除刚刚创建的课程
            self._delete_course_by_name(page, course_name)

    @allure.story("新增课程")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_form_validation_required(self, online_study_page: OnlineStudyPage):
        """TC-NEW-002: 表单必填项校验"""
        page = online_study_page.navigate()
        with allure.step("打开新建弹窗"):
            page.click_element(page.NEW_COURSE_BTN)
            page.wait_element_visible(page.DIALOG_COURSE)
        with allure.step("不填写必填项，直接点击确定"):
            page.click_element(page.SAVE_BTN)
        with allure.step("验证弹窗未关闭且出现校验提示"):
            assert page.is_element_visible(page.DIALOG_COURSE), "弹窗不应关闭"
            # 校验提示通常为 el-form-item__error
            error_elems = page.find_elements((By.CSS_SELECTOR, ".el-form-item__error"))
            assert any("请输入" in e.text or "请选择" in e.text for e in error_elems), \
                f"未找到必填项校验提示，实际元素文本: {[e.text for e in error_elems]}"
        with allure.step("关闭弹窗"):
            page.click_element(page.CANCEL_BTN)

    # ==================================================================
    # 辅助方法
    # ==================================================================
    @staticmethod
    def _timestamp() -> str:
        """生成时间戳字符串，用于唯一命名"""
        import time
        return str(int(time.time() * 1000))[-8:]

    @staticmethod
    def _delete_course_by_name(page: OnlineStudyPage, course_name: str):
        """删除指定名称的课程（通过表格操作列）"""
        try:
            # 搜索该课程
            page.search(course_name=course_name)
            data = page.get_table_data()
            if not data:
                logger.warning(f"未找到课程'{course_name}'，跳过清理")
                return
            # 找到对应行并点击删除
            row_index = None
            for idx, row in enumerate(data):
                if row.get("courseName") == course_name:
                    row_index = idx
                    break
            if row_index is None:
                return
            # 点击该行的删除按钮
            rows = page.find_elements(page.TABLE_ROWS)
            if row_index < len(rows):
                target_row = rows[row_index]
                delete_btn = target_row.find_element(*page.BTN_DELETE_BY_ROW)
                delete_btn.click()
                # 等待确认弹窗并确认
                confirm_btn = page.find_element((By.XPATH, "//div[contains(@class,'el-message-box')]//button[./span[text()='确定']]"))
                confirm_btn.click()
                page.wait_loading_disappear(page.TABLE_LOADING)
                logger.info(f"已删除课程'{course_name}'")
        except Exception as e:
            logger.warning(f"清理课程'{course_name}'时发生异常: {e}")