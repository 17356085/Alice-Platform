# page/personnel_page/qualification_manage_page.py
"""资质管理页面 Page Object

对应模块: personnel (人员管理)
页面类型: 列表页 + 弹窗表单

变更记录:
  2026-06-18: 基于 PAGE_CONTEXT.md 生成
"""

from selenium.webdriver.common.by import By

from base.base_page import BasePage


class QualificationManagePage(BasePage):
    """资质管理页面操作类"""

    # ==================== 导航定位器 ====================
    # 侧边栏导航项 (假设使用 SidebarNavigator)
    # SIDEBAR_NAV = (By.XPATH, "//span[text()='资质管理']/..")

    # ==================== 搜索区定位器 ====================
    SEARCH_NAME_INPUT = (By.CSS_SELECTOR, ".search-area input[placeholder*='资质名称']")
    SEARCH_TYPE_SELECT = (By.CSS_SELECTOR, ".search-area .el-select .el-select__wrapper")
    SEARCH_STATUS_SELECT = (By.CSS_SELECTOR, ".search-area .el-select:nth-child(2) .el-select__wrapper")
    SEARCH_DATE_PICKER = (By.CSS_SELECTOR, ".search-area .el-date-editor--daterange")
    SEARCH_BUTTON = (By.XPATH, "//button[.//span[text()='搜索']]")
    RESET_BUTTON = (By.XPATH, "//button[.//span[text()='重置']]")

    # ==================== 表格区定位器 ====================
    ADD_BUTTON = (By.XPATH, "//button[.//span[text()='新增资质']]")
    TABLE_QUALIFICATION = (By.CSS_SELECTOR, ".el-table")
    TABLE_LOADING = (By.CSS_SELECTOR, ".el-table--loading")
    TABLE_EMPTY = (By.CSS_SELECTOR, ".el-table__empty-text")
    TABLE_ROWS = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr.el-table__row")
    # 行内操作按钮 (通过相对XPath从指定行索引定位)
    # 示例: 第n行的编辑按钮，btn-edit作为基础定位器
    ACTION_EDIT_BTN = (By.XPATH, ".//button[.//span[text()='编辑']]")
    ACTION_DELETE_BTN = (By.XPATH, ".//button[.//span[text()='删除']]")
    ACTION_VIEW_BTN = (By.XPATH, ".//button[.//span[text()='查看详情']]")

    # ==================== 分页区定位器 ====================
    PAGINATION = (By.CSS_SELECTOR, ".el-pagination")
    PAGINATION_TOTAL = (By.CSS_SELECTOR, ".el-pagination__total")
    PAGINATION_PAGE_SIZE = (By.CSS_SELECTOR, ".el-pagination__sizes .el-select")
    PAGINATION_NEXT_BTN = (By.CSS_SELECTOR, ".el-pagination .btn-next")
    PAGINATION_PREV_BTN = (By.CSS_SELECTOR, ".el-pagination .btn-prev")

    # ==================== 弹窗区定位器 ====================
    DIALOG_QUALIFICATION = (By.CSS_SELECTOR, ".el-dialog[role='dialog']")
    DIALOG_TITLE = (By.CSS_SELECTOR, ".el-dialog__title")
    DIALOG_NAME_INPUT = (By.CSS_SELECTOR, ".el-dialog .el-form-item .el-input__inner")
    DIALOG_TYPE_SELECT = (By.CSS_SELECTOR, ".el-dialog .el-select .el-select__wrapper")
    DIALOG_ISSUER_INPUT = (By.CSS_SELECTOR, ".el-dialog .el-form-item:nth-child(3) .el-input__inner")
    DIALOG_OBTAIN_DATE = (By.CSS_SELECTOR, ".el-dialog .el-form-item:nth-child(4) .el-date-editor")
    DIALOG_EXPIRY_DATE = (By.CSS_SELECTOR, ".el-dialog .el-form-item:nth-child(5) .el-date-editor")
    DIALOG_REMARK_TEXTAREA = (By.CSS_SELECTOR, ".el-dialog .el-textarea__inner")
    DIALOG_SAVE_BTN = (By.XPATH, "//div[contains(@class, 'el-dialog')]//button[contains(@class, 'el-button--primary')]")
    DIALOG_CANCEL_BTN = (By.XPATH, "//div[contains(@class, 'el-dialog')]//button[.//span[text()='取消']]")

    # ==================== 页面操作 ====================
    def navigate(self):
        """JS hash 导航到资质管理页面（SPA 内无刷新）"""
        logger.info("导航到：人员管理 > 资质管理")
        self.driver.execute_script("window.location.hash = '#/personnel/qualification'")
        self.wait_vue_stable()
        return self

    # ---------- 搜索操作 ----------
    def search(self, name: str = None, q_type: str = None, status: str = None):
        """
        执行搜索操作

        Args:
            name: 资质名称关键词
            q_type: 资质类型（如：学历证书）
            status: 资质状态（如：有效）
        """
        logger.info(f"执行搜索: name='{name}', type='{q_type}', status='{status}'")
        if name is not None:
            self.input_text(self.SEARCH_NAME_INPUT, name)
        if q_type is not None:
            self.click_element(self.SEARCH_TYPE_SELECT)
            self.click_element((By.XPATH, f"//li[contains(@class, 'el-select__item') and .//span[text()='{q_type}']]"))
        if status is not None:
            self.click_element(self.SEARCH_STATUS_SELECT)
            self.click_element((By.XPATH, f"//div[@id='el-popper-container']//li[.//span[text()='{status}']]"))
        self.click_element(self.SEARCH_BUTTON)
        return self

    def reset_search(self):
        """重置搜索条件"""
        logger.info("重置搜索条件")
        self.click_element(self.RESET_BUTTON)
        return self

    # ---------- 表格操作 ----------
    def get_table_data(self) -> list:
        """获取表格所有行的数据"""
        logger.info("获取表格数据")
        # 等待表格数据加载完成（先等待加载动画消失）
        self.wait_element_hide(self.TABLE_LOADING, timeout=10)
        rows = self.find_elements(self.TABLE_ROWS)
        if not rows:
            logger.warning("表格无数据或未找到表格行")
            return []
        # 使用 BasePage 提供的通用表格数据提取方法
        return self.get_table_all_rows_data(self.TABLE_QUALIFICATION)

    def click_add(self):
        """点击新增按钮"""
        logger.info("点击【新增资质】按钮")
        self.click_element(self.ADD_BUTTON)
        return self

    def click_view(self, row_index: int):
        """点击指定行的【查看详情】

        Args:
            row_index: 行索引（从0开始）
        """
        logger.info(f"点击第 {row_index + 1} 行的【查看详情】")
        row = self.find_elements(self.TABLE_ROWS)[row_index]
        view_btn = row.find_element(*self.ACTION_VIEW_BTN)
        view_btn.click()
        return self

    def click_edit(self, row_index: int):
        """点击指定行的【编辑】

        Args:
            row_index: 行索引（从0开始）
        """
        logger.info(f"点击第 {row_index + 1} 行的【编辑】")
        row = self.find_elements(self.TABLE_ROWS)[row_index]
        edit_btn = row.find_element(*self.ACTION_EDIT_BTN)
        edit_btn.click()
        return self

    def click_delete(self, row_index: int):
        """点击指定行的【删除】并确认

        Args:
            row_index: 行索引（从0开始）
        """
        logger.info(f"点击第 {row_index + 1} 行的【删除】")
        row = self.find_elements(self.TABLE_ROWS)[row_index]
        delete_btn = row.find_element(*self.ACTION_DELETE_BTN)
        delete_btn.click()
        # 弹出删除确认框，通过 BasePage 的通用方法点击确认
        self.confirm_dialog()
        return self

    def open_add_dialog(self):
        """打开新增资质的弹窗（新增操作和fill_form组合）"""
        logger.info("打开新增资质弹窗")
        self.click_add()
        return self

    # ---------- 弹窗操作 ----------
    def fill_form(self, data: dict):
        """
        填写新增/编辑弹窗表单

        Args:
            data: 表单数据字典，格式如：
                {
                    'name': 'xxx',
                    'type': '职业资格',
                    'issuer': 'xxx部门',
                    'obtain_date': '2024-01-01',
                    'expiry_date': '2026-01-01',
                    'remark': '备注信息'
                }
        """
        logger.info(f"填写弹窗表单: {data}")
        for field, value in data.items():
            if value is None:
                continue
            if field == 'name':
                self.input_text(self.DIALOG_NAME_INPUT, value)
            elif field == 'type':
                self.click_element(self.DIALOG_TYPE_SELECT)
                # 选择下拉项（通过popper层内的文本匹配）
                option_locator = (By.XPATH, f"//div[@id='el-popper-container']//li[.//span[text()='{value}']]")
                self.click_element(option_locator)
            elif field == 'issuer':
                self.input_text(self.DIALOG_ISSUER_INPUT, value)
            elif field == 'obtain_date':
                self.input_text(self.DIALOG_OBTAIN_DATE, value)
            elif field == 'expiry_date':
                self.input_text(self.DIALOG_EXPIRY_DATE, value)
            elif field == 'remark':
                self.input_text(self.DIALOG_REMARK_TEXTAREA, value)
        return self

    def confirm_dialog(self):
        """点击弹窗中的【保存】按钮并等待弹窗关闭"""
        logger.info("确认弹窗（点击保存）")
        self.click_element(self.DIALOG_SAVE_BTN)
        # 等待弹窗关闭
        self.wait_element_hide(self.DIALOG_QUALIFICATION, timeout=10)
        return self

    def cancel_dialog(self):
        """点击弹窗中的【取消】按钮"""
        logger.info("取消弹窗（点击取消）")
        self.click_element(self.DIALOG_CANCEL_BTN)
        return self

    # ---------- 分页操作 ----------
    def get_pagination_info(self) -> dict:
        """获取分页信息

        Returns:
            {'total': int, 'page_size': int, 'current_page': int}
        """
        logger.info("获取分页信息")
        return self.get_pagination_data(self.PAGINATION)

    def switch_page(self, page_number: int):
        """切换到指定页码

        Args:
            page_number: 目标页码（从1开始）
        """
        logger.info(f"切换到第 {page_number} 页")
        # 点击对应的页码按钮
        page_btn = (By.XPATH, f"//ul[contains(@class, 'el-pager')]//li[text()='{page_number}']")
        self.click_element(page_btn)
        return self