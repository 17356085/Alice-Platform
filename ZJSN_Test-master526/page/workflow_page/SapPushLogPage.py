"""SAP推送日志页面 Page Object

变更记录:
  2026-06-12: 新建，继承 BasePage，遵循代码红线规范
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


class SapPushLogPage(BasePage):
    """SAP推送日志页面操作 — 继承 BasePage"""

    # ══════════════════════════════════════════════════════════════════
    #  搜索区域定位器
    # ══════════════════════════════════════════════════════════════════
    REQUEST_ID_INPUT = (By.XPATH, '//input[contains(@placeholder,"请求") or contains(@placeholder,"ID") or contains(@placeholder,"编号")]')
    STATUS_SELECT = (
        By.XPATH,
        '//div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"状态") or contains(normalize-space(.),"推送状态")]]'
        '//div[contains(@class,"el-select")]',
    )
    DATE_START_INPUT = (By.XPATH, '(//input[contains(@placeholder,"开始日期") or contains(@placeholder,"开始时间")])[1]')
    DATE_END_INPUT = (By.XPATH, '(//input[contains(@placeholder,"结束日期") or contains(@placeholder,"结束时间")])[1]')
    SEARCH_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="搜索"] or normalize-space(.)="搜索"]')
    RESET_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="重置"] or normalize-space(.)="重置"]')

    # ══════════════════════════════════════════════════════════════════
    #  表格定位器
    # ══════════════════════════════════════════════════════════════════
    EMPTY_TEXT = (By.CSS_SELECTOR, ".el-table__empty-text")
    TABLE_HEADERS = (By.XPATH, '//div[contains(@class,"el-table__header-wrapper")]//th//div')
    CURRENT_PAGE = (By.CSS_SELECTOR, ".el-pagination .el-pager li.active, .el-pagination .el-pager li.is-active")

    # ══════════════════════════════════════════════════════════════════
    #  详情弹窗
    # ══════════════════════════════════════════════════════════════════
    DETAIL_DIALOG = (
        By.XPATH,
        '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]'
        '//div[contains(@class,"el-dialog")])[last()]',
    )
    DETAIL_CLOSE_BTN = (By.XPATH, '//button[contains(@class,"el-dialog__headerbtn")]')

    # ══════════════════════════════════════════════════════════════════
    #  Toast
    # ══════════════════════════════════════════════════════════════════
    TOAST_TEXT = (By.CSS_SELECTOR, ".el-message__content")
    TOAST_FALLBACK = (By.CSS_SELECTOR, 'div[id^="message_"] p, div[id^="message_"] .el-message__content')
    TOAST_ENHANCED = (By.XPATH, '(//*[contains(@class,"el-message__content") and normalize-space(.)!=""])[last()]')

    PAGE_ROUTE = "#/system/workflow/sap-push-log"

    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    # ══════════════════════════════════════════════════════════════════════
    #  导航
    # ══════════════════════════════════════════════════════════════════════

    def navigate(self):
        """导航到SAP推送日志页面"""
        logger.info("导航到 → 系统管理 → 工作流管理 → SAP推送日志")
        self.navigate_to("系统管理", "工作流管理", "SAP推送日志")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        return self

    def _wait_settled(self, timeout=10):
        self._wait_loading_gone(timeout=timeout)

    # ══════════════════════════════════════════════════════════════════════
    #  搜索操作
    # ══════════════════════════════════════════════════════════════════════

    def input_request_id(self, value):
        el = self.wait.until(EC.presence_of_element_located(self.REQUEST_ID_INPUT))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        if value:
            el.send_keys(value)
        logger.info("已输入请求ID: %s", value)

    def select_status(self, status_text):
        self._wait_settled(timeout=6)
        el = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(self.STATUS_SELECT))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        for _ in range(3):
            try:
                self.driver.execute_script("arguments[0].click();", el)
            except Exception:
                pass
            self.wait_vue_stable()
            try:
                dropdowns = self.driver.find_elements(
                    By.XPATH,
                    '//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]'
                    ' | //div[contains(@class,"el-popper") and not(contains(@style,"display: none"))]',
                )
                if dropdowns:
                    break
            except Exception:
                continue
        option_xpath = (
            f'//*[normalize-space(.)="{status_text}" and (ancestor::*[contains(@class,"el-select-dropdown")]'
            f' or ancestor::*[@role="listbox"] or @role="option")][last()]'
        )
        opt = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.XPATH, option_xpath)))
        self.driver.execute_script("arguments[0].click();", opt)
        self.wait_vue_stable()
        logger.info("已选择推送状态: %s", status_text)

    def set_date_range(self, start_date, end_date):
        """设置日期范围。支持三种模式：
        1. 独立开始/结束 input (placeholder含'开始日期'/'结束日期')
        2. el-date-picker daterange 组件
        3. 无日期字段时静默跳过
        """
        # Strategy 1: independent start/end inputs
        for loc in [self.DATE_START_INPUT, (By.CSS_SELECTOR, 'input[placeholder*="开始"]')]:
            try:
                start = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(loc))
                if start and start.is_displayed():
                    # Found start input, look for end
                    for eloc in [self.DATE_END_INPUT, (By.CSS_SELECTOR, 'input[placeholder*="结束"]')]:
                        try:
                            end = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(eloc))
                            if end and end.is_displayed():
                                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", start)
                                self.driver.execute_script(
                                    "arguments[0].value = arguments[1];"
                                    "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
                                    "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
                                    start, start_date)
                                self.driver.execute_script(
                                    "arguments[0].value = arguments[1];"
                                    "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
                                    "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
                                    end, end_date)
                                self.wait_vue_stable()
                                logger.info("已设置日期范围(input): %s ~ %s", start_date, end_date)
                                return
                        except Exception:
                            continue
            except Exception:
                continue

        # Strategy 2: el-date-picker daterange component
        try:
            picker = self.driver.execute_script("""
                var pickers = document.querySelectorAll('.el-date-editor, .el-date-picker, [class*=\"date-range\"], [class*=\"daterange\"]');
                for (var i=0; i<pickers.length; i++) {
                    if (pickers[i].offsetParent !== null) return pickers[i];
                }
                // Search by label '时间范围'
                var labels = document.querySelectorAll('.el-form-item__label');
                for (var j=0; j<labels.length; j++) {
                    if ((labels[j].textContent||'').indexOf('时间')!==-1 || (labels[j].textContent||'').indexOf('日期')!==-1) {
                        var item = labels[j].closest('.el-form-item');
                        if (item) {
                            var editor = item.querySelector('.el-date-editor');
                            if (editor) return editor;
                            var input = item.querySelector('input');
                            if (input) return input;
                        }
                    }
                }
                return null;
            """)
            if picker:
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", picker)
                # Try JS-based date setting via __vue__ component
                set_ok = self.driver.execute_script("""
                    var el = arguments[0];
                    var start = arguments[1];
                    var end = arguments[2];
                    // Try Vue component data
                    if (el.__vue__ && el.__vue__.value !== undefined) {
                        el.__vue__.value = [start, end];
                        return 'vue_set';
                    }
                    // Try setting via input
                    var inputs = el.querySelectorAll('input');
                    if (inputs.length >= 2) {
                        inputs[0].value = start;
                        inputs[0].dispatchEvent(new Event('input', {bubbles:true}));
                        inputs[0].dispatchEvent(new Event('change', {bubbles:true}));
                        inputs[1].value = end;
                        inputs[1].dispatchEvent(new Event('input', {bubbles:true}));
                        inputs[1].dispatchEvent(new Event('change', {bubbles:true}));
                        return 'input_set';
                    }
                    return 'no_set';
                """, picker, start_date, end_date)
                self.wait_vue_stable()
                logger.info("已设置日期范围(picker): %s ~ %s (method=%s)", start_date, end_date, set_ok)
                return
        except Exception as e:
            logger.debug("el-date-picker date set attempt: %s", e)

        # Strategy 3: no date field found — skip gracefully
        logger.warning("未找到日期输入组件，跳过日期设置")
        raise TimeoutException("未找到日期输入组件 (已尝试 input + el-date-picker)")

    def click_search(self):
        self._wait_settled(timeout=6)
        self._js_click_search_or_reset("搜索")
        self._wait_settled(timeout=10)
        logger.info("已点击搜索按钮")

    def click_reset(self):
        self._wait_settled(timeout=6)
        self._js_click_search_or_reset("重置")
        self._wait_settled(timeout=10)
        logger.info("已点击重置按钮")

    def _js_click_search_or_reset(self, text):
        """JS 点击搜索/重置按钮（绕过 element click intercepted）"""
        self.driver.execute_script(f"""
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {{
                if ((btns[i].textContent || '').trim().indexOf('{text}') !== -1) {{
                    btns[i].scrollIntoView({{block:'center'}});
                    btns[i].click();
                    return;
                }}
            }}
            // Fallback: click primary button for search
            if ('{text}' === '搜索') {{
                var primary = document.querySelector('.search-form button.el-button--primary, .search-row button.el-button--primary');
                if (primary) {{ primary.scrollIntoView({{block:'center'}}); primary.click(); }}
            }}
        """)

    # ══════════════════════════════════════════════════════════════════════
    #  表格操作
    # ══════════════════════════════════════════════════════════════════════

    def get_table_headers(self):
        for _ in range(6):
            try:
                self._wait_settled(timeout=5)
            except Exception:
                pass
            self.wait_vue_stable()
            headers = self.driver.execute_script("""
                return Array.from(
                    document.querySelectorAll('.el-table__header-wrapper th .cell')
                ).map(function(el) { return el.textContent.trim(); }).filter(Boolean);
            """)
            if headers and len(headers) >= 2:
                return headers
            self._wait_loading_gone(timeout=2)
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
                if (th.text or "").strip() == header_text:
                    return idx
            except Exception:
                continue
        return None

    def get_column_data(self, col_index):
        self._wait_settled(timeout=10)
        xpath = f'//div[contains(@class,"el-table__body-wrapper")]//tbody/tr/td[{col_index}]//div[contains(@class,"cell")]'
        cells = self.driver.find_elements(By.XPATH, xpath)
        return [(c.text or "").strip().replace("\n", " ").strip() for c in cells if (c.text or "").strip()]

    def get_column_data_by_header(self, header_text):
        idx = self.get_column_index_by_header(header_text)
        return self.get_column_data(idx) if idx else []

    def get_empty_text(self):
        try:
            self._wait_settled(timeout=10)
        except Exception:
            pass
        try:
            return (self.driver.find_element(*self.EMPTY_TEXT).text or "").strip()
        except Exception:
            return ""

    def get_current_page_number(self):
        try:
            return (WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(self.CURRENT_PAGE)
            ).text or "").strip()
        except Exception:
            return ""

    def click_next_page(self):
        try:
            super().click_next_page()
            self._wait_settled(timeout=10)
            return True
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════════
    #  详情弹窗
    # ══════════════════════════════════════════════════════════════════════

    def click_first_row_detail(self):
        self._wait_settled(timeout=10)
        locators = [
            (By.XPATH, '(//div[contains(@class,"el-table__body-wrapper")]//tbody/tr)[1]//td[last()]//button[.//*[normalize-space(.)="详情"]]'),
            (By.XPATH, '(//div[contains(@class,"el-table__body-wrapper")]//tbody/tr)[1]//td[last()]//button[1]'),
        ]
        for loc in locators:
            try:
                btn = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(loc))
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_vue_stable()
                    logger.info("已点击第一行详情按钮")
                    return
            except Exception:
                continue
        raise TimeoutException("未找到第一行详情按钮")

    def wait_detail_dialog_visible(self, timeout=8):
        try:
            WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(self.DETAIL_DIALOG))
            return True
        except TimeoutException:
            return False

    def close_detail_dialog(self):
        try:
            btn = self.driver.find_element(*self.DETAIL_CLOSE_BTN)
            if btn.is_displayed():
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_vue_stable()
                return True
        except Exception:
            pass
        try:
            btn = self.driver.find_element(
                By.XPATH,
                '(//div[contains(@class,"el-dialog")])[last()]//button[.//span[normalize-space(.)="关闭"] or normalize-space(.)="关闭"]',
            )
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_vue_stable()
            return True
        except Exception:
            pass
        return False

    # ══════════════════════════════════════════════════════════════════════
    #  Toast
    # ══════════════════════════════════════════════════════════════════════

    def wait_for_toast_text(self, timeout=6):
        import time as _time
        deadline = _time.time() + timeout
        last = ""
        while _time.time() < deadline:
            for loc in [self.TOAST_ENHANCED, self.TOAST_TEXT, self.TOAST_FALLBACK]:
                try:
                    els = self.driver.find_elements(*loc)
                    for el in els:
                        try:
                            if el.is_displayed():
                                t = (el.text or el.get_attribute("textContent") or "").strip()
                                if t:
                                    return t
                        except Exception:
                            continue
                except Exception:
                    continue
            if last:
                return last
            _time.sleep(0.3)
        return last
