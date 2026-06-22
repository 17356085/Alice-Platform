"""水质分析对比 Page Object

路由: #/lab/water/compare
类型: 搜索表单 + 自定义对比表格

根据 AUTO_STRATEGY 建议，本页面无需拆分。当前实现基于现有代码重构，
将定位器提取为类属性，方法改为链式调用，并统一等待策略。

对应测试脚本: test_water_compare.py
"""

from selenium.webdriver.common.by import By

from base.base_page import BasePage


class WaterComparePage(BasePage):
    """水质分析对比 — 双位置选择+日期筛选+对比表格"""

    # ==================== 定位器 (来自 TECH_ANALYSIS) ====================
    # B级定位器：使用稳定的 placeholder 属性，若无更多 DOM 层级变化可继续使用
    START_DATE_INPUT = (By.CSS_SELECTOR, 'input[placeholder*="开始日期"]')
    END_DATE_INPUT = (By.CSS_SELECTOR, 'input[placeholder*="结束日期"]')

    # 查询/重置按钮：使用 Button 内 span 文本匹配，较现有 JS 实现更可维护
    QUERY_BTN = (By.XPATH, "//button[.//span[text()='查询']]")
    RESET_BTN = (By.XPATH, "//button[.//span[text()='重置']]")

    # 表格主体 (等待确保数据加载)
    TABLE_BODY = (By.CSS_SELECTOR, "div.el-table__body-wrapper table tbody")

    # ==================== 页面入口 ====================
    def navigate(self):
        """导航到化验室取样 → 水质分析 → 水质分析对比"""
        self.logger.info("导航到 → 化验室取样 → 水质分析 → 水质分析对比")
        self.navigate_to("化验室取样", "水质分析对比")
        # 内部已处理菜单动画 + 路由切换，再加一层稳定性等待
        self.wait_page_ready()
        self.wait_vue_stable()
        return self

    # ==================== 搜索条件 ====================
    def set_start_date(self, date_str: str):
        """输入开始日期

        Args:
            date_str: 日期字符串，格式如 '2026-01-01'
        """
        self.logger.info("设置开始日期: %s", date_str)
        el = self.wait_for_element_visible(self.START_DATE_INPUT)
        el.clear()
        el.send_keys(date_str)
        self.wait_vue_stable()
        return self

    def set_end_date(self, date_str: str):
        """输入结束日期

        Args:
            date_str: 日期字符串，格式如 '2026-06-12'
        """
        self.logger.info("设置结束日期: %s", date_str)
        el = self.wait_for_element_visible(self.END_DATE_INPUT)
        el.clear()
        el.send_keys(date_str)
        self.wait_vue_stable()
        return self

    def click_query(self):
        """点击查询按钮并等待表格加载"""
        self.logger.info("点击查询按钮")
        self.wait_for_element_clickable(self.QUERY_BTN).click()
        # 等待加载动画消失 + Vue 稳定
        self.wait_loading_gone()
        self.wait_vue_stable()
        return self

    def click_reset(self):
        """点击重置按钮并等待界面稳定"""
        self.logger.info("点击重置按钮")
        self.wait_for_element_clickable(self.RESET_BTN).click()
        self.wait_loading_gone()
        self.wait_vue_stable()
        return self

    # ==================== 页面状态 ====================
    def is_page_loaded(self) -> bool:
        """验证页面关键元素已加载"""
        self.logger.info("验证水质分析对比页面是否加载完成")
        self.wait_vue_stable()
        self.wait_loading_gone()
        # 检查日期输入框和表格/空状态至少存在一个
        has_date_input = self.is_element_present(self.START_DATE_INPUT)
        has_table_or_empty = self.driver.execute_script(
            "return !!(document.querySelector('div.el-table__body-wrapper table tbody') "
            "|| document.querySelector('div.el-table__empty-block'));"
        )
        return bool(has_date_input and has_table_or_empty)

    # ==================== 表格数据 ====================
    def get_table_row_count(self) -> int:
        """获取当前表格数据行数

        Returns:
            当前可见数据行数，若无表格或异常返回 0
        """
        self.logger.info("获取水质分析对比表格行数")
        try:
            rows = self.wait_for_elements_visible(self.TABLE_BODY)
            # wait_for_elements_visible 返回 WebElement 列表
            visible_rows = [r for r in rows if r.is_displayed()]
            count = len(visible_rows)
            self.logger.info("当前表格行数: %s", count)
            return count
        except Exception:
            self.logger.warning("表格不可用或不存在，返回 0")
            return 0