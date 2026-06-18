# ============================================================
# Page Object: MyExamPage
# Module: personnel
# Page: 我的考试 (my-exam)
# Author: AITest Platform Agent
# ============================================================
from base.base_page import BasePage
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


class MyExamPage(BasePage):
    """
    我的考试页面 - 展示当前用户已分配或需完成的考试/测评列表。
    """

    # ==================== Locators ====================
    # --- 搜索区 ---
    SEARCH_INPUT = (By.CSS_SELECTOR, "input[placeholder*='考试名称']")
    STATUS_SELECT = (By.CSS_SELECTOR, ".el-select")
    STATUS_SELECT_DROPDOWN = (By.CSS_SELECTOR, ".el-select-dropdown__item")
    SEARCH_BTN = (By.XPATH, "//button[.//span[text()='搜索']]")
    RESET_BTN = (By.XPATH, "//button[.//span[text()='重置']]")

    # --- 表格区 ---
    TABLE = (By.CSS_SELECTOR, ".el-table")
    TABLE_ROWS = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr")
    TABLE_LOADING = (By.CSS_SELECTOR, ".el-loading-mask")

    # --- 分页区 ---
    PAGINATION = (By.CSS_SELECTOR, ".el-pagination")
    PAGINATION_TOTAL = (By.CSS_SELECTOR, ".el-pagination__total")
    PAGINATION_PAGES = (By.CSS_SELECTOR, ".el-pagination .el-select .el-input")

    # --- 弹窗 ---
    DIALOG = (By.CSS_SELECTOR, ".el-dialog")
    DIALOG_TITLE = (By.CSS_SELECTOR, ".el-dialog__title")
    DIALOG_CLOSE_BTN = (By.CSS_SELECTOR, ".el-dialog__headerbtn")
    DIALOG_CONFIRM_BTN = (By.XPATH, "//div[contains(@class, 'el-dialog__footer')]//button[.//span[text()='确定']]")
    DIALOG_CANCEL_BTN = (By.XPATH, "//div[contains(@class, 'el-dialog__footer')]//button[.//span[text()='取消']]")

    # ==================== Actions ====================

    def navigate(self):
        """导航到 '我的考试' 页面"""
        self.logger.info("导航到: 人员管理 > 我的考试")
        self.navigate_to("人员管理", "我的考试")
        self.wait_vue_stable()
        self.wait_element_visible(self.TABLE)
        return self

    def search(self, keyword: str):
        """按考试名称搜索"""
        self.logger.info(f"搜索考试名称: {keyword}")
        self.wait_element_clickable(self.SEARCH_INPUT).clear()
        self.find_element(self.SEARCH_INPUT).send_keys(keyword)
        self.wait_element_clickable(self.SEARCH_BTN).click()
        self.wait_element_invisible(self.TABLE_LOADING)
        return self

    def reset_search(self):
        """重置搜索条件"""
        self.logger.info("重置搜索条件")
        self.wait_element_clickable(self.RESET_BTN).click()
        self.wait_element_invisible(self.TABLE_LOADING)
        return self

    def select_status(self, status_text: str):
        """按考试状态筛选

        Args:
            status_text: 未开始 / 进行中 / 已完成
        """
        self.logger.info(f"选择考试状态: {status_text}")
        self.wait_element_clickable(self.STATUS_SELECT).click()
        self.wait_element_visible(self.STATUS_SELECT_DROPDOWN)
        # 根据文本点击下拉项，避免索引依赖
        status_option = (By.XPATH, f"//div[contains(@class, 'el-select-dropdown')]//span[text()='{status_text}']")
        self.wait_element_clickable(status_option).click()
        self.wait_element_invisible(self.TABLE_LOADING)
        return self

    def get_table_data(self) -> list[dict]:
        """获取表格数据，返回字典列表

        Returns:
            list[dict]: 包含列数据的字典列表
        """
        self.logger.info("获取表格数据")
        rows = self.find_elements(self.TABLE_ROWS)
        table_data = []
        for row in rows:
            cells = row.find_elements(By.CSS_SELECTOR, "td")
            if len(cells) >= 8:
                row_data = {
                    "exam_name": cells[0].text.strip(),
                    "duration": cells[1].text.strip(),
                    "total_score": cells[2].text.strip(),
                    "pass_score": cells[3].text.strip(),
                    "status": cells[4].text.strip(),
                    "start_time": cells[5].text.strip(),
                    "end_time": cells[6].text.strip(),
                }
                table_data.append(row_data)
        return table_data

    def get_table_row_count(self) -> int:
        """获取表格行数"""
        self.logger.debug("获取表格行数")
        return len(self.find_elements(self.TABLE_ROWS))

    def get_pagination_info(self) -> dict:
        """获取分页信息

        Returns:
            dict: {"total": int, "current_page": int, "page_size": int}
        """
        self.logger.info("获取分页信息")
        if not self.is_element_present(self.PAGINATION):
            return {"total": 0, "current_page": 1, "page_size": 10}

        total_text = self.find_element(self.PAGINATION_TOTAL).text
        total = int(total_text.replace("共 ", "").replace(" 条", "")) if total_text else 0

        # 获取当前页和每页条数（简化处理，从分页组件提取）
        # 更精确的方法需要解析 el-pagination 的 v-model
        page_size = 10  # 默认值
        current_page = 1
        try:
            page_size_text = self.find_element(self.PAGINATION_PAGES).text
            if page_size_text:
                page_size = int(page_size_text)
        except Exception:
            self.logger.warning("无法获取每页条数，使用默认值10")
        try:
            active_page = self.find_element((By.CSS_SELECTOR, ".el-pagination .el-pager .number.active"))
            if active_page:
                current_page = int(active_page.text)
        except Exception:
            self.logger.warning("无法获取当前页码，使用默认值1")

        return {
            "total": total,
            "current_page": current_page,
            "page_size": page_size
        }

    def click_row_action(self, row_index: int, action_text: str):
        """点击指定行的操作按钮

        Args:
            row_index: 行索引（从0开始）
            action_text: 按钮文本，如 '开始考试'、'查看成绩'
        """
        self.logger.info(f"点击第 {row_index + 1} 行的操作按钮: {action_text}")
        rows = self.find_elements(self.TABLE_ROWS)
        if row_index >= len(rows):
            raise IndexError(f"行索引 {row_index} 超出范围 (共 {len(rows)} 行)")

        target_row = rows[row_index]
        action_btn = target_row.find_element(By.XPATH, f".//button[.//span[text()='{action_text}']]")
        self.wait_element_clickable(action_btn).click()
        self.wait_element_invisible(self.TABLE_LOADING)
        return self

    def view_exam_detail(self, row_index: int):
        """查看考试详情（弹窗方式）

        Args:
            row_index: 行索引
        """
        self.logger.info(f"查看第 {row_index + 1} 行考试详情")
        return self.click_row_action(row_index, "查看详情")

    def start_exam(self, row_index: int):
        """开始考试（触发确认弹窗）

        Args:
            row_index: 行索引
        """
        self.logger.info(f"开始第 {row_index + 1} 行考试")
        self.click_row_action(row_index, "开始考试")
        # 等待确认弹窗出现
        self.wait_element_visible(self.DIALOG)
        return self

    def view_exam_result(self, row_index: int):
        """查看考试成绩

        Args:
            row_index: 行索引
        """
        self.logger.info(f"查看第 {row_index + 1} 行考试成绩")
        return self.click_row_action(row_index, "查看成绩")

    def confirm_start_exam(self):
        """在 '确认开始考试' 弹窗中点击 '确定'"""
        self.logger.info("确认开始考试")
        self.wait_element_clickable(self.DIALOG_CONFIRM_BTN).click()
        self.wait_element_invisible(self.DIALOG)
        self.wait_element_invisible(self.TABLE_LOADING)
        return self

    def cancel_start_exam(self):
        """在 '确认开始考试' 弹窗中点击 '取消'"""
        self.logger.info("取消开始考试")
        self.wait_element_clickable(self.DIALOG_CANCEL_BTN).click()
        self.wait_element_invisible(self.DIALOG)
        return self

    def close_dialog(self):
        """关闭当前弹窗（点击右上角 X）"""
        self.logger.info("关闭弹窗")
        self.wait_element_clickable(self.DIALOG_CLOSE_BTN).click()
        self.wait_element_invisible(self.DIALOG)
        return self