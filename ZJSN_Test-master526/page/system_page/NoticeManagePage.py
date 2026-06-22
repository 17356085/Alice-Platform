"""通知管理页面 Page Object — 重构版

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


class NoticeManagePage(BasePage):
    """通知管理页面操作 — 继承 BasePage"""

    # ══════════════════════════════════════════════════════════════════
    #  页面专属定位器（CSS优先 → 相对XPath → 文本匹配）
    # ══════════════════════════════════════════════════════════════════

    # 搜索区域
    NOTICE_TITLE_INPUT = (By.XPATH, '//input[contains(@placeholder,"请输入通知标题")]')
    NOTICE_TYPE_SELECT = (
        By.XPATH,
        '//input[contains(@placeholder,"请输入通知标题")]/ancestor::form//div[contains(@class,"el-select")]//span',
    )
    # 复用 BasePage.SEARCH_BUTTON_CSS / SEARCH_BUTTON_XPATH、RESET_BUTTON_CSS / RESET_BUTTON_XPATH
    # 不再定义绝对 XPath 版本

    # 工具栏 - 新增按钮
    TOOLBAR_ADD = (
        By.XPATH,
        '//button[contains(normalize-space(.),"新增")]',
    )
    TOOLBAR_ADD_TOOLBAR = (
        By.XPATH,
        '//div[contains(@class,"el-table__toolbar") or contains(@class,"table-toolbar")]'
        '//button[contains(normalize-space(.),"新增")]',
    )

    # 弹窗
    DIALOG_PANEL = (
        By.XPATH,
        '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[@role="dialog"])[last()]',
    )
    DIALOG_CONFIRM = (
        By.XPATH,
        '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[@role="dialog"])[last()]'
        '//footer//button[.//span[normalize-space(.)="确定"] or normalize-space(.)="确定"]',
    )
    DIALOG_CANCEL = (
        By.XPATH,
        '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[@role="dialog"])[last()]'
        '//footer//button[.//span[normalize-space(.)="取消"] or normalize-space(.)="取消"]',
    )
    DIALOG_DELETE_CONFIRM = (
        By.XPATH,
        '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]'
        '//div[contains(@class,"el-message-box")])[last()]'
        '//div[contains(@class,"el-message-box__btns")]'
        '//button[contains(@class,"el-button--primary")'
        ' and (.//span[normalize-space(.)="确定"] or normalize-space(.)="确定")]',
    )

    # 弹窗表单元素
    DIALOG_TITLE_INPUT = (
        By.XPATH,
        './/input[contains(@placeholder,"请输入通知标题")]',
    )
    DIALOG_TYPE_SELECT = (
        By.XPATH,
        '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]'
        '//div[contains(@class,"el-select") and .//span[text()="通知"]]',
    )
    DIALOG_TYPE_OPTION_NOTICE = (
        By.XPATH,
        '//div[contains(@class,"el-select-dropdown")]//li[.//span[normalize-space(.)="通知"]]',
    )
    DIALOG_TYPE_OPTION_ANNOUNCEMENT = (
        By.XPATH,
        '//div[contains(@class,"el-select-dropdown")]//li[.//span[normalize-space(.)="公告"]]',
    )
    DIALOG_STATUS_RADIO_NORMAL = (
        By.XPATH,
        '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]'
        '//label[contains(@class,"el-radio") and .//span[contains(text(),"正常")]]',
    )
    DIALOG_STATUS_RADIO_CLOSE = (
        By.XPATH,
        '(//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))])[last()]'
        '//label[contains(@class,"el-radio") and .//span[contains(text(),"关闭")]]',
    )
    DIALOG_CONTENT_TEXTAREA = (
        By.XPATH,
        './/textarea[contains(@placeholder,"请输入通知内容")]',
    )

    # 表格
    EMPTY_TEXT = (
        By.XPATH,
        '//*[contains(@class,"el-table__empty-text")][not(ancestor::div[contains(@class,"el-dialog")])]',
    )
    MAIN_TABLE_HEADER_WRAPPER = (
        By.XPATH,
        '(//div[contains(@class,"el-table__header-wrapper")][not(ancestor::div[contains(@class,"el-dialog")])])[1]',
    )
    MAIN_TABLE_BODY_WRAPPER = (
        By.XPATH,
        '(//div[contains(@class,"el-table__body-wrapper")][not(ancestor::div[contains(@class,"el-dialog")])])[1]',
    )
    CURRENT_PAGE = (By.CSS_SELECTOR, ".el-pagination .el-pager li.active, .el-pagination .el-pager li.is-active")
    # 复用 BasePage.LOADING_MASK, BasePage.TOTAL_COUNT, BasePage.NEXT_PAGE

    # 消息提示
    TOAST_TEXT = (By.CSS_SELECTOR, ".el-message__content")
    TOAST_TEXT_FALLBACK = (
        By.CSS_SELECTOR,
        'div[id^="message_"] p, div[id^="message_"] .el-message__content, div[id^="message_"]',
    )
    TOAST_MESSAGE_ENHANCED = (
        By.XPATH,
        '(//*[contains(@class,"el-message__content") and normalize-space(.)!=""])[last()]',
    )

    def __init__(self, driver, timeout=None):
        """初始化 — 继承 BasePage"""
        super().__init__(driver, timeout)

    # ══════════════════════════════════════════════════════════════════════
    #  导航
    # ══════════════════════════════════════════════════════════════════════

    def navigate(self):
        """导航到通知管理页面 — 唯一入口"""
        logger.info("导航到 → 系统管理 → 通知管理")
        self.navigate_to("系统管理", "通知管理")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=12)
        self.wait_vue_stable()
        return self

    def navigate_to_notice_management(self):
        """导航到通知管理页面（向后兼容别名）"""
        logger.info("navigate_to_notice_management 已弃用，请使用 navigate()")
        return self.navigate()

    # ══════════════════════════════════════════════════════════════════════
    #  内部等待方法
    # ══════════════════════════════════════════════════════════════════════

    def _wait_settled(self, timeout=10):
        """等待加载完成 — 委托给 BasePage._wait_loading_gone"""
        self._wait_loading_gone(timeout=timeout)

    def _first_displayed(self, locator, timeout=2):
        """查找第一个可见的元素"""
        end = __import__('time').time() + timeout
        last_err = None
        while __import__('time').time() < end:
            try:
                els = self.find_all(locator)
                for el in els:
                    try:
                        if el.is_displayed():
                            return el
                    except Exception:
                        continue
            except Exception as e:
                last_err = e
            __import__('time').sleep(0.2)
        if last_err:
            raise last_err
        raise TimeoutException(f"未找到元素: {locator}")

    def wait_for_toast_text(self, timeout=6):
        """等待并获取Toast提示消息文本"""
        end = __import__('time').time() + timeout
        last = ""
        while __import__('time').time() < end:
            # 优先使用增强的XPath定位器
            try:
                els = self.find_all(self.TOAST_MESSAGE_ENHANCED)
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

            # 备用方案：使用CSS选择器
            try:
                els = self.find_all(self.TOAST_TEXT)
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

            # 最后的备用方案
            try:
                els = self.find_all(self.TOAST_TEXT_FALLBACK)
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

            __import__('time').sleep(0.3)
        return last

    # ══════════════════════════════════════════════════════════════════════
    #  搜索操作
    # ══════════════════════════════════════════════════════════════════════

    def input_notice_title(self, value):
        """输入通知标题"""
        logger.info("输入通知标题: %s", value)
        el = self._clear_input(self.NOTICE_TITLE_INPUT)
        if value:
            el.send_keys(value)

    def select_notice_type(self, text):
        """选择通知类型"""
        logger.info("选择通知类型: %s", text)
        self._wait_loading_gone(timeout=6)
        sel = self.find(self.NOTICE_TYPE_SELECT)
        self._scroll_into_view(sel)
        self._js_click_el(sel)

        # 等待下拉框出现
        dropdown_xpath = (
            f'(//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]'
            f'//li[.//span[normalize-space(.)="{text}"]])[last()]'
        )
        option = WebDriverWait(self.driver, 6).until(
            EC.presence_of_element_located((By.XPATH, dropdown_xpath))
        )
        self._js_click_el(option)
        self.wait_vue_stable()

    def click_search(self):
        """点击搜索"""
        logger.info("点击搜索按钮")
        self._wait_loading_gone(timeout=6)
        # 复用 BasePage 的搜索按钮定位和三级降级
        self.click_search_button()
        self._wait_loading_gone(timeout=10)

    def click_reset(self):
        """点击重置"""
        logger.info("点击重置按钮")
        self._wait_loading_gone(timeout=6)
        # 复用 BasePage 的重置按钮定位和三级降级
        self.click_reset_button()
        self._wait_loading_gone(timeout=10)

    # ══════════════════════════════════════════════════════════════════════
    #  新增操作
    # ══════════════════════════════════════════════════════════════════════

    def click_add(self):
        """点击新增"""
        logger.info("点击新增按钮")
        self._wait_loading_gone(timeout=6)
        btn = self._first_displayed(self.TOOLBAR_ADD, timeout=6)
        if not btn:
            raise TimeoutException("未找到新增按钮")
        self._js_click_el(btn)
        WebDriverWait(self.driver, 6).until(EC.presence_of_element_located(self.DIALOG_PANEL))

    def dialog_input_title(self, value):
        """弹窗输入通知标题"""
        logger.info("弹窗输入通知标题: %s", value)
        dlg = self._dialog()
        el = WebDriverWait(dlg, 4).until(EC.presence_of_element_located(self.DIALOG_TITLE_INPUT))
        self._js_click_el(el)
        try:
            el.clear()
        except Exception:
            pass
        try:
            el.send_keys(Keys.CONTROL + "a")
            el.send_keys(Keys.DELETE)
        except Exception:
            pass
        if value:
            el.send_keys(value)

    def dialog_select_type(self, type_text):
        """弹窗选择通知类型（通知/公告）"""
        logger.info("弹窗选择通知类型: %s", type_text)
        dlg = self._dialog()
        sel = WebDriverWait(dlg, 4).until(EC.presence_of_element_located(self.DIALOG_TYPE_SELECT))
        self._js_click_el(sel)

        # 等待下拉框
        WebDriverWait(self.driver, 6).until(
            EC.presence_of_element_located(
                (By.XPATH, '(//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))])[last()]')
            )
        )

        # 根据类型选择选项
        if "通知" in type_text:
            option = WebDriverWait(self.driver, 4).until(EC.presence_of_element_located(self.DIALOG_TYPE_OPTION_NOTICE))
        elif "公告" in type_text:
            option = WebDriverWait(self.driver, 4).until(EC.presence_of_element_located(self.DIALOG_TYPE_OPTION_ANNOUNCEMENT))
        else:
            raise TimeoutException(f"未知的通知类型：{type_text}")

        self._js_click_el(option)
        self.wait_vue_stable()

    def dialog_select_status(self, status_text):
        """弹窗选择状态（正常/关闭）"""
        logger.info("弹窗选择状态: %s", status_text)
        dlg = self._dialog()
        if "正常" in status_text or "启用" in status_text:
            label = WebDriverWait(dlg, 4).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        './/label[contains(@class,"el-radio")][.//span[normalize-space(.)="正常"]]',
                    )
                )
            )
        elif "关闭" in status_text or "禁用" in status_text:
            label = WebDriverWait(dlg, 4).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        './/label[contains(@class,"el-radio")][.//span[normalize-space(.)="关闭"]]',
                    )
                )
            )
        else:
            raise TimeoutException(f"未知的状态：{status_text}")

        self._js_click_el(label)
        self.wait_vue_stable()

    def dialog_input_content(self, value):
        """弹窗输入通知内容"""
        logger.info("弹窗输入通知内容: %s", value)
        dlg = self._dialog()
        el = WebDriverWait(dlg, 4).until(EC.presence_of_element_located(self.DIALOG_CONTENT_TEXTAREA))
        self._js_click_el(el)
        try:
            el.clear()
        except Exception:
            pass
        try:
            el.send_keys(Keys.CONTROL + "a")
            el.send_keys(Keys.DELETE)
        except Exception:
            pass
        if value:
            el.send_keys(value)

    def dialog_confirm(self):
        """新增/修改弹窗确认"""
        logger.info("点击弹窗确认按钮")
        locators = [
            self.DIALOG_CONFIRM,
            (
                By.XPATH,
                '//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]'
                '//div[@role="dialog" and (@aria-label="添加通知" or @aria-label="修改通知")]'
                '//footer//button[.//span[normalize-space(.)="确定"] or normalize-space(.)="确定"]',
            ),
            (
                By.XPATH,
                '//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]'
                '//div[@role="dialog" and (@aria-label="添加通知" or @aria-label="修改通知")]'
                '//footer//button[contains(@class,"el-button--primary")]',
            ),
            # 兜底：dialog 内的 primary 按钮
            (
                By.XPATH,
                '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]'
                '//div[@role="dialog"])[last()]//button[contains(@class,"el-button--primary")]',
            ),
        ]
        last_err = None
        for locator in locators:
            try:
                btn = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(locator))
                self._scroll_into_view(btn)
                self._js_click_el(btn)
                self._wait_loading_gone(timeout=3)
                self.wait_vue_stable()
                return
            except Exception as e:
                last_err = e
        logger.error("未找到新增/修改弹窗确定按钮")
        raise last_err or TimeoutException("未找到新增/修改弹窗确定按钮")

    def dialog_delete_confirm(self):
        """删除确认弹窗"""
        logger.info("点击删除确认按钮")
        locators = [
            self.DIALOG_DELETE_CONFIRM,
            (
                By.XPATH,
                '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]'
                '//div[contains(@class,"el-message-box")])[last()]'
                '//button[contains(@class,"el-button--primary")]',
            ),
            # 兜底：message box 内的 primary 按钮
            (
                By.XPATH,
                '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]'
                '//div[contains(@class,"el-message-box")])[last()]'
                '//div[contains(@class,"el-message-box__btns")]//button',
            ),
        ]
        last_err = None
        for locator in locators:
            try:
                btn = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(locator))
                self._scroll_into_view(btn)
                self._js_click_el(btn)
                self._wait_loading_gone(timeout=3)
                self.wait_vue_stable()
                return
            except Exception as e:
                last_err = e
        logger.error("未找到删除确认按钮")
        raise last_err or TimeoutException("未找到删除确认按钮")

    def _dialog(self):
        """获取弹窗"""
        return self.find(self.DIALOG_PANEL)

    def is_dialog_open(self):
        """判断弹窗是否打开"""
        try:
            dialogs = self.find_all(self.DIALOG_PANEL)
            for d in dialogs:
                try:
                    if d.is_displayed():
                        return True
                except Exception:
                    continue
            return False
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════════
    #  表格操作
    # ══════════════════════════════════════════════════════════════════════

    def get_empty_text(self):
        """获取空数据提示"""
        self._wait_loading_gone(timeout=8)
        try:
            el = self.find(self.EMPTY_TEXT)
            return (el.text or "").strip()
        except Exception:
            return ""

    def get_table_headers(self):
        """JS提取表格表头（含重试，应对Element Plus异步渲染）

        注意：此方法在旧版中包含了独立的重试逻辑。为保持向后兼容，
        在旧版行为基础上，优先使用 BasePage.get_table_headers。
        """
        logger.info("获取表格表头")
        # 委托给 BasePage 的 get_table_headers，使用最小列数=0 兼容性更好
        return super().get_table_headers(min_columns=0, timeout=15)

    def get_column_index_by_header(self, header_text):
        """获取表头索引"""
        logger.info("获取表头索引: %s", header_text)
        self._wait_loading_gone(timeout=10)
        wrapper = self.find(self.MAIN_TABLE_HEADER_WRAPPER)
        ths = wrapper.find_elements(By.XPATH, ".//table//th")
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
        """获取列数据

        注意：此方法覆盖 BasePage.get_column_data 以保持旧版定位器兼容性。
        如果 MAIN_TABLE_BODY_WRAPPER 定位失败，降级到 BasePage 实现。
        """
        logger.info("获取第 %d 列数据", col_index)
        self._wait_loading_gone(timeout=10)
        try:
            wrapper = self.find(self.MAIN_TABLE_BODY_WRAPPER)
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
        except Exception:
            logger.warning("MAIN_TABLE_BODY_WRAPPER 定位失败，降级到 BasePage 实现")
            return super().get_column_data(col_index)

    def get_table_row_count(self):
        """获取表格行数"""
        logger.info("获取表格行数")
        self._wait_loading_gone(timeout=10)
        try:
            wrapper = self.find(self.MAIN_TABLE_BODY_WRAPPER)
            rows = wrapper.find_elements(By.XPATH, ".//table/tbody/tr")
            count = 0
            for r in rows:
                try:
                    if r.is_displayed():
                        count += 1
                except Exception:
                    continue
            return count
        except Exception:
            logger.warning("MAIN_TABLE_BODY_WRAPPER 定位失败，降级到 BasePage 实现")
            return super().get_table_row_count()

    def click_row_action(self, action_text, row_index=1):
        """点击行操作按钮"""
        logger.info("点击第 %d 行操作按钮: %s", row_index, action_text)
        self._wait_loading_gone(timeout=10)
        row = WebDriverWait(self.driver, 4).until(
            EC.presence_of_element_located(
                (By.XPATH, f'(//div[contains(@class,"el-table__body-wrapper")]//tbody/tr)[{int(row_index)}]')
            )
        )
        act = (action_text or "").strip()
        btn_loc = (By.XPATH, f'.//button[.//*[normalize-space(.)="{act}"] or normalize-space(.)="{act}"]')
        btn = row.find_element(*btn_loc)
        self._js_click_el(btn)
        self.wait_vue_stable()

    # ══════════════════════════════════════════════════════════════════════
    #  分页操作
    # ══════════════════════════════════════════════════════════════════════

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
            logger.info("点击下一页")
            btn = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located(BasePage.NEXT_PAGE)
            )
            self._js_click_el(btn)
            self._wait_loading_gone(timeout=10)
            return True
        except Exception:
            logger.warning("点击下一页失败（可能已在最后一页）")
            return False

    # ══════════════════════════════════════════════════════════════════════
    #  内部辅助方法
    # ══════════════════════════════════════════════════════════════════════

    def _clear_input(self, locator):
        """清空输入框"""
        el = self.find(locator)
        self._scroll_into_view(el)
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        return el
