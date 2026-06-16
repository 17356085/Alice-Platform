"""系统日志页面 Page Object — 重构版

变更记录:
  2026-06-11: 继承 BasePage，清理绝对 XPath，替换 time.sleep → BasePage 等待方法
"""
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class SystemLogPage(BasePage):
    """系统日志页面操作 — 继承 BasePage"""

    # ══════════════════════════════════════════════════════════════════
    #  导航 — 复用 BasePage.navigate_to("系统管理", "日志管理", "系统日志")
    # ══════════════════════════════════════════════════════════════════
 
    LOG_TYPE_INPUT = (
        By.XPATH,
        '//label[normalize-space(.)="日志类型"]/following::div[contains(@class,"el-select")][1]'
        ' | //div[contains(@class,"el-select")][.//span[contains(normalize-space(.),"请选择日志类型")]',
    )
    LOG_LEVEL_INPUT = (
        By.XPATH,
        '//label[normalize-space(.)="日志级别"]/following::div[contains(@class,"el-select")][1]'
        ' | //div[contains(@class,"el-select")][.//span[contains(normalize-space(.),"请选择日志级别")]',
    )
    MODULE_NAME_INPUT = (By.XPATH, '//input[contains(@placeholder,"请输入模块名称")]')
 
    DATE_START_INPUT = (By.XPATH, '//input[contains(@placeholder,"开始日期")]')
    DATE_END_INPUT = (By.XPATH, '//input[contains(@placeholder,"结束日期")]')
    DATE_RANGE_PICKER_PANEL = (
        By.XPATH,
        '(//div[contains(@class,"el-date-range-picker") or contains(@class,"el-picker-panel")][not(contains(@style,"display: none"))])[last()]',
    )
 
    SELECT_DROPDOWN_PANEL = (
        By.XPATH,
        '(//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))])[last()]',
    )
 
    SEARCH_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="搜索"] or normalize-space(.)="搜索"]')
    RESET_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="重置"] or normalize-space(.)="重置"]')
    TOOLBAR_CLEAR = (By.XPATH, '//button[.//span[normalize-space(.)="清空"] or normalize-space(.)="清空"]')
 
    LOADING_MASK = (By.CSS_SELECTOR, ".el-loading-mask")
    EMPTY_TEXT = (By.CSS_SELECTOR, ".el-table__empty-text")
    TABLE_HEADERS = (By.XPATH, '//div[contains(@class,"el-table__header-wrapper")]//th//div')
    TABLE_ROWS = (By.XPATH, '//div[contains(@class,"el-table__body-wrapper")]//table/tbody/tr')
 
    PAGINATION = (By.CSS_SELECTOR, ".el-pagination")
    CURRENT_PAGE = (By.CSS_SELECTOR, ".el-pagination .el-pager li.active, .el-pagination .el-pager li.is-active")
    NEXT_PAGE = (By.CSS_SELECTOR, ".el-pagination button.btn-next:not([disabled])")
 
    MESSAGEBOX_CONFIRM = (
        By.XPATH,
        '(//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))])[last()]//button[.//*[normalize-space(.)="确定"] or normalize-space(.)="确定"]',
    )
    MESSAGEBOX_CONFIRM_FALLBACKS = [
        (By.XPATH, '(//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))])[last()]//button[2]'),
    ]
 
    TOAST_TEXT = (By.CSS_SELECTOR, ".el-message__content")
    TOAST_TEXT_FALLBACK = (By.CSS_SELECTOR, 'div[id^="message_"] p, div[id^="message_"] .el-message__content, div[id^="message_"]')
 
    def __init__(self, driver, timeout=None):
        """初始化 — 继承 BasePage"""
        super().__init__(driver, timeout)
 
    def _wait_settled(self, timeout=10):
        end = time.time() + timeout
        while time.time() < end:
            masks = self.driver.find_elements(*self.LOADING_MASK)
            visible = False
            for m in masks:
                try:
                    if m.is_displayed():
                        visible = True
                        break
                except Exception:
                    continue
            if not visible:
                return
            self.wait_vue_stable()
 
    def wait_for_toast_text(self, timeout=6):
        end = time.time() + timeout
        last = ""
        while time.time() < end:
            els = []
            try:
                els.extend(self.driver.find_elements(*self.TOAST_TEXT_FALLBACK))
            except Exception:
                pass
            try:
                els.extend(self.driver.find_elements(*self.TOAST_TEXT))
            except Exception:
                pass
            for el in els:
                try:
                    t = (el.text or "").strip()
                    if t:
                        last = t
                except Exception:
                    continue
            if last:
                return last
            self.wait_vue_stable()
        return last
 
    def _first_displayed(self, locator, timeout=2):
        end = time.time() + timeout
        last_err = None
        while time.time() < end:
            try:
                els = self.driver.find_elements(*locator)
                for el in els:
                    try:
                        if el.is_displayed():
                            return el
                    except Exception:
                        continue
            except Exception as e:
                last_err = e
            self.wait_vue_stable()
        if last_err:
            raise last_err
        raise TimeoutException(f"未找到元素: {locator}")
 
    # ══════════════════════════════════════════════════════════════════
    #  导航（重构：使用 BasePage.navigate_to）
    # ══════════════════════════════════════════════════════════════════

    def navigate(self):
        """导航到系统日志页面 — 唯一入口"""
        logger.info("导航到 → 系统管理 → 日志管理 → 系统日志")
        self.navigate_to("系统管理", "日志管理", "系统日志")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=12)
        self.wait_vue_stable()
        return self

    def navigate_to_system_log(self):
        """@deprecated: 使用 navigate() 替代"""
        return self.navigate()
 
    def _clear_input(self, locator):
        el = self.wait.until(EC.presence_of_element_located(locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        return el
 
    def _select_dropdown_option(self, input_locator, option_text):
        self._wait_settled(timeout=6)
        inp = self.wait.until(EC.presence_of_element_located(input_locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", inp)
        try:
            self.driver.execute_script("arguments[0].click();", inp)
        except Exception:
            try:
                inp.click()
            except Exception:
                self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles:true}));", inp)
        WebDriverWait(self.driver, 6).until(EC.presence_of_element_located(self.SELECT_DROPDOWN_PANEL))

        def _get_option_locators():
            txt = option_text
            return [
                (
                    By.XPATH,
                    f'(//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]'
                    f'//li[contains(@class,"el-select-dropdown__item") and not(contains(@class,"is-disabled"))]'
                    f'[.//span[normalize-space(.)="{txt}"]])[last()]',
                ),
                (
                    By.XPATH,
                    f'(//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]'
                    f'//*[self::li or self::div][not(contains(@class,"is-disabled"))]'
                    f'[.//*[normalize-space(.)="{txt}"]])[last()]',
                ),
                (
                    By.XPATH,
                    f'(//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]'
                    f'//*[self::li or self::div][not(contains(@class,"is-disabled"))]'
                    f'[.//*[contains(normalize-space(.),"{txt}")]])[last()]',
                ),
                (
                    By.XPATH,
                    f'(//div[contains(@class,"el-popper") and not(contains(@style,"display: none"))]'
                    f'//*[self::li or self::div][not(contains(@class,"is-disabled"))]'
                    f'[.//*[normalize-space(.)="{txt}"]])[last()]',
                ),
                (
                    By.XPATH,
                    f'(//div[contains(@class,"el-popper") and not(contains(@style,"display: none"))]'
                    f'//*[self::li or self::div][not(contains(@class,"is-disabled"))]'
                    f'[.//*[contains(normalize-space(.),"{txt}")]])[last()]',
                ),
            ]

        def _snapshot_visible_dropdown_texts(limit=30):
            texts = []
            xps = [
                '//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]'
                '//li[not(contains(@class,"is-disabled"))]//span',
                '//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]'
                '//*[contains(@class,"el-select-dropdown__item")]',
                '//div[contains(@class,"el-popper") and not(contains(@style,"display: none"))]'
                '//li//span',
            ]
            for xp in xps:
                try:
                    for el in self.driver.find_elements(By.XPATH, xp):
                        try:
                            t = (el.text or "").strip()
                            if t and t not in texts:
                                texts.append(t)
                                if len(texts) >= limit:
                                    return texts
                        except Exception:
                            continue
                except Exception:
                    continue
            return texts

        option = None
        for _ in range(2):
            for loc in _get_option_locators():
                try:
                    cand = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(loc))
                    try:
                        if not cand.is_displayed():
                            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", cand)
                    except Exception:
                        pass
                    option = cand
                    break
                except Exception:
                    continue
            if option:
                break
            try:
                self.driver.execute_script("arguments[0].click();", inp)
            except Exception:
                pass
            self.wait_vue_stable()

        if not option:
            opts = _snapshot_visible_dropdown_texts(limit=30)
            raise TimeoutException(f"未找到下拉选项：{option_text}；可见选项：{opts}")

        self.driver.execute_script("arguments[0].click();", option)
        self.wait_vue_stable()
 
    def select_log_type(self, text):
        self._select_dropdown_option(self.LOG_TYPE_INPUT, text)
 
    def select_log_level(self, text):
        self._select_dropdown_option(self.LOG_LEVEL_INPUT, text)
 
    def input_module_name(self, value):
        el = self._clear_input(self.MODULE_NAME_INPUT)
        if value:
            el.send_keys(value)
 
    def set_operation_date_range(self, start_date, end_date):
        start = self.wait.until(EC.presence_of_element_located(self.DATE_START_INPUT))
        end = self.wait.until(EC.presence_of_element_located(self.DATE_END_INPUT))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", start)
 
        def _type_into(el, text):
            try:
                el.click()
            except Exception:
                pass
            el.send_keys(Keys.CONTROL + "a")
            el.send_keys(Keys.DELETE)
            el.send_keys(text)
 
        def _js_set(el, text):
            self.driver.execute_script(
                "arguments[0].value = arguments[1];"
                "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
                "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));"
                "arguments[0].dispatchEvent(new Event('blur', {bubbles:true}));",
                el,
                text,
            )
 
        try:
            _type_into(start, start_date)
            _type_into(end, end_date)
            end.send_keys(Keys.ENTER)
        except Exception:
            _js_set(start, start_date)
            _js_set(end, end_date)
            try:
                self.driver.execute_script("document.body.click();")
            except Exception:
                pass
        self.wait_vue_stable()
        self._try_click_date_range_days(start_date, end_date)
 
    def get_operation_date_range_values(self):
        try:
            start = self.driver.find_element(*self.DATE_START_INPUT)
            end = self.driver.find_element(*self.DATE_END_INPUT)
            return ((start.get_attribute("value") or "").strip(), (end.get_attribute("value") or "").strip())
        except Exception:
            return ("", "")
 
    def _try_click_date_range_days(self, start_date, end_date):
        try:
            start_day = int(str(start_date).split("-")[-1])
            end_day = int(str(end_date).split("-")[-1])
        except Exception:
            return False
 
        try:
            start = self.driver.find_element(*self.DATE_START_INPUT)
            self.driver.execute_script("arguments[0].click();", start)
        except Exception:
            return False
 
        def _click_day(day, pick_last=False):
            panel = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(self.DATE_RANGE_PICKER_PANEL))
            day_text = str(int(day))
            xps = [
                f'.//td[contains(@class,"available") and not(contains(@class,"disabled"))]//span[normalize-space(.)="{day_text}"]',
                f'.//span[contains(@class,"el-date-table-cell__text") and normalize-space(.)="{day_text}"]',
            ]
            els = []
            for xp in xps:
                try:
                    els = panel.find_elements(By.XPATH, xp)
                    els = [e for e in els if e.is_displayed()]
                    if els:
                        break
                except Exception:
                    continue
            if not els:
                raise TimeoutException(f"未找到日期：{day_text}")
            el = els[-1] if pick_last else els[0]
            self.driver.execute_script("arguments[0].click();", el)
 
        try:
            _click_day(start_day, pick_last=False)
            self.wait_vue_stable()
            _click_day(end_day, pick_last=True)
            self.wait_vue_stable()
            return True
        except Exception:
            return False
 
    def click_search(self):
        self._wait_settled(timeout=6)
        btn = self._first_displayed(self.SEARCH_BUTTON, timeout=4)
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_settled(timeout=10)
 
    def click_reset(self):
        self._wait_settled(timeout=6)
        locators = [
            self.RESET_BUTTON,
            (By.XPATH, '//*[@id="app"]//form/div[5]//button[2]'),
            (By.XPATH, '//*[@id="app"]//form//div[contains(@class,"el-form-item")][last()]//button[2]'),
        ]
        btn = None
        for loc in locators:
            try:
                btn = self._first_displayed(loc, timeout=4)
                if btn:
                    break
            except Exception:
                continue
        if not btn:
            raise TimeoutException("未找到重置按钮")
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_settled(timeout=10)
 
    def click_clear(self):
        self._wait_settled(timeout=6)
        btn = self._first_displayed(self.TOOLBAR_CLEAR, timeout=4)
        self.driver.execute_script("arguments[0].click();", btn)
        self.wait_vue_stable()
 
    def confirm_message_box_if_present(self):
        try:
            btn = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(self.MESSAGEBOX_CONFIRM))
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_vue_stable()
            return True
        except Exception:
            for loc in self.MESSAGEBOX_CONFIRM_FALLBACKS:
                try:
                    btn = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(loc))
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_vue_stable()
                    return True
                except Exception:
                    continue
            return False
 
    def get_empty_text(self):
        self._wait_settled(timeout=8)
        try:
            el = self.driver.find_element(*self.EMPTY_TEXT)
            return (el.text or "").strip()
        except Exception:
            return ""
 
    def get_table_headers(self):
        """JS提取表格表头（含重试，应对Element Plus异步渲染）"""
        import time
        for attempt in range(6):
            try:
                self._wait_table_ready() if hasattr(self, '_wait_table_ready') else self._wait_loading_gone(timeout=5)
            except:
                self._wait_loading_gone(timeout=5)
            self._wait_loading_gone(timeout=3)
            headers = self.driver.execute_script("""
                return Array.from(
                    document.querySelectorAll('.el-table__header-wrapper th .cell')
                ).map(function(el) { return el.textContent.trim(); }).filter(Boolean);
            """)
            if headers and len(headers) >= 3:
                return headers
            self._wait_loading_gone(timeout=5)
        return []
    def get_table_row_count(self):
        self._wait_settled(timeout=10)
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        count = 0
        for r in rows:
            try:
                if r.is_displayed():
                    count += 1
            except Exception:
                continue
        return count
 
    def get_column_index_by_header(self, header_text):
        self._wait_settled(timeout=10)
        ths = self.driver.find_elements(By.XPATH, '//div[contains(@class,"el-table__header-wrapper")]//table//th')
        for idx, th in enumerate(ths, start=1):
            try:
                t = (th.text or "").strip()
                if t == header_text:
                    return idx
            except Exception:
                continue
        return None
 
    def get_column_data(self, col_index):
        self._wait_settled(timeout=10)
        cell_xpath = f'//div[contains(@class,"el-table__body-wrapper")]//tbody/tr/td[{col_index}]//div[contains(@class,"cell")]'
        cells = self.driver.find_elements(By.XPATH, cell_xpath)
        values = []
        for c in cells:
            try:
                t = (c.text or "").strip().replace("\n", " ").strip()
                if t:
                    values.append(t)
            except Exception:
                continue
        return values
 
    def get_column_data_by_header(self, header_text):
        idx = self.get_column_index_by_header(header_text)
        if not idx:
            return []
        return self.get_column_data(idx)
 
    def get_current_page_number(self):
        try:
            el = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(self.CURRENT_PAGE))
            return (el.text or "").strip()
        except Exception:
            return ""
 
    def click_next_page(self):
        try:
            btn = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(self.NEXT_PAGE))
            self.driver.execute_script("arguments[0].click();", btn)
            self._wait_settled(timeout=10)
            return True
        except Exception:
            return False
 
    def click_first_row_detail(self):
        self._wait_settled(timeout=10)
        locators = [
            (
                By.XPATH,
                '(//div[contains(@class,"el-table__body-wrapper")]//tbody/tr)[1]//td[last()]//*[normalize-space(.)="详情"]',
            ),
            (
                By.XPATH,
                '(//div[contains(@class,"el-table__body-wrapper")]//tbody/tr)[1]//td[last()]//button[1]',
            ),
        ]
        btn = None
        for loc in locators:
            try:
                cand = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(loc))
                if cand.is_displayed():
                    btn = cand
                    break
            except Exception:
                continue
        if not btn:
            raise TimeoutException("未找到第一行详情按钮")
        self.driver.execute_script("arguments[0].click();", btn)
        self.wait_vue_stable()
 
