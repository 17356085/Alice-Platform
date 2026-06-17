"""考试管理页面 Page Object — 重构版

变更记录:
  2026-06-11: 继承 BasePage，清理绝对 XPath，替换 time.sleep → BasePage 等待方法
"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class ExamManagePage(BasePage):
    """考试管理页面操作 — 继承 BasePage"""

    # ==================== 导航定位 ====================

    # 同级菜单跳转（导航统一使用 self.navigate_to，此处仅保留引用）
    # 不再使用绝对 XPath，通过 self.navigate_to("人员管理", "培训管理", "考试管理")

    # ==================== 搜索区域 ====================
    # 注: 搜索区使用 search-item 容器，无 el-form-item/label，用 placeholder 区分下拉框
    SEARCH_NAME_INPUT = (By.XPATH, '//input[contains(@placeholder, "考试名称")]')
    SEARCH_STATUS_SELECT = (
        By.XPATH,
        '//div[contains(@class,"search-item")]'
        '//div[contains(@class,"el-select")]'
        '[.//div[contains(@class,"el-select__placeholder")]'
        '[contains(.,"状态") and not(contains(.,"发布"))]]',
    )
    PUBLISH_STATUS_SELECT = (
        By.XPATH,
        '//div[contains(@class,"search-item")]'
        '//div[contains(@class,"el-select")]'
        '[.//div[contains(@class,"el-select__placeholder")][contains(.,"发布状态")]]',
    )
    DATE_RANGE_INPUT = (
        By.XPATH,
        '//input[contains(@placeholder, "开始日期") or contains(@placeholder, "结束日期")]',
    )
    SEARCH_BUTTON = (
        By.XPATH,
        '//button[.//span[contains(normalize-space(.), "查询") or contains(normalize-space(.), "搜索")]]',
    )
    RESET_BUTTON = (
        By.XPATH,
        '//button[.//span[contains(normalize-space(.), "重置")]]',
    )

    # ==================== 工具栏 ====================
    ADD_BUTTON = (
        By.XPATH,
        '//button[.//span[contains(normalize-space(.), "新增考试") or contains(normalize-space(.), "新增")]]',
    )

    # ==================== 表格 ====================
    TABLE_ROWS = (By.XPATH, '//tr[contains(@class,"el-table__row")]')
    TABLE_ALL_ROWS = (By.CSS_SELECTOR, '.el-table__body-wrapper tbody tr.el-table__row')
    TABLE_HEADERS = (
        By.XPATH,
        '//div[contains(@class,"el-table__header-wrapper")]//th//div[contains(@class,"cell")]',
    )
    EMPTY_TEXT = (By.CSS_SELECTOR, ".el-table__empty-text")

    # 表格列索引（用于 get_column_data）
    COL_EXAM_NAME = 1
    COL_PAPER = 2
    COL_EXAM_TIME = 3
    COL_DURATION = 4
    COL_PARTICIPANTS = 5
    COL_EXAMINED = 6
    COL_PASSED = 7
    COL_STATUS = 8
    COL_PUBLISH_STATUS = 9
    COL_OPERATIONS = 10

    # ==================== 分页 ====================
    # TOTAL_COUNT, NEXT_PAGE_BUTTON, PREV_PAGE_BUTTON 复用 BasePage
    CURRENT_PAGE = (
        By.XPATH,
        '//div[contains(@class,"el-pagination")]'
        '//li[contains(@class,"is-active") or contains(@class,"active")]',
    )
    PAGE_SIZE_SELECT = (By.CSS_SELECTOR, '.el-pagination .el-select__wrapper')
    PAGE_SIZE_OPTION_TPL = (
        '//li[contains(@class,"el-select-dropdown__item") and contains(., "{size}")]'
    )

    # ==================== Toast & Form 错误 ====================
    # TOAST_TEXT, FORM_ERRORS 复用 BasePage.TOAST, BasePage.FORM_ERROR

    # ==================== 操作按钮 ====================
    OPERATION_VIEW = "查看"
    OPERATION_EDIT = "编辑"
    OPERATION_DELETE = "删除"
    OPERATION_PUBLISH = "发布"
    OPERATION_UNPUBLISH = "取消发布"

    # ==================== 弹窗 ====================
    DIALOG_CONFIRM = (
        By.XPATH,
        '(//div[contains(@class,"el-dialog")])[last()]'
        '//button[.//span[normalize-space(.)="确定"]]',
    )
    DIALOG_CANCEL = (
        By.XPATH,
        '(//div[contains(@class,"el-dialog")])[last()]'
        '//button[.//span[normalize-space(.)="取消"]]',
    )
    MESSAGEBOX_CONFIRM = (
        By.XPATH,
        '(//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))])[last()]'
        '//button[.//span[normalize-space(.)="确定"]]',
    )
    MESSAGEBOX_CANCEL = (
        By.XPATH,
        '(//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))])[last()]'
        '//button[.//span[normalize-space(.)="取消"]]',
    )

    # ==================== 选择学员弹窗 ====================
    STUDENT_SELECT_BUTTON = (
        By.XPATH,
        '//button[.//span[contains(normalize-space(.),"选择学员")]]',
    )
    STUDENT_SELECT_DIALOG = (
        By.XPATH,
        '//div[contains(@class,"el-dialog") and .//*[contains(normalize-space(.),"选择对象")]]',
    )
    STUDENT_SEARCH_INPUT = (
        By.XPATH,
        '//div[contains(@class,"el-dialog") and .//*[contains(normalize-space(.),"选择对象")]]'
        '//input[contains(@placeholder,"搜索")]',
    )
    STUDENT_LIST_ROW = (
        By.XPATH,
        '//div[contains(@class,"el-dialog") and .//*[contains(normalize-space(.),"选择对象")]]'
        '//tr[contains(@class,"el-table__row")]',
    )
    STUDENT_CONFIRM_BUTTON = (
        By.XPATH,
        '//div[contains(@class,"el-dialog") and .//*[contains(normalize-space(.),"选择对象")]]'
        '//button[.//span[contains(normalize-space(.),"确认选择")]]',
    )

    # ==================== 详情页 ====================
    DETAIL_EXAM_NAME = (
        By.XPATH,
        '//div[contains(@class,"info-grid") or contains(@class,"exam-info")]'
        '//div[contains(@class,"info-item")]'
        '[.//div[contains(@class,"label") and contains(.,"考试名称")]]'
        '//div[contains(@class,"value")]',
    )

    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)
        self.logger = logging.getLogger(__name__)

    # ==================== 通用操作 ====================

    def _click_js(self, locator):
        """JS 点击指定定位器元素（内部快捷方法）"""
        el = self.find(locator)
        self._js_click_el(el)
        self.wait_vue_stable()
        return el

    def _get_visible_dialog(self, timeout=None):
        """获取当前可见弹窗"""
        return super()._get_visible_dialog(timeout)

    def _get_dialog_form_item(self, label_text):
        """通过 label 文本定位弹窗表单项容器"""
        return super()._get_dialog_form_item(label_text)

    def _select_option_by_text(self, text):
        """选择下拉框中的选项（选项列表已打开）"""
        option_xpath = (
            f'//li[contains(@class,"el-select-dropdown__item")]'
            f'[contains(normalize-space(.), "{text}")]'
        )
        try:
            option = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, option_xpath))
            )
            self._js_click_el(option)
            self.wait_vue_stable()
            return True
        except Exception:
            return False

    def _open_dialog_select(self, label_text):
        """打开弹窗中的下拉框，使用 ActionChains 模拟真实点击以触发 Vue 事件"""
        item = self._get_dialog_form_item(label_text)
        self._scroll_into_view(item)
        self.wait_vue_stable()

        # 先尝试点击 el-select__wrapper（标准 Element Plus 结构）
        for cls_name in ["el-select__wrapper", "el-select__input", "el-select"]:
            try:
                target = item.find_element(
                    By.XPATH,
                    f'.//div[contains(@class,"{cls_name}")]'
                    f' | .//input[contains(@class,"{cls_name}")]',
                )
                self._scroll_into_view(target)
                self.wait_vue_stable()
                ActionChains(self.driver).move_to_element(target).click().perform()
                self.wait_vue_stable()
                # 验证下拉是否打开
                if self._is_select_open():
                    return
            except Exception:
                continue

        # 兜底：点击所有可能的触发元素
        triggers = item.find_elements(By.XPATH, './/*[self::div or self::input]')
        for trigger in triggers:
            try:
                ActionChains(self.driver).move_to_element(trigger).click().perform()
                self.wait_vue_stable()
                if self._is_select_open():
                    return
            except Exception:
                continue

        raise Exception(f"无法打开下拉框: {label_text}")

    def _is_select_open(self):
        """检测是否有 el-select 下拉选项可见"""
        try:
            inputs = self.driver.find_elements(
                By.XPATH, '//input[contains(@class,"el-select__input")][@aria-expanded="true"]'
            )
            if inputs:
                return True
        except Exception:
            pass
        opts = self.driver.find_elements(
            By.XPATH,
            '//li[contains(@class,"el-select-dropdown__item")'
            ' and not(contains(@style,"display: none"))]',
        )
        return len(opts) > 0

    # ==================== Toast & 消息 ====================

    def get_toast_text(self, timeout=5):
        """获取 Toast 消息文本"""
        return self.get_toast(timeout)

    def wait_for_toast_contains(self, keyword, timeout=8):
        """轮询等待 Toast 消息包含指定关键字"""
        deadline = __import__('time').time() + timeout
        while __import__('time').time() < deadline:
            text = self.get_toast(timeout=1)
            if text and keyword in text:
                return text
            self.wait_vue_stable()
        return self.get_toast(timeout=1)

    def get_form_error_texts(self):
        """获取所有表单校验错误文本"""
        errors = self.find_all(self.FORM_ERROR)
        return [e.text.strip() for e in errors if e.text.strip()]

    # ==================== 导航 ====================

    def navigate_to_exam_management(self):
        """导航到考试管理页面"""
        self.navigate_to("人员管理", "培训管理", "考试管理")

    # ==================== 页面状态验证 ====================

    def is_page_loaded(self):
        """检查考试管理页面是否已加载"""
        try:
            self.find_visible(
                (By.XPATH, '//div[contains(@class,"el-table")]'), timeout=5
            )
            return True
        except Exception:
            return False

    def get_table_headers(self):
        """JS提取表格表头（含重试，应对Element Plus异步渲染）"""
        return super().get_table_headers(min_columns=3)

    def get_table_row_count(self):
        """获取当前页表格行数"""
        return super().get_table_row_count()

    def get_empty_text(self):
        """获取空数据提示文本"""
        try:
            el = self.find_visible(self.EMPTY_TEXT, timeout=3)
            return el.text.strip()
        except Exception:
            return ""

    def get_total_count_text(self):
        """获取分页总数文本"""
        try:
            el = self.find_visible(self.TOTAL_COUNT, timeout=5)
            return el.text.strip()
        except Exception:
            return ""

    def get_total_count(self):
        """获取分页总数数值"""
        return super().get_total_count()

    def get_column_data(self, col_index):
        """获取指定列（1-based）所有行数据"""
        return super().get_column_data(col_index)

    def get_column_data_by_header(self, header_text):
        """根据表头文字获取列数据"""
        headers = self.get_table_headers()
        col_index = None
        for idx, h in enumerate(headers, start=1):
            if header_text in h:
                col_index = idx
                break
        if not col_index:
            return []
        return self.get_column_data(col_index)

    def get_first_row_data(self):
        """获取第一行所有列数据"""
        return super().get_first_row_data()

    # ==================== 搜索 ====================

    def input_search_name(self, value):
        """输入搜索条件中的考试名称"""
        try:
            self.input_text(self.SEARCH_NAME_INPUT, value)
            return True
        except Exception:
            return False

    def select_search_status(self, status_text):
        """选择搜索条件中的状态"""
        return self._click_then_select_option(self.SEARCH_STATUS_SELECT, status_text)

    def select_publish_status(self, status_text):
        """选择搜索条件中的发布状态"""
        return self._click_then_select_option(self.PUBLISH_STATUS_SELECT, status_text)

    def _click_then_select_option(self, select_locator, option_text):
        """点击下拉框后选择选项"""
        try:
            select = self.find_clickable(select_locator)
            self._js_click_el(select)
            self.wait_vue_stable()
            return self._select_option_by_text(option_text)
        except Exception:
            return False

    def click_search(self):
        """点击搜索按钮"""
        self.click(self.SEARCH_BUTTON)

    def click_reset(self):
        """点击重置按钮"""
        self.click(self.RESET_BUTTON)

    # ==================== 分页 ====================

    def get_current_page_number(self):
        """获取当前页码"""
        try:
            el = self.find(self.CURRENT_PAGE, timeout=3)
            text = el.text.strip()
            return int(text) if text.isdigit() else 1
        except Exception:
            return 1

    def click_next_page(self):
        """点击下一页"""
        self.click(self.NEXT_PAGE, timeout=5)

    def click_prev_page(self):
        """点击上一页"""
        self.click(self.PREV_PAGE, timeout=5)

    def is_next_page_enabled(self):
        """判断下一页按钮是否可用"""
        try:
            btn = self.find(self.NEXT_PAGE, timeout=3)
            return "is-disabled" not in (btn.get_attribute("class") or "") and btn.is_enabled()
        except Exception:
            return False

    def select_page_size(self, size):
        """切换每页条数"""
        try:
            select = self.find_clickable(self.PAGE_SIZE_SELECT)
            self._js_click_el(select)
            self.wait_vue_stable()
            option_xpath = self.PAGE_SIZE_OPTION_TPL.format(size=size)
            option = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, option_xpath))
            )
            self._js_click_el(option)
            self.wait_vue_stable()
        except Exception as e:
            logger.warning("切换每页条数失败: %s", e)

    # ==================== 新增考试 ====================

    def click_add(self):
        """点击新增考试按钮"""
        self._click_js(self.ADD_BUTTON)
        self._get_visible_dialog(timeout=8)

    def input_dialog_field(self, label_text, value):
        """在弹窗中输入文本字段"""
        self.fill_dialog_input(label_text, value)

    def input_dialog_datetime(self, label_text, value):
        """在弹窗中输入日期时间"""
        logger.info("尝试输入日期时间: %s = %s", label_text, value)
        try:
            item = self._get_dialog_form_item(label_text)
            # 多种定位策略
            xpath_candidates = [
                './/input[@type="datetime-local"]',
                './/input[contains(@class,"el-date-editor")]',
                './/input[contains(@class,"el-date")]',
                './/input[@placeholder and contains(@placeholder,"日期")]',
                './/input[@placeholder and contains(@placeholder,"时间")]',
                './/input',
            ]

            input_el = None
            for xpath in xpath_candidates:
                try:
                    input_el = item.find_element(By.XPATH, xpath)
                    logger.debug("找到输入框: %s", xpath)
                    break
                except Exception:
                    continue

            if input_el is None:
                raise Exception("未找到日期时间输入框")

            self._scroll_into_view(input_el)
            self.wait_vue_stable()

            # 尝试移除 readonly 属性（如果有）
            self.driver.execute_script("arguments[0].removeAttribute('readonly');", input_el)
            self.wait_vue_stable()

            # 清空并输入值
            try:
                input_el.send_keys(Keys.CONTROL + "a")
                input_el.send_keys(Keys.DELETE)
            except Exception:
                self.driver.execute_script("arguments[0].value = '';", input_el)

            if value:
                # Element Plus datetime 需要 ISO 格式 T 分隔符
                formatted_value = value.replace('/', '-').replace(' ', 'T')
                input_el.send_keys(formatted_value)
                self.wait_vue_stable()
                # 触发 Vue v-model 绑定: input → change → blur
                self.driver.execute_script(
                    "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
                    "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));"
                    "arguments[0].dispatchEvent(new Event('blur', {bubbles:true}));"
                    "arguments[0].dispatchEvent(new KeyboardEvent('keyup', {bubbles:true}));",
                    input_el,
                )
            logger.info("成功输入日期时间: %s = %s", label_text, value)
        except Exception as e:
            logger.warning("输入日期时间 %s 失败: %s", label_text, e)
            # 终极回退：用 JavaScript 查找并设置
            try:
                js_script = f'''
                    var labels = document.querySelectorAll('label');
                    for (var i = 0; i < labels.length; i++) {{
                        if (labels[i].textContent && labels[i].textContent.includes("{label_text}")) {{
                            var input = labels[i].parentElement.querySelector('input');
                            if (input) {{
                                input.removeAttribute('readonly');
                                input.value = "{value}";
                                input.dispatchEvent(new Event('input', {{bubbles:true}}));
                                input.dispatchEvent(new Event('change', {{bubbles:true}}));
                                return true;
                            }}
                        }}
                    }}
                    return false;
                '''
                result = self.driver.execute_script(js_script)
                if result:
                    logger.info("通过JavaScript成功输入日期时间: %s", label_text)
                    return
            except Exception as e2:
                logger.warning("JavaScript回退也失败: %s", e2)

    def get_visible_select_options(self):
        """获取当前可见下拉框的所有选项文本"""
        xpaths = [
            '//li[contains(@class,"el-select-dropdown__item")]',
            '//div[contains(@class,"el-popper") and not(contains(@style,"display: none"))]'
            '//li[contains(@class,"el-select-dropdown__item")]',
            '//div[contains(@class,"el-select-dropdown")]'
            '//li[contains(@class,"el-select-dropdown__item")]',
        ]
        options = []
        for xp in xpaths:
            try:
                els = self.driver.find_elements(By.XPATH, xp)
                for el in els:
                    try:
                        text = (el.text or "").strip()
                        if text and text not in options:
                            options.append(text)
                    except Exception:
                        pass
            except Exception:
                pass
        return options

    def select_dialog_option(self, label_text, option_text=None):
        """在弹窗中选择下拉选项，优先匹配指定文本，失败则选第一个可用选项"""
        self._open_dialog_select(label_text)
        self.wait_vue_stable()
        available = self.get_visible_select_options()
        logger.info("'%s' 可用选项: %s", label_text, available)

        if option_text:
            if self._select_option_by_text(option_text):
                return
            logger.warning("未找到 '%s'，尝试第一个", option_text)

        if available:
            if self._select_option_by_text(available[0]):
                return

        raise Exception(f"选择 {label_text} 的选项失败，可用选项: {available}")

    def click_dialog_confirm(self):
        """点击弹窗确定按钮"""
        locators = [
            self.DIALOG_CONFIRM,
            (
                By.XPATH,
                '(//footer[contains(@class,"el-dialog__footer")]'
                '//button[.//span[normalize-space(.)="确定"]])[last()]',
            ),
            (
                By.XPATH,
                '(//div[contains(@class,"el-dialog")])[last()]'
                '//div[contains(@class,"el-dialog__footer")]'
                '//button[contains(@class,"el-button--primary")]',
            ),
        ]
        for loc in locators:
            try:
                btn = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(loc))
                if btn.is_displayed():
                    self._js_click_el(btn)
                    self.wait_vue_stable()
                    return
            except Exception:
                continue
        raise TimeoutException("未找到弹窗确定按钮")

    def click_dialog_cancel(self):
        """点击弹窗取消按钮"""
        locators = [
            self.DIALOG_CANCEL,
            (
                By.XPATH,
                '(//footer[contains(@class,"el-dialog__footer")]'
                '//button[.//span[normalize-space(.)="取消"]])[last()]',
            ),
        ]
        for loc in locators:
            try:
                btn = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(loc))
                if btn.is_displayed():
                    self._js_click_el(btn)
                    self.wait_vue_stable()
                    return
            except Exception:
                continue

    def wait_dialog_closed(self, timeout=5):
        """等待弹窗关闭"""
        try:
            self.wait_dialog_close(timeout)
            return True
        except Exception:
            return False

    # ==================== 表格行操作 ====================

    def click_row_action(self, exam_name, action_text):
        """根据考试名称点击行内操作按钮"""
        xpath_candidates = [
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td//div[contains(normalize-space(.), "{exam_name}")]]'
            f'//button[.//span[contains(normalize-space(.), "{action_text}")]]',
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td//*[contains(text(), "{exam_name}")]]'
            f'//button[.//span[contains(text(), "{action_text}")]]',
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td[1]//*[contains(text(), "{exam_name}")]]'
            f'//td[last()]//button[.//span[contains(text(), "{action_text}")]]',
        ]
        for xpath in xpath_candidates:
            try:
                btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                self._js_click_el(btn)
                self.wait_vue_stable()
                return True
            except Exception:
                continue
        return False

    def confirm_message_box(self, action_name="操作"):
        """确认消息确认框"""
        try:
            super().confirm_message_box()
        except Exception:
            # 兜底：使用自定义定位器
            locators = [
                self.MESSAGEBOX_CONFIRM,
                (
                    By.XPATH,
                    '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]'
                    '//div[contains(@class,"el-message-box")])[last()]'
                    '//button[.//span[normalize-space(.)="确定"]]',
                ),
            ]
            for loc in locators:
                try:
                    btn = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(loc))
                    if btn.is_displayed():
                        self._js_click_el(btn)
                        self.wait_vue_stable()
                        return
                except Exception:
                    continue
            raise TimeoutException(f"未找到{action_name}确认框的确定按钮")

    def is_exam_name_present(self, exam_name):
        """判断列表中是否存在指定考试名称"""
        try:
            names = self.get_column_data(self.COL_EXAM_NAME)
            return any(exam_name in n for n in names)
        except Exception:
            return False

    def search_exam_by_name(self, exam_name):
        """按考试名称搜索"""
        self.click_reset()
        self.input_search_name(exam_name)
        self.click_search()

    # ==================== 考试详情 ====================

    def get_detail_exam_name(self):
        """获取详情页的考试名称"""
        try:
            el = self.find_visible(self.DETAIL_EXAM_NAME, timeout=5)
            return el.text.strip()
        except Exception:
            return ""

    def click_detail_back(self):
        """点击详情页返回按钮"""
        back_btn = (By.XPATH, '//button[.//span[contains(text(),"返回")]]')
        try:
            self.click(back_btn)
        except Exception:
            pass

    # ==================== 新增考试流程 ====================

    def add_exam_minimal(self, exam_name, paper_name=None):
        """新增考试（必选字段），自动选择第一个可用试卷，返回操作提示"""
        self.click_add()
        self.input_dialog_field("考试名称", exam_name)

        # 关联试卷：优先指定名称，失败则选第一个
        if paper_name:
            try:
                self.select_dialog_option("关联试卷", paper_name)
            except Exception as e:
                logger.warning("选择试卷 '%s' 失败: %s", paper_name, e)
                self.select_dialog_option("关联试卷", None)
        else:
            self.select_dialog_option("关联试卷", None)

        # 尝试点击确定按钮，失败则返回错误信息（不抛出异常）
        try:
            self.click_dialog_confirm()
        except Exception as e:
            logger.warning("点击确定按钮失败: %s", e)
            # 尝试使用其他方式提交表单
            try:
                save_btn = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, '//button[.//span[normalize-space(.)="保存"]]')
                    )
                )
                self._js_click_el(save_btn)
                self.wait_vue_stable()
            except Exception:
                return f"提交失败: {e}"

        if not self.wait_dialog_closed(timeout=3):
            errors = self.get_form_error_texts()
            if errors:
                logger.warning("表单校验错误: %s", errors)
                self.click_dialog_cancel()
                return f"表单校验失败: {errors}"
        toast = self.get_toast(timeout=4)
        return toast

    def select_students(self, student_name="test"):
        """在新增考试弹窗中选择参与学员"""
        logger.info("选择参与学员: %s", student_name)
        try:
            # 1. 点击"选择学员"按钮
            btn = self.find_clickable(self.STUDENT_SELECT_BUTTON)
            self._js_click_el(btn)
            logger.info("已点击选择学员按钮")
            self.wait_vue_stable()

            # 2. 等待选择对象弹窗
            self.find_visible(self.STUDENT_SELECT_DIALOG)
            logger.info("选择对象弹窗已打开")

            # 3. 搜索学员
            try:
                search_input = self.find(self.STUDENT_SEARCH_INPUT)
                search_input.clear()
                search_input.send_keys(student_name)
                self.wait_vue_stable()
                search_input.send_keys(Keys.ENTER)
                self.wait_vue_stable()
                logger.info("已搜索学员: %s", student_name)
            except Exception as e:
                logger.warning("搜索学员输入框未找到: %s", e)

            # 4. 在人员列表中勾选目标学员
            js_select_student = f"""
                var rows = document.querySelectorAll('.el-dialog tr.el-table__row');
                for (var i = 0; i < rows.length; i++) {{
                    var nameCell = rows[i].querySelector('td:nth-child(3) .cell');
                    if (nameCell && nameCell.textContent.trim() === "{student_name}") {{
                        var checkbox = rows[i].querySelector('.el-checkbox__original');
                        if (checkbox && !checkbox.checked) {{
                            checkbox.click();
                            return true;
                        }}
                    }}
                }}
                return false;
            """
            result = self.driver.execute_script(js_select_student)
            if result:
                logger.info("已勾选学员: %s", student_name)
            else:
                logger.warning("未找到学员: %s，尝试勾选第一个", student_name)
                self.driver.execute_script("""
                    var checkbox = document.querySelector('.el-dialog tr.el-table__row .el-checkbox__original');
                    if (checkbox) checkbox.click();
                """)
            self.wait_vue_stable()

            # 5. 点击确认选择
            confirm_btn = self.find_clickable(self.STUDENT_CONFIRM_BUTTON)
            self._js_click_el(confirm_btn)
            logger.info("已确认选择学员")
            self.wait_vue_stable()

        except Exception as e:
            logger.error("选择学员失败: %s", e)

    def add_exam_full(
        self,
        exam_name,
        paper_name=None,
        start_time="2026-05-16 09:00",
        end_time="2026-05-17 18:00",
        duration=45,
        exam_times="不限制",
        screen_rule="不限制",
        pass_score=90,
        desc="自动化测试创建的考试",
        select_student="test",
    ):
        """新增考试（全部字段），返回操作提示"""
        self.click_add()
        self.input_dialog_field("考试名称", exam_name)

        # 关联试卷：优先指定名称，失败则选第一个
        if paper_name:
            try:
                self.select_dialog_option("关联试卷", paper_name)
            except Exception:
                logger.warning("选择试卷 '%s' 失败，尝试第一个可用选项", paper_name)
                try:
                    self.select_dialog_option("关联试卷", None)
                except Exception as e:
                    logger.warning("选择试卷失败: %s", e)
        else:
            try:
                self.select_dialog_option("关联试卷", None)
            except Exception as e:
                logger.warning("选择试卷失败: %s", e)

        if start_time:
            try:
                self.input_dialog_datetime("开始时间", start_time)
            except Exception as e:
                logger.warning("输入开始时间失败: %s", e)
        if end_time:
            try:
                self.input_dialog_datetime("结束时间", end_time)
            except Exception as e:
                logger.warning("输入结束时间失败: %s", e)

        try:
            self.input_dialog_field("考试时长", str(duration))
        except Exception as e:
            logger.warning("输入考试时长失败: %s", e)

        try:
            self.select_dialog_option("考试次数", exam_times)
        except Exception as e:
            logger.warning("选择考试次数失败: %s", e)

        try:
            self.select_dialog_option("切屏规则", screen_rule)
        except Exception as e:
            logger.warning("选择切屏规则失败: %s", e)

        try:
            self.input_dialog_field("及格分数", str(pass_score))
        except Exception as e:
            logger.warning("输入及格分数失败: %s", e)

        # 选择参与学员
        if select_student:
            try:
                self.select_students(select_student)
            except Exception as e:
                logger.warning("选择学员失败: %s", e)

        if desc:
            try:
                item = self._get_dialog_form_item("考试说明")
                textarea = item.find_element(By.XPATH, './/textarea')
                textarea.send_keys(desc)
            except Exception as e:
                logger.warning("输入考试说明失败: %s", e)

        # 尝试点击确定按钮，失败则返回错误信息（不抛出异常）
        try:
            self.click_dialog_confirm()
        except Exception as e:
            logger.warning("点击确定按钮失败: %s", e)
            try:
                save_btn = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, '//button[.//span[normalize-space(.)="保存"]]')
                    )
                )
                self._js_click_el(save_btn)
                self.wait_vue_stable()
            except Exception as e2:
                return f"提交失败: {e2}"

        if not self.wait_dialog_closed(timeout=3):
            errors = self.get_form_error_texts()
            if errors:
                logger.warning("表单校验错误: %s", errors)
                self.click_dialog_cancel()
                return f"表单校验失败: {errors}"
        toast = self.get_toast(timeout=4)
        return toast

    def delete_exam(self, exam_name):
        """删除指定考试"""
        self.search_exam_by_name(exam_name)
        if self.get_table_row_count() == 0:
            raise AssertionError(f"未查询到待删除考试: {exam_name}")
        self.click_row_action(exam_name, self.OPERATION_DELETE)
        self.confirm_message_box()
        toast = self.get_toast(timeout=4)
        self.search_exam_by_name(exam_name)
        present = self.get_table_row_count() > 0
        return toast, not present

    def toggle_publish_status(self, exam_name):
        """切换发布/取消发布状态"""
        for action in [self.OPERATION_PUBLISH, self.OPERATION_UNPUBLISH]:
            clicked = self.click_row_action(exam_name, action)
            if clicked:
                return action
        return None
