# ============================================================
# 文件: page/dcs_page/alarm_config_page.py
# 类: AlarmConfigPage
# 说明: 设备报警配置页面 Page Object
# 适用: Selenium + pytest + Vue3/Element Plus
# ============================================================

from base.base_page import BasePage
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from typing import List, Dict, Any


class AllDataPage(BasePage):
    """
    设备报警配置页面对象，封装所有针对该页面的操作。
    """
    # ==================== 定位器 ====================
    # 搜索区域
    SEARCH_INPUT = (By.CSS_SELECTOR, ".search-area .el-input__inner[placeholder*='报警']")
    SEARCH_BTN = (By.XPATH, "//button[.//span[text()='搜索']]")
    RESET_BTN = (By.XPATH, "//button[.//span[text()='重置']]")

    # 列表/表格区域
    TABLE = (By.CSS_SELECTOR, ".el-table__body")
    TABLE_LOADING = (By.CSS_SELECTOR, ".el-loading-mask")  # Element Plus 表格加载遮罩
    TABLE_ROWS = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr.el-table__row")
    TABLE_EMPTY = (By.CSS_SELECTOR, ".el-table__empty-text")

    # 表格列定位器（用于获取数据）
    CELL_ALARM_TYPE = (By.CSS_SELECTOR, "td:nth-child(1) .cell")
    CELL_DEVICE_NAME = (By.CSS_SELECTOR, "td:nth-child(2) .cell")
    CELL_ALARM_LEVEL = (By.CSS_SELECTOR, "td:nth-child(3) .cell")
    CELL_STATUS = (By.CSS_SELECTOR, "td:nth-child(4) .cell")

    # 操作按钮 (编辑/删除按钮在每一行内)
    EDIT_BTN = (By.CSS_SELECTOR, "button.el-button--primary.el-button--small span")
    DELETE_BTN = (By.CSS_SELECTOR, "button.el-button--danger.el-button--small span")
    # 注意：以上两个定位器匹配文本，需要配合行元素使用

    # 新增按钮
    ADD_BTN = (By.XPATH, "//button[.//span[text()='新增']]")

    # 分页区域
    PAGINATION = (By.CSS_SELECTOR, ".el-pagination")
    PAGINATION_INFO = (By.CSS_SELECTOR, ".el-pagination__total")
    PAGINATION_PAGES = (By.CSS_SELECTOR, ".el-pager .number")

    # 弹窗（使用 BasePage 的通用定位器 DIALOG，无需重复定义）
    # 表单元素
    FORM_ITEM_ALARM_NAME = (By.CSS_SELECTOR, ".el-dialog .el-form-item__content input[placeholder='请输入报警名称']")
    FORM_ITEM_ALARM_LEVEL = (By.CSS_SELECTOR, ".el-dialog .el-select")
    FORM_ITEM_ALARM_LEVEL_DROPDOWN = (By.CSS_SELECTOR, ".el-select-dropdown__item")
    FORM_ITEM_STATUS_SWITCH = (By.CSS_SELECTOR, ".el-dialog .el-switch")
    FORM_ITEM_REMARK = (By.CSS_SELECTOR, ".el-dialog .el-textarea__inner")
    FORM_SUBMIT_BTN = (By.CSS_SELECTOR, ".el-dialog .el-button--primary")
    FORM_CANCEL_BTN = (By.CSS_SELECTOR, ".el-dialog .el-button:not(.el-button--primary)")

    # ==================== 导航 ====================
    def navigate(self):
        """
        导航到设备报警配置页面。
        """
        self.logger.info("导航到页面: 设备报警配置")
        self.navigate_to("设备管理", "设备报警配置")
        self.wait_vue_stable()
        self.wait_element_visible(self.SEARCH_INPUT)
        self.logger.info("设备报警配置页面加载成功")
        return self

    # ==================== 搜索功能 ====================
    def search(self, keyword: str):
        """
        搜索报警配置。
        :param keyword: 搜索关键词
        """
        self.logger.info(f"搜索报警配置, 关键词: {keyword}")
        self.wait_element_clickable(self.SEARCH_INPUT).clear()
        self.wait_element_clickable(self.SEARCH_INPUT).send_keys(keyword)
        self.wait_element_clickable(self.SEARCH_BTN).click()
        self.wait_vue_stable()
        # 等待表格加载完毕
        self.wait_element_invisible(self.TABLE_LOADING)
        self.logger.info("搜索完成")
        return self

    def reset_search(self):
        """
        重置搜索条件。
        """
        self.logger.info("重置搜索条件")
        self.wait_element_clickable(self.RESET_BTN).click()
        self.wait_vue_stable()
        self.wait_element_invisible(self.TABLE_LOADING)
        self.logger.info("搜索条件已重置")
        return self

    # ==================== 表格数据 ====================
    def get_table_data(self) -> List[Dict[str, str]]:
        """
        获取当前表格中所有行的数据。
        :return: 包含 dict 的列表, 每个 dict 包含报警类型、设备名称、报警级别、状态
        """
        self.logger.info("获取表格数据")
        # 等待表格出现且加载完成
        self.wait_element_invisible(self.TABLE_LOADING)
        rows = self.wait_elements_presence(self.TABLE_ROWS)
        data = []
        for row in rows:
            alarm_type = row.find_element(*self.CELL_ALARM_TYPE).text.strip()
            device_name = row.find_element(*self.CELL_DEVICE_NAME).text.strip()
            alarm_level = row.find_element(*self.CELL_ALARM_LEVEL).text.strip()
            status = row.find_element(*self.CELL_STATUS).text.strip()
            data.append({
                "alarm_type": alarm_type,
                "device_name": device_name,
                "alarm_level": alarm_level,
                "status": status
            })
        self.logger.info(f"获取到 {len(data)} 条数据")
        return data

    # ==================== 新增 ====================
    def click_add(self):
        """
        点击新增按钮，打开新增弹窗。
        """
        self.logger.info("点击新增按钮")
        self.wait_element_clickable(self.ADD_BTN).click()
        self.wait_vue_stable()
        self.wait_element_visible(self.DIALOG)
        self.logger.info("新增弹窗已打开")
        return self

    def fill_form(self, data_dict: Dict[str, Any]):
        """
        填写新增或编辑弹窗中的表单。
        根据传入的 dict 填充字段，不存在的字段将跳过。
        支持的字段: alarm_name, alarm_level, status, remark
        :param data_dict: 包含表单数据的字典
                           e.g. {"alarm_name": "测试报警", "alarm_level": "严重", "status": True}
        """
        self.logger.info(f"填写表单数据: {data_dict}")
        self.wait_element_visible(self.DIALOG)

        if "alarm_name" in data_dict:
            self.logger.debug("填写报警名称")
            self.wait_element_visible(self.FORM_ITEM_ALARM_NAME).clear()
            self.wait_element_visible(self.FORM_ITEM_ALARM_NAME).send_keys(data_dict["alarm_name"])

        if "alarm_level" in data_dict:
            self.logger.debug("选择报警级别")
            self.wait_element_clickable(self.FORM_ITEM_ALARM_LEVEL).click()
            self.wait_element_visible(self.FORM_ITEM_ALARM_LEVEL_DROPDOWN)
            level_options = self.wait_elements_presence(self.FORM_ITEM_ALARM_LEVEL_DROPDOWN)
            for option in level_options:
                if option.text.strip() == data_dict["alarm_level"]:
                    option.click()
                    break
            else:
                self.logger.warning(f"未找到报警级别选项: {data_dict['alarm_level']}")
                # 点击空白区域关闭下拉菜单
                self.wait_element_clickable(self.DIALOG).click()

        if "status" in data_dict:
            self.logger.debug("设置状态开关")
            switch = self.wait_element_presence(self.FORM_ITEM_STATUS_SWITCH)
            expected_class = "el-switch is-checked" if data_dict["status"] else "el-switch"
            current_class = switch.get_attribute("class")
            if current_class != expected_class:
                switch.click()

        if "remark" in data_dict:
            self.logger.debug("填写备注")
            self.wait_element_visible(self.FORM_ITEM_REMARK).clear()
            self.wait_element_visible(self.FORM_ITEM_REMARK).send_keys(data_dict["remark"])

        self.logger.info("表单填写完成")
        return self

    def confirm_dialog(self):
        """
        确认弹窗（点击确定/保存按钮）。
        """
        self.logger.info("确认弹窗")
        self.wait_element_clickable(self.FORM_SUBMIT_BTN).click()
        self.wait_vue_stable()
        # 等待弹窗关闭
        self.wait_element_invisible(self.DIALOG)
        self.wait_element_visible(self.TOAST_SUCCESS)
        self.logger.info("弹窗确认成功")
        return self

    def cancel_dialog(self):
        """
        取消弹窗（点击取消按钮）。
        """
        self.logger.info("取消弹窗")
        self.wait_element_clickable(self.FORM_CANCEL_BTN).click()
        self.wait_vue_stable()
        self.wait_element_invisible(self.DIALOG)
        self.logger.info("弹窗取消成功")
        return self

    # ==================== 编辑 & 删除 ====================
    def get_row(self, row_index: int) -> WebElement:
        """
        根据索引获取表格行元素。
        :param row_index: 行索引 (从 0 开始)
        :return: WebElement 行元素
        """
        self.wait_element_invisible(self.TABLE_LOADING)
        rows = self.wait_elements_presence(self.TABLE_ROWS)
        if row_index < 0 or row_index >= len(rows):
            raise IndexError(f"行索引 {row_index} 超出范围, 当前共有 {len(rows)} 行")
        return rows[row_index]

    def click_edit(self, row_index: int):
        """
        点击指定行的编辑按钮。
        :param row_index: 行索引 (从 0 开始)
        """
        self.logger.info(f"编辑第 {row_index + 1} 行数据")
        row = self.get_row(row_index)
        edit_button = row.find_element(*self.EDIT_BTN)
        self.wait_element_clickable(edit_button)
        # JavaScript 点击避免元素被覆盖
        self.driver.execute_script("arguments[0].click();", edit_button)
        self.wait_vue_stable()
        self.wait_element_visible(self.DIALOG)
        self.logger.info("编辑弹窗已打开")
        return self

    def click_delete(self, row_index: int):
        """
        点击指定行的删除按钮。
        :param row_index: 行索引 (从 0 开始)
        """
        self.logger.info(f"删除第 {row_index + 1} 行数据")
        row = self.get_row(row_index)
        delete_button = row.find_element(*self.DELETE_BTN)
        self.wait_element_clickable(delete_button)
        self.driver.execute_script("arguments[0].click();", delete_button)
        self.wait_vue_stable()
        self.wait_element_visible(self.DIALOG)
        self.logger.info("删除确认弹窗已打开")
        return self

    # ==================== 分页信息 ====================
    def get_pagination_info(self) -> str:
        """
        获取分页信息，例如 "第 1 页，共 10 页，共 100 条"
        :return: 分页信息文本
        """
        self.logger.info("获取分页信息")
        self.wait_element_visible(self.PAGINATION)
        info = self.wait_element_visible(self.PAGINATION_INFO).text.strip()
        self.logger.info(f"分页信息: {info}")
        return info