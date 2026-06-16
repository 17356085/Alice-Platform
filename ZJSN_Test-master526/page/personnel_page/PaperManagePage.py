"""试卷管理页面操作类"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class PaperManagePage(BasePage):
    """试卷管理页面操作"""

    # ==================== 导航定位 ====================

    # 同级菜单跳转（跨模块跳转）
    COURSE_MANAGEMENT = (By.CSS_SELECTOR, 'a[href*="course"] li div.cursor-pointer')
    TRAIN_PLAN_MANAGEMENT = (By.CSS_SELECTOR, 'a[href*="train-plan"] li div.cursor-pointer')
    QUESTION_BANK = (By.CSS_SELECTOR, 'a[href*="question-bank"] li div.cursor-pointer')

    # ==================== 搜索区域 ====================
    SEARCH_NAME_INPUT = (By.CSS_SELECTOR, 'input[placeholder*="试卷名称"]')
    SEARCH_FORM = (By.XPATH, '//div[contains(@class,"el-form")][.//input[contains(@placeholder,"试卷名称")]]')
    SEARCH_CATEGORY_SELECT = (By.XPATH, '//div[contains(@class,"el-form")][.//input[contains(@placeholder,"试卷名称")]]//div[contains(@class,"el-select")][1]')
    SEARCH_MODE_SELECT = (By.XPATH, '//div[contains(@class,"el-form")][.//input[contains(@placeholder,"试卷名称")]]//div[contains(@class,"el-select")][2]')
    SEARCH_STATUS_SELECT = (By.XPATH, '//div[contains(@class,"el-form")][.//input[contains(@placeholder,"试卷名称")]]//div[contains(@class,"el-select")][3]')
    SEARCH_BUTTON = (By.XPATH, '//button[.//span[contains(normalize-space(.),"查询") or contains(normalize-space(.),"搜索")]]')
    RESET_BUTTON = (By.XPATH, '//button[.//span[contains(normalize-space(.),"重置")]]')

    # ==================== 工具栏 ====================
    ADD_BUTTON = (By.XPATH, '//button[.//span[contains(normalize-space(.),"新增试卷") or contains(normalize-space(.),"新增")]]')

    # ==================== 表格 ====================
    TABLE_ROWS = (By.CSS_SELECTOR, '.el-table__body-wrapper tbody tr.el-table__row')
    TABLE_ALL_ROWS = (By.CSS_SELECTOR, '.el-table__body-wrapper tbody tr.el-table__row')
    TABLE_COLUMN_HEADERS = (By.XPATH, '//div[contains(@class,"el-table__header-wrapper")]//th//div[contains(@class,"cell")]')

    # 表格列索引（用于按列获取数据）
    COL_PAPER_NAME = 1
    COL_CATEGORY = 2
    COL_MODE = 3
    COL_QUESTION_COUNT = 4
    COL_TOTAL_SCORE = 5
    COL_DURATION = 6
    COL_PASS_SCORE = 7
    COL_EXAMINEE_COUNT = 8
    COL_STATUS = 9
    COL_OPERATIONS = 10

    # ==================== 分页 ====================
    TOTAL_COUNT = (By.CSS_SELECTOR, '.el-pagination__total')
    PAGE_SIZE_SELECT = (By.CSS_SELECTOR, '.el-pagination .el-select__wrapper')
    NEXT_PAGE_BUTTON = (By.CSS_SELECTOR, '.el-pagination .btn-next')
    PREV_PAGE_BUTTON = (By.CSS_SELECTOR, '.el-pagination .btn-prev')
    CURRENT_PAGE = (By.XPATH, '//div[contains(@class,"el-pagination")]//button[contains(@class,"is-active") or contains(@class,"active")]')
    PAGE_SIZE_OPTION = '//li[contains(@class,"el-select-dropdown__item") and contains(., "{size}")]'

    # ==================== 行内操作按钮 ====================
    TABLE_VIEW_BUTTON = (By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[contains(text(),"查看")]]')
    TABLE_EDIT_BUTTON = (By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[contains(text(),"编辑")]]')
    TABLE_DELETE_BUTTON = (By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[contains(text(),"删除")]]')
    TABLE_PUBLISH_BUTTON = (By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[contains(text(),"发布")]]')
    TABLE_STOP_BUTTON = (By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[contains(text(),"停用")]]')

    # ==================== 确认弹窗 ====================
    CONFIRM_DIALOG = (By.XPATH, '//div[contains(@class,"el-message-box")]')
    CONFIRM_OK_BUTTON = (By.XPATH, '//div[contains(@class,"el-message-box")]//button[.//span[contains(normalize-space(.),"确定")]]')
    CONFIRM_CANCEL_BUTTON = (By.XPATH, '//div[contains(@class,"el-message-box")]//button[.//span[contains(normalize-space(.),"取消")]]')
    CONFIRM_DIALOG_TEXT = (By.XPATH, '//div[contains(@class,"el-message-box")]//p')

    # ==================== Toast ====================
    TOAST_TEXT = (By.CSS_SELECTOR, ".el-message__content")
    TOAST_TEXT_FALLBACK = (By.CSS_SELECTOR, 'div[id^="message_"] p, div[id^="message_"] .el-message__content, div[id^="message_"]')

    # ==================== 新增试卷 — 组卷方式选择弹窗 ====================
    MODE_DIALOG = (By.CSS_SELECTOR, 'div[role="dialog"]:not([style*="display: none"])')
    # 三种组卷方式选项：优先匹配标题/说明所在卡片，再回退到标题文本本身
    MODE_FIXED = (By.XPATH, '//div[contains(@class,"mode-card") and .//*[contains(normalize-space(.),"固定组卷")]]')
    MODE_RANDOM = (By.XPATH, '//div[contains(@class,"mode-card") and .//*[contains(normalize-space(.),"随机组卷")]]')
    MODE_RULE = (By.XPATH, '//div[contains(@class,"mode-card") and .//*[contains(normalize-space(.),"规则组卷")]]')
    MODE_FIXED_FALLBACK = (By.XPATH, '//div[contains(@class,"mode-title") and contains(normalize-space(.),"固定组卷")]')
    MODE_RANDOM_FALLBACK = (By.XPATH, '//div[contains(@class,"mode-title") and contains(normalize-space(.),"随机组卷")]')
    MODE_RULE_FALLBACK = (By.XPATH, '//div[contains(@class,"mode-title") and contains(normalize-space(.),"规则组卷")]')

    # ==================== 创建/编辑试卷 — 步骤1：基本信息 ====================
    # 【待确认】以下是基于原型推断的定位，实际系统可能不同
    STEP1_PAPER_NAME_INPUT = (By.CSS_SELECTOR, 'input[placeholder*="请输入试卷名称"]')
    STEP1_CATEGORY_SELECT = (By.XPATH, '(//div[contains(@class,"el-form")]//div[contains(@class,"el-select")])[1]')
    STEP1_DURATION_INPUT = (By.XPATH, '(//div[contains(@class,"el-form")]//input[@type="number"])[1]')
    STEP1_PASS_SCORE_INPUT = (By.XPATH, '(//div[contains(@class,"el-form")]//input[@type="number"])[2]')
    STEP1_DESC_TEXTAREA = (By.CSS_SELECTOR, 'textarea[placeholder*="请输入试卷说明"]')
    STEP1_NEXT_BUTTON = (By.XPATH, '//button[.//span[contains(normalize-space(.),"下一步") or contains(normalize-space(.),"下一页")]]')
    STEP1_PREV_BUTTON = (By.XPATH, '//button[.//span[contains(text(),"上一页")]]')

    # ==================== 创建试卷 — 步骤2：试题配置 ====================
    # 通用
    STEP2_NEXT_BUTTON = (By.XPATH, '//button[.//span[contains(normalize-space(.),"下一页") or contains(normalize-space(.),"下一步")]]')

    # --- 固定组卷 ---
    # 使用按钮文本定位，避免依赖绝对 XPath
    ADD_QUESTION_BUTTON = (By.XPATH, '//button[.//span[contains(normalize-space(.),"添加试题")]]')
    ADD_QUESTION_BUTTON_FALLBACKS = [
        (By.XPATH, '//button[contains(normalize-space(.),"添加试题")]'),
        (By.XPATH, '//*[contains(normalize-space(.),"固定组卷")]/ancestor::div[contains(@class,"el-card") or contains(@class,"el-form") or contains(@class,"content")][1]//button[.//span[contains(normalize-space(.),"添加试题")]]'),
    ]
    # 【待确认】试题选择弹窗 — 搜索、勾选、确认
    QUESTION_SEARCH_INPUT = (By.CSS_SELECTOR, '.el-dialog input[placeholder*="题干"]')
    QUESTION_SEARCH_BUTTON = (By.XPATH, '//div[contains(@class,"el-dialog")]//button[.//span[contains(text(),"搜索")]]')
    QUESTION_SELECT_ALL = (By.XPATH, '//div[contains(@class,"el-dialog")]//div[contains(@class,"el-table__header-wrapper")]//label[contains(@class,"el-checkbox")]')
    QUESTION_SELECT_ALL_FALLBACK = (By.XPATH, '//div[contains(@class,"el-dialog")]//thead//label[contains(@class,"el-checkbox")]')
    QUESTION_CONFIRM_ADD = (By.XPATH, '//div[contains(@class,"el-dialog")]//footer//button[.//span[contains(normalize-space(.),"确认添加") or contains(normalize-space(.),"确定")]]')
    # 【待确认】固定组卷中修改各题型分值的输入框
    FIXED_SCORE_INPUT_TPL = '//div[contains(@class,"question-section") or contains(@class,"section-header")][.//*[contains(text(),"{type}")]]//input[contains(@class,"score") or @type="number"]'

    # --- 随机组卷 ---
    # 试题分类范围复选框 — 改用CSS/层级相对定位
    CATEGORY_SCOPE_CHECKBOX = (By.XPATH, '//div[contains(@class,"el-form")][.//span[contains(text(),"试题分类范围")]]//span[contains(@class,"el-checkbox__input")]')
    # 随机组卷中各题型抽取数量和分值的输入框（按表格行定位）
    RANDOM_ROW_NUM_INPUT_TPL = '//*[contains(normalize-space(.),"{type}")]/ancestor::tr[1]//input[@type="number" or contains(@class,"el-input__inner")][1]'
    RANDOM_ROW_SCORE_INPUT_TPL = '//*[contains(normalize-space(.),"{type}")]/ancestor::tr[1]//input[@type="number" or contains(@class,"el-input__inner")][2]'
    # 单选题增加按钮（+）
    RANDOM_INCREASE_BTN_TPL = '//*[contains(normalize-space(.),"单选题")]/ancestor::tr[1]//span[contains(@class,"el-input-number__increase")]'
    # 更精确的定位：表格行内第一个 el-input-number 组件的输入框（抽取数量）
    RANDOM_ROW_NUM_INPUT_CSS = 'tr:has(td:first-child:contains("{type}")) .el-input-number:first-child input'
    RANDOM_ROW_NUM_INPUT_JS = 'document.querySelectorAll("table tbody tr")[{row_idx}].querySelectorAll(".el-input-number input")[0]'
    PREVIEW_RANDOM_BUTTON = (By.XPATH, '//button[.//span[contains(text(),"预览抽题结果")]]')
    REFRESH_RANDOM_BUTTON = (By.XPATH, '//button[.//span[contains(text(),"重新抽题")]]')

    # --- 规则组卷 ---
    # 难度权重滑块（多种定位方式）
    RULE_EASY_WEIGHT_INPUT = (By.XPATH, '//label[contains(text(),"简单")]/following::input[@type="range"][1]')
    RULE_MEDIUM_WEIGHT_INPUT = (By.XPATH, '//label[contains(text(),"中等")]/following::input[@type="range"][1]')
    RULE_HARD_WEIGHT_INPUT = (By.XPATH, '//label[contains(text(),"困难")]/following::input[@type="range"][1]')
    # 备用定位器 - 基于页面结构
    RULE_WEIGHT_SLIDES = (By.CSS_SELECTOR, 'input[type="range"]')
    RULE_EASY_WEIGHT_FALLBACK = (By.XPATH, '//div[contains(@class,"el-slider") and .//span[contains(text(),"简单")]]//input')
    RULE_MEDIUM_WEIGHT_FALLBACK = (By.XPATH, '//div[contains(@class,"el-slider") and .//span[contains(text(),"中等")]]//input')
    RULE_HARD_WEIGHT_FALLBACK = (By.XPATH, '//div[contains(@class,"el-slider") and .//span[contains(text(),"困难")]]//input')
    # 题型配置（按表格行定位）
    RULE_ROW_NUM_INPUT_TPL = '//h4[contains(text(),"题型配置")]/following::table[1]//tr[td[contains(text(),"{type}")]]//input[1]'
    RULE_ROW_SCORE_INPUT_TPL = '//h4[contains(text(),"题型配置")]/following::table[1]//tr[td[contains(text(),"{type}")]]//input[2]'
    # 备用定位器 - 更通用的题型配置定位
    RULE_CONFIG_TABLE = (By.XPATH, '//table[contains(@class,"el-table")]')
    RULE_QUESTION_TYPE_ROW_TPL = '//tr[.//*[contains(normalize-space(.),"{qtype}")]]'

    # ==================== 创建试卷 — 步骤3：预览确认 ====================
    PUBLISH_BUTTON = (By.XPATH, '//button[.//span[contains(normalize-space(.),"发布试卷") or contains(normalize-space(.),"发布")]]')
    SAVE_DRAFT_BUTTON = (By.XPATH, '//button[.//span[contains(normalize-space(.),"保存草稿") or contains(normalize-space(.),"保存")]]')
    CONFIRM_PUBLISH_BUTTON = (By.XPATH, '//div[contains(@class,"el-message-box") or contains(@class,"el-dialog")]//button[.//span[contains(normalize-space(.),"确定") or contains(normalize-space(.),"确认")]]')

    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)
        self.logger = logging.getLogger(__name__)

    # ==================== 通用操作 ====================

    def _click_js(self, locator):
        """JS 点击，避免遮挡"""
        try:
            el = self.wait.until(EC.presence_of_element_located(locator))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'nearest'});", el)
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", el)
            return el
        except Exception as e:
            self.logger.error("JS点击失败: %s, 错误: %s", locator, e)
            raise

    def _click_action(self, locator):
        """使用 ActionChains 真实点击，确保 Vue 事件被触发"""
        el = self.wait.until(EC.presence_of_element_located(locator))
        ActionChains(self.driver).move_to_element(el).click().perform()
        return el

    def _wait_settled(self, timeout=15):
        """等待页面加载完成（旋转图标消失/加载遮罩消失）"""
        self._wait_loading_gone(timeout=timeout)
        self.wait_vue_stable()

    def _select_option_by_text(self, text):
        """在下拉弹出框中选择文本匹配的选项"""
        option_xpath = f'//li[contains(@class,"el-select-dropdown__item") and contains(normalize-space(.),"{text}")]'
        try:
            option = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, option_xpath))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", option)
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", option)
            self.wait_vue_stable()
            return True
        except Exception:
            return False

    def get_toast_text(self):
        """获取 Toast 提示文本"""
        candidates = [self.TOAST_TEXT, self.TOAST_TEXT_FALLBACK]
        for loc in candidates:
            try:
                el = WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located(loc))
                text = el.text.strip()
                if text:
                    return text
            except Exception:
                pass
        return ""

    # ==================== 导航 ====================

    def navigate_to_paper_management(self):
        self.navigate_to("人员管理", "培训管理", "试卷管理")
        self._wait_settled(timeout=12)

    def navigate_to_course_management(self):
        """导航到课程管理（通过 SidebarNavigator）"""
        self.navigate_to("人员管理", "培训管理", "课程管理")
        self._wait_settled()

    def navigate_to_train_plan(self):
        """导航到培训计划管理（通过 SidebarNavigator）"""
        self.navigate_to("人员管理", "培训管理", "培训计划")
        self._wait_settled()

    def navigate_to_question_bank(self):
        """导航到题库管理（通过 SidebarNavigator）"""
        self.navigate_to("人员管理", "培训管理", "题库管理")
        self._wait_settled()

    def _switch_to_sibling(self, target_locator):
        """在已展开的同级菜单中切换到目标页面"""
        el = self.wait.until(EC.element_to_be_clickable(target_locator))
        self.driver.execute_script("arguments[0].click();", el)
        self.wait_vue_stable()

    def switch_to_paper_management(self):
        """切回试卷管理页面，优先同级切换避免菜单折叠"""
        try:
            close_buttons = self.driver.find_elements(
                By.XPATH, '//button[.//span[contains(text(),"关闭")] or .//span[contains(text(),"取消")] or @aria-label="Close"]'
            )
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
            ("侧边栏导航", lambda: self.navigate_to("人员管理", "培训管理", "试卷管理")),
        ]
        for method_name, method_fn in methods:
            try:
                method_fn()
                try:
                    self.wait.until(
                        EC.presence_of_element_located(
                            (By.XPATH, '//div[contains(@class,"el-table")]')
                        )
                    )
                    self.logger.info("成功导航到试卷管理页面（%s）", method_name)
                    return
                except Exception:
                    self.logger.warning("%s 后页面验证失败，尝试下一种方式", method_name)
            except Exception as e:
                self.logger.warning("%s 失败: %s", method_name, e)

        raise Exception("无法导航到试卷管理页面")

    # ==================== 页面状态验证 ====================

    def get_page_title_text(self):
        """获取页面主标题"""
        candidates = [
            '//header//h2',
            '//h2[not(ancestor::div[contains(@style,"display: none")])]',
            '//div[contains(@class,"page-header") or contains(@class,"page-title")]//h2',
            '//section//h2 | //main//h2',
        ]
        for xpath in candidates:
            try:
                el = self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
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

    def get_table_row_count(self):
        """获取当前页表格行数"""
        try:
            rows = self.driver.find_elements(*self.TABLE_ALL_ROWS)
            return len(rows)
        except Exception:
            return 0

    def is_table_has_data(self):
        """判断表格是否有数据"""
        return self.get_table_row_count() > 0

    def get_first_row_data(self):
        """获取第一行所有列的数据（用于验证分页后数据变化）"""
        try:
            row = self.wait.until(EC.presence_of_element_located(self.TABLE_ALL_ROWS))
            cells = row.find_elements(By.XPATH, './/td//div[contains(@class,"el-table__cell")]')
            if not cells:
                cells = row.find_elements(By.TAG_NAME, 'td')
            return [cell.text.strip() for cell in cells]
        except Exception:
            return []

    # ==================== 搜索 ====================

    def input_search_name(self, value):
        """输入搜索关键词（试卷名称）"""
        try:
            el = self.wait.until(EC.element_to_be_clickable(self.SEARCH_NAME_INPUT))
            el.clear()
            el.send_keys(value)
            return True
        except Exception:
            return False

    def click_search(self):
        """点击查询按钮"""
        try:
            self._click_action(self.SEARCH_BUTTON)
        except Exception:
            btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, '//button[.//span[contains(normalize-space(.),"搜索") or contains(normalize-space(.),"查询")]]'))
            )
            self.driver.execute_script("arguments[0].click();", btn)
        self._wait_settled()

    def click_reset(self):
        """点击重置按钮"""
        self._click_js(self.RESET_BUTTON)
        self._wait_settled()

    def select_search_category(self, category_text):
        """选择搜索条件中的试卷分类"""
        self.logger.info("尝试选择搜索分类: %s", category_text)
        return self._select_search_dropdown_by_label("培训分类", category_text)

    def select_search_mode(self, mode_text):
        """选择搜索条件中的组卷方式"""
        self.logger.info("尝试选择组卷方式: %s", mode_text)
        return self._select_search_dropdown_by_label("组卷方式", mode_text)

    def select_search_status(self, status_text):
        """选择搜索条件中的状态"""
        self.logger.info("尝试选择状态: %s", status_text)
        return self._select_search_dropdown_by_label("试卷状态", status_text)

    def _select_search_dropdown_by_label(self, label_text, option_text):
        """根据标签文本选择搜索下拉框选项 - 基于真实HTML结构

        HTML结构: search-item → label(标签文本) + el-select(下拉框)
        """
        self.logger.info("开始选择下拉框 [标签:%s, 选项:%s]", label_text, option_text)

        # 步骤1: 通过label文本找到对应的search-item，然后找到相邻的el-select
        js_find_and_select = f'''
            var labels = document.querySelectorAll('label');
            var targetSelect = null;

            for (var i = 0; i < labels.length; i++) {{
                var labelText = labels[i].textContent ? labels[i].textContent.trim() : '';
                if (labelText === "{label_text}" || labelText.indexOf("{label_text}") !== -1) {{
                    var parent = labels[i].closest('.search-item, .el-form-item');
                    if (parent) {{
                        targetSelect = parent.querySelector('.el-select');
                        if (targetSelect) break;
                    }}
                }}
            }}

            if (!targetSelect) {{
                var allSelects = document.querySelectorAll('.el-select');
                for (var j = 0; j < allSelects.length; j++) {{
                    var placeholder = allSelects[j].querySelector('.el-select__placeholder');
                    if (placeholder) {{
                        var phText = placeholder.textContent ? placeholder.textContent.trim() : '';
                        if (phText.indexOf("{label_text}") !== -1) {{
                            targetSelect = allSelects[j];
                            break;
                        }}
                    }}
                }}
            }}

            if (!targetSelect) {{
                console.log("未找到标签为 {label_text} 的下拉框");
                return {{success: false, error: "未找到下拉框"}};
            }}

            var trigger = targetSelect.querySelector('.el-select__wrapper, .el-select__selection, [role="combobox"]');
            if (!trigger) trigger = targetSelect;
            trigger.click();

            return {{success: true, selectId: targetSelect.id || j}};
        '''

        try:
            result = self.driver.execute_script(js_find_and_select)
            self.logger.info("点击下拉框结果: %s", result)
            if not result or not result.get('success'):
                self.logger.warning("未找到标签为 '%s' 的下拉框", label_text)
                return False
        except Exception as e:
            self.logger.warning("点击下拉框失败: %s", e)
            return False

        # 步骤2: 等待下拉展开并选择选项
        self.wait_vue_stable()

        js_select_option = f'''
            var dropdowns = document.querySelectorAll('.el-select-dropdown, .el-popper.is-light');
            var targetDropdown = null;

            for (var i = 0; i < dropdowns.length; i++) {{
                var style = window.getComputedStyle(dropdowns[i]);
                var rect = dropdowns[i].getBoundingClientRect();
                if (style.display !== 'none' && style.visibility !== 'hidden' && rect.height > 0) {{
                    targetDropdown = dropdowns[i];
                    break;
                }}
            }}

            if (!targetDropdown) {{
                console.log("未找到展开的下拉选项");
                return false;
            }}

            var items = targetDropdown.querySelectorAll('li.el-select-dropdown__item');
            console.log("找到 " + items.length + " 个选项");

            for (var j = 0; j < items.length; j++) {{
                var itemText = items[j].textContent ? items[j].textContent.trim() : '';
                console.log("选项 " + j + ": " + itemText);
                if (itemText === "{option_text}" || itemText.indexOf("{option_text}") !== -1) {{
                    items[j].click();
                    console.log("成功选择: " + itemText);
                    return true;
                }}
            }}

            console.log("未找到选项: {option_text}");
            return false;
        '''

        try:
            result = self.driver.execute_script(js_select_option)
            self.wait_vue_stable()

            if result:
                self.logger.info("成功选择 '%s'", option_text)
                return True
            else:
                self.logger.warning("未在下拉选项中找到 '%s'", option_text)
                return False
        except Exception as e:
            self.logger.warning("选择选项失败: %s", e)
            return False

    def _get_selected_search_value(self, label_text):
        """获取指定标签下拉框的当前选中值"""
        try:
            js_get_value = f'''
                var labels = document.querySelectorAll('label');
                for (var i = 0; i < labels.length; i++) {{
                    var text = labels[i].textContent ? labels[i].textContent.trim() : '';
                    if (text === "{label_text}" || text.indexOf("{label_text}") !== -1) {{
                        var parent = labels[i].closest('.search-item, .el-form-item');
                        if (parent) {{
                            var select = parent.querySelector('.el-select');
                            if (select) {{
                                var selected = select.querySelector('.el-select__selected-item');
                                if (selected) return selected.textContent.trim();
                                var placeholder = select.querySelector('.el-select__placeholder');
                                if (placeholder) return placeholder.textContent.trim();
                            }}
                        }}
                    }}
                }}
                return "";
            '''
            return self.driver.execute_script(js_get_value) or ""
        except Exception:
            return ""

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

    def click_next_page(self):
        """点击下一页"""
        self._click_js(self.NEXT_PAGE_BUTTON)
        self._wait_settled()

    def click_prev_page(self):
        """点击上一页"""
        self._click_js(self.PREV_PAGE_BUTTON)
        self._wait_settled()

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
            self._wait_settled()
        except Exception as e:
            raise Exception(f"切换每页条数失败: {e}")

    # ==================== 表格行操作 ====================

    def click_row_button(self, paper_name, button_text):
        """根据试卷名称找到对应行，点击行内操作按钮"""
        xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//*[contains(text(),"{paper_name}")]]'
            f'//button[.//span[contains(text(),"{button_text}")]]'
        )
        try:
            btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            self.wait_vue_stable()
            self.driver.execute_script("arguments[0].click();", btn)
            return True
        except Exception:
            return False

    def click_first_row_button(self, button_text):
        """点击第一行的操作按钮"""
        xpath = (
            f'(//tr[contains(@class,"el-table__row")])[1]'
            f'//button[.//span[contains(text(),"{button_text}")]]'
        )
        try:
            btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            self.driver.execute_script("arguments[0].click();", btn)
            return True
        except Exception:
            return False

    def get_first_row_paper_name(self):
        """获取第一行试卷名称"""
        try:
            for col_idx in [2, 1]:
                xpath = f'(//tr[contains(@class,"el-table__row")])[1]//td[{col_idx}]//div[contains(@class,"cell")]'
                els = self.driver.find_elements(By.XPATH, xpath)
                for el in els:
                    text = el.text.strip()
                    if text and text not in ['-', '...'] and not text.startswith('test'):
                        continue
                    if text and len(text) > 0:
                        return text
            xpath = '(//tr[contains(@class,"el-table__row")])[1]//td//div[contains(@class,"cell")]'
            els = self.driver.find_elements(By.XPATH, xpath)
            for el in els:
                text = el.text.strip()
                if text and text not in ['-', '...', '详情', '编辑', '停用', '发布', '删除', '已发布', '草稿']:
                    return text
            return None
        except Exception:
            return None

    def click_row_action_by_name(self, paper_name, action_text):
        """根据试卷名称点击对应行的操作按钮（支持详情/编辑/停用/发布/删除）"""
        row_xpath = f'//tr[contains(@class,"el-table__row")][.//*[contains(normalize-space(.),"{paper_name}")]]'
        try:
            row = self.wait.until(EC.presence_of_element_located((By.XPATH, row_xpath)))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", row)
            self.wait_vue_stable()
        except Exception:
            return False

        button_xpaths = [
            f'{row_xpath}//button[contains(normalize-space(.),"{action_text}")]',
            f'{row_xpath}//button[.//span[contains(normalize-space(.),"{action_text}")]]',
            f'{row_xpath}//td[contains(@class,"el-table__cell")][last()]//button[contains(normalize-space(.),"{action_text}")]',
            f'{row_xpath}//td[contains(@class,"el-table__cell")][last()]//button',
        ]

        for xpath in button_xpaths:
            try:
                buttons = self.driver.find_elements(By.XPATH, xpath)
                for btn in buttons:
                    btn_text = btn.text.strip() or ''
                    if action_text in btn_text:
                        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                        self.wait_vue_stable()
                        self.driver.execute_script("arguments[0].click();", btn)
                        return True
            except Exception:
                continue
        return False

    def confirm_dialog(self, confirm=True):
        """处理确认弹窗（确定/取消）"""
        try:
            self.wait.until(EC.visibility_of_element_located(self.CONFIRM_DIALOG))
            if confirm:
                btn = self.wait.until(EC.element_to_be_clickable(self.CONFIRM_OK_BUTTON))
                self.driver.execute_script("arguments[0].click();", btn)
            else:
                btn = self.wait.until(EC.element_to_be_clickable(self.CONFIRM_CANCEL_BUTTON))
                self.driver.execute_script("arguments[0].click();", btn)
            self.wait_vue_stable()
            return True
        except Exception:
            return False

    def is_confirm_dialog_visible(self):
        """判断确认弹窗是否显示"""
        try:
            return self.driver.find_element(*self.CONFIRM_DIALOG).is_displayed()
        except Exception:
            return False

    def get_confirm_dialog_text(self):
        """获取确认弹窗提示文本"""
        try:
            el = self.driver.find_element(*self.CONFIRM_DIALOG_TEXT)
            return el.text.strip()
        except Exception:
            return ''

    def get_row_status_by_name(self, paper_name):
        """根据试卷名称获取对应行的状态文本"""
        xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td[contains(normalize-space(.),"{paper_name}")]]'
            f'//td[contains(@class,"el-table__cell")][contains(.//span,"已发布") or contains(.//span,"草稿") or contains(.//span,"停用")]'
        )
        try:
            status_cell = self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            return status_cell.text.strip()
        except Exception:
            return None

    # ==================== 创建试卷 — 通用流程 ====================

    def select_paper_mode(self, mode):
        """点击新增试卷后，在弹窗中选择组卷方式

        Args:
            mode: 'fixed' | 'random' | 'rule'
        """
        self.logger.info("点击新增试卷按钮")
        self._click_action(self.ADD_BUTTON)
        self._wait_loading_gone(timeout=5)
        self.wait_vue_stable()

        mode_map = {
            'fixed': [self.MODE_FIXED, self.MODE_FIXED_FALLBACK],
            'random': [self.MODE_RANDOM, self.MODE_RANDOM_FALLBACK],
            'rule': [self.MODE_RULE, self.MODE_RULE_FALLBACK],
        }
        locators = mode_map.get(mode, [self.MODE_FIXED, self.MODE_FIXED_FALLBACK])
        mode_text = {'fixed': '固定组卷', 'random': '随机组卷', 'rule': '规则组卷'}.get(mode, '固定组卷')

        self.logger.info("选择组卷方式：%s", mode_text)
        dialog_xpath = '//div[@role="dialog" and .//*[contains(normalize-space(.),"选择组卷方式")]]'
        try:
            WebDriverWait(self.driver, 8).until(EC.presence_of_element_located((By.XPATH, dialog_xpath)))
        except Exception:
            pass

        for locator in locators:
            try:
                option = self.wait.until(EC.element_to_be_clickable(locator))
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'nearest'});", option)
                self.wait_vue_stable()
                ActionChains(self.driver).move_to_element(option).click().perform()
                self._wait_settled()
                return
            except Exception:
                continue

        self.logger.info("使用卡片/文本回退定位组卷方式")
        fallback_xpaths = [
            f'//div[@role="dialog"]//*[contains(normalize-space(.),"{mode_text}")]',
            f'//div[@role="dialog"]//div[contains(@class,"mode-card") and .//*[contains(normalize-space(.),"{mode_text}")]]',
            f'//div[@role="dialog"]//div[contains(@class,"mode-title") and contains(normalize-space(.),"{mode_text}")]'
        ]
        last_error = None
        for xpath in fallback_xpaths:
            try:
                option = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'nearest'});", option)
                self.wait_vue_stable()
                ActionChains(self.driver).move_to_element(option).click().perform()
                self._wait_settled()
                return
            except Exception as e:
                last_error = e

        self.logger.info("使用JavaScript终极回退定位组卷方式")
        try:
            js_script = f'''
                var elements = document.querySelectorAll('*');
                for (var i = 0; i < elements.length; i++) {{
                    if (elements[i].textContent && elements[i].textContent.trim() === "{mode_text}") {{
                        var el = elements[i];
                        while (el) {{
                            if (el.tagName === 'BUTTON' || el.tagName === 'DIV' && el.style.cursor === 'pointer') {{
                                el.click();
                                return true;
                            }}
                            el = el.parentElement;
                        }}
                        elements[i].click();
                        return true;
                    }}
                }}
                return false;
            '''
            result = self.driver.execute_script(js_script)
            if result:
                self._wait_loading_gone(timeout=5)
                self.wait_vue_stable()
                self.logger.info("通过JavaScript成功选择组卷方式: %s", mode_text)
                return
        except Exception as e:
            last_error = e

        raise Exception(f"选择组卷方式 '{mode_text}' 失败: {last_error}")

    def fill_step1_basic_info(self, name, category="", duration=60, pass_score=60, desc=""):
        """填写创建试卷第1步：基本信息

        Args:
            name: 试卷名称
            category: 试卷分类（空字符串则不选）
            duration: 答题时长（分钟）
            pass_score: 及格分数
            desc: 试卷说明
        """
        self.logger.info("填写试卷基本信息")

        try:
            name_input = self.wait.until(EC.element_to_be_clickable(self.STEP1_PAPER_NAME_INPUT))
            name_input.clear()
            name_input.send_keys(name)
        except Exception:
            self.logger.warning("试卷名称输入框未找到，尝试备用定位")
            name_input = self.driver.find_element(By.XPATH, '//input[@id="paperName" or contains(@placeholder,"名称")]')
            name_input.clear()
            name_input.send_keys(name)

        if category:
            self.logger.info("选择试卷分类：%s", category)
            try:
                self._click_action(self.STEP1_CATEGORY_SELECT)
                self._select_option_by_text(category)
            except Exception:
                self.logger.warning("选择试卷分类失败: %s", category)

        if duration:
            try:
                duration_input = self.wait.until(EC.presence_of_element_located(self.STEP1_DURATION_INPUT))
                self.driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true}));", duration_input, str(duration))
            except Exception:
                self.logger.warning("答题时长输入框未找到")

        if pass_score:
            try:
                score_input = self.wait.until(EC.presence_of_element_located(self.STEP1_PASS_SCORE_INPUT))
                self.driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true}));", score_input, str(pass_score))
            except Exception:
                self.logger.warning("及格分数输入框未找到")

        if desc:
            try:
                desc_input = self.wait.until(EC.element_to_be_clickable(self.STEP1_DESC_TEXTAREA))
                desc_input.clear()
                desc_input.send_keys(desc)
            except Exception:
                self.logger.warning("试卷说明输入框未找到")

        self.logger.info("点击下一步")
        try:
            btn = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.STEP1_NEXT_BUTTON))
            btn.click()
        except Exception:
            btn = self.wait.until(EC.presence_of_element_located(self.STEP1_NEXT_BUTTON))
            ActionChains(self.driver).move_to_element(btn).click().perform()
        self._wait_settled()

    def _click_with_fallbacks(self, primary_locator, fallback_locators=None, timeout=5):
        """依次尝试多个定位器点击目标元素"""
        locators = [primary_locator] + (fallback_locators or [])
        last_error = None
        for locator in locators:
            try:
                el = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(locator))
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'nearest'});", el)
                self.wait_vue_stable()
                self.driver.execute_script("arguments[0].click();", el)
                return True
            except Exception as e:
                last_error = e
        raise Exception(f"点击元素失败: {last_error}")

    def _find_and_click_in_dialog(self, locators, timeout=5):
        """在当前弹窗中依次尝试多个定位器点击"""
        last_error = None
        for locator in locators:
            try:
                el = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(locator))
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'nearest'});", el)
                self.wait_vue_stable()
                self.driver.execute_script("arguments[0].click();", el)
                return True
            except Exception as e:
                last_error = e
        raise Exception(f"在弹窗中点击元素失败: {last_error}")

    def fill_step2_fixed(self, question_keyword=""):
        """填写创建试卷第2步：固定组卷 — 添加试题

        Args:
            question_keyword: 搜索试题的关键词（空则全选）
        """
        self.logger.info("固定组卷 — 添加试题")
        try:
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(self.ADD_QUESTION_BUTTON)
            )
        except Exception:
            found = False
            for locator in self.ADD_QUESTION_BUTTON_FALLBACKS:
                try:
                    WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(locator))
                    found = True
                    break
                except Exception:
                    continue
            if not found:
                self.logger.warning("未找到'添加试题'按钮，可能未进入步骤2")
                return
        try:
            self._click_with_fallbacks(self.ADD_QUESTION_BUTTON, self.ADD_QUESTION_BUTTON_FALLBACKS, timeout=5)
        except Exception as e:
            self.logger.warning("点击'添加试题'按钮失败: %s", e)
            return
        self._wait_loading_gone(timeout=5)
        self.wait_vue_stable()

        if question_keyword:
            try:
                search_input = self.wait.until(EC.element_to_be_clickable(self.QUESTION_SEARCH_INPUT))
                search_input.clear()
                search_input.send_keys(question_keyword)
                self._click_js(self.QUESTION_SEARCH_BUTTON)
                self._wait_loading_gone(timeout=5)
                self.wait_vue_stable()
            except Exception:
                self.logger.warning("试题搜索框未找到，直接全选")

        try:
            self._find_and_click_in_dialog([self.QUESTION_SELECT_ALL, self.QUESTION_SELECT_ALL_FALLBACK], timeout=5)
            self.wait_vue_stable()
        except Exception:
            try:
                checkboxes = self.driver.find_elements(
                    By.XPATH, '//div[contains(@class,"el-dialog")]//label[contains(@class,"el-checkbox")]'
                )
                for cb in checkboxes:
                    try:
                        self.driver.execute_script("arguments[0].click();", cb)
                    except Exception:
                        pass
            except Exception:
                self.logger.warning("试题复选框未找到")

        try:
            self._find_and_click_in_dialog([self.QUESTION_CONFIRM_ADD], timeout=5)
        except Exception:
            try:
                confirm = self.driver.find_element(
                    By.XPATH, '//div[contains(@class,"el-dialog")]//footer//button[.//span[contains(normalize-space(.),"确定")]]'
                )
                self.driver.execute_script("arguments[0].click();", confirm)
            except Exception:
                self.logger.warning("确认添加按钮未找到")

        self._wait_settled()

    def fill_step2_random(self, config=None, select_category=True):
        """填写创建试卷第2步：随机组卷 — 配置抽取规则

        Args:
            config: dict，各题型配置，如
                   {'单选题': {'num': 20, 'score': 2}, '多选题': {'num': 10, 'score': 3}, ...}
            select_category: bool，是否勾选试题分类范围复选框
        """
        if select_category:
            try:
                checkbox = self.wait.until(
                    EC.element_to_be_clickable(self.CATEGORY_SCOPE_CHECKBOX)
                )
                if 'is-checked' not in checkbox.get_attribute('class'):
                    self.driver.execute_script("arguments[0].click();", checkbox)
                    self.logger.info("已勾选试题分类范围")
                    self._wait_loading_gone(timeout=5)
                    self._wait_settled(timeout=5)
            except Exception:
                self.logger.warning("试题分类范围复选框未找到或已勾选")

        if not config:
            config = {
                '单选题': {'num': 20, 'score': 2},
                '多选题': {'num': 10, 'score': 3},
                '判断题': {'num': 10, 'score': 1},
                '填空题': {'num': 10, 'score': 2},
                '简答题': {'num': 2, 'score': 10},
            }

        self.logger.info("随机组卷 — 配置各题型抽取数量和分值")
        qtype_row_map = {'单选题': 0, '多选题': 1, '判断题': 2, '填空题': 3, '简答题': 4}
        for qtype, settings in config.items():
            num = settings.get('num', 0)
            score = settings.get('score', 0)
            if num:
                success = False
                row_idx = qtype_row_map.get(qtype, 0)
                try:
                    js_set_num = f"""
                        var rows = document.querySelectorAll('table tbody tr');
                        if (rows.length > {row_idx}) {{
                            var inputs = rows[{row_idx}].querySelectorAll('.el-input-number input.el-input__inner');
                            if (inputs.length > 0) {{
                                var inp = inputs[0];
                                inp.value = '{num}';
                                inp.dispatchEvent(new Event('input', {{bubbles: true}}));
                                inp.dispatchEvent(new Event('change', {{bubbles: true}}));
                                return true;
                            }}
                        }}
                        return false;
                    """
                    result = self.driver.execute_script(js_set_num)
                    if result:
                        self.logger.info("随机组卷-%s通过JS设置抽取数量为%s", qtype, num)
                        success = True
                        self.wait_vue_stable()
                except Exception as e:
                    self.logger.warning("JS设置%s数量失败: %s", qtype, e)

                if not success and '单选题' in qtype and num == 1:
                    try:
                        increase_js = f"""
                            var rows = document.querySelectorAll('table tbody tr');
                            if (rows.length > {row_idx}) {{
                                var btn = rows[{row_idx}].querySelector('.el-input-number__increase');
                                if (btn) {{ btn.click(); return true; }}
                            }}
                            return false;
                        """
                        result = self.driver.execute_script(increase_js)
                        if result:
                            self.logger.info("随机组卷-%s通过JS点击增加按钮", qtype)
                            success = True
                            self.wait_vue_stable()
                    except Exception as e:
                        self.logger.warning("JS点击增加按钮失败: %s", e)

                if not success:
                    try:
                        num_input = self.driver.find_element(
                            By.XPATH, self.RANDOM_ROW_NUM_INPUT_TPL.format(type=qtype)
                        )
                        max_val = num_input.get_attribute('max')
                        if max_val and int(max_val) > 0:
                            num_input.clear()
                            num_input.send_keys(str(num))
                            self.logger.info("随机组卷-%s通过XPath输入抽取数量%s", qtype, num)
                            success = True
                        else:
                            self.logger.warning("随机组卷-%s题库数量为0，跳过配置", qtype)
                    except Exception:
                        self.logger.warning("随机组卷-%s抽取数量输入框未找到", qtype)

                if not success:
                    self.logger.warning("随机组卷-%s所有方法均失败，无法设置抽取数量", qtype)

            if score:
                try:
                    row_idx = qtype_row_map.get(qtype, 0)
                    js_set_score = f"""
                        var rows = document.querySelectorAll('table tbody tr');
                        if (rows.length > {row_idx}) {{
                            var inputs = rows[{row_idx}].querySelectorAll('.el-input-number input.el-input__inner');
                            if (inputs.length > 1) {{
                                var inp = inputs[1];
                                inp.value = '{score}';
                                inp.dispatchEvent(new Event('input', {{bubbles: true}}));
                                inp.dispatchEvent(new Event('change', {{bubbles: true}}));
                                return true;
                            }}
                        }}
                        return false;
                    """
                    result = self.driver.execute_script(js_set_score)
                    if result:
                        self.logger.info("随机组卷-%s通过JS设置分值为%s", qtype, score)
                    else:
                        score_input = self.driver.find_element(
                            By.XPATH, self.RANDOM_ROW_SCORE_INPUT_TPL.format(type=qtype)
                        )
                        score_input.clear()
                        score_input.send_keys(str(score))
                except Exception:
                    self.logger.warning("随机组卷-%s分值输入框未找到", qtype)

        self._wait_settled()

    def fill_step2_rule(self, weights=None, config=None):
        """填写创建试卷第2步：规则组卷 — 配置难度权重和题型

        Args:
            weights: dict，难度权重，如 {'easy': 30, 'medium': 50, 'hard': 20}
            config: dict，各题型配置，同 fill_step2_random
        """
        if weights:
            self.logger.info("规则组卷 — 配置难度权重: %s", weights)
            self._set_weight_slider('easy', weights.get('easy', 30))
            self._set_weight_slider('medium', weights.get('medium', 50))
            self._set_weight_slider('hard', weights.get('hard', 20))
            self.wait_vue_stable()

        if config:
            self.logger.info("规则组卷 — 配置各题型数量和分值")
            for qtype, settings in config.items():
                num = settings.get('num', 0)
                score = settings.get('score', 0)
                if num:
                    try:
                        num_input = self.driver.find_element(
                            By.XPATH, self.RULE_ROW_NUM_INPUT_TPL.format(type=qtype)
                        )
                        num_input.clear()
                        num_input.send_keys(str(num))
                    except Exception:
                        self.logger.warning("规则组卷-%s抽取数量输入框未找到", qtype)
                if score:
                    try:
                        score_input = self.driver.find_element(
                            By.XPATH, self.RULE_ROW_SCORE_INPUT_TPL.format(type=qtype)
                        )
                        score_input.clear()
                        score_input.send_keys(str(score))
                    except Exception:
                        self.logger.warning("规则组卷-%s分值输入框未找到", qtype)

        self._wait_settled()

    def _set_weight_slider(self, weight_type, value):
        """设置难度权重滑块的值"""
        locators = {
            'easy': [self.RULE_EASY_WEIGHT_INPUT, self.RULE_EASY_WEIGHT_FALLBACK],
            'medium': [self.RULE_MEDIUM_WEIGHT_INPUT, self.RULE_MEDIUM_WEIGHT_FALLBACK],
            'hard': [self.RULE_HARD_WEIGHT_INPUT, self.RULE_HARD_WEIGHT_FALLBACK],
        }

        weight_text = {'easy': '简单', 'medium': '中等', 'hard': '困难'}.get(weight_type, weight_type)

        for locator in locators.get(weight_type, []):
            try:
                slider = self.wait.until(EC.presence_of_element_located(locator))
                self.driver.execute_script(
                    "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input'));",
                    slider, str(value)
                )
                self.logger.info("成功设置%s难度权重为%s", weight_text, value)
                return
            except Exception:
                continue

        try:
            sliders = self.driver.find_elements(*self.RULE_WEIGHT_SLIDES)
            idx = {'easy': 0, 'medium': 1, 'hard': 2}.get(weight_type, 0)
            if idx < len(sliders):
                self.driver.execute_script(
                    "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input'));",
                    sliders[idx], str(value)
                )
                self.logger.info("通过索引方式设置%s难度权重为%s", weight_text, value)
                return
        except Exception:
            pass

        self.logger.warning("%s难度滑块未找到", weight_text)

    def click_rule_paper_increase_button(self, qtype):
        """点击规则组卷中指定题型的抽取数量增加按钮

        Args:
            qtype: 题型名称，如 '单选题', '多选题' 等
        """
        self.logger.info("规则组卷 — 点击%s抽取数量增加按钮", qtype)
        candidate_xpaths = [
            f'//*[contains(normalize-space(.),"{qtype}")]/ancestor::tr[1]//span[contains(@class,"el-input-number__increase")]',
            f'//tr[contains(@class,"el-table__row") and .//*[contains(normalize-space(.),"{qtype}")]]//span[contains(@class,"el-input-number__increase")]',
            f'//tr[.//*[contains(normalize-space(.),"{qtype}")]]//button[contains(@class,"el-input-number__increase")]',
            f'//tr[.//*[contains(normalize-space(.),"{qtype}")]]//span[contains(@class,"el-icon-plus")]/parent::*',
            '//div[contains(@class,"el-input-number")]//span[contains(@class,"el-input-number__increase")]',
            '//div[contains(@class,"el-input-number")]//button[contains(@class,"el-input-number__increase")]',
        ]

        for xpath in candidate_xpaths:
            try:
                btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                self.wait_vue_stable()
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_vue_stable()
                self.logger.info("成功点击%s增加按钮", qtype)
                return
            except Exception as e:
                self.logger.warning("尝试定位增加按钮失败 (%s): %s", xpath, str(e)[:100])
                continue

        self.logger.info("尝试使用JavaScript直接查找并点击增加按钮")
        try:
            js_script = f'''
                var rows = document.querySelectorAll('tr');
                for (var i = 0; i < rows.length; i++) {{
                    if (rows[i].textContent.includes("{qtype}")) {{
                        var increaseBtn = rows[i].querySelector('.el-input-number__increase, .el-icon-plus');
                        if (increaseBtn) {{
                            increaseBtn.click();
                            return true;
                        }}
                    }}
                }}
                return false;
            '''
            result = self.driver.execute_script(js_script)
            if result:
                self.wait_vue_stable()
                self.logger.info("通过JavaScript成功点击%s增加按钮", qtype)
                return
        except Exception as e:
            self.logger.warning("JavaScript点击失败: %s", e)

        raise Exception(f"未找到{qtype}的增加按钮")

    def set_rule_paper_extract_num(self, qtype, num):
        """直接在输入框中设置规则组卷指定题型的抽取数量

        Args:
            qtype: 题型名称
            num: 抽取数量
        """
        self.logger.info("规则组卷 — 直接设置%s抽取数量为%s", qtype, num)
        candidate_xpaths = [
            f'//*[contains(normalize-space(.),"{qtype}")]/ancestor::tr[1]//input[@type="number" or contains(@class,"el-input__inner")][1]',
            f'//tr[contains(@class,"el-table__row") and .//*[contains(normalize-space(.),"{qtype}")]]//input[@type="number" or contains(@class,"el-input__inner")][1]',
            f'//tr[.//*[contains(normalize-space(.),"{qtype}")]]//input[@type="number"][1]',
            f'//tr[.//*[contains(normalize-space(.),"{qtype}")]]//td[3]//input',
            f'//tr[.//*[contains(normalize-space(.),"{qtype}")]]//div[contains(@class,"el-input-number")]//input',
        ]

        for xpath in candidate_xpaths:
            try:
                input_el = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", input_el)
                self.wait_vue_stable()
                self.driver.execute_script("arguments[0].focus();", input_el)
                self.wait_vue_stable()
                self.driver.execute_script("arguments[0].value = '';", input_el)
                input_el.send_keys(str(num))
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('input'));", input_el)
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", input_el)
                self.wait_vue_stable()
                self.logger.info("成功直接设置%s抽取数量为%s", qtype, num)
                return
            except Exception as e:
                self.logger.warning("尝试设置抽取数量失败 (%s): %s", xpath, str(e)[:100])
                continue

        self.logger.info("尝试使用JavaScript直接查找并设置抽取数量")
        try:
            js_script = f'''
                var rows = document.querySelectorAll('tr');
                for (var i = 0; i < rows.length; i++) {{
                    if (rows[i].textContent.includes("{qtype}")) {{
                        var inputs = rows[i].querySelectorAll('input[type="number"], .el-input__inner');
                        if (inputs.length >= 1) {{
                            inputs[0].focus();
                            inputs[0].value = "{num}";
                            inputs[0].dispatchEvent(new Event('input'));
                            inputs[0].dispatchEvent(new Event('change'));
                            return true;
                        }}
                    }}
                }}
                return false;
            '''
            result = self.driver.execute_script(js_script)
            if result:
                self.wait_vue_stable()
                self.logger.info("通过JavaScript成功设置%s抽取数量为%s", qtype, num)
                return
        except Exception as e:
            self.logger.warning("JavaScript设置抽取数量失败: %s", e)

        raise Exception(f"未找到{qtype}的抽取数量输入框")

    def set_rule_paper_score(self, qtype, score):
        """设置规则组卷中指定题型的分值

        Args:
            qtype: 题型名称
            score: 分值
        """
        self.logger.info("规则组卷 — 设置%s分值为%s", qtype, score)
        candidate_xpaths = [
            f'//*[contains(normalize-space(.),"{qtype}")]/ancestor::tr[1]//input[@type="number" or contains(@class,"el-input__inner")][2]',
            f'//tr[contains(@class,"el-table__row") and .//*[contains(normalize-space(.),"{qtype}")]]//input[@type="number" or contains(@class,"el-input__inner")][2]',
            f'//tr[.//*[contains(normalize-space(.),"{qtype}")]]//input[@type="number"][2]',
            f'//tr[.//*[contains(normalize-space(.),"{qtype}")]]//td[3]//input',
        ]

        for xpath in candidate_xpaths:
            try:
                input_el = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                self.driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input'));",
                                           input_el, str(score))
                self.wait_vue_stable()
                self.logger.info("成功设置%s分值为%s", qtype, score)
                return
            except Exception as e:
                self.logger.warning("尝试设置分值失败 (%s): %s", xpath, str(e)[:100])
                continue

        self.logger.info("尝试使用JavaScript直接查找并设置分值")
        try:
            js_script = f'''
                var rows = document.querySelectorAll('tr');
                for (var i = 0; i < rows.length; i++) {{
                    if (rows[i].textContent.includes("{qtype}")) {{
                        var inputs = rows[i].querySelectorAll('input[type="number"], .el-input__inner');
                        if (inputs.length >= 2) {{
                            inputs[1].value = "{score}";
                            inputs[1].dispatchEvent(new Event('input'));
                            return true;
                        }}
                    }}
                }}
                return false;
            '''
            result = self.driver.execute_script(js_script)
            if result:
                self.wait_vue_stable()
                self.logger.info("通过JavaScript成功设置%s分值为%s", qtype, score)
                return
        except Exception as e:
            self.logger.warning("JavaScript设置分值失败: %s", e)

        raise Exception(f"未找到{qtype}的分值输入框")

    def click_save_and_publish(self):
        """点击规则组卷页面的保存并发布按钮"""
        self.logger.info("规则组卷 — 点击保存并发布")
        candidate_xpaths = [
            '//button[.//span[contains(normalize-space(.),"保存并发布")]]',
            '//button[.//span[contains(normalize-space(.),"保存并发布试卷")]]',
            '//button[contains(@class,"el-button--primary") and .//span[contains(normalize-space(.),"发布")]]',
            '//div[contains(@class,"footer")]//button[.//span[contains(normalize-space(.),"保存并发布")]]',
        ]

        for xpath in candidate_xpaths:
            try:
                btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                self.wait_vue_stable()
                self.driver.execute_script("arguments[0].click();", btn)
                self._wait_loading_gone(timeout=5)
                self.wait_vue_stable()
                self.logger.info("成功点击保存并发布按钮")
                return
            except Exception as e:
                self.logger.warning("尝试定位保存并发布按钮失败 (%s): %s", xpath, e)
                continue

        raise Exception("未找到保存并发布按钮")

    def go_to_step3(self):
        """从步骤2 进入步骤3（点击下一步/下一页）"""
        try:
            self._click_js(self.STEP2_NEXT_BUTTON)
        except Exception:
            self.logger.warning("步骤2下一页按钮未找到，可能是规则组卷模式")
        self._wait_settled()

    def publish_paper(self):
        """发布试卷（点击发布试卷按钮，处理确认弹窗）"""
        self.logger.info("发布试卷")
        try:
            self._click_js(self.PUBLISH_BUTTON)
            self._wait_loading_gone(timeout=5)
            self.wait_vue_stable()
        except Exception:
            self.logger.warning("发布试卷按钮未找到")

        try:
            confirm = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(self.CONFIRM_PUBLISH_BUTTON)
            )
            self.driver.execute_script("arguments[0].click();", confirm)
            self._wait_loading_gone(timeout=5)
            self.wait_vue_stable()
        except Exception:
            pass

        self._wait_settled()

    def save_draft(self):
        """保存草稿"""
        self.logger.info("保存草稿")
        try:
            self._click_js(self.SAVE_DRAFT_BUTTON)
            self._wait_loading_gone(timeout=5)
            self.wait_vue_stable()
        except Exception:
            self.logger.warning("保存草稿按钮未找到")

        try:
            confirm = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(self.CONFIRM_PUBLISH_BUTTON)
            )
            self.driver.execute_script("arguments[0].click();", confirm)
            self._wait_loading_gone(timeout=5)
            self.wait_vue_stable()
        except Exception:
            pass

        self._wait_settled()

    def search_paper_by_name(self, name):
        """按试卷名称搜索（从列表页搜索）"""
        self.logger.info("搜索试卷：%s", name)
        self.input_search_name(name)
        self.click_search()
        self._wait_settled()

    def verify_paper_exists(self, name, status=None):
        """验证试卷是否在列表中，可选验证状态"""
        self.search_paper_by_name(name)
        row_count = self.get_table_row_count()
        if row_count > 0:
            row_data = self.get_first_row_data()
            self.logger.info("找到试卷: %s", row_data)
            if status:
                status_index = self.COL_STATUS - 1
                if status_index < len(row_data):
                    actual_status = row_data[status_index]
                    self.logger.info("实际状态: %s, 期望状态: %s", actual_status, status)
                    return status in actual_status
            return True
        return False
