"""
在线学习管理页面 Page Object
"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class OnlineStudyPage(BasePage):
    """
    在线学习管理页面，封装课程搜索、表格操作、新增/编辑弹窗等方法。
    """

    # ============================================================
    # 搜索/筛选区
    # ============================================================
    SEARCH_COURSE_NAME_INPUT = (By.CSS_SELECTOR, "#search-courseName .el-input__inner")
    SEARCH_CATEGORY_SELECT = (By.CSS_SELECTOR, "#search-category .el-select__wrapper")
    SEARCH_CATEGORY_DROPDOWN = (By.CSS_SELECTOR, ".el-select-dropdown")
    SEARCH_STATUS_SELECT = (By.CSS_SELECTOR, "#search-status .el-select__wrapper")
    SEARCH_DATE_RANGE = (By.CSS_SELECTOR, "#search-dateRange .el-date-editor--daterange")
    SEARCH_BTN = (By.XPATH, "//button[@id='btn-search' and .//span[text()='查询']]")
    RESET_BTN = (By.XPATH, "//button[@id='btn-reset' and .//span[text()='重置']]")

    # ============================================================
    # 顶部操作区
    # ============================================================
    NEW_COURSE_BTN = (By.CSS_SELECTOR, "button#btn-newCourse")

    # ============================================================
    # 表格区
    # ============================================================
    TABLE = (By.CSS_SELECTOR, ".el-table")
    TABLE_LOADING = (By.CSS_SELECTOR, ".el-table__body-wrapper .el-loading-mask")
    TABLE_ROWS = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr.el-table__row")
    COL_COURSE_NAME_LINK = (By.CSS_SELECTOR, ".cell a.el-link")

    # 操作列按钮（根据行索引定位）
    BTN_EDIT_BY_ROW = (By.XPATH, ".//button[.//span[text()='编辑']]")
    BTN_DELETE_BY_ROW = (By.XPATH, ".//button[.//span[text()='删除']]")
    BTN_VIEW_PROGRESS_BY_ROW = (By.XPATH, ".//button[.//span[text()='查看进度']]")

    # ============================================================
    # 分页区
    # ============================================================
    PAGINATION = (By.CSS_SELECTOR, ".el-pagination")
    PAGE_SIZE_SELECT = (By.CSS_SELECTOR, ".el-pagination .el-select__wrapper")
    PAGINATION_NEXT_BTN = (By.CSS_SELECTOR, ".el-pagination .btn-next")
    PAGINATION_PREV_BTN = (By.CSS_SELECTOR, ".el-pagination .btn-prev")

    # ============================================================
    # 弹窗（新建/编辑课程）
    # ============================================================
    DIALOG_COURSE = (By.CSS_SELECTOR, "div#dialog-course")
    DIALOG_TITLE = (By.CSS_SELECTOR, "div#dialog-course .el-dialog__title")
    FORM_COURSE_NAME_INPUT = (By.CSS_SELECTOR, "#dialog-course #form-courseName .el-input__inner")
    FORM_CATEGORY_SELECT = (By.CSS_SELECTOR, "#dialog-course #form-category .el-select__wrapper")
    FORM_TEACHER_INPUT = (By.CSS_SELECTOR, "#dialog-course #form-teacher .el-input__inner")
    FORM_DESCRIPTION_TEXTAREA = (By.CSS_SELECTOR, "#dialog-course #form-description .el-textarea__inner")
    FORM_COVER_UPLOAD = (By.CSS_SELECTOR, "#dialog-course #form-cover .el-upload-dragger")
    FORM_STATUS_SWITCH = (By.CSS_SELECTOR, "#dialog-course #form-status .el-switch")
    SAVE_BTN = (By.XPATH, "//div[@id='dialog-course']//button[.//span[text()='确定']]")
    CANCEL_BTN = (By.XPATH, "//div[@id='dialog-course']//button[.//span[text()='取消']]")

    # ============================================================
    # 导航入口
    # ============================================================
    def navigate(self) -> "OnlineStudyPage":
        """导航到在线学习管理页面"""
        self.navigate_to("人员管理", "在线学习")
        self.wait_vue_stable()
        # 等待表格加载完成
        self.wait_loading_disappear(self.TABLE_LOADING)
        logger.info("导航到在线学习管理页面成功")
        return self

    # ============================================================
    # 搜索操作
    # ============================================================
    def search(self, course_name: str = None, category: str = None,
               status: str = None, date_range: list = None) -> "OnlineStudyPage":
        """
        在搜索区输入条件并点击查询

        :param course_name: 课程名称关键字
        :param category: 课程分类选项文案
        :param status: 课程状态选项文案（全部/上架/下架）
        :param date_range: 创建日期范围 [开始日期, 结束日期]
        """
        if course_name is not None:
            self.fill_input(self.SEARCH_COURSE_NAME_INPUT, course_name)
            logger.info(f"输入课程名称: {course_name}")

        if category is not None:
            self.click_element(self.SEARCH_CATEGORY_SELECT)
            self.wait_element_visible(self.SEARCH_CATEGORY_DROPDOWN)
            self.click_by_text(category)
            logger.info(f"选择课程分类: {category}")

        if status is not None:
            self.click_element(self.SEARCH_STATUS_SELECT)
            self.wait_element_visible(self.SEARCH_CATEGORY_DROPDOWN)
            self.click_by_text(status)
            logger.info(f"选择课程状态: {status}")

        if date_range is not None and len(date_range) == 2:
            self.click_element(self.SEARCH_DATE_RANGE)
            self.fill_input(self.SEARCH_DATE_RANGE, f"{date_range[0]} ~ {date_range[1]}")
            self.click_element(self.SEARCH_DATE_RANGE)  # 点击关闭日期面板
            logger.info(f"选择日期范围: {date_range[0]} ~ {date_range[1]}")

        self.click_element(self.SEARCH_BTN)
        self.wait_loading_disappear(self.TABLE_LOADING)
        logger.info("点击搜索按钮，等待加载完成")
        return self

    def reset_search(self) -> "OnlineStudyPage":
        """点击重置按钮，清空所有搜索条件"""
        self.click_element(self.RESET_BTN)
        self.wait_loading_disappear(self.TABLE_LOADING)
        logger.info("重置搜索条件成功")
        return self

    # ============================================================
    # 表格操作
    # ============================================================
    def get_table_data(self) -> list[dict]:
        """
        获取当前页表格数据

        :return: 列表，每项为 dict {index, courseName, category, teacher, studentCount, status, createTime}
        """
        rows = self.find_elements(self.TABLE_ROWS)
        table_data = []
        for row in rows:
            cells = row.find_elements(By.CSS_SELECTOR, "td")
            if len(cells) >= 8:
                row_data = {
                    "index": cells[0].text.strip(),
                    "courseName": cells[1].text.strip(),
                    "category": cells[2].text.strip(),
                    "teacher": cells[3].text.strip(),
                    "studentCount": cells[4].text.strip(),
                    "status": cells[5].text.strip(),
                    "createTime": cells[6].text.strip(),
                }
                table_data.append(row_data)
        logger.info(f"获取到 {len(table_data)} 条表格数据")
        return table_data

    def click_course_name_link(self, row_index: int = 0) -> "OnlineStudyPage":
        """
        点击指定行的课程名称链接进入详情

        :param row_index: 行索引，从0开始
        """
        rows = self.find_elements(self.TABLE_ROWS)
        if row_index < len(rows):
            link = rows[row_index].find_element(*self.COL_COURSE_NAME_LINK)
            self.click_element(link)
            logger.info(f"点击第 {row_index + 1} 行的课程名称链接")
        return self

    def click_edit(self, row_index: int = 0) -> "OnlineStudyPage":
        """
        点击指定行的编辑按钮

        :param row_index: 行索引，从0开始
        """
        rows = self.find_elements(self.TABLE_ROWS)
        if row_index < len(rows):
            edit_btn = rows[row_index].find_element(*self.BTN_EDIT_BY_ROW)
            self.scroll_to_element(edit_btn)
            self.click_element(edit_btn)
            self.wait_element_visible(self.DIALOG_COURSE)
            logger.info(f"点击第 {row_index + 1} 行的编辑按钮")
        return self

    def click_delete(self, row_index: int = 0) -> "OnlineStudyPage":
        """
        点击指定行的删除按钮

        :param row_index: 行索引，从0开始
        """
        rows = self.find_elements(self.TABLE_ROWS)
        if row_index < len(rows):
            delete_btn = rows[row_index].find_element(*self.BTN_DELETE_BY_ROW)
            self.scroll_to_element(delete_btn)
            self.click_element(delete_btn)
            # 等待确认对话框出现
            self.wait_for_dialog()
            logger.info(f"点击第 {row_index + 1} 行的删除按钮")
        return self

    def click_view_progress(self, row_index: int = 0) -> "OnlineStudyPage":
        """
        点击指定行的查看进度按钮

        :param row_index: 行索引，从0开始
        """
        rows = self.find_elements(self.TABLE_ROWS)
        if row_index < len(rows):
            progress_btn = rows[row_index].find_element(*self.BTN_VIEW_PROGRESS_BY_ROW)
            self.scroll_to_element(progress_btn)
            self.click_element(progress_btn)
            logger.info(f"点击第 {row_index + 1} 行的查看进度按钮")
        return self

    # ============================================================
    # 分页操作
    # ============================================================
    def get_pagination_info(self) -> dict:
        """
        获取分页信息

        :return: dict {total, page_size, current_page, total_pages}
        """
        total_text = self.get_text(self.TOTAL_COUNT).replace("共 ", "").replace(" 条", "")
        total = int(total_text) if total_text and total_text.isdigit() else 0

        page_size_text = self.get_text(self.PAGE_SIZE_SELECT)
        page_size = 10  # default
        if page_size_text and page_size_text.isdigit():
            page_size = int(page_size_text)

        # 简单估算当前页码和总页数
        current_page_text = self.get_text((By.CSS_SELECTOR, ".el-pagination .el-pager .is-active"))
        current_page = int(current_page_text) if current_page_text and current_page_text.isdigit() else 1
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

        pagination_info = {
            "total": total,
            "page_size": page_size,
            "current_page": current_page,
            "total_pages": total_pages,
        }
        logger.info(f"分页信息: {pagination_info}")
        return pagination_info

    def go_to_next_page(self) -> "OnlineStudyPage":
        """点击下一页"""
        self.click_element(self.PAGINATION_NEXT_BTN)
        self.wait_loading_disappear(self.TABLE_LOADING)
        logger.info("翻到下一页")
        return self

    def go_to_prev_page(self) -> "OnlineStudyPage":
        """点击上一页"""
        self.click_element(self.PAGINATION_PREV_BTN)
        self.wait_loading_disappear(self.TABLE_LOADING)
        logger.info("翻到上一页")
        return self

    # ============================================================
    # 新增课程
    # ============================================================
    def click_add(self) -> "OnlineStudyPage":
        """点击新建课程按钮"""
        self.click_element(self.NEW_COURSE_BTN)
        self.wait_element_visible(self.DIALOG_COURSE)
        logger.info("点击新建课程按钮，弹窗已打开")
        return self

    # ============================================================
    # 弹窗表单操作
    # ============================================================
    def fill_form(self, data: dict) -> "OnlineStudyPage":
        """
        填写新建/编辑课程弹窗表单

        :param data: dict，支持以下字段：
            courseName (str), category (str), teacher (str),
            description (str), status (bool)
        """
        if "courseName" in data:
            self.fill_input(self.FORM_COURSE_NAME_INPUT, data["courseName"])
            logger.info(f"填写课程名称: {data['courseName']}")

        if "category" in data:
            self.click_element(self.FORM_CATEGORY_SELECT)
            self.wait_element_visible(self.SEARCH_CATEGORY_DROPDOWN)
            self.click_by_text(data["category"])
            logger.info(f"选择课程分类: {data['category']}")

        if "teacher" in data:
            self.fill_input(self.FORM_TEACHER_INPUT, data["teacher"])
            logger.info(f"填写授课老师: {data['teacher']}")

        if "description" in data:
            textarea = self.find_element(self.FORM_DESCRIPTION_TEXTAREA)
            textarea.clear()
            textarea.send_keys(data["description"])
            logger.info(f"填写课程描述")

        if "status" in data:
            self.click_element(self.FORM_STATUS_SWITCH)
            logger.info(f"设置课程状态: {data['status']}")

        return self

    def confirm_dialog(self) -> "OnlineStudyPage":
        """点击弹窗中的确定按钮"""
        self.click_element(self.SAVE_BTN)
        self.wait_dialog_close()
        self.wait_loading_disappear(self.TABLE_LOADING)
        logger.info("保存课程成功")
        return self

    def cancel_dialog(self) -> "OnlineStudyPage":
        """点击弹窗中的取消按钮"""
        self.click_element(self.CANCEL_BTN)
        self.wait_dialog_close()
        logger.info("取消课程编辑")
        return self

    # ============================================================
    # 删除确认弹窗
    # ============================================================
    def confirm_delete(self) -> "OnlineStudyPage":
        """确认删除"""
        self.click_element(self.CONFIRM_BTN)
        self.wait_dialog_close()
        self.wait_loading_disappear(self.TABLE_LOADING)
        logger.info("确认删除成功")
        return self

    def cancel_delete(self) -> "OnlineStudyPage":
        """取消删除"""
        self.click_element(self.CANCEL_BTN)
        self.wait_dialog_close()
        logger.info("取消删除")
        return self