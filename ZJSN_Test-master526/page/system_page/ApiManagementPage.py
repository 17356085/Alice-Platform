# =============================================================================
# File: page/system_page/api_management_page/ApiManagementPage.py
# Description: API管理页面的Page Object
# =============================================================================
from base.base_page import BasePage
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from typing import List, Dict, Any
import logging

class ApiManagementPage(BasePage):
    """
    系统管理 -> API 管理 页面对象
    
    封装了API管理页面的所有交互操作，包括搜索、增删改查等。
    """

    # ==================== 1. 定位器定义 ====================
    # --- 搜索区 ---
    SEARCH_NAME_INPUT = (By.CSS_SELECTOR, "input[placeholder*='API名称']")
    SEARCH_METHOD_SELECT = (By.CSS_SELECTOR, ".search-area .el-select:first-child")  # 假设第一个下拉是请求方法
    SEARCH_STATUS_SELECT = (By.CSS_SELECTOR, ".search-area .el-select:last-child")   # 假设第二个下拉是状态
    SEARCH_BTN = (By.XPATH, "//button[.//span[text()='搜索']]")
    RESET_BTN = (By.XPATH, "//button[.//span[text()='重置']]")

    # --- 操作按钮 ---
    ADD_API_BTN = (By.XPATH, "//button[.//span[text()='新增API']]")

    # --- 表格区 ---
    TABLE_BODY = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody")
    TABLE_ROW = (By.CSS_SELECTOR, ".el-table__row")
    TABLE_CELL = (By.CSS_SELECTOR, ".cell")
    # 操作列按钮 (相对定位，需要在行元素上使用)
    EDIT_BTN_IN_ROW = (By.XPATH, ".//button[contains(@class, 'el-button--primary')]")
    DELETE_BTN_IN_ROW = (By.XPATH, ".//button[contains(@class, 'el-button--danger')]")

    # --- 分页区 ---
    PAGINATION = (By.CSS_SELECTOR, ".el-pagination")
    PAGINATION_INFO = (By.CSS_SELECTOR, ".el-pagination__total")  # 或 .el-pagination__jump
    PAGE_SIZE_SELECTOR = (By.CSS_SELECTOR, ".el-pagination .el-select .el-input__inner")
    PAGE_NUM_INPUT = (By.CSS_SELECTOR, ".el-pagination__jump input")

    # --- 弹窗区 (部分引用BasePage通用定位器) ---
    # DIALOG = (By.CSS_SELECTOR, ".el-dialog")  # In BasePage
    # DIALOG_TITLE = (By.CSS_SELECTOR, ".el-dialog__title") # In BasePage
    # DIALOG_SAVE = (By.CSS_SELECTOR, ".el-dialog__footer .el-button--primary") # In BasePage
    # DIALOG_CANCEL = (By.CSS_SELECTOR, ".el-dialog__footer .el-button--default") # In BasePage
    
    # 弹窗表单字段 (假设表单在 el-dialog__body 下)
    DIALOG_NAME_INPUT = (By.CSS_SELECTOR, ".el-dialog__body #name")  # 假设 id 为 name
    DIALOG_METHOD_SELECT = (By.CSS_SELECTOR, ".el-dialog__body .el-select:first-of-type")
    DIALOG_PATH_INPUT = (By.CSS_SELECTOR, ".el-dialog__body input[placeholder*='path']")
    DIALOG_DESC_INPUT = (By.CSS_SELECTOR, ".el-dialog__body textarea")
    DIALOG_STATUS_SWITCH = (By.CSS_SELECTOR, ".el-dialog__body .el-switch")


    # ==================== 2. 页面入口 ====================
    def navigate(self) -> 'ApiManagementPage':
        """
        导航到 API 管理页面
        
        Returns:
            ApiManagementPage: 返回自身实例以支持链式调用
        """
        self.logger.info("导航到 API 管理页面")
        self.navigate_to("系统管理", "API管理")
        self.wait_vue_stable()
        return self


    # ==================== 3. 搜索功能 ====================
    def search(self, name: str = "", method: str = "", status: str = "") -> 'ApiManagementPage':
        """
        按条件搜索API
        
        Args:
            name: API名称
            method: 请求方法 (GET/POST/PUT/DELETE)
            status: 状态 (启用/禁用)
            
        Returns:
            ApiManagementPage: 返回自身实例以支持链式调用
        """
        self.logger.info(f"搜索API: name='{name}', method='{method}', status='{status}'")
        
        if name:
            self.logger.debug(f"输入搜索名称: {name}")
            input_el = self.wait_element_visible(self.SEARCH_NAME_INPUT)
            input_el.clear()
            input_el.send_keys(name)
        
        if method:
            self.logger.debug(f"选择请求方法: {method}")
            self.select_dropdown_option(self.SEARCH_METHOD_SELECT, method)  # 假设有通用下拉选择方法
        
        if status:
            self.logger.debug(f"选择状态: {status}")
            self.select_dropdown_option(self.SEARCH_STATUS_SELECT, status)
        
        self.click_element(self.SEARCH_BTN)
        self.wait_vue_stable()
        return self

    def reset_search(self) -> 'ApiManagementPage':
        """
        重置搜索条件
        
        Returns:
            ApiManagementPage: 返回自身实例以支持链式调用
        """
        self.logger.info("重置搜索条件")
        self.click_element(self.RESET_BTN)
        self.wait_vue_stable()
        return self


    # ==================== 4. 表格功能 ====================
    def _get_all_rows(self) -> List[WebElement]:
        """
        获取表格中所有数据行
        
        Returns:
            List[WebElement]: 表格行元素列表
        """
        self.logger.debug("获取表格行元素")
        table = self.wait_element_visible(self.TABLE_BODY)
        return table.find_elements(*self.TABLE_ROW)

    def get_table_data(self) -> List[Dict[str, str]]:
        """
        获取表格数据
        
        Returns:
            List[Dict[str, str]]: 表格数据列表，包含 ['名称', '请求方法', '路径', '描述', '状态', '创建时间']
        """
        self.logger.info("获取表格数据")
        rows = self._get_all_rows()
        data = []
        for row in rows:
            cells = row.find_elements(*self.TABLE_CELL)
            # 假设表格列顺序固定
            row_data = {
                '名称': cells[1].text if len(cells) > 1 else '',
                '请求方法': cells[2].text if len(cells) > 2 else '',
                '路径': cells[3].text if len(cells) > 3 else '',
                '描述': cells[4].text if len(cells) > 4 else '',
                '状态': cells[5].text if len(cells) > 5 else '',
                '创建时间': cells[6].text if len(cells) > 6 else '',
            }
            data.append(row_data)
        self.logger.debug(f"获取到 {len(data)} 条数据")
        return data

    def click_edit(self, row_index: int) -> 'ApiManagementPage':
        """
        点击指定行的"编辑"按钮
        
        Args:
            row_index: 行索引 (从0开始)
            
        Returns:
            ApiManagementPage: 返回自身实例以支持链式调用
        """
        self.logger.info(f"点击第 {row_index + 1} 行的编辑按钮")
        rows = self._get_all_rows()
        if row_index >= len(rows):
            self.logger.error(f"行索引 {row_index} 超出范围，总行数: {len(rows)}")
            raise IndexError(f"行索引超出范围. 总行数: {len(rows)}")
        
        target_row = rows[row_index]
        # 等待该行可见
        self.wait_element_visible(target_row)
        # 在该行范围内查找编辑按钮
        edit_btn = target_row.find_element(*self.EDIT_BTN_IN_ROW)
        self.scroll_into_view(edit_btn)  # 确保按钮可见
        self.click_element(edit_btn)
        self.wait_dialog_visible()  # 等待编辑弹窗出现
        return self

    def click_delete(self, row_index: int) -> 'ApiManagementPage':
        """
        点击指定行的"删除"按钮
        
        Args:
            row_index: 行索引 (从0开始)
            
        Returns:
            ApiManagementPage: 返回自身实例以支持链式调用
        """
        self.logger.info(f"点击第 {row_index + 1} 行的删除按钮")
        rows = self._get_all_rows()
        if row_index >= len(rows):
            raise IndexError(f"行索引超出范围. 总行数: {len(rows)}")
        
        target_row = rows[row_index]
        self.wait_element_visible(target_row)
        delete_btn = target_row.find_element(*self.DELETE_BTN_IN_ROW)
        self.scroll_into_view(delete_btn)
        self.click_element(delete_btn)
        self.wait_element_visible(self.DIALOG)  # 等待确认弹窗
        return self


    # ==================== 5. 增/改弹窗功能 ====================
    def click_add(self) -> 'ApiManagementPage':
        """
        点击"新增API"按钮，打开新增弹窗
        
        Returns:
            ApiManagementPage: 返回自身实例以支持链式调用
        """
        self.logger.info("点击新增API按钮")
        self.click_element(self.ADD_API_BTN)
        self.wait_dialog_visible()
        return self

    def fill_form(self, data: Dict[str, Any]) -> 'ApiManagementPage':
        """
        填写表单（新增/编辑弹窗）
        
        Args:
            data: 表单数据字典，支持键: 'name', 'method', 'path', 'description', 'status'
            
        Returns:
            ApiManagementPage: 返回自身实例以支持链式调用
        """
        self.logger.info(f"填写弹窗表单: {data}")
        
        if 'name' in data:
            self.logger.debug("填写API名称")
            input_el = self.wait_element_visible(self.DIALOG_NAME_INPUT)
            input_el.clear()
            input_el.send_keys(data['name'])
        
        if 'method' in data:
            self.logger.debug(f"选择请求方法: {data['method']}")
            self.select_dropdown_option(self.DIALOG_METHOD_SELECT, data['method'])
        
        if 'path' in data:
            self.logger.debug("填写API路径")
            input_el = self.wait_element_visible(self.DIALOG_PATH_INPUT)
            input_el.clear()
            input_el.send_keys(data['path'])
        
        if 'description' in data:
            self.logger.debug("填写API描述")
            # textarea 可能也是 send_keys
            desc_el = self.wait_element_visible(self.DIALOG_DESC_INPUT)
            desc_el.clear()
            desc_el.send_keys(data['description'])
        
        if 'status' in data:
            self.logger.debug(f"设置状态为: {data['status']}")
            switch_el = self.wait_element_visible(self.DIALOG_STATUS_SWITCH)
            switch_checked = switch_el.get_attribute('aria-checked') == 'true'
            if (data['status'] == '启用' and not switch_checked) or (data['status'] == '禁用' and switch_checked):
                self.click_element(switch_el)  # 切换状态
        
        return self

    def confirm_dialog(self) -> 'ApiManagementPage':
        """
        点击弹窗确认按钮 (保存)
        
        Returns:
            ApiManagementPage: 返回自身实例以支持链式调用
        """
        self.logger.info("点击弹窗保存按钮")
        self.click_element(self.DIALOG_SAVE)
        self.wait_dialog_closed()  # 等待弹窗关闭
        self.wait_toast()          # 等待toast提示
        self.wait_vue_stable()
        return self

    def cancel_dialog(self) -> 'ApiManagementPage':
        """
        点击弹窗取消按钮
        
        Returns:
            ApiManagementPage: 返回自身实例以支持链式调用
        """
        self.logger.info("点击弹窗取消按钮")
        self.click_element(self.DIALOG_CANCEL)
        self.wait_dialog_closed()
        self.wait_vue_stable()
        return self


    # ==================== 6. 分页功能 ====================
    def get_pagination_info(self) -> Dict[str, Any]:
        """
        获取分页信息
        
        Returns:
            Dict: 包含 'total', 'current_page', 'page_size' 的字典
        """
        self.logger.info("获取分页信息")
        pagination = self.wait_element_visible(self.PAGINATION)
        
        # 解析分页信息 (具体实现取决于Element Plus分页组件)
        # 以下为示例解析逻辑
        total_text = pagination.find_element(*self.PAGINATION_INFO).text
        total = int(total_text) if total_text else 0
        
        # 获取当前页码和每页条数 (假设有 .el-pager .number 和 .el-pagination__select)
        # 这取决于具体的Element Plus版本和配置
        current_page = 1  # 默认
        page_size = 10    # 默认
        
        self.logger.debug(f"分页信息: total={total}, current_page={current_page}, page_size={page_size}")
        return {
            'total': total,
            'current_page': current_page,
            'page_size': page_size
        }

    def select_page_size(self, size: int) -> 'ApiManagementPage':
        """
        选择每页显示条数
        
        Args:
            size: 每页条数 (10, 20, 50 等)
            
        Returns:
            ApiManagementPage: 返回自身实例以支持链式调用
        """
        self.logger.info(f"选择每页显示 {size} 条")
        self.select_dropdown_option(self.PAGE_SIZE_SELECTOR, str(size))
        self.wait_vue_stable()
        return self

    def go_to_page(self, page_num: int) -> 'ApiManagementPage':
        """
        跳转到指定页码
        
        Args:
            page_num: 目标页码 (从1开始)
            
        Returns:
            ApiManagementPage: 返回自身实例以支持链式调用
        """
        self.logger.info(f"跳转到第 {page_num} 页")
        page_input = self.wait_element_visible(self.PAGE_NUM_INPUT)
        page_input.clear()
        page_input.send_keys(str(page_num))
        page_input.send_keys("\n")  # 模拟回车确认
        self.wait_vue_stable()
        return self

    # ==================== 7. 辅助方法 (假设存在) ====================
    # def wait_dialog_visible(self):
    #     """等待弹窗可见，复用BasePage"""
    #     return self.wait_element_visible(self.DIALOG)
    #
    # def wait_dialog_closed(self):
    #     """等待弹窗关闭"""
    #     return self.wait_element_invisible(self.DIALOG)
    #
    # def toggle_switch(self, locator, target_state):
    #     """通用开关切换"""
    #     switch_el = self.wait_element_visible(locator)
    #     current = switch_el.get_attribute('aria-checked') == 'true'
    #     if (target_state and not current) or (not target_state and current):
    #         self.click_element(switch_el)
    #
    # def select_dropdown_option(self, select_locator, option_text):
    #     """通用el-select选项选择"""
    #     trigger = self.wait_element_clickable(select_locator)
    #     self.click_element(trigger)
    #     option_locator = (By.XPATH, f"//span[text()='{option_text}']")  # 或更复杂
    #     self.click_element(option_locator)