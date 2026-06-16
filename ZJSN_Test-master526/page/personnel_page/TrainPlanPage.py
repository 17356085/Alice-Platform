"""培训计划管理页面操作类"""
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from base.base_page import BasePage
from config import TIMEOUT_CONFIG

logger = logging.getLogger(__name__)


class TrainPlanPage(BasePage):
    """培训计划管理页面操作"""

    # ==================== 导航定位 ====================
    TRAIN_PLAN_MANAGEMENT = (By.XPATH, '//li[contains(@class,"el-menu-item")]//span[normalize-space(.)="培训计划"]')
    COURSE_MANAGEMENT = (By.XPATH, '//li[contains(@class,"el-menu-item")]//span[normalize-space(.)="课程管理"]')

    # ==================== 搜索区域 ====================
    SEARCH_NAME_INPUT = (By.CSS_SELECTOR, 'input[placeholder*="计划名称"]')
    SEARCH_BUTTON = (By.XPATH, '//button[.//span[contains(normalize-space(.),"查询") or contains(normalize-space(.),"搜索")]]')
    RESET_BUTTON = (By.XPATH, '//button[.//span[contains(normalize-space(.),"重置")]]')

    # 搜索下拉框（培训类型 / 状态 / 发布状态）
    SEARCH_TYPE_SELECT = (By.CSS_SELECTOR, '.el-form .el-select:nth-of-type(1) .el-select__wrapper')
    SEARCH_STATUS_SELECT = (By.CSS_SELECTOR, '.el-form .el-select:nth-of-type(2) .el-select__wrapper')
    SEARCH_PUBLISH_SELECT = (By.CSS_SELECTOR, '.el-form .el-select:nth-of-type(3) .el-select__wrapper')

    # ==================== 表格 ====================
    TABLE_COLUMN_HEADERS = (By.CSS_SELECTOR, '.el-table__header-wrapper th .cell')

    # 表格列（按索引，用于获取单元格数据）
    COL_PLAN_NAME = 1
    COL_TRAIN_TYPE = 2
    COL_TARGET = 3
    COL_TIME_RANGE = 4
    COL_PRINCIPAL = 5
    COL_COURSES = 6
    COL_STATUS = 7
    COL_PUBLISH_STATUS = 8
    COL_OPERATIONS = 9

    # ==================== 分页 ====================
    PAGE_SIZE_SELECT = (By.CSS_SELECTOR, '.el-pagination .el-select__wrapper')
    NEXT_PAGE_BUTTON = (By.CSS_SELECTOR, '.el-pagination .btn-next')
    PREV_PAGE_BUTTON = (By.CSS_SELECTOR, '.el-pagination .btn-prev')
    PAGE_BUTTONS = (By.XPATH, '//div[contains(@class,"el-pagination")]//button[not(contains(@class,"btn-next")) and not(contains(@class,"btn-prev")) and not(@disabled)]')
    CURRENT_PAGE = (By.XPATH, '//div[contains(@class,"el-pagination")]//button[contains(@class,"is-active") or contains(@class,"active")]')
    PAGE_SIZE_OPTION = '//li[contains(@class,"el-select-dropdown__item") and contains(., "{size}")]'

    # ==================== 新增 / 编辑弹窗 ====================
    ADD_BUTTON = (By.XPATH, '//button[.//span[contains(normalize-space(.),"新增培训计划") or contains(normalize-space(.),"新增")]]')
    DIALOG_TITLE = (By.CSS_SELECTOR, '.el-dialog:not([style*="display: none"]) .el-dialog__title')

    SAVE_BUTTON = (By.CSS_SELECTOR, '.el-dialog:not([style*="display: none"]) .el-button--primary')
    CANCEL_BUTTON = (By.XPATH, '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//*[contains(@class,"el-dialog__footer")]//button[.//span[contains(text(),"取消")]]')

    # 关联课程 — 打开课程选择弹窗的按钮/区域
    COURSE_SELECT_TRIGGER = (By.XPATH, '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[contains(@class,"el-button") and (.//span[contains(text(),"选择课程") or contains(text(),"关联课程") or contains(text(),"添加")])]')
    COURSE_SELECT_DIALOG = (By.XPATH, '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[contains(@class,"el-dialog") and (.//*[contains(text(),"选择课程") or contains(text(),"课程列表")])])[last()]')
    COURSE_SELECT_SEARCH = (By.XPATH, '//div[contains(@class,"el-dialog") and (.//*[contains(text(),"选择课程") or contains(text(),"课程列表") or contains(text(),"关联课程")])]//input[contains(@placeholder,"搜索") or contains(@placeholder,"课程名称")]')
    COURSE_SELECT_ROW = (By.XPATH, '//div[contains(@class,"el-dialog") and (.//*[contains(text(),"选择课程") or contains(text(),"课程列表") or contains(text(),"关联课程")])]//tr[contains(@class,"el-table__row")][.//*[contains(text(),"{course_name}")]]')
    COURSE_SELECT_ROW_CHECKBOX = (By.XPATH, '//div[contains(@class,"el-dialog") and (.//*[contains(text(),"选择课程") or contains(text(),"课程列表") or contains(text(),"关联课程")])]//tr[contains(@class,"el-table__row")]//label[contains(@class,"el-checkbox")]')
    COURSE_SELECT_CONFIRM = (By.XPATH, '//div[contains(@class,"el-dialog") and (.//*[contains(text(),"选择课程") or contains(text(),"课程列表") or contains(text(),"关联课程")])]//*[contains(@class,"el-dialog__footer")]//button[contains(@class,"el-button--primary")]')
    COURSE_SELECT_CANCEL = (By.XPATH, '//div[contains(@class,"el-dialog") and (.//*[contains(text(),"选择课程") or contains(text(),"课程列表") or contains(text(),"关联课程")])]//*[contains(@class,"el-dialog__footer")]//button[.//span[contains(text(),"取消")]]')

    # 日期输入框 — Element Plus date-picker input
    DATE_INPUT = (By.XPATH, '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//div[contains(@class,"el-form-item")][.//label[contains(text(),"{label}")]]//input[contains(@class,"el-date") or contains(@placeholder,"选择") or contains(@placeholder,"YYYY")]')

    # ==================== 操作按钮（表格行内） ====================
    TABLE_VIEW_BUTTON = (By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[contains(text(),"查看")]]')
    TABLE_EDIT_BUTTON = (By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[contains(text(),"编辑")]]')
    TABLE_DELETE_BUTTON = (By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[contains(text(),"删除")]]')
    TABLE_PUBLISH_BUTTON = (By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[contains(text(),"发布")]]')

    def __init__(self, driver):
        super().__init__(driver, timeout=TIMEOUT_CONFIG.get("explicit_wait", 10))
        self.logger = logging.getLogger(__name__)

    # ==================== 通用操作 ====================

    def _click_js(self, locator):
        """点击元素，优先原生点击（触发 Vue 事件），失败则 JS 兜底"""
        el = self.wait.until(EC.presence_of_element_located(locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'nearest'});", el)
        self.wait_vue_stable()
        try:
            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(locator))
            el.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", el)
        return el

    def _get_visible_dialog(self, dialog_title=None):
        """获取当前可见的 Element Plus 弹窗，可选指定弹窗标题"""
        if not dialog_title:
            dialog_title = "添加培训计划"

        locator = (
            By.XPATH,
            f'//div[contains(@class,"el-dialog") and not(contains(@style,"display: none")) and .//*[contains(text(),"{dialog_title}")]]'
        )
        try:
            dialog = self.wait.until(EC.visibility_of_element_located(locator))
            return dialog
        except Exception:
            pass

        locator = (
            By.XPATH,
            '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]'
            '//div[contains(@class,"el-dialog")]'
            ' | //div[contains(@class,"el-dialog__wrapper") and not(contains(@style,"display: none"))]'
            '//div[contains(@class,"el-dialog")])[last()]'
        )

        try:
            dialog = self.wait.until(EC.visibility_of_element_located(locator))
            try:
                title = dialog.find_element(By.XPATH, './/*[contains(@class,"el-dialog__title")]').text.strip()
                logger.info("当前定位到的弹窗标题: '%s'", title)
            except Exception:
                pass
            return dialog
        except Exception as e:
            logger.warning("\n===== 弹窗定位失败，当前页面所有弹窗 =====")
            all_dialogs = self.driver.find_elements(By.XPATH, '//div[contains(@class,"el-dialog")]')
            logger.warning("找到 %d 个弹窗元素", len(all_dialogs))
            for i, d in enumerate(all_dialogs):
                try:
                    style = d.get_attribute('style')
                    is_visible = 'display: none' not in style if style else True
                    title_el = d.find_elements(By.XPATH, './/*[contains(@class,"el-dialog__title")]')
                    title = title_el[0].text.strip() if title_el else "无标题"
                    logger.warning("  [%d] 可见=%s, 标题='%s'", i + 1, is_visible, title)
                except Exception as ex:
                    logger.warning("  [%d] 获取信息失败: %s", i + 1, ex)
            logger.warning("=========================================")
            raise e

    def _get_dialog_form_item(self, label_text):
        """获取弹窗内指定 label 对应的表单项（尝试多种 label 匹配方式）"""
        def _locate(_driver):
            dialog = self._get_visible_dialog()

            # 先尝试滚动弹窗内容区域，确保所有字段都可见
            try:
                scrollable = dialog.find_element(By.XPATH, './/div[contains(@class,"el-dialog__body") or .//div[contains(@class,"scrollbar")]]')
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", scrollable)
                self.wait_vue_stable()
                self.driver.execute_script("arguments[0].scrollTop = 0;", scrollable)
                self.wait_vue_stable()
            except Exception:
                pass

            xpaths = [
                f'.//div[contains(@class,"el-form-item")]'
                f'[.//label[contains(@class,"el-form-item__label") and contains(normalize-space(.), "{label_text}")]]',
                f'.//div[contains(@class,"el-form-item")]'
                f'[.//label[contains(@class,"el-form-item__label") and contains(text(), "{label_text}")]]',
                f'.//div[contains(@class,"el-form-item")]'
                f'[.//*[contains(@class,"el-form-item__label") and contains(normalize-space(.), "{label_text}")]]',
                f'.//div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.), "{label_text}")]]',
                f'.//div[contains(@class,"el-form-item")][.//input[@placeholder and contains(@placeholder, "{label_text}")]]',
                f'.//div[contains(@class,"el-form-item")][.//textarea[@placeholder and contains(@placeholder, "{label_text}")]]',
                f'.//div[contains(@class,"el-form-item")][.//div[contains(@class,"el-select")]//span[contains(text(), "{label_text}")]]',
                f'.//div[contains(@class,"el-form-item")][@label="{label_text}"]',
                f'.//div[contains(@class,"el-form-item")][.//*[contains(normalize-space(.), "{label_text}")]]',
                f'.//*[contains(normalize-space(.), "{label_text}")]/ancestor::div[contains(@class,"el-form-item")]',
                f'.//div[contains(@class,"el-form-item")][.//*[contains(text(), "{label_text}：")]]',
                f'.//div[contains(@class,"el-form-item")][.//*[contains(text(), "{label_text}:")]]',
                f'.//div[contains(@class,"el-form-item")][.//input[@id and contains(@id, "{label_text}")]]',
                f'.//div[contains(@class,"el-form-item")][.//input[@name and contains(@name, "{label_text}")]]',
            ]

            for xp in xpaths:
                try:
                    item = dialog.find_element(By.XPATH, xp)
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", item)
                    self.wait_vue_stable()
                    return item
                except Exception:
                    continue

            prefix = label_text[:3]
            fallback = f'.//div[contains(@class,"el-form-item")][.//*[contains(text(),"{prefix}")]]'
            try:
                item = dialog.find_element(By.XPATH, fallback)
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", item)
                self.wait_vue_stable()
                return item
            except Exception as e:
                try:
                    all_form_items = dialog.find_elements(By.XPATH, './/div[contains(@class,"el-form-item")]')
                    logger.warning("\n===== 调试信息: 无法定位 '%s' =====", label_text)
                    logger.warning("当前弹窗中找到 %d 个表单项:", len(all_form_items))
                    for i, item in enumerate(all_form_items):
                        try:
                            label_el = item.find_element(By.XPATH, './/label')
                            label_text_found = label_el.text.strip()
                        except Exception:
                            label_text_found = "无label"
                        try:
                            item.find_element(By.XPATH, './/div[contains(@class,"el-select")]')
                            field_type = "下拉框"
                        except Exception:
                            try:
                                item.find_element(By.XPATH, './/input')
                                field_type = "输入框"
                            except Exception:
                                field_type = "未知类型"
                        logger.warning("  [%d] label='%s', type=%s", i + 1, label_text_found, field_type)
                    logger.warning("=========================================")
                except Exception:
                    logger.warning("无法获取表单调试信息: %s", e)
                raise Exception(f"无法定位表单项: {label_text}")

        return WebDriverWait(self.driver, 10).until(lambda d: _locate(d))

    def _select_option_by_text(self, option_text):
        """从已展开的下拉列表中选择指定文本的选项"""
        self.wait_vue_stable()

        # 打印当前页面所有可用的下拉选项（调试用）
        try:
            all_options = self.driver.find_elements(
                By.XPATH, '//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display:none"))]//li'
                ' | //div[contains(@class,"el-popper") and not(contains(@style,"display:none"))]//li'
            )
            logger.info("\n===== 当前可见下拉选项 (%d 个) =====", len(all_options))
            for i, opt in enumerate(all_options[:20]):
                try:
                    text = opt.text.strip()
                    logger.info("  [%d] '%s'", i + 1, text)
                except Exception:
                    logger.info("  [%d] 获取文本失败", i + 1)
            if len(all_options) > 10:
                logger.info("  ... 还有 %d 个选项", len(all_options) - 10)
            logger.info("=========================================")
        except Exception:
            logger.warning("无法获取当前页面选项列表")

        for _ in range(3):
            option_xpaths = [
                f'//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]'
                f'//li[not(contains(@class,"is-disabled")) and contains(normalize-space(.), "{option_text}")]',
                f'//div[contains(@class,"el-popper") and not(contains(@style,"display: none"))]'
                f'//li[not(contains(@class,"is-disabled")) and contains(normalize-space(.), "{option_text}")]',
                f'//body//li[@role="option" and contains(normalize-space(.), "{option_text}")]',
                f'//body//li[not(contains(@class,"is-disabled")) and contains(normalize-space(.), "{option_text}")]',
                f'//label[contains(@class,"el-checkbox") and .//*[contains(text(), "{option_text}")]]',
                f'//tr[contains(@class,"el-table__row") and .//*[contains(text(), "{option_text}")]]',
            ]

            for option_xpath in option_xpaths:
                try:
                    option = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, option_xpath))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'nearest'});", option)
                    self.wait_vue_stable()
                    try:
                        option.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", option)
                    self.wait_vue_stable()
                    return option_text
                except Exception as e:
                    logger.debug("尝试定位选项失败 (%s): %s", option_xpath, e)
                    continue

            self.wait_vue_stable()

        # 部分匹配
        option_xpaths_partial = [
            f'//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]'
            f'//li[not(contains(@class,"is-disabled"))]',
            f'//div[contains(@class,"el-popper") and not(contains(@style,"display: none"))]'
            f'//li[not(contains(@class,"is-disabled"))]',
            f'//body//li[@role="option" and not(contains(@class,"is-disabled"))]',
            f'//body//li[not(contains(@class,"is-disabled"))]',
        ]
        for option_xpath in option_xpaths_partial:
            try:
                options = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_all_elements_located((By.XPATH, option_xpath))
                )
                for option in options:
                    try:
                        text = option.text.strip()
                        if option_text in text or text in option_text:
                            logger.info("找到部分匹配选项: '%s'", text)
                            self.driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'nearest'});", option)
                            self.wait_vue_stable()
                            try:
                                option.click()
                            except Exception:
                                self.driver.execute_script("arguments[0].click();", option)
                            self.wait_vue_stable()
                            return text
                    except Exception:
                        continue
            except Exception:
                continue

        # 处理表格形式的选择弹窗（如培训对象选择）
        logger.info("尝试表格形式选择...")
        table_select_xpaths = [
            f'//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//tr[contains(@class,"el-table__row") and .//*[contains(text(), "{option_text}")]]',
            f'//tr[contains(@class,"el-table__row") and .//*[contains(text(), "{option_text}")]]',
        ]

        for table_xpath in table_select_xpaths:
            try:
                row = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, table_xpath))
                )
                checkbox = row.find_element(By.XPATH, './/label[contains(@class,"el-checkbox")]')
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", checkbox)
                self.wait_vue_stable()
                self.driver.execute_script("arguments[0].click();", checkbox)
                self.wait_vue_stable()

                confirm_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//*[contains(@class,"el-dialog__footer")]//button[contains(@class,"el-button--primary")]')
                    )
                )
                self.driver.execute_script("arguments[0].click();", confirm_btn)
                self._wait_loading_gone(timeout=4)
                return option_text
            except Exception as e:
                logger.debug("表格选择失败 (%s): %s", table_xpath, e)
                continue

        raise Exception(f"无法选择选项: {option_text}")

    def _click_dialog_confirm_button(self, dialog_el, close_timeout=4):
        """通用方法：点击弹窗底部的确认/确定选择按钮"""
        confirm_xpaths = [
            './/button[.//span[normalize-space(.)="确认选择"]]',
            './/button[.//span[normalize-space(.)="确定"]]',
            './/button[.//span[normalize-space(.)="确定选择"]]',
            './/footer//button[contains(@class,"el-button--primary")]',
            './/button[contains(@class,"el-button--primary")]',
            './/button[last()]',
        ]

        btn = None
        for xp in confirm_xpaths:
            try:
                btn = dialog_el.find_element(By.XPATH, xp)
                break
            except Exception:
                continue

        if btn is None:
            global_xpaths = [
                '//button[.//span[normalize-space(.)="确认选择"]]',
                '//button[.//span[normalize-space(.)="确定选择"]]',
                '//button[.//span[normalize-space(.)="确定"]]',
                '//button[contains(@class,"el-button--primary")]',
            ]
            for xp in global_xpaths:
                try:
                    btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, xp))
                    )
                    break
                except Exception:
                    continue

        if btn is None:
            raise Exception("未找到弹窗的确认/确定选择按钮")

        for attempt in range(3):
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            self.wait_vue_stable()
            try:
                btn.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", btn)
            self._wait_loading_gone(timeout=close_timeout)

            try:
                WebDriverWait(self.driver, close_timeout, poll_frequency=0.2).until(
                    EC.invisibility_of_element(dialog_el)
                )
                return
            except Exception:
                if attempt < 2:
                    logger.warning("弹窗未关闭，重试点击 (尝试 %d/3)...", attempt + 2)
                    self.wait_vue_stable()
                continue

    # ==================== 导航 ====================

    def navigate(self):
        """通过侧边栏导航到培训计划页面"""
        self.navigate_to("人员管理", "培训管理", "培训计划")
        self._wait_loading_gone(timeout=12)

    def navigate_to_train_plan(self):
        """通过侧边栏导航到培训计划页面（兼容旧调用方）"""
        self.navigate()

    def navigate_to_course_management(self):
        """从培训计划导航到课程管理（同级菜单切换）"""
        course = self.wait.until(EC.element_to_be_clickable(self.COURSE_MANAGEMENT))
        self.driver.execute_script("arguments[0].click();", course)
        self.wait_vue_stable()

    def _switch_to_sibling(self, target_locator):
        """在已展开的同级菜单中切换到目标页面"""
        el = self.wait.until(EC.element_to_be_clickable(target_locator))
        self.driver.execute_script("arguments[0].click();", el)
        self.wait_vue_stable()

    def switch_to_train_plan(self):
        """切回培训计划管理页面，优先同级切换避免菜单折叠"""
        # 先尝试关闭可能存在的弹窗
        try:
            close_buttons = self.driver.find_elements(By.XPATH, '//button[.//span[contains(text(),"关闭")] or .//span[contains(text(),"取消")] or @aria-label="Close"]')
            for btn in close_buttons:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_vue_stable()
                except Exception:
                    pass
        except Exception:
            pass

        methods = [
            ("同级菜单切换", self._switch_to_sibling, [self.TRAIN_PLAN_MANAGEMENT]),
            ("完整导航", self.navigate_to_train_plan, []),
        ]

        for method_name, method, args in methods:
            try:
                method(*args)
                self.wait_vue_stable()
                # 验证是否成功导航
                try:
                    self.driver.find_element(By.XPATH, '//*[contains(text(),"培训计划")]')
                    logger.info("成功导航到培训计划页面（%s）", method_name)
                    return
                except Exception:
                    logger.warning("%s 后页面验证失败，尝试下一种方式", method_name)
            except Exception as e:
                logger.warning("%s 失败: %s", method_name, e)

        raise Exception("无法导航到培训计划管理页面")

    # ==================== 页面状态验证 ====================

    def get_page_title_text(self):
        """获取页面主标题"""
        candidates = [
            (By.XPATH, '//header//h2'),
            (By.XPATH, '//h2[not(ancestor::div[contains(@style,"display: none")])]'),
            (By.XPATH, '//div[contains(@class,"page-header") or contains(@class,"page-title")]//h2'),
            (By.XPATH, '//section//h2 | //main//h2'),
            (By.XPATH, '//div[contains(@class,"el-tabs")]//span[contains(@class,"el-tabs__item") and contains(@class,"is-active")]'),
        ]
        for locator in candidates:
            try:
                el = self.wait.until(EC.presence_of_element_located(locator))
                text = el.text.strip()
                if text:
                    return text
            except Exception:
                continue
        return ''

    def is_page_loaded(self):
        """判断页面是否加载完成（表格或关键元素存在）"""
        try:
            self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[contains(@class,"el-table")]')
                )
            )
            return True
        except Exception:
            return False

    def get_table_header_texts(self):
        """获取表格所有列头的文本"""
        try:
            headers = self.wait.until(
                EC.presence_of_all_elements_located(self.TABLE_COLUMN_HEADERS)
            )
            return [h.text.strip() for h in headers if h.text.strip()]
        except Exception:
            return []

    # ==================== 搜索 ====================

    def input_search_name(self, value):
        """输入搜索关键词"""
        el = self.wait.until(EC.visibility_of_element_located(self.SEARCH_NAME_INPUT))
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        el.send_keys(value)

    def click_search(self):
        """点击查询按钮"""
        self._click_js(self.SEARCH_BUTTON)
        self.wait_vue_stable()

    def click_reset(self):
        """点击重置按钮"""
        self._click_js(self.RESET_BUTTON)
        self.wait_vue_stable()

    def select_search_type(self, type_text):
        """选择搜索条件中的培训类型"""
        self._click_js(self.SEARCH_TYPE_SELECT)
        return self._select_option_by_text(type_text)

    def select_search_status(self, status_text):
        """选择搜索条件中的状态"""
        self._click_js(self.SEARCH_STATUS_SELECT)
        return self._select_option_by_text(status_text)

    def select_search_publish(self, publish_text):
        """选择搜索条件中的发布状态"""
        self._click_js(self.SEARCH_PUBLISH_SELECT)
        return self._select_option_by_text(publish_text)

    # ==================== 分页 ====================

    def get_total_count_text(self):
        """获取总条数文本，如 '共 12 条'"""
        try:
            el = self.wait.until(EC.visibility_of_element_located(self.TOTAL_COUNT))
            return el.text.strip()
        except Exception:
            return ''

    def get_total_count(self):
        """解析总条数数字"""
        text = self.get_total_count_text()
        try:
            return int(''.join(filter(str.isdigit, text)))
        except (ValueError, TypeError):
            return 0

    def get_current_page_number(self):
        """获取当前页码"""
        try:
            el = self.wait.until(EC.presence_of_element_located(self.CURRENT_PAGE))
            text = el.text.strip()
            return int(text) if text.isdigit() else 1
        except Exception:
            return 1

    def click_page(self, page_number):
        """点击指定页码按钮"""
        page_xpath = (
            f'//div[contains(@class,"el-pagination")]'
            f'//button[not(contains(@class,"btn-next")) and not(contains(@class,"btn-prev"))'
            f' and normalize-space(.)="{page_number}"]'
        )
        self._click_js((By.XPATH, page_xpath))
        self.wait_vue_stable()

    def click_next_page(self):
        """点击下一页"""
        self._click_js(self.NEXT_PAGE_BUTTON)
        self.wait_vue_stable()

    def click_prev_page(self):
        """点击上一页"""
        self._click_js(self.PREV_PAGE_BUTTON)
        self.wait_vue_stable()

    def is_next_page_enabled(self):
        """下一页按钮是否可用"""
        try:
            btn = self.driver.find_element(*self.NEXT_PAGE_BUTTON)
            return btn.is_enabled()
        except Exception:
            return False

    def is_prev_page_enabled(self):
        """上一页按钮是否可用"""
        try:
            btn = self.driver.find_element(*self.PREV_PAGE_BUTTON)
            return btn.is_enabled()
        except Exception:
            return False

    def select_page_size(self, size):
        """切换每页条数"""
        try:
            select = self.wait.until(EC.element_to_be_clickable(self.PAGE_SIZE_SELECT))
            self.driver.execute_script("arguments[0].click();", select)
            self.wait_vue_stable()
            option_xpath = self.PAGE_SIZE_OPTION.format(size=size)
            option = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, option_xpath))
            )
            self.driver.execute_script("arguments[0].click();", option)
            self.wait_vue_stable()
        except Exception as e:
            raise Exception(f"切换每页条数失败: {e}")

    # ==================== 弹窗操作 ====================

    def click_add_button(self):
        """点击新增培训计划按钮"""
        add_button_xpaths = [
            '//button[.//span[contains(normalize-space(.),"新增培训计划")]]',
            '//button[.//span[contains(normalize-space(.),"新增")]]',
            '//button[contains(@class,"el-button--primary") and .//span[contains(normalize-space(.),"新增")]]',
            '//div[contains(@class,"search-bar") or contains(@class,"toolbar") or contains(@class,"header")]//button[.//span[contains(normalize-space(.),"新增")]]',
            '//div[contains(@class,"el-container") or contains(@class,"main-content")]//button[.//span[contains(normalize-space(.),"新增")]]',
            '//*[contains(text(),"新增")]//ancestor::button[1]',
            '//span[contains(text(),"新增")]//ancestor::button[1]',
        ]

        clicked = False
        for xp in add_button_xpaths:
            try:
                add_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
                self.wait_vue_stable()
                self.driver.execute_script("arguments[0].click();", add_btn)
                clicked = True
                break
            except Exception as e:
                logger.debug("尝试定位新增按钮失败 (%s): %s", xp, e)
                continue

        if not clicked:
            logger.warning("\n===== 页面上所有按钮 =====")
            all_buttons = self.driver.find_elements(By.XPATH, '//button')
            for i, btn in enumerate(all_buttons[:20]):
                try:
                    text = btn.text.strip()
                    cls = btn.get_attribute('class') or ''
                    logger.warning("  [%d] text='%s' class='%s'", i + 1, text, cls)
                except Exception:
                    logger.warning("  [%d] 获取信息失败", i + 1)
            logger.warning("=================================")
            raise Exception("无法找到并点击新增培训计划按钮")

        self._wait_loading_gone(timeout=4)
        WebDriverWait(self.driver, 15).until(
            EC.visibility_of_element_located(
                (By.XPATH, '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]')
            )
        )
        self.wait_vue_stable()

    def get_dialog_title_text(self):
        """获取弹窗标题"""
        try:
            return self.wait.until(EC.visibility_of_element_located(self.DIALOG_TITLE)).text.strip()
        except Exception:
            return ''

    def wait_dialog_closed(self, timeout=5):
        """等待弹窗关闭"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, '.el-overlay-dialog, .el-dialog__wrapper, .el-dialog')
                )
            )
            return True
        except Exception:
            return False

    # ==================== 表单填充 ====================

    def fill_dialog_input(self, label_text, value):
        """按 label 文本找到弹窗输入框并输入"""
        item = self._get_dialog_form_item(label_text)
        input_el = WebDriverWait(self.driver, 10).until(
            lambda d: item.find_element(By.XPATH, './/input[not(@disabled)] | .//textarea[not(@disabled)]')
        )
        input_el.click()
        input_el.send_keys(Keys.CONTROL + "a")
        input_el.send_keys(Keys.DELETE)
        if value:
            input_el.send_keys(value)
        self.wait_vue_stable()

    def fill_dialog_date(self, label_text, date_str):
        """输入日期 - 直接给 input 输入日期字符串后按回车"""
        item = self._get_dialog_form_item(label_text)

        try:
            self.driver.execute_script("document.body.click();")
            self.wait_vue_stable()
        except Exception:
            pass

        el = None
        for xpath in [
            './/input[contains(@class,"el-date")]',
            './/input[@placeholder]',
            './/input',
        ]:
            try:
                el = item.find_element(By.XPATH, xpath)
                break
            except Exception:
                continue

        if el is None:
            raise Exception(f"日期输入框未找到 ({label_text})")

        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        self.wait_vue_stable()

        self.driver.execute_script("arguments[0].removeAttribute('readonly');", el)
        el.clear()
        self.wait_vue_stable()
        el.send_keys(date_str)
        self.wait_vue_stable()
        el.send_keys(Keys.ENTER)
        self.wait_vue_stable()

        logger.info("[日期输入] 完成: %s", date_str)

    def select_dialog_option(self, label_text, option_text):
        """在弹窗中点击下拉框并选择选项（带重试）"""
        item = self._get_dialog_form_item(label_text)
        content = item.find_element(By.XPATH, './/div[contains(@class,"el-form-item__content")] | .')

        select_el = None
        for xp in [
            './/div[contains(@class,"el-select__wrapper")]',
            './/div[@role="combobox"]',
            './/div[contains(@class,"el-select")]',
            './/span[contains(@class,"el-select__wrapper")]',
            './/span[contains(@class,"el-select")]',
            './/*[@role="combobox"]',
            './/*[contains(@class,"el-select")]',
        ]:
            try:
                select_el = content.find_element(By.XPATH, xp)
                logger.debug("[select_dialog_option] 找到下拉框 (xpath: %s)", xp)
                break
            except Exception:
                continue

        if select_el is None:
            raise Exception(f"无法定位下拉框: {label_text}")

        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", select_el)
        self.wait_vue_stable()

        for attempt in range(3):
            try:
                try:
                    select_el.click()
                    logger.debug("[select_dialog_option] 原生点击 (尝试%d)", attempt + 1)
                except Exception:
                    self.driver.execute_script("arguments[0].click();", select_el)
                    logger.debug("[select_dialog_option] JS点击 (尝试%d)", attempt + 1)
                self.wait_vue_stable()

                options_count = len(self.driver.find_elements(
                    By.XPATH, '//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display:none"))]//li | '
                               '//div[contains(@class,"el-popper") and not(contains(@style,"display:none"))]//li'
                ))

                logger.debug("[select_dialog_option] 尝试%d: 展开后找到 %d 个可见选项", attempt + 1, options_count)
                if options_count > 0 or attempt >= 2:
                    break

                logger.debug("[select_dialog_option] 下拉未展开，重试...")
                self.driver.execute_script("document.body.click();")
                self.wait_vue_stable()
            except Exception as e:
                logger.debug("[select_dialog_option] 点击异常: %s", e)

        result = self._select_option_by_text(option_text)

        if result is None:
            raise Exception(f"无法选择选项 '{option_text}' (字段: {label_text})")

        return result

    def select_principal(self, principal_name=None):
        """选择负责人（点击后弹出人员选择弹窗）"""
        original_dialogs = self.driver.find_elements(By.XPATH, '//div[contains(@class,"el-dialog")][not(contains(@style,"display: none"))]')
        original_count = len(original_dialogs)
        logger.info("\n===== select_principal: 初始弹窗数=%d =====", original_count)

        item = self._get_dialog_form_item("负责人")
        content = item.find_element(By.XPATH, './/div[contains(@class,"el-form-item__content")] | .')
        select_xpaths = [
            './/div[contains(@class,"el-select__wrapper")]',
            './/div[@role="combobox"]',
            './/div[contains(@class,"el-select")]',
            './/input',
        ]
        select_el = None
        for xp in select_xpaths:
            try:
                select_el = content.find_element(By.XPATH, xp)
                break
            except Exception:
                continue

        if select_el is None:
            raise Exception("无法定位负责人选择框")

        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", select_el)
        self.wait_vue_stable()
        select_el.click()
        self.wait_vue_stable()

        WebDriverWait(self.driver, 10).until(
            lambda d: len(d.find_elements(By.XPATH, '//div[contains(@class,"el-dialog")][not(contains(@style,"display: none"))]')
) > original_count)

        dialogs = self.driver.find_elements(By.XPATH, '//div[contains(@class,"el-dialog")][not(contains(@style,"display: none"))]')
        principal_dialog = None

        for d in reversed(dialogs):
            try:
                title_els = d.find_elements(By.XPATH, './/*[contains(@class,"el-dialog__title")]')
                if not title_els:
                    continue
                title = title_els[0].text.strip()
                if not title or title == "添加培训计划":
                    continue
                principal_dialog = d
                break
            except Exception:
                continue

        if principal_dialog is None:
            logger.warning("\n===== 所有弹窗信息 =====")
            for i, d in enumerate(dialogs):
                try:
                    title_els = d.find_elements(By.XPATH, './/*[contains(@class,"el-dialog__title")]')
                    title = title_els[0].text.strip() if title_els else "无标题"
                    logger.warning("  弹窗[%d]: title='%s'", i + 1, title)
                except Exception:
                    logger.warning("  弹窗[%d]: 获取信息失败", i + 1)
            logger.warning("=========================")
            raise Exception("无法找到负责人选择弹窗")

        logger.info("负责人选择弹窗已找到")

        if principal_name:
            try:
                search_input = principal_dialog.find_element(By.XPATH, './/input[@placeholder]')
                search_input.clear()
                search_input.send_keys(principal_name)
                self.wait_vue_stable()
            except Exception:
                pass

        try:
            first_checkbox = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, './/tr[contains(@class,"el-table__row")][1]//label[contains(@class,"el-checkbox")]')
                )
            )
            self.driver.execute_script("arguments[0].click();", first_checkbox)
            self.wait_vue_stable()
            logger.info("已选择第一个人员")
        except Exception as e:
            raise Exception(f"无法选择负责人: {e}")

        try:
            self._click_dialog_confirm_button(principal_dialog)
            self.wait_vue_stable()
            logger.info("已点击负责人选择弹窗的确认选择按钮")
        except Exception as e:
            raise Exception(f"无法确认负责人选择: {e}")

    def select_training_target(self, target_name=None):
        """选择培训对象（点击后弹出人员/组织选择弹窗）"""
        item = self._get_dialog_form_item("培训对象")

        trigger_xpaths = [
            './/input[contains(@placeholder,"请选择") or contains(@placeholder,"选择")]',
            './/div[contains(@class,"el-input__inner")]',
            './/button',
        ]

        clicked = False
        for xp in trigger_xpaths:
            try:
                trigger = item.find_element(By.XPATH, xp)
                self.driver.execute_script("arguments[0].click();", trigger)
                self.wait_vue_stable()
                clicked = True
                break
            except Exception:
                continue

        if not clicked:
            raise Exception("无法点击培训对象选择框")

        dialog_xpaths = [
            '//div[contains(@class,"el-dialog") and .//*[contains(text(),"选择培训对象")]]',
            '//div[contains(@class,"el-dialog") and .//*[contains(text(),"选择人员")]]',
            '//div[contains(@class,"el-dialog") and .//*[contains(text(),"选择组织")]]',
            '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))][last()]',
        ]

        dialog = None
        for xpath in dialog_xpaths:
            try:
                candidate = WebDriverWait(self.driver, 8).until(
                    EC.visibility_of_element_located((By.XPATH, xpath))
                )
                try:
                    title = candidate.find_element(By.XPATH, './/*[contains(@class,"el-dialog__title")]').text.strip()
                    if title == "添加培训计划":
                        continue
                    logger.info("[select_training_target] 找到弹窗: %s", title)
                except Exception:
                    pass
                dialog = candidate
                break
            except Exception:
                continue

        if dialog is None:
            raise Exception("培训对象选择弹窗未出现")

        if target_name:
            try:
                search_input = dialog.find_element(
                    By.XPATH, './/input[contains(@placeholder,"搜索") or contains(@placeholder,"请输入")]'
                )
                search_input.clear()
                search_input.send_keys(target_name)
                self.wait_vue_stable()
                logger.info("[select_training_target] 已搜索: %s", target_name)
            except Exception:
                logger.debug("[select_training_target] 搜索框未找到，跳过搜索")

        try:
            first_checkbox = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, './/tr[contains(@class,"el-table__row")][1]//label[contains(@class,"el-checkbox")]')
                )
            )
            self.driver.execute_script("arguments[0].click();", first_checkbox)
            self.wait_vue_stable()
            logger.info("[select_training_target] 已选择第一个人员（表格）")
        except Exception:
            try:
                first_node = dialog.find_element(
                    By.XPATH, './/*[contains(@class,"el-tree-node__content")][1]'
                )
                self.driver.execute_script("arguments[0].click();", first_node)
                self.wait_vue_stable()
                logger.info("[select_training_target] 已选择第一个节点（树形）")
            except Exception:
                raise Exception("无法选择任何人员")

        try:
            self._click_dialog_confirm_button(dialog)
            self.wait_vue_stable()
            logger.info("[select_training_target] 已确认选择")
        except Exception as e:
            raise Exception(f"无法确认培训对象选择: {e}")

    # ==================== 关联课程弹窗 ====================

    def click_course_select_trigger(self):
        """点击新增弹窗中的'选择课程'按钮，打开课程选择弹窗"""
        try:
            self._click_js(self.COURSE_SELECT_TRIGGER)
            self.wait_vue_stable()
        except Exception:
            try:
                item = self._get_dialog_form_item("关联课程")
                btn = item.find_element(By.XPATH, './/button | .//a | .//span[contains(@class,"el-button")]')
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_vue_stable()
            except Exception as e:
                raise Exception(f"无法打开课程选择弹窗: {e}")

    def search_and_select_course(self, course_name):
        """在课程选择弹窗中搜索并勾选指定课程"""
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[contains(@class,"el-dialog") and (.//*[contains(text(),"选择课程") or contains(text(),"课程列表") or contains(text(),"关联课程")])]')
            )
        )
        self.wait_vue_stable()

        try:
            search_input = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(self.COURSE_SELECT_SEARCH)
            )
            search_input.click()
            search_input.send_keys(Keys.CONTROL + "a")
            search_input.send_keys(Keys.DELETE)
            search_input.send_keys(course_name)
            self.wait_vue_stable()
            search_input.send_keys(Keys.ENTER)
            self.wait_vue_stable()
        except Exception:
            logger.info("课程搜索框未找到，尝试直接选择")

        checkbox_candidates = [
            (f'//div[contains(@class,"el-dialog") and .//*[text()="选择课程"]]'
             f'//label[contains(@class,"el-checkbox")]'
             f'/ancestor::div[contains(@class,"el-card") or contains(@class,"course-item")][.//text()="{course_name}"]'
             f'//label[contains(@class,"el-checkbox")]'),
            (f'//div[contains(@class,"el-dialog") and .//*[text()="选择课程"]]'
             f'//*[contains(normalize-space(.),"{course_name}")]'
             f'/ancestor::div[contains(@class,"el-card") or contains(@class,"course-item") or contains(@class,"el-row")]'
             f'[1]//label[contains(@class,"el-checkbox")]'),
            (f'//div[contains(@class,"el-dialog") and .//*[text()="选择课程"]]'
             f'//tr[contains(@class,"el-table__row")][.//*[contains(normalize-space(.),"{course_name}")]]'
             f'//label[contains(@class,"el-checkbox")]'),
            (f'//div[contains(@class,"el-dialog") and .//*[text()="选择课程"]]'
             f'//label[contains(@class,"el-checkbox")]'
             f'[following::*[contains(normalize-space(.),"{course_name}")]]'),
            (f'//div[contains(@class,"el-dialog") and .//*[text()="选择课程"]]'
             f'//*[contains(normalize-space(.),"{course_name}")]'
             f'/preceding::label[contains(@class,"el-checkbox")][1]'),
            ('(//div[contains(@class,"el-dialog") and .//*[text()="选择课程"]]'
             '//label[contains(@class,"el-checkbox")])[1]'),
        ]

        for i, xp in enumerate(checkbox_candidates):
            try:
                checkbox = WebDriverWait(self.driver, 8 if i < len(checkbox_candidates) - 1 else 3).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", checkbox)
                self.wait_vue_stable()
                self.driver.execute_script("arguments[0].click();", checkbox)
                logger.info("[关联课程] 成功勾选课程「%s」（策略 %d）", course_name, i + 1)
                self.wait_vue_stable()
                return
            except Exception as e:
                logger.debug("[关联课程] 策略 %d 失败: %s", i + 1, e)
                continue

        try:
            first_cb = self.COURSE_SELECT_ROW_CHECKBOX
            checkbox = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(first_cb))
            self.driver.execute_script("arguments[0].click();", checkbox)
            logger.info("[关联课程] 使用后备策略勾选了第一个课程")
            return
        except Exception as e:
            raise Exception(f"课程选择失败 ({course_name}): {e}")

    def click_all_courses_button(self):
        """点击课程选择弹窗中的「全部」按钮，全选左侧课程列表"""
        all_xpaths = [
            '//div[contains(@class,"el-dialog") and (.//*[text()="选择课程"] or .//*[text()="选择关联课程"])]'
            '//button[.//span[normalize-space(.)="全部"]]',
            '//div[contains(@class,"el-dialog") and .//*[text()="选择课程"]]'
            '//button[.//span[normalize-space(.)="全部"]]',
            '//button[.//span[normalize-space(.)="全部"]]',
        ]
        for xp in all_xpaths:
            try:
                btn = WebDriverWait(self.driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                self.wait_vue_stable()
                self.driver.execute_script("arguments[0].click();", btn)
                logger.info("[关联课程] 已点击「全部」按钮")
                self.wait_vue_stable()
                return
            except Exception as e:
                logger.debug("[关联课程] 「全部」按钮定位失败: %s", e)
                continue
        raise Exception("未找到「全部」按钮")

    def confirm_course_selection(self):
        """点击课程选择弹窗的「确定选择」按钮（弹窗底部右侧蓝色按钮），等待关闭"""
        course_dialog = None
        for xp in [
            '//div[contains(@class,"el-dialog") and (.//*[text()="选择课程"] or .//*[text()="课程列表"] or .//*[text()="选择关联课程"])]',
            '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]',
        ]:
            try:
                course_dialog = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, xp))
                )
                break
            except Exception:
                continue

        if course_dialog is None:
            raise Exception("确认课程选择失败: 未找到课程选择弹窗")

        confirm_xpaths = [
            './/button[.//span[normalize-space(.)="确定选择"]]',
            './/button[.//span[normalize-space(.)="确定"]]',
            './/button[contains(@class,"el-button--primary")][normalize-space()="确定"]',
            './/button[contains(@class,"el-button--primary")]',
            './/button[last()]',
        ]

        btn = None
        for xp in confirm_xpaths:
            try:
                btn = course_dialog.find_element(By.XPATH, xp)
                break
            except Exception:
                continue

        if btn is None:
            for xp in [
                '//button[.//span[normalize-space(.)="确定选择"]]',
                '//button[.//span[normalize-space(.)="确定"]]',
                '//button[contains(@class,"el-button--primary")][normalize-space()="确定"]',
                '//button[contains(@class,"el-button--primary")]',
            ]:
                try:
                    btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, xp))
                    )
                    break
                except Exception:
                    continue

        if btn is None:
            raise Exception("确认课程选择失败: 未找到确认按钮")

        for attempt in range(3):
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            self.wait_vue_stable()
            try:
                btn.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", btn)
            self.wait_vue_stable()

            try:
                WebDriverWait(self.driver, 4, poll_frequency=0.2).until(
                    EC.invisibility_of_element(course_dialog)
                )
                logger.info("[关联课程] 弹窗已关闭")
                return
            except Exception:
                if attempt < 2:
                    logger.warning("[关联课程] 弹窗未关闭，重试 (尝试 %d/3)...", attempt + 2)
                    self.wait_vue_stable()
                continue

        logger.warning("[关联课程] 弹窗未自动关闭，继续执行")

    def close_sub_dialogs(self):
        """关闭所有子弹窗/遮罩层，只保留主弹窗（添加培训计划）"""
        try:
            self.driver.execute_script("""
                (function() {
                    var overlays = document.querySelectorAll('.el-overlay');
                    for (var o of overlays) {
                        var dialog = o.querySelector('.el-dialog__title');
                        if (dialog && dialog.textContent.trim() === '添加培训计划') continue;
                        o.style.display = 'none';
                        o.remove();
                    }
                    var dialogs = document.querySelectorAll('.el-dialog');
                    for (var d of dialogs) {
                        var title = d.querySelector('.el-dialog__title');
                        if (title && title.textContent.trim() === '添加培训计划') continue;
                        d.style.display = 'none';
                    }
                    document.body.classList.remove('el-overflow-hidden');
                })();
            """)
            self.wait_vue_stable()
        except Exception:
            pass

    def click_save(self):
        """点击弹窗保存/确定按钮"""
        main_dialog_xp = '//div[contains(@class,"el-dialog") and .//*[contains(@class,"el-dialog__title")][contains(.,"添加培训计划")]]'

        save_xpaths = [
            main_dialog_xp + '//*[contains(@class,"el-dialog__footer")]//button[contains(@class,"el-button--primary")]',
            main_dialog_xp + '//button[contains(@class,"el-button--primary")]',
            '//div[contains(@class,"el-overlay") and not(contains(@style,"display:none"))]//div[contains(@class,"el-dialog")]//*[contains(@class,"el-dialog__footer")]//button[contains(@class,"el-button--primary")]',
            '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]//*[contains(@class,"el-dialog__footer")]//button[contains(@class,"el-button--primary")]',
            '//div[not(contains(@style,"display:none"))]//button[contains(@class,"el-button--primary") and not(.//span[contains(text(),"取消")])]',
        ]

        el = None
        for i, xp_str in enumerate(save_xpaths):
            try:
                el = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, xp_str))
                )
                logger.debug("[保存] 方案%d 找到按钮", i + 1)
                break
            except Exception:
                continue

        if el is None:
            logger.warning("[保存] 所有方案均未找到按钮，尝试直接查找页面所有主按钮")
            all_primary = self.driver.find_elements(
                By.XPATH, '//button[contains(@class,"el-button--primary")]'
            )
            for btn in all_primary:
                try:
                    if btn.is_enabled() and btn.is_displayed():
                        el = btn
                        logger.warning("[保存] 兜底找到按钮: text='%s'", btn.text)
                        break
                except Exception:
                    continue

        if el is None:
            raise Exception("无法找到保存/确定按钮")

        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        self.wait_vue_stable()

        for attempt in range(3):
            try:
                el.click()
                logger.debug("[保存] 原生点击成功 (尝试 %d)", attempt + 1)
                break
            except Exception as e:
                logger.debug("[保存] 原生点击异常: %s", e)
                try:
                    self.driver.execute_script("arguments[0].click();", el)
                    logger.debug("[保存] JS 点击成功 (尝试 %d)", attempt + 1)
                    break
                except Exception as e2:
                    logger.debug("[保存] JS 点击异常: %s", e2)
                    self.wait_vue_stable()

        self._wait_loading_gone(timeout=4)

        try:
            WebDriverWait(self.driver, 5).until(
                EC.invisibility_of_element_located(
                    (By.XPATH, main_dialog_xp)
                )
            )
            logger.info("[保存] 主弹窗已关闭")
        except Exception:
            logger.warning("[保存] 主弹窗未关闭（可能保存失败或等待超时）")

    def click_cancel(self):
        """点击弹窗取消按钮"""
        self._click_js(self.CANCEL_BUTTON)
        self.wait_vue_stable()

    def get_toast_text(self, timeout=10):
        """获取操作提示消息"""
        self.wait_vue_stable()
        try:
            el = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.XPATH,
                     '//*[contains(@class,"el-message") and not(contains(@style,"display: none"))]'
                     '//p[contains(@class,"el-message__content")]')
                )
            )
            return (el.text or '').strip()
        except Exception:
            try:
                el = WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located(
                        (By.XPATH, '//*[contains(@class,"el-message")][normalize-space(.)!=""]')
                    )
                )
                return (el.text or '').strip()
            except Exception:
                return ''

    # ==================== 表格数据获取 ====================

    def get_table_data(self):
        """获取当前页所有行的表格数据"""
        try:
            rows = self.driver.find_elements(*self.TABLE_ROWS)
            data = []
            for row in rows:
                cells = row.find_elements(By.XPATH, './/td//div[contains(@class,"el-table__cell")]')
                if not cells:
                    cells = row.find_elements(By.TAG_NAME, 'td')
                row_data = [cell.text.strip() for cell in cells]
                if row_data and any(row_data):
                    data.append(row_data)
            return data
        except Exception:
            return []

    def find_row_by_plan_name(self, plan_name):
        """根据计划名称查找所在行的数据"""
        row_xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td//div[contains(text(),"{plan_name}")]]'
        )
        try:
            row = self.wait.until(EC.presence_of_element_located((By.XPATH, row_xpath)))
            cells = row.find_elements(By.XPATH, './/td//div[contains(@class,"el-table__cell")]')
            if not cells:
                cells = row.find_elements(By.TAG_NAME, 'td')
            return [cell.text.strip() for cell in cells]
        except Exception:
            return []

    def is_plan_exists(self, plan_name):
        """判断指定计划名称是否在表格中存在"""
        return bool(self.find_row_by_plan_name(plan_name))

    # ==================== 删除操作 ====================

    def delete_plan_by_search(self, plan_name):
        """搜索指定计划名称，然后在结果行中点击删除并确认。"""
        self.click_reset()
        self.wait_vue_stable()
        self.input_search_name(plan_name)
        self.click_search()
        self.wait_vue_stable()

        delete_xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td//div[contains(text(),"{plan_name}")]]'
            f'//button[.//span[contains(text(),"删除")]]'
        )
        try:
            delete_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, delete_xpath))
            )
            self.driver.execute_script("arguments[0].click();", delete_btn)
            self.wait_vue_stable()
        except Exception as e:
            raise Exception(f"未找到计划「{plan_name}」的删除按钮: {e}")

        return self._confirm_delete_dialog()

    def _confirm_delete_dialog(self, timeout=8):
        """确认删除弹框（el-message-box 确定按钮）"""
        confirm_xpaths = [
            '//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))]'
            '//button[.//span[normalize-space()="确定"]]',
            '//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]'
            '//div[contains(@class,"el-message-box")]'
            '//button[.//span[normalize-space()="确定"]]',
            '//div[@role="dialog"]//button[.//span[normalize-space()="确定"]]',
            '//div[contains(@class,"el-message-box__btns")]'
            '//button[.//span[normalize-space()="确定"]]',
        ]
        for xp in confirm_xpaths:
            try:
                btn = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_vue_stable()
                return True
            except Exception:
                continue
        raise Exception("删除确认弹框未找到或确定按钮无法点击")

    # ==================== 行内操作 ====================

    def click_row_button(self, plan_name, button_text):
        """点击某行内指定文本的按钮（如 编辑/删除/发布/查看）"""
        btn_xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td//div[contains(text(),"{plan_name}")]]'
            f'//button[.//span[contains(text(),"{button_text}")]]'
        )
        try:
            btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, btn_xpath))
            )
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_vue_stable()
            return True
        except Exception as e:
            raise Exception(f"未找到计划「{plan_name}」的「{button_text}」按钮: {e}")
