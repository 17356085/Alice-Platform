"""课程管理页面操作类 — 重构版

变更记录:
  2026-06-11: 继承 BasePage，替换 time.sleep -> BasePage 等待方法，
              替换 print() -> logger，替换绝对 XPath -> CSS/相对 XPath
"""
import os
import logging
import time
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage
from base.sidebar_navigator import SidebarNavigator

logger = logging.getLogger(__name__)


class CourseManagePage(BasePage):
    """课程管理页面操作 — 继承 BasePage"""

    # ══════════════════════════════════════════════════════════════════
    #  页面专属定位器（CSS优先 -> 相对XPath -> 文本匹配）
    # ══════════════════════════════════════════════════════════════════

    ADD_COURSE_BUTTON = (By.XPATH,
                         '//button[.//span[normalize-space(.)="新增课程" or normalize-space(.)="新增" or normalize-space(.)="新建"]]')
    SEARCH_COURSE_NAME_INPUT = (By.XPATH,
                                '//input[contains(@placeholder,"课程名称") or contains(@placeholder,"请输入课程名称")]')
    SEARCH_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="查询" or normalize-space(.)="搜索"]]')
    RESET_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="重置"]]')

    SEARCH_COURSE_CATEGORY_SELECT = (By.XPATH,
                                     '//div[contains(@class,"search-bar")]//div[contains(@class,"el-select")][.//span[normalize-space(.)="课程分类"]]')
    SEARCH_MATERIAL_TYPE_SELECT = (By.XPATH,
                                   '//div[contains(@class,"search-bar")]//div[contains(@class,"el-select")][.//span[normalize-space(.)="资料类型"]]')
    SEARCH_PUBLISH_STATUS_SELECT = (By.XPATH,
                                    '//div[contains(@class,"search-bar")]//div[contains(@class,"el-select")][.//span[normalize-space(.)="发布状态"]]')

    COURSE_CARD_VIEW_BUTTON = (By.XPATH,
                               '//div[contains(@class,"course-grid") or contains(@class,"course-card")]//button[.//span[normalize-space(.)="查看"]]')
    COURSE_DETAIL_DIALOG_CLOSE_BUTTON = (By.XPATH,
                                         '//div[contains(@class,"el-dialog") and .//*[text()="课程详情"]]//button[.//span[normalize-space(.)="关闭"]]')

    DIALOG_TITLE = (By.XPATH,
                    '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//header//*[contains(@class,"el-dialog__title") or self::span]')
    COURSE_NAME_INPUT = (By.XPATH,
                         '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//input[contains(@placeholder,"课程名称") or contains(@placeholder,"请输入课程名称")]')
    COURSE_DURATION_INPUT = (By.XPATH,
                             '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//label[contains(., "课程时长")]/following::input[1]')
    COURSE_INTRO_TEXTAREA = (By.XPATH,
                             '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//textarea[@placeholder="请输入课程简介"]')
    COURSE_REMARK_TEXTAREA = (By.XPATH,
                              '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//textarea[@placeholder="请输入备注"]')
    COURSE_FILE_INPUT = (By.XPATH, '//input[@type="file"]')
    COURSE_FILE_UPLOAD_AREA = (By.XPATH,
                               '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//div[contains(@class,"upload-area")]')
    SAVE_BUTTON = (By.XPATH,
                   '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
                   '//button[contains(@class,"el-button--primary")]'
                   '[.//span[normalize-space(.)="保存" or normalize-space(.)="确定" or normalize-space(.)="确 认"]]')
    CANCEL_BUTTON = (By.XPATH,
                     '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
                     '//button[not(contains(@class,"el-button--primary"))]'
                     '[.//span[normalize-space(.)="取消" or normalize-space(.)="取 消"]]')

    FORM_ITEM = (By.XPATH,
                 '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//div[contains(@class,"el-form-item")]')

    # ========== 课程卡片发布/操作相关 ==========

    COURSE_CARD_PUBLISH_BUTTON = (By.CSS_SELECTOR,
                                  'div.course-grid div.course-actions button.el-button--primary')
    COURSE_CARD_PUBLISH_BY_TEXT = (By.XPATH,
                                   '//div[contains(@class,"course-grid")]//div[contains(@class,"course-actions")]/button[contains(@class,"el-button--primary")][.//span[normalize-space(.)="发布"]]')

    CONFIRM_DIALOG_OK_BUTTON = (By.XPATH,
                                 '//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))]//button[.//span[normalize-space(.)="确定"]]')

    # ── 构造 ──────────────────────────────────────────────────────────

    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    # ── 导航 ──────────────────────────────────────────────────────────

    def navigate(self):
        """导航到课程管理页面（外部统一入口）"""
        self.navigate_to("人员管理", "培训管理", "课程管理")
        self._wait_table_rows(timeout=15)

    # ── 内部等待辅助 ──────────────────────────────────────────────────

    def _wait_animate(self, seconds=0.3):
        """等待 Element Plus 动画/渲染完成（委托 BasePage）"""
        self.wait_vue_stable()

    def _wait_dropdown_open(self, timeout=5):
        """等待下拉选项面板出现"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((
                By.XPATH,
                '//body//div[contains(@class,"el-select-dropdown") or contains(@class,"el-popper")]'
                '[not(contains(@style,"display: none")) and not(contains(@style,"visibility: hidden"))]'
            ))
        )

    def _wait_dialog_visible(self, timeout=15):
        """等待弹窗可见"""
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((
                By.XPATH,
                '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
            ))
        )

    def _wait_dialog_gone(self, timeout=10):
        """等待弹窗消失"""
        try:
            self.wait_dialog_close(timeout=timeout)
            return True
        except Exception:
            return False

    def _wait_table_rows(self, timeout=10):
        """等待页面数据加载完成（课程页使用卡片布局，等待卡片或分页出现）"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: (
                    len(d.find_elements(By.CSS_SELECTOR, '.el-table__row')) > 0 or
                    len(d.find_elements(By.CSS_SELECTOR, '.el-card, .course-card')) > 0 or
                    len(d.find_elements(By.CSS_SELECTOR, '.el-pagination')) > 0
                )
            )
        except Exception:
            pass

    def _click_js(self, locator):
        el = self.wait.until(EC.presence_of_element_located(locator))
        self._scroll_into_view(el)
        self._wait_animate()
        self._js_click_el(el)
        return el

    def _get_visible_dialog(self):
        # 复用 BasePage 的 _get_visible_dialog，其内部使用 CSS_SELECTOR
        return BasePage._get_visible_dialog(self)

    def _get_dialog_form_item(self, label_text):
        # 使用更稳定的定位方式：基于对话框和label文本
        item_xpath = (
            f'//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
            f'//label[contains(@class,"el-form-item__label") and contains(normalize-space(.), "{label_text}")]'
            f'/ancestor::div[contains(@class,"el-form-item")]'
        )

        def _locate(_driver):
            dialog = self._get_visible_dialog()
            return dialog.find_element(By.XPATH, item_xpath)

        return WebDriverWait(self.driver, 10).until(lambda d: _locate(d))

    # ── 页面操作方法 ──────────────────────────────────────────────────

    def navigate_to_course_management(self):
        """导航到课程管理（兼容旧调用方，推荐使用 navigate()）"""
        SidebarNavigator(self.driver).navigate_to("人员管理", "培训管理", "课程管理")
        self._wait_table_rows(timeout=15)

    def click_add_course_button(self):
        """点击新增课程按钮（先重置搜索确保按钮可见）"""
        # 确保页面状态干净：重置搜索避免过滤导致按钮不可见
        try:
            self.click_reset_button()
            self.wait_vue_stable()
        except Exception:
            pass
        for attempt in range(3):
            try:
                self._click_js(self.ADD_COURSE_BUTTON)
                self._wait_dialog_visible()
                return
            except Exception as e:
                if attempt < 2:
                    logger.warning("新增课程按钮点击失败 (尝试 %d/3): %s", attempt + 1, e)
                    self.wait_vue_stable()
                else:
                    raise

    def input_course_name(self, value):
        el = self.wait.until(EC.visibility_of_element_located(self.COURSE_NAME_INPUT))
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        el.send_keys(value)

    def input_course_duration(self, value):
        el = self.wait.until(EC.visibility_of_element_located(self.COURSE_DURATION_INPUT))
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        el.send_keys(str(value))

    def input_course_intro(self, value):
        el = self.wait.until(EC.visibility_of_element_located(self.COURSE_INTRO_TEXTAREA))
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        el.send_keys(value)

    def input_course_remark(self, value):
        el = self.wait.until(EC.visibility_of_element_located(self.COURSE_REMARK_TEXTAREA))
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        el.send_keys(value)

    def upload_course_file(self, file_path):
        abs_path = os.path.abspath(file_path)

        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"文件不存在: {abs_path}")

        file_name = os.path.basename(abs_path)

        # 等上传区域就绪（弹窗已完全渲染）
        upload_area_locators = [
            (By.XPATH, '//div[contains(@class,"upload-area")]'),
            (By.XPATH, '//div[contains(text(),"点击或拖拽")]'),
            (By.XPATH, '//div[contains(@class,"el-upload")]'),
        ]

        upload_area = None
        for locator in upload_area_locators:
            try:
                upload_area = WebDriverWait(self.driver, 8).until(
                    EC.element_to_be_clickable(locator)
                )
                break
            except Exception:
                continue

        if upload_area:
            self.driver.execute_script("arguments[0].click();", upload_area)

        file_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]'))
        )

        self.driver.execute_script("arguments[0].style.display = 'block'; arguments[0].style.opacity = '1';",
                                   file_input)
        self._wait_animate()

        file_input.send_keys(abs_path)

        # 等上传按钮出现（文件已就绪的信号）
        try:
            upload_button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, '//button[.//span[text()="上传"]]'))
            )
            self.driver.execute_script("arguments[0].click();", upload_button)
            # 等确定按钮出现（上传完成的信号）
            WebDriverWait(self.driver, 60).until(
                EC.element_to_be_clickable((By.XPATH, '//button[.//span[text()="确定"]]'))
            )
        except Exception:
            pass

        confirm_button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//button[.//span[text()="确定"]]'))
        )
        self.driver.execute_script("arguments[0].click();", confirm_button)
        # 等上传弹窗关闭
        self._wait_dialog_gone(timeout=15)

        return abs_path

    def open_dialog_select(self, label_text):
        item = self._get_dialog_form_item(label_text)
        candidates = [
            './/div[contains(@class,"el-select__wrapper")]',
            './/div[contains(@class,"el-select")]',
            './/div[contains(@class,"el-select__selection")]',
            './/input',
            './/span[contains(@class,"el-select__placeholder")]',
            './/i[contains(@class,"el-select__caret")]',
            './/*[name()="svg"]',
        ]

        last_exc = None
        for xp in candidates:
            try:
                el = item.find_element(By.XPATH, xp)
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                self._wait_animate()
                for _ in range(2):
                    try:
                        self.driver.execute_script("arguments[0].click();", el)
                    except Exception:
                        el.click()
                    self._wait_animate(0.5)

                    dropdowns = self.driver.find_elements(
                        By.XPATH,
                        '//body//div[contains(@class,"el-select-dropdown") or contains(@class,"el-popper")]'
                        '[not(contains(@style,"display: none")) and not(contains(@style,"visibility: hidden"))]'
                    )
                    if dropdowns:
                        return
            except Exception as e:
                last_exc = e
                continue

        raise Exception(f"无法打开下拉框: {label_text}")

    def select_dialog_option_by_text(self, label_text, option_text):
        # 第一步：找到并点击下拉框，打开下拉选项
        item = self._get_dialog_form_item(label_text)

        # Element Plus 中真正可交互的通常是 wrapper / combobox
        select_xpaths = [
            './/div[contains(@class,"el-select__wrapper")]',
            './/div[@role="combobox"]',
            './/div[contains(@class,"el-select")]',
            './/input',
        ]

        select_el = None
        last_exc = None
        for select_xpath in select_xpaths:
            try:
                select_el = item.find_element(By.XPATH, select_xpath)
                break
            except Exception as e:
                last_exc = e
                continue

        if select_el is None:
            # 调试：打印表单项内容
            logger.warning("\n===== 表单项 '%s' 的内容 =====", label_text)
            all_elements = item.find_elements(By.XPATH, './/*')
            for i, el in enumerate(all_elements[:10]):
                try:
                    tag = el.tag_name
                    cls = el.get_attribute('class') or ''
                    text = el.text.strip()[:30]
                    logger.warning("  [%s] %s class='%s' text='%s'", i + 1, tag, cls, text)
                except Exception:
                    logger.warning("  [%s] 获取信息失败", i + 1)
            logger.warning("=================================")
            raise Exception(f"无法定位下拉框 '{label_text}': {last_exc}")

        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", select_el)
            self._wait_animate()
            try:
                select_el.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", select_el)
            self._wait_dropdown_open(timeout=5)
        except Exception as e:
            raise Exception(f"无法点击下拉框 '{label_text}': {e}")

        max_retries = 3
        for retry in range(max_retries):
            option_xpaths = [
                f'//body//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]//div[contains(@class,"el-select-dropdown__item") and contains(., "{option_text}")]',
                f'//body//div[contains(@class,"el-popper") and not(contains(@style,"display: none"))]//*[contains(@class,"el-select-dropdown__item") and contains(., "{option_text}")]',
                f'//body//li[@role="option" and contains(., "{option_text}")]',
                f'//body//*[contains(@class,"el-select-dropdown__item") and contains(., "{option_text}")]',
            ]

            for option_xpath in option_xpaths:
                try:
                    option = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, option_xpath))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", option)
                    self._wait_animate()
                    try:
                        option.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", option)
                    self._wait_animate()
                    return option_text
                except Exception:
                    continue

            # 如果当前重试失败，尝试重新点击下拉框
            if retry < max_retries - 1:
                try:
                    select_el.click()
                    self._wait_animate(0.5)
                except Exception:
                    pass

        # 调试：打印所有可见选项
        logger.warning("\n===== 查找选项 '%s' 失败，当前页面可见选项 =====", option_text)
        all_options = self.driver.find_elements(By.XPATH, '//body//*[contains(@class,"el-select-dropdown__item") or @role="option"]')
        for i, opt in enumerate(all_options[:15]):
            try:
                text = opt.text.strip()
                logger.warning("  [%s] '%s'", i + 1, text)
            except Exception:
                logger.warning("  [%s] 获取文本失败", i + 1)
        logger.warning("=================================")

        raise Exception(f"无法选择下拉选项 '{label_text}' -> '{option_text}'，已重试{max_retries}次")

    def click_save_button(self):
        """点击弹窗保存按钮（JS click + 长超时，服务端响应可能慢）"""
        for attempt in range(3):
            try:
                self._click_js(self.SAVE_BUTTON)
                self._wait_dialog_gone(timeout=25)
                return
            except Exception as e:
                if attempt < 2:
                    logger.warning("保存按钮点击失败 (尝试 %d/3): %s", attempt + 1, e)
                    self.wait_vue_stable()
                else:
                    raise

    def click_cancel_button(self):
        self._click_js(self.CANCEL_BUTTON)
        self._wait_dialog_gone(timeout=5)

    def wait_dialog_closed(self, timeout=5):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, '.el-overlay-dialog, .el-dialog__wrapper, .el-dialog'))
            )
            return True
        except Exception:
            return False

    def fill_add_course_form(self, course_name, course_duration, course_category, material_type, intro, remark,
                             file_path=None):
        self.input_course_name(course_name)
        self.input_course_duration(course_duration)
        self.select_dialog_option_by_text("课程分类", course_category)
        self.select_dialog_option_by_text("资料类型", material_type)
        self.input_course_intro(intro)
        if file_path:
            self.upload_course_file(file_path)
        self.input_course_remark(remark)

    def get_toast_text(self, timeout=10):
        return self.get_toast(timeout)

    def click_search_button(self):
        """点击搜索按钮（JS click + 重试）"""
        for attempt in range(3):
            try:
                self._click_js(self.SEARCH_BUTTON)
                self._wait_table_rows()
                return
            except Exception as e:
                if attempt < 2:
                    logger.warning("搜索按钮点击失败 (尝试 %d/3): %s", attempt + 1, e)
                    self.wait_vue_stable()
                else:
                    raise

    def click_reset_button(self):
        self._click_js(self.RESET_BUTTON)
        self._wait_table_rows()

    def input_search_course_name(self, value):
        el = self.wait.until(EC.visibility_of_element_located(self.SEARCH_COURSE_NAME_INPUT))
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        el.send_keys(value)

    def _click_select_by_locator(self, locator):
        el = self.wait.until(EC.element_to_be_clickable(locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        self._wait_animate()
        self.driver.execute_script("arguments[0].click();", el)

    def _select_option_by_text(self, option_text):
        option_xpaths = [
            f'//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]//li[not(contains(@class,"is-disabled")) and contains(normalize-space(.), "{option_text}")]',
            f'//div[contains(@class,"el-popper") and not(contains(@style,"display: none"))]//li[not(contains(@class,"is-disabled")) and contains(normalize-space(.), "{option_text}")]',
            f'//body//li[@role="option" and contains(normalize-space(.), "{option_text}")]',
            f'//div[contains(@class,"el-select-dropdown__item") and contains(normalize-space(.), "{option_text}")]',
        ]

        self.wait_vue_stable()  # 等 Teleport 渲染完成（Element Plus 固有延迟）

        for option_xpath in option_xpaths:
            try:
                option = WebDriverWait(self.driver, 8).until(EC.presence_of_element_located((By.XPATH, option_xpath)))
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'nearest'});", option)
                self._wait_animate()
                try:
                    option.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", option)
                self._wait_animate(0.3)
                return option_text
            except Exception:
                continue

        raise Exception(f"无法选择选项: {option_text}")

    def select_search_course_category(self, category_text):
        self._click_select_by_locator(self.SEARCH_COURSE_CATEGORY_SELECT)
        return self._select_option_by_text(category_text)

    def select_search_material_type(self, type_text):
        self._click_select_by_locator(self.SEARCH_MATERIAL_TYPE_SELECT)
        return self._select_option_by_text(type_text)

    def select_search_publish_status(self, status_text):
        self._click_select_by_locator(self.SEARCH_PUBLISH_STATUS_SELECT)
        return self._select_option_by_text(status_text)

    def get_dialog_title_text(self):
        try:
            return self.wait.until(EC.visibility_of_element_located(self.DIALOG_TITLE)).text.strip()
        except Exception:
            return ''

    def click_view_course_button(self):
        el = self.wait.until(EC.element_to_be_clickable(self.COURSE_CARD_VIEW_BUTTON))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        self._wait_animate()
        self.driver.execute_script("arguments[0].click();", el)
        self._wait_dialog_visible()

    def click_close_course_detail_button(self):
        el = self.wait.until(EC.element_to_be_clickable(self.COURSE_DETAIL_DIALOG_CLOSE_BUTTON))
        self.driver.execute_script("arguments[0].click();", el)
        self._wait_dialog_gone(timeout=5)

    def click_publish_button_in_card(self, course_name=None):
        """点击课程卡片中的发布按钮

        优先基于文字"发布"定位，其次用CSS选择器定位 course-actions 中的主按钮。
        如果传了 course_name，会先滚动到对应课程卡片再点击。
        """
        # 候选选择器：按稳定性排序
        candidate_xpaths = [
            # 1) 在指定课程名称的卡片范围内找发布按钮（最精确）
            f'//*[contains(normalize-space(.),"{course_name}")]'
            f'/ancestor::div[contains(@class,"el-card") or contains(@class,"course-card")]'
            f'//div[contains(@class,"course-actions")]'
            f'/button[contains(@class,"el-button--primary")]' if course_name else None,
            # 2) 全局按文字匹配发布按钮
            '//div[contains(@class,"course-grid")]//div[contains(@class,"course-actions")]'
            '/button[.//span[normalize-space(.)="发布"]]',
            # 3) 基于用户提供的路径模式查找
            '//div[contains(@class,"el-card")]//button[.//span[normalize-space(.)="发布"]]',
            # 4) CSS 选择器：course-actions 下的 primary 按钮
            'div.course-grid div.course-actions > button.el-button--primary',
            # 5) 全局 XPath 按文字
            '//button[.//span[normalize-space(.)="发布"]]',
        ]

        for xp in candidate_xpaths:
            if not xp:
                continue
            try:
                if xp.startswith('//') or xp.startswith('/'):
                    locator = (By.XPATH, xp)
                else:
                    locator = (By.CSS_SELECTOR, xp)
                el = self.wait.until(EC.element_to_be_clickable(locator))
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                self._wait_animate()
                self.driver.execute_script("arguments[0].click();", el)
                self._wait_animate(1.5)
                return el
            except Exception as e:
                logger.warning("[publish] 尝试定位失败 (%s): %s", xp, e)
                continue

        raise Exception(f"未找到课程发布按钮{'（课程: ' + course_name + '）' if course_name else ''}")

    def click_confirm_dialog_ok(self):
        """点击确认弹窗（MessageBox）的确定按钮"""
        confirm_xpaths = [
            '//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))]'
            '//button[.//span[normalize-space(.)="确定"]]',
            '//div[contains(@class,"el-overlay-message-box") and not(contains(@style,"display: none"))]'
            '//div[contains(@class,"el-message-box")]'
            '//button[.//span[normalize-space(.)="确定"]]',
        ]
        for xp in confirm_xpaths:
            try:
                btn = WebDriverWait(self.driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                self.driver.execute_script("arguments[0].click();", btn)
                self._wait_dialog_gone(timeout=5)
                return True
            except Exception:
                continue
        raise Exception("未找到确认弹窗的确定按钮")

    def publish_course_by_name(self, course_name):
        """完整流程：搜索课程 -> 点击发布 -> 确认发布"""
        self.click_reset_button()
        self.input_search_course_name(course_name)
        self.click_search_button()  # click_search_button 内已等表格就绪

        self.click_publish_button_in_card(course_name)

        try:
            self.click_confirm_dialog_ok()
        except Exception:
            pass  # 可能无确认弹窗

        return self.get_toast_text()
