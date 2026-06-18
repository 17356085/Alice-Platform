"""访客管理页面 Page Object

模块: personnel
页面: visitor

变更记录:
    2026-06-18: 基于 PAGE_CONTEXT.md 创建。
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from base.base_page import BasePage


class VisitorPage(BasePage):
    """访客管理页面操作类"""

    # ==================== 搜索区 ====================
    SEARCH_VISITOR_NAME_INPUT = (By.CSS_SELECTOR, "input[placeholder*='访客姓名']")
    SEARCH_PHONE_INPUT = (By.CSS_SELECTOR, "input[placeholder*='手机号']")
    SEARCH_STATUS_SELECT = (By.CSS_SELECTOR, ".search-area .el-select .el-input__inner")
    SEARCH_VISIT_DATE_RANGE = (By.CSS_SELECTOR, ".el-date-editor--daterange .el-input__inner")
    SEARCH_INTERVIEWER_INPUT = (By.CSS_SELECTOR, "input[placeholder*='被访人']")
    SEARCH_BTN = (By.XPATH, "//button[.//span[text()='搜索']]")
    RESET_BTN = (By.XPATH, "//button[.//span[text()='重置']]")

    # ==================== 工具栏 ====================
    ADD_BTN = (By.XPATH, "//button[.//span[text()='新增访客']]")
    IMPORT_BTN = (By.XPATH, "//button[.//span[text()='批量导入']]")
    EXPORT_BTN = (By.XPATH, "//button[.//span[text()='导出']]")

    # ==================== 表格区 ====================
    TABLE = (By.CSS_SELECTOR, ".el-table")
    TABLE_BODY_ROWS = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr")
    TABLE_ROW_CELLS = (By.CSS_SELECTOR, "td.el-table__cell")
    TABLE_STATUS_TAG = (By.CSS_SELECTOR, ".el-table .el-tag")

    # ==================== 分页区 ====================
    PAGINATION_TOTAL = (By.CSS_SELECTOR, ".el-pagination__total")
    PAGINATION_PAGE_SIZE_SELECT = (By.CSS_SELECTOR, ".el-pagination .el-select .el-input__inner")
    PAGINATION_PAGER = (By.CSS_SELECTOR, ".el-pager li.number")
    PAGINATION_ACTIVE_PAGE = (By.CSS_SELECTOR, ".el-pager li.number.active")
    PAGINATION_NEXT_BTN = (By.CSS_SELECTOR, ".el-pagination .btn-next")
    PAGINATION_PREV_BTN = (By.CSS_SELECTOR, ".el-pagination .btn-prev")
    PAGINATION_GOTO_INPUT = (By.CSS_SELECTOR, ".el-pagination__jump .el-input__inner")

    # ==================== 弹窗（新增/编辑/查看） ====================
    DIALOG = (By.CSS_SELECTOR, ".el-dialog")
    DIALOG_TITLE = (By.CSS_SELECTOR, ".el-dialog__title")
    DIALOG_CLOSE_BTN = (By.CSS_SELECTOR, ".el-dialog__headerbtn .el-dialog__close")
    DIALOG_CONFIRM_BTN = (By.CSS_SELECTOR, ".el-dialog .el-button--primary")
    DIALOG_CANCEL_BTN = (By.XPATH, "//div[contains(@class, 'el-dialog')]//button[.//span[text()='取 消']]")

    FORM_VISITOR_NAME_INPUT = (By.CSS_SELECTOR, ".el-dialog input[placeholder*='访客姓名']")
    FORM_COMPANY_INPUT = (By.CSS_SELECTOR, ".el-dialog input[placeholder*='所属单位']")
    FORM_PHONE_INPUT = (By.CSS_SELECTOR, ".el-dialog input[placeholder*='手机号']")
    FORM_INTERVIEWER_INPUT = (By.CSS_SELECTOR, ".el-dialog input[placeholder*='被访人']")
    FORM_VISIT_PURPOSE_INPUT = (By.CSS_SELECTOR, ".el-dialog input[placeholder*='来访事由']")

    # ==================== 行内操作按钮定位（动态生成） ====================
    def _row_edit_btn(self, row_index: int):
        """获取指定行编辑按钮的定位器"""
        return (By.XPATH,
                f"({self.TABLE_BODY_ROWS[1]})[{row_index + 1}]//button[.//span[text()='编辑']]")

    def _row_view_btn(self, row_index: int):
        """获取指定行查看按钮的定位器"""
        return (By.XPATH,
                f"({self.TABLE_BODY_ROWS[1]})[{row_index + 1}]//button[.//span[text()='查看']]")

    def _row_delete_btn(self, row_index: int):
        """获取指定行删除按钮的定位器"""
        return (By.XPATH,
                f"({self.TABLE_BODY_ROWS[1]})[{row_index + 1}]//button[.//span[text()='删除']]")

    def _row_force_logout_btn(self, row_index: int):
        """获取指定行强制离场按钮的定位器（仅对在访状态有效）"""
        return (By.XPATH,
                f"({self.TABLE_BODY_ROWS[1]})[{row_index + 1}]//button[.//span[text()='强制离场']]")

    # ==================== 页面入口 ====================

    def navigate(self):
        """导航到访客管理页面"""
        self.logger.info("导航到访客管理页面")
        self.navigate_to("人员管理", "访客管理")
        self.wait_vue_stable()
        return self

    # ==================== 搜索操作 ====================

    def search(self, keyword: str = None, phone: str = None, interviewer: str = None):
        """
        根据提供的参数进行搜索

        Args:
            keyword: 访客姓名/单位
            phone: 手机号
            interviewer: 被访人
        """
        self.logger.info(f"执行搜索: keyword={keyword}, phone={phone}, interviewer={interviewer}")
        if keyword:
            self.wait_element_visible(self.SEARCH_VISITOR_NAME_INPUT)
            self.find_element(self.SEARCH_VISITOR_NAME_INPUT).clear()
            self.find_element(self.SEARCH_VISITOR_NAME_INPUT).send_keys(keyword)
        if phone:
            self.wait_element_visible(self.SEARCH_PHONE_INPUT)
            self.find_element(self.SEARCH_PHONE_INPUT).clear()
            self.find_element(self.SEARCH_PHONE_INPUT).send_keys(phone)
        if interviewer:
            self.wait_element_visible(self.SEARCH_INTERVIEWER_INPUT)
            self.find_element(self.SEARCH_INTERVIEWER_INPUT).clear()
            self.find_element(self.SEARCH_INTERVIEWER_INPUT).send_keys(interviewer)
        self.wait_element_clickable(self.SEARCH_BTN).click()
        self.wait_vue_stable()
        return self

    def search_by_status(self, status_text: str):
        """按来访状态搜索"""
        self.logger.info(f"按状态搜索: {status_text}")
        self.wait_element_clickable(self.SEARCH_STATUS_SELECT).click()
        status_option = (By.XPATH, f"//div[contains(@class, 'el-select-dropdown')]//span[text()='{status_text}']")
        self.wait_element_clickable(status_option).click()
        self.wait_vue_stable()
        return self

    def search_by_date_range(self, start_date: str, end_date: str):
        """按来访日期范围搜索"""
        self.logger.info(f"按日期范围搜索: {start_date} ~ {end_date}")
        self.wait_element_clickable(self.SEARCH_VISIT_DATE_RANGE).click()
        date_inputs = self.find_elements(self.SEARCH_VISIT_DATE_RANGE)
        if len(date_inputs) >= 2:
            date_inputs[0].clear()
            date_inputs[0].send_keys(start_date)
            date_inputs[1].clear()
            date_inputs[1].send_keys(end_date)
            date_inputs[1].send_keys(Keys.ENTER)
        self.wait_vue_stable()
        return self

    def reset_search(self):
        """重置搜索条件"""
        self.logger.info("重置搜索条件")
        self.wait_element_clickable(self.RESET_BTN).click()
        self.wait_vue_stable()
        return self

    # ==================== 表格数据获取 ====================

    def get_table_data(self):
        """
        获取表格中所有行的文本数据

        Returns:
            list[dict]: 每行数据字典，key为列索引（从0开始）
        """
        self.logger.info("获取表格数据")
        rows = self.wait_elements_visible(self.TABLE_BODY_ROWS)
        table_data = []
        for row in rows:
            cells = row.find_elements(*self.TABLE_ROW_CELLS)
            row_data = {}
            for index, cell in enumerate(cells):
                row_data[index] = cell.text
            table_data.append(row_data)
        self.logger.info(f"获取到 {len(table_data)} 行表格数据")
        return table_data

    # ==================== 表格行操作 ====================

    def click_edit(self, row_index: int):
        """
        点击指定行的编辑按钮

        Args:
            row_index: 行索引（从0开始）
        """
        self.logger.info(f"编辑第 {row_index + 1} 行数据")
        edit_btn_locator = self._row_edit_btn(row_index)
        self.wait_element_clickable(edit_btn_locator).click()
        return self

    def click_view(self, row_index: int):
        """
        点击指定行的查看按钮

        Args:
            row_index: 行索引（从0开始）
        """
        self.logger.info(f"查看第 {row_index + 1} 行数据")
        view_btn_locator = self._row_view_btn(row_index)
        self.wait_element_clickable(view_btn_locator).click()
        return self

    def click_delete(self, row_index: int):
        """
        点击指定行的删除按钮

        Args:
            row_index: 行索引（从0开始）
        """
        self.logger.info(f"删除第 {row_index + 1} 行数据")
        delete_btn_locator = self._row_delete_btn(row_index)
        self.wait_element_clickable(delete_btn_locator).click()
        return self

    def click_force_logout(self, row_index: int):
        """
        点击指定行的强制离场按钮

        Args:
            row_index: 行索引（从0开始）
        """
        self.logger.info(f"对第 {row_index + 1} 行数据执行强制离场")
        force_logout_btn_locator = self._row_force_logout_btn(row_index)
        self.wait_element_clickable(force_logout_btn_locator).click()
        return self

    # ==================== 新增/编辑弹窗操作 ====================

    def click_add(self):
        """点击新增访客按钮，打开新增弹窗"""
        self.logger.info("点击新增访客按钮")
        self.wait_element_clickable(self.ADD_BTN).click()
        self.wait_element_visible(self.DIALOG)
        return self

    def fill_dialog_form(self, data_dict: dict):
        """
        在弹窗表单中填写数据

        Args:
            data_dict: 表单数据，key必须与表单字段的placeholder匹配（如'访客姓名'、'所属单位'）
                       或使用特定key: visitor_name, company, phone, interviewer, visit_purpose
        """
        self.logger.info(f"填写弹窗表单: {data_dict}")
        if "访客姓名" in data_dict or "visitor_name" in data_dict:
            self.wait_element_visible(self.FORM_VISITOR_NAME_INPUT)
            input_el = self.find_element(self.FORM_VISITOR_NAME_INPUT)
            input_el.clear()
            input_el.send_keys(data_dict.get("visitor_name", data_dict.get("访客姓名")))
        if "所属单位" in data_dict or "company" in data_dict:
            self.wait_element_visible(self.FORM_COMPANY_INPUT)
            input_el = self.find_element(self.FORM_COMPANY_INPUT)
            input_el.clear()
            input_el.send_keys(data_dict.get("company", data_dict.get("所属单位")))
        if "手机号" in data_dict or "phone" in data_dict:
            self.wait_element_visible(self.FORM_PHONE_INPUT)
            input_el = self.find_element(self.FORM_PHONE_INPUT)
            input_el.clear()
            input_el.send_keys(data_dict.get("phone", data_dict.get("手机号")))
        if "被访人" in data_dict or "interviewer" in data_dict:
            self.wait_element_visible(self.FORM_INTERVIEWER_INPUT)
            input_el = self.find_element(self.FORM_INTERVIEWER_INPUT)
            input_el.clear()
            input_el.send_keys(data_dict.get("interviewer", data_dict.get("被访人")))
        if "来访事由" in data_dict or "visit_purpose" in data_dict:
            self.wait_element_visible(self.FORM_VISIT_PURPOSE_INPUT)
            input_el = self.find_element(self.FORM_VISIT_PURPOSE_INPUT)
            input_el.clear()
            input_el.send_keys(data_dict.get("visit_purpose", data_dict.get("来访事由")))
        return self

    def confirm_dialog(self):
        """点击弹窗中的确定按钮"""
        self.logger.info("确认弹窗")
        self.wait_element_clickable(self.DIALOG_CONFIRM_BTN).click()
        return self

    def cancel_dialog(self):
        """点击弹窗中的取消按钮"""
        self.logger.info("取消弹窗")
        self.wait_element_clickable(self.DIALOG_CANCEL_BTN).click()
        return self

    def close_dialog(self):
        """点击弹窗右上角的关闭按钮"""
        self.logger.info("关闭弹窗")
        self.wait_element_clickable(self.DIALOG_CLOSE_BTN).click()
        return self

    # ==================== 二次确认弹窗（如删除确认） ====================
    CONFIRM_DIALOG = (By.CSS_SELECTOR, ".el-message-box")
    CONFIRM_DIALOG_YES_BTN = (By.XPATH, "//div[contains(@class, 'el-message-box')]//button[.//span[text()='确定']]")
    CONFIRM_DIALOG_NO_BTN = (By.XPATH, "//div[contains(@class, 'el-message-box')]//button[.//span[text()='取消']]")

    def confirm_delete(self):
        """在删除二次确认弹窗中点击确定"""
        self.logger.info("确认删除操作")
        self.wait_element_clickable(self.CONFIRM_DIALOG_YES_BTN).click()
        return self

    def cancel_delete(self):
        """在删除二次确认弹窗中点击取消"""
        self.logger.info("取消删除操作")
        self.wait_element_clickable(self.CONFIRM_DIALOG_NO_BTN).click()
        return self

    # ==================== 分页操作 ====================

    def get_pagination_info(self):
        """
        获取分页信息

        Returns:
            dict: 包含'total'和'current_page'的字典
        """
        total_text = self.wait_element_visible(self.PAGINATION_TOTAL).text
        total = int(''.join(filter(str.isdigit, total_text))) if total_text else 0
        page_text = self.wait_element_visible(self.PAGINATION_ACTIVE_PAGE).text
        current_page = int(page_text) if page_text else 1
        return {"total": total, "current_page": current_page}

    def go_to_page(self, page_num: int):
        """
        跳转到指定页

        Args:
            page_num: 页码
        """
        self.logger.info(f"跳转到第 {page_num} 页")
        self.wait_element_visible(self.PAGINATION_GOTO_INPUT).clear()
        self.wait_element_visible(self.PAGINATION_GOTO_INPUT).send_keys(str(page_num))
        self.wait_element_visible(self.PAGINATION_GOTO_INPUT).send_keys(Keys.ENTER)
        self.wait_vue_stable()
        return self

    def click_next_page(self):
        """点击下一页"""
        self.logger.info("点击下一页")
        self.wait_element_clickable(self.PAGINATION_NEXT_BTN).click()
        self.wait_vue_stable()
        return self

    def click_prev_page(self):
        """点击上一页"""
        self.logger.info("点击上一页")
        self.wait_element_clickable(self.PAGINATION_PREV_BTN).click()
        self.wait_vue_stable()
        return self