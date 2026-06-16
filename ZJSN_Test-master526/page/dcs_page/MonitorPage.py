from base.base_page import BasePage
from selenium.webdriver.common.by import By


class DcsMonitorPage(BasePage):
    """
    DCS 模块 - Monitor 页面对象
    注意：所有定位器需根据 TECH_ANALYSIS.md 替换，此处为示例占位。
    """

    # ========== 定位器（占位符，需替换为真实选择器）==========
    SEARCH_INPUT = (By.CSS_SELECTOR, ".monitor-search input")
    SEARCH_BUTTON = (By.XPATH, "//button[.//span[text()='搜索']]")
    RESET_BUTTON = (By.XPATH, "//button[.//span[text()='重置']]")
    ADD_BUTTON = (By.XPATH, "//button[.//span[text()='新增']]")
    TABLE = (By.CSS_SELECTOR, ".el-table")
    PAGINATION = (By.CSS_SELECTOR, ".el-pagination")

    # 弹窗相关（复用 BasePage 通用定位器 DIALOG / DIALOG_SAVE / DIALOG_CANCEL）

    # ========== 页面入口 ==========
    def navigate(self):
        """导航至 Monitor 页面（菜单路径需确认）"""
        self.logger.info("导航到 DCS Monitor 页面")
        self.navigate_to("DCS模块", "Monitor")  # 请替换为实际菜单项名称
        self.wait_vue_stable()
        return self

    # ========== 搜索 / 重置 ==========
    def search(self, keyword: str):
        """搜索关键字"""
        self.logger.info(f"输入搜索关键字: {keyword}")
        self.find(self.SEARCH_INPUT).clear()
        self.find(self.SEARCH_INPUT).send_keys(keyword)
        self.click_element(self.SEARCH_BUTTON)
        self.wait_vue_stable()
        return self

    def reset_search(self):
        """重置搜索条件"""
        self.logger.info("重置搜索")
        self.click_element(self.RESET_BUTTON)
        self.wait_vue_stable()
        return self

    # ========== 表格数据 ==========
    def get_table_data(self):
        """获取表格所有行的文本数据（按需调整解析逻辑）"""
        self.logger.info("获取表格数据")
        self.wait_element_visible(self.TABLE)
        rows = self.find_elements((By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr"))
        data = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            data.append([cell.text for cell in cells])
        return data

    # ========== 操作（新增/编辑/删除）==========
    def click_add(self):
        """点击新增按钮"""
        self.logger.info("点击新增")
        self.click_element(self.ADD_BUTTON)
        self.wait_dialog_visible()  # 假设新增打开弹窗
        return self

    def fill_form(self, data: dict):
        """
        填充弹窗表单
        :param data: 字段名->值的字典，例如 {"name": "test", "status": "1"}
        """
        self.logger.info(f"填充表单: {data}")
        for field, value in data.items():
            # 根据字段名定位输入框（示例用标签定位，需根据实际 DOM 调整）
            locator = (By.XPATH, f"//label[text()='{field}']/following-sibling::div//input")
            self.find(locator).clear()
            self.find(locator).send_keys(value)
        return self

    def confirm_dialog(self):
        """确认弹窗（点击保存）"""
        self.logger.info("确认弹窗")
        self.click_element(self.DIALOG_SAVE)
        self.wait_dialog_invisible()
        self.wait_vue_stable()
        return self

    def cancel_dialog(self):
        """取消弹窗"""
        self.logger.info("取消弹窗")
        self.click_element(self.DIALOG_CANCEL)
        self.wait_dialog_invisible()
        return self

    def click_edit(self, row_index: int):
        """
        点击指定行的编辑按钮
        :param row_index: 从0开始的索引
        """
        self.logger.info(f"编辑第 {row_index+1} 行")
        # 假设每行最后一个操作列有编辑按钮
        edit_btn = (By.XPATH, f"//tbody/tr[{row_index+1}]//button[contains(@class, 'el-button--text') and .//span[text()='编辑']]")
        self.click_element(edit_btn)
        self.wait_dialog_visible()
        return self

    def click_delete(self, row_index: int):
        """
        点击指定行的删除按钮
        :param row_index: 从0开始的索引
        """
        self.logger.info(f"删除第 {row_index+1} 行")
        del_btn = (By.XPATH, f"//tbody/tr[{row_index+1}]//button[contains(@class, 'el-button--text') and .//span[text()='删除']]")
        self.click_element(del_btn)
        return self

    # ========== 分页 ==========
    def get_pagination_info(self):
        """获取分页信息，返回 (当前页, 总条数)"""
        self.logger.info("获取分页信息")
        self.wait_element_visible(self.PAGINATION)
        # Element Plus 分页通常显示 "共 X 条"，可通过 .el-pagination__total 获取
        total_text = self.find((By.CSS_SELECTOR, ".el-pagination__total")).text
        total = int(total_text.replace("共 ", "").replace(" 条", ""))
        current_page = self.find((By.CSS_SELECTOR, ".el-pagination .el-pager li.active")).text
        return int(current_page), total