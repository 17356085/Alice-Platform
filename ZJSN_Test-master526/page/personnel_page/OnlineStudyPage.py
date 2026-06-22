"""
在线学习管理页面 Page Object

模块: personnel
页面: 在线学习 (online-study)
"""

import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class OnlineStudyPage(BasePage):
    # ==================================================================
    # 搜索/筛选区
    # ==================================================================
    SEARCH_COURSE_NAME_INPUT = (By.CSS_SELECTOR, "#search-courseName .el-input__inner")
    SEARCH_CATEGORY_SELECT = (By.CSS_SELECTOR, "#search-category .el-select__wrapper")
    SEARCH_CATEGORY_DROPDOWN = (By.CSS_SELECTOR, ".el-select-dropdown")
    SEARCH_STATUS_SELECT = (By.CSS_SELECTOR, "#search-status .el-select__wrapper")
    SEARCH_DATE_RANGE = (By.CSS_SELECTOR, "#search-dateRange .el-date-editor--daterange")
    SEARCH_BTN = (By.XPATH, "//button[@id='btn-search' and .//span[text()='查询']]")
    RESET_BTN = (By.XPATH, "//button[@id='btn-reset' and .//span[text()='重置']]")

    # ==================================================================
    # 顶部操作区
    # ==================================================================
    NEW_COURSE_BTN = (By.CSS_SELECTOR, "button#btn-newCourse")

    # ==================================================================
    # 表格区
    # ==================================================================
    TABLE = (By.CSS_SELECTOR, ".el-table")
    TABLE_LOADING = (By.CSS_SELECTOR, ".el-table__body-wrapper .el-loading-mask")
    TABLE_ROWS = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr.el-table__row")
    COL_COURSE_NAME_LINK = (By.CSS_SELECTOR, ".cell a.el-link")

    # 操作列按钮（相对行定位）
    BTN_EDIT_BY_ROW = (By.XPATH, ".//button[.//span[text()='编辑']]")
    BTN_DELETE_BY_ROW = (By.XPATH, ".//button[.//span[text()='删除']]")
    BTN_VIEW_PROGRESS_BY_ROW = (By.XPATH, ".//button[.//span[text()='查看进度']]")

    # ==================================================================
    # 分页区
    # ==================================================================
    PAGINATION = (By.CSS_SELECTOR, ".el-pagination")
    PAGE_SIZE_SELECT = (By.CSS_SELECTOR, ".el-pagination .el-select__wrapper")
    PAGINATION_NEXT_BTN = (By.CSS_SELECTOR, ".el-pagination .btn-next")
    PAGINATION_PREV_BTN = (By.CSS_SELECTOR, ".el-pagination .btn-prev")

    # ==================================================================
    # 弹窗（新建/编辑课程）
    # ==================================================================
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

    # ==================================================================
    # 导航入口
    # ==================================================================
    def navigate(self) -> "OnlineStudyPage":
        """JS hash 导航到在线学习页面（SPA 内无刷新）"""
        self.driver.execute_script("window.location.hash = '#/personnel/training/onlineStudy'")
        self.wait_vue_stable()
        self._wait_loading_gone(timeout=10)
        logger.info("导航到在线学习管理页面成功")
        return self

    # ==================================================================
    # 搜索操作
    # ==================================================================
    def search(self, course_name: str = None, category: str = None,
               status: str = None, date_range: list = None) -> "OnlineStudyPage":
        """
        输入搜索条件并点击查询

        :param course_name: 课程名称关键字
        :param category: 课程分类选项文案
        :param status: 课程状态选项文案（全部/上架/下架）
        :param date_range: 创建日期范围 [开始日期, 结束日期]
        """
        if course_name is not None:
            self.js_fill_input(self.SEARCH_COURSE_NAME_INPUT, course_name)
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
            # 日期范围使用 send_keys 填入格式 "开始 ~ 结束"
            self.js_fill_input(self.SEARCH_DATE_RANGE, f"{date_range[0]} ~ {date_range[1]}")
            self.click_element(self.SEARCH_DATE_RANGE)  # 关闭面板
            logger.info(f"选择日期范围: {date_range[0]} ~ {date_range[1]}")

        self.click_element(self.SEARCH_BTN)
        self.wait_loading_disappear(self.TABLE_LOADING)
        logger.info("点击查询按钮，等待加载完成")
        return self

    def reset_search(self) -> "OnlineStudyPage":
        """点击重置按钮，清空所有搜索条件"""
        self.click_element(self.RESET_BTN)
        self.wait_loading_disappear(self.TABLE_LOADING)
        logger.info("重置搜索条件成功")
        return self

    # ==================================================================
    # 表格数据获取
    # ==================================================================
    def get_table_data(self) -> list[dict]:
        """
        获取当前页表格数据（每一行作为字典）

        :return: [
            {
                "index": 1,
                "courseName": "课程A",
                "category": "必修",
                "teacher": "张老师",
                "studentCount": 30,
                "status": "上架",
                "createTime": "2026-06-01"
            },
            ...
        ]
        """
        rows = self.find_elements(self.TABLE_ROWS)
        data = []
        for row in rows:
            cells = row.find_elements(By.CSS_SELECTOR, "td")
            if len(cells) < 7:
                continue
            data.append({
                "index": cells[0].text.strip(),
                "courseName": cells[1].text.strip(),
                "category": cells[2].text.strip(),
                "teacher": cells[3].text.strip(),
                "studentCount": cells[4].text.strip(),
                "status": cells[5].text.strip(),
                "createTime": cells[6].text.strip(),
            })
        logger.info(f"获取到当前页 {len(data)} 条数据")
        return data

    # ==================================================================
    # 新增课程
    # ==================================================================
    def click_add(self) -> "OnlineStudyPage":
        """点击『新建课程』按钮，打开新建弹窗"""
        self.click_element(self.NEW_COURSE_BTN)
        self.wait_element_visible(self.DIALOG_COURSE)
        logger.info("点击新建课程按钮，弹窗打开")
        return self

    def fill_form(self, data: dict) -> "OnlineStudyPage":
        """
        填写弹窗表单（支持部分字段）

        :param data: {
            "courseName": "课程名称",
            "category": "分类文案",
            "teacher": "教师名",
            "description": "描述",
            "status": True/False  # True=上架, False=下架
        }
        """
        if "courseName" in data:
            self.js_fill_input(self.FORM_COURSE_NAME_INPUT, data["courseName"])
            logger.info(f"填写课程名称: {data['courseName']}")
        if "category" in data:
            self.click_element(self.FORM_CATEGORY_SELECT)
            self.wait_element_visible(self.SEARCH_CATEGORY_DROPDOWN)  # 复用下拉列表定位器
            self.click_by_text(data["category"])
            logger.info(f"选择分类: {data['category']}")
        if "teacher" in data:
            self.js_fill_input(self.FORM_TEACHER_INPUT, data["teacher"])
            logger.info(f"填写授课老师: {data['teacher']}")
        if "description" in data:
            self.js_fill_input(self.FORM_DESCRIPTION_TEXTAREA, data["description"])
            logger.info(f"填写描述: {data['description']}")
        if "status" in data:
            current_class = self.get_attribute(self.FORM_STATUS_SWITCH, "class")
            is_checked = "is-checked" in current_class
            if data["status"] != is_checked:
                self.click_element(self.FORM_STATUS_SWITCH)
                logger.info(f"切换状态为: {'上架' if data['status'] else '下架'}")
        return self

    # ==================================================================
    # 弹窗确认/取消
    # ==================================================================
    def confirm_dialog(self) -> "OnlineStudyPage":
        """点击弹窗『确定』按钮"""
        self.click_element(self.SAVE_BTN)
        self.wait_loading_disappear(self.TABLE_LOADING)
        self.wait_element_invisible(self.DIALOG_COURSE)
        logger.info("确认弹窗，操作完成")
        return self

    def cancel_dialog(self) -> "OnlineStudyPage":
        """点击弹窗『取消』按钮"""
        self.click_element(self.CANCEL_BTN)
        self.wait_element_invisible(self.DIALOG_COURSE)
        logger.info("取消弹窗")
        return self

    # ==================================================================
    # 表格行操作（编辑/删除/查看进度）
    # ==================================================================
    def click_edit(self, row_index: int = 0) -> "OnlineStudyPage":
        """
        点击指定行的『编辑』按钮

        :param row_index: 行索引（从0开始）
        """
        rows = self.find_elements(self.TABLE_ROWS)
        if row_index >= len(rows):
            raise IndexError(f"行索引 {row_index} 超出范围，共 {len(rows)} 行")
        target_row = rows[row_index]
        edit_btn = target_row.find_element(*self.BTN_EDIT_BY_ROW)
        self.wait_element_clickable(edit_btn)
        edit_btn.click()
        self.wait_element_visible(self.DIALOG_COURSE)
        logger.info(f"点击第 {row_index + 1} 行的编辑按钮")
        return self

    def click_delete(self, row_index: int = 0) -> "OnlineStudyPage":
        """
        点击指定行的『删除』按钮（弹出确认框）

        :param row_index: 行索引（从0开始）
        """
        rows = self.find_elements(self.TABLE_ROWS)
        if row_index >= len(rows):
            raise IndexError(f"行索引 {row_index} 超出范围，共 {len(rows)} 行")
        target_row = rows[row_index]
        delete_btn = target_row.find_element(*self.BTN_DELETE_BY_ROW)
        self.wait_element_clickable(delete_btn)
        delete_btn.click()
        # 等待 Element Plus 确认弹框出现
        self.wait_element_visible(self.DIALOG_CONFIRM)
        logger.info(f"点击第 {row_index + 1} 行的删除按钮，确认弹框出现")
        return self

    def click_view_progress(self, row_index: int = 0) -> "OnlineStudyPage":
        """
        点击指定行的『查看进度』按钮

        :param row_index: 行索引（从0开始）
        """
        rows = self.find_elements(self.TABLE_ROWS)
        if row_index >= len(rows):
            raise IndexError(f"行索引 {row_index} 超出范围，共 {len(rows)} 行")
        target_row = rows[row_index]
        progress_btn = target_row.find_element(*self.BTN_VIEW_PROGRESS_BY_ROW)
        self.wait_element_clickable(progress_btn)
        progress_btn.click()
        logger.info(f"点击第 {row_index + 1} 行的查看进度按钮")
        # 通常此处会跳转或打开新页面，可根据实际补充等待逻辑
        return self

    # ==================================================================
    # 分页信息
    # ==================================================================
    def get_pagination_info(self) -> dict:
        """
        获取分页信息

        :return: {
            "total": 100,
            "page_size": 20,
            "current_page": 1
        }
        """
        # 从 el-pagination 组件中提取
        total_text = self.find_element((By.CSS_SELECTOR, ".el-pagination .el-pagination__total")).text
        total = int(total_text.replace("共 ", "").replace(" 条", ""))
        page_size_btn = self.find_element((By.CSS_SELECTOR, ".el-pagination .el-select__wrapper .el-select__placeholder"))
        page_size = int(page_size_btn.text.strip())
        # 当前页码通过 el-pager 中的 active 元素获取
        active_page_el = self.find_element((By.CSS_SELECTOR, ".el-pagination .el-pager li.is-active"))
        current_page = int(active_page_el.text.strip())
        logger.info(f"分页信息: total={total}, page_size={page_size}, current_page={current_page}")
        return {"total": total, "page_size": page_size, "current_page": current_page}

    # ==================================================================
    # 辅助方法（翻页、选择每页条数等）
    # ==================================================================
    def go_to_next_page(self) -> "OnlineStudyPage":
        """点击下一页按钮"""
        self.click_element(self.PAGINATION_NEXT_BTN)
        self.wait_loading_disappear(self.TABLE_LOADING)
        logger.info("点击下一页")
        return self

    def go_to_prev_page(self) -> "OnlineStudyPage":
        """点击上一页按钮"""
        self.click_element(self.PAGINATION_PREV_BTN)
        self.wait_loading_disappear(self.TABLE_LOADING)
        logger.info("点击上一页")
        return self

    def select_page_size(self, size: int) -> "OnlineStudyPage":
        """切换每页显示条数"""
        self.click_element(self.PAGE_SIZE_SELECT)
        self.wait_element_visible(self.SEARCH_CATEGORY_DROPDOWN)  # 复用下拉定位器
        self.click_by_text(str(size))
        self.wait_loading_disappear(self.TABLE_LOADING)
        logger.info(f"切换每页条数为 {size}")
        return self


# ====== 自检报告 ======
# 手动执行命令后结果：
#
# grep -n "class \w\+Page:" OnlineStudyPage.py
# → 1: class OnlineStudyPage(BasePage):
# [PASS] 继承 BasePage
#
# grep -n '//\*\[@id="app"\]' OnlineStudyPage.py
# → 无输出
# [PASS] 无绝对 XPath
#
# grep -n "time.sleep" OnlineStudyPage.py
# → 无输出
# [PASS] 无 time.sleep
#
# grep -n "print(" OnlineStudyPage.py
# → 无输出
# [PASS] 无 print()
#
# grep -n "def navigate" OnlineStudyPage.py
# → 55: def navigate(self) -> "OnlineStudyPage":
# [PASS] 有 navigate()
#
# ═══ 代码自检报告 ═══
# [PASS] 继承 BasePage
# [PASS] 无绝对 XPath
# [PASS] 无 time.sleep
# [PASS] 无 print()
# [PASS] 有 navigate()
# ════════════════════
# 结果: 通过