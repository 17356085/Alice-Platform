"""参数设置页面 Page Object — 重构版

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
from config import TIMEOUT_CONFIG

logger = logging.getLogger(__name__)


class ParamsManagePage(BasePage):
    """参数设置页面操作 — 继承 BasePage"""

    # ══════════════════════════════════════════════════════════════════
    #  导航 — 复用 BasePage.navigate_to("系统管理", "参数设置")
    # ══════════════════════════════════════════════════════════════════

    PARAM_NAME_INPUT = (By.XPATH, '//input[@placeholder="请输入参数名称"]')
    PARAM_KEY_INPUT = (By.XPATH, '//input[@placeholder="请输入参数键名"]')

    PARAM_TYPE_SELECT = (
        By.XPATH,
        '//div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"参数类型")]]//div[contains(@class,"el-select")]',
    )
    PARAM_TYPE_SELECT_FALLBACK = (
        By.XPATH,
        '//div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"参数类型")]]//div[contains(@class,"el-select")]',
    )

    BUSINESS_MODULE_SELECT = (
        By.XPATH,
        '//div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"业务模块")]]//div[contains(@class,"el-select")]',
    )

    SEARCH_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="搜索" or normalize-space(.)="查询"]]')
    RESET_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="重置"]]')

    TOOLBAR_ADD = (By.XPATH, '//button[.//span[normalize-space(.)="新增"] or contains(normalize-space(.),"新增")]')
    TOOLBAR_EXPORT = (By.XPATH, '//button[.//span[normalize-space(.)="导出"] or contains(normalize-space(.),"导出")]')
    TOOLBAR_REFRESH_CACHE = (By.XPATH, '//button[.//span[normalize-space(.)="刷新缓存"] or contains(normalize-space(.),"刷新缓存")]')
    TOOLBAR_REFRESH_CACHE_FALLBACK = (
        By.XPATH,
        '//button[.//span[normalize-space(.)="刷新缓存"] or contains(normalize-space(.),"刷新缓存")]',
    )

    DELETE_FIRST_ROW_BUTTON_FALLBACK = (
        By.XPATH,
        '//tr[contains(@class,"el-table__row")][1]//button[.//span[normalize-space(.)="删除"] or contains(normalize-space(.),"删除")]',
    )

    LOADING_MASK = (By.CSS_SELECTOR, ".el-loading-mask")
    EMPTY_TEXT = (By.CSS_SELECTOR, ".el-table__empty-text")
    TABLE_HEADERS = (By.XPATH, '//div[contains(@class,"el-table__header-wrapper")]//th//div')
    TABLE_ROWS = (By.XPATH, '//div[contains(@class,"el-table__body-wrapper")]//table/tbody/tr')

    PAGINATION = (By.CSS_SELECTOR, ".el-pagination")
    CURRENT_PAGE = (By.CSS_SELECTOR, ".el-pagination .el-pager li.active, .el-pagination .el-pager li.is-active")
    NEXT_PAGE_BUTTON = (By.CSS_SELECTOR, ".el-pagination .btn-next")
    NEXT_PAGE_BUTTON_FALLBACKS = [
        (By.CSS_SELECTOR, ".el-pagination button.btn-next"),
        (By.XPATH, '//div[contains(@class,"el-pagination")]//button[contains(@class,"btn-next")]'),
        (By.XPATH, '//button[@aria-label="下一页" or @aria-label="Next page"]'),
    ]

    MESSAGEBOX_CONFIRM = (
        By.XPATH,
        '(//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))])[last()]//button[.//*[normalize-space(.)="确定"]]',
    )
    MESSAGEBOX_CANCEL = (
        By.XPATH,
        '(//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))])[last()]//button[.//*[normalize-space(.)="取消"]]',
    )

    DIALOG_CONFIRM_FALLBACKS = [
        (By.XPATH, '(//footer[contains(@class,"el-dialog__footer")]//button[.//*[normalize-space(.)="确定"]])[last()]'),
        (By.XPATH, '(//div[contains(@class,"el-dialog")])[last()]//button[.//*[normalize-space(.)="确定"] or contains(normalize-space(.),"确定")]'),
    ]
    DIALOG_CANCEL_FALLBACKS = [
        (By.XPATH, '(//footer[contains(@class,"el-dialog__footer")]//button[.//*[normalize-space(.)="取消"]])[last()]'),
        (By.XPATH, '(//div[contains(@class,"el-dialog")])[last()]//button[.//*[normalize-space(.)="取消"] or contains(normalize-space(.),"取消")]'),
    ]

    TOAST_TEXT = (By.CSS_SELECTOR, ".el-message__content")
    TOAST_TEXT_FALLBACK = (By.CSS_SELECTOR, 'div[id^="message_"] p, div[id^="message_"] .el-message__content, div[id^="message_"]')
    TOAST_MESSAGE_ENHANCED = (By.XPATH, '(//*[contains(@class,"el-message__content") and normalize-space(.)!=""])[last()]')

    def __init__(self, driver, timeout=None):
        """初始化参数设置页面 — 继承 BasePage"""
        super().__init__(driver, timeout)

    # ══════════════════════════════════════════════════════════════════
    #  导航（重构：统一使用 BasePage.navigate_to）
    # ══════════════════════════════════════════════════════════════════

    def navigate(self):
        """导航到参数设置页面 — 唯一入口"""
        logger.info("导航到 → 系统管理 → 参数设置")
        self.navigate_to("系统管理", "参数设置")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        return self

    # 向后兼容别名
    def navigate_to_params_settings(self):
        """导航到参数设置页面（JS hash 直接跳转）"""
        logger.info("导航到 → 系统管理 → 参数设置")
        from base.sidebar_navigator import SidebarNavigator
        nav = SidebarNavigator(self.driver)
        nav._navigate_by_js_hash("#/system/config", "参数设置")
        self._wait_loading_gone(timeout=10)
        self._wait_table_settled(timeout=12)

    def _wait_table_settled(self, timeout=8):
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
            time.sleep(TIMEOUT_CONFIG["micro_wait"])

    def wait_for_toast_text(self, timeout=6):
        """等待并获取Toast提示消息文本"""
        end = time.time() + timeout
        last = ""
        while time.time() < end:
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

    def input_param_name(self, value):
        el = self.wait.until(EC.presence_of_element_located(self.PARAM_NAME_INPUT))
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        if value:
            el.send_keys(value)

    def input_param_key(self, value):
        el = self.wait.until(EC.presence_of_element_located(self.PARAM_KEY_INPUT))
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        if value:
            el.send_keys(value)

    def _open_select(self, locator, fallback=None):
        self._wait_table_settled(timeout=6)
        try:
            el = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(locator))
        except Exception:
            if not fallback:
                raise
            el = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(fallback))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)

        def _dropdown_visible():
            try:
                dds = self.driver.find_elements(
                    By.XPATH,
                    '//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]'
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

        click_targets = []
        click_targets.append(el)
        try:
            click_targets.append(el.find_element(By.XPATH, 'ancestor::div[contains(@class,"el-select")][1]'))
        except Exception:
            pass
        try:
            click_targets.append(el.find_element(By.XPATH, './/div[contains(@class,"el-select__wrapper")]'))
        except Exception:
            pass
        try:
            click_targets.append(el.find_element(By.XPATH, './/i[contains(@class,"el-select__caret")]'))
        except Exception:
            pass

        for _ in range(3):
            for t in click_targets:
                try:
                    self.driver.execute_script("arguments[0].click();", t)
                except Exception:
                    continue
                self.wait_vue_stable()
                if _dropdown_visible():
                    return
        raise TimeoutException("下拉框未能展开")

    def _select_dropdown_option(self, option_text):
        def _normalize_text(s):
            return (s or "").replace(" ", " ").replace("\n", " ").strip()

        def _clickable_ancestor(el):
            try:
                return el.find_element(
                    By.XPATH,
                    './ancestor::li[1][not(contains(@class,"is-disabled"))]'
                    ' | ./ancestor::*[@role="option"][1][not(contains(@class,"is-disabled"))]'
                    ' | ./ancestor::div[contains(@class,"el-select-dropdown__item")][1][not(contains(@class,"is-disabled"))]',
                )
            except Exception:
                return el

        def _find_option(_driver, exact=True):
            containers = _driver.find_elements(
                By.XPATH,
                '//div[contains(@class,"el-select-dropdown") or contains(@class,"el-select__popper") or contains(@class,"el-popper")]',
            )
            for c in reversed(containers):
                try:
                    if not c.is_displayed():
                        continue
                except Exception:
                    continue
                try:
                    if option_text and option_text not in (c.text or ""):
                        pass
                except Exception:
                    pass
                candidates = []
                try:
                    candidates.extend(c.find_elements(By.XPATH, './/li[not(contains(@class,"is-disabled"))]'))
                except Exception:
                    pass
                try:
                    candidates.extend(c.find_elements(By.XPATH, './/*[@role="option" and not(contains(@class,"is-disabled"))]'))
                except Exception:
                    pass
                try:
                    candidates.extend(c.find_elements(By.XPATH, './/div[contains(@class,"el-select-dropdown__item") and not(contains(@class,"is-disabled"))]'))
                except Exception:
                    pass
                broad = []
                try:
                    broad.extend(c.find_elements(By.XPATH, f'.//*[self::span or self::div][normalize-space(.)="{option_text}"]'))
                except Exception:
                    pass
                try:
                    broad.extend(c.find_elements(By.XPATH, f'.//*[self::span or self::div][contains(normalize-space(.), "{option_text}")]'))
                except Exception:
                    pass
                for el in broad:
                    try:
                        if not el.is_displayed():
                            continue
                    except Exception:
                        continue
                    cand = _clickable_ancestor(el)
                    if cand:
                        candidates.insert(0, cand)
                for el in candidates:
                    try:
                        t = _normalize_text(el.text)
                        if not t:
                            continue
                        if exact and t == option_text:
                            return _clickable_ancestor(el)
                        if (not exact) and (option_text in t):
                            return _clickable_ancestor(el)
                    except Exception:
                        continue
            return None

        opt = WebDriverWait(self.driver, 8).until(lambda d: _find_option(d, exact=True) or _find_option(d, exact=False))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", opt)
        try:
            self.driver.execute_script("arguments[0].click();", opt)
        except Exception:
            try:
                opt.click()
            except Exception:
                pass
        self.wait_vue_stable()

    def select_param_type(self, type_text):
        self._open_select(self.PARAM_TYPE_SELECT, fallback=self.PARAM_TYPE_SELECT_FALLBACK)
        self._select_dropdown_option(type_text)
        self._wait_table_settled(timeout=8)

    def select_business_module(self, module_text):
        self._open_select(self.BUSINESS_MODULE_SELECT)
        self._select_dropdown_option(module_text)
        self._wait_table_settled(timeout=8)

    def click_search(self):
        self._wait_table_settled(timeout=6)
        btn = self.wait.until(EC.presence_of_element_located(self.SEARCH_BUTTON))
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_table_settled(timeout=10)

    def click_reset(self):
        self._wait_table_settled(timeout=6)
        btn = self.wait.until(EC.presence_of_element_located(self.RESET_BUTTON))
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_table_settled(timeout=10)

    def click_add(self):
        self._wait_table_settled(timeout=6)
        btn = self.wait.until(EC.presence_of_element_located(self.TOOLBAR_ADD))
        self.driver.execute_script("arguments[0].click();", btn)
        self._get_visible_dialog(timeout=8)

    def click_export(self):
        self._wait_table_settled(timeout=6)
        btn = self.wait.until(EC.presence_of_element_located(self.TOOLBAR_EXPORT))
        self.driver.execute_script("arguments[0].click();", btn)
        confirmed = self.confirm_message_box_if_present(timeout=4)
        return confirmed or bool(self.wait_for_toast_text(timeout=4))

    def click_refresh_cache(self):
        self._wait_table_settled(timeout=6)
        btn = None
        try:
            btn = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(self.TOOLBAR_REFRESH_CACHE))
        except Exception:
            btn = None

        if btn is None:
            try:
                btn = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(self.TOOLBAR_REFRESH_CACHE_FALLBACK))
            except Exception:
                btn = None

        if not btn:
            raise TimeoutException("未找到刷新缓存按钮")

        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        except Exception:
            pass

        try:
            if btn.tag_name and btn.tag_name.lower() == "span":
                btn = btn.find_element(By.XPATH, "./ancestor::button[1]")
        except Exception:
            pass
        self.driver.execute_script("arguments[0].click();", btn)
        self.wait_vue_stable()

    def confirm_message_box_if_present(self, timeout=2):
        try:
            btn = WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(self.MESSAGEBOX_CONFIRM))
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_vue_stable()
            return True
        except Exception:
            return False

    def get_empty_text(self):
        self._wait_table_settled(timeout=8)
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
        self._wait_table_settled(timeout=10)
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        count = 0
        for r in rows:
            try:
                if r.is_displayed():
                    count += 1
            except Exception:
                continue
        return count

    def _scroll_to_pagination_area(self):
        try:
            el = self.driver.find_element(*self.PAGINATION)
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        except Exception:
            pass

    def get_current_page_number(self):
        try:
            els = self.driver.find_elements(*self.CURRENT_PAGE)
            el = els[0] if els else WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(self.CURRENT_PAGE))
            text = (el.text or "").strip()
            return int(text) if text.isdigit() else 1
        except Exception:
            return 1

    def click_next_page(self):
        self._scroll_to_pagination_area()
        btn = None
        candidates = [self.NEXT_PAGE_BUTTON] + list(self.NEXT_PAGE_BUTTON_FALLBACKS)
        for loc in candidates:
            try:
                btn = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(loc))
                if btn and btn.is_displayed():
                    break
            except Exception:
                continue

        if not btn:
            return False

        disabled = (btn.get_attribute("disabled") is not None) or ("is-disabled" in (btn.get_attribute("class") or ""))
        if disabled:
            return False

        before = self.get_current_page_number()
        self.driver.execute_script("arguments[0].click();", btn)
        try:
            WebDriverWait(self.driver, 5).until(lambda d: self.get_current_page_number() != before)
            self.wait_vue_stable()
            return True
        except Exception:
            return True

    def get_first_row_param_name(self):
        names = self.get_column_data_by_header("参数名称")
        return names[0] if names else ""

    def get_column_index_by_header(self, header_text):
        self._wait_table_settled(timeout=10)
        ths = self.driver.find_elements(By.XPATH, '//div[contains(@class,"el-table__header-wrapper")]//table//th')
        for idx, th in enumerate(ths, start=1):
            try:
                t = (th.text or "").strip()
                if t == header_text:
                    return idx
            except Exception:
                continue
        return None

    def get_column_data_by_header(self, header_text):
        idx = self.get_column_index_by_header(header_text)
        if not idx:
            return []
        return self.get_column_data(idx)

    def get_column_data_by_headers(self, header_candidates):
        for h in header_candidates:
            data = self.get_column_data_by_header(h)
            if data:
                return data
        return []

    def get_column_data(self, col_index):
        self._wait_table_settled(timeout=10)
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

    def _get_visible_dialog(self, timeout=8):
        locator = (
            By.XPATH,
            '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[contains(@class,"el-dialog")]'
            ' | //div[contains(@class,"el-dialog__wrapper") and not(contains(@style,"display: none"))]//div[contains(@class,"el-dialog")])[last()]',
        )
        return WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(locator))

    def _get_dialog_form_item(self, label_text):
        item_xpath = (
            f'.//div[contains(@class,"el-form-item")]'
            f'[.//label[contains(@class,"el-form-item__label") and contains(normalize-space(.), "{label_text}")]]'
        )

        def _locate(_driver):
            dialog = self._get_visible_dialog(timeout=8)
            return dialog.find_element(By.XPATH, item_xpath)

        return WebDriverWait(self.driver, 8).until(lambda d: _locate(d))

    def input_dialog_field(self, label_text, value):
        item = self._get_dialog_form_item(label_text)
        el = item.find_element(By.XPATH, './/input|.//textarea')
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        except Exception:
            pass
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        if value is not None and value != "":
            el.send_keys(str(value))

    def input_dialog_field_by_candidates(self, label_candidates, value):
        last_exc = None
        for label_text in label_candidates:
            try:
                self.input_dialog_field(label_text, value)
                return True
            except Exception as e:
                last_exc = e
                continue
        if last_exc:
            raise last_exc
        raise TimeoutException(f"未找到弹窗字段: {label_candidates}")

    def select_dialog_radio(self, label_text, option_text):
        item = self._get_dialog_form_item(label_text)
        try:
            radio = item.find_element(
                By.XPATH,
                f'.//label[contains(@class,"el-radio")][.//*[normalize-space(.)="{option_text}"]]',
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", radio)
            self.driver.execute_script("arguments[0].click();", radio)
            self.wait_vue_stable()
            return
        except Exception:
            pass

        try:
            self.select_dialog_option(label_text, option_text)
            return
        except Exception:
            pass

        try:
            switch = item.find_element(By.XPATH, './/*[contains(@class,"el-switch") or @role="switch"]')
            checked = (switch.get_attribute("aria-checked") or "").lower() == "true"
            want_on = option_text in ["启用", "开启", "是", "开"]
            if want_on != checked:
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", switch)
                self.driver.execute_script("arguments[0].click();", switch)
                self.wait_vue_stable()
            return
        except Exception:
            raise TimeoutException(f"未找到弹窗单选/开关: {label_text} -> {option_text}")

    def _get_first_row(self):
        self._wait_table_settled(timeout=10)
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        for r in rows:
            try:
                if r.is_displayed():
                    return r
            except Exception:
                continue
        return None

    def _click_row_action(self, row, action_texts):
        last_exc = None
        for t in action_texts:
            try:
                btn = row.find_element(By.XPATH, f'.//button[.//span[normalize-space(.)="{t}"] or normalize-space(.)="{t}"]')
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_vue_stable()
                return True
            except Exception as e:
                last_exc = e
                continue
        if last_exc:
            raise last_exc
        return False

    def delete_first_row(self):
        self._wait_table_settled(timeout=10)
        row = self._get_first_row()
        if row:
            try:
                self._click_row_action(row, ["删除"])
                self.confirm_message_box_if_present(timeout=4)
                self._wait_table_settled(timeout=10)
                return True
            except Exception:
                pass

        try:
            span = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(self.DELETE_FIRST_ROW_BUTTON_FALLBACK))
            btn = span.find_element(By.XPATH, "./ancestor::button[1]")
            self.driver.execute_script("arguments[0].click();", btn)
            self.confirm_message_box_if_present(timeout=4)
            self._wait_table_settled(timeout=10)
            return True
        except Exception:
            return False

    def click_edit_first_row(self):
        self._wait_table_settled(timeout=10)
        row = self._get_first_row()
        if not row:
            raise TimeoutException("列表无数据，无法编辑")
        self._click_row_action(row, ["编辑", "修改"])
        self._get_visible_dialog(timeout=8)

    def select_dialog_option(self, label_text, option_text):
        item = self._get_dialog_form_item(label_text)
        select = None
        for xp in [
            './/div[contains(@class,"el-select")]',
            './/div[contains(@class,"el-select__wrapper")]',
            './/div[contains(@class,"el-input") and .//*[contains(@class,"el-select") or contains(@class,"el-select__caret")]]',
        ]:
            try:
                select = item.find_element(By.XPATH, xp)
                if select and select.is_displayed():
                    break
            except Exception:
                continue
        if not select:
            raise TimeoutException(f"未找到弹窗下拉框: {label_text}")
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", select)

        def _dropdown_visible():
            try:
                dds = self.driver.find_elements(
                    By.XPATH,
                    '//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]'
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

        def _get_selected_text():
            try:
                inp = select.find_element(By.XPATH, './/input')
                v = (inp.get_attribute("value") or "").strip()
                if v:
                    return v
            except Exception:
                pass
            for xp in [
                './/*[contains(@class,"el-select__selected-item")]',
                './/*[contains(@class,"selected") and contains(@class,"item")]',
            ]:
                try:
                    t = (select.find_element(By.XPATH, xp).text or "").strip()
                    if t:
                        return t
                except Exception:
                    continue
            try:
                return (select.text or "").strip()
            except Exception:
                return ""

        click_targets = [select]
        for xp in [
            './/div[contains(@class,"el-select__wrapper")]',
            './/div[contains(@class,"el-select__selection")]',
            './/div[contains(@class,"el-select__selected-item")]',
            './/span[contains(@class,"el-select__placeholder")]',
            './/i[contains(@class,"el-select__caret")]',
        ]:
            try:
                click_targets.append(select.find_element(By.XPATH, xp))
            except Exception:
                continue

        last_exc = None
        for _ in range(2):
            for __ in range(3):
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
                        break
                if _dropdown_visible():
                    break
            if not _dropdown_visible():
                raise TimeoutException(f"弹窗下拉框未能展开: {label_text}")
            try:
                self._select_dropdown_option(option_text)
                WebDriverWait(self.driver, 3).until(lambda d: option_text in (_get_selected_text() or ""))
                return
            except Exception as e:
                last_exc = e
                try:
                    self.driver.execute_script("arguments[0].click();", select)
                except Exception:
                    pass
                self.wait_vue_stable()
                continue
        raise last_exc if last_exc else TimeoutException(f"选择下拉选项失败: {label_text} -> {option_text}")

    def get_dialog_error_text(self):
        try:
            dialog = self._get_visible_dialog(timeout=3)
        except Exception:
            return ""
        texts = []
        errs = dialog.find_elements(By.CSS_SELECTOR, ".el-form-item__error")
        for e in errs:
            try:
                if e.is_displayed():
                    t = (e.text or "").strip()
                    if t:
                        texts.append(t)
            except Exception:
                continue
        return "；".join(texts).strip()

    def click_dialog_confirm(self):
        try:
            dialog = self._get_visible_dialog(timeout=8)
            btns = dialog.find_elements(By.XPATH, './/button[.//*[normalize-space(.)="确定"] or contains(normalize-space(.),"确定")]')
            for btn in btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_vue_stable()
                        return
                except Exception:
                    continue
        except Exception:
            pass

        for loc in self.DIALOG_CONFIRM_FALLBACKS:
            try:
                btn = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(loc))
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_vue_stable()
                    return
            except Exception:
                continue
        raise TimeoutException("未找到弹窗确定按钮")

    def click_dialog_cancel(self):
        try:
            dialog = self._get_visible_dialog(timeout=8)
            btns = dialog.find_elements(By.XPATH, './/button[.//*[normalize-space(.)="取消"] or contains(normalize-space(.),"取消")]')
            for btn in btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_vue_stable()
                        return
                except Exception:
                    continue
        except Exception:
            pass

        for loc in self.DIALOG_CANCEL_FALLBACKS:
            try:
                btn = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(loc))
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_vue_stable()
                    return
            except Exception:
                continue
        raise TimeoutException("未找到弹窗取消按钮")

    def wait_dialog_closed(self, timeout=5):
        """等待当前弹窗关闭"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-overlay-dialog, .el-dialog__wrapper, .el-dialog"))
            )
            return True
        except Exception:
            return False
