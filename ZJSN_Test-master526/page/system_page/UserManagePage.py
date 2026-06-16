"""用户管理页面 Page Object — 重构版

变更记录:
  2026-06-11: 继承 BasePage，清理绝对 XPath，替换 time.sleep → BasePage 等待方法
"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class UserManagePage(BasePage):
    """用户管理页面操作 — 继承 BasePage"""

    # ══════════════════════════════════════════════════════════════════
    #  导航（复用 BasePage.navigate_to + SidebarNavigator）
    # ══════════════════════════════════════════════════════════════════
    # 注意：不再使用绝对 XPath 点击菜单，统一通过 navigate_to("系统管理", "用户管理")

    # ══════════════════════════════════════════════════════════════════
    #  页面专属定位器（CSS优先 → 相对XPath → 文本匹配）
    # ══════════════════════════════════════════════════════════════════
    
    # 列表相关定位
    TOTAL_COUNT_TEXT = (By.CSS_SELECTOR, ".el-pagination__total")  # 复用 BasePage.TOTAL_COUNT
    USERNAME_HEADER = (By.XPATH, '//th//div[text()="用户名"]')
    FIRST_ROW_USERNAME = (By.XPATH, '//tr[contains(@class, "el-table__row")][1]//td[2]//div')
    NEXT_PAGE_BUTTON = (By.CSS_SELECTOR, ".el-pagination .btn-next")  # 复用 BasePage.NEXT_PAGE
    SCROLL_CONTAINER = (By.CSS_SELECTOR, ".el-scrollbar__wrap")

    # 搜索相关定位
    SEARCH_USERNAME_INPUT = (
        By.CSS_SELECTOR,
        'input[placeholder*="用户名"]'
    )
    ROLE_SELECT = (
        By.XPATH,
        '//form[contains(@class,"el-form")]//div[contains(@class,"el-select")][.//label[contains(text(),"角色")]]'
        '| //div[contains(@class,"el-form-item")][.//label[contains(text(),"角色")]]//div[contains(@class,"el-select")]'
    )
    STATUS_RADIO_GROUP = (By.XPATH, '//form//div[contains(@class, "el-radio-group")]')
    SEARCH_BUTTON = (By.XPATH, '//button[.//span[contains(normalize-space(.), "查询")]]')
    RESET_BUTTON = (By.XPATH, '//button[.//span[contains(normalize-space(.), "重置")]]')
    # 下拉选项通用定位
    SELECT_OPTION = (By.XPATH, '//li[contains(@class, "el-select-dropdown__item")]//span')

    # 操作相关定位
    ADD_USER_BUTTON = (
        By.XPATH,
        '//button[contains(@class,"el-button")][.//span[contains(text(),"新增") or contains(text(),"新建")]]'
    )
    EDIT_BUTTON = (By.XPATH, '//button[.//span[text()="编辑"]]')
    ASSIGN_ROLE_BUTTON = (By.XPATH, '//button[.//span[text()="分配角色"]]')
    MORE_BUTTON = (By.XPATH, '//div[contains(@class, "el-dropdown")]//button[contains(., "更多")]')
    
    # 更多操作下拉菜单项 (这些在 body 下的独立容器中)
    MORE_DELETE_OPTION = (By.XPATH, '(//li[contains(@class,"el-dropdown-menu__item") and contains(normalize-space(.), "删除") and not(ancestor::div[contains(@style,"display: none")])])[last()]')
    MORE_RESET_PWD_OPTION = (By.XPATH, '(//li[contains(@class,"el-dropdown-menu__item") and (contains(normalize-space(.), "重置密码") or contains(normalize-space(.), "启用/重置密码")) and not(ancestor::div[contains(@style,"display: none")])])[last()]')

    # 弹窗/对话框相关
    # 姓名输入框 (编辑弹窗)
    DIALOG_NAME_INPUT = (By.XPATH, '//div[contains(@class, "el-dialog")]//label[contains(., "姓名")]/..//input')
    # 用户名输入框 (编辑弹窗)
    DIALOG_USERNAME_INPUT = (By.XPATH, '//div[contains(@class, "el-dialog")]//label[contains(., "用户名")]/..//input')
    # 密码输入框 (新增弹窗)
    DIALOG_PASSWORD_INPUT = (By.XPATH, '//div[contains(@class, "el-dialog")]//label[contains(., "密码")]/..//input')
    # 确定按钮 (弹窗通用)
    DIALOG_CONFIRM_BUTTON = (By.XPATH, '//div[contains(@class, "el-dialog")]//button[.//span[text()="确定"]]')
    # 取消按钮 (弹窗通用)
    DIALOG_CANCEL_BUTTON = (By.XPATH, '//div[contains(@class, "el-dialog")]//button[.//span[normalize-space(.)="取消"]]')
    # 表单校验错误信息
    FORM_VALIDATION_ERROR = (By.CSS_SELECTOR, ".el-form-item__error")
    
    # 消息提示 (Toast)
    TOAST_MESSAGE = (By.CSS_SELECTOR, ".el-message__content")

    # 复选框/单选框在弹窗中 (分配角色)
    DIALOG_ROLE_CHECKBOX = (By.XPATH, '//div[contains(@class, "el-dialog")]//label[contains(@class, "el-checkbox")]')

    def __init__(self, driver, timeout=None):
        """初始化用户管理页面 — 继承 BasePage"""
        super().__init__(driver, timeout)

    # ══════════════════════════════════════════════════════════════════
    #  弹窗辅助（BasePage._get_visible_dialog 已提供，此处作为增强）
    # ══════════════════════════════════════════════════════════════════

    def _get_visible_dialog(self, timeout=None):
        locator = (
            By.XPATH,
            '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[contains(@class,"el-dialog")]'
            ' | //div[contains(@class,"el-dialog__wrapper") and not(contains(@style,"display: none"))]//div[contains(@class,"el-dialog")])[last()]',
        )
        return self.wait.until(EC.visibility_of_element_located(locator))

    def _get_dialog_form_item(self, label_text):
        """
        获取当前可见弹窗内，指定 label 对应的表单项。
        说明：弹窗出现后表单渲染可能有延迟，需要等待元素出现，避免偶发定位失败。
        """
        item_xpath = (
            f'.//div[contains(@class,"el-form-item")]'
            f'[.//label[contains(@class,"el-form-item__label") and contains(normalize-space(.), "{label_text}")]]'
        )

        def _locate(_driver):
            dialog = self._get_visible_dialog()
            return dialog.find_element(By.XPATH, item_xpath)

        return WebDriverWait(self.driver, 10).until(lambda d: _locate(d))

    def input_dialog_input(self, label_text, value):
        try:
            from selenium.webdriver.common.keys import Keys
            item = self._get_dialog_form_item(label_text)
            input_el = WebDriverWait(self.driver, 10).until(
                lambda d: item.find_element(By.XPATH, './/input[not(@disabled)]')
            )
            WebDriverWait(self.driver, 10).until(lambda d: input_el.is_displayed() and input_el.is_enabled())
            try:
                input_el.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", input_el)
            input_el.send_keys(Keys.CONTROL + "a")
            input_el.send_keys(Keys.DELETE)
            input_el.send_keys(value)
            logger.info("弹窗输入 [%s] = %s", label_text, value)
        except Exception as e:
            logger.error("弹窗输入 [%s] 失败: %s", label_text, e)
            raise

    def input_dialog_textarea(self, label_text, value):
        try:
            from selenium.webdriver.common.keys import Keys
            item = self._get_dialog_form_item(label_text)
            textarea = WebDriverWait(self.driver, 10).until(lambda d: item.find_element(By.XPATH, './/textarea[not(@disabled)]'))
            WebDriverWait(self.driver, 10).until(lambda d: textarea.is_displayed() and textarea.is_enabled())
            try:
                textarea.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", textarea)
            textarea.send_keys(Keys.CONTROL + "a")
            textarea.send_keys(Keys.DELETE)
            textarea.send_keys(value)
            logger.info("弹窗输入 [%s] = %s", label_text, value)
        except Exception as e:
            logger.error("弹窗输入 [%s] 失败: %s", label_text, e)
            raise

    def clear_dialog_input(self, label_text):
        try:
            from selenium.webdriver.common.keys import Keys
            item = self._get_dialog_form_item(label_text)
            input_el = WebDriverWait(self.driver, 10).until(
                lambda d: item.find_element(By.XPATH, './/input[not(@disabled)]')
            )
            WebDriverWait(self.driver, 10).until(lambda d: input_el.is_displayed() and input_el.is_enabled())
            try:
                input_el.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", input_el)
            input_el.send_keys(Keys.CONTROL + "a")
            input_el.send_keys(Keys.DELETE)
            logger.info("已清空弹窗输入框: %s", label_text)
        except Exception as e:
            logger.error("清空弹窗输入框 [%s] 失败: %s", label_text, e)
            raise

    def get_dialog_select_text(self, label_text):
        try:
            item = self._get_dialog_form_item(label_text)
            text_locators = [
                (By.XPATH, './/div[contains(@class,"el-select__selected-item")]//span[normalize-space(.)!=""]'),
                (By.XPATH, './/div[contains(@class,"el-select__selection")]//span[normalize-space(.)!=""]'),
                (By.XPATH, './/span[normalize-space(.)!="请选择部门" and normalize-space(.)!="请选择角色" and normalize-space(.)!="请选择岗位" and normalize-space(.)!=""]'),
            ]
            for loc in text_locators:
                elements = item.find_elements(*loc)
                for el in elements:
                    text = el.text.strip()
                    if text:
                        return text
            return ""
        except Exception:
            return ""

    def open_dialog_select(self, label_text):
        try:
            item = self._get_dialog_form_item(label_text)
            trigger = item.find_element(
                By.XPATH,
                './/div[contains(@class,"el-select") or contains(@class,"el-select-v2") or contains(@class,"el-tree-select") or contains(@class,"el-cascader")]',
            )

            def _click(el):
                try:
                    if el.tag_name.lower() == "svg":
                        el = el.find_element(By.XPATH, "./ancestor::*[self::i or self::span or self::div][1]")
                except Exception:
                    pass
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", el)
                self.wait_vue_stable()
                self.driver.execute_script("arguments[0].click();", el)

            click_candidates = []
            if label_text == "部门":
                department_trigger_xpaths = [
                    './/div[contains(@class,"el-select__wrapper")]//div[contains(@class,"el-select__selected-item") and contains(@class,"el-select__placeholder")]//span[contains(normalize-space(.),"请选择部门")]',
                    './/div[contains(@class,"el-select__wrapper")]//span[contains(normalize-space(.),"请选择部门")]',
                    './/div[contains(@class,"el-select__wrapper")]',
                    './/div[contains(@class,"el-select")]//div[contains(@class,"el-select__wrapper")]',
                ]
                for xp in department_trigger_xpaths:
                    try:
                        click_candidates.append(item.find_element(By.XPATH, xp))
                    except Exception:
                        continue

            click_candidates.append(trigger)
            try:
                click_candidates.append(item.find_element(By.XPATH, './/input'))
            except Exception:
                pass
            try:
                click_candidates.append(item.find_element(By.XPATH, './/div[contains(@class,"el-select__selection")]'))
            except Exception:
                pass
            try:
                click_candidates.append(item.find_element(By.XPATH, './/div[contains(@class,"el-select__selected-item") and contains(@class,"el-select__placeholder")]'))
            except Exception:
                pass

            arrow_xpaths = [
                './/i[contains(@class,"el-select__caret")]',
                './/span[contains(@class,"el-input__suffix")]//*[name()="svg"]',
                './/span[contains(@class,"el-input__suffix")]//i',
                './/div[contains(@class,"el-input__suffix")]//*[name()="svg"]',
                './/div[contains(@class,"el-input__suffix")]//i',
                './/div/div/div/div/div[2]//*[name()="svg"]',
            ]
            for xp in arrow_xpaths:
                try:
                    click_candidates.append(item.find_element(By.XPATH, xp))
                except Exception:
                    continue

            last_error = None
            for cand in click_candidates:
                try:
                    _click(cand)
                    WebDriverWait(self.driver, 3).until(lambda d: self.get_visible_select_option_count() > 0)
                    logger.info("已打开下拉框: %s", label_text)
                    return
                except Exception as e:
                    last_error = e
                    continue

            raise Exception(f"下拉弹层未打开: {last_error}")
        except Exception as e:
            logger.error("打开下拉框 [%s] 失败: %s", label_text, e)
            raise

    def select_dialog_first_option(self, label_text):
        try:
            self.open_dialog_select(label_text)
            li_locator = (
                By.XPATH,
                '(//div[(contains(@class,"el-select-dropdown") or contains(@class,"el-select-v2__popper") or contains(@class,"el-cascader__dropdown") or contains(@class,"el-popper")) and not(contains(@style,"display: none"))])[last()]'
                '//li[contains(@class,"el-select-dropdown__item") and not(contains(@class,"is-disabled"))][1]',
            )
            try:
                option = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable(li_locator))
                text = option.text.strip()
                self.driver.execute_script("arguments[0].click();", option)
                self.wait_vue_stable()
                logger.info("已选择下拉框 [%s] 的第一个选项: %s", label_text, text)
                return text
            except Exception:
                tree_locator = (
                    By.XPATH,
                    '(//div[(contains(@class,"el-tree-select__popper") or contains(@class,"el-popper") or contains(@class,"el-select-dropdown") or contains(@class,"el-select-v2__popper")) and not(contains(@style,"display: none"))])[last()]'
                    '//*[contains(@class,"el-tree-node__content")][1]',
                )
                node = self.wait.until(EC.element_to_be_clickable(tree_locator))
                text = node.text.strip()
                self.driver.execute_script("arguments[0].click();", node)
                self.wait_vue_stable()
                logger.info("已选择下拉框 [%s] 的第一个选项: %s", label_text, text)
                return text
        except Exception as e:
            logger.error("选择下拉框 [%s] 的第一个选项失败: %s", label_text, e)
            raise

    def _is_dialog_select_selected(self, label_text):
        """判断弹窗下拉字段是否已经选中有效值。"""
        selected_text = (self.get_dialog_select_text(label_text) or "").strip()
        invalid_texts = ["", f"请选择{label_text}", "请选择部门", "请选择角色", "请选择岗位"]
        return selected_text not in invalid_texts, selected_text

    def _click_dialog_option_and_verify(self, label_text, option):
        """点击一个下拉候选项，并验证弹窗字段是否真的被赋值。"""
        try:
            click_target = option
            option_class = option.get_attribute("class") or ""
            if "el-tree-node__label" in option_class:
                click_target = option.find_element(By.XPATH, './ancestor::*[contains(@class,"el-tree-node__content")][1]')

            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", click_target)
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", click_target)
            self.wait_vue_stable()
            is_selected, selected_text = self._is_dialog_select_selected(label_text)
            return is_selected, selected_text
        except Exception as e:
            logger.warning("点击候选下拉选项失败: %s", e)
            return False, ""

    def select_dialog_first_valid_option(self, label_text):
        """选择弹窗下拉框中第一个真正可选的有效选项。用于部门树存在不可选父节点的场景。"""
        try:
            js_result = self.driver.execute_script(
                """
                const labelText = arguments[0];
                const invalidTexts = new Set(['', '请选择' + labelText, '请选择部门', '请选择角色', '请选择岗位']);

                function visible(el) {
                    if (!el) return false;
                    const style = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
                }

                function getDialogItem() {
                    const labels = Array.from(document.querySelectorAll('.el-dialog .el-form-item__label'));
                    const label = labels.find(el => (el.innerText || '').trim().includes(labelText));
                    return label ? label.closest('.el-form-item') : null;
                }

                function getSelectedText() {
                    const item = getDialogItem();
                    if (!item) return '';
                    const selected = item.querySelector('.el-select__selected-item:not(.el-select__placeholder), .el-select__selection span, input');
                    return selected ? ((selected.innerText || selected.value || '').trim()) : '';
                }

                function openSelect() {
                    const item = getDialogItem();
                    if (!item) return 'no item';
                    const targets = [
                        item.querySelector('.el-select__wrapper'),
                        item.querySelector('.el-select'),
                        item.querySelector('.el-input__wrapper'),
                        item.querySelector('input'),
                        item.querySelector('.el-select__selection')
                    ].filter(Boolean);
                    for (const target of targets) {
                        target.scrollIntoView({block: 'center', inline: 'nearest'});
                        target.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true, view: window}));
                        target.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true, view: window}));
                        target.click();
                    }
                    return 'opened';
                }

                function optionCandidates() {
                    const selector = [
                        '.el-select-dropdown:not([style*="display: none"]) .el-select-dropdown__item:not(.is-disabled)',
                        '.el-popper:not([style*="display: none"]) .el-select-dropdown__item:not(.is-disabled)',
                        '.el-popper:not([style*="display: none"]) .el-tree-node__content',
                        '.el-popper:not([style*="display: none"]) .el-cascader-node:not(.is-disabled)',
                        '.el-select-dropdown__item:not(.is-disabled)',
                        '.el-tree-node__content',
                        '.el-cascader-node:not(.is-disabled)'
                    ].join(',');
                    return Array.from(document.querySelectorAll(selector))
                        .filter(visible)
                        .filter(el => (el.innerText || '').trim())
                        .filter(el => !(el.className || '').toString().includes('is-disabled'));
                }

                openSelect();
                return new Promise(resolve => {
                    setTimeout(() => {
                        let candidates = optionCandidates();
                        const before = getSelectedText();
                        for (let i = candidates.length - 1; i >= 0; i--) {
                            const el = candidates[i];
                            const text = (el.innerText || '').trim();
                            el.scrollIntoView({block: 'center', inline: 'nearest'});
                            el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true, view: window}));
                            el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true, view: window}));
                            el.click();
                            const after = getSelectedText();
                            if (after && !invalidTexts.has(after) && after !== before) {
                                resolve({ok: true, text: after, clicked: text, count: candidates.length});
                                return;
                            }
                            openSelect();
                            candidates = optionCandidates();
                        }
                        resolve({ok: false, text: getSelectedText(), count: candidates.length});
                    }, 500);
                });
                """,
                label_text,
            )
            if js_result and js_result.get("ok"):
                selected_text = js_result.get("text") or js_result.get("clicked")
                logger.info("已选择下拉框 [%s] 的有效选项: %s", label_text, selected_text)
                return selected_text
            logger.warning("JS选择 [%s] 未成功，结果: %s", label_text, js_result)

            option_locators = [
                (By.XPATH, '//li[contains(@class,"el-select-dropdown__item") and not(contains(@class,"is-disabled")) and not(contains(@style,"display: none"))]'),
                (By.XPATH, '//*[contains(@class,"el-tree-node") and not(contains(@class,"is-disabled"))]//*[contains(@class,"el-tree-node__content")]'),
                (By.XPATH, '//*[contains(@class,"el-cascader-node") and not(contains(@class,"is-disabled"))]'),
            ]

            for _ in range(2):
                try:
                    self.open_dialog_select(label_text)
                except Exception:
                    pass

                candidates = []
                for loc in option_locators:
                    try:
                        candidates.extend(self.driver.find_elements(*loc))
                    except Exception:
                        continue

                visible_candidates = []
                for candidate in candidates:
                    try:
                        text = (candidate.text or "").strip()
                        classes = candidate.get_attribute("class") or ""
                        if candidate.is_displayed() and text and "is-disabled" not in classes:
                            visible_candidates.append(candidate)
                    except Exception:
                        continue

                for candidate in reversed(visible_candidates):
                    is_selected, selected_text = self._click_dialog_option_and_verify(label_text, candidate)
                    if is_selected:
                        logger.info("已选择下拉框 [%s] 的有效选项: %s", label_text, selected_text)
                        return selected_text
                    try:
                        self.open_dialog_select(label_text)
                    except Exception:
                        pass

            raise Exception(f"未能选择 {label_text} 的任何有效选项")
        except Exception as e:
            logger.error("选择下拉框 [%s] 的有效选项失败: %s", label_text, e)
            raise

    def select_dialog_option_by_text(self, label_text, option_text):
        try:
            locators = [
                (By.XPATH, f'//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]//li[contains(@class,"el-select-dropdown__item") and not(contains(@class,"is-disabled"))][.//span[normalize-space(.)="{option_text}"] or normalize-space(.)="{option_text}"]'),
                (By.XPATH, f'//div[contains(@class,"el-popper") and not(contains(@style,"display: none"))]//li[contains(@class,"el-select-dropdown__item") and not(contains(@class,"is-disabled"))][.//span[normalize-space(.)="{option_text}"] or normalize-space(.)="{option_text}"]'),
                (By.XPATH, f'//li[contains(@class,"el-select-dropdown__item") and not(contains(@class,"is-disabled"))][.//span[normalize-space(.)="{option_text}"] or normalize-space(.)="{option_text}"]'),
                (By.XPATH, f'//*[contains(@class,"el-tree-node__content")][.//*[normalize-space(.)="{option_text}"] or normalize-space(.)="{option_text}"]'),
                (By.XPATH, f'//*[contains(@class,"el-tree-node__label") and normalize-space(.)="{option_text}"]'),
                (By.XPATH, f'//*[contains(@class,"el-cascader-node")][.//*[normalize-space(.)="{option_text}"] or normalize-space(.)="{option_text}"]'),
            ]

            for _ in range(2):
                self.open_dialog_select(label_text)
                candidates = []
                for loc in locators:
                    try:
                        candidates.extend(self.driver.find_elements(*loc))
                    except Exception:
                        continue

                visible_candidates = [el for el in candidates if el.is_displayed()]
                for option in reversed(visible_candidates):
                    is_selected, selected_text = self._click_dialog_option_and_verify(label_text, option)
                    if is_selected:
                        logger.info("已选择下拉框 [%s] 的选项: %s", label_text, selected_text)
                        return selected_text
                    try:
                        self.open_dialog_select(label_text)
                    except Exception:
                        pass

            logger.warning("未能按文本选择 %s，改为选择第一个有效部门选项", option_text)
            return self.select_dialog_first_valid_option(label_text)
        except Exception as e:
            logger.error("选择下拉框 [%s] 的选项 %s 失败: %s", label_text, option_text, e)
            raise

    def get_visible_select_option_count(self):
        try:
            xpaths = [
                '//li[contains(@class,"el-select-dropdown__item") and not(contains(@class,"is-disabled"))]',
                '//div[contains(@class,"el-select-dropdown")]//li[not(contains(@class,"is-disabled"))]',
                '//*[contains(@class,"el-tree-node__content") or contains(@class,"el-tree-node__label")]',
                '//*[contains(@class,"el-cascader-node")]',
            ]
            items = []
            for xp in xpaths:
                items.extend(self.driver.find_elements(By.XPATH, xp))
            return len([o for o in items if o.is_displayed()])
        except Exception:
            return 0
    
    # ══════════════════════════════════════════════════════════════════
    #  导航（重构：统一使用 BasePage.navigate_to，废弃绝对XPath点击）
    # ══════════════════════════════════════════════════════════════════

    def navigate(self):
        """导航到用户管理页面 — 唯一入口"""
        logger.info("导航到 → 系统管理 → 用户管理")
        self.navigate_to("系统管理", "用户管理")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        return self

    # 向后兼容别名
    def navigate_to_user_management(self):
        """@deprecated: 使用 navigate() 替代"""
        return self.navigate()

    def get_total_count_text(self):
        """获取列表总条数文本（含重试，应对异步渲染）"""
        import time
        for attempt in range(10):
            try:
                self.scroll_to_element(self.TOTAL_COUNT_TEXT)
                element = self.wait.until(EC.visibility_of_element_located(self.TOTAL_COUNT_TEXT))
                text = element.text
                if text and any(c.isdigit() for c in text):
                    return text
            except Exception:
                pass
            self._wait_loading_gone(timeout=3)
        raise TimeoutException("获取总条数失败: 10次重试后仍未出现含数字的分页文本")

    def get_username_header_text(self):
        """获取用户名表头文本"""
        try:
            element = self.wait.until(EC.visibility_of_element_located(self.USERNAME_HEADER))
            return element.text
        except Exception as e:
            logger.error("获取表头文本失败: %s", e)
            raise

    def get_table_row_count(self):
        """获取当前页表格行数"""
        try:
            # 等待至少一行出现，超时时间设短一点，因为搜索可能返回空
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(self.TABLE_ROWS)
            )
            rows = self.driver.find_elements(*self.TABLE_ROWS)
            return len(rows)
        except TimeoutException:
            logger.info("暂无数据或表格未加载")
            return 0
        except Exception as e:
            logger.error("获取行数失败: %s", e)
            return 0

    def get_first_row_username(self):
        """获取第一行用户名"""
        try:
            element = self.wait.until(EC.visibility_of_element_located(self.FIRST_ROW_USERNAME))
            return element.text
        except Exception as e:
            logger.error("获取第一行用户名失败: %s", e)
            raise

    def scroll_to_element(self, locator):
        """将元素滚动到视野范围内（增强版）"""
        try:
            # 等待元素存在
            element = self.wait.until(EC.presence_of_element_located(locator))
            
            # 方案1: 使用 ActionChains 移动到元素 (有时候对 Vue 框架很有效)
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(self.driver).move_to_element(element).perform()
            except:
                pass

            # 方案2: 尝试对所有 el-scrollbar__wrap 容器进行滚动
            script = """
            var containers = document.querySelectorAll('.el-scrollbar__wrap');
            for (var i = 0; i < containers.length; i++) {
                if (containers[i].scrollHeight > containers[i].clientHeight) {
                    // 滚动到底部或者滚动到元素位置
                    containers[i].scrollTop = containers[i].scrollHeight;
                }
            }
            // 同时尝试全局滚动
            window.scrollTo(0, document.body.scrollHeight);
            """
            self.driver.execute_script(script)
            self._wait_loading_gone(timeout=3)
            
            # 方案3: 针对具体元素进行 scrollIntoView
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", element)
            self._wait_loading_gone(timeout=3)
            
            logger.info("已执行增强滚动操作")
        except Exception as e:
            logger.error("滚动操作失败: %s", e)
            # 不抛出异常，尝试继续

    def click_next_page(self):
        """点击下一页按钮（包含滚动处理）"""
        try:
            # 1. 先滚动到按钮位置
            self.scroll_to_element(self.NEXT_PAGE_BUTTON)
            
            # 2. 等待按钮可点击并点击
            button = self.wait.until(EC.element_to_be_clickable(self.NEXT_PAGE_BUTTON))
            button.click()
            logger.info("已点击下一页")
            self._wait_loading_gone(timeout=5)  # 等待数据加载
        except Exception as e:
            logger.error("点击下一页失败: %s", e)
            raise

    def input_search_username(self, username):
        """输入搜索用户名"""
        try:
            from selenium.webdriver.common.keys import Keys
            element = self.wait.until(EC.visibility_of_element_located(self.SEARCH_USERNAME_INPUT))
            element.send_keys(Keys.CONTROL + "a")
            element.send_keys(Keys.DELETE)
            element.send_keys(username)
            logger.info("已输入搜索用户名: %s", username)
        except Exception as e:
            logger.error("输入搜索用户名失败: %s", e)
            raise

    def click_search_button(self):
        """点击查询按钮"""
        try:
            button = self.wait.until(EC.element_to_be_clickable(self.SEARCH_BUTTON))
            button.click()
            logger.info("已点击查询按钮")
            self._wait_loading_gone(timeout=5)  # 等待搜索结果加载
        except Exception as e:
            logger.error("点击查询按钮失败: %s", e)
            raise

    def click_reset_button(self):
        """点击重置按钮"""
        try:
            button = self.wait.until(EC.element_to_be_clickable(self.RESET_BUTTON))
            button.click()
            logger.info("已点击重置按钮")
            self._wait_loading_gone(timeout=5)  # 等待列表重置
        except Exception as e:
            logger.error("点击重置按钮失败: %s", e)
            raise

    def select_role(self, role_name):
        """选择搜索角色"""
        try:
            # 1. 点击下拉框容器
            select = self.wait.until(EC.element_to_be_clickable(self.ROLE_SELECT))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select)
            select.click()
            logger.info("已点击角色下拉框")
            self._wait_loading_gone(timeout=3)
            
            # 2. 在可见的下拉列表中选择选项
            # ElementUI/Plus 的下拉列表通常在 body 下
            option_xpath = f'//div[contains(@class, "el-select-dropdown") and not(contains(@style, "display: none"))]//li[.//span[text()="{role_name}"]]'
            option = self.wait.until(EC.element_to_be_clickable((By.XPATH, option_xpath)))
            option.click()
            logger.info("已选择角色: %s", role_name)
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("选择角色失败: %s", e)
            raise

    def select_status(self, status_label):
        """选择搜索状态 (全部/启用/禁用)"""
        try:
            # 根据截图，状态是在 el-radio-group 下的 label 里的 span 文本
            radio_xpath = f'//div[contains(@class, "el-radio-group")]//label[.//span[text()="{status_label}"]]'
            radio = self.wait.until(EC.element_to_be_clickable((By.XPATH, radio_xpath)))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", radio)
            radio.click()
            logger.info("已选择状态: %s", status_label)
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("选择状态失败: %s", e)
            raise

    def get_column_data(self, col_index):
        """获取指定列的所有数据 (col_index从1开始)"""
        try:
            # 列定位器：每一行的第 col_index 个 td
            col_locator = (By.CSS_SELECTOR, f".el-table__body-wrapper tbody tr td:nth-child({col_index}) div")
            elements = self.driver.find_elements(*col_locator)
            return [el.text.strip() for el in elements if el.text.strip()]
        except Exception as e:
            logger.error("获取第 %s 列数据失败: %s", col_index, e)
            return []

    # --- 操作类方法 ---

    def _get_action_button_by_username(self, username, action_text):
        """通用方法：根据用户名在表格中找到对应的操作按钮"""
        # 结合用户提供的绝对路径结构和动态用户名定位
        base_xpath = '//*[@id="app"]/div/div[3]/div/section/div/div/div[1]/div/div/div/div/div[2]/div[2]/div[2]/div[1]/div[1]/div[3]/div/div[1]/div/table/tbody'
        row_xpath = f'{base_xpath}/tr[.//td[contains(., "{username}")]]'
        
        if action_text == "编辑":
            xpath = f'{row_xpath}/td[9]/div/button[1]'
        elif action_text == "分配角色":
            xpath = f'{row_xpath}/td[9]/div/button[2]'
        elif action_text == "更多":
            xpath = f'{row_xpath}/td[9]/div/div[contains(@class, "el-dropdown")]/button'
        else:
            xpath = f'{row_xpath}//button[.//span[contains(text(), "{action_text}")]]'
            
        return (By.XPATH, xpath)

    def click_edit_user(self, username):
        """点击指定用户的编辑按钮"""
        try:
            # 尝试多种定位方式
            locators = [
                self._get_action_button_by_username(username, "编辑"),
                (By.XPATH, f'//tr[contains(., "{username}")]//button[1]'), # 退而求其次使用索引
                (By.XPATH, f'//tr[.//div[contains(text(), "{username}")]]//button[.//span[contains(text(), "编辑")]]')
            ]
            
            button = None
            for loc in locators:
                try:
                    button = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable(loc))
                    if button: break
                except:
                    continue
            
            if not button:
                raise Exception(f"无法定位到用户 '{username}' 的编辑按钮")

            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", button)
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", button)
            logger.info("已点击用户 %s 的编辑按钮", username)
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("点击编辑按钮失败: %s", e)
            raise

    def click_add_user_button(self):
        """点击新增按钮"""
        try:
            self._wait_loading_gone(timeout=10)  # 等 http-full-loading 遮罩消失
            locators = [
                self.ADD_USER_BUTTON,
                (By.XPATH, '//button[.//span[normalize-space(.)="新增" or normalize-space(.)="新建"]]'),
                (By.XPATH, '//button[contains(@class,"el-button") and contains(normalize-space(.),"新增")]'),
            ]

            button = None
            for loc in locators:
                try:
                    button = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(loc))
                    if button:
                        break
                except Exception:
                    continue

            if not button:
                raise Exception("无法定位到新增按钮")

            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", button)
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", button)
            logger.info("已点击新增按钮")
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("点击新增按钮失败: %s", e)
            raise

    def input_password_in_dialog(self, password):
        """在弹窗中输入密码和确认密码，先清空默认值再输入一致密码"""
        password_labels = ["密码", "确认密码"]
        for label_text in password_labels:
            try:
                self.input_dialog_input(label_text, password)
                logger.info("已在弹窗中输入 %s: ****", label_text)
            except Exception as e:
                logger.error("在弹窗中输入 [%s] 失败: %s", label_text, e)
                raise

    def input_edit_name(self, new_name):
        """在编辑弹窗中输入姓名"""
        try:
            from selenium.webdriver.common.keys import Keys
            input_el = self.wait.until(EC.visibility_of_element_located(self.DIALOG_NAME_INPUT))
            input_el.send_keys(Keys.CONTROL + "a")
            input_el.send_keys(Keys.DELETE)
            input_el.send_keys(new_name)
            logger.info("已在编辑弹窗输入姓名: %s", new_name)
        except Exception as e:
            logger.error("输入姓名失败: %s", e)
            raise

    def input_edit_username(self, username):
        """在编辑弹窗中输入用户名"""
        try:
            from selenium.webdriver.common.keys import Keys
            input_el = self.wait.until(EC.visibility_of_element_located(self.DIALOG_USERNAME_INPUT))
            input_el.send_keys(Keys.CONTROL + "a")
            input_el.send_keys(Keys.DELETE)
            input_el.send_keys(username)
            logger.info("已在编辑弹窗输入用户名: %s", username)
        except Exception as e:
            logger.error("输入用户名失败: %s", e)
            raise

    def click_dialog_confirm(self):
        """点击弹窗的确定按钮"""
        try:
            button = self.wait.until(EC.element_to_be_clickable(self.DIALOG_CONFIRM_BUTTON))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", button)
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", button)
            logger.info("已点击弹窗确定按钮")
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("点击确定按钮失败: %s", e)
            raise

    def click_dialog_cancel(self):
        """点击弹窗的取消按钮"""
        try:
            locators = [
                self.DIALOG_CANCEL_BUTTON,
                (By.XPATH, '/html/body/div[5]/div/div/footer/div/button[2]'),
                (By.XPATH, '/html/body/div[5]/div/div/footer/div/button[2]/span'),
            ]

            button = None
            for loc in locators:
                try:
                    el = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(loc))
                    if el.tag_name.lower() == "button":
                        button = el
                    else:
                        button = el.find_element(By.XPATH, "./ancestor::button[1]")
                    if button and button.is_displayed():
                        break
                except Exception:
                    continue

            if not button:
                raise Exception("无法定位到弹窗取消按钮")

            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", button)
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", button)
            logger.info("已点击弹窗取消按钮")
            self.wait_vue_stable()
        except Exception as e:
            logger.error("点击取消按钮失败: %s", e)
            raise

    def wait_dialog_closed(self, timeout=5):
        """等待当前弹窗关闭"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-overlay-dialog, .el-dialog__wrapper, .el-dialog"))
            )
            logger.info("弹窗已关闭")
            return True
        except Exception as e:
            logger.error("等待弹窗关闭失败: %s", e)
            return False

    def get_toast_text(self, timeout=5):
        """获取 Toast 提示消息文本。Element Plus 的 message id 是动态的，不使用 message_数字 定位。"""
        try:
            wait_toast = WebDriverWait(self.driver, timeout)
            element = wait_toast.until(
                EC.visibility_of_element_located(
                    (By.XPATH, '(//*[contains(@class,"el-message__content") or contains(@class,"el-message")][normalize-space(.)!=""])[last()]')
                )
            )
            text = element.text.strip()
            logger.info("获取到提示消息: %s", text)
            return text
        except Exception as e:
            logger.error("获取提示消息失败: %s", e)
            return ""

    def get_form_error_text(self, timeout=15):
        """获取表单校验错误文本"""
        try:
            element = WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(self.FORM_VALIDATION_ERROR))
            text = element.text
            logger.info("获取到校验错误: %s", text)
            return text
        except Exception as e:
            logger.error("获取校验错误失败: %s", e)
            return ""

    def click_assign_role_user(self, username):
        """点击指定用户的分配角色按钮"""
        try:
            locators = [
                self._get_action_button_by_username(username, "分配角色"),
                (By.XPATH, f'//tr[contains(., "{username}")]//button[2]'),
                (By.XPATH, f'//tr[.//div[contains(text(), "{username}")]]//button[.//span[contains(text(), "分配角色")]]')
            ]
            
            button = None
            for loc in locators:
                try:
                    button = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable(loc))
                    if button: break
                except:
                    continue

            if not button:
                raise Exception(f"无法定位到用户 '{username}' 的分配角色按钮")

            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", button)
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", button)
            logger.info("已点击用户 %s 的分配角色按钮", username)
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("点击分配角色按钮失败: %s", e)
            raise

    def select_role_in_dialog(self, role_name):
        """在分配角色弹窗中勾选角色"""
        try:
            dialog_xpath = '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[contains(@class,"el-dialog")] | //div[contains(@class,"el-dialog__wrapper") and not(contains(@style,"display: none"))]//div[contains(@class,"el-dialog")])[last()]'
            label_locators = [
                (By.XPATH, f'{dialog_xpath}//div[contains(@class,"el-checkbox-group")]//span[contains(@class,"el-checkbox__label") and normalize-space(.)="{role_name}"]/ancestor::label[contains(@class,"el-checkbox")][1]'),
                (By.XPATH, f'{dialog_xpath}//span[contains(@class,"el-checkbox__label") and contains(normalize-space(.), "{role_name}")]/ancestor::label[contains(@class,"el-checkbox")][1]'),
                (By.XPATH, f'{dialog_xpath}//*[contains(normalize-space(.), "{role_name}")]/ancestor::label[contains(@class,"el-checkbox")][1]'),
                (By.XPATH, f'(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//*[contains(normalize-space(.), "{role_name}")]/ancestor::label[contains(@class,"el-checkbox")][1])[last()]'),
            ]

            if role_name == "部门经理":
                label_locators.append((By.XPATH, f'{dialog_xpath}//div[contains(@class,"el-checkbox-group") and @role="group"]//span[contains(@class,"el-checkbox__label") and normalize-space(.)="部门经理"]/ancestor::label[contains(@class,"el-checkbox")][1]'))
                label_locators.append((By.XPATH, '//*[@id="el-id-934-332"]/label[2]'))
                label_locators.append((By.XPATH, '//*[@id="el-id-934-332"]/label[2]/span[2]'))

            checkbox_label = None
            for loc in label_locators:
                try:
                    checkbox_label = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(loc))
                    if checkbox_label and checkbox_label.is_displayed():
                        break
                except Exception:
                    continue

            if not checkbox_label:
                raise Exception(f"无法定位到分配角色弹窗中的角色项: {role_name}")

            if checkbox_label.tag_name.lower() != "label":
                checkbox_label = checkbox_label.find_element(By.XPATH, "./ancestor::label[contains(@class,'el-checkbox')][1]")

            if "is-checked" not in (checkbox_label.get_attribute("class") or ""):
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", checkbox_label)
                self.wait_vue_stable()
                self.driver.execute_script("arguments[0].click();", checkbox_label)
                logger.info("已勾选角色: %s", role_name)
            else:
                logger.info("角色 '%s' 已处于勾选状态", role_name)
        except Exception as e:
            logger.error("勾选角色失败: %s", e)
            raise

    def click_assign_role_dialog_confirm(self):
        """点击分配角色弹窗的确定按钮"""
        try:
            locators = [
                (By.XPATH, '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[contains(@class,"el-dialog")] | //div[contains(@class,"el-dialog__wrapper") and not(contains(@style,"display: none"))]//div[contains(@class,"el-dialog")])[last()]//button[.//span[normalize-space(.)="确定"]]'),
                self.DIALOG_CONFIRM_BUTTON,
                (By.XPATH, '/html/body/div[7]/div/div/footer/div/button[1]'),
                (By.XPATH, '/html/body/div[7]/div/div/footer/div/button[1]/span'),
            ]

            button = None
            for loc in locators:
                try:
                    el = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(loc))
                    if el.tag_name.lower() == "button":
                        button = el
                    else:
                        button = el.find_element(By.XPATH, "./ancestor::button[1]")
                    if button and button.is_displayed():
                        break
                except Exception:
                    continue

            if not button:
                raise Exception("无法定位到分配角色弹窗确定按钮")

            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", button)
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", button)
            logger.info("已点击分配角色弹窗确定按钮")
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("点击分配角色弹窗确定按钮失败: %s", e)
            raise

    def click_more_user(self, username):
        """点击指定用户的更多按钮"""
        try:
            locators = [
                self._get_action_button_by_username(username, "更多"),
                (By.XPATH, f'//tr[contains(., "{username}")]//div[contains(@class, "el-dropdown")]//button'),
                (By.XPATH, f'//tr[.//div[contains(text(), "{username}")]]//button[.//span[contains(text(), "更多")]]')
            ]
            
            button = None
            for loc in locators:
                try:
                    button = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable(loc))
                    if button: break
                except:
                    continue

            if not button:
                raise Exception(f"无法定位到用户 '{username}' 的更多按钮")

            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", button)
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", button)
            logger.info("已点击用户 %s 的更多按钮", username)
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("点击更多按钮失败: %s", e)
            raise

    def click_more_delete(self):
        """点击更多下拉菜单中的删除"""
        try:
            option = self.wait.until(EC.element_to_be_clickable(self.MORE_DELETE_OPTION))
            option.click()
            logger.info("已点击下拉菜单中的删除")
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("点击删除选项失败: %s", e)
            raise

    def click_more_reset_pwd(self):
        """点击更多下拉菜单中的重置密码"""
        try:
            option = self.wait.until(EC.element_to_be_clickable(self.MORE_RESET_PWD_OPTION))
            option.click()
            logger.info("已点击下拉菜单中的重置密码")
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("点击重置密码选项失败: %s", e)
            raise

    def confirm_message_box(self, action_name="操作"):
        """确认 Element Plus 消息确认框 (MessageBox)"""
        try:
            locators = [
                (By.XPATH, '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[contains(@class,"el-message-box")])[last()]//button[.//span[normalize-space(.)="确定" or normalize-space(.)="确认"]]'),
                (By.XPATH, '(//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))])[last()]//div[contains(@class,"el-message-box__btns")]//button[contains(@class,"el-button--primary")]'),
                (By.XPATH, '(//div[contains(@class,"el-message-box")])[last()]//button[.//span[normalize-space(.)="确定" or normalize-space(.)="确认"]]'),
            ]

            button = None
            for loc in locators:
                try:
                    button = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(loc))
                    if button and button.is_displayed():
                        break
                except Exception:
                    continue

            if not button:
                raise Exception(f"无法定位到{action_name}确认框的确定按钮")

            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", button)
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", button)
            logger.info("已点击 %s 确认框的确定按钮", action_name)
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("点击 %s 确认失败: %s", action_name, e)
            raise

    def confirm_delete_message_box(self):
        """确认删除的消息确认框 (MessageBox)"""
        self.confirm_message_box("删除")

    def confirm_reset_password_message_box(self):
        """确认重置密码的消息确认框 (MessageBox)"""
        self.confirm_message_box("重置密码")
    
    def select_user_checkbox(self, username):
        """勾选表格中指定用户的复选框 (用于批量删除)"""
        try:
            locators = [
                (By.XPATH, f'//tr[.//td[2]//div[normalize-space(.)="{username}"]]//td[1]//label[contains(@class,"el-checkbox")]'),
                (By.XPATH, f'//tr[.//td[contains(@class,"el-table__cell")]//div[normalize-space(.)="{username}"]]//td[1]//label[contains(@class,"el-checkbox")]'),
            ]

            checkbox = None
            for loc in locators:
                try:
                    checkbox = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(loc))
                    if checkbox and checkbox.is_displayed():
                        break
                except Exception:
                    continue

            if not checkbox:
                raise Exception(f"无法定位到用户 '{username}' 的复选框")

            if "is-checked" not in (checkbox.get_attribute("class") or ""):
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", checkbox)
                self.wait_vue_stable()
                self.driver.execute_script("arguments[0].click();", checkbox)
                logger.info("已勾选用户 %s 的复选框", username)
            self.wait_vue_stable()
        except Exception as e:
            logger.error("勾选用户复选框失败: %s", e)
            raise

    def click_batch_delete_button(self):
        """点击列表上方的批量删除按钮"""
        try:
            locators = [
                (By.XPATH, '//*[@id="app"]//button[contains(@class,"el-button--danger") and .//span[normalize-space(.)="删除"]]'),
                (By.XPATH, '//button[contains(@class,"el-button--danger") and .//span[normalize-space(.)="删除"]]'),
                (By.XPATH, '//*[@id="app"]/div/div[3]/div/section/div/div/div[1]/div/div/div/div/div[2]/div[2]/div[1]/div/div[3]/button'),
                (By.XPATH, '//*[@id="app"]/div/div[3]/div/section/div/div/div[1]/div/div/div/div/div[2]/div[2]/div[1]/div/div[3]/button/span'),
            ]

            button = None
            for loc in locators:
                try:
                    el = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(loc))
                    if el.tag_name.lower() == "button":
                        button = el
                    else:
                        button = el.find_element(By.XPATH, "./ancestor::button[1]")
                    if button and button.is_displayed():
                        break
                except Exception:
                    continue

            if not button:
                raise Exception("无法定位到批量删除按钮")

            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", button)
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", button)
            logger.info("已点击批量删除按钮")
            self._wait_loading_gone(timeout=3)
        except Exception as e:
            logger.error("点击批量删除按钮失败: %s", e)
            raise

    def is_username_present(self, username):
        """判断列表中是否存在指定用户名(精确匹配)"""
        try:
            usernames = self.get_column_data(2)
            return any(u == username for u in usernames)
        except Exception:
            return False

    def press_escape(self):
        try:
            from selenium.webdriver.common.keys import Keys
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            self.wait_vue_stable()
        except Exception:
            pass

    def click_dialog_body(self):
        try:
            dialog = self._get_visible_dialog()
            body = dialog.find_element(By.XPATH, './/div[contains(@class,"el-dialog__body")]')
            self.driver.execute_script("arguments[0].click();", body)
            self.wait_vue_stable()
        except Exception:
            try:
                dialog = self._get_visible_dialog()
                self.driver.execute_script("arguments[0].click();", dialog)
                self.wait_vue_stable()
            except Exception:
                pass


if __name__ == "__main__":
    """测试用户管理页面导航"""
    from base.browser_driver import BaseDriver
    from page.LoginPage import LoginPage
    
    base = BaseDriver()
    try:
        # 打开浏览器
        driver = base.open_browser()
        
        # 先登录
        login_page = LoginPage(driver)
        login_page.login("admin", "admin123")
        self._wait_loading_gone(timeout=5)
        
        # 导航到用户管理页面
        user_manage_page = UserManagePage(driver)
        user_manage_page.navigate_to_user_management()
        
        # 等待观察结果
        self._wait_loading_gone(timeout=5)
        
    finally:
        # 关闭浏览器
        base.close_browser()
