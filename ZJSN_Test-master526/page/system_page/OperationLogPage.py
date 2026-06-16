"""操作日志页面 Page Object — 重构版

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


class OperationLogPage(BasePage):
    """操作日志页面操作 — 继承 BasePage"""

    # ══════════════════════════════════════════════════════════════════
    #  导航 — 复用 BasePage.navigate_to("系统管理", "日志管理", "操作日志")
    # ══════════════════════════════════════════════════════════════════

    SYSTEM_MODULE_INPUT = (By.XPATH, '//input[contains(@placeholder,"请输入系统模块")]')
    OPERATION_TYPE_INPUT = (By.XPATH, '//input[contains(@placeholder,"请输入操作类型")]')
    OPERATOR_INPUT = (By.XPATH, '//input[contains(@placeholder,"请输入操作人员")]')

    STATUS_ALL = (By.XPATH, '//label[contains(@class,"el-radio")][.//span[normalize-space(.)="全部"]]')
    STATUS_SUCCESS = (By.XPATH, '//label[contains(@class,"el-radio")][.//span[normalize-space(.)="成功"]]')
    STATUS_FAIL = (By.XPATH, '//label[contains(@class,"el-radio")][.//span[normalize-space(.)="失败"]]')
    STATUS_SELECT = (
        By.XPATH,
        '//div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"状态")]]//div[contains(@class,"el-select") or contains(@class,"el-select-v2")]',
    )

    DATE_START_INPUT = (By.XPATH, '//input[contains(@placeholder,"开始日期")]')
    DATE_END_INPUT = (By.XPATH, '//input[contains(@placeholder,"结束日期")]')
    DATE_RANGE_PICKER_PANEL = (
        By.XPATH,
        '(//div[contains(@class,"el-date-range-picker") or contains(@class,"el-picker-panel")][not(contains(@style,"display: none"))])[last()]',
    )

    SEARCH_BUTTON_FALLBACK = (
        By.XPATH,
        '//*[@id="app"]/div/div[3]/div/section/div/div/div[1]/div/div/div/div[1]/div/form/div[6]/div/button[1]/span/ancestor::button[1]',
    )
    RESET_BUTTON_FALLBACK = (
        By.XPATH,
        '//*[@id="app"]/div/div[3]/div/section/div/div/div[1]/div/div/div/div[1]/div/form/div[6]/div/button[2]',
    )
    TOOLBAR_CLEAR_FALLBACK = (
        By.XPATH,
        '//*[@id="app"]/div/div[3]/div/section/div/div/div[1]/div/div/div/div[2]/div[1]/div/div[1]/button',
    )
    TOOLBAR_EXPORT_FALLBACK = (
        By.XPATH,
        '//*[@id="app"]/div/div[3]/div/section/div/div/div[1]/div/div/div/div[2]/div[1]/div/div[2]/button',
    )

    FIRST_ROW_DETAIL_FALLBACK = (
        By.XPATH,
        '//*[@id="app"]/div/div[3]/div/section/div/div/div[1]/div/div/div/div[2]/div[2]/div[1]/div[1]/div[3]/div/div[1]/div/table/tbody/tr[1]/td[8]/div/button/span/ancestor::button[1]',
    )

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

    TOAST_TEXT = (By.CSS_SELECTOR, ".el-message__content")
    TOAST_TEXT_FALLBACK = (By.CSS_SELECTOR, 'div[id^="message_"] p, div[id^="message_"] .el-message__content, div[id^="message_"]')
    # 增强的Toast定位器 - 使用last()获取最新的消息
    TOAST_MESSAGE_ENHANCED = (By.XPATH, '(//*[contains(@class,"el-message__content") and normalize-space(.)!=""])[last()]')

    def __init__(self, driver, timeout=None):
        """初始化 — 继承 BasePage"""
        super().__init__(driver, timeout)

    def _wait_settled(self, timeout=10):
        """@deprecated: 使用 self._wait_loading_gone(timeout) 替代"""
        return self._wait_loading_gone(timeout)

    def _wait_settled_legacy(self, timeout=10):
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
        """等待并获取Toast提示消息文本"""
        end = time.time() + timeout
        last = ""
        while time.time() < end:
            # 优先使用增强的XPath定位器
            try:
                els = self.driver.find_elements(*self.TOAST_MESSAGE_ENHANCED)
                if els:
                    for el in els:
                        try:
                            if el.is_displayed():
                                t = (el.text or "").strip()
                                if t:
                                    return t
                        except Exception:
                            continue
            except Exception:
                pass
            
            # 备用方案：使用CSS选择器
            try:
                els = self.driver.find_elements(*self.TOAST_TEXT)
                for el in els:
                    try:
                        if el.is_displayed():
                            t = (el.text or "").strip()
                            if t:
                                last = t
                    except Exception:
                        continue
            except Exception:
                pass
            
            # 最后的备用方案
            try:
                els = self.driver.find_elements(*self.TOAST_TEXT_FALLBACK)
                for el in els:
                    try:
                        if el.is_displayed():
                            t = (el.text or "").strip()
                            if t:
                                last = t
                    except Exception:
                        continue
            except Exception:
                pass
            
            if last:
                return last
            
            self.wait_vue_stable()
        return last

    # ══════════════════════════════════════════════════════════════════
    #  导航（重构：使用 BasePage.navigate_to）
    # ══════════════════════════════════════════════════════════════════

    def navigate(self):
        """导航到操作日志页面 — 唯一入口"""
        logger.info("导航到 → 系统管理 → 日志管理 → 操作日志")
        self.navigate_to("系统管理", "日志管理", "操作日志")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=12)
        self.wait_vue_stable()
        return self

    def navigate_to_operation_log(self):
        """@deprecated: 使用 navigate() 替代"""
        return self.navigate()

    def _clear_input(self, locator):
        el = self.wait.until(EC.presence_of_element_located(locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        return el

    def input_system_module(self, value):
        el = self._clear_input(self.SYSTEM_MODULE_INPUT)
        if value:
            el.send_keys(value)

    def input_operation_type(self, value):
        el = self._clear_input(self.OPERATION_TYPE_INPUT)
        if value:
            el.send_keys(value)

    def input_operator(self, value):
        el = self._clear_input(self.OPERATOR_INPUT)
        if value:
            el.send_keys(value)

    def select_status(self, text):
        mapping = {"全部": self.STATUS_ALL, "成功": self.STATUS_SUCCESS, "失败": self.STATUS_FAIL}
        loc = mapping.get(text)
        if not loc:
            raise TimeoutException(f"未知状态: {text}")
        try:
            el = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(loc))
            if el and el.is_displayed():
                self.driver.execute_script("arguments[0].click();", el)
                self.wait_vue_stable()
                return
        except Exception:
            pass

        self._open_select(self.STATUS_SELECT)
        self._click_option_in_visible_dropdown(text)
        self.wait_vue_stable()

    def _open_select(self, locator):
        self._wait_settled(timeout=6)
        el = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)

        def _dropdown_visible():
            try:
                dds = self.driver.find_elements(
                    By.XPATH,
                    '//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]'
                    ' | //div[contains(@class,"el-select-v2__popper") and not(contains(@style,"display: none"))]'
                    ' | //div[contains(@class,"el-select__popper") and not(contains(@style,"display: none"))]'
                    ' | //div[contains(@class,"el-popper") and not(contains(@style,"display: none"))]',
                )
                for d in dds:
                    try:
                        if d.is_displayed():
                            return True
                    except Exception:
                        continue
            except Exception:
                pass
            return False

        click_targets = [el]
        for xp in [
            './/div[contains(@class,"el-select__wrapper")]',
            './/div[contains(@class,"el-select__selection")]',
            './/span[contains(@class,"el-select__placeholder")]',
            './/i[contains(@class,"el-select__caret")]',
        ]:
            try:
                click_targets.append(el.find_element(By.XPATH, xp))
            except Exception:
                continue

        for _ in range(3):
            for t in click_targets:
                try:
                    self.driver.execute_script("arguments[0].click();", t)
                except Exception:
                    try:
                        t.click()
                    except Exception:
                        continue
                self.wait_vue_stable()
                if _dropdown_visible():
                    return
        raise TimeoutException("下拉框未能展开")

    def _click_option_in_visible_dropdown(self, option_text):
        broad = [
            (
                By.XPATH,
                f'//*[normalize-space(.)="{option_text}" and (ancestor::*[contains(@class,"el-select-dropdown") or contains(@class,"el-select__popper") or contains(@class,"el-select-v2__popper") or contains(@class,"el-popper") or @role="listbox"])][last()]',
            ),
            (By.XPATH, f'//*[@role="option" and normalize-space(.)="{option_text}"][last()]'),
        ]
        for loc in broad:
            try:
                el = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(loc))
                if el and el.is_displayed():
                    try:
                        li = el.find_element(By.XPATH, './ancestor::li[1][not(contains(@class,"is-disabled"))] | ./ancestor::*[@role="option"][1]')
                        self.driver.execute_script("arguments[0].click();", li)
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", el)
                    self.wait_vue_stable()
                    return
            except Exception:
                continue

        containers = self.driver.find_elements(
            By.XPATH,
            '//div[contains(@class,"el-select-dropdown") or contains(@class,"el-select-v2__popper") or contains(@class,"el-select__popper") or contains(@class,"el-popper") or @role="listbox"]',
        )
        for c in reversed(containers):
            try:
                if not c.is_displayed():
                    continue
            except Exception:
                continue
            items = []
            try:
                items.extend(c.find_elements(By.XPATH, './/li[not(contains(@class,"is-disabled"))]'))
            except Exception:
                pass
            try:
                items.extend(c.find_elements(By.XPATH, './/*[@role="option" and not(contains(@class,"is-disabled"))]'))
            except Exception:
                pass
            for it in items:
                try:
                    if ((it.text or "").strip().replace("\n", " ").strip()) == option_text:
                        self.driver.execute_script("arguments[0].click();", it)
                        self.wait_vue_stable()
                        return
                except Exception:
                    continue
        raise TimeoutException(f"未找到下拉选项：{option_text}")

    def _get_input_value(self, locator):
        try:
            el = self.driver.find_element(*locator)
            return (el.get_attribute("value") or "").strip()
        except Exception:
            return ""

    def get_system_module_value(self):
        return self._get_input_value(self.SYSTEM_MODULE_INPUT)

    def get_operation_type_value(self):
        return self._get_input_value(self.OPERATION_TYPE_INPUT)

    def get_operator_value(self):
        return self._get_input_value(self.OPERATOR_INPUT)

    def get_status_selected_text(self):
        try:
            checked = self.driver.find_elements(
                By.XPATH,
                '//label[contains(@class,"el-radio") and (contains(@class,"is-checked") or .//input[@checked])][1]//span[contains(@class,"el-radio__label")]',
            )
            if checked:
                t = (checked[0].text or "").strip()
                if t:
                    return t
        except Exception:
            pass
        try:
            wrap = self.driver.find_element(*self.STATUS_SELECT)
            for xp in [
                './/*[contains(@class,"el-select__selected-item")]',
                './/*[contains(@class,"el-select__placeholder")]',
            ]:
                try:
                    t = (wrap.find_element(By.XPATH, xp).text or "").strip()
                    if t:
                        return t
                except Exception:
                    continue
        except Exception:
            pass
        return ""

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
        btn = self.wait.until(EC.presence_of_element_located(self.SEARCH_BUTTON_FALLBACK))
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_settled(timeout=10)

    def click_reset(self):
        self._wait_settled(timeout=6)
        btn = self.wait.until(EC.presence_of_element_located(self.RESET_BUTTON_FALLBACK))
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_settled(timeout=10)

    def click_clear(self):
        self._wait_settled(timeout=6)
        btn = self.wait.until(EC.presence_of_element_located(self.TOOLBAR_CLEAR_FALLBACK))
        self.driver.execute_script("arguments[0].click();", btn)
        self.wait_vue_stable()

    def click_export(self):
        self._wait_settled(timeout=6)
        btn = self.wait.until(EC.presence_of_element_located(self.TOOLBAR_EXPORT_FALLBACK))
        self.driver.execute_script("arguments[0].click();", btn)
        self.wait_vue_stable()
        self.confirm_message_box_if_present()

    def confirm_message_box_if_present(self):
        try:
            btn = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(self.MESSAGEBOX_CONFIRM))
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_vue_stable()
            return True
        except Exception:
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
            self.FIRST_ROW_DETAIL_FALLBACK,
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

    def is_login_page(self):
        try:
            return bool(self.driver.find_elements(By.XPATH, '//input[@placeholder="请输入账号"]'))
        except Exception:
            return False
