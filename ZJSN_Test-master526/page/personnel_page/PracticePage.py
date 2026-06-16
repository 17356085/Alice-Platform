"""自主练习页面操作类

Phase 4 自动生成 | 2026-06-12
页面类型: 个人端记录列表（表格 + 状态筛选 + 行操作按钮）
"""
import logging

from selenium.webdriver.common.by import By

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class PracticePage(BasePage):
    """自主练习页面 — 表格 + 状态下拉筛选 + 行操作"""

    # ══════════════════════════════════════════════════════════════════
    # 页面专属定位器
    # ══════════════════════════════════════════════════════════════════

    # — 筛选 —
    STATUS_SELECT = (
        By.XPATH,
        '//div[contains(@class,"el-select")]',
    )

    # — 行操作（按练习名称定位） —
    ROW_START_PRACTICE = (
        By.XPATH,
        '//tr[contains(@class,"el-table__row")]'
        '[.//td[contains(normalize-space(.),"{name}")]]'
        '//button[contains(.,"开始练习")]',
    )
    ROW_CONTINUE_PRACTICE = (
        By.XPATH,
        '//tr[contains(@class,"el-table__row")]'
        '[.//td[contains(normalize-space(.),"{name}")]]'
        '//button[contains(.,"继续练习")]',
    )
    ROW_VIEW_RESULT = (
        By.XPATH,
        '//tr[contains(@class,"el-table__row")]'
        '[.//td[contains(normalize-space(.),"{name}")]]'
        '//button[contains(.,"查看成绩")]',
    )
    ROW_DELETE = (
        By.XPATH,
        '//tr[contains(@class,"el-table__row")]'
        '[.//td[contains(normalize-space(.),"{name}")]]'
        '//button[contains(.,"删除")]',
    )

    # ==================================================================
    # 导航
    # ==================================================================

    def navigate_to_practice(self):
        """导航到自主练习页面"""
        self.navigate_to("人员管理", "培训管理", "自主练习")
        self.wait_vue_stable()
        logger.info("已导航到自主练习页面")

    # ==================================================================
    # 表格操作
    # ==================================================================

    def get_practice_headers(self):
        """获取表格表头"""
        return self.get_table_headers(min_columns=5)

    def get_practice_count(self):
        """获取当前页练习记录数"""
        return self.get_table_row_count()

    def get_first_row_texts(self):
        """获取第一行所有列数据"""
        return self.get_first_row_data()

    def is_record_present(self, name):
        """判断指定名称的练习记录是否存在"""
        return self.is_row_present(name)

    def get_row_status(self, name):
        """获取指定行的状态列文本 (列8)"""
        try:
            col_data = self.get_column_data(8)
            idx = self._find_row_index(name, 3)
            if idx < len(col_data):
                return col_data[idx]
        except Exception:
            pass
        return ""

    # ==================================================================
    # 行操作
    # ==================================================================

    def _click_row_btn(self, locator_template, name, btn_desc):
        locator = (By.XPATH, locator_template[1].replace("{name}", name))
        self.click(locator)
        self.wait_vue_stable()
        logger.info("%s: %s", btn_desc, name)

    def start_practice(self, name):
        """点击已完成记录的"开始练习"（新建一次练习）"""
        self._click_row_btn(self.ROW_START_PRACTICE, name, "开始练习")

    def continue_practice(self, name):
        """点击未完成记录的"继续练习"（恢复进度）"""
        self._click_row_btn(self.ROW_CONTINUE_PRACTICE, name, "继续练习")

    def view_result(self, name):
        """点击"查看成绩"打开成绩弹窗"""
        self._click_row_btn(self.ROW_VIEW_RESULT, name, "查看成绩")
        self.wait_dialog_open()

    def click_delete(self, name):
        """点击删除按钮"""
        self._click_row_btn(self.ROW_DELETE, name, "点击删除")

    def confirm_delete(self):
        """确认删除 MessageBox"""
        self.confirm_message_box()
        logger.info("已确认删除")

    def delete_record(self, name, confirm=True):
        """删除练习记录"""
        self.click_delete(name)
        if confirm:
            self.confirm_delete()
            self.wait_vue_stable()

    # ==================================================================
    # 搜索结果
    # ==================================================================

    def get_accuracy_values(self):
        """获取正确率列所有值 (列6)"""
        return self.get_column_data(6)

    # ==================================================================
    # 内部工具
    # ==================================================================

    def _find_row_index(self, search_text, col_index=1):
        """在指定列中搜索文本，返回匹配行索引(0-based)"""
        col_data = self.get_column_data(col_index)
        for i, val in enumerate(col_data):
            if search_text in val:
                return i
        return -1
