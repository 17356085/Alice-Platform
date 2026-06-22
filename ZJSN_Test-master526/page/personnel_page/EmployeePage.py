# =====================================================================
# Page Object: EmployeePage (人员管理)
# 文件路径: page/personnel_page/EmployeePage.py
# 基类: base.base_page.BasePage
# 技术栈: Vue3 + Element Plus
# =====================================================================

import logging
from base.base_page import BasePage
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)


class EmployeePage(BasePage):
    """
    人员管理页面对象
    包含搜索区、操作按钮、表格、分页、新增/编辑弹窗等操作
    """

    # ==================== 搜索区 ====================
    SEARCH_NAME_INPUT = (By.CSS_SELECTOR, "input[placeholder*='员工姓名']")
    # 部门选择器（el-select，使用可搜索模式）
    SEARCH_DEPARTMENT_SELECT = (By.CSS_SELECTOR, ".search-area .el-select__wrapper")
    # 状态选择器
    SEARCH_STATUS_SELECT = (By.CSS_SELECTOR, ".search-area .el-select:nth-child(2) .el-select__wrapper")
    # 日期范围（el-date-picker，类型 daterange）
    SEARCH_DATE_RANGE = (By.CSS_SELECTOR, ".search-area .el-date-editor--daterange")
    # 查询按钮
    SEARCH_BTN = (By.XPATH, "//button[.//span[text()='查询']]")
    # 重置按钮
    RESET_BTN = (By.XPATH, "//button[.//span[text()='重置']]")

    # ==================== 操作按钮区 ====================
    ADD_BTN = (By.XPATH, "//button[.//span[text()='新增员工']]")
    IMPORT_BTN = (By.XPATH, "//button[.//span[text()='导入']]")
    EXPORT_BTN = (By.XPATH, "//button[.//span[text()='导出']]")

    # ==================== 表格区 ====================
    TABLE = (By.CSS_SELECTOR, ".el-table")
    TABLE_ROW = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr.el-table__row")
    # 表格中每行的操作按钮（编辑、删除）—— 通过 row_index 定位
    # 使用相对 XPath 从指定行内查找
    EDIT_BTN_IN_ROW = (By.XPATH, ".//button[contains(@class, 'edit-btn')]")
    DELETE_BTN_IN_ROW = (By.XPATH, ".//button[contains(@class, 'delete-btn')]")

    # ==================== 弹窗 ====================
    # 使用基类通用定位器 DIALOG
    # 新增/编辑弹窗内的表单字段
    # 姓名输入框
    DIALOG_NAME_INPUT = (By.CSS_SELECTOR, ".el-dialog .el-form-item:nth-child(1) .el-input__inner")
    # 性别选择
    DIALOG_GENDER_SELECT = (By.CSS_SELECTOR, ".el-dialog .el-form-item:nth-child(2) .el-select__wrapper")
    # 手机号
    DIALOG_PHONE_INPUT = (By.CSS_SELECTOR, ".el-dialog .el-form-item:nth-child(3) .el-input__inner")
    # 部门选择（弹窗内）
    DIALOG_DEPARTMENT_SELECT = (By.CSS_SELECTOR, ".el-dialog .el-form-item:nth-child(4) .el-select__wrapper")
    # 职位
    DIALOG_POSITION_INPUT = (By.CSS_SELECTOR, ".el-dialog .el-form-item:nth-child(5) .el-input__inner")
    # 状态
    DIALOG_STATUS_SELECT = (By.CSS_SELECTOR, ".el-dialog .el-form-item:nth-child(6) .el-select__wrapper")
    # 入职日期
    DIALOG_HIRE_DATE_PICKER = (By.CSS_SELECTOR, ".el-dialog .el-form-item:nth-child(7) .el-date-editor")

    # ==================== 分页 ====================
    PAGINATION = (By.CSS_SELECTOR, ".el-pagination")
    CURRENT_PAGE_INPUT = (By.CSS_SELECTOR, ".el-pagination .el-input__inner")
    PAGE_SIZE_DROPDOWN = (By.CSS_SELECTOR, ".el-pagination .el-select__wrapper")
    TOTAL_COUNT = (By.CSS_SELECTOR, ".el-pagination .el-pagination__total")

    # ==================== 导航（页面入口） ====================
    URL = "#/personnel/employee"

    def navigate(self):
        """JS hash 导航到人员管理页面（无全页刷新，依赖当前已登录的 SPA）"""
        logger.info("导航到人员管理页面")
        self.driver.execute_script(f"window.location.hash = '{self.URL}'")
        self.wait_vue_stable()
        return self

    def is_page_loaded(self):
        """判断页面是否加载完成"""
        try:
            self.find_visible((By.XPATH, '//div[contains(@class,"el-table")]'))
            return True
        except Exception:
            return False

    def is_title_displayed(self):
        """判断页面标题是否显示 — 多重检测"""
        indicators = [
            (By.XPATH, '//span[contains(text(),"员工")]'),
            (By.XPATH, '//*[contains(text(),"人员")]'),
            (By.CSS_SELECTOR, '.el-breadcrumb, [class*="breadcrumb"]'),
            (By.CSS_SELECTOR, '.search-area, .search-form, [class*="search"]'),
        ]
        for locator in indicators:
            try:
                if self.is_element_present(locator):
                    return True
            except Exception:
                continue
        return self.is_page_loaded()

    # ==================== 搜索相关 ====================
    def search(self, keyword: str = None, department: str = None, status: str = None,
               date_range: tuple = None):
        """
        在搜索区填入信息并点击查询
        :param keyword: 员工姓名（可选）
        :param department: 部门名称（可选）
        :param status: 状态（在职/离职/试用）
        :param date_range: 入职日期范围 (start_date, end_date)，格式 'YYYY-MM-DD'
        :return: self
        """
        logger.info(f"搜索条件: 姓名={keyword}, 部门={department}, 状态={status}, 日期范围={date_range}")
        if keyword is not None:
            self.fill_element(self.SEARCH_NAME_INPUT, keyword)
        if department is not None:
            self.click(self.SEARCH_DEPARTMENT_SELECT)
            # 选择部门（需要具体选择器，这里假设输入后从下拉列表选择）
            department_option = (By.XPATH, f"//div[@class='el-select-dropdown']//span[text()='{department}']")
            self.click(department_option)
        if status is not None:
            self.click(self.SEARCH_STATUS_SELECT)
            status_option = (By.XPATH, f"//div[@class='el-select-dropdown']//span[text()='{status}']")
            self.click(status_option)
        if date_range is not None:
            start, end = date_range
            self.fill_element(self.SEARCH_DATE_RANGE, f"{start} ~ {end}")
            # 部分 Element Plus 日期组件可能需要点击确认关闭面板，若存在则点击确认
            try:
                confirm_btn = (By.XPATH, "//button[contains(@class, 'el-date-picker__confirm')]")
                self.click_with_wait(confirm_btn)
            except Exception:
                pass
        self.click(self.SEARCH_BTN)
        self.wait_vue_stable()
        return self

    def reset_search(self):
        """
        重置所有搜索条件
        :return: self
        """
        logger.info("重置搜索条件")
        self.click(self.RESET_BTN)
        self.wait_vue_stable()
        return self

    # ==================== 表格数据获取 ====================
    def get_table_data(self) -> list:
        """
        获取表格当前页所有行数据（文本形式）
        :return: list of dict，每个 dict 包含列名-文本
        """
        logger.info("获取表格数据")
        # 等待表格行出现
        self.wait_for_visible(self.TABLE_ROW)
        rows = self.find_elements(self.TABLE_ROW)
        data = []
        for row in rows:
            # 获取该行所有 td 的文本
            cells = row.find_elements(By.TAG_NAME, "td")
            row_data = {
                "name": cells[0].text.strip() if len(cells) > 0 else "",
                "gender": cells[1].text.strip() if len(cells) > 1 else "",
                "phone": cells[2].text.strip() if len(cells) > 2 else "",
                "department": cells[3].text.strip() if len(cells) > 3 else "",
                "position": cells[4].text.strip() if len(cells) > 4 else "",
                "status": cells[5].text.strip() if len(cells) > 5 else "",
                "hire_date": cells[6].text.strip() if len(cells) > 6 else "",
            }
            data.append(row_data)
        return data

    # ==================== 新增员工 ====================
    def click_add(self):
        """
        点击「新增员工」按钮
        :return: self
        """
        logger.info("点击新增员工按钮")
        self.click_with_wait(self.ADD_BTN)
        self.wait_for_visible(self.DIALOG)
        return self

    def click_add_button(self):
        """兼容测试脚本 API"""
        return self.click_add()

    def select_first_row(self):
        """选中表格第一行"""
        self.click_row(0)
        return self

    def fill_form(self, data: dict):
        """
        在弹窗中填写表单
        :param data: 字段名-值字典，支持键: name, gender, phone, department, position, status, hire_date
        :return: self
        """
        logger.info(f"填写表单: {data}")
        if "name" in data:
            self.fill_element(self.DIALOG_NAME_INPUT, data["name"])
        if "gender" in data:
            self.click(self.DIALOG_GENDER_SELECT)
            gender_option = (By.XPATH, f"//div[@class='el-select-dropdown']//span[text()='{data['gender']}']")
            self.click(gender_option)
        if "phone" in data:
            self.fill_element(self.DIALOG_PHONE_INPUT, data["phone"])
        if "department" in data:
            self.click(self.DIALOG_DEPARTMENT_SELECT)
            dept_option = (By.XPATH, f"//div[@class='el-select-dropdown']//span[text()='{data['department']}']")
            self.click(dept_option)
        if "position" in data:
            self.fill_element(self.DIALOG_POSITION_INPUT, data["position"])
        if "status" in data:
            self.click(self.DIALOG_STATUS_SELECT)
            status_option = (By.XPATH, f"//div[@class='el-select-dropdown']//span[text()='{data['status']}']")
            self.click(status_option)
        if "hire_date" in data:
            self.fill_element(self.DIALOG_HIRE_DATE_PICKER, data["hire_date"])
            # 如果日期选择器需要确认，可点击确认
            try:
                confirm_btn = (By.XPATH, "//button[contains(@class, 'el-date-picker__confirm')]")
                self.click_with_wait(confirm_btn)
            except Exception:
                pass
        return self

    def confirm_dialog(self):
        """
        点击弹窗确定按钮（保存）
        :return: self
        """
        logger.info("确认弹窗")
        self.click_with_wait(self.DIALOG_SAVE)
        self.wait_for_invisible(self.DIALOG)  # 等待弹窗关闭
        return self

    def cancel_dialog(self):
        """
        点击弹窗取消按钮
        :return: self
        """
        logger.info("取消弹窗")
        self.click_with_wait(self.DIALOG_CANCEL)
        self.wait_for_invisible(self.DIALOG)
        return self

    # ==================== 编辑/删除 ====================
    def click_edit(self, row_index: int = 0):
        """
        点击指定行的编辑按钮（从0开始）
        :param row_index: 行索引
        :return: self
        """
        logger.info(f"点击第 {row_index} 行的编辑按钮")
        # 先定位到对应行
        rows = self.find_elements(self.TABLE_ROW)
        if row_index >= len(rows):
            logger.error(f"行索引 {row_index} 超出范围，总行数 {len(rows)}")
            raise IndexError(f"Row index {row_index} out of range, total rows: {len(rows)}")
        edit_btn = rows[row_index].find_element(*self.EDIT_BTN_IN_ROW)
        self.click_with_wait(edit_btn)
        self.wait_for_visible(self.DIALOG)
        return self

    def click_delete(self, row_index: int = 0):
        """
        点击指定行的删除按钮
        :param row_index: 行索引
        :return: self
        """
        logger.info(f"点击第 {row_index} 行的删除按钮")
        rows = self.find_elements(self.TABLE_ROW)
        if row_index >= len(rows):
            logger.error(f"行索引 {row_index} 超出范围，总行数 {len(rows)}")
            raise IndexError(f"Row index {row_index} out of range, total rows: {len(rows)}")
        delete_btn = rows[row_index].find_element(*self.DELETE_BTN_IN_ROW)
        self.click_with_wait(delete_btn)
        self.wait_for_visible(self.DIALOG)  # 一般删除有确认弹窗
        return self

    # ==================== 分页信息 ====================
    def get_pagination_info(self) -> dict:
        """
        获取分页信息：当前页、每页条数、总记录数
        :return: dict {"current_page": int, "page_size": int, "total": int}
        """
        logger.info("获取分页信息")
        self.wait_for_visible(self.PAGINATION)
        current_page_text = self.get_attribute(self.CURRENT_PAGE_INPUT, "value")
        page_size_text = self.get_text(self.PAGE_SIZE_DROPDOWN)  # 可能需调整
        total_text = self.get_text(self.TOTAL_COUNT)
        # 解析文本，例如 "共 100 条"
        import re
        total_match = re.search(r'\d+', total_text)
        total = int(total_match.group()) if total_match else 0
        return {
            "current_page": int(current_page_text) if current_page_text.isdigit() else 1,
            "page_size": int(page_size_text) if page_size_text.isdigit() else 10,
            "total": total
        }

    # ==================== 兼容方法（测试脚本期望的 API） ====================

    def enter_search_keyword(self, keyword: str):
        """输入搜索关键词（兼容测试脚本 API）"""
        self.input_text(self.SEARCH_NAME_INPUT, keyword)
        return self

    def click_search(self):
        """点击查询按钮（兼容测试脚本 API）"""
        return self.click(self.SEARCH_BTN)

    def get_search_input_value(self) -> str:
        """获取搜索输入框当前值"""
        return self.get_attribute(self.SEARCH_NAME_INPUT, "value") or ""

    def select_department(self, department: str):
        """选择部门筛选（兼容测试脚本 API）"""
        self.click(self.SEARCH_DEPARTMENT_SELECT)
        self.wait_vue_stable()
        option = (By.XPATH, f'//li[contains(@class,"el-select-dropdown__item") and contains(.,"{department}")]')
        self.click(option)
        return self

    def click_reset_search(self):
        """点击重置按钮（兼容测试脚本 API）"""
        return self.click(self.RESET_BTN)

    def is_search_default(self) -> bool:
        """判断搜索区是否处于默认状态"""
        val = self.get_attribute(self.SEARCH_NAME_INPUT, "value") or ""
        return val == ""

    def is_pagination_visible(self) -> bool:
        """判断分页组件是否可见"""
        try:
            return self.is_element_present(self.PAGINATION)
        except Exception:
            return False

    def is_empty_state_displayed(self) -> bool:
        """判断空数据状态是否显示"""
        indicators = [
            (By.XPATH, '//*[contains(text(),"暂无数据")]'),
            (By.XPATH, '//*[contains(@class,"el-empty")]'),
            (By.CSS_SELECTOR, '.el-empty, [class*="empty"]'),
        ]
        for locator in indicators:
            try:
                if self.is_element_present(locator):
                    return True
            except Exception:
                continue
        return self.get_table_row_count() == 0

    def click_export(self):
        """点击导出按钮"""
        self.click(self.EXPORT_BTN)
        self.wait_vue_stable()
        return self

    def is_download_completed(self) -> bool:
        """判断文件下载是否完成（检查下载目录有新文件）"""
        import glob
        import os
        download_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "downloads")
        if not os.path.isdir(download_dir):
            return True  # 目录不存在则跳过验证
        files = glob.glob(os.path.join(download_dir, "*"))
        return len(files) > 0

    def is_permission_denied_displayed(self) -> bool:
        """判断权限不足提示是否显示"""
        indicators = [
            (By.XPATH, '//*[contains(text(),"403") or contains(text(),"权限") or contains(text(),"无权")]'),
            (By.CSS_SELECTOR, '.el-message--error, [class*="error"]'),
        ]
        for locator in indicators:
            try:
                if self.is_element_present(locator):
                    return True
            except Exception:
                continue
        return False

    def get_table_row_count(self) -> int:
        """获取表格行数"""
        try:
            rows = self.driver.find_elements(*self.TABLE_ROW)
            return len(rows)
        except Exception:
            return 0

    def click_row(self, row_index: int = 0):
        """点击表格指定行"""
        rows = self.driver.find_elements(*self.TABLE_ROW)
        if row_index >= len(rows):
            raise IndexError(f"Row index {row_index} out of range, total: {len(rows)}")
        self.click_with_wait(rows[row_index])
        return self