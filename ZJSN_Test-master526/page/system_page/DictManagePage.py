"""字典管理页面 Page Object — 重构版

变更记录:
  2026-06-11: 继承 BasePage，去绝对XPath，去time.sleep→BasePage等待方法
"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class DictManagePage(BasePage):
    """字典管理页面操作 — 继承 BasePage"""

    # ══════════════════════════════════════════════════════════════════
    #  页面专属定位器（CSS优先 → 相对XPath → 文本匹配）
    # ══════════════════════════════════════════════════════════════════

    TAB_DICT = (By.XPATH, '//div[contains(@class,"el-tabs__item") and normalize-space(.)="字典"]')
    TAB_DICT_CATEGORY = (By.XPATH, '//div[contains(@class,"el-tabs__item") and normalize-space(.)="字典分类"]')

    CATEGORY_FILTER_ALL = (By.XPATH, '//span[contains(@class,"el-radio-button__inner") and normalize-space(.)="全部"]/ancestor::label[1]')
    CATEGORY_FILTER_SYSTEM = (By.XPATH, '//span[contains(@class,"el-radio-button__inner") and normalize-space(.)="系统"]/ancestor::label[1]')
    CATEGORY_FILTER_CUSTOM = (By.XPATH, '//span[contains(@class,"el-radio-button__inner") and normalize-space(.)="自定义"]/ancestor::label[1]')
    CATEGORY_SEARCH_INPUT = (By.XPATH, '//input[contains(@placeholder,"搜索字典分类")]')

    CATEGORY_ADD_BUTTON_FALLBACK = (
        By.XPATH,
        '//div[contains(@class,"dict-type-panel")]//button[.//span[contains(text(),"新增") or contains(text(),"添加")]]',
    )

    CATEGORY_ITEM_BY_TEXT_CONTAINS = (
        By.XPATH,
        '//div[contains(@class,"dict-type-panel")]//*[self::span or self::div][contains(normalize-space(.),"{text}")]',
    )

    DICT_LABEL_INPUT = (By.XPATH, '//input[contains(@placeholder,"字典") and (contains(@placeholder,"标签") or contains(@placeholder,"名称") or contains(@placeholder,"键值"))]')
    SEARCH_BUTTON = (By.XPATH, '//button[.//*[normalize-space(.)="搜索" or normalize-space(.)="查询"] or contains(normalize-space(.),"搜索") or contains(normalize-space(.),"查询")]')
    RESET_BUTTON = (By.XPATH, '//button[.//*[normalize-space(.)="重置"] or contains(normalize-space(.),"重置")]')

    STATUS_SELECT = (
        By.XPATH,
        '//div[contains(@class,"el-form")]//div[contains(@class,"el-select")][.//label[contains(text(),"状态")]]',
    )
    STATUS_SELECT_TRIGGER = (
        By.XPATH,
        '(//div[contains(@class,"el-select__wrapper")])[1]',
    )

    TOOLBAR_ADD = (By.XPATH, '//button[.//*[normalize-space(.)="新增"] or contains(normalize-space(.),"新增")]')
    TOOLBAR_EXPORT = (By.XPATH, '//button[.//*[normalize-space(.)="导出"] or contains(normalize-space(.),"导出")]')

    FIRST_ROW_EDIT_BUTTON = (
        By.XPATH,
        '(//tr[contains(@class,"el-table__row")])[1]//button[.//span[contains(text(),"编辑")]]',
    )
    FIRST_ROW_DELETE_BUTTON = (
        By.XPATH,
        '(//tr[contains(@class,"el-table__row")])[1]//button[.//span[contains(text(),"删除")]]',
    )

    # 复用 BasePage 已有定位器：BasePage.TOTAL_COUNT, BasePage.TABLE_ROWS, BasePage.LOADING_MASK, BasePage.TOAST

    MESSAGEBOX_CONFIRM = (
        By.XPATH,
        '(//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))])[last()]'
        '//button[contains(translate(normalize-space(.)," ",""),"确定") or contains(translate(normalize-space(.)," ",""),"确认")]',
    )
    MESSAGEBOX_CONFIRM_FALLBACKS = [
        (By.XPATH, '/html/body/div[last()]//div[contains(@class,"el-message-box")]//button[2]'),
        (By.XPATH, '(//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))])[last()]//button[2]'),
        (By.XPATH, '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]'
         '//button[contains(translate(normalize-space(.)," ",""),"确定") or contains(translate(normalize-space(.)," ",""),"确认")])[last()]'),
    ]
    MESSAGEBOX_CANCEL = (
        By.XPATH,
        '(//div[contains(@class,"el-message-box") and not(contains(@style,"display: none"))])[last()]//button[contains(translate(normalize-space(.)," ",""),"取消")]',
    )

    DIALOG_CONFIRM_FALLBACKS = [
        (By.XPATH, '/html/body/div[5]/div/div/footer/div/button[1]/span/ancestor::button[1]'),
        (By.XPATH, '/html/body/div[6]/div/div/footer/div/button[1]/span/ancestor::button[1]'),
        (By.XPATH, '(//footer[contains(@class,"el-dialog__footer")]'
         '//button[contains(translate(normalize-space(.)," ",""),"确定")])[last()]'),
        (By.XPATH, '(//div[contains(@class,"el-dialog")])[last()]'
         '//button[contains(translate(normalize-space(.)," ",""),"确定")]'),
    ]
    DIALOG_CANCEL_FALLBACKS = [
        (By.XPATH, '/html/body/div[5]/div/div/footer/div/button[2]'),
        (By.XPATH, '/html/body/div[6]/div/div/footer/div/button[2]'),
        (By.XPATH, '(//footer[contains(@class,"el-dialog__footer")]//button[.//*[normalize-space(.)="取消"]])[last()]'),
        (By.XPATH, '(//div[contains(@class,"el-dialog")])[last()]//button[.//*[normalize-space(.)="取消"] or contains(normalize-space(.),"取消")]'),
    ]

    TOAST_TEXT = (By.CSS_SELECTOR, ".el-message__content")
    TOAST_TEXT_FALLBACK = (
        By.CSS_SELECTOR,
        'div[id^="message_"] p, div[id^="message_"] .el-message__content, div[id^="message_"]',
    )
    TOAST_MESSAGE_ENHANCED = (By.XPATH, '(//*[contains(@class,"el-message__content") and normalize-space(.)!=""])[last()]')

    def __init__(self, driver, timeout=None):
        """初始化 — 继承 BasePage"""
        super().__init__(driver, timeout)

    def _wait_table_settled(self, timeout=8):
        """等待表格数据加载完成（loading 遮罩消失）"""
        self._wait_loading_gone(timeout=timeout)

    def wait_for_toast_text(self, timeout=6):
        """等待并获取Toast提示消息文本"""
        end = time.time() + timeout
        last = ""
        while time.time() < end:
            # 优先使用增强的XPath定位器
            try:
                els = self.driver.find_elements(*self.TOAST_MESSAGE_ENHANCED)
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
                els = self.driver.find_elements(*self.TOAST_TEXT)
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
                els = self.driver.find_elements(*self.TOAST_TEXT_FALLBACK)
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

            time.sleep(0.3)
        return last

    PAGE_ROUTE = "#/system/dict"

    def navigate(self):
        """导航到字典管理页面 — 唯一入口"""
        logger.info("导航到 → 系统管理 → 字典管理")
        self.navigate_to("系统管理", "字典管理")
        self.wait_page_ready(timeout=15)
        self._wait_table_settled(timeout=15)
        self.wait_vue_stable()
        return self

    def navigate_to_dict_management(self):
        """通过侧边栏导航到字典管理页面（使用统一导航器）"""
        logger.info("导航到 → 系统管理 → 字典管理")
        self.navigate_to("系统管理", "字典管理")
        self._wait_table_settled(timeout=15)

    def switch_to_dict_tab(self):
        try:
            tab = self.wait.until(EC.presence_of_element_located(self.TAB_DICT))
            self.driver.execute_script("arguments[0].click();", tab)
            self._wait_table_settled(timeout=8)
            logger.info("已切换到字典标签页")
            return True
        except Exception:
            logger.warning("切换到字典标签页失败")
            return False

    # ── 兼容重构后测试 API 的包装方法 ──
    def fill_dict_form(self, label, key_value, status, sort_value=None, remark=None):
        """填充字典弹窗表单（兼容包装）"""
        self.input_dialog_field("字典标签", label)
        self.input_dialog_field("字典键值", key_value)
        self.select_dialog_status(status)
        if sort_value is not None:
            self.input_dialog_field("排序", sort_value)
        if remark:
            self.input_dialog_field("备注", remark)

    def click_dialog_save(self):
        """点击弹窗保存（兼容包装）"""
        self.click_dialog_confirm()

    def switch_to_category_tab(self):
        locators = [
            self.TAB_DICT_CATEGORY,
            (By.XPATH, '//*[self::span or self::div or self::a][normalize-space(.)="字典分类"]/ancestor::*[self::a or self::div or self::li][1]'),
            (By.XPATH, '//button[.//*[normalize-space(.)="字典分类"] or normalize-space(.)="字典分类"]'),
        ]
        for loc in locators:
            try:
                tab = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(loc))
                if tab.is_displayed():
                    self.driver.execute_script("arguments[0].click();", tab)
                    self._wait_table_settled(timeout=10)
                    logger.info("已切换到字典分类标签页")
                    return True
            except Exception:
                continue
        logger.warning("切换到字典分类标签页失败")
        return False

    def click_category_filter(self, filter_text):
        mapping = {"全部": self.CATEGORY_FILTER_ALL, "系统": self.CATEGORY_FILTER_SYSTEM, "自定义": self.CATEGORY_FILTER_CUSTOM}
        loc = mapping.get(filter_text)
        if not loc:
            raise TimeoutException(f"未知分类筛选: {filter_text}")
        el = self.wait.until(EC.presence_of_element_located(loc))
        self.driver.execute_script("arguments[0].click();", el)
        self._wait_table_settled(timeout=8)
        logger.info("已点击分类筛选: %s", filter_text)

    def input_category_search(self, text):
        el = self.wait.until(EC.presence_of_element_located(self.CATEGORY_SEARCH_INPUT))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        if text:
            el.send_keys(text)
        self.wait_vue_stable()

    def click_category_add(self):
        btn = self.wait.until(EC.presence_of_element_located(self.CATEGORY_ADD_BUTTON_FALLBACK))
        self.driver.execute_script("arguments[0].click();", btn)
        self._get_visible_dialog(timeout=8)
        logger.info("已点击新增分类")

    def category_item_exists(self, category_name):
        item_xpath = self.CATEGORY_ITEM_BY_TEXT_CONTAINS[1].format(text=category_name)
        els = self.driver.find_elements(By.XPATH, item_xpath)
        for el in els:
            try:
                if el.is_displayed():
                    return True
            except Exception:
                continue
        return False

    def get_category_names(self, limit=10):
        xpaths = [
            '//div[contains(@class,"dict-type-panel")]//*[contains(@class,"dict-type-item")]',
            '//div[contains(@class,"dict-type-panel")]//div[contains(@class,"el-scrollbar__view")]/*',
        ]
        names = []
        seen = set()
        for xp in xpaths:
            els = self.driver.find_elements(By.XPATH, xp)
            for el in els:
                try:
                    if not el.is_displayed():
                        continue
                    t = (el.text or "").strip().replace("\n", " ").strip()
                    if not t:
                        continue
                    if t in {"全部", "系统", "自定义"}:
                        continue
                    if "搜索字典分类" in t:
                        continue
                    name = t.split("(")[0].strip()
                    if not name or name in seen:
                        continue
                    seen.add(name)
                    names.append(name)
                    if len(names) >= limit:
                        return names
                except Exception:
                    continue
        return names

    def _find_category_container(self, category_name):
        xp_candidates = [
            f'//div[contains(@class,"dict-type-panel")]//*[contains(@class,"dict-type-item")][.//*[contains(normalize-space(.),"{category_name}")]]',
            f'//div[contains(@class,"dict-type-panel")]//*[self::div or self::li][.//*[contains(normalize-space(.),"{category_name}")]]',
        ]
        for xp in xp_candidates:
            try:
                el = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.XPATH, xp)))
                if el.is_displayed():
                    return el
            except Exception:
                continue
        return None

    def category_action_exists(self, category_name, action):
        container = self._find_category_container(category_name)
        if not container:
            return False
        if action == "编辑":
            xps = [
                './/i[contains(@class,"el-icon") and contains(@class,"edit")]/ancestor::*[self::button or self::span or self::a][1]',
                './/*[normalize-space(.)="编辑"]/ancestor::*[self::button or self::a][1]',
            ]
        elif action == "删除":
            xps = [
                './/i[contains(@class,"el-icon") and contains(@class,"delete")]/ancestor::*[self::button or self::span or self::a][1]',
                './/*[normalize-space(.)="删除"]/ancestor::*[self::button or self::a][1]',
            ]
        else:
            return False
        for xp in xps:
            try:
                els = container.find_elements(By.XPATH, xp)
                for el in els:
                    try:
                        if el.is_displayed():
                            return True
                    except Exception:
                        continue
            except Exception:
                continue
        try:
            btns = container.find_elements(By.XPATH, './/button')
            visible_btns = []
            for b in btns:
                try:
                    if b.is_displayed():
                        visible_btns.append(b)
                except Exception:
                    continue
            if action == "编辑":
                return len(visible_btns) >= 1
            if action == "删除":
                return len(visible_btns) >= 2
        except Exception:
            pass
        return False

    def click_category_action(self, category_name, action):
        container = self._find_category_container(category_name)
        if not container:
            raise TimeoutException(f"未找到分类：{category_name}")
        if action == "编辑":
            xps = [
                './/i[contains(@class,"el-icon") and contains(@class,"edit")]/ancestor::*[self::button or self::a][1]',
                './/*[normalize-space(.)="编辑"]/ancestor::*[self::button or self::a][1]',
            ]
        elif action == "删除":
            xps = [
                './/i[contains(@class,"el-icon") and contains(@class,"delete")]/ancestor::*[self::button or self::a][1]',
                './/*[normalize-space(.)="删除"]/ancestor::*[self::button or self::a][1]',
            ]
        else:
            raise TimeoutException(f"未知分类操作：{action}")
        for xp in xps:
            try:
                el = container.find_element(By.XPATH, xp)
                self.driver.execute_script("arguments[0].click();", el)
                self.wait_vue_stable()
                return
            except Exception:
                continue
        try:
            btns = container.find_elements(By.XPATH, './/button')
            visible_btns = []
            for b in btns:
                try:
                    if b.is_displayed():
                        visible_btns.append(b)
                except Exception:
                    continue
            if action == "编辑" and len(visible_btns) >= 1:
                self.driver.execute_script("arguments[0].click();", visible_btns[0])
                self.wait_vue_stable()
                return
            if action == "删除" and len(visible_btns) >= 2:
                self.driver.execute_script("arguments[0].click();", visible_btns[1])
                self.wait_vue_stable()
                return
        except Exception:
            pass
        raise TimeoutException(f"未找到分类\"{category_name}\"的操作按钮：{action}")

    def add_category(self, name, code, is_system, sort_value, remark):
        self.switch_to_category_tab()
        self.click_category_add()
        self.input_dialog_field("分类名称", name)
        self.input_dialog_field("分类编码", code)
        self.select_dialog_is_system("是" if is_system else "否")
        if sort_value is not None:
            self.input_dialog_field("排序", sort_value)
        if remark is not None and remark != "":
            self.input_dialog_field("备注", remark)
        self.click_dialog_confirm()
        msg = self.wait_for_toast_text(timeout=6)
        logger.info("新增分类结果: %s", msg)
        return msg

    def ensure_category_exists(self, name, code="C123", is_system=True, sort_value=1, remark="123"):
        self.switch_to_category_tab()
        self.click_category_filter("全部")
        self.input_category_search(name)
        if self.category_item_exists(name):
            logger.info("分类已存在: %s", name)
            return "已存在"
        self.input_category_search("")
        return self.add_category(name, code, is_system, sort_value, remark)

    def input_dict_label(self, value):
        el = self.wait.until(EC.presence_of_element_located(self.DICT_LABEL_INPUT))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        if value:
            el.send_keys(value)

    def select_category(self, category_name):
        self.input_category_search(category_name)
        item_xpath = self.CATEGORY_ITEM_BY_TEXT_CONTAINS[1].format(text=category_name)
        item = self.wait.until(EC.presence_of_element_located((By.XPATH, item_xpath)))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", item)
        self.driver.execute_script("arguments[0].click();", item)
        self._wait_table_settled(timeout=10)

    def get_dict_label_value(self):
        try:
            return (self.driver.find_element(*self.DICT_LABEL_INPUT).get_attribute("value") or "").strip()
        except Exception:
            return ""

    def select_status(self, text):
        """选择状态下拉（含重试，应对 Vue 异步渲染）"""
        if text == "禁用":
            text = "停用"
        if text not in {"全部", "启用", "停用"}:
            raise TimeoutException(f"未知状态: {text}")

        option_texts = [text]
        if text == "停用":
            option_texts.append("禁用")

        for attempt in range(3):
            trigger = self.wait.until(EC.presence_of_element_located(self.STATUS_SELECT_TRIGGER))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", trigger)
            self.driver.execute_script("arguments[0].click();", trigger)
            self.wait_vue_stable()

            option = self._find_dropdown_option(option_texts)
            if option:
                self.driver.execute_script("arguments[0].click();", option)
                self.wait_vue_stable()
                logger.info("已选择状态: %s", text)
                return
            self._wait_loading_gone(timeout=1)

        raise TimeoutException(f"未找到状态下拉选项: {text}")

    def _find_dropdown_option(self, option_texts):
        """在展开的下拉列表中查找选项"""
        for option_text in option_texts:
            option_xpath_candidates = [
                f'(//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]'
                f'//li[contains(@class,"el-select-dropdown__item")][.//span[normalize-space(.)="{option_text}"] or normalize-space(.)="{option_text}"])[last()]',
                f'(//div[contains(@class,"el-popper") and not(contains(@style,"display: none"))]'
                f'//*[self::li or self::div][contains(@class,"item")][.//span[normalize-space(.)="{option_text}"] or normalize-space(.)="{option_text}"])[last()]',
                f'(//*[self::li or self::div or self::span][normalize-space(.)="{option_text}" and not(ancestor::div[contains(@class,"el-dialog")])])[last()]',
            ]
            for xp in option_xpath_candidates:
                try:
                    candidate = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.XPATH, xp)))
                    if candidate.is_displayed():
                        return candidate
                except Exception:
                    continue
        return None

    def click_search(self):
        self._wait_table_settled(timeout=6)
        btn = self.wait.until(EC.presence_of_element_located(self.SEARCH_BUTTON))
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_table_settled(timeout=10)
        self.wait_vue_stable()
        logger.info("已点击搜索按钮")

    def click_reset(self):
        self._wait_table_settled(timeout=6)
        btn = self.wait.until(EC.presence_of_element_located(self.RESET_BUTTON))
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_table_settled(timeout=10)
        self.wait_vue_stable()
        logger.info("已点击重置按钮")

    def click_add(self):
        self._wait_table_settled(timeout=6)
        btn = self.wait.until(EC.presence_of_element_located(self.TOOLBAR_ADD))
        self.driver.execute_script("arguments[0].click();", btn)
        self._get_visible_dialog(timeout=8)
        logger.info("已点击新增按钮")

    def click_export(self):
        self._wait_table_settled(timeout=6)
        btn = self.wait.until(EC.presence_of_element_located(self.TOOLBAR_EXPORT))
        self.driver.execute_script("arguments[0].click();", btn)
        logger.info("已点击导出按钮")
        return self.confirm_message_box_if_present()

    def confirm_message_box_if_present(self):
        try:
            btn = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(self.MESSAGEBOX_CONFIRM))
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_vue_stable()
            logger.info("已确认消息框")
            return True
        except Exception:
            pass
        for loc in self.MESSAGEBOX_CONFIRM_FALLBACKS:
            try:
                btn = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located(loc))
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_vue_stable()
                    logger.info("已确认消息框（备用定位器）")
                    return True
            except Exception:
                continue
        return False

    def get_empty_text(self):
        self._wait_table_settled(timeout=8)
        try:
            el = self.driver.find_element(*self.EMPTY_TEXT)
            return (el.text or "").strip()
        except Exception:
            return ""

    def get_table_headers(self):
        """JS提取表格表头（含重试，比XPath text更可靠）"""
        for attempt in range(6):
            self._wait_table_settled(timeout=10)
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
        self._wait_table_settled(timeout=10)
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        count = 0
        for r in rows:
            try:
                if r.is_displayed():
                    count += 1
            except Exception:
                continue
        return count

    def get_column_index_by_header(self, header_text):
        self._wait_table_settled(timeout=10)
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

    def get_column_data(self, col_index):
        self._wait_table_settled(timeout=10)
        cell_xpath = f'//div[contains(@class,"el-table__body-wrapper")]//tbody/tr/td[{col_index}]//div[contains(@class,"cell")]'
        cells = self.driver.find_elements(By.XPATH, cell_xpath)
        values = []
        for c in cells:
            try:
                t = (c.text or "").strip().replace("\n", " ").strip()
                if t:
                    values.append(t)
            except Exception:
                continue
        return values

    def _get_visible_dialog(self, timeout=8):
        locator = (
            By.XPATH,
            '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]//div[contains(@class,"el-dialog")]'
            ' | //div[contains(@class,"el-dialog__wrapper") and not(contains(@style,"display: none"))]//div[contains(@class,"el-dialog")])[last()]',
        )
        return WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(locator))

    def _get_dialog_form_item(self, label_text):
        item_xpath = (
            f'.//div[contains(@class,"el-form-item")]'
            f'[.//label[contains(@class,"el-form-item__label") and contains(normalize-space(.), "{label_text}")]]'
        )

        def _locate(_driver):
            dialog = self._get_visible_dialog(timeout=8)
            return dialog.find_element(By.XPATH, item_xpath)

        return WebDriverWait(self.driver, 8).until(lambda d: _locate(d))

    def input_dialog_field(self, label_text, value):
        item = self._get_dialog_form_item(label_text)
        el = item.find_element(By.XPATH, './/input|.//textarea')
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        except Exception:
            pass
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        if value is not None and value != "":
            el.send_keys(str(value))

    def select_dialog_status(self, status_text):
        if status_text == "禁用":
            status_text = "停用"
        item = self._get_dialog_form_item("状态")
        label = item.find_element(
            By.XPATH,
            f'.//label[(contains(@class,"el-radio") or contains(@class,"el-radio-button"))][.//*[normalize-space(.)="{status_text}"]]',
        )
        self.driver.execute_script("arguments[0].click();", label)
        self.wait_vue_stable()

    def select_dialog_is_system(self, option_text):
        item = self._get_dialog_form_item("是否系统")
        label = item.find_element(
            By.XPATH,
            f'.//label[contains(@class,"el-radio")][.//*[normalize-space(.)="{option_text}"]]',
        )
        self.driver.execute_script("arguments[0].click();", label)
        self.wait_vue_stable()

    def get_dialog_is_system_selected(self):
        item = self._get_dialog_form_item("是否系统")
        try:
            checked = item.find_element(By.XPATH, './/label[contains(@class,"el-radio") and contains(@class,"is-checked")]')
            t = (checked.text or "").strip()
            return t
        except Exception:
            return ""

    def click_dialog_confirm(self):
        try:
            dialog = self._get_visible_dialog(timeout=8)
            btns = dialog.find_elements(By.XPATH, './/button[contains(translate(normalize-space(.)," ",""),"确定")]')
            for btn in btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_vue_stable()
                        logger.info("已点击弹窗确定按钮")
                        return
                except Exception:
                    continue
        except Exception:
            pass

        for loc in self.DIALOG_CONFIRM_FALLBACKS:
            try:
                btn = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(loc))
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_vue_stable()
                    logger.info("已点击弹窗确定按钮（备用定位器）")
                    return
            except Exception:
                continue
        raise TimeoutException("未找到弹窗确定按钮")

    def click_dialog_cancel(self):
        try:
            dialog = self._get_visible_dialog(timeout=8)
            btns = dialog.find_elements(By.XPATH, './/button[.//*[normalize-space(.)="取消"] or contains(normalize-space(.),"取消")]')
            for btn in btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_vue_stable()
                        return
                except Exception:
                    continue
        except Exception:
            pass

        for loc in self.DIALOG_CANCEL_FALLBACKS:
            try:
                btn = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(loc))
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_vue_stable()
                    return
            except Exception:
                continue
        raise TimeoutException("未找到弹窗取消按钮")

    def click_row_action(self, dict_label, action_text):
        row_xpath_candidates = [
            f'//tr[contains(@class,"el-table__row")][.//td[1]//*[contains(normalize-space(.),"{dict_label}")]]',
            f'//tr[contains(@class,"el-table__row")][contains(normalize-space(.),"{dict_label}")]',
        ]
        for row_xpath in row_xpath_candidates:
            btn_xpath_candidates = [
                f'{row_xpath}//td[last()]//*[self::span or self::button][normalize-space(.)="{action_text}"]/ancestor::button[1]',
                f'{row_xpath}//td[last()]//*[normalize-space(.)="{action_text}"]',
            ]
            for xp in btn_xpath_candidates:
                try:
                    el = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.XPATH, xp)))
                    if el.is_displayed():
                        self.driver.execute_script("arguments[0].click();", el)
                        self.wait_vue_stable()
                        logger.info("已点击行操作: %s → %s", dict_label, action_text)
                        return
                except Exception:
                    continue
        raise TimeoutException(f"未找到字典'{dict_label}'的操作按钮: {action_text}")

    def click_first_row_edit(self):
        btn = self.wait.until(EC.presence_of_element_located(self.FIRST_ROW_EDIT_BUTTON))
        self.driver.execute_script("arguments[0].click();", btn)
        self.wait_vue_stable()
        logger.info("已点击第一行编辑按钮")

    def click_first_row_delete(self):
        btn = self.wait.until(EC.presence_of_element_located(self.FIRST_ROW_DELETE_BUTTON))
        self.driver.execute_script("arguments[0].click();", btn)
        self.wait_vue_stable()
        logger.info("已点击第一行删除按钮")

    def delete_by_label(self, dict_label):
        self.click_row_action(dict_label, "删除")
        self.confirm_message_box_if_present()
        msg = self.wait_for_toast_text(timeout=6)
        if not msg:
            try:
                self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-message-box, .el-overlay-dialog")))
            except Exception:
                pass
        logger.info("删除字典标签 '%s' 结果: %s", dict_label, msg)
        return msg

    def wait_dialog_closed(self, timeout=5):
        """等待当前弹窗关闭"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-overlay-dialog, .el-dialog__wrapper, .el-dialog"))
            )
            return True
        except Exception:
            return False
