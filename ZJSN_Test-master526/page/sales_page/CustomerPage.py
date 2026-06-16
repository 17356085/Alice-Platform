"""客户管理页面 Page Object — 企业级（基于真实页面 HTML 分析）

==== 页面概述 ====
  路径：销售管理 → 客户管理  (#/sales/customer)
  功能：维护企业客户主数据，管理客户资质、等级及合作状态
  操作：新增客户、编辑、查看、资质维护、条件查询

==== 页面结构（来源：真实 HTML 分析报告）====
  搜索区：
    - input[placeholder="客户名称/编码"]         （客户名称/编码联合搜索）
    - .el-select[placeholder="客户等级"]         （客户等级筛选）
    - .el-select[placeholder="合作状态"]         （合作状态筛选）
    - button: 查询 | 重置 | 新增客户

  表格区（7 列）：
    客户编码 | 客户名称 | 联系人 | 联系电话 | 客户等级 | 合作状态 | 操作
    操作列按钮：查看 | 编辑 | 资质维护

  新增客户弹窗（11 个字段）：
    必填 — 客户编码、客户名称、统一社会信用代码(maxlength=18)、客户等级(Select)、
           联系人、联系电话、注册地址(Textarea, maxlength=500)、合作状态(Select)
    非必填 — 财务联系人、财务电话、客户备注(Textarea)

==== 定位策略（A/B/C 三级）====
  A级（推荐）：placeholder 语义属性、button text() 文本匹配、label 文本匹配
  B级（可用）：Element Plus 标准类（.el-table__row, .el-dialog__title）
  C级（禁止）：动态 id（el-id-*）、scoped CSS（data-v-*）、绝对结构索引

==== Vue/Element Plus 风险与处理 ====
  1. Select 下拉异步渲染：下拉面板通过 Teleport 挂载到 <body>，需等待可见后点击
  2. Dialog 动画与销毁：弹窗有过渡动画，关闭后 v-if 销毁 DOM
  3. Table 异步加载：查询后需等待加载遮罩消失 + 行数据渲染
  4. 标签页 keep-alive 缓存：切换标签页需手动刷新数据
"""
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from base.base_page import BasePage
from config import BASE_URL

logger = logging.getLogger(__name__)


class CustomerPage(BasePage):
    """客户管理页面 — 基于真实 HTML 的 Page Object"""

    # ==================================================================
    #  路由
    # ==================================================================
    PAGE_ROUTE = "#/sales/customer"

    # ==================================================================
    #  1. LOCATORS — 搜索区
    # ==================================================================
    # A级：placeholder 语义定位
    SEARCH_KEYWORD_INPUT = (
        By.XPATH,
        '//input[@placeholder="客户名称/编码"]',
    )
    # 搜索区 Select：通过 placeholder 文本定位每个 el-select
    SEARCH_LEVEL_TRIGGER = (
        By.XPATH,
        '//div[contains(@class,"el-select")]'
        '[.//span[contains(normalize-space(.),"客户等级")]]',
    )
    SEARCH_STATUS_TRIGGER = (
        By.XPATH,
        '//div[contains(@class,"el-select")]'
        '[.//span[contains(normalize-space(.),"合作状态")]]',
    )

    # ── 按钮：CSS_SELECTOR 优先（基于实际页面 class 结构，避免中文文本XPath匹配问题）──
    # 查询按钮：el-button--primary（工具栏唯一，非 is-link）
    BTN_SEARCH_CSS = (
        By.CSS_SELECTOR,
        'button.el-button--primary:not(.is-link)',
    )
    # 重置按钮：el-button 无颜色修饰符（工具栏中唯一仅有 el-button 类的按钮）
    BTN_RESET_CSS = (
        By.CSS_SELECTOR,
        'button.el-button:not([class*="el-button--"])',
    )
    # 新增客户按钮：el-button--success 无 is-link（排除行操作按钮）
    BTN_ADD_CUSTOMER_CSS = (
        By.CSS_SELECTOR,
        'button.el-button--success:not(.is-link)',
    )

    # ── XPath 文本匹配保底（CSS 失败时使用）──
    BTN_SEARCH_XPATH = (
        By.XPATH,
        '//button[contains(@class,"el-button--primary") and not(contains(@class,"is-link"))]',
    )
    BTN_RESET_XPATH = (
        By.XPATH,
        '//button[@class="el-button"]',
    )
    BTN_ADD_CUSTOMER_XPATH = (
        By.XPATH,
        '//button[contains(@class,"el-button--success") and not(contains(@class,"is-link"))]',
    )

    # ==================================================================
    #  1. LOCATORS — 表格区
    # ==================================================================
    # 表头文本 — A级
    TABLE_HEADER_CELLS = (
        By.XPATH,
        '//div[contains(@class,"el-table__header-wrapper")]//th//div[@class="cell"]',
    )
    # 数据行 — B级
    TABLE_ROWS_CSS = (
        By.CSS_SELECTOR,
        '.el-table__body-wrapper tbody tr.el-table__row',
    )
    # 空数据 — B级
    TABLE_EMPTY = (
        By.CSS_SELECTOR,
        '.el-table__empty-block, .el-table__empty-text',
    )

    # 列索引常量（1-based）
    COL_CODE = 1       # 客户编码
    COL_NAME = 2       # 客户名称
    COL_CONTACT = 3    # 联系人
    COL_PHONE = 4      # 联系电话
    COL_LEVEL = 5      # 客户等级
    COL_STATUS = 6     # 合作状态
    COL_OPERATIONS = 7  # 操作

    # 客户等级标签 CSS 类（B级）
    LEVEL_TAG_STRATEGIC = (
        By.CSS_SELECTOR,
        'span.sales-level-tag--strategic, '
        'span[class*="level"][class*="strategic"]',
    )
    LEVEL_TAG_IMPORTANT = (
        By.CSS_SELECTOR,
        'span.sales-level-tag--important, '
        'span[class*="level"][class*="important"]',
    )
    LEVEL_TAG_NORMAL = (
        By.CSS_SELECTOR,
        'span.sales-level-tag--normal, '
        'span[class*="level"][class*="normal"]',
    )

    # 合作状态标签 CSS 类（B级）
    STATUS_TAG_COOPERATING = (
        By.CSS_SELECTOR,
        'span.sales-status-tag--cooperating, '
        'span[class*="status"][class*="cooperating"]',
    )
    STATUS_TAG_TERMINATED = (
        By.CSS_SELECTOR,
        'span.sales-status-tag--terminated, '
        'span[class*="status"][class*="terminated"]',
    )

    # ==================================================================
    #  1. LOCATORS — 分页区
    # ==================================================================
    PAGINATION_TOTAL = (
        By.CSS_SELECTOR,
        '.el-pagination__total',
    )
    PAGINATION_NEXT = (
        By.CSS_SELECTOR,
        '.el-pagination .btn-next:not([disabled])',
    )
    PAGINATION_PREV = (
        By.CSS_SELECTOR,
        '.el-pagination .btn-prev:not([disabled])',
    )
    PAGINATION_SIZE_SELECT = (
        By.CSS_SELECTOR,
        '.el-pagination__sizes .el-select',
    )

    # ==================================================================
    #  1. LOCATORS — 新增/编辑弹窗
    # ==================================================================
    # A级：弹窗标题文本定位
    DIALOG_BY_TITLE = (
        By.XPATH,
        '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
        '[.//span[contains(@class,"el-dialog__title") and contains(text(),"客户")]]',
    )
    DIALOG_TITLE_ADD = (
        By.XPATH,
        '//span[contains(@class,"el-dialog__title") and contains(text(),"新增客户")]',
    )
    DIALOG_TITLE_EDIT = (
        By.XPATH,
        '//span[contains(@class,"el-dialog__title") and contains(text(),"编辑客户")]',
    )
    DIALOG_TITLE_VIEW = (
        By.XPATH,
        '//span[contains(@class,"el-dialog__title") and contains(text(),"客户详情")]',
    )

    # ── 弹窗表单：placeholder CSS_SELECTOR 定位（基于实际 DOM，最简单可靠）──
    # 必填字段 — input
    DIALOG_INPUT_CODE = (
        By.CSS_SELECTOR,
        'input[placeholder="请输入客户编码"]',
    )
    DIALOG_INPUT_NAME = (
        By.CSS_SELECTOR,
        'input[placeholder="请输入客户名称"]',
    )
    DIALOG_INPUT_CREDIT_CODE = (
        By.CSS_SELECTOR,
        'input[placeholder="请输入18位信用代码"]',
    )
    DIALOG_INPUT_CONTACT = (
        By.CSS_SELECTOR,
        'input[placeholder="请输入联系人"]',
    )
    DIALOG_INPUT_PHONE = (
        By.CSS_SELECTOR,
        'input[placeholder="请输入联系电话"]',
    )
    # 必填 — Textarea
    DIALOG_TEXTAREA_ADDRESS = (
        By.CSS_SELECTOR,
        'textarea[placeholder="请输入注册地址"]',
    )
    # 非必填字段
    DIALOG_INPUT_FINANCE_CONTACT = (
        By.CSS_SELECTOR,
        'input[placeholder="请输入财务联系人"]',
    )
    DIALOG_INPUT_FINANCE_PHONE = (
        By.CSS_SELECTOR,
        'input[placeholder="请输入财务电话"]',
    )
    DIALOG_TEXTAREA_REMARK = (
        By.CSS_SELECTOR,
        'textarea[placeholder="请输入备注信息"]',
    )

    # 弹窗底部按钮
    DIALOG_SAVE_BTN = (
        By.XPATH,
        '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
        '//button[contains(@class,"el-button--primary")]'
        '//span[contains(text(),"保存")]/parent::button',
    )
    DIALOG_CANCEL_BTN = (
        By.XPATH,
        '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
        '//button[contains(@class,"el-button") and not(contains(@class,"el-button--primary"))]'
        '//span[contains(text(),"取消")]/parent::button',
    )

    # ==================================================================
    #  1. LOCATORS — Element Plus 下拉面板（Teleport 到 body）
    # ==================================================================
    DROPDOWN_PANEL = (
        By.XPATH,
        '//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]',
    )
    DROPDOWN_OPTION_BY_TEXT = (
        By.XPATH,
        '//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]'
        '//li[contains(@class,"el-select-dropdown__item") and not(contains(@class,"is-disabled"))]'
        '[normalize-space(.)="{text}"]',
    )

    # ==================================================================
    #  2. PAGE METHODS — 构造
    # ==================================================================
    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    # ==================================================================
    #  2. PAGE METHODS — 导航
    # ==================================================================
    def navigate(self):
        """导航到客户管理页面（侧边栏 + 长等待确保 keep-alive 标签页渲染完毕）"""
        logger.info("导航到 → 客户管理 (%s)", self.PAGE_ROUTE)
        self.navigate_to("销售管理", "客户管理")
        self._wait_page_ready()

    # ==================================================================
    #  2. PAGE METHODS — 搜索区
    # ==================================================================
    def input_search_keyword(self, keyword):
        """输入客户名称/编码搜索关键字

        Args:
            keyword: 客户名称或编码（支持模糊匹配）
        """
        logger.info("搜索关键字: %s", keyword)
        self.input_text(self.SEARCH_KEYWORD_INPUT, keyword or "")

    def select_search_level(self, level_text):
        """选择客户等级筛选（键盘导航，绕过Teleport popper）

        Args:
            level_text: "战略客户" | "重要客户" | "一般客户"
        """
        logger.info("筛选客户等级: %s", level_text)
        trigger = self.find_clickable(self.SEARCH_LEVEL_TRIGGER)
        self._select_by_keyboard(trigger, level_text)
        self.wait_vue_stable()

    def select_search_status(self, status_text):
        """选择合作状态筛选（键盘导航，绕过Teleport popper）

        Args:
            status_text: "合作中" | "终止合作"
        """
        logger.info("筛选合作状态: %s", status_text)
        trigger = self.find_clickable(self.SEARCH_STATUS_TRIGGER)
        self._select_by_keyboard(trigger, status_text)
        self.wait_vue_stable()

    def click_search(self):
        """点击查询按钮，等待表格刷新"""
        logger.info("点击查询按钮")
        try:
            self.click(self.BTN_SEARCH_CSS)
        except TimeoutException:
            logger.warning("CSS 定位查询按钮失败，尝试 XPath 保底")
            self.click(self.BTN_SEARCH_XPATH)
        self._wait_table_ready()

    def click_reset(self):
        """点击重置按钮，清空所有搜索条件

        多重保底：CSS click → JS click → 导航刷新
        """
        logger.info("点击重置按钮")
        for attempt in range(2):
            try:
                el = self.find(self.BTN_RESET_CSS, timeout=3)
                self.driver.execute_script("arguments[0].click();", el)
                self._wait_table_ready()
                return
            except TimeoutException:
                try:
                    el = self.find(self.BTN_RESET_XPATH, timeout=2)
                    self.driver.execute_script("arguments[0].click();", el)
                    self._wait_table_ready()
                    return
                except TimeoutException:
                    if attempt == 0:
                        self._wait_loading_gone(timeout=1)  # 等待页面稳定后重试
        # 最终兜底：直接重新导航
        logger.warning("重置按钮始终不可用，重新导航页面")
        self.navigate()

    # ==================================================================
    #  2. PAGE METHODS — 表格行操作
    # ==================================================================
    def click_view(self, row_identifier):
        """点击指定行的「查看」按钮

        Args:
            row_identifier: 行标识文本（客户编码或客户名称）
        """
        logger.info("查看客户: %s", row_identifier)
        self._click_row_action(row_identifier, "查看")
        self._wait_dialog_ready()

    def click_edit(self, row_identifier):
        """点击指定行的「编辑」按钮

        Args:
            row_identifier: 行标识文本（客户编码或客户名称）
        """
        logger.info("编辑客户: %s", row_identifier)
        self._click_row_action(row_identifier, "编辑")
        self._wait_dialog_ready()

    def click_qualification(self, row_identifier):
        """点击指定行的「资质维护」按钮

        Args:
            row_identifier: 行标识文本（客户编码或客户名称）
        """
        logger.info("资质维护: %s", row_identifier)
        self._click_row_action(row_identifier, "资质维护")
        self._wait_dialog_ready()

    def click_add(self):
        """点击「新增客户」按钮，等待弹窗打开"""
        logger.info("点击新增客户按钮")
        # JS轮询：等待按钮渲染完成（getBoundingClientRect w>0 h>0）
        deadline = time.time() + 15
        while time.time() < deadline:
            ready = self.driver.execute_script(
                "var b=document.querySelector('button.el-button--success:not(.is-link)');"
                "if(!b)return'no-btn';var r=b.getBoundingClientRect();"
                "return r.width>0&&r.height>0?'ready':'w='+r.width+'h='+r.height;"
            )
            if ready == 'ready':
                break
            self._wait_loading_gone(timeout=0.5)
        # JS点击
        self.driver.execute_script(
            "var b=document.querySelector('button.el-button--success:not(.is-link)');"
            "b.scrollIntoView({block:'center'});b.click();"
        )
        self.wait_vue_stable()
        self._wait_dialog_ready()

    # ==================================================================
    #  2. PAGE METHODS — 弹窗表单填充
    # ==================================================================
    def fill_code(self, code):
        """填充客户编码"""
        logger.info("填充客户编码: %s", code)
        self.input_text(self.DIALOG_INPUT_CODE, str(code))

    def fill_name(self, name):
        """填充客户名称"""
        logger.info("填充客户名称: %s", name)
        self.input_text(self.DIALOG_INPUT_NAME, str(name))

    def fill_credit_code(self, credit_code):
        """填充统一社会信用代码（18位）"""
        logger.info("填充信用代码: %s", credit_code)
        self.input_text(self.DIALOG_INPUT_CREDIT_CODE, str(credit_code))

    def fill_contact(self, contact):
        """填充联系人"""
        logger.info("填充联系人: %s", contact)
        self.input_text(self.DIALOG_INPUT_CONTACT, str(contact))

    def fill_phone(self, phone):
        """填充联系电话"""
        logger.info("填充联系电话: %s", phone)
        self.input_text(self.DIALOG_INPUT_PHONE, str(phone))

    def fill_finance_contact(self, finance_contact):
        """填充财务联系人（非必填）"""
        logger.info("填充财务联系人: %s", finance_contact)
        self.input_text(self.DIALOG_INPUT_FINANCE_CONTACT, str(finance_contact))

    def fill_finance_phone(self, finance_phone):
        """填充财务电话（非必填）"""
        logger.info("填充财务电话: %s", finance_phone)
        self.input_text(self.DIALOG_INPUT_FINANCE_PHONE, str(finance_phone))

    def fill_address(self, address):
        """填充注册地址（Textarea, maxlength=500）"""
        logger.info("填充注册地址: %s", address[:50] if len(str(address)) > 50 else address)
        self.input_text(self.DIALOG_TEXTAREA_ADDRESS, str(address))

    def fill_remark(self, remark):
        """填充客户备注（Textarea, 非必填）"""
        logger.info("填充客户备注: %s", remark[:50] if len(str(remark)) > 50 else remark)
        self.input_text(self.DIALOG_TEXTAREA_REMARK, str(remark))

    def select_level(self, level_text):
        """选择客户等级（弹窗内下拉）

        Args:
            level_text: "战略客户" | "重要客户" | "一般客户"
        """
        logger.info("选择客户等级: %s", level_text)
        self._select_dialog_option("客户等级", level_text)

    def select_status(self, status_text):
        """选择合作状态（弹窗内下拉）

        Args:
            status_text: "合作中" | "终止合作"
        """
        logger.info("选择合作状态: %s", status_text)
        self._select_dialog_option("合作状态", status_text)

    # ==================================================================
    #  键盘导航选择 Select（绕过 Element Plus Teleport popper 问题）
    # ==================================================================
    def _select_by_keyboard(self, trigger_element, option_text):
        """用 ActionChains 全局键盘导航选择 Element Plus Select 选项

        Element Plus Select 内部 input 是 readonly，不能直接 send_keys。
        策略：ActionChains 点击 wrapper → 全局 send_keys 输入过滤 → Enter 选中。
        此方法完全绕过 Teleport popper 的渲染时序问题。

        Args:
            trigger_element: 已找到的 el-select 容器元素 (WebElement)
            option_text: 要选择的选项文本
        """
        # 点击 wrapper 打开下拉（ActionChains 模拟真实点击）
        wrapper = trigger_element.find_element(By.CSS_SELECTOR, '.el-select__wrapper')
        ActionChains(self.driver).move_to_element(wrapper).click().perform()
        self.wait_vue_stable()

        # ActionChains 发送全局键盘事件（输入过滤选项文本）
        ActionChains(self.driver).send_keys(option_text).perform()
        self.wait_vue_stable()  # 等待 Element Plus 过滤选项

        # 按 Enter 选择第一个匹配项
        ActionChains(self.driver).send_keys(Keys.ENTER).perform()
        self.wait_vue_stable()
        logger.info("键盘选择: %s", option_text)

    # ==================================================================
    #  弹窗内下拉选择
    # ==================================================================
    def _select_dialog_option(self, label_text, option_text):
        """在弹窗中选择下拉选项

        策略：
        1. 找到弹窗表单项中的 el-select wrapper → 点击打开下拉
        2. WebDriverWait 等待 body 下 popper 中目标选项变为可点击
        3. 点击选项
        """
        dialog = self._get_visible_dialog()
        if not dialog:
            raise Exception("未找到可见弹窗")

        # 查找表单项
        xp = f'.//div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"{label_text}")]]'
        form_item = dialog.find_element(By.XPATH, xp)

        # 点击 wrapper 打开下拉
        wrapper = form_item.find_element(By.CSS_SELECTOR, '.el-select__wrapper')
        wrapper.click()
        self.wait_vue_stable()

        # JS轮询：找到body下popper中匹配选项并强制点击（绕过Selenium可见性检查）
        js_click_option = f"""
        var deadline = Date.now() + 5000;
        while (Date.now() < deadline) {{
            var items = document.querySelectorAll(
                '.el-select-dropdown__item:not(.is-disabled)'
            );
            for (var i = 0; i < items.length; i++) {{
                if (items[i].textContent.indexOf('{option_text}') >= 0) {{
                    items[i].click();
                    return 'clicked';
                }}
            }}
        }}
        return 'timeout: ' + document.querySelectorAll('.el-select-dropdown__item').length + ' items';
        """
        result = self.driver.execute_script(js_click_option)
        if 'timeout' in str(result):
            raise Exception(f"下拉选项未找到: {option_text} — {result}")
        self.wait_vue_stable()
        logger.info("已选择: %s → %s", label_text, option_text)

    def click_save(self):
        """点击弹窗「保存」按钮，使用 BasePage 通用方法

        Returns:
            str: Toast 提示文本；超时返回空字符串
        """
        logger.info("点击弹窗保存按钮")
        self.click_dialog_save()
        return self.wait_for_toast_text()

    def click_cancel(self):
        """点击弹窗「取消」按钮，使用 BasePage 通用方法"""
        logger.info("点击弹窗取消按钮")
        self.click_dialog_cancel()

    # ==================================================================
    #  3. BUSINESS METHODS — 组合业务操作
    # ==================================================================
    def search_by_keyword(self, keyword):
        """按客户名称/编码搜索（最常用搜索）

        Args:
            keyword: 客户名称或编码
        """
        self.click_reset()
        self.input_search_keyword(keyword)
        self.click_search()

    def search_combined(self, keyword=None, level=None, status=None):
        """多条件组合搜索

        Args:
            keyword: 客户名称/编码
            level: 客户等级
            status: 合作状态
        """
        self.click_reset()
        if keyword is not None:
            self.input_search_keyword(keyword)
        if level is not None:
            self.select_search_level(level)
        if status is not None:
            self.select_search_status(status)
        self.click_search()

    def add_customer(self, *, code, name, credit_code, level,
                     contact, phone, address, status,
                     finance_contact=None, finance_phone=None, remark=None):
        """新增客户（完整流程：打开弹窗 → 填充 → 保存）

        Args:
            code: 客户编码（必填）
            name: 客户名称（必填）
            credit_code: 统一社会信用代码（必填，18位）
            level: 客户等级（必填，Select）
            contact: 联系人（必填）
            phone: 联系电话（必填）
            address: 注册地址（必填，Textarea）
            status: 合作状态（必填，Select）
            finance_contact: 财务联系人（非必填）
            finance_phone: 财务电话（非必填）
            remark: 客户备注（非必填，Textarea）

        Returns:
            str: Toast 提示文本
        """
        self.click_add()
        self.fill_code(code)
        self.fill_name(name)
        self.fill_credit_code(credit_code)
        self.select_level(level)
        self.fill_contact(contact)
        self.fill_phone(phone)
        if finance_contact:
            self.fill_finance_contact(finance_contact)
        if finance_phone:
            self.fill_finance_phone(finance_phone)
        self.fill_address(address)
        self.select_status(status)
        if remark:
            self.fill_remark(remark)
        return self.click_save()

    def edit_customer(self, row_identifier, **kwargs):
        """编辑客户（查找 → 点击编辑 → 修改字段 → 保存）

        Args:
            row_identifier: 行标识（客户编码或客户名称）
            **kwargs: 需要修改的字段，支持：
                code, name, credit_code, level, contact, phone,
                finance_contact, finance_phone, address, status, remark

        Returns:
            str: Toast 提示文本
        """
        self.click_edit(row_identifier)
        field_map = {
            "code": self.fill_code,
            "name": self.fill_name,
            "credit_code": self.fill_credit_code,
            "contact": self.fill_contact,
            "phone": self.fill_phone,
            "finance_contact": self.fill_finance_contact,
            "finance_phone": self.fill_finance_phone,
            "address": self.fill_address,
            "remark": self.fill_remark,
        }
        for field, value in kwargs.items():
            if field in field_map and value is not None:
                field_map[field](value)
            elif field == "level" and value is not None:
                self.select_level(value)
            elif field == "status" and value is not None:
                self.select_status(value)
        return self.click_save()

    def view_customer_detail(self, row_identifier):
        """查看客户详情

        Args:
            row_identifier: 行标识

        Returns:
            str: 详情弹窗文本内容
        """
        self.click_view(row_identifier)
        try:
            el = self.find_visible(self.DIALOG_BY_TITLE, timeout=5)
            return (el.text or "").strip()
        except TimeoutException:
            return ""

    def get_customer_level_tag_class(self, row_identifier):
        """获取客户等级标签的 CSS 类（用于验证等级样式）

        Args:
            row_identifier: 行标识

        Returns:
            str: CSS 类名
        """
        self._wait_table_ready()
        xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td[contains(normalize-space(.),"{row_identifier}")]]'
            f'/td[{self.COL_LEVEL}]//span'
        )
        try:
            el = self.find((By.XPATH, xpath), timeout=3)
            return el.get_attribute("class") or ""
        except TimeoutException:
            return ""

    def get_customer_status_tag_class(self, row_identifier):
        """获取合作状态标签的 CSS 类（用于验证状态样式）

        Args:
            row_identifier: 行标识

        Returns:
            str: CSS 类名
        """
        self._wait_table_ready()
        xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td[contains(normalize-space(.),"{row_identifier}")]]'
            f'/td[{self.COL_STATUS}]//span'
        )
        try:
            el = self.find((By.XPATH, xpath), timeout=3)
            return el.get_attribute("class") or ""
        except TimeoutException:
            return ""

    def is_terminated(self, row_identifier):
        """检查客户是否已终止合作

        Args:
            row_identifier: 行标识

        Returns:
            bool: 合作状态是否为「终止合作」
        """
        status = self.get_customer_status(row_identifier)
        return "终止" in status

    # ==================================================================
    #  2. PAGE METHODS — 表格数据读取
    # ==================================================================
    def get_table_headers(self):
        """JS提取表格表头（含重试，应对Element Plus异步渲染）"""
        for attempt in range(6):
            try:
                self._wait_table_ready()
            except:
                self._wait_loading_gone(timeout=2)
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
        """获取当前页可见数据行数

        Returns:
            int: 可见行数
        """
        self._wait_table_ready()
        rows = self.find_all(self.TABLE_ROWS_CSS)
        return sum(1 for r in rows if r.is_displayed())

    def get_total_count_text(self):
        """获取分页总条数文本

        Returns:
            str: 如 "共 3 条"
        """
        try:
            el = self.find_visible(self.PAGINATION_TOTAL, timeout=5)
            return (el.text or "").strip()
        except TimeoutException:
            return ""

    def get_total_count(self):
        """获取分页总条数

        Returns:
            int: 总条数，解析失败返回 0
        """
        import re
        text = self.get_total_count_text()
        nums = re.findall(r'\d+', text)
        return int(nums[-1]) if nums else 0

    def get_column_data(self, col_index):
        """获取指定列的所有数据（当前页）

        Args:
            col_index: 列索引（1-based）

        Returns:
            list[str]: 该列所有单元格文本
        """
        self._wait_table_ready()
        cells = self.find_all(
            (By.CSS_SELECTOR,
             f'.el-table__body-wrapper tbody tr.el-table__row '
             f'td:nth-child({col_index}) .cell')
        )
        if not cells:
            cells = self.find_all(
                (By.CSS_SELECTOR, f'tbody tr td:nth-child({col_index})')
            )
        return [(c.text or "").strip() for c in cells if c.is_displayed()]

    def is_row_present(self, identifier, timeout=10):
        """检查表格中是否存在指定标识的行

        轮询重试以处理 Vue 异步数据刷新竞态。

        Args:
            identifier: 客户编码或客户名称（部分匹配）
            timeout: 轮询超时秒数

        Returns:
            bool: 是否存在
        """
        self._wait_table_ready()
        xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'//td[contains(normalize-space(.),"{identifier}")]'
        )
        import time as _time
        deadline = _time.time() + timeout
        while _time.time() < deadline:
            try:
                if self.is_present((By.XPATH, xpath), timeout=2):
                    return True
            except Exception:
                pass
            _time.sleep(0.5)
        return False

    def get_customer_status(self, identifier):
        """获取指定行的合作状态文本

        Args:
            identifier: 行标识

        Returns:
            str: 合作状态文本
        """
        self._wait_table_ready()
        try:
            xpath = (
                f'//tr[contains(@class,"el-table__row")]'
                f'[.//td[contains(normalize-space(.),"{identifier}")]]'
                f'/td[{self.COL_STATUS}]'
            )
            el = self.find((By.XPATH, xpath), timeout=5)
            return (el.text or "").strip()
        except TimeoutException:
            return ""

    def get_first_row_data(self):
        """获取第一行数据（用于分页对比）

        Returns:
            str: 第一行所有单元格文本拼接
        """
        self._wait_table_ready()
        rows = self.find_all(self.TABLE_ROWS_CSS)
        visible = [r for r in rows if r.is_displayed()]
        return visible[0].text.strip() if visible else ""

    def get_row_by_code(self, code):
        """按客户编码精确查找行数据

        Args:
            code: 客户编码

        Returns:
            dict: {col_index: cell_text} 或空 dict
        """
        self._wait_table_ready()
        xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[td[{self.COL_CODE}]//div[normalize-space(.)="{code}"]]'
        )
        try:
            row = self.find((By.XPATH, xpath), timeout=5)
            cells = row.find_elements(By.TAG_NAME, "td")
            return {i + 1: c.text.strip() for i, c in enumerate(cells)}
        except TimeoutException:
            return {}

    # ==================================================================
    #  2. PAGE METHODS — 分页
    # ==================================================================
    def is_next_page_enabled(self):
        """检查是否有下一页"""
        try:
            self.find(self.PAGINATION_NEXT, timeout=2)
            return True
        except TimeoutException:
            return False

    def is_prev_page_enabled(self):
        """检查是否有上一页"""
        try:
            self.find(self.PAGINATION_PREV, timeout=2)
            return True
        except TimeoutException:
            return False

    def click_next_page(self):
        """翻到下一页"""
        logger.info("翻到下一页")
        self.click(self.PAGINATION_NEXT)
        self._wait_table_ready()

    def click_prev_page(self):
        """翻到上一页"""
        logger.info("翻到上一页")
        self.click(self.PAGINATION_PREV)
        self._wait_table_ready()

    # ==================================================================
    #  2. PAGE METHODS — 弹窗信息
    # ==================================================================
    def get_dialog_title(self):
        """获取当前可见弹窗的标题

        Returns:
            str: 弹窗标题，如 "新增客户"、"编辑客户"、"客户详情"
        """
        try:
            el = self.find_visible(
                (By.CSS_SELECTOR,
                 '.el-dialog:not([style*="display: none"]) .el-dialog__title'),
                timeout=5,
            )
            return (el.text or "").strip()
        except TimeoutException:
            return ""

    def is_dialog_open(self):
        """检查弹窗是否打开

        Returns:
            bool: 弹窗是否可见
        """
        try:
            el = self.find(
                (By.CSS_SELECTOR,
                 '.el-overlay-dialog:not([style*="display: none"]), '
                 '.el-dialog__wrapper:not([style*="display: none"])'),
                timeout=2,
            )
            return el.is_displayed()
        except TimeoutException:
            return False

    # ==================================================================
    #  4. WAIT METHODS — 等待策略
    # ==================================================================
    def _wait_page_ready(self, timeout=20):
        """等待页面完全就绪"""
        self._wait_loading_gone(timeout)
        self.wait_vue_stable()
        self._wait_loading_gone(timeout=2)  # keep-alive 标签切换需要额外布局时间
        self._wait_table_ready(timeout)

    def _wait_table_ready(self, timeout=15):
        """等待表格渲染完成

        策略：JS 轮询 thead th 出现且可见（比 WebDriverWait 更可靠，
        因为 Element Plus 表格在 Vue 异步渲染期间 DOM 已存在但 offsetHeight=0）
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                th_count = self.driver.execute_script(
                    "return document.querySelectorAll('.el-table__header-wrapper thead th').length || "
                    "       document.querySelectorAll('thead th').length;"
                )
                logger.debug("_wait_table_ready: thead th=%d", th_count)

                if th_count > 0:
                    has_visible = self.driver.execute_script(
                        "var ths = document.querySelectorAll('.el-table__header-wrapper thead th');"
                        "if (!ths.length) ths = document.querySelectorAll('thead th');"
                        "for (var i = 0; i < ths.length; i++) {"
                        "  if (ths[i].offsetHeight > 0 && ths[i].textContent.trim()) return true;"
                        "}"
                        "return false;"
                    )
                    if has_visible:
                        return True
                    else:
                        logger.debug("thead th 存在但 offsetHeight=0（动画中），继续等待...")
            except Exception as e:
                logger.debug("_wait_table_ready 轮询异常: %s", str(e)[:100])
            self._wait_loading_gone(timeout=0.5)

        logger.warning("表格表头未在 %ds 内变为可见", timeout)

    def _wait_dialog_ready(self, timeout=15):
        """等待弹窗完全打开（动画结束后可交互）

        关键：Element Plus Dialog 有过渡动画 + Teleport，按钮 JS click 后
        Vue 需要时间创建弹窗 DOM。等待策略：轮询 overlay，等待表单输入框就绪
        """
        logger.debug("等待弹窗打开...")
        # 轮询等待弹窗出现（比 WebDriverWait 更可靠）
        deadline = time.time() + timeout
        dialog_found = False
        while time.time() < deadline:
            try:
                el = self.find(
                    (By.CSS_SELECTOR, '.el-dialog:not([style*="display: none"])'),
                    timeout=1,
                )
                if el.is_displayed() and el.size['width'] > 0:
                    dialog_found = True
                    break
            except Exception:
                pass
            self._wait_loading_gone(timeout=0.5)
        if not dialog_found:
            raise TimeoutException(f"弹窗未在 {timeout}s 内出现")

        self.wait_vue_stable()
        # 等待表单输入框渲染完成
        deadline2 = time.time() + 10
        while time.time() < deadline2:
            try:
                el = self.find(self.DIALOG_INPUT_CODE, timeout=2)
                if el.is_displayed() and el.size['width'] > 0:
                    logger.debug("弹窗表单已就绪")
                    break
            except TimeoutException:
                pass
            self._wait_loading_gone(timeout=0.5)
        self.wait_vue_stable()

    def _wait_dropdown_ready(self, timeout=5):
        """等待 Element Plus Select 下拉面板通过 Teleport 挂载并可见

        关键：Select 下拉默认不在触发按钮的 DOM 子树中，
        点击后通过 Vue Teleport 挂载到 <body> 末尾
        """
        logger.debug("等待下拉面板渲染...")
        WebDriverWait(self.driver, timeout, poll_frequency=0.3).until(
            EC.visibility_of_element_located(self.DROPDOWN_PANEL)
        )
        # 额外等待选项列表渲染
        self.wait_vue_stable()

    # ==================================================================
    #  内部工具方法
    # ==================================================================
    def _click_select_trigger(self, trigger_locator):
        """点击 Element Plus Select 触发器

        封装点击逻辑：scroll → native click → JS click fallback
        """
        el = self.wait.until(EC.element_to_be_clickable(trigger_locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        self.wait_vue_stable()
        try:
            el.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", el)
        self.wait_vue_stable()

    def _click_dropdown_option(self, option_text):
        """在下拉面板中点击指定文本的选项

        Args:
            option_text: 选项显示文本
        """
        xpath = self.DROPDOWN_OPTION_BY_TEXT[1].format(text=option_text)
        option = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        self.driver.execute_script("arguments[0].click();", option)
        self.wait_vue_stable()
        # 等待下拉面板关闭
        try:
            WebDriverWait(self.driver, 3).until(
                EC.invisibility_of_element_located(self.DROPDOWN_PANEL)
            )
        except TimeoutException:
            # 如果下拉面板未自动关闭，按 Escape
            self.driver.execute_script("document.activeElement.blur();")

    def _click_row_action(self, row_identifier, action_text):
        """点击表格行内的操作按钮

        Args:
            row_identifier: 行标识文本（客户编码或客户名称）
            action_text: 按钮文本，如 "查看"、"编辑"、"资质维护"
        """
        self._wait_table_ready()
        # 注意：行内客户编码也是 is-link 按钮，因此必须通过 action_text 精准匹配
        xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td[contains(normalize-space(.),"{row_identifier}")]]'
            f'//button[contains(normalize-space(.),"{action_text}")]'
        )
        try:
            self.click((By.XPATH, xpath), timeout=5)
        except TimeoutException:
            # fallback: JS click
            el = self.find((By.XPATH, xpath), timeout=3)
            self.driver.execute_script("arguments[0].click();", el)
        self.wait_vue_stable()

    def _wait_loading_gone(self, timeout=15):
        """等待加载遮罩消失（覆盖 BasePage 方法，增加 Element Plus 特定策略）

        同时检查：.el-loading-mask 和 aria-busy 属性
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                # 检查 loading mask
                mask_count = self.driver.execute_script(
                    "return document.querySelectorAll('.el-loading-mask').length;"
                )
                # 检查表格是否标记为 busy
                busy = self.driver.execute_script(
                    "var t = document.querySelector('.el-table');"
                    "return t ? t.getAttribute('aria-busy') : null;"
                )
                if mask_count == 0 and busy != "true":
                    return True
                logger.debug("_wait_loading_gone: masks=%d, busy=%s", mask_count, busy)
            except Exception:
                pass
            self.wait_vue_stable()
        logger.warning("加载遮罩未在 %ds 内消失", timeout)
        return False
