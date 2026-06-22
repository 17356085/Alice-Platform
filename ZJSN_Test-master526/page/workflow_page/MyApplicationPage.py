"""我发起的页面 Page Object

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


class MyApplicationPage(BasePage):
    """我发起的页面操作 — 继承 BasePage"""

    # ══════════════════════════════════════════════════════════════════
    #  搜索区域定位器
    # ══════════════════════════════════════════════════════════════════
    TITLE_INPUT = (By.XPATH, '//div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"标题")]]//input[contains(@class,"el-input")] | //input[contains(@placeholder,"请输入标题")]')
    # 页面实际字段：工厂代码（非标题）
    FACTORY_INPUT = (By.XPATH, '//div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"工厂")]]//input[contains(@class,"el-input")] | //input[contains(@placeholder,"工厂")]')
    STATUS_SELECT = (
        By.XPATH,
        '//div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"状态") or contains(normalize-space(.),"审批状态")]]'
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
    #  详情弹窗定位器
    # ══════════════════════════════════════════════════════════════════
    DETAIL_DIALOG = (
        By.XPATH,
        '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]'
        '//div[contains(@class,"el-dialog")])[last()]',
    )
    DETAIL_CLOSE_BTN = (By.XPATH, '//button[contains(@class,"el-dialog__headerbtn")]')

    # ══════════════════════════════════════════════════════════════════
    #  撤回按钮
    # ══════════════════════════════════════════════════════════════════
    WITHDRAW_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="撤回"] or normalize-space(.)="撤回"]')

    # ══════════════════════════════════════════════════════════════════
    #  Toast 定位器
    # ══════════════════════════════════════════════════════════════════
    TOAST_TEXT = (By.CSS_SELECTOR, ".el-message__content")
    TOAST_FALLBACK = (By.CSS_SELECTOR, 'div[id^="message_"] p, div[id^="message_"] .el-message__content')
    TOAST_ENHANCED = (By.XPATH, '(//*[contains(@class,"el-message__content") and normalize-space(.)!=""])[last()]')

    PAGE_ROUTE = "#/system/workflow/my-applications"

    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    # ══════════════════════════════════════════════════════════════════════
    #  导航
    # ══════════════════════════════════════════════════════════════════════

    def navigate(self):
        """导航到我发起的页面"""
        logger.info("导航到 → 系统管理 → 工作流管理 → 我发起的")
        self.navigate_to("系统管理", "工作流管理", "我发起的")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        return self

    def _wait_settled(self, timeout=10):
        self._wait_loading_gone(timeout=timeout)

    # ══════════════════════════════════════════════════════════════════════
    #  搜索操作
    # ══════════════════════════════════════════════════════════════════════

    def input_title(self, value):
        """输入关键词 — 委托给 input_factory（此页面搜索字段实际为'工厂代码'）"""
        logger.warning("'我发起的'页面无'标题'搜索字段，委托给 input_factory")
        self.input_factory(value)

    def input_factory(self, value):
        """输入工厂代码搜索 — JS 遍历标签定位 → XPath 降级"""
        el = self.driver.execute_script("""
            var labels = document.querySelectorAll('.el-form-item__label');
            for (var i = 0; i < labels.length; i++) {
                var text = (labels[i].textContent || '').trim();
                if (text.indexOf('工厂') !== -1) {
                    var formItem = labels[i].closest('.el-form-item');
                    if (!formItem) continue;
                    var input = formItem.querySelector('input.el-input__inner');
                    if (!input) input = formItem.querySelector('input:not([type="hidden"]):not([readonly])');
                    if (input) return input;
                }
            }
            var inputs = document.querySelectorAll('input[placeholder]');
            for (var j = 0; j < inputs.length; j++) {
                var ph = inputs[j].getAttribute('placeholder') || '';
                if (ph.indexOf('工厂') !== -1)
                    return inputs[j];
            }
            return null;
        """)
        if el:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.send_keys(Keys.CONTROL + "a")
            el.send_keys(Keys.DELETE)
            if value:
                el.send_keys(value)
            logger.info("已输入工厂代码: %s", value)
            return
        # XPath 降级
        for loc in [
            self.FACTORY_INPUT,
            (By.XPATH, '//div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"工厂")]]//input[not(@readonly) and not(@type="hidden")]'),
            (By.XPATH, '//input[contains(@placeholder,"工厂")]'),
        ]:
            try:
                el = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(loc))
                if el.is_displayed():
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                    el.send_keys(Keys.CONTROL + "a")
                    el.send_keys(Keys.DELETE)
                    if value:
                        el.send_keys(value)
                    logger.info("已输入工厂代码(XPath): %s", value)
                    return
            except Exception:
                continue
        raise TimeoutException(f"未找到工厂代码输入框: {value}")

    def _select_by_label(self, label_text, option_keyword=None):
        """根据表单项标签定位 el-select 并选择选项"""
        form_item = (By.XPATH, f'//div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"{label_text}")]]')
        el = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(form_item))
        # 找到其中的 el-select 包装器并点击展开（重试3次）
        select_wrapper = el.find_element(By.XPATH, './/div[contains(@class,"el-select__wrapper")]')
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", select_wrapper)
        for _ in range(3):
            try:
                self.driver.execute_script("arguments[0].click();", select_wrapper)
            except Exception:
                pass
            self.wait_vue_stable()
            dropdowns = self.driver.find_elements(
                By.XPATH,
                '//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]'
                ' | //div[contains(@class,"el-popper") and not(contains(@style,"display: none"))]',
            )
            if dropdowns:
                break
        # 选择匹配选项（或第一个非禁用选项）
        options_xpath = '//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]//li[not(contains(@class,"is-disabled"))]'
        options = WebDriverWait(self.driver, 3).until(EC.presence_of_all_elements_located((By.XPATH, options_xpath)))
        if option_keyword:
            for opt in options:
                if option_keyword in (opt.text or ""):
                    self.driver.execute_script("arguments[0].click();", opt)
                    self.wait_vue_stable()
                    logger.info("已选择下拉选项(匹配'%s'): %s", option_keyword, opt.text)
                    return
        if options:
            self.driver.execute_script("arguments[0].click();", options[0])
            self.wait_vue_stable()
            logger.info("已选择第一个下拉选项: %s", options[0].text)

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
        logger.info("已选择状态: %s", status_text)

    def set_date_range(self, start_date, end_date):
        start = self.wait.until(EC.presence_of_element_located(self.DATE_START_INPUT))
        end = self.wait.until(EC.presence_of_element_located(self.DATE_END_INPUT))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", start)
        self.driver.execute_script(
            "arguments[0].value = arguments[1];"
            "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
            "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
            start, start_date,
        )
        self.driver.execute_script(
            "arguments[0].value = arguments[1];"
            "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
            "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
            end, end_date,
        )
        self.wait_vue_stable()
        logger.info("已设置日期范围: %s ~ %s", start_date, end_date)

    def click_search(self):
        self._wait_settled(timeout=6)
        self.click_search_button()
        self._wait_settled(timeout=10)
        logger.info("已点击搜索按钮")

    def click_reset(self):
        self._wait_settled(timeout=6)
        self.click_reset_button()
        self._wait_settled(timeout=10)
        logger.info("已点击重置按钮")

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
    #  撤回操作
    # ══════════════════════════════════════════════════════════════════════

    def click_first_row_withdraw(self):
        """点击第一行的撤回按钮"""
        self._wait_settled(timeout=10)
        locators = [
            (By.XPATH, '(//div[contains(@class,"el-table__body-wrapper")]//tbody/tr)[1]//td[last()]//button[.//*[normalize-space(.)="撤回"]]'),
            (By.XPATH, '(//div[contains(@class,"el-table__body-wrapper")]//tbody/tr)[1]//td[last()]//*[normalize-space(.)="撤回"]'),
        ]
        for loc in locators:
            try:
                btn = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(loc))
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_vue_stable()
                    logger.info("已点击第一行撤回按钮")
                    return
            except Exception:
                continue
        raise TimeoutException("未找到第一行撤回按钮")

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
