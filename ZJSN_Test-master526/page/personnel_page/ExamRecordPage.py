"""
考试记录页面 Page Object

⚠️ 本文件基于 PAGE_CONTEXT 中的预测元素生成，非最终版本。
请确保从 TECH_ANALYSIS.md 中替换所有定位器为已验证的选择器。

遵循规范:
    - 继承 BasePage
    - 定位器使用 CSS/XPath 元组，禁止绝对 XPath
    - 操作方法返回 self 支持链式调用
    - 使用 self.logger 记录日志
    - 无 time.sleep，使用 BasePage 等待方法
"""
import logging
import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class ExamRecordPage(BasePage):
    """
    考试记录管理页面操作类
    """

    # ==================== 搜索区域 ====================
    # ⚠️ 预测性定位器，需根据 TECH_ANALYSIS 验证或替换
    SEARCH_PERSON_NAME_INPUT = (
        By.CSS_SELECTOR,
        "input[placeholder*='请输入姓名']",
    )
    SEARCH_EXAM_DATE_RANGE = (
        By.CSS_SELECTOR,
        ".el-date-editor--daterange.el-input__inner",
    )
    SEARCH_EXAM_TYPE_SELECT = (
        By.XPATH,
        "//label[contains(text(),'考试类型')]/following-sibling::div//input",
    )
    SEARCH_STATUS_SELECT = (
        By.XPATH,
        "//label[contains(text(),'状态')]/following-sibling::div//input",
    )
    BTN_SEARCH = (By.XPATH, "//button[.//span[text()='搜索']]")
    BTN_RESET = (By.XPATH, "//button[.//span[text()='重置']]")

    # ==================== 表格区域 ====================
    TABLE = (By.CSS_SELECTOR, ".el-table")
    TABLE_HEADERS = (By.CSS_SELECTOR, ".el-table__header-wrapper th .cell")
    TABLE_ROWS = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr")

    # ==================== 操作按钮 ====================
    BTN_EXPORT = (By.XPATH, "//button[.//span[text()='导出']]")

    # ==================== 分页 ====================
    PAGINATION = (By.CSS_SELECTOR, ".el-pagination")

    # ==================== 详情弹窗 ====================
    DIALOG_DETAIL = (
        By.XPATH,
        "//div[contains(@class,'el-dialog') and .//span[text()='考试记录详情']]",
    )
    DIALOG_DETAIL_BTN_CONFIRM = (
        By.XPATH,
        "//div[contains(@class,'el-dialog') and .//span[text()='考试记录详情']]"
        "//div[contains(@class,'el-dialog__footer')]//button[.//span[text()='确定']]",
    )

    def navigate(self) -> "ExamRecordPage":
        """JS hash 导航至考试记录页面（SPA 内无刷新）"""
        self.driver.execute_script("window.location.hash = '#/personnel/training/examRecord'")
        self.wait_vue_stable()
        logger.info("已导航至考试记录页面")
        return self

    # ==================== 搜索操作 ====================

    def search(self, person_name: str = "", exam_type: str = "", status: str = "") -> "ExamRecordPage":
        """
        按条件搜索考试记录

        :param person_name: 人员姓名（可选）
        :param exam_type: 考试类型（可选）
        :param status: 状态（可选）
        """
        if person_name:
            self._fill_input_and_wait(self.SEARCH_PERSON_NAME_INPUT, person_name)
        if exam_type:
            self.select_dropdown_option_by_label(self.SEARCH_EXAM_TYPE_SELECT, exam_type)
        if status:
            self.select_dropdown_option_by_label(self.SEARCH_STATUS_SELECT, status)

        self.click(self.BTN_SEARCH)
        self.wait_vue_stable()
        logger.info("已执行搜索（姓名=%s, 类型=%s, 状态=%s）", person_name, exam_type, status)
        return self

    def reset_search(self) -> "ExamRecordPage":
        """重置搜索条件"""
        self.click(self.BTN_RESET)
        self.wait_vue_stable()
        logger.info("已重置搜索条件")
        return self

    # ==================== 表格数据 ====================

    def get_table_data(self) -> list[dict]:
        """
        获取当前表格所有行的数据

        :return: list[dict]，每行字典的键为表头文本，值为对应单元格文本
        """
        rows = self.find_elements(self.TABLE_ROWS)
        headers = self._get_table_headers()
        data = []
        for row in rows:
            cells = row.find_elements(By.CSS_SELECTOR, "td.el-table__cell")
            row_dict = {}
            for idx, cell in enumerate(cells):
                if idx < len(headers):
                    row_dict[headers[idx]] = cell.text
            if row_dict:
                data.append(row_dict)
        logger.info("获取到 %d 行表格数据", len(data))
        return data

    def _get_table_headers(self) -> list[str]:
        """获取表头文本列表"""
        header_cells = self.find_elements(self.TABLE_HEADERS)
        return [cell.text.strip() for cell in header_cells if cell.text.strip()]

    # ==================== 详情弹窗 ====================

    def view_detail(self, row_index: int = 0) -> "ExamRecordPage":
        """
        点击指定行的“查看详情”按钮（假设操作列包含此按钮）

        :param row_index: 行索引（0-based）
        """
        action_button = self._get_row_action_button(row_index, "查看详情")
        self.click(action_button)
        self.wait_for_visible(self.DIALOG_DETAIL)
        logger.info("已点击第 %d 行的查看详情按钮", row_index)
        return self

    def close_detail_dialog(self) -> "ExamRecordPage":
        """关闭考试记录详情弹窗"""
        self.click(self.DIALOG_DETAIL_BTN_CONFIRM)
        self.wait_for_invisible(self.DIALOG_DETAIL)
        logger.info("已关闭考试记录详情弹窗")
        return self

    # ==================== 导出 ====================

    def export(self) -> "ExamRecordPage":
        """点击导出按钮（可能触发文件下载）"""
        self.click(self.BTN_EXPORT)
        logger.info("已点击导出按钮")
        # 注意：导出功能可能需要处理文件下载或额外的确认弹窗，此处仅做点击操作
        return self

    # ==================== 分页 ====================

    def get_pagination_info(self) -> dict:
        """
        获取底部分页信息

        :return: dict，包含 total, current_page, page_size
        """
        info = self.get_pagination_text(self.PAGINATION)
        logger.info("获取分页信息: %s", info)
        return info

    # ==================== 辅助方法 ====================

    def _fill_input_and_wait(self, locator: tuple, value: str) -> None:
        """填写输入框（清除现有内容、输入、触发 Vue 更新）"""
        element = self.wait_for_clickable(locator)
        element.clear()
        element.send_keys(value)
        # 对于 el-input，可能需要触发 input 事件或按下回车/Tab 以更新 v-model
        element.send_keys(Keys.TAB)
        self.wait_vue_stable()

    def _get_row_action_button(self, row_index: int, button_text: str):
        """
        获取指定行操作列中文本为 button_text 的按钮

        :param row_index: 行索引
        :param button_text: 按钮文本，例如 "查看详情"
        :return: WebElement
        """
        # 定位到特定行，然后在该行内查找按钮
        row_xpath = f"({self.TABLE_ROWS[1]})[{row_index + 1}]"
        button_xpath = f".//button[.//span[text()='{button_text}']]"
        row = self.find_element((By.XPATH, row_xpath))
        button = row.find_element(By.XPATH, button_xpath)
        return button