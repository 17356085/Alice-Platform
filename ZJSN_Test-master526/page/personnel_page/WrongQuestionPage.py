"""错题本页面操作类

Phase 4 自动生成 | 2026-06-12
⚠️ 页面当前无数据，定位器为推断。数据就绪后需验证。
页面类型: 个人端数据列表（8筛选 + 表格 + 重新作答弹窗）
"""
import logging

from selenium.webdriver.common.by import By

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class WrongQuestionPage(BasePage):
    """错题本页面 — 多条件筛选 + 表格 + 重新作答弹窗"""

    # ══════════════════════════════════════════════════════════════════
    # 页面专属定位器
    # ══════════════════════════════════════════════════════════════════

    # — 筛选区（8 个 el-select） —
    FILTER_SELECTS = (
        By.CSS_SELECTOR,
        '.search-bar .el-select, [class*="search"] .el-select, .el-form .el-select',
    )
    KEYWORD_INPUT = (
        By.CSS_SELECTOR,
        'input[placeholder*="搜索"]',
    )

    # — 行操作（按题目文本定位） —
    ROW_REDO = (
        By.XPATH,
        '//tr[contains(@class,"el-table__row")]'
        '[.//td[contains(normalize-space(.),"{q}")]]'
        '//button[contains(.,"作答") or contains(.,"重做")]',
    )
    ROW_ANALYSIS = (
        By.XPATH,
        '//tr[contains(@class,"el-table__row")]'
        '[.//td[contains(normalize-space(.),"{q}")]]'
        '//button[contains(.,"解析") or contains(.,"查看")]',
    )
    ROW_REMOVE = (
        By.XPATH,
        '//tr[contains(@class,"el-table__row")]'
        '[.//td[contains(normalize-space(.),"{q}")]]'
        '//button[contains(.,"移除") or contains(.,"移出")]',
    )

    # ==================================================================
    # 导航
    # ==================================================================

    def navigate_to_wrong_question(self):
        """导航到错题本页面（侧边栏显示为"错题集"）"""
        self.navigate_to("人员管理", "培训管理", "错题集")
        self.wait_vue_stable()
        logger.info("已导航到错题本页面")

    # ==================================================================
    # 搜索区操作
    # ==================================================================

    def click_search(self):
        """点击查询按钮"""
        self.click_search_button()
        self.wait_vue_stable()

    def click_reset(self):
        """点击重置按钮"""
        self.click_reset_button()
        self.wait_vue_stable()

    def input_keyword(self, keyword):
        """输入关键词搜索"""
        self.input_text(self.KEYWORD_INPUT, keyword)
        logger.info("错题搜索: %s", keyword)

    def select_filter_by_index(self, index, option_text):
        """按索引选择筛选下拉（0-based）

        Args:
            index: 下拉框索引 (0-7，对应8个筛选条件)
            option_text: 选项文本
        """
        selects = self.find_all(self.FILTER_SELECTS)
        if index < len(selects):
            self._scroll_into_view(selects[index])
            selects[index].click()
            self._select_option(option_text)
            logger.info("筛选[%d] = %s", index, option_text)

    # ==================================================================
    # 表格操作
    # ==================================================================

    def get_question_count(self):
        """获取当前页错题数"""
        return self.get_table_row_count()

    def get_question_headers(self):
        """获取表格表头"""
        return self.get_table_headers(min_columns=5)

    def get_first_row_texts(self):
        """获取第一行所有列数据"""
        return self.get_first_row_data()

    # ==================================================================
    # 行操作
    # ==================================================================

    def click_redo(self, question_text):
        """点击重新作答"""
        locator = (By.XPATH, self.ROW_REDO[1].replace("{q}", question_text))
        self.click(locator)
        self.wait_dialog_open()
        logger.info("重新作答: %s", question_text[:30])

    def click_view_analysis(self, question_text):
        """点击查看解析"""
        locator = (By.XPATH, self.ROW_ANALYSIS[1].replace("{q}", question_text))
        self.click(locator)
        self.wait_vue_stable()
        logger.info("查看解析: %s", question_text[:30])

    def click_remove(self, question_text):
        """点击移出错题本"""
        locator = (By.XPATH, self.ROW_REMOVE[1].replace("{q}", question_text))
        self.click(locator)
        self.wait_vue_stable()
        logger.info("移出错题: %s", question_text[:30])

    def confirm_remove(self):
        """确认移除 MessageBox"""
        self.confirm_message_box()

    # ==================================================================
    # 重新作答弹窗操作（推断，待数据就绪后验证）
    # ==================================================================

    def select_answer(self, option_index):
        """选择答案选项（按索引）"""
        options = self.find_all(
            (By.CSS_SELECTOR, '.el-dialog:not([style*="display: none"]) .el-radio')
        )
        if not options:
            options = self.find_all(
                (By.CSS_SELECTOR, '.el-dialog:not([style*="display: none"]) .el-checkbox')
            )
        if option_index < len(options):
            self._js_click_el(options[option_index])
            self.wait_vue_stable()
            logger.info("选择答案选项[%d]", option_index)

    def click_submit_answer(self):
        """提交答案"""
        self.click_dialog_save()
        logger.info("已提交答案")

    def get_result_text(self):
        """获取作答结果"""
        return self.get_toast()

    def close_redo_dialog(self):
        """关闭重新作答弹窗"""
        self.click_dialog_cancel()
