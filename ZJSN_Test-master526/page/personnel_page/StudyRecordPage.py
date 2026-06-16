"""学习记录页面操作类

Phase 4 自动生成 | 2026-06-12
页面类型: 管理端记录列表（表格 + 3条件筛选 + 无行操作按钮）
"""
import logging

from selenium.webdriver.common.by import By

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class StudyRecordPage(BasePage):
    """学习记录页面 — 表格 + 3条件筛选"""

    # ══════════════════════════════════════════════════════════════════
    # 页面专属定位器
    # ══════════════════════════════════════════════════════════════════

    # — 筛选 —
    SEARCH_STUDENT_NAME = (
        By.CSS_SELECTOR,
        'input[placeholder*="请输入学员名称"]',
    )
    SEARCH_COURSE_NAME = (
        By.CSS_SELECTOR,
        'input[placeholder*="请输入课程名称"]',
    )
    COMPLETED_SELECT = (
        By.XPATH,
        '//label[contains(.,"是否完成")]/following::div[contains(@class,"el-select")][1]',
    )

    # ==================================================================
    # 导航
    # ==================================================================

    def navigate_to_study_record(self):
        """导航到学习记录页面"""
        self.navigate_to("人员管理", "培训管理", "学习记录")
        self.wait_vue_stable()
        logger.info("已导航到学习记录页面")

    # ==================================================================
    # 搜索区操作
    # ==================================================================

    def input_student_name(self, name):
        """输入学员名称"""
        self.input_text(self.SEARCH_STUDENT_NAME, name)
        logger.info("搜索学员: %s", name)

    def input_course_name(self, name):
        """输入课程名称"""
        self.input_text(self.SEARCH_COURSE_NAME, name)
        logger.info("搜索课程: %s", name)

    def select_completed(self, option_text):
        """选择是否完成（需下拉选项文本）"""
        item = self.find_visible(self.COMPLETED_SELECT)
        self._scroll_into_view(item)
        item.click()
        self._select_option(option_text)
        logger.info("选择是否完成: %s", option_text)

    def click_search(self):
        """点击查询按钮"""
        self.click_search_button()
        self.wait_vue_stable()

    def click_reset(self):
        """点击重置按钮"""
        self.click_reset_button()
        self.wait_vue_stable()

    # ==================================================================
    # 表格操作
    # ==================================================================

    def get_record_count(self):
        """获取当前页记录数"""
        return self.get_table_row_count()

    def get_student_names(self):
        """获取学员名称列 (列1) 所有值"""
        return self.get_column_data(1)

    def get_course_names(self):
        """获取课程名称列 (列2) 所有值"""
        return self.get_column_data(2)

    def get_progress_values(self):
        """获取学习进度列 (列5) 所有值"""
        return self.get_column_data(5)

    def is_student_present(self, name):
        """判断指定学员是否在列表中"""
        return self.is_row_present(name)

    def get_first_row_texts(self):
        """获取第一行所有列数据"""
        return self.get_first_row_data()

    # ==================================================================
    # 复合操作
    # ==================================================================

    def search_by_student(self, name):
        """按学员名称搜索"""
        self.input_student_name(name)
        self.click_search()

    def search_by_course(self, name):
        """按课程名称搜索"""
        self.input_course_name(name)
        self.click_search()

    def search_combined(self, student="", course="", completed=""):
        """组合筛选"""
        if student:
            self.input_student_name(student)
        if course:
            self.input_course_name(course)
        if completed:
            self.select_completed(completed)
        self.click_search()
