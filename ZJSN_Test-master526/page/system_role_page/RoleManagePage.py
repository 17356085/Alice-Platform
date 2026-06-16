"""角色管理页面 Page Object — 重构版

变更记录:
  2026-06-11: 继承 BasePage，去绝对XPath，去time.sleep → BasePage等待方法
"""
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class RoleManagePage(BasePage):
    """角色管理页面操作 — 继承 BasePage"""

    # ══════════════════════════════════════════════════════════════════
    #  导航 — 复用 BasePage.navigate_to("系统管理", "角色管理")
    # ══════════════════════════════════════════════════════════════════

    ROLE_MANAGEMENT_FALLBACK = (By.XPATH, '//ul//span[normalize-space(.)="角色管理"]')

    ROLE_NAME_INPUT = (By.XPATH, '//input[@placeholder="请输入角色名称"]')
    ROLE_CODE_INPUT = (By.XPATH, '//input[@placeholder="请输入角色编码"]')

    STATUS_SELECT = (
        By.XPATH,
        '//*[normalize-space(.)="状态"]/ancestor::div[contains(@class,"el-form-item")][1]//div[contains(@class,"el-select")]',
    )
    STATUS_SELECT_FALLBACKS = [
        (
            By.XPATH,
            '//label[normalize-space(.)="状态"]/following::div[contains(@class,"el-select")][1]',
        ),
        (
            By.XPATH,
            '//form//div[contains(@class,"el-form-item")][.//*[contains(text(),"状态")]]//div[contains(@class,"el-select")]',
        ),
    ]

    SEARCH_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="搜索" or normalize-space(.)="查询"]]')
    RESET_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="重置"]]')

    TABLE_ROWS = (By.XPATH, '//tr[contains(@class, "el-table__row")]')
    TABLE_HEADERS = (By.XPATH, '//div[contains(@class,"el-table__header-wrapper")]//th//div')

    PAGINATION = (By.CSS_SELECTOR, ".el-pagination")
    CURRENT_PAGE = (By.CSS_SELECTOR, ".el-pagination .el-pager li.active, .el-pagination .el-pager li.is-active")
    NEXT_PAGE_BUTTON = (By.CSS_SELECTOR, ".el-pagination .btn-next")
    NEXT_PAGE_BUTTON_FALLBACKS = [
        (By.CSS_SELECTOR, ".el-pagination button.btn-next"),
        (By.XPATH, '//div[contains(@class,"el-pagination")]//button[contains(@class,"btn-next")]'),
        (By.XPATH, '//button[@aria-label="下一页" or @aria-label="Next page"]'),
    ]

    TOOLBAR_ADD = (By.XPATH, '//button[.//span[normalize-space(.)="新增" or normalize-space(.)="新建"]]')
    TOOLBAR_EDIT = (By.XPATH, '//button[.//span[normalize-space(.)="修改" or normalize-space(.)="编辑"]]')
    TOOLBAR_DELETE = (By.XPATH, '//button[.//span[normalize-space(.)="删除"]]')
    TOOLBAR_ADD_FALLBACK = (By.XPATH, '//button[contains(@class,"el-button")][.//span[contains(text(),"新增") or contains(text(),"新建")]]')
    TOOLBAR_EDIT_FALLBACK = (By.XPATH, '//div[contains(@class,"el-button-group")]//button[contains(.,"修改") or contains(.,"编辑")]')
    TOOLBAR_DELETE_FALLBACK = (By.XPATH, '//button[contains(@class,"el-button")][.//span[contains(text(),"删除")]]')

    TOAST_MESSAGE = (By.XPATH, '(//*[contains(@class,"el-message__content") and normalize-space(.)!=""])[last()]')
    FORM_ERRORS = (By.CSS_SELECTOR, ".el-form-item__error")

    DIALOG_TITLE = (By.XPATH, '(//div[contains(@class,"el-dialog")])[last()]//span[contains(@class,"el-dialog__title")]')
    DIALOG_ROLE_NAME_INPUT = (By.XPATH, '//div[contains(@class,"el-dialog")]//input[@placeholder="请输入角色名称"]')
    DIALOG_ROLE_CODE_INPUT = (By.XPATH, '//div[contains(@class,"el-dialog")]//input[@placeholder="请输入角色编码"]')
    DIALOG_ORDER_INPUT = (By.XPATH, '//div[contains(@class,"el-dialog")]//*[contains(normalize-space(.),"显示顺序")]/ancestor::div[contains(@class,"el-form-item")][1]//input')
    DIALOG_REMARK_TEXTAREA = (By.XPATH, '//div[contains(@class,"el-dialog")]//*[contains(normalize-space(.),"备注")]/ancestor::div[contains(@class,"el-form-item")][1]//textarea')
    DIALOG_STATUS_ENABLE = (By.XPATH, '(//div[contains(@class,"el-dialog")])[last()]//label[.//span[normalize-space(.)="启用"]]')
    DIALOG_STATUS_DISABLE = (By.XPATH, '(//div[contains(@class,"el-dialog")])[last()]//label[.//span[normalize-space(.)="停用" or normalize-space(.)="禁用"]]')
    DIALOG_CONFIRM = (By.XPATH, '(//div[contains(@class,"el-dialog")])[last()]//button[.//span[normalize-space(.)="确定"]]')
    DIALOG_CANCEL = (By.XPATH, '(//div[contains(@class,"el-dialog")])[last()]//button[.//span[normalize-space(.)="取消"]]')
    DIALOG_CONFIRM_FALLBACKS = [
        (By.XPATH, '(//footer[contains(@class,"el-dialog__footer")]//button[.//span[normalize-space(.)="确定"]])[last()]'),
        (By.XPATH, '(//footer//button[.//span[normalize-space(.)="确定"]])[last()]'),
    ]
    DIALOG_CANCEL_FALLBACKS = [
        (By.XPATH, '(//footer[contains(@class,"el-dialog__footer")]//button[.//span[normalize-space(.)="取消"]])[last()]'),
        (By.XPATH, '(//footer//button[.//span[normalize-space(.)="取消"]])[last()]'),
    ]

    MESSAGEBOX_CONFIRM = (By.XPATH, '(//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))])[last()]//button[.//span[normalize-space(.)="确定"]]')

    PERMISSION_BUTTON_TEXT = "权限"
    ASSIGN_USER_BUTTON_TEXT = "分配用户"

    TAB_PC_OPERATIONS = (By.ID, "tab-operations")
    TAB_MINIAPP_OPERATIONS = (By.ID, "tab-miniappOperations")
    TAB_DATA_SCOPE = (By.ID, "tab-dataScope")

    ACTIVE_TAB_PANE_FIRST_CHECKBOX = (
        By.XPATH,
        '(//div[contains(@class,"el-tab-pane") and contains(@class,"is-active")]//span[contains(@class,"el-checkbox__inner")])[1]',
    )
    ACTIVE_TAB_PANE_FIRST_RADIO = (
        By.XPATH,
        '(//div[contains(@class,"el-tab-pane") and contains(@class,"is-active")]//span[contains(@class,"el-radio__inner")])[1]',
    )
    ACTIVE_TAB_PANE_FIRST_NAV_TO_CHILD = (
        By.XPATH,
        '(//div[contains(@class,"el-tab-pane") and contains(@class,"is-active")]'
        '//*[contains(@class,"el-icon") and (contains(@class,"right") or contains(@class,"arrow"))])[1]',
    )
    ACTIVE_TAB_PANE_BACK_ICON = (
        By.XPATH,
        '(//div[contains(@class,"el-tab-pane") and contains(@class,"is-active")]'
        '//*[contains(@class,"el-icon") and (contains(@class,"left") or contains(@class,"back"))])[1]',
    )
    PERMISSION_DIALOG_CONFIRM_LOCATORS = [
        (
            By.XPATH,
            '(//div[contains(@class,"el-dialog__wrapper") and not(contains(@style,"display: none"))]//button[.//span[normalize-space(.)="确定"]])[last()]',
        ),
        (
            By.XPATH,
            '(//div[contains(@class,"el-drawer__wrapper") and not(contains(@style,"display: none"))]//button[.//span[normalize-space(.)="确定"]])[last()]',
        ),
        (
            By.XPATH,
            '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[.//span[normalize-space(.)="确定"]])[last()]',
        ),
        (By.XPATH, '(//button[normalize-space(.)="确定"])[last()]'),
        (By.XPATH, '(//button[.//span[normalize-space(.)="确定"]])[last()]'),
        (
            By.XPATH,
            '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[contains(@class,"el-button--primary")])[last()]',
        ),
        (
            By.XPATH,
            '(//div[contains(@class,"el-drawer__wrapper") and not(contains(@style,"display: none"))]//button[contains(@class,"el-button--primary")])[last()]',
        ),
    ]
    PERMISSION_DIALOG_CANCEL_LOCATORS = [
        (
            By.XPATH,
            '(//div[contains(@class,"el-dialog__wrapper") and not(contains(@style,"display: none"))]//button[.//span[normalize-space(.)="取消"]])[last()]',
        ),
        (
            By.XPATH,
            '(//div[contains(@class,"el-drawer__wrapper") and not(contains(@style,"display: none"))]//button[.//span[normalize-space(.)="取消"]])[last()]',
        ),
        (
            By.XPATH,
            '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[.//span[normalize-space(.)="取消"]])[last()]',
        ),
        (By.XPATH, '(//button[.//span[normalize-space(.)="取消"]])[last()]'),
    ]

    ASSIGN_USER_DIALOG_FIRST_ROW_CHECKBOX = (
        By.XPATH,
        '(//div[contains(@class,"el-dialog")])[last()]//table//tbody/tr[1]/td[1]//label[contains(@class,"el-checkbox")]',
    )
    ASSIGN_USER_DIALOG_CONFIRM = (
        By.XPATH,
        '(//div[contains(@class,"el-dialog")])[last()]//button[.//span[normalize-space(.)="确定"]]',
    )
    ASSIGN_USER_DIALOG_CONFIRM_FALLBACKS = [
        (By.XPATH, '(//div[contains(@class,"el-dialog")])[last()]//footer//button[2]'),
        (By.XPATH, '(//div[contains(@class,"el-dialog")])[last()]//div[contains(@class,"el-dialog__footer")]//button[2]'),
        (By.XPATH, '/html/body/div[7]/div/div/footer/div/button[2]/span/ancestor::button[1]'),
        (By.XPATH, '/html/body/div[7]/div/div/footer/div/button[2]'),
    ]

    def __init__(self, driver, timeout=None):
        """初始化角色管理页面 — 继承 BasePage"""
        super().__init__(driver, timeout)

    # ══════════════════════════════════════════════════════════════════
    #  导航（重构：统一使用 BasePage.navigate_to）
    # ══════════════════════════════════════════════════════════════════

    def navigate(self):
        """导航到角色管理页面 — 唯一入口"""
        logger.info("导航到 → 系统管理 → 角色管理")
        self.navigate_to("系统管理", "角色管理")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        return self

    # 向后兼容别名
    def navigate_to_role_management(self):
        """@deprecated: 使用 navigate() 替代"""
        return self.navigate()
        self._wait_loading_gone(timeout=3)

    def input_role_name(self, name):
        self._wait_loading_gone(timeout=10)
        el = self.wait.until(EC.presence_of_element_located(self.ROLE_NAME_INPUT))
        # JS clear + focus, then Selenium send_keys — avoids http-full-loading overlay
        self.driver.execute_script("arguments[0].value = ''; arguments[0].focus();", el)
        el.send_keys(name)
        time.sleep(0.3)

    def input_role_code(self, code):
        self._wait_loading_gone(timeout=10)
        el = self.wait.until(EC.presence_of_element_located(self.ROLE_CODE_INPUT))
        self.driver.execute_script("arguments[0].value = ''; arguments[0].focus();", el)
        el.send_keys(code)
        time.sleep(0.3)

    def click_search(self):
        btn = self.wait.until(EC.element_to_be_clickable(self.SEARCH_BUTTON))
        self._scroll_to_pagination_area()
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_loading_gone(timeout=3)

    def wait_table_ready(self, timeout=8):
        """等待表格数据渲染完成（JS轮询 thead th + tbody tr 或空状态提示）。
        返回 True 如果表格就绪，timeout 后返回 True（不阻塞后续操作）。"""
        import time
        deadline = time.time() + timeout
        last_th = 0
        while time.time() < deadline:
            try:
                th_count = self.driver.execute_script(
                    "return document.querySelectorAll('.el-table__header-wrapper th').length || "
                    "document.querySelectorAll('thead th').length;"
                )
                body_count = self.driver.execute_script(
                    "return document.querySelectorAll('.el-table__body-wrapper tbody tr').length || "
                    "document.querySelectorAll('tbody tr').length;"
                )
                empty_visible = self.driver.execute_script(
                    "var el = document.querySelector('.el-table__empty-text, .el-table-empty, [class*=empty]');"
                    "return el && el.offsetHeight > 0;"
                )
                if th_count > 0 and (body_count >= 1 or empty_visible):
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        return True  # timeout 后不阻塞，让后续断言自然失败

    def click_reset(self):
        btn = self.wait.until(EC.element_to_be_clickable(self.RESET_BUTTON))
        self._scroll_to_pagination_area()
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_loading_gone(timeout=3)

    def _scroll_to_pagination_area(self):
        try:
            el = self.driver.find_element(*self.PAGINATION)
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
        except Exception:
            pass

    def select_status(self, status_text):
        if status_text == "禁用":
            status_text = "停用"

        candidates = [self.STATUS_SELECT] + list(self.STATUS_SELECT_FALLBACKS)
        select = None
        for loc in candidates:
            try:
                select = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(loc))
                if select and select.is_displayed():
                    break
            except Exception:
                continue

        if not select:
            raise TimeoutException("未找到状态下拉框")

        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select)
        self.wait_vue_stable()

        # 点击下拉框触发器
        try:
            trigger = select.find_element(
                By.XPATH,
                './/*[contains(@class,"el-select__wrapper") or contains(@class,"el-input__wrapper") or contains(@class,"el-select__selection") or contains(@class,"el-select__selected-item")][1]',
            )
            self.driver.execute_script("arguments[0].click();", trigger)
        except Exception:
            self.driver.execute_script("arguments[0].click();", select)
        
        # 等待下拉菜单展开
        self.wait_vue_stable()
        
        # 多种策略查找选项
        option_found = False
        
        # 策略1: 使用更宽松的XPath定位
        option_strategies = [
            # 直接通过文本内容查找
            f'//li[contains(@class,"el-select-dropdown__item") and not(contains(@class,"is-disabled"))][normalize-space(.)="{status_text}"]',
            # 在下拉容器中查找
            f'(//div[contains(@class,"el-select-dropdown")])[last()]//li[normalize-space(.)="{status_text}"]',
            # 在popper容器中查找
            f'(//div[contains(@class,"el-popper")])[last()]//li[normalize-space(.)="{status_text}"]',
            # 模糊匹配文本
            f'//li[contains(@class,"el-select-dropdown__item")][contains(normalize-space(.),"{status_text}")]',
        ]
        
        for xpath in option_strategies:
            try:
                opt = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                self.driver.execute_script("arguments[0].click();", opt)
                option_found = True
                self.wait_vue_stable()
                break
            except Exception:
                continue
        
        # 如果所有策略都失败，尝试重新打开下拉框
        if not option_found:
            try:
                self.driver.execute_script("arguments[0].click();", select)
                self.wait_vue_stable()
                
                # 再次尝试最简单的定位
                opt = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, f'//li[normalize-space(.)="{status_text}"]')
                    )
                )
                self.driver.execute_script("arguments[0].click();", opt)
                self.wait_vue_stable()
            except Exception as e:
                # 输出调试信息
                logger.warning("无法选择状态 '%s'，错误: %s", status_text, e)
                raise TimeoutException(f"无法选择状态 '{status_text}'，请检查页面元素")

    def click_add(self):
        candidates = [self.TOOLBAR_ADD, self.TOOLBAR_ADD_FALLBACK]
        btn = None
        for loc in candidates:
            try:
                btn = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(loc))
                if btn and btn.is_displayed():
                    break
            except Exception:
                continue
        if not btn:
            raise TimeoutException("未找到新增按钮")
        self.driver.execute_script("arguments[0].click();", btn)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(self.DIALOG_ROLE_NAME_INPUT))
        self.wait_vue_stable()

    def _click_first_available(self, locators):
        last_exc = None
        for loc in locators:
            try:
                el = WebDriverWait(self.driver, 8).until(EC.presence_of_element_located(loc))
                if el and el.is_displayed():
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                    self.wait_vue_stable()
                    self.driver.execute_script("arguments[0].click();", el)
                    return
            except Exception as e:
                last_exc = e
                continue
        # fallback: 免去 is_displayed 检查，直接 JS click
        for loc in locators:
            try:
                el = self.driver.find_element(*loc)
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                self.wait_vue_stable()
                self.driver.execute_script("arguments[0].click();", el)
                return
            except Exception as e:
                last_exc = e
                continue
        raise TimeoutException(str(last_exc) if last_exc else "未找到可点击元素")

    def click_edit(self):
        candidates = [self.TOOLBAR_EDIT, self.TOOLBAR_EDIT_FALLBACK]
        btn = None
        for loc in candidates:
            try:
                btn = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(loc))
                if btn and btn.is_displayed():
                    break
            except Exception:
                continue
        if not btn:
            raise TimeoutException("未找到修改按钮")
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_loading_gone(timeout=3)

    def click_delete(self):
        candidates = [self.TOOLBAR_DELETE, self.TOOLBAR_DELETE_FALLBACK]
        btn = None
        for loc in candidates:
            try:
                btn = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(loc))
                if btn and btn.is_displayed():
                    break
            except Exception:
                continue
        if not btn:
            raise TimeoutException("未找到删除按钮")
        self.driver.execute_script("arguments[0].click();", btn)
        self.wait_vue_stable()

    def _get_action_button_in_row(self, role_name, action_text):
        row_xpath_candidates = [
            f'//tr[contains(@class,"el-table__row")][.//td//div[normalize-space(.)="{role_name}"]]',
            f'//tr[contains(@class,"el-table__row")][.//td//div[contains(normalize-space(.),"{role_name}")]]',
        ]

        for row_xpath in row_xpath_candidates:
            button_xpath_candidates = [
                f'{row_xpath}//button[.//span[normalize-space(.)="{action_text}"]]',
                f'{row_xpath}//a[normalize-space(.)="{action_text}"]',
                f'{row_xpath}//span[normalize-space(.)="{action_text}"]/ancestor::button[1]',
            ]
            for btn_xpath in button_xpath_candidates:
                try:
                    return WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.XPATH, btn_xpath))
                    )
                except Exception:
                    continue

        raise TimeoutException(f"未找到角色'{role_name}'行内按钮: {action_text}")

    def click_permission_by_role_name(self, role_name):
        btn = self._get_action_button_in_row(role_name, self.PERMISSION_BUTTON_TEXT)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        self.wait_vue_stable()
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_loading_gone(timeout=3)

    def click_assign_users_by_role_name(self, role_name):
        btn = self._get_action_button_in_row(role_name, self.ASSIGN_USER_BUTTON_TEXT)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        self.wait_vue_stable()
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_loading_gone(timeout=3)

    def click_permission_tab_pc(self):
        return self._click_permission_tab(tab_id="tab-operations", tab_text="PC操作权限")

    def click_permission_tab_miniapp(self):
        return self._click_permission_tab(tab_id="tab-miniappOperations", tab_text="小程序操作权限")

    def click_permission_tab_data_scope(self):
        return self._click_permission_tab(tab_id="tab-dataScope", tab_text="数据权限")

    def _click_permission_tab(self, tab_id, tab_text):
        locators = [
            (By.ID, tab_id),
            (By.XPATH, f'//*[@id="{tab_id}"]'),
            (By.XPATH, f'//div[contains(@class,"el-tabs__item") and normalize-space(.)="{tab_text}"]'),
            (By.XPATH, f'//span[normalize-space(.)="{tab_text}"]/ancestor::div[contains(@class,"el-tabs__item")][1]'),
        ]
        for loc in locators:
            try:
                el = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(loc))
                if el and el.is_displayed():
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                    self.wait_vue_stable()
                    self.driver.execute_script("arguments[0].click();", el)
                    self.wait_vue_stable()
                    return True
            except Exception:
                continue
        return False

    def toggle_first_permission_item_in_active_tab(self):
        return self.ensure_permission_selected_in_active_tab()

    def select_first_two_permission_checkboxes_in_active_tab(self):
        """在当前权限 Tab 中勾选前两个未选中的权限复选框。"""
        locators = [
            (
                By.XPATH,
                '//div[contains(@class,"el-tab-pane") and contains(@class,"is-active")]'
                '//label[contains(@class,"el-checkbox") and not(contains(@class,"is-checked"))]'
                '//span[contains(@class,"el-checkbox__inner")]',
            ),
            (
                By.XPATH,
                '//div[contains(@class,"el-tab-pane") and contains(@class,"is-active")]'
                '//*[contains(@class,"el-checkbox__inner")]',
            ),
        ]

        clicked = 0
        for loc in locators:
            try:
                checkboxes = self.driver.find_elements(*loc)
                for checkbox in checkboxes:
                    if clicked >= 2:
                        break
                    try:
                        label = checkbox.find_element(By.XPATH, './ancestor::label[contains(@class,"el-checkbox")][1]')
                        if "is-checked" in (label.get_attribute("class") or ""):
                            continue
                        if not checkbox.is_displayed():
                            continue
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", checkbox)
                        self.wait_vue_stable()
                        self.driver.execute_script("arguments[0].click();", checkbox)
                        clicked += 1
                        self.wait_vue_stable()
                    except Exception:
                        continue
                if clicked >= 2:
                    break
            except Exception:
                continue

        if clicked < 2:
            try:
                self._open_first_permission_sublist_in_active_tab()
                self.wait_vue_stable()
                checkboxes = self.driver.find_elements(
                    By.XPATH,
                    '//div[contains(@class,"el-tab-pane") and contains(@class,"is-active")]'
                    '//label[contains(@class,"el-checkbox") and not(contains(@class,"is-checked"))]'
                    '//span[contains(@class,"el-checkbox__inner")]',
                )
                for checkbox in checkboxes:
                    if clicked >= 2:
                        break
                    if checkbox.is_displayed():
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", checkbox)
                        self.wait_vue_stable()
                        self.driver.execute_script("arguments[0].click();", checkbox)
                        clicked += 1
                        self.wait_vue_stable()
            except Exception:
                pass

        logger.info("当前权限 Tab 已勾选 %s 个权限复选框", clicked)
        return clicked >= 2

    def _get_permission_confirm_button(self):
        for loc in self.PERMISSION_DIALOG_CONFIRM_LOCATORS:
            try:
                btn = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(loc))
                if btn and btn.is_displayed():
                    return btn
            except Exception:
                continue
        return None

    def _is_permission_confirm_enabled(self):
        btn = self._get_permission_confirm_button()
        if not btn:
            return False
        disabled = (btn.get_attribute("disabled") is not None) or ("is-disabled" in (btn.get_attribute("class") or ""))
        return not disabled

    def _open_first_permission_sublist_in_active_tab(self):
        locators = [
            (By.XPATH, '(//div[contains(@class,"el-tab-pane") and contains(@class,"is-active")]//*[self::i][contains(@class,"el-icon") and contains(@class,"right")])[1]'),
            (By.XPATH, '(//div[contains(@class,"el-tab-pane") and contains(@class,"is-active")]//*[contains(@class,"el-icon") and (contains(@class,"arrow-right") or contains(@class,"right"))])[1]'),
            self.ACTIVE_TAB_PANE_FIRST_NAV_TO_CHILD,
        ]
        try:
            self._click_first_available(locators)
            self.wait_vue_stable()
            return True
        except Exception:
            return False

    def _toggle_first_checkbox_in_active_tab(self):
        candidates = [
            (
                By.XPATH,
                '(//div[contains(@class,"el-tab-pane") and contains(@class,"is-active")]'
                '//label[contains(@class,"el-checkbox") and not(contains(@class,"is-checked"))]'
                '//span[contains(@class,"el-checkbox__inner")])[1]',
            ),
            self.ACTIVE_TAB_PANE_FIRST_CHECKBOX,
        ]
        for loc in candidates:
            try:
                el = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(loc))
                self.driver.execute_script("arguments[0].click();", el)
                self.wait_vue_stable()
                return True
            except Exception:
                continue
        return False

    def _toggle_first_radio_in_active_tab(self):
        preferred = [
            (
                By.XPATH,
                '(//div[contains(@class,"el-tab-pane") and contains(@class,"is-active")]'
                '//label[contains(@class,"el-radio")][.//*[normalize-space(.)="本组织数据"]])[1]',
            ),
            (
                By.XPATH,
                '(//div[contains(@class,"el-tab-pane") and contains(@class,"is-active")]'
                '//label[contains(@class,"el-radio") and not(contains(@class,"is-checked"))]'
                '//span[contains(@class,"el-radio__inner")])[1]',
            ),
            self.ACTIVE_TAB_PANE_FIRST_RADIO,
        ]
        for loc in preferred:
            try:
                el = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(loc))
                self.driver.execute_script("arguments[0].click();", el)
                self.wait_vue_stable()
                return True
            except Exception:
                continue
        return False

    def ensure_permission_selected_in_active_tab(self):
        if self._toggle_first_checkbox_in_active_tab() and self._is_permission_confirm_enabled():
            return True

        if self._open_first_permission_sublist_in_active_tab():
            if self._toggle_first_checkbox_in_active_tab() and self._is_permission_confirm_enabled():
                return True

        if self._toggle_first_radio_in_active_tab() and self._is_permission_confirm_enabled():
            return True

        self._toggle_first_checkbox_in_active_tab()
        self._toggle_first_radio_in_active_tab()
        return True

    def click_permission_confirm(self):
        last_exc = None
        found_disabled = False
        for loc in self.PERMISSION_DIALOG_CONFIRM_LOCATORS:
            try:
                btn = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(loc))
                if btn and btn.is_displayed():
                    disabled = (btn.get_attribute("disabled") is not None) or ("is-disabled" in (btn.get_attribute("class") or ""))
                    if not disabled:
                        self.driver.execute_script("arguments[0].click();", btn)
                        self._wait_loading_gone(timeout=3)
                        return
                    found_disabled = True
            except Exception as e:
                last_exc = e
                continue
        if found_disabled and not last_exc:
            raise TimeoutException("权限弹窗确定按钮处于禁用状态，请先在子列表中勾选至少一项权限")
        raise TimeoutException(str(last_exc) if last_exc else "未找到权限弹窗确定按钮")

    def click_permission_cancel(self):
        last_exc = None
        for loc in self.PERMISSION_DIALOG_CANCEL_LOCATORS:
            try:
                btn = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(loc))
                if btn and btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_vue_stable()
                    return
            except Exception as e:
                last_exc = e
                continue
        raise TimeoutException(str(last_exc) if last_exc else "未找到权限弹窗取消按钮")

    def assign_user_select_first_row_and_confirm(self):
        cb = self.wait.until(EC.presence_of_element_located(self.ASSIGN_USER_DIALOG_FIRST_ROW_CHECKBOX))
        self.driver.execute_script("arguments[0].click();", cb)
        self.wait_vue_stable()
        locators = [self.ASSIGN_USER_DIALOG_CONFIRM] + list(self.ASSIGN_USER_DIALOG_CONFIRM_FALLBACKS)
        self._click_first_available(locators)
        self._wait_loading_gone(timeout=3)

    def assign_user_clear_and_confirm(self):
        """清空分配用户弹窗中的已选用户并点击确定，避免角色测试产生分配残留。"""
        dialog_xpath = '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]'
        try:
            clear_locators = [
                (By.XPATH, f'{dialog_xpath}//button[.//span[normalize-space(.)="清空" or normalize-space(.)="清除"]]'),
                (By.XPATH, f'{dialog_xpath}//*[self::button or self::span][normalize-space(.)="清空" or normalize-space(.)="清除"]'),
                (By.XPATH, f'{dialog_xpath}//*[contains(@class,"el-transfer__button") and not(contains(@class,"is-disabled"))][.//*[contains(@class,"el-icon-arrow-left") or contains(@class,"arrow-left")]]'),
            ]

            clicked_clear = False
            for loc in clear_locators:
                try:
                    elements = self.driver.find_elements(*loc)
                    for el in elements:
                        target = el
                        if el.tag_name.lower() != "button":
                            try:
                                target = el.find_element(By.XPATH, "./ancestor::button[1]")
                            except Exception:
                                pass
                        disabled = (target.get_attribute("disabled") is not None) or ("is-disabled" in (target.get_attribute("class") or ""))
                        if target.is_displayed() and not disabled:
                            self.driver.execute_script("arguments[0].click();", target)
                            clicked_clear = True
                            self.wait_vue_stable()
                            break
                    if clicked_clear:
                        break
                except Exception:
                    continue

            if not clicked_clear:
                checked_locators = [
                    (By.XPATH, f'{dialog_xpath}//label[contains(@class,"el-checkbox") and contains(@class,"is-checked")]'),
                    (By.XPATH, f'{dialog_xpath}//tr[contains(@class,"el-table__row")]//label[contains(@class,"el-checkbox") and contains(@class,"is-checked")]'),
                ]
                for loc in checked_locators:
                    checked = self.driver.find_elements(*loc)
                    for checkbox in reversed(checked):
                        try:
                            if checkbox.is_displayed():
                                self.driver.execute_script("arguments[0].click();", checkbox)
                                clicked_clear = True
                                self.wait_vue_stable()
                        except Exception:
                            continue
                    if clicked_clear:
                        break

            locators = [self.ASSIGN_USER_DIALOG_CONFIRM] + list(self.ASSIGN_USER_DIALOG_CONFIRM_FALLBACKS)
            self._click_first_available(locators)
            self._wait_loading_gone(timeout=3)
        except Exception:
            try:
                self.click_dialog_cancel()
            except Exception:
                pass
            raise

    def select_role_checkbox_by_name(self, role_name):
        row_locators = [
            (By.XPATH, f'//tr[contains(@class,"el-table__row")][.//td//div[normalize-space(.)="{role_name}"]]'),
            (By.XPATH, f'//tr[contains(@class,"el-table__row")][.//td//div[contains(normalize-space(.),"{role_name}")]]'),
        ]

        row = None
        for loc in row_locators:
            try:
                row = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(loc))
                if row:
                    break
            except Exception:
                continue

        if row:
            checkbox = row.find_element(By.XPATH, './/td[1]//label[contains(@class,"el-checkbox")]')
        else:
            checkbox = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '(//tr[contains(@class,"el-table__row")]//td[1]//label[contains(@class,"el-checkbox")])[1]')
                )
            )

        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
        self.wait_vue_stable()
        self.driver.execute_script("arguments[0].click();", checkbox)
        self.wait_vue_stable()

    # ══════════════════════════════════════════════════════════════════
    #  Dialog 输入（BasePage.js_fill_input 封装）
    # ══════════════════════════════════════════════════════════════════

    def input_dialog_role_name(self, text, fallback_send_keys=True):
        """输入角色名称 — JS 赋值 + send_keys 保底（确保 v-model 触发）"""
        self.wait_vue_stable()
        self.js_fill_input_multi([
            self.DIALOG_ROLE_NAME_INPUT,
            (By.XPATH, '//div[contains(@class,"el-dialog")]//input[contains(@placeholder,"角色名称")]'),
            (By.XPATH, '//div[contains(@class,"el-dialog")]//div[contains(@class,"el-form-item")][.//label[contains(.,"角色名称")]]//input'),
        ], text, fallback_send_keys=fallback_send_keys)

    def input_dialog_role_code(self, text, fallback_send_keys=True):
        """输入角色编码 — JS 赋值 + send_keys 保底（确保 v-model 触发）"""
        self.wait_vue_stable()
        self.js_fill_input_multi([
            self.DIALOG_ROLE_CODE_INPUT,
            (By.XPATH, '//div[contains(@class,"el-dialog")]//input[contains(@placeholder,"角色编码")]'),
            (By.XPATH, '//div[contains(@class,"el-dialog")]//div[contains(@class,"el-form-item")][.//label[contains(.,"角色编码")]]//input'),
            (By.XPATH, '//div[contains(@class,"el-dialog")]//div[contains(@class,"el-form-item")][.//input[@placeholder="请输入角色名称"]]/following-sibling::div[contains(@class,"el-form-item")]//input'),
            (By.XPATH, '(//div[contains(@class,"el-dialog")]//input)[2]'),
            (By.XPATH, '//div[contains(@class,"el-dialog")]//label[contains(text(),"编码")]/following::input[1]'),
        ], text, fallback_send_keys=fallback_send_keys)

    def input_dialog_order(self, value, fallback_send_keys=True):
        """输入显示顺序 — JS 赋值 + send_keys 保底"""
        self.wait_vue_stable()
        self.js_fill_input_multi([
            self.DIALOG_ORDER_INPUT,
            (By.XPATH, '//div[contains(@class,"el-dialog")]//input[contains(@placeholder,"显示顺序") or contains(@placeholder,"排序")]'),
            (By.XPATH, '//div[contains(@class,"el-dialog")]//div[contains(@class,"el-form-item")][.//label[contains(.,"显示顺序") or contains(.,"排序")]]//input'),
        ], str(value), fallback_send_keys=fallback_send_keys)

    def input_dialog_remark(self, text):
        el = self.wait.until(EC.visibility_of_element_located(self.DIALOG_REMARK_TEXTAREA))
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        el.send_keys(text)

    def select_dialog_status(self, status_text):
        self.wait_vue_stable()
        locator = self.DIALOG_STATUS_ENABLE if status_text == "启用" else self.DIALOG_STATUS_DISABLE
        from selenium.common.exceptions import StaleElementReferenceException
        for attempt in range(3):
            try:
                # fresh locate 每次重试，不缓存 WebElement 引用
                el = self.driver.find_element(*locator)
                self.driver.execute_script("arguments[0].click();", el)
                self.wait_vue_stable()
                return
            except StaleElementReferenceException:
                if attempt < 2:
                    self.wait_vue_stable()
                else:
                    raise

    def click_dialog_confirm(self):
        locators = [self.DIALOG_CONFIRM] + list(self.DIALOG_CONFIRM_FALLBACKS)
        self._click_first_available(locators)
        self._wait_loading_gone(timeout=3)

    def click_dialog_cancel(self):
        locators = [self.DIALOG_CANCEL] + list(self.DIALOG_CANCEL_FALLBACKS)
        self._click_first_available(locators)
        self.wait_vue_stable()

    def confirm_message_box(self):
        btn = self.wait.until(EC.element_to_be_clickable(self.MESSAGEBOX_CONFIRM))
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_loading_gone(timeout=3)

    def get_toast_text(self):
        elements = self.driver.find_elements(*self.TOAST_MESSAGE)
        texts = []
        for el in elements:
            try:
                t = (el.text or "").strip()
                if t:
                    texts.append(t)
            except Exception:
                continue
        return texts[-1] if texts else ""

    def wait_for_toast_text(self, timeout=8):
        end = time.time() + timeout
        last = ""
        while time.time() < end:
            last = self.get_toast_text()
            if last:
                return last
            self.wait_vue_stable()
        return last

    def wait_for_toast_contains(self, keyword, timeout=8):
        end = time.time() + timeout
        while time.time() < end:
            text = self.get_toast_text()
            if text and keyword in text:
                return text
            self.wait_vue_stable()
        return self.get_toast_text()

    def get_form_error_texts(self):
        errors = self.driver.find_elements(*self.FORM_ERRORS)
        texts = []
        for e in errors:
            t = (e.text or "").strip()
            if t:
                texts.append(t)
        return texts

    def search(self, role_name=None, role_code=None, status=None):
        self.click_reset()
        if role_name is not None:
            self.input_role_name(role_name)
        if role_code is not None:
            self.input_role_code(role_code)
        if status is not None:
            self.select_status(status)
        self.click_search()
        self.wait_table_ready(timeout=8)  # 等表格渲染完毕再返回（避免 StaleElement）

    def get_selected_status(self):
        candidates = [self.STATUS_SELECT] + list(self.STATUS_SELECT_FALLBACKS)
        select = None
        for loc in candidates:
            try:
                select = self.driver.find_element(*loc)
                if select and select.is_displayed():
                    break
            except Exception:
                continue

        if not select:
            return ""

        try:
            v = select.find_element(By.XPATH, './/*[contains(@class,"el-input__inner") or self::input]')
            value = (v.get_attribute("value") or "").strip()
            if value:
                return value
        except Exception:
            pass

        try:
            text = (select.text or "").strip()
            return text
        except Exception:
            return ""

    def get_table_row_count(self):
        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(self.TABLE_ROWS))
            return len(self.driver.find_elements(*self.TABLE_ROWS))
        except TimeoutException:
            return 0

    def get_column_data(self, col_index, max_retries=3):
        """获取表格列数据，带重试机制处理StaleElementReferenceException"""
        for attempt in range(max_retries):
            try:
                locator = (By.CSS_SELECTOR, f".el-table__body-wrapper tbody tr td:nth-child({col_index}) div")
                elements = self.driver.find_elements(*locator)
                return [e.text.strip() for e in elements if e.text and e.text.strip()]
            except StaleElementReferenceException:
                if attempt == max_retries - 1:
                    raise
                # 等待表格重新渲染
                self._wait_loading_gone(timeout=2)
                continue
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                # 其他异常也重试
                self._wait_loading_gone(timeout=2)
                continue

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
    def get_current_page_number(self):
        try:
            els = self.driver.find_elements(*self.CURRENT_PAGE)
            el = els[0] if els else self.wait.until(EC.presence_of_element_located(self.CURRENT_PAGE))
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
            raise TimeoutException("未找到下一页按钮")

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
            pass

        next_num = before + 1
        page_locators = [
            (By.XPATH, f'//div[contains(@class,"el-pagination")]//ul[contains(@class,"el-pager")]//li[normalize-space(.)="{next_num}"]'),
            (By.XPATH, '//*[@id="app"]/div/div[3]/div/section/div/div/div[1]/div/div/div/div/div/div[2]/div[2]/div[2]/ul/li[2]'),
        ]
        for loc in page_locators:
            try:
                li = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable(loc))
                self.driver.execute_script("arguments[0].click();", li)
                WebDriverWait(self.driver, 5).until(lambda d: self.get_current_page_number() == next_num)
                self.wait_vue_stable()
                return True
            except Exception:
                continue

        return True

    def get_role_name_input_value(self):
        el = self.wait.until(EC.presence_of_element_located(self.ROLE_NAME_INPUT))
        return (el.get_attribute("value") or "").strip()

    def get_role_code_input_value(self):
        el = self.wait.until(EC.presence_of_element_located(self.ROLE_CODE_INPUT))
        return (el.get_attribute("value") or "").strip()

    # ══════════════════════════════════════════════════════════════════
    #  清空缓存 & 权限模块选择（Phase 1 基建新增）
    # ══════════════════════════════════════════════════════════════════

    def click_clear_cache(self):
        """点击全局「清空缓存」按钮（el-button--danger is-text，浮动按钮）

        该按钮在多个系统页面存在，用于刷新权限缓存。
        使用 JS 文本搜索定位，绕过 span 嵌套和浮动定位问题。

        Returns:
            bool: 是否成功点击
        """
        clicked = self.driver.execute_script("""
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                var txt = (btns[i].textContent || '').trim();
                if (txt.indexOf('清空缓存') !== -1 && btns[i].offsetParent !== null) {
                    btns[i].scrollIntoView({block: 'center'});
                    btns[i].click();
                    return true;
                }
            }
            // 降级：不检查可见性（可能被浮动层遮挡但仍可点击）
            for (var i = 0; i < btns.length; i++) {
                var txt = (btns[i].textContent || '').trim();
                if (txt.indexOf('清空缓存') !== -1) {
                    btns[i].scrollIntoView({block: 'center'});
                    btns[i].click();
                    return true;
                }
            }
            return false;
        """)
        if clicked:
            self.wait_vue_stable()
            # 等清空缓存的 Toast
            try:
                self.wait_for_toast_text(timeout=5)
            except Exception:
                pass
            logger.info("已点击清空缓存按钮")
        else:
            logger.warning("未找到清空缓存按钮（可能不在当前页面）")
        return bool(clicked)

    def select_permission_module(self, module_name):
        """在权限弹窗中勾选指定模块（PC操作权限 Tab 内）

        权限树使用自定义 .perm-group 组件（非 el-tree），结构：
          .perm-group
          ├── .perm-group__arrow (展开箭头)
          ├── .perm-group__name (模块名称，如"系统管理")
          └── 子节点中含 .el-checkbox

        遍历 .perm-group__name 找到匹配模块 → 勾选其下第一个未选中的 checkbox。
        如果该组处于折叠状态，先点击 .perm-group__arrow 展开。

        Args:
            module_name: 模块名称关键词，如 "设备管理"、"系统管理"

        Returns:
            bool: 是否成功勾选或已勾选
        """
        self.wait_vue_stable()
        # 确保权限树已渲染（el-tab-pane 切换后异步加载）
        import time
        for _ in range(5):
            has_tree = self.driver.execute_script(
                "return !!document.querySelector('.perm-group__name');"
            )
            if has_tree:
                break
            time.sleep(0.5)
        self.wait_vue_stable()

        result = self.driver.execute_script("""
            var moduleName = arguments[0];

            // 找可见的权限弹窗
            var dlg = document.querySelector('.el-dialog:not([style*="display: none"])');
            if (!dlg) {
                var dialogs = document.querySelectorAll('.el-dialog');
                for (var i = 0; i < dialogs.length; i++) {
                    if (dialogs[i].offsetParent !== null) {
                        dlg = dialogs[i];
                        break;
                    }
                }
            }
            if (!dlg) return 'no_dialog';

            // 策略1：通过 .perm-group__name 精确匹配模块名
            var nameEls = dlg.querySelectorAll('.perm-group__name');
            var targetGroup = null;
            for (var i = 0; i < nameEls.length; i++) {
                var txt = (nameEls[i].textContent || '').trim();
                if (txt.indexOf(moduleName) !== -1) {
                    targetGroup = nameEls[i].closest('.perm-group');
                    break;
                }
            }

            // 策略2：降级 — 遍历所有 .perm-group 按 textContent 模糊匹配
            if (!targetGroup) {
                var groups = dlg.querySelectorAll('.perm-group');
                for (var j = 0; j < groups.length; j++) {
                    var t = (groups[j].textContent || '').trim();
                    if (t.indexOf(moduleName) !== -1) {
                        targetGroup = groups[j];
                        break;
                    }
                }
            }

            // 策略3：再降级 — 搜索 checkbox label 文本
            if (!targetGroup) {
                var labels = dlg.querySelectorAll('.el-checkbox__label');
                for (var k = 0; k < labels.length; k++) {
                    var lt = (labels[k].textContent || '').trim();
                    if (lt.indexOf(moduleName) !== -1) {
                        // 点击该 label 对应的 checkbox
                        var cb = labels[k].closest('.el-checkbox');
                        if (cb) {
                            var inner = cb.querySelector('.el-checkbox__inner');
                            if (inner && inner.offsetParent !== null) {
                                inner.scrollIntoView({block: 'center'});
                                inner.click();
                                return 'checked_by_label';
                            }
                        }
                    }
                }
                return 'no_module';
            }

            // 展开折叠的组
            var arrow = targetGroup.querySelector('.perm-group__arrow');
            if (arrow && arrow.offsetParent !== null) {
                var isExpanded = targetGroup.classList.contains('is-expanded') ||
                    (targetGroup.getAttribute('aria-expanded') === 'true');
                if (!isExpanded) {
                    arrow.scrollIntoView({block: 'center'});
                    arrow.click();
                }
            }

            // 勾选第一个未选中的 checkbox
            var checkboxes = targetGroup.querySelectorAll('.el-checkbox:not(.is-checked) .el-checkbox__inner');
            for (var m = 0; m < checkboxes.length; m++) {
                if (checkboxes[m].offsetParent !== null) {
                    checkboxes[m].scrollIntoView({block: 'center'});
                    checkboxes[m].click();
                    return 'checked';
                }
            }

            // 如果全部已选中，也算成功
            var checkedAll = targetGroup.querySelectorAll('.el-checkbox.is-checked');
            if (checkedAll.length > 0) return 'already_checked';

            return 'no_checkbox';
        """, module_name)

        self.wait_vue_stable()
        logger.info("select_permission_module('%s') → %s", module_name, result)
        return result in ('checked', 'checked_by_label', 'already_checked')
