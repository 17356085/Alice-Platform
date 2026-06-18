"""
考试记录页面 Page Object

⚠️ 本文件基于 PAGE_CONTEXT.md 中的预测元素生成，非最终版本。
请确保从 TECH_ANALYSIS.md 中替换所有定位器为已验证的选择器。
"""
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class ExamRecordPage(BasePage):
    """
    考试记录管理页面
    """

    # ==================== 搜索区域 ====================
    SEARCH_PERSON_NAME_INPUT = (
        By.CSS_SELECTOR,
        "input[placeholder*='请输入姓名']",
    )  # 预测：placeholder 含 "请输入姓名"
    SEARCH_EXAM_DATE_RANGE = (
        By.CSS_SELECTOR,
        ".el-date-editor--daterange",
    )  # 预测：CSS 类
    SEARCH_EXAM_TYPE_SELECT = (
        By.XPATH,
        "//label[contains(text(),'考试类型')]/following-sibling::div//input",
    )  # 预测：label 关联 select
    SEARCH_STATUS_SELECT = (
        By.XPATH,
        "//label[contains(text(),'状态')]/following-sibling::div//input",
    )  # 预测：label 关联 select
    BTN_SEARCH = (By.XPATH, "//button[.//span[text()='搜索']]")  # 通用
    BTN_RESET = (By.XPATH, "//button[.//span[text()='重置']]")  # 通用

    # ==================== 表格区域 ====================
    TABLE = (By.CSS_SELECTOR, ".el-table")  # 通用
    TABLE_ROWS = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr")  # 通用

    # ==================== 操作按钮 ====================
    BTN_EXPORT = (By.XPATH, "//button[.//span[text()='导出']]")  # 预测

    # ==================== 分页 ====================
    PAGINATION = (By.CSS_SELECTOR, ".el-pagination")  # 通用

    # ==================== 详情弹窗 ====================
    DIALOG_DETAIL = (By.XPATH, "//div[contains(@class,'el-dialog') and .//span[text()='考试记录详情']]")
    DIALOG_DETAIL_BTN_CONFIRM = (
        By.XPATH,
        "//div[contains(@class,'el-dialog') and .//span[text()='考试记录详情']]//button[.//span[text()='确定']]",
    )

    def navigate(self) -> "ExamRecordPage":
        """
        导航至考试记录页面（通过侧边栏菜单）
        假设菜单路径：人员管理 -> 考试记录
        """
        self.navigate_to("人员管理", "考试记录")  # 需确认菜单名称
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
            self._fill_input(self.SEARCH_PERSON_NAME_INPUT, person_name)
        if exam_type:
            self._select_by_label(self.SEARCH_EXAM_TYPE_SELECT, exam_type)
        if status:
            self._select_by_label(self.SEARCH_STATUS_SELECT, status)
        # 日期范围暂未实现，可后续扩展
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
        获取当前表格行数据（简化版）

        返回：每行字典，键为表头文本，值为单元格文本
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
        header_cells = self.find_elements(
            By.CSS_SELECTOR, ".el-table__header-wrapper th .cell"
        )
        return [cell.text.strip() for cell in header_cells if cell.text.strip()]

    # ==================== 详情弹窗 ====================

    def view_detail(self, row_index: int = 0) -> "ExamRecordPage":
        """
        点击某行的“查看详情”按钮（假设操作列有该按钮）

        :param row_index: 行索引（0-based）
        """
        # 找到操作列中的查看按钮
        action_btn = self._get_action_button(row_index, "查看详情")
        self.click(action_btn)
        self.wait_vue_stable()
        # 等待详情弹窗可见
        self.wait_for_visible(self.DIALOG_DETAIL)
        logger.info("已点击第 %d 行查看详情", row_index)
        return self

    def close_detail_dialog(self) -> "ExamRecordPage":
        """关闭详情弹窗"""
        self.click(self.DIALOG_DETAIL_BTN_CONFIRM)
        self.wait_for_invisible(self.DIALOG_DETAIL)
        logger.info("已关闭考试记录详情弹窗")
        return self

    # ==================== 导出 ====================

    def export(self) -> "ExamRecordPage":
        """点击导出按钮（可能触发下载）"""
        self.click(self.BTN_EXPORT)
        # 如果导出有确认弹窗，需额外处理，此处仅做点击
        logger.info("已点击导出按钮")
        return self

    # ==================== 分页 ====================

    def get_pagination_info(self) -> dict:
        """
        获取分页信息

        返回：{"total": int, "current_page": int, "page_size": int, "pages": int}
        """
        info = self.get_pagination_text(self.PAGINATION)  # 假设 BasePage 有该方法
        logger.info("获取分页信息: %s", info)
        return info

    # ==================== 辅助方法 ====================

    def _fill_input(self, locator: tuple, value: str) -> None:
        """填写输入框（先清除再输入）"""
        el = self.find_element(locator)
        el.clear()
        el.send_keys(value)

    def _select_by_label(self, selector_locator: tuple, option_text: str) -> None:
        """
        通过点击 select 并选择选项文本
        简化版：点击 select 展开下拉，点击包含 option_text 的选项
        """
        self.click(selector_locator)
        option_loc = (By.XPATH, f"//span[text()='{option_text}']")
        self.click(option_loc)

    def _get_action_button(self, row_index: int, button_text: str):
        """
        获取指定行操作列中的按钮

        :param row_index: 行索引
        :param button_text: 按钮文本（如 "查看详情"）
        """
        rows = self.find_elements(self.TABLE_ROWS)
        if row_index >= len(rows):
            raise IndexError(f"行索引 {row_index} 超出范围（共 {len(rows)} 行）")
        target_row = rows[row_index]
        return target_row.find_element(
            By.XPATH, f".//button[.//span[text()='{button_text}']]"
        )