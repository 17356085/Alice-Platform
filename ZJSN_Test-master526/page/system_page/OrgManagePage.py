"""组织管理页面 Page Object — 重构版

变更记录:
  2026-06-11: 继承 BasePage，去绝对XPath，去time.sleep→BasePage等待方法，print→logger
"""
import os
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class OrgManagePage(BasePage):
    """组织管理页面操作 — 继承 BasePage"""

    # ══════════════════════════════════════════════════════════════════
    #  页面专属定位器（CSS优先 → 相对XPath → 文本匹配）
    # ══════════════════════════════════════════════════════════════════

    ORG_NAME_INPUT = (By.XPATH, '//input[contains(@placeholder,"组织名称") or contains(@placeholder,"联系电话")]')

    ORG_TYPE_SELECT_FALLBACK = (
        By.XPATH,
        './/div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"组织类型")]]'
        '//div[contains(@class,"el-select")]',
    )
    ORG_TYPE_SELECT_FALLBACK_SPAN = (
        By.XPATH,
        './/div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"组织类型")]]'
        '//span[contains(@class,"el-select__placeholder")]',
    )
    STATUS_SELECT_FALLBACK = (
        By.XPATH,
        './/div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"状态")]]'
        '//div[contains(@class,"el-select")]',
    )
    STATUS_SELECT_FALLBACK_SPAN = (
        By.XPATH,
        './/div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"状态")]]'
        '//span[contains(@class,"el-select__placeholder")]',
    )

    DOWNLOAD_DIR_DEFAULT = os.path.abspath(os.path.join(os.getcwd(), "downloads"))

    SEARCH_BUTTON = (By.XPATH, '//button[.//*[normalize-space(.)="搜索" or normalize-space(.)="查询"] or contains(normalize-space(.),"搜索") or contains(normalize-space(.),"查询")]')
    RESET_BUTTON = (By.XPATH, '//button[.//*[normalize-space(.)="重置"] or contains(normalize-space(.),"重置")]')
    SEARCH_BUTTON_FALLBACK = (
        By.XPATH,
        '//div[contains(@class,"el-form")]//button[.//span[contains(normalize-space(.),"搜索") or contains(normalize-space(.),"查询")]][1]',
    )
    RESET_BUTTON_FALLBACK = (
        By.XPATH,
        '//div[contains(@class,"el-form")]//button[.//span[contains(normalize-space(.),"重置")]][1]',
    )

    TOOLBAR_ADD = (By.XPATH, '//button[.//span[normalize-space(.)="新增" or normalize-space(.)="新建"]]')
    TOOLBAR_ADD_FALLBACK = (
        By.XPATH,
        '//div[contains(@class,"el-table__toolbar")]//button[1]',
    )
    TOOLBAR_EXPORT_FALLBACK = (
        By.XPATH,
        '//div[contains(@class,"el-table__toolbar")]//button[.//span[text()="导出"]]',
    )

    FIRST_ROW_VIEW_BUTTON_FALLBACK = (
        By.XPATH,
        '(//tr[contains(@class,"el-table__row")])[1]//td[last()]//button[1]',
    )
    FIRST_ROW_EDIT_BUTTON_FALLBACKS = [
        (
            By.XPATH,
            '(//tr[contains(@class,"el-table__row")])[1]//td[last()]//button[2]',
        ),
        (
            By.XPATH,
            '(//tr[contains(@class,"el-table__row")])[1]//td[last()]//button[1]',
        ),
    ]
    FIRST_ROW_ADD_CHILD_BUTTON_FALLBACK = (
        By.XPATH,
        '(//tr[contains(@class,"el-table__row")])[1]//td[last()]//button[3]',
    )
    NINTH_ROW_DELETE_BUTTON_FALLBACK = (
        By.XPATH,
        '(//tr[contains(@class,"el-table__row")])[9]//td[last()]//button[4]',
    )

    # 复用 BasePage 已有定位器：LOADING_MASK, TABLE_ROWS, TABLE_EMPTY, TOTAL_COUNT, TOAST
    EMPTY_TEXT = (By.CSS_SELECTOR, ".el-table__empty-text")
    TABLE_HEADERS = (By.XPATH, '//div[contains(@class,"el-table__header-wrapper")]//th//div')
    TABLE_ROWS_LOCAL = (By.XPATH, '//div[contains(@class,"el-table__body-wrapper")]//table/tbody/tr')
    TABLE_BODY = (By.XPATH, '//div[contains(@class,"el-table__body-wrapper")]')
    TOAST_MESSAGE = (By.CSS_SELECTOR, ".el-message__content")
    TOAST_MESSAGE_CONTAINER = (By.CSS_SELECTOR, 'div[id^="message_"]')
    TOAST_MESSAGE_CONTAINER_TEXT = (By.CSS_SELECTOR, 'div[id^="message_"] .el-message__content')
    TOAST_MESSAGE_ENHANCED = (By.XPATH, '(//*[contains(@class,"el-message__content") and normalize-space(.)!=""])[last()]')

    MESSAGEBOX_CONFIRM = (
        By.XPATH,
        '(//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))])[last()]//button[.//span[normalize-space(.)="确定"]]',
    )

    DIALOG_CONFIRM = (By.XPATH, './/button[.//*[normalize-space(.)="确定"] or contains(normalize-space(.),"确定")]')
    DIALOG_CANCEL = (By.XPATH, './/button[.//*[normalize-space(.)="取消"] or contains(normalize-space(.),"取消")]')
    DIALOG_CLOSE = (By.XPATH, './/button[.//*[normalize-space(.)="关闭"] or contains(normalize-space(.),"关闭")]')

    def __init__(self, driver, timeout=None):
        """初始化 — 继承 BasePage"""
        super().__init__(driver, timeout)
        explicit_wait = self.timeout
        self._explicit_wait = int(explicit_wait) if str(explicit_wait).isdigit() else 5
        self._click_wait = max(3, self._explicit_wait)
        self._table_settle_wait = max(3, min(6, self._explicit_wait + 1))

    def navigate(self):
        """导航到组织管理页面 — 唯一入口"""
        logger.info("导航到 → 系统管理 → 组织管理")
        self.navigate_to("系统管理", "组织管理")
        self.wait_page_ready(timeout=15)
        self._wait_table_settled(timeout=6)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(self.TABLE_BODY))
        return self

    def _wait_table_settled(self, timeout=None):
        timeout = self._table_settle_wait if timeout is None else timeout
        self._wait_loading_gone(timeout=timeout)

    def navigate_to_org_management(self):
        """已弃用: 请使用 navigate() 方法"""
        logger.warning("navigate_to_org_management 已弃用，请使用 navigate()")
        return self.navigate()

    def input_org_name(self, value):
        el = self.wait.until(EC.visibility_of_element_located(self.ORG_NAME_INPUT))
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        if value:
            el.send_keys(value)

    def get_org_name_input_value(self):
        try:
            return (self.find(self.ORG_NAME_INPUT).get_attribute("value") or "").strip()
        except Exception:
            return ""

    def get_empty_text(self):
        self._wait_table_settled()
        try:
            el = self.find(self.EMPTY_TEXT)
            return (el.text or "").strip()
        except Exception:
            return ""

    def _get_form_item(self, label_text):
        xpath = (
            f'//div[contains(@class,"el-form-item")]'
            f'[.//label[contains(@class,"el-form-item__label") and contains(normalize-space(.), "{label_text}")]]'
        )
        return self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

    def _open_form_select(self, label_text, fallback_locators=None):
        fallback_locators = fallback_locators or []
        item = None
        try:
            item = self._get_form_item(label_text)
        except Exception:
            item = None

        click_candidates = []
        for loc in list(fallback_locators):
            try:
                click_candidates.append(self.driver.find_element(*loc))
            except Exception:
                continue
        if item is not None:
            for xp in [
                './/div[contains(@class,"el-select")]',
                './/div[contains(@class,"el-select__wrapper")]',
                './/div[contains(@class,"el-select__selection")]',
                './/span[contains(@class,"el-select__placeholder")]',
                './/input',
                './/i[contains(@class,"el-select__caret")]',
                './/*[name()="svg"]',
            ]:
                try:
                    click_candidates.append(item.find_element(By.XPATH, xp))
                except Exception:
                    continue

        last_exc = None
        for cand in click_candidates:
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", cand)
                self.wait_vue_stable()
                self.driver.execute_script("arguments[0].click();", cand)
                WebDriverWait(self.driver, 2).until(
                    lambda d: any(
                        (e.is_displayed() for e in d.find_elements(By.XPATH, '//*[contains(@class,"el-select-dropdown__item") or @role="option"]')),
                    )
                )
                self.wait_vue_stable()
                return
            except Exception as e:
                last_exc = e
                continue
        raise TimeoutException(f"{label_text}下拉未成功打开: {last_exc}")

    def _click_option_in_visible_select_dropdown(self, option_text):
        def _find_clickable(_driver):
            broad = [
                (
                    By.XPATH,
                    f'//*[normalize-space(.)="{option_text}" and (ancestor::*[contains(@class,"el-select-dropdown") or contains(@class,"el-popper") or @role="listbox"])][last()]',
                ),
                (
                    By.XPATH,
                    f'//*[@role="option" and normalize-space(.)="{option_text}"][last()]',
                ),
            ]
            for loc in broad:
                try:
                    el = _driver.find_element(*loc)
                    if el and el.is_displayed():
                        try:
                            li = el.find_element(
                                By.XPATH,
                                './ancestor::li[1][not(contains(@class,"is-disabled"))] | ./ancestor::*[@role="option"][1]',
                            )
                            if li and li.is_displayed():
                                return li
                        except Exception:
                            return el
                except Exception:
                    continue

            containers = _driver.find_elements(
                By.XPATH,
                '//div[contains(@class,"el-select-dropdown") or contains(@class,"el-popper")]',
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
                    items.extend(
                        c.find_elements(
                            By.XPATH,
                            './/*[contains(@class,"el-select-dropdown__item") and not(contains(@class,"is-disabled"))]',
                        )
                    )
                except Exception:
                    pass

                for it in items:
                    try:
                        t = (it.text or "").strip().replace("\n", " ").strip()
                        if t == option_text:
                            return it
                    except Exception:
                        continue
            return None

        el = WebDriverWait(self.driver, 6).until(lambda d: _find_clickable(d))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        self.driver.execute_script("arguments[0].click();", el)
        self.wait_vue_stable()
        return True

    def select_org_type(self, type_text):
        aliases = {
            "组织": ["部门", "组织"],
            "禁用": ["停用", "禁用"],
        }
        desired_texts = [type_text]
        desired_texts.extend([t for t in aliases.get(type_text, []) if t not in desired_texts])

        self._open_form_select(
            "组织类型",
            fallback_locators=[self.ORG_TYPE_SELECT_FALLBACK, self.ORG_TYPE_SELECT_FALLBACK_SPAN],
        )

        for desired in desired_texts:
            try:
                if self._click_option_in_visible_select_dropdown(desired):
                    return
            except Exception:
                pass

        self._click_option_in_visible_select_dropdown(type_text)

    def select_status(self, status_text):
        if status_text == "禁用":
            status_text = "停用"

        self._open_form_select(
            "状态",
            fallback_locators=[self.STATUS_SELECT_FALLBACK, self.STATUS_SELECT_FALLBACK_SPAN],
        )
        self._click_option_in_visible_select_dropdown(status_text)
        self.wait_vue_stable()
        self._wait_table_settled()

    def get_download_dir(self):
        d = getattr(self.driver, "download_dir", None)
        if d:
            return d
        return self.DOWNLOAD_DIR_DEFAULT

    def wait_for_new_download(self, before_files, timeout=30):
        end = time.time() + timeout
        download_dir = self.get_download_dir()
        before_set = set(before_files)
        while time.time() < end:
            try:
                current = [f for f in os.listdir(download_dir) if os.path.isfile(os.path.join(download_dir, f))]
            except Exception:
                current = []
            new_files = [f for f in current if f not in before_set and not f.endswith(".crdownload")]
            if new_files:
                return os.path.join(download_dir, sorted(new_files, key=lambda x: os.path.getmtime(os.path.join(download_dir, x)))[-1])
            self._wait_loading_gone(timeout=0.5)
        return ""

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
                els = self.driver.find_elements(*self.TOAST_MESSAGE)
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
                els = self.driver.find_elements(*self.TOAST_MESSAGE_CONTAINER_TEXT)
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

            self._wait_loading_gone(timeout=0.3)
        return last

    def confirm_message_box_if_present(self):
        try:
            btn = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located(self.MESSAGEBOX_CONFIRM))
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_vue_stable()
            return True
        except Exception:
            return False

    def _click_with_fallbacks(self, locators, timeout=None):
        timeout = self._click_wait if timeout is None else timeout
        self._wait_table_settled(timeout=min(3, self._table_settle_wait))
        last_exc = None
        for loc in locators:
            try:
                el = WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(loc))
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                except Exception:
                    pass
                if el.is_displayed():
                    self.driver.execute_script("arguments[0].click();", el)
                else:
                    self.driver.execute_script("arguments[0].click();", el)
                self._wait_table_settled(timeout=min(4, self._table_settle_wait))
                return
            except Exception as e:
                last_exc = e
                continue
        raise last_exc if last_exc else TimeoutException("点击失败")

    def click_search(self):
        logger.info("点击搜索按钮")
        self._click_with_fallbacks([self.SEARCH_BUTTON, self.SEARCH_BUTTON_FALLBACK])

    def click_reset(self):
        logger.info("点击重置按钮")
        self._click_with_fallbacks([self.RESET_BUTTON, self.RESET_BUTTON_FALLBACK])

    def click_add(self):
        logger.info("点击新增按钮")
        self._click_with_fallbacks([self.TOOLBAR_ADD, self.TOOLBAR_ADD_FALLBACK])

    def click_export(self):
        logger.info("点击导出按钮")
        candidates = [
            (By.XPATH, '//button[.//span[normalize-space(.)="导出"] or normalize-space(.)="导出"]'),
            self.TOOLBAR_EXPORT_FALLBACK,
        ]
        self._click_with_fallbacks(candidates)
        self.confirm_message_box_if_present()

    def _get_visible_dialog(self):
        locator = (
            By.XPATH,
            '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[contains(@class,"el-dialog")]'
            ' | //div[contains(@class,"el-dialog__wrapper") and not(contains(@style,"display: none"))]//div[contains(@class,"el-dialog")])[last()]',
        )
        return self.wait.until(EC.visibility_of_element_located(locator))

    def _get_dialog_form_item(self, label_text):
        item_xpath = (
            f'.//div[contains(@class,"el-form-item")]'
            f'[.//label[contains(@class,"el-form-item__label") and contains(normalize-space(.), "{label_text}")]]'
        )

        def _locate(_driver):
            dialog = self._get_visible_dialog()
            return dialog.find_element(By.XPATH, item_xpath)

        return WebDriverWait(self.driver, 8).until(lambda d: _locate(d))

    def input_dialog_field(self, label_text, value):
        dialog = self._get_visible_dialog()
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
        try:
            dialog.click()
        except Exception:
            pass

    def _open_dialog_select(self, label_text):
        item = self._get_dialog_form_item(label_text)
        for xp in [
            './/div[contains(@class,"el-select")]',
            './/div[contains(@class,"el-select__wrapper")]',
            './/div[contains(@class,"el-select__selection")]',
            './/span[contains(@class,"el-select__placeholder")]',
            './/input',
            './/i[contains(@class,"el-select__caret")]',
            './/*[name()="svg"]',
        ]:
            try:
                el = item.find_element(By.XPATH, xp)
                self.driver.execute_script("arguments[0].click();", el)
                WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '(//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))])[last()]')
                    )
                )
                return
            except Exception:
                continue
        raise TimeoutException(f"弹窗下拉未打开: {label_text}")

    def select_dialog_option(self, label_text, option_text):
        self._open_dialog_select(label_text)
        option_locators = [
            (
                By.XPATH,
                f'(//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))])[last()]'
                f'//li[not(contains(@class,"is-disabled"))]//*[normalize-space(.)="{option_text}"]/ancestor::li[1]',
            ),
            (
                By.XPATH,
                f'(//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))])[last()]'
                f'//li[not(contains(@class,"is-disabled"))]//*[contains(normalize-space(.),"{option_text}")]/ancestor::li[1]',
            ),
        ]
        for loc in option_locators:
            try:
                option = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(loc))
                self.driver.execute_script("arguments[0].click();", option)
                return
            except Exception:
                continue
        raise TimeoutException(f"弹窗下拉未找到选项: {label_text}={option_text}")

    def select_dialog_status(self, status_text):
        item = self._get_dialog_form_item("状态")
        label = item.find_element(
            By.XPATH,
            f'.//label[(contains(@class,"el-radio") or contains(@class,"el-radio-button"))][.//*[normalize-space(.)="{status_text}"]]',
        )
        self.driver.execute_script("arguments[0].click();", label)
        self.wait_vue_stable()

    def click_dialog_confirm(self):
        logger.info("点击弹窗确定按钮")
        try:
            dialog = self._get_visible_dialog()
            btns = dialog.find_elements(*self.DIALOG_CONFIRM)
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

        fallbacks = [
            (
                By.XPATH,
                '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]//button[contains(normalize-space(.),"确定")]',
            ),
            (By.XPATH, '(//button[contains(normalize-space(.),"确定")])[last()]'),
        ]
        for loc in fallbacks:
            try:
                btn = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(loc))
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_vue_stable()
                    return
            except Exception:
                continue
        logger.error("未找到弹窗确定按钮")
        raise TimeoutException("未找到弹窗确定按钮")

    def click_dialog_cancel(self):
        logger.info("点击弹窗取消按钮")
        try:
            dialog = self._get_visible_dialog()
            btns = dialog.find_elements(*self.DIALOG_CANCEL)
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

        fallbacks = [
            (
                By.XPATH,
                '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]//button[contains(normalize-space(.),"取消")]',
            ),
            (By.XPATH, '(//button[contains(normalize-space(.),"取消")])[last()]'),
        ]
        for loc in fallbacks:
            try:
                btn = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(loc))
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_vue_stable()
                    return
            except Exception:
                continue
        logger.error("未找到弹窗取消按钮")
        raise TimeoutException("未找到弹窗取消按钮")

    def click_dialog_close(self):
        logger.info("点击弹窗关闭按钮")
        try:
            dialog = self._get_visible_dialog()
            btns = dialog.find_elements(*self.DIALOG_CLOSE)
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

        fallbacks = [
            (
                By.XPATH,
                '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]//button[contains(normalize-space(.),"关闭")]',
            ),
            (By.XPATH, '(//button[contains(normalize-space(.),"关闭")])[last()]'),
        ]
        for loc in fallbacks:
            try:
                btn = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(loc))
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_vue_stable()
                    return
            except Exception:
                continue
        logger.error("未找到弹窗关闭按钮")
        raise TimeoutException("未找到弹窗关闭按钮")

    def click_row_action(self, org_name, action_text):
        row_xpath_candidates = [
            f'//tr[contains(@class,"el-table__row")][.//td[1]//*[contains(normalize-space(.),"{org_name}")]]',
            f'//tr[contains(@class,"el-table__row")][contains(normalize-space(.),"{org_name}")]',
        ]
        for row_xpath in row_xpath_candidates:
            btn_xpath_candidates = [
                f'{row_xpath}//td[last()]//*[self::span or self::button][normalize-space(.)="{action_text}"]/ancestor::button[1]',
                f'{row_xpath}//td[last()]//*[normalize-space(.)="{action_text}"]',
            ]
            for xp in btn_xpath_candidates:
                try:
                    el = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.XPATH, xp)))
                    if el.is_displayed():
                        self.driver.execute_script("arguments[0].click();", el)
                        self.wait_vue_stable()
                        return
                except Exception:
                    continue
        logger.error("未找到组织'%s'的操作按钮: %s", org_name, action_text)
        raise TimeoutException(f"未找到组织'{org_name}'的操作按钮: {action_text}")

    def open_add_child_dialog(self, parent_org_name):
        self.click_row_action(parent_org_name, "新增子组织")
        return self._get_visible_dialog()

    def delete_org_by_name(self, org_name):
        self.click_row_action(org_name, "删除")
        self.confirm_message_box_if_present()
        return self.wait_for_toast_text(timeout=6)

    def click_first_row_view(self):
        logger.info("尝试点击第一行的查看按钮")
        self._click_with_fallbacks([self.FIRST_ROW_VIEW_BUTTON_FALLBACK])
        logger.info("查看按钮点击完成")

    def click_first_row_edit(self):
        logger.info("点击第一行编辑按钮")
        self._click_with_fallbacks(self.FIRST_ROW_EDIT_BUTTON_FALLBACKS)

    def click_first_row_add_child(self):
        logger.info("点击第一行新增子组织按钮")
        self._click_with_fallbacks([self.FIRST_ROW_ADD_CHILD_BUTTON_FALLBACK])

    def click_ninth_row_delete(self):
        logger.info("点击第九行删除按钮")
        self._click_with_fallbacks([self.NINTH_ROW_DELETE_BUTTON_FALLBACK])

    def delete_ninth_row_and_confirm(self):
        self.click_ninth_row_delete()
        self.confirm_message_box_if_present()
        return self.wait_for_toast_text(timeout=6)

    def open_view_dialog(self, org_name=None):
        """打开查看组织弹窗，并兼容 dialog / drawer 两种展示形式。"""
        last_exc = None
        for attempt in range(2):
            logger.info("尝试第 %d 次打开查看弹窗", attempt + 1)
            try:
                if org_name:
                    self.click_row_action(org_name, "查看")
                else:
                    self.click_first_row_view()
            except Exception as e:
                last_exc = e
                logger.error("点击按钮失败: %s", e)

            candidates = [
                (
                    By.XPATH,
                    '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//*[contains(@class,"el-dialog") or contains(@class,"el-drawer")])[last()]',
                ),
                (
                    By.XPATH,
                    '(//div[contains(@class,"el-dialog__wrapper") and not(contains(@style,"display: none"))]//div[contains(@class,"el-dialog")])[last()]',
                ),
                (
                    By.XPATH,
                    '(//div[contains(@class,"el-drawer__wrapper") and not(contains(@style,"display: none"))]//*[contains(@class,"el-drawer")])[last()]',
                ),
            ]

            logger.info("开始检测弹窗元素...")
            for i, loc in enumerate(candidates):
                logger.info("尝试定位器 %d: %s", i + 1, loc)
                try:
                    dialog = WebDriverWait(self.driver, 6).until(EC.visibility_of_element_located(loc))
                    try:
                        title = (dialog.find_element(By.XPATH, './/header//*[contains(@class,"el-dialog__title") or self::span]').text or dialog.text).strip()
                        if title:
                            logger.info("查看弹窗标题: %s", title)
                    except Exception:
                        pass
                    logger.info("成功找到弹窗")
                    return dialog
                except Exception as e:
                    last_exc = e
                    logger.error("定位器 %d 失败: %s", i + 1, e)
                    continue

            page_source = self.driver.page_source or ""
            logger.info("页面源码中包含'查看组织': %s", "查看组织" in page_source)
            try:
                if "查看组织" in page_source:
                    logger.info("页面中存在'查看组织'文本，尝试获取可见对话框")
                    return self._get_visible_dialog(timeout=3)
            except Exception as e:
                logger.error("_get_visible_dialog 失败: %s", e)
                pass

        raise last_exc if last_exc else TimeoutException("查看弹窗未打开")

    def get_table_headers(self):
        """JS提取表格表头（含重试，应对Element Plus异步渲染）"""
        for attempt in range(6):
            try:
                self._wait_table_settled()
            except Exception:
                self._wait_loading_gone(timeout=2)
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
        self._wait_table_settled()
        rows = self.driver.find_elements(*self.TABLE_ROWS_LOCAL)
        count = 0
        for r in rows:
            try:
                if r.is_displayed():
                    count += 1
            except Exception:
                continue
        return count

    def get_column_index_by_header(self, header_text):
        self._wait_table_settled()
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

    def get_column_data(self, col_index):
        self._wait_table_settled()
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

    def expand_first_row_if_possible(self):
        self._wait_table_settled()
        candidates = self.driver.find_elements(By.CSS_SELECTOR, ".el-table__expand-icon")
        for el in candidates:
            try:
                if el.is_displayed():
                    self.driver.execute_script("arguments[0].click();", el)
                    self._wait_table_settled()
                    self.wait_vue_stable()
                    return True
            except Exception:
                continue
        return False
