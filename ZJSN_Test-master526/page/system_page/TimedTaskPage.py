"""定时任务页面 Page Object — 重构版

变更记录:
  2026-06-11: 继承 BasePage，去绝对XPath，去time.sleep→BasePage等待方法
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


class TimedTaskPage(BasePage):
    """定时任务页面操作 — 继承 BasePage"""

    # ══════════════════════════════════════════════════════════════════
    #  页面专属定位器（CSS优先 → 相对XPath → 文本匹配）
    # ══════════════════════════════════════════════════════════════════

    SYSTEM_MANAGEMENT = (By.XPATH, '//span[normalize-space(.)="系统管理"]')
    LOG_MANAGEMENT = (By.XPATH, '//span[normalize-space(.)="日志管理"]')
    TIMED_TASK = (By.XPATH, '//span[normalize-space(.)="定时任务"]')

    TASK_NAME_INPUT = (By.CSS_SELECTOR, 'input[placeholder*="请输入任务名称"]')
    TASK_TYPE_SELECT = (
        By.XPATH,
        '(//label[normalize-space(.)="任务类型"]/following::div[contains(@class,"el-select")][1])[1]',
    )

    STATUS_ALL = (By.XPATH, '//label[contains(@class,"el-radio")][.//span[normalize-space(.)="全部"]]')
    STATUS_RUNNING = (By.XPATH, '//label[contains(@class,"el-radio")][.//span[normalize-space(.)="运行中"]]')
    STATUS_PAUSED = (By.XPATH, '//label[contains(@class,"el-radio")][.//span[normalize-space(.)="已暂停"] or .//span[normalize-space(.)="已停停"] or .//span[contains(normalize-space(.),"暂停")]]')

    SEARCH_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="搜索"] or normalize-space(.)="搜索"]')
    RESET_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="重置"] or contains(normalize-space(.),"重置")]')

    SELECT_DROPDOWN_PANEL = (
        By.XPATH,
        '(//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))])[last()]',
    )

    TOOLBAR_ADD = (By.XPATH, '//button[.//span[normalize-space(.)="新增"] or normalize-space(.)="新增"]')
    TOOLBAR_EDIT = (By.XPATH, '//button[.//span[normalize-space(.)="修改"] or normalize-space(.)="修改"]')
    TOOLBAR_DELETE = (By.XPATH, '//button[.//span[normalize-space(.)="删除"] or normalize-space(.)="删除"]')
    TOOLBAR_LOG = (By.XPATH, '//button[.//span[normalize-space(.)="日志"] or normalize-space(.)="日志"]')

    DIALOG_PANEL = (
        By.XPATH,
        '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]',
    )
    DIALOG_CONFIRM = (
        By.XPATH,
        '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]//button[.//span[normalize-space(.)="确定"] or .//span[normalize-space(.)="保存"] or normalize-space(.)="确定" or normalize-space(.)="保存"]',
    )
    DIALOG_CANCEL = (
        By.XPATH,
        '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]//button[.//span[normalize-space(.),"取消"] or normalize-space(.),"取消"]',
    )

    # 可视化生成Cron弹窗
    CRON_VISUAL_DRAWER = (
        By.XPATH,
        '//div[contains(@class,"cron-generator-drawer") and not(contains(@style,"display: none"))]',
    )
    CRON_VISUAL_CONFIRM = (
        By.XPATH,
        '//div[contains(@class,"cron-generator-drawer")]//button//span[contains(text(),"确认使用")]/parent::button',
    )
    CRON_VISUAL_CANCEL = (
        By.XPATH,
        '//div[contains(@class,"cron-generator-drawer")]//button//span[contains(text(),"取消")]/parent::button',
    )
    CRON_VISUAL_CLOSE = (
        By.XPATH,
        '//div[contains(@class,"cron-generator-drawer")]//button//span[contains(text(),"取消")]/parent::button',
    )

    # 复用 BasePage 已有定位器：复用 BasePage.TOTAL_COUNT

    LOADING_MASK = (By.CSS_SELECTOR, ".el-loading-mask")
    EMPTY_TEXT = (By.XPATH, '//*[contains(@class,"el-table__empty-text")][not(ancestor::div[contains(@class,"el-dialog")])]')
    MAIN_TABLE_HEADER_WRAPPER = (
        By.XPATH,
        '(//div[contains(@class,"el-table__header-wrapper")][not(ancestor::div[contains(@class,"el-dialog")])])[1]',
    )
    MAIN_TABLE_BODY_WRAPPER = (
        By.XPATH,
        '(//div[contains(@class,"el-table__body-wrapper")][not(ancestor::div[contains(@class,"el-dialog")])])[1]',
    )
    PAGINATION = (By.CSS_SELECTOR, ".el-pagination")
    CURRENT_PAGE = (By.CSS_SELECTOR, ".el-pagination .el-pager li.active, .el-pagination .el-pager li.is-active")
    NEXT_PAGE = (By.CSS_SELECTOR, ".el-pagination button.btn-next:not([disabled])")

    TOAST_TEXT = (By.CSS_SELECTOR, ".el-message__content")
    TOAST_TEXT_FALLBACK = (By.CSS_SELECTOR, 'div[id^="message_"] p, div[id^="message_"] .el-message__content, div[id^="message_"]')

    # ══════════════════════════════════════════════════════════════════
    #  MESSAGEBOX 定位器
    # ══════════════════════════════════════════════════════════════════

    MESSAGEBOX_CONFIRM = (
        By.XPATH,
        '(//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))])[last()]//button[.//*[normalize-space(.)="确定"] or normalize-space(.)="确定"]',
    )
    MESSAGEBOX_TEXT = (
        By.XPATH,
        '(//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))])[last()]//*[contains(@class,"el-message-box__message") or contains(@class,"el-message-box__content")]',
    )

    def __init__(self, driver, timeout=None):
        """初始化 — 继承 BasePage"""
        super().__init__(driver, timeout)

    # ══════════════════════════════════════════════════════════════════
    #  导航
    # ══════════════════════════════════════════════════════════════════

    def navigate(self):
        """导航到定时任务页面 — 唯一入口"""
        logger.info("导航到 → 系统管理 → 日志管理 → 定时任务")
        self.navigate_to("系统管理", "日志管理", "定时任务")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        return self

    def navigate_to_timed_task(self):
        """导航到定时任务页面 (保留旧接口)"""
        logger.info("导航到 → 系统管理 → 日志管理 → 定时任务")
        self.navigate_to("系统管理", "日志管理", "定时任务")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()

    # ══════════════════════════════════════════════════════════════════
    #  内部工具方法
    # ══════════════════════════════════════════════════════════════════

    def _wait_settled(self, timeout=10):
        """等待 loading 遮罩消失 (使用 BasePage 的 _wait_loading_gone)"""
        self._wait_loading_gone(timeout=timeout)
        self.wait_vue_stable()

    def _first_displayed(self, locator, timeout=2):
        """查找第一个可见元素 — 委托 BasePage.find_visible"""
        return self.find_visible(locator, timeout=timeout)

    def wait_for_toast_text(self, timeout=6):
        """等待 Toast 消息出现并返回文本"""
        last = ""
        end = __import__('time').time() + timeout
        while __import__('time').time() < end:
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

    def _get_visible_dialog_footer_buttons(self):
        if not self.is_dialog_open():
            return []
        dlg = self._dialog()
        buttons = []
        try:
            candidates = dlg.find_elements(By.XPATH, './/div[contains(@class,"el-dialog__footer")]//button[not(@disabled)]')
            for b in candidates:
                try:
                    if b.is_displayed():
                        buttons.append(b)
                except Exception:
                    continue
        except Exception:
            pass
        return buttons

    def _clear_input(self, locator):
        el = self.wait.until(EC.presence_of_element_located(locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        return el

    def input_task_name(self, value):
        el = self._clear_input(self.TASK_NAME_INPUT)
        if value:
            el.send_keys(value)

    def _select_dropdown_option(self, select_locator, option_text):
        self._wait_settled(timeout=6)
        sel = self.wait.until(EC.presence_of_element_located(select_locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", sel)
        try:
            self.driver.execute_script("arguments[0].click();", sel)
        except Exception:
            try:
                sel.click()
            except Exception:
                self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles:true}));", sel)
        WebDriverWait(self.driver, 6).until(EC.presence_of_element_located(self.SELECT_DROPDOWN_PANEL))

        txt = option_text
        option_locators = [
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

        option = None
        for _ in range(2):
            for loc in option_locators:
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
                self.driver.execute_script("arguments[0].click();", sel)
            except Exception:
                pass
            self.wait_vue_stable()

        if not option:
            raise TimeoutException(f"未找到下拉选项：{option_text}")
        self.driver.execute_script("arguments[0].click();", option)
        self.wait_vue_stable()

    def select_task_type(self, text):
        self._select_dropdown_option(self.TASK_TYPE_SELECT, text)

    def select_status(self, text):
        mapping = {"全部": self.STATUS_ALL, "运行中": self.STATUS_RUNNING, "已暂停": self.STATUS_PAUSED}
        loc = mapping.get(text)
        if not loc:
            raise TimeoutException(f"未知状态: {text}")
        el = self.wait.until(EC.presence_of_element_located(loc))
        self.driver.execute_script("arguments[0].click();", el)
        self.wait_vue_stable()

    def click_search(self):
        self._wait_settled(timeout=6)
        btn = None
        try:
            btn = self._first_displayed(self.SEARCH_BUTTON, timeout=4)
        except Exception:
            raise TimeoutException("未找到搜索按钮")
        if not btn:
            raise TimeoutException("未找到搜索按钮")
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_settled(timeout=10)

    def click_reset(self):
        self._wait_settled(timeout=6)
        btn = None
        try:
            btn = self._first_displayed(self.RESET_BUTTON, timeout=4)
        except Exception:
            raise TimeoutException("未找到重置按钮")
        if not btn:
            raise TimeoutException("未找到重置按钮")
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_settled(timeout=10)

    def get_empty_text(self):
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
                self.wait_vue_stable()
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
        self._wait_settled(timeout=10)
        wrapper = self.driver.find_element(*self.MAIN_TABLE_BODY_WRAPPER)
        rows = wrapper.find_elements(By.XPATH, ".//table/tbody/tr")
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
        wrapper = self.driver.find_element(*self.MAIN_TABLE_HEADER_WRAPPER)
        ths = wrapper.find_elements(By.XPATH, ".//table//th")
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
        wrapper = self.driver.find_element(*self.MAIN_TABLE_BODY_WRAPPER)
        cell_xpath = f'.//tbody/tr/td[{col_index}]//div[contains(@class,"cell")]'
        cells = wrapper.find_elements(By.XPATH, cell_xpath)
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

    def _find_row_by_task_name(self, task_name):
        self._wait_settled(timeout=10)
        safe = (task_name or "").replace('"', '\\"')
        loc = (
            By.XPATH,
            f'(//div[contains(@class,"el-table__body-wrapper")]//tbody/tr[.//*[contains(@class,"cell") and contains(normalize-space(.),"{safe}")]])[1]',
        )
        return WebDriverWait(self.driver, 4).until(EC.presence_of_element_located(loc))

    def click_row_action(self, action_text, task_name=None, row_index=1):
        self._wait_settled(timeout=10)
        if task_name:
            row = self._find_row_by_task_name(task_name)
        else:
            row = WebDriverWait(self.driver, 4).until(
                EC.presence_of_element_located(
                    (By.XPATH, f'(//div[contains(@class,"el-table__body-wrapper")]//tbody/tr)[{int(row_index)}]'),
                )
            )
        act = (action_text or "").strip()
        btn_locators = [
            (By.XPATH, f'.//button[.//*[normalize-space(.)="{act}"] or normalize-space(.)="{act}"]'),
            (By.XPATH, f'.//*[self::a or self::span][normalize-space(.)="{act}"]/ancestor::button[1]'),
            (By.XPATH, f'.//*[normalize-space(.)="{act}"]'),
        ]
        btn = None
        for loc in btn_locators:
            try:
                cand = row.find_element(*loc)
                if cand:
                    btn = cand
                    break
            except Exception:
                continue
        if not btn:
            raise TimeoutException(f"未找到行内操作：{act}")
        self.driver.execute_script("arguments[0].click();", btn)
        self.wait_vue_stable()

    def click_toolbar_add(self):
        self._wait_settled(timeout=6)
        btn = None
        try:
            btn = self._first_displayed(self.TOOLBAR_ADD, timeout=6)
        except Exception:
            raise TimeoutException("未找到新增按钮")
        if not btn:
            raise TimeoutException("未找到新增按钮")
        try:
            self.driver.execute_script("arguments[0].click();", btn)
        except Exception:
            try:
                btn.click()
            except Exception:
                self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles:true}));", btn)
        WebDriverWait(self.driver, 6).until(EC.presence_of_element_located(self.DIALOG_PANEL))

    def click_toolbar_edit(self):
        self._wait_settled(timeout=6)
        btn = self._first_displayed(self.TOOLBAR_EDIT, timeout=6)
        self.driver.execute_script("arguments[0].click();", btn)
        WebDriverWait(self.driver, 6).until(EC.presence_of_element_located(self.DIALOG_PANEL))

    def click_toolbar_delete(self):
        self._wait_settled(timeout=6)
        btn = self._first_displayed(self.TOOLBAR_DELETE, timeout=6)
        self.driver.execute_script("arguments[0].click();", btn)
        self.wait_vue_stable()

    def confirm_message_box_if_present(self):
        try:
            btn = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(self.MESSAGEBOX_CONFIRM))
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_vue_stable()
            return True
        except Exception:
            return False

    def confirm_message_box_and_get_text(self):
        text = ""
        try:
            try:
                el = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located(self.MESSAGEBOX_TEXT))
                text = (el.text or "").strip()
            except Exception:
                text = ""
            btn = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located(self.MESSAGEBOX_CONFIRM))
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_vue_stable()
            return text
        except Exception:
            return text

    def _dialog(self):
        return self.wait.until(EC.presence_of_element_located(self.DIALOG_PANEL))

    def is_dialog_open(self):
        try:
            dialogs = self.driver.find_elements(*self.DIALOG_PANEL)
            for d in dialogs:
                try:
                    if d.is_displayed():
                        return True
                except Exception:
                    continue
            return False
        except Exception:
            return False

    def _dialog_find(self, by, selector):
        dlg = self._dialog()
        return dlg.find_element(by, selector)

    def dialog_input_by_label(self, label_text, value, skip_blur=False):
        dlg = self._dialog()
        safe = (label_text or "").replace('"', '\\"')
        locators = [
            (By.XPATH, f'.//label[contains(normalize-space(.),"{safe}")]/following::input[1]'),
            (By.XPATH, f'.//label[contains(normalize-space(.),"{safe}")]/following::textarea[1]'),
        ]
        el = None
        for loc in locators:
            try:
                el = dlg.find_element(*loc)
                break
            except Exception:
                continue
        if not el:
            raise TimeoutException(f"弹窗未找到输入框：{label_text}")
        try:
            el.send_keys(Keys.CONTROL + "a")
            el.send_keys(Keys.DELETE)
        except Exception:
            pass
        if value:
            el.send_keys(value)
        if not skip_blur:
            try:
                self.driver.execute_script(
                    "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
                    "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));"
                    "arguments[0].dispatchEvent(new Event('blur', {bubbles:true}));",
                    el,
                )
            except Exception:
                pass

    def close_cron_visual_drawer(self):
        """关闭可视化生成Cron弹窗"""
        # 方案1：直接定位到可视化弹窗的取消按钮
        try:
            drawer = self.driver.find_element(*self.CRON_VISUAL_DRAWER)
            if drawer.is_displayed():
                cancel_btn = drawer.find_element(By.XPATH, './/button[2]//span[contains(text(),"取消")]')
                if cancel_btn.is_displayed():
                    cancel_btn.click()
                    self.wait_vue_stable()
                    return
        except Exception:
            pass

        # 方案2：使用 CRON_VISUAL_CANCEL 定位器
        try:
            cancel_span = self.driver.find_element(*self.CRON_VISUAL_CANCEL)
            if cancel_span.is_displayed():
                parent_btn = cancel_span.find_element(By.XPATH, './parent::button')
                parent_btn.click()
                self.wait_vue_stable()
                return
        except Exception:
            pass

        # 方案3：在drawer内查找非primary按钮
        try:
            drawer = self.driver.find_element(*self.CRON_VISUAL_DRAWER)
            cancel_btn = drawer.find_element(By.XPATH, './/button[contains(@class,"el-button") and not(contains(@class,"primary"))]')
            if cancel_btn.is_displayed():
                cancel_btn.click()
                self.wait_vue_stable()
                return
        except Exception:
            pass

        # 方案4：按ESC关闭
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            self.wait_vue_stable()
        except Exception:
            pass

    def dialog_select_by_label(self, label_text, option_text):
        dlg = self._dialog()
        safe = (label_text or "").replace('"', '\\"')
        loc = (By.XPATH, f'.//label[contains(normalize-space(.),"{safe}")]/following::div[contains(@class,"el-select")][1]')
        sel = WebDriverWait(dlg, 4).until(EC.presence_of_element_located(loc))
        try:
            self.driver.execute_script("arguments[0].click();", sel)
        except Exception:
            try:
                sel.click()
            except Exception:
                self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles:true}));", sel)

        WebDriverWait(self.driver, 6).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    '(//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]'
                    ' | //div[contains(@class,"el-popper") and not(contains(@style,"display: none"))])[last()]',
                )
            )
        )

        txt = (option_text or "").strip()
        option_locators = [
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

        option = None
        for _ in range(2):
            for loc2 in option_locators:
                try:
                    cand = WebDriverWait(self.driver, 4).until(EC.presence_of_element_located(loc2))
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
                self.driver.execute_script("arguments[0].click();", sel)
            except Exception:
                pass
            self.wait_vue_stable()

        if not option:
            options = []
            try:
                els = self.driver.find_elements(
                    By.XPATH,
                    '(//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))])[last()]//li[not(contains(@class,"is-disabled"))]',
                )
                for e in els:
                    t = (e.text or "").strip().replace("\n", " ").strip()
                    if t:
                        options.append(t)
            except Exception:
                pass
            raise TimeoutException(f"弹窗下拉未找到选项: {option_text}，可选项={options or '[]'}")

        self.driver.execute_script("arguments[0].click();", option)
        self.wait_vue_stable()

    def dialog_get_select_text_by_label(self, label_text):
        if not self.is_dialog_open():
            return ""
        dlg = self._dialog()
        safe = (label_text or "").replace('"', '\\"')
        loc = (By.XPATH, f'.//label[contains(normalize-space(.),"{safe}")]/following::div[contains(@class,"el-select")][1]')
        sel = WebDriverWait(dlg, 4).until(EC.presence_of_element_located(loc))
        candidates = [
            ".//*[contains(@class,'el-select__selected-item')]//span",
            ".//*[contains(@class,'el-select__selection')]//span",
            ".//*[contains(@class,'el-select__placeholder')]//span",
            ".//span",
        ]
        texts = []
        for xp in candidates:
            try:
                for el in sel.find_elements(By.XPATH, xp):
                    try:
                        t = (el.text or "").strip()
                        if t and t not in texts:
                            texts.append(t)
                    except Exception:
                        continue
            except Exception:
                continue
        return texts[0] if texts else ""

    def dialog_click_radio(self, radio_text):
        dlg = self._dialog()
        safe = (radio_text or "").replace('"', '\\"')
        locators = [
            (By.XPATH, f'.//label[contains(@class,"el-radio")][.//span[normalize-space(.)="{safe}"]]'),
            (By.XPATH, f'.//*[normalize-space(.)="{safe}"]/ancestor::label[contains(@class,"el-radio")][1]'),
        ]
        btn = None
        for loc in locators:
            try:
                btn = dlg.find_element(*loc)
                break
            except Exception:
                continue
        if not btn:
            raise TimeoutException(f"弹窗未找到单选：{radio_text}")
        self.driver.execute_script("arguments[0].click();", btn)
        self.wait_vue_stable()

    def get_dialog_error_texts(self):
        if not self.is_dialog_open():
            return []
        dlg = self._dialog()
        els = dlg.find_elements(By.CSS_SELECTOR, ".el-form-item__error")
        texts = []
        for e in els:
            try:
                t = (e.text or "").strip()
                if t:
                    texts.append(t)
            except Exception:
                continue
        return texts

    def dialog_confirm(self):
        if not self.is_dialog_open():
            return ""

        msgbox_text = ""
        toast_text = ""

        dlg = self._dialog()
        candidates = [
            (By.XPATH, './/button[contains(@class,"el-button--primary") and not(@disabled)]'),
            (
                By.XPATH,
                './/button[not(@disabled) and (.//span[normalize-space(.)="确定"] or .//span[normalize-space(.)="保存"] or .//span[normalize-space(.)="提交"] or .//span[normalize-space(.)="确认"] or normalize-space(.)="确定" or normalize-space(.)="保存" or normalize-space(.)="提交" or normalize-space(.)="确认")]',
            ),
            (By.XPATH, './/div[contains(@class,"el-dialog__footer")]//button[not(@disabled)][1]'),
            (By.XPATH, './/div[contains(@class,"el-dialog__footer")]//button[not(@disabled)][last()]'),
        ]

        def _try_click(el):
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            except Exception:
                pass
            for _ in range(2):
                try:
                    self.driver.execute_script("arguments[0].click();", el)
                    return True
                except Exception:
                    try:
                        el.click()
                        return True
                    except Exception:
                        self.wait_vue_stable()
            return False

        def _wait_after_submit():
            nonlocal msgbox_text, toast_text
            msgbox_text = self.confirm_message_box_and_get_text() or msgbox_text
            toast_text = self.wait_for_toast_text(timeout=2) or toast_text
            try:
                WebDriverWait(self.driver, 6).until(lambda d: not self.is_dialog_open())
                return True
            except Exception:
                return False

        clicked = False
        for loc in candidates:
            try:
                els = dlg.find_elements(*loc)
                els = [e for e in els if e.is_displayed()]
                if not els:
                    continue
                btn = els[0]
                clicked = _try_click(btn) or clicked
                if _wait_after_submit():
                    self._wait_settled(timeout=12)
                    return (toast_text or msgbox_text or "").strip()
            except Exception:
                continue

        if clicked:
            _wait_after_submit()
            self._wait_settled(timeout=12)
            return (toast_text or msgbox_text or "").strip()

        raise TimeoutException("弹窗未找到可点击的确定/保存按钮")

    def dialog_cancel(self):
        dlg = self._dialog()
        candidates = [
            (
                By.XPATH,
                './/button[not(@disabled) and (.//span[normalize-space(.)="取消"] or normalize-space(.)="取消")]',
            ),
            (
                By.XPATH,
                './/button[not(@disabled) and (.//span[normalize-space(.)="关闭"] or normalize-space(.)="关闭")]',
            ),
            (By.XPATH, './/div[contains(@class,"el-dialog__footer")]//button[not(@disabled)][1]'),
            (By.CSS_SELECTOR, ".el-dialog__headerbtn"),
            (By.CSS_SELECTOR, ".el-dialog__headerbtn .el-dialog__close"),
        ]
        btn = None
        for loc in candidates:
            try:
                els = dlg.find_elements(*loc)
                els = [e for e in els if e.is_displayed()]
                if els:
                    btn = els[0]
                    break
            except Exception:
                continue
        if not btn:
            try:
                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                self.wait_vue_stable()
                return
            except Exception:
                raise TimeoutException("弹窗未找到取消/关闭按钮")
        try:
            self.driver.execute_script("arguments[0].click();", btn)
        except Exception:
            try:
                btn.click()
            except Exception:
                self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles:true}));", btn)
        self.wait_vue_stable()
