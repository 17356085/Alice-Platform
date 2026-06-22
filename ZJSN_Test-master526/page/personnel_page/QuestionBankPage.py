"""题库管理页面操作类"""
import logging
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

from base.base_page import BasePage
from base.sidebar_navigator import SidebarNavigator

logger = logging.getLogger(__name__)


class QuestionBankPage(BasePage):
    """题库管理页面操作"""

    # ==================== 导航 ====================

    # ==================== 搜索区域 ====================
    SEARCH_KEYWORD_INPUT = (By.XPATH, '//input[contains(@placeholder,"题干")]')
    SEARCH_TYPE_SELECT = (By.CSS_SELECTOR, '.el-form .el-select:nth-child(1)')
    SEARCH_DIFFICULTY_SELECT = (By.CSS_SELECTOR, '.el-form .el-select:nth-child(2)')
    SEARCH_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="查询" or normalize-space(.)="搜索"]]')
    RESET_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="重置"]]')

    # ==================== 工具栏 ====================
    ADD_QUESTION_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="新建试题" or normalize-space(.)="新建"]]')
    IMPORT_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="导入"]]')
    BATCH_DELETE_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="批量删除"]]')

    # ==================== 表格 ====================
    LOADING_MASK = (By.CSS_SELECTOR, ".el-loading-mask")
    EMPTY_TEXT = (By.CSS_SELECTOR, ".el-table__empty-text")
    MAIN_TABLE_HEADER_WRAPPER = (By.CSS_SELECTOR, ".el-table__header-wrapper")
    MAIN_TABLE_BODY_WRAPPER = (By.CSS_SELECTOR, ".el-table__body-wrapper")

    TABLE_CHECKBOX_ALL = (By.CSS_SELECTOR, '.el-table__header-wrapper label.el-checkbox')

    # ==================== 分页 ====================
    PAGINATION = (By.CSS_SELECTOR, ".el-pagination")
    CURRENT_PAGE = (By.CSS_SELECTOR, ".el-pagination .el-pager li.is-active")
    NEXT_PAGE = (By.CSS_SELECTOR, ".el-pagination button.btn-next:not([disabled])")

    # ==================== 弹窗（统一） ====================
    DIALOG_PANEL = (By.CSS_SELECTOR, '.el-overlay:not([style*="display: none"]) div[role=dialog]:last-child')
    DIALOG_CONFIRM = (By.XPATH, '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[@role="dialog"])[last()]//button[.//span[normalize-space(.)="确定"]]')
    DIALOG_CANCEL = (By.XPATH, '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[@role="dialog"])[last()]//button[.//span[normalize-space(.)="取消" or normalize-space(.)="关闭"]]')
    DIALOG_DELETE_CONFIRM = (By.XPATH, '//div[contains(@class,"el-message-box")]//button[contains(@class,"el-button--primary")]')

    # ==================== 新建/编辑试题弹窗 ====================
    DIALOG_QUESTION_CATEGORY_SELECT = (By.XPATH, '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]//span[contains(text(),"请选择分类")]/ancestor::div[contains(@class,"el-select")]')
    DIALOG_QUESTION_TYPE_SELECT = (By.XPATH, '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]//div[contains(@class,"el-select")][2]')
    DIALOG_SCORE_INPUT = (By.XPATH, '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]//input[@type="number"]')
    DIALOG_DIFFICULTY_SELECT = (By.XPATH, '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]//div[contains(@class,"el-select")][3]')
    DIALOG_QUESTION_TEXT_INPUT = (By.XPATH, '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]//textarea[@placeholder="请输入题目内容"]')
    DIALOG_ANALYSIS_TEXTAREA = (By.XPATH, '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]//textarea[@placeholder="请输入答案解析（选填）"]')

    # ==================== 试题分类侧边栏 ====================
    CATEGORY_ADD_BUTTON = (By.XPATH, '//section//button[.//span[normalize-space(.)="新增"]]')
    CATEGORY_EDIT_BUTTON = (By.XPATH, '//section//button[.//span[normalize-space(.)="编辑"]]')
    CATEGORY_DELETE_BUTTON = (By.XPATH, '//section//button[.//span[normalize-space(.)="删除"]]')
    CATEGORY_TREE_NODES = (By.CSS_SELECTOR, '.el-tree span.category-name')

    # ==================== 试题分类弹窗 ====================
    DIALOG_CATEGORY_NAME_INPUT = (By.XPATH, '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]//input[contains(@placeholder,"分类名称")]')
    DIALOG_CATEGORY_PARENT_SELECT = (By.XPATH, '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]//label[contains(text(),"上级分类")]/following::div[contains(@class,"el-select")][1]')
    DIALOG_CATEGORY_SORT_INPUT = (By.XPATH, '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]//label[contains(text(),"排序号")]/following::input[1]')

    # ==================== Toast ====================
    TOAST_TEXT = (By.CSS_SELECTOR, ".el-message__content")
    TOAST_TEXT_FALLBACK = (By.CSS_SELECTOR, 'div[id^="message_"] p, div[id^="message_"] .el-message__content, div[id^="message_"]')

    def __init__(self, driver, timeout=15):
        super().__init__(driver, timeout)
        self.wait = WebDriverWait(driver, timeout)

    def short_sleep(self, seconds=None):
        """微等待（默认使用 TIMEOUT_CONFIG micro_wait）"""
        import time
        from config import TIMEOUT_CONFIG
        time.sleep(seconds if seconds is not None else TIMEOUT_CONFIG.get("micro_wait", 0.2))

    # ==================== 导航 ====================

    def navigate(self):
        SidebarNavigator(self.driver).navigate_to("人员管理", "培训管理", "题库管理")
        self._wait_settled(timeout=12)

    # ==================== 通用操作 ====================

    def _click_js(self, locator):
        """JS 点击，避免遮挡"""
        el = self.wait.until(EC.presence_of_element_located(locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'nearest'});", el)
        self.short_sleep()
        self.driver.execute_script("arguments[0].click();", el)
        return el

    def wait_for_loading_mask(self, timeout=10):
        """等待 Element Plus loading 遮罩消失（重试到消失或超时）"""
        return self._wait_loading_gone(timeout=timeout)

    def _wait_settled(self, timeout=10):
        """等待加载动画消失"""
        self.wait_for_loading_mask(timeout=timeout)

    def _first_displayed(self, locator, timeout=2):
        """查找第一个可见的元素"""
        from selenium.common.exceptions import TimeoutException as SeleniumTimeoutException
        end_time = self._get_current_time() + timeout
        last_err = None
        while self._get_current_time() < end_time:
            try:
                els = self.driver.find_elements(*locator)
                for el in els:
                    try:
                        if el.is_displayed():
                            return el
                    except Exception:
                        continue
            except Exception as e:
                last_err = e
            self.short_sleep()
        if last_err:
            raise last_err
        raise SeleniumTimeoutException(f"未找到元素: {locator}")

    def _get_current_time(self):
        """获取当前时间"""
        import time
        return time.time()

    def _get_visible_dialog(self):
        """获取当前可见的弹窗"""
        return self.wait.until(EC.visibility_of_element_located(self.DIALOG_PANEL))

    def _select_dropdown_option(self, option_text):
        """在已打开的 select 下拉框中选择选项"""
        dropdown_xpath = f'(//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]//li[.//span[normalize-space(.)="{option_text}"]])[last()]'
        option = WebDriverWait(self.driver, 6).until(
            EC.presence_of_element_located((By.XPATH, dropdown_xpath))
        )
        self.driver.execute_script("arguments[0].click();", option)
        self.short_sleep()

    def wait_for_toast_text(self, timeout=6):
        """等待toast提示文本"""
        end_time = self._get_current_time() + timeout
        last = ""
        while self._get_current_time() < end_time:
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
            self.short_sleep()
        return last

    # ==================== 导航 ====================

    def navigate_to_question_bank(self):
        SidebarNavigator(self.driver).navigate_to("人员管理", "培训管理", "题库管理")
        self._wait_settled(timeout=12)

    # ==================== 搜索 ====================

    def _clear_input(self, locator):
        """清空输入框"""
        el = self.wait.until(EC.presence_of_element_located(locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        return el

    def input_keyword(self, value):
        """输入题干关键词"""
        el = self._clear_input(self.SEARCH_KEYWORD_INPUT)
        if value:
            el.send_keys(value)

    def select_search_type(self, type_text):
        """选择搜索题型"""
        self._wait_settled(timeout=6)
        sel = self.wait.until(EC.presence_of_element_located(self.SEARCH_TYPE_SELECT))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", sel)
        self.driver.execute_script("arguments[0].click();", sel)
        self._select_dropdown_option(type_text)

    def select_search_difficulty(self, difficulty_text):
        """选择搜索难度"""
        self._wait_settled(timeout=6)
        sel = self.wait.until(EC.presence_of_element_located(self.SEARCH_DIFFICULTY_SELECT))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", sel)
        self.driver.execute_script("arguments[0].click();", sel)
        self._select_dropdown_option(difficulty_text)

    def click_search(self):
        """点击搜索"""
        self._wait_settled(timeout=6)
        btn = self._first_displayed(self.SEARCH_BUTTON, timeout=4)
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_settled(timeout=10)

    def click_reset(self):
        """点击重置"""
        self._wait_settled(timeout=6)
        btn = self._first_displayed(self.RESET_BUTTON, timeout=4)
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_settled(timeout=10)

    # ==================== 表格 ====================

    def get_table_headers(self):
        """JS提取表格表头（含重试，应对Element Plus异步渲染）"""
        for attempt in range(6):
            try:
                self._wait_table_ready()
            except Exception:
                self.short_sleep()
            self.short_sleep()
            headers = self.driver.execute_script("""
                return Array.from(
                    document.querySelectorAll('.el-table__header-wrapper th .cell')
                ).map(function(el) { return el.textContent.trim(); }).filter(Boolean);
            """)
            if headers and len(headers) >= 3:
                return headers
            self.short_sleep()
        return []

    def _wait_table_ready(self):
        """等待表格就绪"""
        self._wait_settled(timeout=10)

    def get_table_row_count(self):
        """获取表格行数"""
        self._wait_settled(timeout=10)
        wrapper = self.driver.find_element(*self.MAIN_TABLE_BODY_WRAPPER)
        rows = wrapper.find_elements(By.CSS_SELECTOR, "table tbody tr")
        count = 0
        for r in rows:
            try:
                if r.is_displayed():
                    count += 1
            except Exception:
                continue
        return count

    def get_column_index_by_header(self, header_text):
        """获取表头索引"""
        self._wait_settled(timeout=10)
        wrapper = self.driver.find_element(*self.MAIN_TABLE_HEADER_WRAPPER)
        ths = wrapper.find_elements(By.CSS_SELECTOR, "table th")
        for idx, th in enumerate(ths, start=1):
            try:
                t = (th.text or "").strip()
                if t == header_text:
                    return idx
            except Exception:
                continue
        return None

    def get_column_data_by_header(self, header_text):
        """按表头获取列数据"""
        idx = self.get_column_index_by_header(header_text)
        if not idx:
            return []
        return self.get_column_data(idx)

    def get_column_data(self, col_index):
        """获取列数据"""
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

    def click_row_action(self, action_text, row_index=1):
        """点击行内操作按钮"""
        self._wait_settled(timeout=10)
        row_xpath = f'(//div[contains(@class,"el-table__body-wrapper")]//tbody/tr)[{int(row_index)}]'
        row = WebDriverWait(self.driver, 4).until(
            EC.presence_of_element_located((By.XPATH, row_xpath))
        )
        btn_loc = (By.XPATH, f'.//button[.//*[normalize-space(.)="{action_text}"] or normalize-space(.)="{action_text}"]')
        btn = row.find_element(*btn_loc)
        self.driver.execute_script("arguments[0].click();", btn)
        self.short_sleep()

    def check_table_row_checkbox(self, row_index=1):
        """勾选表格行的复选框"""
        self._wait_settled(timeout=10)
        row_xpath = f'(//div[contains(@class,"el-table__body-wrapper")]//tbody/tr)[{int(row_index)}]'
        row = WebDriverWait(self.driver, 4).until(
            EC.presence_of_element_located((By.XPATH, row_xpath))
        )
        cb = row.find_element(By.XPATH, './/label[contains(@class,"el-checkbox")]')
        self.driver.execute_script("arguments[0].click();", cb)
        self.short_sleep()

    def get_empty_text(self):
        """获取空数据提示"""
        self._wait_settled(timeout=8)
        try:
            el = self.driver.find_element(*self.EMPTY_TEXT)
            return (el.text or "").strip()
        except Exception:
            return ""

    # ==================== 分页 ====================

    def get_current_page_number(self):
        """获取当前页码"""
        try:
            el = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(self.CURRENT_PAGE))
            return (el.text or "").strip()
        except Exception:
            return ""

    def click_next_page(self):
        """点击下一页"""
        try:
            btn = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(self.NEXT_PAGE))
            self.driver.execute_script("arguments[0].click();", btn)
            self._wait_settled(timeout=10)
            return True
        except Exception:
            return False

    # ==================== 新建试题 ====================

    def click_add_question(self):
        """点击新建试题"""
        self._wait_settled(timeout=6)
        try:
            WebDriverWait(self.driver, 3).until(
                EC.invisibility_of_element_located(self.DIALOG_PANEL))
        except Exception:
            pass
        btn = self._first_displayed(self.ADD_QUESTION_BUTTON, timeout=6)
        self.driver.execute_script("arguments[0].click();", btn)
        WebDriverWait(self.driver, 6).until(
            EC.visibility_of_element_located(self.DIALOG_PANEL))

    def dialog_select_category(self, category_text):
        """选择试题分类"""
        for xpath in [
            self.DIALOG_QUESTION_CATEGORY_SELECT,
            (By.XPATH, '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]//div[contains(@class,"el-select")][1]'),
            (By.XPATH, '//div[contains(@class,"el-select")]//span[contains(text(),"请选择分类")]/ancestor::div[contains(@class,"el-select")]'),
        ]:
            try:
                sel = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(xpath))
                self.driver.execute_script("arguments[0].click();", sel)
                self._select_dropdown_option(category_text)
                return
            except Exception:
                continue
        raise TimeoutException(f"无法找到试题分类下拉框")

    def dialog_select_type(self, type_text):
        """选择题型（单选题/多选题/判断题/填空题/简答题）"""
        try:
            sel = self.wait.until(EC.presence_of_element_located(self.DIALOG_QUESTION_TYPE_SELECT))
        except Exception:
            sel = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.XPATH,
                    '(//input[contains(@placeholder,"题型")])[1]/ancestor::div[contains(@class,"el-select")]')))
        self.driver.execute_script("arguments[0].click();", sel)
        self._select_dropdown_option(type_text)

    def dialog_input_score(self, score):
        """输入分值"""
        el = self.wait.until(EC.presence_of_element_located(self.DIALOG_SCORE_INPUT))
        self.driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true}));", el, str(score) if score is not None else "")

    def dialog_select_difficulty(self, difficulty_text):
        """选择难度（简单/中等/困难）—— radio 按钮"""
        xpath = f'//span[contains(@class,"el-radio__label")][normalize-space()="{difficulty_text}"]'
        el = WebDriverWait(self.driver, 6).until(EC.presence_of_element_located((By.XPATH, xpath)))
        parent = el.find_element(By.XPATH, './ancestor::label[contains(@class,"el-radio")]')
        self.driver.execute_script("arguments[0].click();", parent)
        self.short_sleep()

    def dialog_input_question_text(self, text):
        """输入题目内容"""
        for xpath in [
            self.DIALOG_QUESTION_TEXT_INPUT,
            (By.XPATH, '//textarea[@placeholder="请输入题目内容"]'),
        ]:
            try:
                el = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(xpath))
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center', inline:'nearest'});", el)
                self.short_sleep()
                if text:
                    el.send_keys(text)
                return
            except Exception:
                continue
        raise TimeoutException("无法找到题目输入框")

    def dialog_input_option(self, option_label, value):
        """输入选项值（option_label: A/B/C/D 或 选项A/选项B/...）"""
        letter = option_label.replace("选项", "").replace(".", "").strip().upper()
        letter_index = ord(letter) - ord('A')
        if letter_index < 0 or letter_index > 25:
            letter_index = 0

        for xpath in [
            (By.XPATH, '//input[@placeholder="请输入选项内容"]'),
            (By.XPATH, '(//div[contains(@class,"el-dialog")])[last()]//input[contains(@placeholder,"请输入选项内容")]'),
        ]:
            try:
                inputs = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_all_elements_located(xpath))
                if letter_index < len(inputs):
                    el = inputs[letter_index]
                    el.clear()
                    el.send_keys(Keys.CONTROL + "a")
                    el.send_keys(Keys.DELETE)
                    if value:
                        el.send_keys(value)
                    return
            except Exception:
                continue
        raise Exception(f"选项 {option_label} 输入框未找到")

    def dialog_select_correct_answer(self, option_letter):
        """选中正确答案（选项字母: A/B/C/D）"""
        letter_index = ord(option_letter.upper()) - ord('A')
        radios = self.driver.find_elements(By.XPATH,
            '//label[contains(@class,"el-radio") and not(contains(@style,"display:none"))]')
        visible_radios = [r for r in radios if r.is_displayed()]
        if letter_index < len(visible_radios):
            self.driver.execute_script("arguments[0].click();", visible_radios[letter_index])
            self.short_sleep()
            return
        for xpath in [
            f'//span[contains(@class,"el-radio__label") and normalize-space()="{option_letter}"]/ancestor::label[contains(@class,"el-radio")]',
            f'//label[contains(@class,"el-radio")]//span[contains(text(),"{option_letter}")]/..',
        ]:
            try:
                el = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                self.driver.execute_script("arguments[0].click();", el)
                self.short_sleep()
                return
            except Exception:
                continue
        raise Exception(f"无法找到正确答案选项 {option_letter}")

    def dialog_input_analysis(self, text):
        """输入答案解析"""
        for xpath in [
            self.DIALOG_ANALYSIS_TEXTAREA,
            (By.XPATH, '//textarea[@placeholder="请输入答案解析（选填）"]'),
        ]:
            try:
                el = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(xpath))
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center', inline:'nearest'});", el)
                self.short_sleep()
                if text:
                    el.send_keys(text)
                return
            except Exception:
                continue
        raise TimeoutException("无法找到答案解析输入框")

    def dialog_confirm(self):
        """弹窗确定（多策略）"""
        for xpath in [
            self.DIALOG_CONFIRM,
            (By.XPATH, '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[.//span[normalize-space(.)="确定"]]'),
            (By.XPATH, '//button[.//span[normalize-space(.)="确定"]]'),
        ]:
            try:
                btn = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(xpath))
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_for_element_disappear(self.DIALOG_PANEL, timeout=5)
                return
            except Exception:
                continue
        for btn in self.driver.find_elements(By.CSS_SELECTOR, 'button'):
            try:
                t = btn.text.strip()
                if ("确定" in t or (t and "确" in t and "定" in t)) and btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_for_element_disappear(self.DIALOG_PANEL, timeout=5)
                    return
            except Exception:
                continue
        raise Exception("无法找到确定按钮")

    def dialog_cancel(self):
        """弹窗取消/关闭（支持"取消"和"关闭"两种按钮文字）"""
        cancel_xpaths = [
            self.DIALOG_CANCEL,
            (By.CSS_SELECTOR, '.el-overlay:not([style*="display: none"]) div[role=dialog]:last-child button.el-dialog__close'),
            (By.CSS_SELECTOR, '.el-dialog:not([style*="display: none"]) button.el-dialog__close'),
            (By.XPATH, '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//footer//button[1]'),
            (By.XPATH, '//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//button[.//span[normalize-space(.)="关闭"]]'),
        ]
        for xp in cancel_xpaths:
            try:
                btn = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(xp))
                self.driver.execute_script("arguments[0].click();", btn)
                self.short_sleep()
                return
            except Exception:
                continue
        raise Exception("未找到取消/关闭按钮")

    def dialog_delete_confirm(self):
        """删除确认弹窗 — 点击确定按钮"""
        confirm_xpaths = [
            self.DIALOG_DELETE_CONFIRM,
            (By.CSS_SELECTOR, '.el-message-box button.el-button--primary'),
            (By.XPATH, '//button[contains(@class,"el-button--primary")][.//span[normalize-space(.)="确定"]]'),
            (By.XPATH, '//div[@role="dialog"]//button[.//span[normalize-space(.)="确定"]]'),
        ]
        for xp in confirm_xpaths:
            try:
                btn = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(xp))
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_for_element_disappear(self.DIALOG_PANEL, timeout=5)
                return
            except Exception:
                continue
        raise Exception("未找到删除确认按钮")

    def is_dialog_open(self):
        """判断弹窗是否打开"""
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

    # ==================== 新建试题（完整流程） ====================

    def create_question(self, category, q_type, score, difficulty, question_text,
                        options=None, correct_answer=None, analysis=None):
        """完整的新建试题流程"""
        self.click_add_question()
        if category:
            self.dialog_select_category(category)
        if q_type:
            self.dialog_select_type(q_type)
        if score is not None:
            self.dialog_input_score(score)
        if difficulty:
            self.dialog_select_difficulty(difficulty)
        if question_text:
            self.dialog_input_question_text(question_text)
        if options:
            for label, value in options.items():
                self.dialog_input_option(label, value)
        if correct_answer:
            self.dialog_select_correct_answer(correct_answer)
        if analysis:
            self.dialog_input_analysis(analysis)
        self.dialog_confirm()
        msg = self.wait_for_toast_text(timeout=6)
        return msg

    # ==================== 试题分类 ====================

    def get_category_names(self):
        """获取试题分类列表文本"""
        self._wait_settled(timeout=6)
        try:
            nodes = self.driver.find_elements(*self.CATEGORY_TREE_NODES)
            return [n.text.strip() for n in nodes if n.text.strip()]
        except Exception:
            return []

    def _real_click(self, element):
        """使用 ActionChains 执行真实浏览器点击（触发 Vue/React 事件）"""
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'nearest'});", element)
        self.short_sleep()
        ActionChains(self.driver).move_to_element(element).click().perform()

    def click_category_add(self):
        """点击分类新增"""
        self._wait_settled(timeout=6)

        for xpath in [
            '//div[contains(@class,"el-tree")]/preceding::button[./span[normalize-space()="新增"]][1]',
            '//section//button[./span[normalize-space()="新增"]][1]',
            '//button[./span[normalize-space()="新增"]][1]',
        ]:
            try:
                btns = self.driver.find_elements(By.XPATH, xpath)
                for btn in btns:
                    try:
                        if not btn.is_displayed():
                            continue
                        ActionChains(self.driver).move_to_element(btn).click().perform()
                        WebDriverWait(self.driver, 8).until(
                            EC.presence_of_element_located(self.DIALOG_CATEGORY_NAME_INPUT))
                        return
                    except Exception:
                        continue
            except Exception:
                continue

        raise Exception("无法点击分类新增按钮")

    def click_category_edit(self):
        """点击分类编辑（需先选中一个分类节点）"""
        self._wait_settled(timeout=6)
        btn = self._first_displayed(self.CATEGORY_EDIT_BUTTON, timeout=6)
        self.driver.execute_script("arguments[0].click();", btn)
        WebDriverWait(self.driver, 6).until(EC.presence_of_element_located(self.DIALOG_PANEL))

    def click_category_delete(self):
        """点击分类删除（需先选中一个分类节点）"""
        self._wait_settled(timeout=6)
        btn = self._first_displayed(self.CATEGORY_DELETE_BUTTON, timeout=6)
        self.driver.execute_script("arguments[0].click();", btn)
        self.short_sleep()

    def select_category_tree_node(self, node_text):
        """点击选中试题分类树中的某个节点"""
        self._wait_settled(timeout=6)
        node_xpath = f'//span[contains(@class,"el-tree-node__label")][normalize-space(.)="{node_text}"]'
        node = WebDriverWait(self.driver, 6).until(EC.element_to_be_clickable((By.XPATH, node_xpath)))
        self.driver.execute_script("arguments[0].click();", node)
        self.short_sleep()

    def dialog_input_category_name(self, name):
        """输入分类名称"""
        el = self.wait.until(EC.presence_of_element_located(self.DIALOG_CATEGORY_NAME_INPUT))
        el.clear()
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        if name:
            el.send_keys(name)

    def dialog_select_category_parent(self, parent_text):
        """选择上级分类"""
        sel = self.wait.until(EC.presence_of_element_located(self.DIALOG_CATEGORY_PARENT_SELECT))
        self.driver.execute_script("arguments[0].click();", sel)
        self._select_dropdown_option(parent_text)

    def dialog_input_category_sort(self, sort_order):
        """输入排序号"""
        el = self.wait.until(EC.presence_of_element_located(self.DIALOG_CATEGORY_SORT_INPUT))
        el.clear()
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        if sort_order is not None:
            el.send_keys(str(sort_order))

    # ==================== 批量操作 ====================

    def click_batch_delete(self):
        """点击批量删除"""
        self._wait_settled(timeout=6)
        btn = self._first_displayed(self.BATCH_DELETE_BUTTON, timeout=6)
        self.driver.execute_script("arguments[0].click();", btn)
        self.short_sleep()

    def click_select_all(self):
        """点击表格全选复选框"""
        self._wait_settled(timeout=6)
        try:
            cb = self.driver.find_element(*self.TABLE_CHECKBOX_ALL)
            self.driver.execute_script("arguments[0].click();", cb)
            self.short_sleep()
        except Exception:
            pass

    def click_import(self):
        """点击导入"""
        self._wait_settled(timeout=6)
        btn = self._first_displayed(self.IMPORT_BUTTON, timeout=6)
        self.driver.execute_script("arguments[0].click();", btn)
        self.short_sleep()
