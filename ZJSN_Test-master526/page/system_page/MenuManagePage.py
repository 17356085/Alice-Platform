"""菜单管理页面 Page Object — 重构版

变更记录:
  2026-06-11: 继承 BasePage，去绝对 XPath，去 time.sleep → BasePage 等待方法
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


class MenuManagePage(BasePage):
    """菜单管理页面操作 — 继承 BasePage"""

    # ══════════════════════════════════════════════════════════════════
    #  页面专属定位器（CSS优先 → 相对XPath → 文本匹配）
    # ══════════════════════════════════════════════════════════════════

    MENU_NAME_INPUT = (By.XPATH, '//input[contains(@placeholder, "请输入菜单名称")]')
    SEARCH_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="搜索" or normalize-space(.)="查询"]]')
    RESET_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="重置"]]')

    TABLE_HEADERS = (By.XPATH, '//div[contains(@class,"el-table__header-wrapper")]//th//div')
    TABLE_ROWS = (By.XPATH, '//div[contains(@class,"el-table__body-wrapper")]//table/tbody/tr')
    FIRST_ROW_NAME = (By.XPATH, '(//div[contains(@class,"el-table__body-wrapper")]//table/tbody/tr[1]/td[1]//div[contains(@class,"cell")])[1]')

    TAB_PC_MENU = (By.XPATH, '//span[contains(@class,"el-radio-button__inner") and normalize-space(.)="PC端菜单"]/ancestor::label[1]')
    TAB_MINIAPP_MENU = (By.XPATH, '//span[contains(@class,"el-radio-button__inner") and normalize-space(.)="小程序菜单"]/ancestor::label[1]')

    # 复用 BasePage 已有定位器：BasePage.LOADING_MASK / BasePage.TABLE_EMPTY / BasePage.TOAST
    LOADING_MASK = (By.CSS_SELECTOR, ".el-loading-mask")

    TOOLBAR_ADD = (By.XPATH, '//button[.//span[normalize-space(.)="新增"]]')
    TOOLBAR_EXPAND_ALL = (By.XPATH, '//button[.//span[normalize-space(.)="展开全部"]]')
    TOOLBAR_COLLAPSE_ALL = (By.XPATH, '//button[.//span[normalize-space(.)="收起全部"]]')

    DIALOG_MENU_NAME_INPUT = (By.XPATH, '(//div[contains(@class,"el-dialog")])[last()]//input[@placeholder="请输入菜单名称"]')
    DIALOG_MENU_TYPE_RADIO = (By.XPATH, '(//div[contains(@class,"el-dialog")])[last()]//label[contains(@class,"el-radio")]')
    DIALOG_CONFIRM = (By.XPATH, '(//div[contains(@class,"el-dialog")])[last()]//button[.//span[normalize-space(.)="确定"]]')
    DIALOG_CANCEL = (By.XPATH, '(//div[contains(@class,"el-dialog")])[last()]//button[.//span[normalize-space(.)="取消"]]')
    DIALOG_CONFIRM_FALLBACKS = [
        (By.XPATH, '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[contains(@class,"el-dialog")])[last()]//footer//button[.//span[normalize-space(.)="确定"]]'),
        (By.XPATH, '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]//footer//button[.//span[normalize-space(.)="确定"]]'),
        (By.XPATH, '(//footer[contains(@class,"el-dialog__footer")]//button[.//span[normalize-space(.)="确定"]])[last()]'),
        (By.XPATH, '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[contains(@class,"el-button--primary") and .//span[normalize-space(.)="确定"]])[last()]'),
    ]
    DIALOG_CANCEL_FALLBACKS = [
        (By.XPATH, '(//footer[contains(@class,"el-dialog__footer")]//button[.//span[normalize-space(.)="取消"]])[last()]'),
    ]
    MESSAGEBOX_CONFIRM = (By.XPATH, '(//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))])[last()]//button[.//span[normalize-space(.)="确定"]]')

    def __init__(self, driver, timeout=None):
        """初始化 — 继承 BasePage"""
        super().__init__(driver, timeout)

    def navigate(self):
        """导航到菜单管理页面 — 唯一入口"""
        logger.info("导航到 → 系统管理 → 菜单管理")
        self.navigate_to("系统管理", "菜单管理")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        return self

    def _get_form_item(self, label_text):
        """Find a VISIBLE form item by label text. Falls back to any presence if none visible."""
        xpath = (
            f'//div[contains(@class,"el-form-item")]'
            f'[.//label[contains(@class,"el-form-item__label") and contains(normalize-space(.), "{label_text}")]]'
        )
        items = self.driver.find_elements(By.XPATH, xpath)
        for item in items:
            try:
                if item.is_displayed():
                    return item
            except Exception:
                continue
        # Fallback to any (first) matching item
        return self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

    def input_menu_name(self, name):
        el = self.wait.until(EC.visibility_of_element_located(self.MENU_NAME_INPUT))
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        if name:
            el.send_keys(name)

    def _wait_table_settled(self, timeout=5):
        """等待表格 loading 遮罩消失（委托 BasePage._wait_loading_gone）"""
        self._wait_loading_gone(timeout=timeout)

    def get_empty_text(self):
        self._wait_table_settled()
        try:
            el = self.driver.find_element(*self.EMPTY_TEXT)
            return (el.text or "").strip()
        except Exception:
            return ""

    def _get_dialog_form_item(self, label_text):
        xpath = (
            f'(//div[contains(@class,"el-dialog")])[last()]'
            f'//div[contains(@class,"el-form-item")]'
            f'[.//label[contains(@class,"el-form-item__label") and contains(normalize-space(.), "{label_text}")]]'
        )
        return self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

    def _get_visible_dialog(self, timeout=8):
        locator = (
            By.XPATH,
            '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[contains(@class,"el-dialog")]'
            ' | //div[contains(@class,"el-dialog__wrapper") and not(contains(@style,"display: none"))]//div[contains(@class,"el-dialog")])[last()]',
        )
        return WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(locator))

    def click_toolbar_add(self):
        candidates = [self.TOOLBAR_ADD]
        last_exc = None
        for loc in candidates:
            try:
                btn = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(loc))
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(self.DIALOG_MENU_NAME_INPUT))
                    self.wait_vue_stable()
                    return
            except Exception as e:
                last_exc = e
                continue
        raise last_exc if last_exc else TimeoutException("未找到新增按钮")

    def click_expand_all(self):
        candidates = [self.TOOLBAR_EXPAND_ALL]
        last_exc = None
        for loc in candidates:
            try:
                btn = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(loc))
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    self._wait_table_settled()
                    self.wait_vue_stable()
                    return
            except Exception as e:
                last_exc = e
                continue
        raise last_exc if last_exc else TimeoutException("未找到展开全部按钮")

    def click_collapse_all(self):
        candidates = [self.TOOLBAR_COLLAPSE_ALL]
        last_exc = None
        for loc in candidates:
            try:
                btn = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(loc))
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    self._wait_table_settled()
                    self.wait_vue_stable()
                    return
            except Exception as e:
                last_exc = e
                continue
        raise last_exc if last_exc else TimeoutException("未找到收起全部按钮")

    def select_dialog_menu_type(self, type_text):
        radios = self.driver.find_elements(*self.DIALOG_MENU_TYPE_RADIO)
        for r in radios:
            try:
                if type_text in (r.text or ""):
                    self.driver.execute_script("arguments[0].click();", r)
                    self.wait_vue_stable()
                    return
            except Exception:
                continue
        radio = self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, f'(//div[contains(@class,"el-dialog")])[last()]//label[contains(@class,"el-radio")][.//*[normalize-space(.)="{type_text}"]]')
            )
        )
        self.driver.execute_script("arguments[0].click();", radio)
        self.wait_vue_stable()

    def input_dialog_menu_name(self, name):
        el = self.wait.until(EC.visibility_of_element_located(self.DIALOG_MENU_NAME_INPUT))
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        if name:
            el.send_keys(name)

    def input_dialog_field(self, label_text, value):
        item = self._get_dialog_form_item(label_text)
        el = item.find_element(By.XPATH, './/input|.//textarea')
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        if value is not None and value != "":
            el.send_keys(str(value))

    def try_input_dialog_field(self, label_text, value):
        xpath = (
            f'(//div[contains(@class,"el-dialog")])[last()]'
            f'//div[contains(@class,"el-form-item")]'
            f'[.//label[contains(@class,"el-form-item__label") and contains(normalize-space(.), "{label_text}")]]'
        )
        items = self.driver.find_elements(By.XPATH, xpath)
        if not items:
            return False
        try:
            el = items[0].find_element(By.XPATH, './/input|.//textarea')
            el.send_keys(Keys.CONTROL + "a")
            el.send_keys(Keys.DELETE)
            if value is not None and value != "":
                el.send_keys(str(value))
            return True
        except Exception:
            return False

    def dialog_has_form_item(self, label_text):
        """判断当前弹窗是否存在指定表单项。"""
        try:
            dialog = self._get_visible_dialog(timeout=3)
            items = dialog.find_elements(
                By.XPATH,
                f'.//div[contains(@class,"el-form-item")]'
                f'[.//label[contains(@class,"el-form-item__label") and contains(normalize-space(.), "{label_text}")]]',
            )
            return any(item.is_displayed() for item in items)
        except Exception:
            return False

    def input_dialog_permission(self, value):
        self.input_dialog_field("权限标识", value)

    def input_dialog_sort(self, value):
        self.input_dialog_field("菜单排序", value)

    def input_dialog_icon(self, value):
        self.input_dialog_field("菜单图标", value)

    def input_dialog_path(self, value):
        self.input_dialog_field("路由地址", value)

    def input_dialog_component_path(self, value):
        self.input_dialog_field("组件路径", value)

    def select_dialog_visible(self, text):
        self._select_radio_in_dialog(["是否可见", "可见性", "是否显示", "显示状态"], text)

    def select_dialog_cache(self, text):
        self._select_radio_in_dialog(["是否缓存", "缓存"], text)

    def select_dialog_status(self, text):
        self._select_radio_in_dialog(["菜单状态", "状态"], text)

    def _select_radio_in_dialog(self, label_candidates, option_text):
        dialog = self._get_visible_dialog(timeout=8)

        for label_text in label_candidates:
            items = dialog.find_elements(
                By.XPATH,
                f'.//div[contains(@class,"el-form-item")]'
                f'[.//label[contains(@class,"el-form-item__label") and contains(normalize-space(.), "{label_text}")]]',
            )
            for item in items:
                try:
                    labels = item.find_elements(
                        By.XPATH,
                        f'.//label[(contains(@class,"el-radio") or contains(@class,"el-radio-button"))][.//*[normalize-space(.)="{option_text}"]]',
                    )
                    for lb in labels:
                        try:
                            if not lb.is_displayed():
                                continue
                            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", lb)
                            self.wait_vue_stable()
                            self.driver.execute_script("arguments[0].click();", lb)
                            try:
                                WebDriverWait(self.driver, 2).until(
                                    lambda d: "is-checked" in (lb.get_attribute("class") or "")
                                    or lb.find_elements(By.XPATH, './/input[@checked or @aria-checked="true"]')
                                )
                            except Exception:
                                pass
                            self.wait_vue_stable()
                            return
                        except Exception:
                            continue
                except Exception:
                    continue

        global_candidates = dialog.find_elements(
            By.XPATH,
            f'.//label[(contains(@class,"el-radio") or contains(@class,"el-radio-button"))][.//*[normalize-space(.)="{option_text}"]]',
        )
        visible_global = []
        for el in global_candidates:
            try:
                if el.is_displayed():
                    visible_global.append(el)
            except Exception:
                continue

        preferred = None
        if len(visible_global) > 1:
            for el in visible_global:
                try:
                    item = el.find_element(By.XPATH, 'ancestor::div[contains(@class,"el-form-item")][1]')
                    label_el = item.find_element(By.XPATH, './/label[contains(@class,"el-form-item__label")]')
                    t = (label_el.text or "").strip()
                    if any(x in t for x in label_candidates):
                        preferred = el
                        break
                except Exception:
                    continue
        elif len(visible_global) == 1:
            preferred = visible_global[0]

        if preferred is not None:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", preferred)
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", preferred)
            self.wait_vue_stable()
            return

        label_texts = []
        for lb in dialog.find_elements(By.XPATH, './/label[contains(@class,"el-form-item__label")]'):
            try:
                t = (lb.text or "").strip()
                if t:
                    label_texts.append(t)
            except Exception:
                continue
        raise TimeoutException(f"弹窗中未找到单选项：{option_text}，表单项={label_texts or '[]'}")

    def click_dialog_confirm(self):
        locators = [self.DIALOG_CONFIRM] + list(self.DIALOG_CONFIRM_FALLBACKS)
        last_exc = None
        for loc in locators:
            try:
                el = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(loc))
                btn = el
                if el.tag_name.lower() != "button":
                    try:
                        btn = el.find_element(By.XPATH, "./ancestor::button[1]")
                    except Exception:
                        btn = el
                if btn.is_displayed():
                    disabled = btn.get_attribute("disabled") is not None or "is-disabled" in (btn.get_attribute("class") or "")
                    if disabled:
                        continue
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", btn)
                    self.wait_vue_stable()
                    self.driver.execute_script("arguments[0].click();", btn)
                    self._wait_loading_gone(timeout=5)
                    self.wait_vue_stable()
                    return
            except Exception as e:
                last_exc = e
                continue
        raise last_exc if last_exc else TimeoutException("未找到弹窗确定按钮")

    def click_dialog_cancel(self):
        locators = [self.DIALOG_CANCEL] + list(self.DIALOG_CANCEL_FALLBACKS)
        last_exc = None
        for loc in locators:
            try:
                btn = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(loc))
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_vue_stable()
                    return
            except Exception as e:
                last_exc = e
                continue
        raise last_exc if last_exc else TimeoutException("未找到弹窗取消按钮")

    def confirm_message_box(self):
        btn = self.wait.until(EC.presence_of_element_located(self.MESSAGEBOX_CONFIRM))
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_loading_gone(timeout=5)
        self.wait_vue_stable()

    def click_row_action(self, menu_name, action_text):
        row_xpath_candidates = [
            f'//tr[contains(@class,"el-table__row")][.//td[1]//*[contains(normalize-space(.),"{menu_name}")]]',
            f'//tr[contains(@class,"el-table__row")][contains(normalize-space(.),"{menu_name}")]',
        ]
        for row_xpath in row_xpath_candidates:
            btn_xpath_candidates = [
                f'{row_xpath}//td[last()]//*[self::button or self::a or self::span][normalize-space(.)="{action_text}"]/ancestor::button[1]',
                f'{row_xpath}//td[last()]//*[normalize-space(.)="{action_text}"]',
            ]
            for xp in btn_xpath_candidates:
                try:
                    el = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.XPATH, xp)))
                    if el.is_displayed():
                        self.driver.execute_script("arguments[0].click();", el)
                        self._wait_loading_gone(timeout=5)
                        self.wait_vue_stable()
                        return
                except Exception:
                    continue
        raise TimeoutException(f"未找到菜单'{menu_name}'的操作按钮: {action_text}")

    def click_first_row_edit(self):
        """点击第一行编辑按钮（基于文本匹配定位）"""
        try:
            row = self.wait.until(EC.presence_of_element_located(
                (By.XPATH, '//tr[contains(@class,"el-table__row")][1]')
            ))
            btn_xpaths = [
                './/button[.//span[normalize-space(.)="编辑"]]',
                './/button[contains(@class,"el-button")][.//*[normalize-space(.)="编辑"]]',
                './/td[last()]//button[1]',  # 备用
            ]
            for xp in btn_xpaths:
                try:
                    btn = row.find_element(By.XPATH, xp)
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self._wait_loading_gone(timeout=5)
                        self.wait_vue_stable()
                        return
                except Exception:
                    continue
            raise TimeoutException("第一行未找到编辑按钮")
        except Exception as e:
            logger.error("点击第一行编辑按钮失败: %s", e)
            raise

    def click_first_row_delete(self):
        """点击第一行删除按钮（基于文本匹配定位）"""
        try:
            row = self.wait.until(EC.presence_of_element_located(
                (By.XPATH, '//tr[contains(@class,"el-table__row")][1]')
            ))
            btn_xpaths = [
                './/button[.//span[normalize-space(.)="删除"]]',
                './/button[contains(@class,"el-button")][.//*[normalize-space(.)="删除"]]',
                './/td[last()]//button[2]',  # 备用
            ]
            for xp in btn_xpaths:
                try:
                    btn = row.find_element(By.XPATH, xp)
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self._wait_loading_gone(timeout=5)
                        self.wait_vue_stable()
                        return
                except Exception:
                    continue
            raise TimeoutException("第一行未找到删除按钮")
        except Exception as e:
            logger.error("点击第一行删除按钮失败: %s", e)
            raise

    def click_search(self):
        self._wait_table_settled()
        try:
            btn = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(self.SEARCH_BUTTON))
            if btn.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                self.wait_vue_stable()
                self.driver.execute_script("arguments[0].click();", btn)
                self._wait_table_settled()
                self.wait_vue_stable()
                return
        except Exception as e:
            logger.error("搜索按钮点击失败: %s", e)
            raise TimeoutException("无法点击搜索按钮")

    def click_reset(self):
        self._wait_table_settled()
        try:
            btn = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(self.RESET_BUTTON))
            if btn.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                self.wait_vue_stable()
                self.driver.execute_script("arguments[0].click();", btn)
                self._wait_table_settled()
                self.wait_vue_stable()
                return
        except Exception as e:
            logger.error("重置按钮点击失败: %s", e)
            raise TimeoutException("无法点击重置按钮")

    def click_tab_pc_menu(self):
        """切换到「PC端菜单」Tab（el-radio-button）

        多策略定位 + 切换后验证 is-active 状态。
        失败时抛出明确异常，不再静默返回 False。
        """
        locators = [
            self.TAB_PC_MENU,
            # Fallback: 按文本找 el-radio-button 的 label
            (By.XPATH,
             '//label[contains(@class,"el-radio-button")]'
             '//span[contains(@class,"el-radio-button__inner") and contains(normalize-space(.),"PC端")]'
             '/..'),
            # Fallback: 所有 el-radio-button label 中第一个含 "PC" 的
            (By.XPATH,
             '//label[contains(@class,"el-radio-button")]'
             '[.//span[contains(normalize-space(.),"PC")]]'),
        ]
        last_error = None
        for loc in locators:
            try:
                el = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(loc)
                )
                self.driver.execute_script("arguments[0].click();", el)
                self.wait_vue_stable()
                self._wait_table_settled()
                # 验证切换是否生效
                if self._is_tab_active("PC端"):
                    logger.info("已切换到PC端菜单Tab")
                    return True
            except TimeoutException as e:
                last_error = e
                continue
        raise TimeoutException(
            f"无法切换到「PC端菜单」Tab（已尝试 {len(locators)} 种定位策略）: {last_error}"
        )

    def click_tab_miniapp_menu(self):
        """切换到「小程序菜单」Tab（el-radio-button）

        多策略定位 + 切换后验证 is-active 状态。
        失败时抛出明确异常，不再静默返回 False。
        """
        locators = [
            self.TAB_MINIAPP_MENU,
            # Fallback: 按文本找 el-radio-button 的 label
            (By.XPATH,
             '//label[contains(@class,"el-radio-button")]'
             '//span[contains(@class,"el-radio-button__inner") and contains(normalize-space(.),"小程序")]'
             '/..'),
            # Fallback: 所有 el-radio-button label 中第一个含 "小程序" 的
            (By.XPATH,
             '//label[contains(@class,"el-radio-button")]'
             '[.//span[contains(normalize-space(.),"小程序")]]'),
        ]
        last_error = None
        for loc in locators:
            try:
                el = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(loc)
                )
                self.driver.execute_script("arguments[0].click();", el)
                self.wait_vue_stable()
                self._wait_table_settled()
                # 验证切换是否生效
                if self._is_tab_active("小程序"):
                    logger.info("已切换到小程序菜单Tab")
                    return True
            except TimeoutException as e:
                last_error = e
                continue
        raise TimeoutException(
            f"无法切换到「小程序菜单」Tab（已尝试 {len(locators)} 种定位策略）: {last_error}"
        )

    def _is_tab_active(self, keyword):
        """验证包含 keyword 的 Tab 是否处于激活状态"""
        try:
            active_labels = self.driver.find_elements(
                By.XPATH,
                f'//label[contains(@class,"el-radio-button") and contains(@class,"is-active")]'
                f'//span[contains(@class,"el-radio-button__inner") and contains(normalize-space(.),"{keyword}")]'
            )
            return len(active_labels) > 0
        except Exception:
            return False

    def select_type(self, type_text):
        """选择类型（目录/菜单/按钮）"""
        item = self._get_form_item("类型")
        click_candidates = []
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

        opened = False
        for cand in click_candidates:
            try:
                self.driver.execute_script("arguments[0].click();", cand)
                WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '(//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))])[last()]')
                    )
                )
                opened = True
                break
            except Exception:
                continue

        if not opened:
            raise TimeoutException("类型下拉未成功打开")

        option_locators = [
            (
                By.XPATH,
                f'(//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))])[last()]'
                f'//li[not(contains(@class,"is-disabled"))]//*[normalize-space(.)="{type_text}"]/ancestor::li[1]',
            ),
            (
                By.XPATH,
                f'(//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))])[last()]'
                f'//*[self::span or self::div][normalize-space(.)="{type_text}"]',
            ),
            (By.XPATH, f'//*[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]//*[normalize-space(.)="{type_text}"]'),
        ]

        last_error = None
        for loc in option_locators:
            try:
                option = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(loc))
                self.driver.execute_script("arguments[0].click();", option)
                self.wait_vue_stable()
                return
            except Exception as e:
                last_error = e
                continue

        # Final fallback: use JS to set the select value synchronously (no setTimeout)
        try:
            result = self.driver.execute_script("""
                var typeText = arguments[0];
                var selects = document.querySelectorAll('.el-select');
                for (var s of selects) {
                    var item = s.closest('.el-form-item');
                    if (item && item.querySelector('.el-form-item__label') &&
                        item.querySelector('.el-form-item__label').textContent.indexOf('类型') >= 0) {
                        // Click the trigger to open dropdown
                        var wrapper = s.querySelector('.el-select__wrapper');
                        if (!wrapper) wrapper = s;
                        wrapper.click();
                        return 'clicked';
                    }
                }
                return 'not_found';
            """, type_text)
            if result == 'not_found':
                raise TimeoutException(f"未找到类型下拉框")
            # Wait for dropdown to appear synchronously
            _time.sleep(0.5)
            # Click the option synchronously
            clicked = self.driver.execute_script("""
                var typeText = arguments[0];
                var items = document.querySelectorAll('.el-select-dropdown__item:not(.is-disabled)');
                for (var i = 0; i < items.length; i++) {
                    if ((items[i].textContent || '').trim().indexOf(typeText) >= 0) {
                        items[i].click();
                        return true;
                    }
                }
                // Try li items
                var lis = document.querySelectorAll('.el-select-dropdown li:not(.is-disabled)');
                for (var j = 0; j < lis.length; j++) {
                    if ((lis[j].textContent || '').trim().indexOf(typeText) >= 0) {
                        lis[j].click();
                        return true;
                    }
                }
                return false;
            """, type_text)
            if not clicked:
                raise TimeoutException(f"类型下拉选项未找到: {type_text}")
            self._wait_loading_gone(timeout=5)
            self.wait_vue_stable()
            # Verify selection was applied
            current_val = self.driver.execute_script("""
                var selects = document.querySelectorAll('.el-select');
                for (var s of selects) {
                    var item = s.closest('.el-form-item');
                    if (item && item.querySelector('.el-form-item__label') &&
                        item.querySelector('.el-form-item__label').textContent.indexOf('类型') >= 0) {
                        var sel = s.querySelector('.el-select__selected-item');
                        if (sel) return sel.textContent.trim();
                        var input = s.querySelector('input');
                        if (input && input.value) return input.value;
                        var placeholder = s.querySelector('.el-select__placeholder');
                        if (!placeholder || !placeholder.offsetParent || placeholder.offsetParent === null) {
                            // placeholder hidden = value selected, check inner input
                            var inner = s.querySelector('.el-select__input');
                            if (inner) return inner.value || inner.getAttribute('value') || '';
                        }
                        return placeholder ? placeholder.textContent.trim() : '';
                    }
                }
                return '';
            """)
            logger.info("select_type('%s') applied, current: '%s'", type_text, current_val)
            return
        except Exception as e:
            raise TimeoutException(f"类型下拉未找到选项: {type_text} (last={last_error}, fallback={e})")

        self.wait_vue_stable()

    def select_visibility(self, text):
        """选择可见性（全部/显示/隐藏）"""
        self._select_radio_or_select_in_form("可见性", text)

    def select_status(self, text):
        """选择状态（全部/启用/禁用）"""
        self._select_radio_or_select_in_form("状态", text)

    def _select_radio_or_select_in_form(self, form_label, option_text):
        try:
            self._select_radio_in_form(form_label, option_text)
            return
        except Exception:
            pass
        self._select_select_in_form(form_label, option_text)

    def _select_select_in_form(self, form_label, option_text):
        item = self._get_form_item(form_label)
        select = None
        select_xpaths = [
            './/div[contains(@class,"el-select")]',
            './/div[contains(@class,"el-select__wrapper")]',
            './/div[contains(@class,"el-input") and .//i[contains(@class,"arrow") or contains(@class,"caret")]]',
        ]
        for xp in select_xpaths:
            try:
                select = item.find_element(By.XPATH, xp)
                if select and select.is_displayed():
                    break
            except Exception:
                continue

        if not select:
            raise TimeoutException(f'未找到筛选项"{form_label}"的下拉框')

        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select)
        self.wait_vue_stable()
        try:
            trigger = select.find_element(
                By.XPATH,
                './/*[contains(@class,"el-select__wrapper") or contains(@class,"el-input__wrapper") or contains(@class,"el-select__selection") or contains(@class,"el-select__selected-item")][1]',
            )
            self.driver.execute_script("arguments[0].click();", trigger)
        except Exception:
            self.driver.execute_script("arguments[0].click();", select)

        option_locators = [
            (
                By.XPATH,
                f'(//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))])[last()]'
                f'//li[not(contains(@class,"is-disabled"))][.//*[normalize-space(.)="{option_text}"]]',
            ),
            (
                By.XPATH,
                f'(//div[contains(@class,"el-popper") and not(contains(@style,"display: none")) and .//*[normalize-space(.)="{option_text}"]])[last()]'
                f'//li[not(contains(@class,"is-disabled"))][.//*[normalize-space(.)="{option_text}"]]',
            ),
        ]
        last_exc = None
        for loc in option_locators:
            try:
                opt = WebDriverWait(self.driver, 6).until(EC.element_to_be_clickable(loc))
                self.driver.execute_script("arguments[0].click();", opt)
                self.wait_vue_stable()
                return
            except Exception as e:
                last_exc = e
                continue
        raise TimeoutException(str(last_exc) if last_exc else f"未找到下拉选项：{option_text}")

    def _select_radio_in_form(self, form_label, option_text):
        item = self._get_form_item(form_label)
        candidates = [
            f'.//label[contains(@class,"el-radio")][.//span[contains(@class,"el-radio__label") and normalize-space(.)="{option_text}"]]',
            f'.//label[contains(@class,"el-radio-button")][.//span[contains(@class,"el-radio-button__inner") and normalize-space(.)="{option_text}"]]',
            f'.//label[(contains(@class,"el-radio") or contains(@class,"el-radio-button"))][.//*[normalize-space(.)="{option_text}"]]',
        ]

        last_exc = None
        for xp in candidates:
            try:
                radio_label = item.find_element(By.XPATH, xp)
                self.driver.execute_script("arguments[0].click();", radio_label)
                try:
                    WebDriverWait(self.driver, 2).until(
                        lambda d: "is-active" in (radio_label.get_attribute("class") or "")
                        or "is-checked" in (radio_label.get_attribute("class") or "")
                    )
                except Exception:
                    try:
                        inner = radio_label.find_element(By.XPATH, './/*[contains(@class,"__inner")]')
                        self.driver.execute_script("arguments[0].click();", inner)
                        WebDriverWait(self.driver, 2).until(
                            lambda d: "is-active" in (radio_label.get_attribute("class") or "")
                            or "is-checked" in (radio_label.get_attribute("class") or "")
                        )
                    except Exception:
                        pass
                self.wait_vue_stable()
                return
            except Exception as e:
                last_exc = e
                continue

        raise last_exc

    def get_table_headers(self):
        """JS提取表格表头（含重试，应对Element Plus异步渲染）"""
        for attempt in range(6):
            try:
                self._wait_table_settled()
            except Exception:
                pass
            self.wait_vue_stable()
            headers = self.driver.execute_script("""
                return Array.from(
                    document.querySelectorAll('.el-table__header-wrapper th .cell')
                ).map(function(el) { return el.textContent.trim(); }).filter(Boolean);
            """)
            if headers and len(headers) >= 3:
                return headers
            self.wait_vue_stable()
        return []

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

    def get_table_row_count(self):
        self._wait_table_settled()
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        count = 0
        for r in rows:
            try:
                if r.is_displayed():
                    count += 1
            except Exception:
                continue
        return count

    def get_column_data(self, col_index):
        self._wait_table_settled()
        cell_xpath = f'//div[contains(@class,"el-table__body-wrapper")]//tbody/tr/td[{col_index}]//div[contains(@class,"cell")]'
        last_exc = None
        for _ in range(3):
            try:
                cells = self.driver.find_elements(By.XPATH, cell_xpath)
                values = []
                for c in cells:
                    t = (c.text or "").strip().replace("\n", " ").strip()
                    if t:
                        values.append(t)
                return values
            except Exception as e:
                last_exc = e
                self.wait_vue_stable()
                continue
        if last_exc:
            raise last_exc
        return []

    def get_first_row_name(self):
        names = self.get_column_data_by_header("菜单名称")
        if names:
            return names[0]
        try:
            return self.wait.until(EC.visibility_of_element_located(self.FIRST_ROW_NAME)).text.strip()
        except TimeoutException:
            return ""

    def get_menu_name_input_value(self):
        return self.wait.until(EC.presence_of_element_located(self.MENU_NAME_INPUT)).get_attribute("value") or ""
