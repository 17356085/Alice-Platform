"""生产日报表页面 Page Object

==== 页面概述 ====
  路径：生产管理 → 日报表管理
  路由：#/production/daily-report
  功能：按日期查看产品/原料/公辅工程/冷剂消耗四区生产数据，支持录入/补录/趋势/导出

==== 定位策略 ====
  1. CSS_SELECTOR：placeholder / Element Plus 标准类
  2. 相对 XPath：按钮文本匹配 / 弹窗标题匹配
  3. 禁止：绝对 XPath（/html/body/div[n]/...）
"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage
from config import TIMEOUT_CONFIG

logger = logging.getLogger(__name__)


class DailyReportPage(BasePage):
    """生产日报表页面"""

    # ══════════════════════════════════════════════════════════════════
    #  搜索/操作区
    # ══════════════════════════════════════════════════════════════════
    DATE_PICKER_INPUT = (
        By.CSS_SELECTOR,
        'input[placeholder="请选择日期"]',
    )

    # 操作按钮 — XPath 文本匹配
    BTN_SEARCH = (
        By.XPATH,
        '//button[contains(@class,"el-button--primary")][contains(.,"查询")]',
    )
    BTN_ENTER_DATA = (
        By.XPATH,
        '//button[contains(.,"录入数据")]',
    )
    BTN_SUPPLEMENT = (
        By.XPATH,
        '//button[contains(.,"补录数据")]',
    )
    BTN_ADJUST = (
        By.XPATH,
        '//button[contains(.,"调整数据")]',
    )
    BTN_TREND = (
        By.XPATH,
        '//button[contains(.,"趋势") and not(contains(.,"分析"))]',
    )
    BTN_EXPORT = (
        By.XPATH,
        '//button[contains(.,"导出") and not(contains(.,"确认导出"))]',
    )
    BTN_PRINT = (
        By.XPATH,
        '//button[contains(.,"打印")]',
    )

    # ══════════════════════════════════════════════════════════════════
    #  数据分区卡片 — 通过 section-title 文本定位卡片容器
    # ══════════════════════════════════════════════════════════════════
    # 分区卡片模板（内部使用，不直接作为定位器使用）
    # 注意：dashboard 分区用 <span class="section-title">，生产分区用 <div class="section-title">
    _SECTION_CARD_XPATH = (
        '//*[contains(@class,"section-title") and contains(.,"{section_name}")]'
        '/ancestor::div[contains(@class,"el-card")]'
    )
    _SECTION_TABLE = (
        By.CSS_SELECTOR,
        '.el-table',
    )
    _SECTION_TABLE_ROWS = (
        By.CSS_SELECTOR,
        '.el-table__body-wrapper tbody tr.el-table__row',
    )
    _SECTION_TABLE_HEADERS = (
        By.CSS_SELECTOR,
        '.el-table__header-wrapper th .cell',
    )
    _SECTION_CARD_HEADER = (
        By.CSS_SELECTOR,
        '.el-card__header',
    )

    # ══════════════════════════════════════════════════════════════════
    #  弹窗 — 通过 el-dialog + 标题定位
    # ══════════════════════════════════════════════════════════════════
    _DIALOG_BY_TITLE_XPATH = (
        '//div[contains(@class,"el-dialog") and .//span[contains(@class,"el-dialog__title")'
        ' and contains(.,"{title}")]]'
    )
    DIALOG_TITLE = (
        By.CSS_SELECTOR,
        '.el-dialog__title',
    )
    DIALOG_CONFIRM = (
        By.XPATH,
        './/button[contains(@class,"el-button--primary")]',
    )
    DIALOG_CANCEL = (
        By.XPATH,
        './/button[contains(.,"取消")]',
    )

    # ══════════════════════════════════════════════════════════════════
    #  导航
    # ══════════════════════════════════════════════════════════════════
    def navigate_to_daily_report(self):
        """导航到生产日报表页面"""
        self.navigate_to("生产管理", "日报表管理")
        self.wait_vue_stable()
        self.wait_page_ready()
        # 等待日期选择器出现（页面核心元素，比分区卡片更早出现）
        try:
            self.wait_until_visible(self.DATE_PICKER_INPUT, timeout=15)
        except TimeoutException:
            logger.warning("日期选择器未在15s内可见，继续尝试")
        self.wait_vue_stable()
        return self

    # ══════════════════════════════════════════════════════════════════
    #  日期选择器操作
    # ══════════════════════════════════════════════════════════════════
    def select_date(self, date_str):
        """选择日期（格式: yyyy-MM-dd 或 yyyy/MM/dd）

        用法:
            page.select_date("2026-06-12")
        """
        logger.info("选择日期: %s", date_str)
        date_input = self.find(self.DATE_PICKER_INPUT)
        date_input.click()
        self.wait_vue_stable()
        # 清空并输入日期
        date_input.clear()
        date_input.send_keys(date_str)
        # 按 Enter 确认（关闭日期面板）
        from selenium.webdriver.common.keys import Keys
        date_input.send_keys(Keys.ENTER)
        self.wait_vue_stable()
        return self

    def get_current_date(self):
        """获取日期选择器当前值"""
        el = self.find(self.DATE_PICKER_INPUT)
        return el.get_attribute("value") or ""

    # ══════════════════════════════════════════════════════════════════
    #  操作按钮
    # ══════════════════════════════════════════════════════════════════
    def click_search(self):
        """点击查询按钮"""
        logger.info("点击查询按钮")
        self.click(self.BTN_SEARCH)
        self.wait_vue_stable()
        # 等待 loading 遮罩消失（如果存在）
        self.wait_overlay_gone(timeout=15)
        return self

    def click_enter_data(self):
        """点击录入数据按钮"""
        logger.info("点击录入数据按钮")
        self._js_click_by_text("录入数据")
        self._wait_dialog_open("录入数据")
        return self

    def click_supplement(self):
        """点击补录数据按钮"""
        logger.info("点击补录数据按钮")
        self._js_click_by_text("补录数据")
        self._wait_dialog_open("补录数据")
        return self

    def click_trend(self):
        """点击趋势按钮"""
        logger.info("点击趋势按钮")
        self._js_click_by_text("趋势")
        self._wait_dialog_open("趋势分析")
        return self

    def click_export(self):
        """点击导出按钮"""
        logger.info("点击导出按钮")
        self._js_click_by_text("导出")
        self._wait_dialog_open("生产日报表")
        return self

    def is_adjust_disabled(self):
        """检查调整数据按钮是否 disabled"""
        el = self.find(self.BTN_ADJUST)
        classes = el.get_attribute("class") or ""
        return "is-disabled" in classes

    def is_print_visible(self):
        """检查打印按钮是否可见"""
        return self.is_visible(self.BTN_PRINT)

    # ══════════════════════════════════════════════════════════════════
    #  分区表格操作
    # ══════════════════════════════════════════════════════════════════
    def _get_section_locator(self, section_name):
        """获取分区卡片的定位器"""
        return (By.XPATH, self._SECTION_CARD_XPATH.format(section_name=section_name))

    def get_section_table_headers(self, section_name):
        """获取指定分区的表头列表

        Args:
            section_name: 分区名称（"产品"/"原料"/"公辅工程"/"冷剂消耗"）
        Returns:
            list[str]: 表头文字列表
        """
        card_locator = self._get_section_locator(section_name)
        card = self.find(card_locator)
        headers = card.find_elements(*self._SECTION_TABLE_HEADERS)
        return [h.text.strip() for h in headers if h.text.strip()]

    def get_section_row_count(self, section_name):
        """获取指定分区的数据行数"""
        card_locator = self._get_section_locator(section_name)
        card = self.find(card_locator)
        rows = card.find_elements(*self._SECTION_TABLE_ROWS)
        return len(rows)

    def get_section_cell(self, section_name, row_index, col_index):
        """获取指定分区表格的单元格文本

        Args:
            section_name: 分区名称
            row_index: 行索引（0-based）
            col_index: 列索引（0-based）
        """
        card_locator = self._get_section_locator(section_name)
        card = self.find(card_locator)
        rows = card.find_elements(*self._SECTION_TABLE_ROWS)
        if row_index >= len(rows):
            raise IndexError(f"行索引 {row_index} 超出范围（共 {len(rows)} 行）")
        cells = rows[row_index].find_elements(By.CSS_SELECTOR, "td .cell")
        if col_index >= len(cells):
            raise IndexError(f"列索引 {col_index} 超出范围（共 {len(cells)} 列）")
        return cells[col_index].text.strip()

    def get_all_section_data(self, section_name):
        """获取指定分区全部数据

        Returns:
            list[list[str]]: 二维数组，每行是一个 list[str]
        """
        card_locator = self._get_section_locator(section_name)
        card = self.find(card_locator)
        rows = card.find_elements(*self._SECTION_TABLE_ROWS)
        data = []
        for row in rows:
            cells = row.find_elements(By.CSS_SELECTOR, "td .cell")
            data.append([c.text.strip() for c in cells])
        return data

    def is_section_table_empty(self, section_name):
        """检查分区表格是否为空（空数据状态）"""
        card_locator = self._get_section_locator(section_name)
        card = self.find(card_locator)
        empty_blocks = card.find_elements(By.CSS_SELECTOR, ".el-table__empty-block")
        return len(empty_blocks) > 0 and empty_blocks[0].is_displayed()

    def is_section_visible(self, section_name):
        """检查分区卡片是否可见"""
        locator = self._get_section_locator(section_name)
        return self.is_visible(locator, timeout=5)

    # ══════════════════════════════════════════════════════════════════
    #  弹窗操作
    # ══════════════════════════════════════════════════════════════════
    def _get_dialog_locator(self, title):
        """获取弹窗定位器"""
        return (By.XPATH, self._DIALOG_BY_TITLE_XPATH.format(title=title))

    def _wait_dialog_open(self, title, timeout=None):
        """等待指定标题的弹窗打开"""
        if timeout is None:
            timeout = TIMEOUT_CONFIG.get('dialog_open', 10)
        dialog_locator = self._get_dialog_locator(title)
        self.wait_until_visible(dialog_locator, timeout=timeout)
        self.wait_vue_stable()
        return self

    def wait_dialog_close(self, title, timeout=None):
        """等待指定标题的弹窗关闭"""
        if timeout is None:
            timeout = TIMEOUT_CONFIG.get('dialog_open', 10)
        dialog_locator = self._get_dialog_locator(title)
        self.wait_until_gone(dialog_locator, timeout=timeout)
        return self

    def is_dialog_open(self, title):
        """检查指定标题的弹窗是否打开"""
        dialog_locator = self._get_dialog_locator(title)
        return self.is_visible(dialog_locator, timeout=3)

    def get_dialog_title(self, title):
        """获取弹窗标题文本"""
        dialog_locator = self._get_dialog_locator(title)
        dialog = self.find(dialog_locator)
        title_el = dialog.find_element(*self.DIALOG_TITLE)
        return title_el.text.strip()

    def click_dialog_confirm(self, title):
        """点击弹窗确定/确认按钮"""
        dialog_locator = self._get_dialog_locator(title)
        dialog = self.find(dialog_locator)
        confirm_btn = dialog.find_element(*self.DIALOG_CONFIRM)
        confirm_btn.click()
        self.wait_vue_stable()
        return self

    def click_dialog_cancel(self, title):
        """关闭指定弹窗（优先点击取消按钮，兜底点 × 关闭）"""
        dialog_locator = self._get_dialog_locator(title)
        dialog = self.find(dialog_locator)
        try:
            # 优先：找"取消"按钮
            cancel_btn = dialog.find_element(*self.DIALOG_CANCEL)
            cancel_btn.click()
        except Exception:
            # 兜底：点击右上角 × 关闭按钮
            logger.info("弹窗'%s'无取消按钮，使用 × 关闭", title)
            close_btn = dialog.find_element(By.CSS_SELECTOR, ".el-dialog__headerbtn")
            close_btn.click()
        self.wait_dialog_close(title)
        return self

    # ══════════════════════════════════════════════════════════════════
    #  弹窗内操作（按弹窗类型）
    # ══════════════════════════════════════════════════════════════════

    # --- 录入数据弹窗 ---
    def enter_data_select_device(self, device_name):
        """在录入数据弹窗中选择装置"""
        self._select_dialog_dropdown("录入数据", device_name)
        return self

    def enter_data_confirm(self):
        """确认录入数据"""
        self.click_dialog_confirm("录入数据")
        return self

    # --- 补录数据弹窗 ---
    def supplement_select_device(self, device_name):
        """在补录数据弹窗中选择装置"""
        self._select_dialog_dropdown("补录数据", device_name)
        return self

    # --- 趋势分析弹窗 ---
    def trend_set_date_range(self, start_date, end_date):
        """设置趋势分析的日期范围"""
        dialog_locator = self._get_dialog_locator("趋势分析")
        dialog = self.find(dialog_locator)
        # 开始日期
        start_input = dialog.find_element(
            By.XPATH, './/input[@placeholder="开始日期"]'
        )
        start_input.clear()
        start_input.send_keys(start_date)
        # 结束日期
        end_input = dialog.find_element(
            By.XPATH, './/input[@placeholder="结束日期"]'
        )
        end_input.clear()
        end_input.send_keys(end_date)
        return self

    def trend_click_query(self):
        """在趋势分析弹窗中点击查询"""
        dialog_locator = self._get_dialog_locator("趋势分析")
        dialog = self.find(dialog_locator)
        query_btn = dialog.find_element(By.XPATH, './/button[contains(.,"查询")]')
        query_btn.click()
        self.wait_vue_stable()
        return self

    # --- 导出弹窗 ---
    def export_select_device(self, device_name):
        """在导出弹窗中选择装置"""
        self._select_dialog_dropdown("生产日报表", device_name)
        return self

    def export_confirm(self):
        """确认导出"""
        self.click_dialog_confirm("生产日报表")
        return self

    # ══════════════════════════════════════════════════════════════════
    #  内部辅助方法
    # ══════════════════════════════════════════════════════════════════
    def _js_click_by_text(self, text, exact=False):
        """用 JS 查找并点击匹配文本的按钮（绕过 Selenium 拦截问题）

        Args:
            text: 按钮文本（子串匹配）
            exact: 是否精确匹配
        """
        script = """
            var buttons = document.querySelectorAll('button, .el-button');
            for (var i = 0; i < buttons.length; i++) {
                var b = buttons[i];
                var btnText = (b.innerText || b.textContent || '').trim();
                if (arguments[0] ? (btnText === arguments[1]) : (btnText.indexOf(arguments[1]) >= 0)) {
                    if (b.offsetParent !== null && !b.classList.contains('is-disabled')) {
                        b.click();
                        return {clicked: true, text: btnText, index: i};
                    }
                }
            }
            return {clicked: false};
        """
        result = self.driver.execute_script(script, exact, text)
        if result and result.get('clicked'):
            logger.info("JS点击成功: '%s' (按钮[%d])", result['text'], result['index'])
        else:
            logger.warning("JS点击未找到匹配按钮: '%s'", text)
        self.wait_vue_stable()
        return self

    def _select_dialog_dropdown(self, dialog_title, option_text):
        """在指定弹窗中选择下拉选项"""
        dialog_locator = self._get_dialog_locator(dialog_title)
        dialog = self.find(dialog_locator)
        # 点击弹窗内的 el-select 触发展开
        select = dialog.find_element(By.CSS_SELECTOR, ".el-select")
        select.click()
        self.wait_vue_stable()
        # 在 body 下的下拉列表中查找选项（Teleport 渲染）
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        option_locator = (
            By.XPATH,
            f'//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]'
            f'//li[contains(@class,"el-select-dropdown__item")]//span[contains(.,"{option_text}")]',
        )
        try:
            option = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(option_locator)
            )
            option.click()
            self.wait_vue_stable()
        except TimeoutException:
            logger.warning("下拉选项 '%s' 未找到或不可点击", option_text)
        return self
