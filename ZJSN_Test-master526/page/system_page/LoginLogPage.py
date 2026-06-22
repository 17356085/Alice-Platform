"""登录日志页面 Page Object — 重构版

变更记录:
  2026-06-11: 继承 BasePage，去绝对XPath，去time.sleep→BasePage等待方法，print→logger
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


class LoginLogPage(BasePage):
    """登录日志页面操作 — 继承 BasePage"""

    # ══════════════════════════════════════════════════════════════════
    #  页面专属定位器（CSS优先 → 相对XPath → 文本匹配）
    # ══════════════════════════════════════════════════════════════════

    USERNAME_INPUT = (By.XPATH, '//input[contains(@placeholder,"请输入用户名")]')
    STATUS_ALL = (By.XPATH, '//label[contains(@class,"el-radio")][.//span[normalize-space(.)="全部"]]')
    STATUS_SUCCESS = (By.XPATH, '//label[contains(@class,"el-radio")][.//span[normalize-space(.)="成功"]]')
    STATUS_FAIL = (By.XPATH, '//label[contains(@class,"el-radio")][.//span[normalize-space(.)="失败"]]')
    STATUS_SELECT = (
        By.XPATH,
        '//div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"登录状态") or contains(normalize-space(.),"状态")]]//div[contains(@class,"el-select") or contains(@class,"el-select-v2")]',
    )

    DATE_START_INPUT = (
        By.XPATH,
        '(//input[contains(@placeholder,"开始日期") or contains(@placeholder,"开始时间")]'
        ' | //div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"登录时间") or contains(normalize-space(.),"时间")]]//input[contains(@placeholder,"开始")])[1]',
    )
    DATE_END_INPUT = (
        By.XPATH,
        '(//input[contains(@placeholder,"结束日期") or contains(@placeholder,"结束时间")]'
        ' | //div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"登录时间") or contains(normalize-space(.),"时间")]]//input[contains(@placeholder,"结束")])[1]',
    )
    DATE_RANGE_PICKER_PANEL = (
        By.XPATH,
        '(//div[contains(@class,"el-date-range-picker") or contains(@class,"el-picker-panel")][not(contains(@style,"display: none"))])[last()]',
    )

    SEARCH_BUTTON_FALLBACK = (By.XPATH, '//button[.//span[normalize-space(.)="搜索"] or normalize-space(.)="搜索"]')
    RESET_BUTTON_FALLBACK = (By.XPATH, '//button[.//span[normalize-space(.)="重置"] or normalize-space(.)="重置"]')
    TOOLBAR_CLEAR_FALLBACK = (By.XPATH, '//button[.//span[normalize-space(.)="清空"] or normalize-space(.)="清空"]')
    TOOLBAR_EXPORT_FALLBACK = (By.XPATH, '//button[.//span[normalize-space(.)="导出"] or normalize-space(.)="导出"]')

    # 复用 BasePage.LOADING_MASK / BasePage.TABLE_ROWS / BasePage.TOTAL_COUNT / BasePage.NEXT_PAGE
    EMPTY_TEXT = (By.CSS_SELECTOR, ".el-table__empty-text")
    TABLE_HEADERS = (By.XPATH, '//div[contains(@class,"el-table__header-wrapper")]//th//div')

    CURRENT_PAGE = (By.CSS_SELECTOR, ".el-pagination .el-pager li.active, .el-pagination .el-pager li.is-active")

    MESSAGEBOX_CONFIRM = (
        By.XPATH,
        '(//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))])[last()]//button[.//*[normalize-space(.)="确定"] or normalize-space(.)="确定"]',
    )
    MESSAGEBOX_CONFIRM_FALLBACKS = [
        (By.XPATH, '(//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))])[last()]//button[2]'),
    ]

    # 复用 BasePage 的 TOAST 定位器
    TOAST_TEXT = (By.CSS_SELECTOR, ".el-message__content")
    TOAST_TEXT_FALLBACK = (By.CSS_SELECTOR, 'div[id^="message_"] p, div[id^="message_"] .el-message__content, div[id^="message_"]')
    TOAST_MESSAGE_ENHANCED = (By.XPATH, '(//*[contains(@class,"el-message__content") and normalize-space(.)!=""])[last()]')

    DETAIL_DIALOG_TITLE = (By.XPATH, '//*[contains(@class,"el-dialog__title") and normalize-space(.)="登录日志详情"]')
    DETAIL_PAGE_TITLE = (By.XPATH, '//*[normalize-space(.)="登录日志详情"]')
    DETAIL_TITLE_STRICT = (
        By.XPATH,
        '(//div[contains(@class,"login-log-detail-dialog") and contains(@class,"el-dialog")]'
        '//span[(contains(@class,"el-dialog__title") or @role="heading") and normalize-space(.)="登录日志详情"])[last()]',
    )
    DETAIL_TITLE_FALLBACK = (
        By.XPATH,
        '(//div[(contains(@class,"el-overlay-dialog") or contains(@class,"el-overlay") or contains(@class,"el-dialog__wrapper")) and not(contains(@style,"display: none"))]'
        '//header//span[(contains(@class,"el-dialog__title") or @role="heading" or self::span) and normalize-space(.)="登录日志详情"])[last()]',
    )

    def __init__(self, driver, timeout=None):
        """初始化 — 继承 BasePage"""
        super().__init__(driver, timeout)

    def navigate(self):
        """导航到登录日志页面 — 唯一入口"""
        logger.info("导航到 → 系统管理 → 日志管理 → 登录日志")
        self.navigate_to("系统管理", "日志管理", "登录日志")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        return self

    def navigate_to_login_log(self):
        """兼容旧调用的导航方法（委托给 navigate）"""
        logger.info("navigate_to_login_log → 委托 navigate")
        self.navigate()

    def _wait_settled(self, timeout=10):
        """等待 loading 遮罩消失（委托给 BasePage._wait_loading_gone）"""
        self._wait_loading_gone(timeout=timeout)

    def _wait_page_ready(self, timeout=20):
        """等待页面就绪（URL 或页面元素特征检测）"""
        def _ready(_driver):
            try:
                if "#/system/log/login-log" in (_driver.current_url or ""):
                    body = _driver.find_element(By.TAG_NAME, "body").text
                    if "登录日志" in body:
                        return True
            except Exception:
                pass
            locators = [
                self.USERNAME_INPUT,
                self.TABLE_HEADERS,
                self.EMPTY_TEXT,
                self.SEARCH_BUTTON_FALLBACK,
            ]
            for locator in locators:
                try:
                    for el in _driver.find_elements(*locator):
                        try:
                            if el.is_displayed():
                                return True
                        except Exception:
                            continue
                except Exception:
                    continue
            return False

        self._wait_settled(timeout=timeout)
        WebDriverWait(self.driver, timeout, poll_frequency=0.3).until(_ready)

    def _save_debug_snapshot(self, prefix="login_log_debug"):
        """保存调试快照（委托给 BasePage.save_debug_snapshot）"""
        self.save_debug_snapshot(prefix)

    def _force_open_login_log_route(self):
        """强制通过 URL 直接跳转到登录日志页面"""
        current = self.driver.current_url
        base = current.split("#", 1)[0] if "#" in current else current.rstrip("/") + "/"
        target = base + "#/system/log/login-log"
        logger.info("直接访问登录日志路由: %s", target)
        try:
            self.driver.get(target)
        except TimeoutException:
            logger.warning("直接访问登录日志路由超时，继续等待前端渲染")
        try:
            self.driver.execute_script("window.dispatchEvent(new Event('resize'));")
        except Exception:
            pass
        self._wait_settled(timeout=10)

    def wait_for_toast_text(self, timeout=6):
        """等待并获取Toast提示消息文本"""
        deadline = __import__('time').time() + timeout
        last = ""
        while __import__('time').time() < deadline:
            # 优先使用增强的XPath定位器
            try:
                els = self.driver.find_elements(*self.TOAST_MESSAGE_ENHANCED)
                if els:
                    for el in els:
                        try:
                            if el.is_displayed():
                                t = (
                                    el.text
                                    or el.get_attribute("textContent")
                                    or el.get_attribute("innerText")
                                    or ""
                                ).strip()
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
                            t = (
                                el.text
                                or el.get_attribute("textContent")
                                or el.get_attribute("innerText")
                                or ""
                            ).strip()
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
                            t = (
                                el.text
                                or el.get_attribute("textContent")
                                or el.get_attribute("innerText")
                                or ""
                            ).strip()
                            if t:
                                last = t
                    except Exception:
                        continue
            except Exception:
                pass

            if last:
                return last

            __import__('time').sleep(0.3)
        return last

    def input_username(self, value):
        """输入用户名"""
        el = self.wait.until(EC.presence_of_element_located(self.USERNAME_INPUT))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        if value:
            el.send_keys(value)
        logger.info("已输入用户名: %s", value)

    def select_status(self, text):
        """选择登录状态（全部/成功/失败）"""
        mapping = {"全部": self.STATUS_ALL, "成功": self.STATUS_SUCCESS, "失败": self.STATUS_FAIL}
        loc = mapping.get(text)
        if not loc:
            raise TimeoutException(f"未知状态: {text}")
        try:
            el = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(loc))
            if el and el.is_displayed():
                self.driver.execute_script("arguments[0].click();", el)
                self.wait_vue_stable()
                logger.info("已选择状态（radio）: %s", text)
                return
        except Exception:
            pass

        self._open_select(self.STATUS_SELECT)
        self._click_option_in_visible_dropdown(text)
        self.wait_vue_stable()
        logger.info("已选择状态（dropdown）: %s", text)

    def _open_select(self, locator):
        """展开下拉框"""
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
        """在已展开的下拉框中选择指定选项"""
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

    def set_login_date_range(self, start_date, end_date):
        """设置登录日期范围"""
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

        _js_set(start, start_date)
        _js_set(end, end_date)
        try:
            _type_into(start, start_date)
            _type_into(end, end_date)
            end.send_keys(Keys.ENTER)
        except Exception:
            try:
                self.driver.execute_script("document.body.click();")
            except Exception:
                pass
        self.wait_vue_stable()
        self._try_click_date_range_days(start_date, end_date)
        logger.info("已设置日期范围: %s ~ %s", start_date, end_date)

    def _try_click_date_range_days(self, start_date, end_date):
        """尝试通过日期选择面板选中起止日期"""
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

    def get_login_date_range_values(self):
        """获取当前日期范围输入框的值"""
        try:
            start = self.driver.find_element(*self.DATE_START_INPUT)
            end = self.driver.find_element(*self.DATE_END_INPUT)
            return ((start.get_attribute("value") or "").strip(), (end.get_attribute("value") or "").strip())
        except Exception:
            return ("", "")

    def click_search(self):
        """点击搜索按钮"""
        self._wait_settled(timeout=6)
        btn = self.wait.until(EC.presence_of_element_located(self.SEARCH_BUTTON_FALLBACK))
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_settled(timeout=10)
        logger.info("已点击搜索按钮")

    def click_reset(self):
        """点击重置按钮"""
        self._wait_settled(timeout=6)
        btn = self.wait.until(EC.presence_of_element_located(self.RESET_BUTTON_FALLBACK))
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_settled(timeout=10)
        logger.info("已点击重置按钮")

    def click_clear(self):
        """点击清空按钮"""
        self._wait_settled(timeout=6)
        btn = self.wait.until(EC.presence_of_element_located(self.TOOLBAR_CLEAR_FALLBACK))
        self.driver.execute_script("arguments[0].click();", btn)
        self.wait_vue_stable()
        logger.info("已点击清空按钮")

    def click_export(self):
        """点击导出按钮"""
        self._wait_settled(timeout=6)
        btn = self.wait.until(EC.presence_of_element_located(self.TOOLBAR_EXPORT_FALLBACK))
        self.driver.execute_script("arguments[0].click();", btn)
        self.wait_vue_stable()
        self.confirm_message_box_if_present()
        logger.info("已点击导出按钮")

    def confirm_message_box_if_present(self):
        """确认 MessageBox（如果存在）"""
        try:
            btn = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(self.MESSAGEBOX_CONFIRM))
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_vue_stable()
            logger.info("已确认 MessageBox")
            return True
        except Exception:
            pass
        for loc in self.MESSAGEBOX_CONFIRM_FALLBACKS:
            try:
                btn = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located(loc))
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_vue_stable()
                    logger.info("已确认 MessageBox（fallback）")
                    return True
            except Exception:
                continue
        return False

    def get_empty_text(self):
        """获取空状态文本"""
        try:
            self._wait_page_ready(timeout=10)
        except Exception:
            self._wait_settled(timeout=8)
        try:
            el = self.driver.find_element(*self.EMPTY_TEXT)
            return (el.text or "").strip()
        except Exception:
            return ""

    def get_table_headers(self):
        """JS提取表格表头（含重试，应对Element Plus异步渲染）"""
        for attempt in range(6):
            try:
                self._wait_settled(timeout=5)
            except Exception:
                self._wait_loading_gone(timeout=5)
            self.wait_vue_stable()
            headers = self.driver.execute_script("""
                return Array.from(
                    document.querySelectorAll('.el-table__header-wrapper th .cell')
                ).map(function(el) { return el.textContent.trim(); }).filter(Boolean);
            """)
            if headers and len(headers) >= 3:
                return headers
            self._wait_loading_gone(timeout=2)
        return []

    def get_table_row_count(self):
        """获取当前页表格行数"""
        try:
            self._wait_page_ready(timeout=10)
        except Exception:
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
        """根据表头文本获取列索引（1-based）"""
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
        """获取指定列（1-based）所有行数据"""
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
        """根据表头文本获取整列数据"""
        idx = self.get_column_index_by_header(header_text)
        if not idx:
            return []
        return self.get_column_data(idx)

    def get_current_page_number(self):
        """获取当前页码"""
        try:
            el = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(self.CURRENT_PAGE))
            return (el.text or "").strip()
        except Exception:
            return ""

    def click_next_page(self):
        """点击下一页（复用 BasePage.click_next_page）"""
        try:
            self.click_next_page_base()
            self._wait_settled(timeout=10)
            return True
        except Exception:
            return False

    def click_next_page_base(self):
        """BasePage 的 click_next_page 包装，避免递归"""
        super().click_next_page()

    def click_first_row_detail(self):
        """点击第一行的详情按钮"""
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
            (
                By.XPATH,
                '(//div[contains(@class,"el-table__body-wrapper")]//tbody/tr)[1]//td[7]//button[1]',
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
        logger.info("已点击第一行详情按钮")

    def wait_detail_title_visible(self, timeout=8):
        """等待详情弹窗标题可见"""
        xps = [
            '//div[contains(@class,"login-log-detail-dialog") and contains(@class,"el-dialog")]'
            '//header//span[(contains(@class,"el-dialog__title") or @role="heading") and normalize-space(.)="登录日志详情"]',
            '//div[contains(@class,"el-overlay-dialog") and @role="dialog" and (contains(@aria-label,"登录日志详情") or contains(@aria-labelledby,"登录日志详情"))]',
            '//div[contains(@class,"el-overlay-dialog") and @role="dialog"]//header//span[normalize-space(.)="登录日志详情"]',
            '//div[contains(@class,"el-overlay-dialog") and @role="dialog"]//*[normalize-space(.)="登录日志详情"]',
            '//header//span[(contains(@class,"el-dialog__title") or @role="heading") and normalize-space(.)="登录日志详情"]',
            '//*[@role="heading" and normalize-space(.)="登录日志详情"]',
            '//*[contains(@class,"el-dialog__title") and normalize-space(.)="登录日志详情"]',
            '//*[normalize-space(.)="登录日志详情"]',
        ]

        def _find(_driver):
            for xp in xps:
                try:
                    els = _driver.find_elements(By.XPATH, xp)
                    if els:
                        return els[-1]
                except Exception:
                    continue
            return None

        WebDriverWait(self.driver, timeout).until(lambda d: _find(d) is not None)
        logger.info("详情弹窗标题可见")
        return True

    def open_detail_dialog(self, timeout=8):
        """打开详情弹窗并返回弹窗元素"""
        def _find_visible_panel(_driver):
            panels = _driver.find_elements(
                By.XPATH,
                '//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[contains(@class,"el-dialog")]'
                ' | //div[contains(@class,"el-dialog__wrapper") and not(contains(@style,"display: none"))]//div[contains(@class,"el-dialog")]'
                ' | //div[contains(@class,"el-drawer__wrapper") and not(contains(@style,"display: none"))]//div[contains(@class,"el-drawer")]'
                ' | //div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[contains(@class,"el-drawer")]',
            )
            for p in reversed(panels):
                try:
                    if not p.is_displayed():
                        continue
                except Exception:
                    continue
                try:
                    if "登录日志详情" in ((p.text or "").strip()):
                        return p
                except Exception:
                    pass
                try:
                    if p.find_elements(*self.DETAIL_DIALOG_TITLE):
                        return p
                except Exception:
                    pass
                return p

            try:
                title = _driver.find_element(*self.DETAIL_PAGE_TITLE)
                if title and title.is_displayed():
                    try:
                        root = title.find_element(
                            By.XPATH,
                            './ancestor::div[contains(@class,"app-container") or contains(@class,"el-card") or contains(@class,"el-main")][1]',
                        )
                        return root
                    except Exception:
                        return title
            except Exception:
                pass

            try:
                label = _driver.find_element(By.XPATH, '//*[normalize-space(.)="日志编号" or normalize-space(.)="登录时间"]')
                if label and label.is_displayed():
                    try:
                        return label.find_element(By.XPATH, './ancestor::div[contains(@class,"el-card") or contains(@class,"app-container")][1]')
                    except Exception:
                        return label
            except Exception:
                pass
            return None

        return WebDriverWait(self.driver, timeout).until(lambda d: _find_visible_panel(d))

    def get_detail_value(self, label_text):
        """获取详情弹窗中指定标签的值"""
        dialog = self.open_detail_dialog(timeout=6)
        xps = [
            f'.//*[normalize-space(.)="{label_text}"]/ancestor::td[1]/following-sibling::td[1]',
            f'.//*[normalize-space(.)="{label_text}"]/ancestor::th[1]/following-sibling::td[1]',
            f'.//*[contains(@class,"el-descriptions__label") and normalize-space(.)="{label_text}"]/following-sibling::*[1]',
            f'.//*[normalize-space(.)="{label_text}"]/following-sibling::*[1]',
        ]
        for xp in xps:
            try:
                el = dialog.find_element(By.XPATH, xp)
                v = (el.text or "").strip().replace("\n", " ").strip()
                if v != "":
                    return v
            except Exception:
                continue
        try:
            el = self.driver.find_element(By.XPATH, f'//*[normalize-space(.)="{label_text}"]/ancestor::td[1]/following-sibling::td[1]')
            return (el.text or "").strip().replace("\n", " ").strip()
        except Exception:
            pass
        return ""

    def close_detail_dialog(self):
        """关闭详情弹窗"""
        try:
            btn = self.driver.find_element(By.XPATH, '//button[.//*[normalize-space(.)="关闭"] or normalize-space(.)="关闭"]')
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_vue_stable()
            logger.info("已关闭详情弹窗")
            return True
        except Exception:
            pass

        dialog = self.open_detail_dialog(timeout=6)
        candidates = [
            (By.XPATH, './/button[.//*[normalize-space(.)="关闭"] or normalize-space(.)="关闭"]'),
            (By.XPATH, './/button[.//*[normalize-space(.)="取消"] or normalize-space(.)="取消"]'),
            (By.XPATH, './/button[contains(@class,"el-dialog__headerbtn")]'),
        ]
        for loc in candidates:
            try:
                btn = dialog.find_element(*loc)
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_vue_stable()
                    logger.info("已关闭详情弹窗（fallback）")
                    return True
            except Exception:
                continue
        logger.warning("无法关闭详情弹窗")
        return False

    def is_login_page(self):
        """判断当前是否在登录页面"""
        try:
            return bool(self.driver.find_elements(By.XPATH, '//input[@placeholder="请输入账号"]'))
        except Exception:
            return False
