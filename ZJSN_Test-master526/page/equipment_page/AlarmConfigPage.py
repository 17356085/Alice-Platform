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

    # ══════════════════════════════════════════════════════════════════
    #  弹窗操作 — teleport-safe el-select
    # ══════════════════════════════════════════════════════════════════

    def _select_dialog_option(self, label, option_text):
        """在弹窗中选择指定 label 的 el-select 下拉选项（teleport 安全）

        原理: Element Plus 2.x filterable el-select 下拉列表 teleport 到 body，
        Selenium is_displayed() 对其失效。改用 WebDriverWait + element_to_be_clickable
        在 body 下直接定位下拉列表项。
        """
        # 1. 定位弹窗内对应 label 的 el-select 容器并点击展开
        select_xpath = (
            '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
            f'//label[contains(.,"{label}")]/following-sibling::div'
            '//div[contains(@class,"el-select")]'
        )
        select_el = WebDriverWait(self.driver, 8).until(
            EC.element_to_be_clickable((By.XPATH, select_xpath))
        )
        self.driver.execute_script("arguments[0].click();", select_el)
        self.wait_vue_stable()

        # 2. 在 body 下定位下拉列表项（teleport 渲染），点击匹配项
        option_xpath = (
            '//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]'
            f'//li[contains(@class,"el-select-dropdown__item")]//span[contains(.,"{option_text}")]'
        )
        try:
            option = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, option_xpath))
            )
            self.driver.execute_script("arguments[0].click();", option)
            self.wait_vue_stable()
        except TimeoutException:
            logger.warning("下拉选项 '%s' → '%s' 未找到，重新抛出", label, option_text)
            raise TimeoutException(f"dropdown option not found: label='{label}', option='{option_text}'")

    def _fill_dialog_input(self, label, value):
        """在弹窗中填写指定 label 的 input 字段"""
        input_xpath = (
            '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
            f'//label[contains(.,"{label}")]/following-sibling::div//input'
        )
        inp = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, input_xpath))
        )
        inp.clear()
        inp.send_keys(value)

    def click_add_config(self):
        """点击新增配置按钮，等待弹窗出现"""
        self.click(self.BTN_ADD)
        self.wait_dialog_open()

    def fill_alarm_name(self, name):
        """填写报警名称"""
        self._fill_dialog_input("报警名称", name)

    def select_alarm_type(self, type_name):
        """选择报警类型（teleport-safe）"""
        self._select_dialog_option("报警类型", type_name)

    def select_alarm_level(self, level):
        """选择报警级别（teleport-safe）"""
        self._select_dialog_option("报警级别", level)

    def select_device(self, device_name):
        """选择关联设备"""
        self._select_dialog_option("关联设备", device_name)

    def select_notify_mode(self, mode):
        """选择通知方式"""
        self._select_dialog_option("通知方式", mode)

    def click_dialog_confirm(self):
        """点击弹窗确定按钮，等待弹窗关闭"""
        self.click(self.DIALOG_SAVE_BTN)
        self.wait_dialog_close()

    def click_dialog_cancel(self):
        """点击弹窗取消按钮"""
        self.click(self.DIALOG_CANCEL_BTN)
        self.wait_dialog_close()

    # ── 行级操作 ────────────────────────────────────────────

    def click_row_edit(self, row_index=0):
        """点击指定行的编辑按钮"""
        rows = self.find_all(self.TABLE_ROWS)
        edit_btns = rows[row_index].find_elements(
            By.XPATH, './/button[contains(.,"编辑")]')
        if edit_btns:
            self.driver.execute_script("arguments[0].click();", edit_btns[0])
        self.wait_dialog_open()

    def click_row_delete(self, row_index=0):
        """点击指定行的删除按钮"""
        rows = self.find_all(self.TABLE_ROWS)
        del_btns = rows[row_index].find_elements(
            By.XPATH, './/button[contains(.,"删除")]')
        if del_btns:
            self.driver.execute_script("arguments[0].click();", del_btns[0])
        self.wait_vue_stable()

    def click_row_view(self, row_index=0):
        """点击指定行的查看按钮"""
        rows = self.find_all(self.TABLE_ROWS)
        view_btns = rows[row_index].find_elements(
            By.XPATH, './/button[contains(.,"查看")]')
        if view_btns:
            self.driver.execute_script("arguments[0].click();", view_btns[0])
        self.wait_dialog_open()

    def click_status_toggle(self, row_index=0):
        """点击指定行的状态开关（el-switch）"""
        rows = self.find_all(self.TABLE_ROWS)
        switch = rows[row_index].find_element(By.CSS_SELECTOR, '.el-switch')
        self.driver.execute_script("arguments[0].click();", switch)
        self.wait_vue_stable()
