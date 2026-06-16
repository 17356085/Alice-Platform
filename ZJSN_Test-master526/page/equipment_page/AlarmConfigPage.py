"""设备报警配置页面 Page Object

稳定方法：导航/统计卡片/搜索/表格/分页 — 已验证通过
弹窗方法：暂标记 @skip，因 Element Plus 2.x filterable el-select
          + Selenium is_displayed() 对 teleport 元素失效
"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage
from config import TIMEOUT_CONFIG

logger = logging.getLogger(__name__)


class AlarmConfigPage(BasePage):
    """设备报警配置页面"""

    # ══════════════════════════════════════════════════════════════════
    #  统计卡片 — 非 BEM 命名，标签在下、数字在上
    # ══════════════════════════════════════════════════════════════════
    STAT_VALUE_XPATH = (
        By.XPATH,
        '//*[contains(normalize-space(.),"{label}")]/preceding-sibling::*[1]',
    )
    STAT_CARD_CONTAINER = (By.CSS_SELECTOR, '.stat-value')

    # ══════════════════════════════════════════════════════════════════
    #  搜索区
    # ══════════════════════════════════════════════════════════════════
    INPUT_KEYWORD = (
        By.CSS_SELECTOR,
        'input[placeholder="报警名称/设备名称"]',
    )
    SELECT_ALARM_TYPE = (
        By.XPATH,
        '(//form[contains(@class,"el-form--inline")]'
        '//div[contains(@class,"el-select")])[1]',
    )
    SELECT_ALARM_LEVEL = (
        By.XPATH,
        '(//form[contains(@class,"el-form--inline")]'
        '//div[contains(@class,"el-select")])[2]',
    )
    SELECT_STATUS = (
        By.XPATH,
        '(//form[contains(@class,"el-form--inline")]'
        '//div[contains(@class,"el-select")])[3]',
    )
    BTN_SEARCH = (
        By.XPATH,
        '//form[contains(@class,"el-form--inline")]'
        '//button[contains(@class,"el-button--primary")][contains(.,"查询")]',
    )
    BTN_RESET = (
        By.XPATH,
        '//form[contains(@class,"el-form--inline")]'
        '//button[contains(.,"重置")]',
    )
    BTN_ADD = (
        By.XPATH,
        '//button[contains(.,"新增配置")]',
    )

    # ══════════════════════════════════════════════════════════════════
    #  表格 — fixed-right 克隆风险
    # ══════════════════════════════════════════════════════════════════
    TABLE_HEADER_CELLS = (
        By.CSS_SELECTOR,
        '.el-table__header-wrapper th .cell',
    )
    TABLE_ROWS = (
        By.CSS_SELECTOR,
        '.el-table__body-wrapper tbody tr.el-table__row',
    )
    TABLE_EMPTY = (
        By.CSS_SELECTOR,
        '.el-table__empty-text',
    )
    COL_ALARM_NAME = 1

    # ══════════════════════════════════════════════════════════════════
    #  弹窗
    # ══════════════════════════════════════════════════════════════════
    DIALOG_SAVE_BTN = (
        By.XPATH,
        '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
        '//button[contains(@class,"el-button--primary")][contains(.,"确定")]',
    )
    DIALOG_CANCEL_BTN = (
        By.XPATH,
        '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
        '//button[contains(.,"取消")]',
    )

    # ══════════════════════════════════════════════════════════════════
    #  构造 & 导航
    # ══════════════════════════════════════════════════════════════════

    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    def navigate_to_alarm_config(self):
        """导航 + JS hash 兜底"""
        logger.info("导航到 → 设备管理 → 设备报警配置")
        try:
            self.navigate_to("设备管理", "设备报警配置")
            url = self.driver.current_url
            if 'alarm-config' not in url:
                self.driver.execute_script(
                    "window.location.hash = '#/equipment/alarm-config'")
        except Exception:
            self.driver.execute_script(
                "window.location.hash = '#/equipment/alarm-config'")
        self._wait_page_ready()

    # ══════════════════════════════════════════════════════════════════
    #  页面就绪等待
    # ══════════════════════════════════════════════════════════════════

    def _wait_page_ready(self, timeout=25):
        """合并等待: loading消失 + 主内容区出现"""
        self.wait_page_ready(timeout=30)        # document.readyState == 'complete'
        self._wait_loading_gone(timeout)
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.find_elements(
                    By.CSS_SELECTOR, '.el-table__body-wrapper')
            )
        except TimeoutException:
            logger.warning("表格 body 在 %ds 内未出现", timeout)
        self.wait_vue_stable()

    def _wait_table_ready(self, timeout=5):
        """轻量等待: 数据行或空状态"""
        self.wait_vue_stable()
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, 'tr.el-table__row')
                or d.find_elements(By.CSS_SELECTOR, '.el-table__empty-text')
            )
        except TimeoutException:
            pass

    # ══════════════════════════════════════════════════════════════════
    #  统计卡片
    # ══════════════════════════════════════════════════════════════════

    def _parse_stat(self, label):
        try:
            loc = (By.XPATH,
                   f'//*[contains(normalize-space(.),"{label}")]/preceding-sibling::*[1]')
            text = self.get_text(loc, timeout=3)
            return int(text.strip())
        except (ValueError, TypeError, TimeoutException):
            return 0

    def get_all_stats(self):
        return {
            'total': self._parse_stat("报警规则总数"),
            'enabled': self._parse_stat("已启用"),
            'disabled': self._parse_stat("已禁用"),
            'today': self._parse_stat("今日报警"),
        }

    def get_stat_card_count(self):
        for _ in range(4):
            cards = self.find_all(self.STAT_CARD_CONTAINER)
            if len(cards) >= 4:
                return len(cards)
            self.wait_vue_stable()
        return len(self.find_all(self.STAT_CARD_CONTAINER))

    # ══════════════════════════════════════════════════════════════════
    #  搜索区
    # ══════════════════════════════════════════════════════════════════

    def search_keyword(self, keyword):
        self.input_text(self.INPUT_KEYWORD, keyword or '')

    def click_search(self):
        self.click(self.BTN_SEARCH)
        self._wait_table_ready()

    def click_reset(self):
        self.click(self.BTN_RESET)
        self._wait_table_ready()

    def is_search_input_visible(self):
        return self.is_visible(self.INPUT_KEYWORD, timeout=3)

    def is_add_button_visible(self):
        return self.is_visible(self.BTN_ADD, timeout=3)

    # ══════════════════════════════════════════════════════════════════
    #  表格
    # ══════════════════════════════════════════════════════════════════

    def get_table_headers(self):
        """JS提取表格表头（含重试，应对Element Plus异步渲染）"""
        for attempt in range(6):
            try:
                self.wait_vue_stable()
                self._wait_table_ready()
            except Exception:
                pass
            headers = self.driver.execute_script("""
                return Array.from(
                    document.querySelectorAll('.el-table__header-wrapper th .cell')
                ).map(function(el) { return el.textContent.trim(); }).filter(Boolean);
            """)
            if headers and len(headers) >= 3:
                return headers
            self.wait_vue_stable()
        return []

    def get_table_row_count(self):
        self._wait_table_ready()
        rows = self.find_all(self.TABLE_ROWS)
        return sum(1 for r in rows if r.is_displayed())

    def get_cell(self, row_index, col_index):
        self._wait_table_ready()
        try:
            rows = self.find_all(self.TABLE_ROWS)
            if 1 <= row_index <= len(rows):
                cells = rows[row_index - 1].find_elements(
                    By.TAG_NAME, 'td')
                if 1 <= col_index <= len(cells):
                    return cells[col_index - 1].text.strip()
            return ''
        except Exception:
            return ''

    def is_table_empty(self):
        try:
            return self.is_visible(self.TABLE_EMPTY, timeout=3)
        except Exception:
            return self.get_table_row_count() == 0
