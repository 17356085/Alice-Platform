"""销售订单页面 Page Object — 企业级

==== 页面概述 ====
  路径：销售管理 → 销售订单
  功能：记录每笔销售出库业务，关联客户与合同，记录销售量、车牌号等发货信息
  操作：新增、查看详情、多条件查询

==== 页面实际结构（2026-06-03 验证）====
  搜索区:
    [销售单号_____] [客户名称_____] [产品类型▾]
    [开始日期_____] 至 [结束日期_____]
    [查询] [重置]                    [新增销售]

  表格区（8列）:
    销售单号 | 客户名称 | 产品类型 | 销售量 | 车牌号 | 销售时间 | 关联合同 | 操作
    - 第1列销售单号本身是可点击的 el-button（链接样式）
    - 第3列产品类型使用 el-tag（LNG=primary, 焦油=warning）
    - 第8列操作包含"详情"按钮

  分页区:
    共 N 条 | 每页条数选择 | 上一页/下一页

==== 业务规则 ====
  1. 选择客户后，合同下拉框自动过滤为该客户的合同
  2. 销售量不能超过关联合同的剩余量（防超卖）
  3. 浮点数精度需保持一致

==== 定位策略 ====
  1. CSS_SELECTOR：语义属性（placeholder）> Element Plus 标准类
  2. 相对 XPath：仅用于文本内容匹配
  3. 禁止：绝对 XPath（/html/body/div[n]/...）、动态 ID、Scoped CSS

==== 风险点 ====
  1. 并发下单可能导致合同超卖
  2. 浮点数溢出或截断误差（如 0.0001t）
"""
import logging
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class SalesOrderPage(BasePage):
    """销售订单页面"""

    # ==================================================================
    #  路由
    # ==================================================================
    PAGE_ROUTE = "#/sales/order"

    # ==================================================================
    #  搜索区 — 输入框（CSS_SELECTOR: placeholder 精确匹配 — 已通过实际页面验证）
    # ==================================================================
    SEARCH_ORDER_NO_INPUT = (By.CSS_SELECTOR, 'input[placeholder="销售单号"]')
    SEARCH_CUSTOMER_INPUT = (By.CSS_SELECTOR, 'input[placeholder="客户名称"]')
    SEARCH_DATE_START = (By.CSS_SELECTOR, 'input[placeholder="开始日期"]')
    SEARCH_DATE_END = (By.CSS_SELECTOR, 'input[placeholder="结束日期"]')

    # ==================================================================
    #  搜索区 — el-select 下拉（XPath 文本匹配）
    # ==================================================================
    SELECT_PRODUCT_TYPE = (
        By.XPATH,
        '//div[contains(@class,"el-select")]'
        '[.//*[contains(@class,"el-select__placeholder") and contains(.,"产品类型")]]',
    )

    # ==================================================================
    #  搜索区 — 按钮（CSS_SELECTOR + XPath 双保险）
    # ==================================================================
    # CSS — 基础匹配
    BTN_SEARCH_CSS = (
        By.CSS_SELECTOR,
        '.el-button--primary',
    )
    BTN_RESET_CSS = (
        By.CSS_SELECTOR,
        'button.el-button:not(.el-button--primary)',
    )
    BTN_ADD_CSS = (
        By.CSS_SELECTOR,
        'button.el-button--primary',
    )

    # XPath — 文本匹配保底（已通过实际页面验证）
    BTN_SEARCH_XPATH = (
        By.XPATH,
        '//button[contains(@class,"el-button--primary")]'
        '//span[contains(normalize-space(.),"查询")]/parent::button',
    )
    BTN_RESET_XPATH = (
        By.XPATH,
        '//button[not(contains(@class,"el-button--primary"))]'
        '//span[contains(normalize-space(.),"重置")]/parent::button',
    )
    # 注意：「新增销售」按钮可能使用 el-button--success 而非 el-button--primary
    BTN_ADD_XPATH = (
        By.XPATH,
        '//button[contains(@class,"el-button")]'
        '//span[contains(normalize-space(.),"新增销售")]/parent::button',
    )
    BTN_ADD_XPATH_FALLBACK = (
        By.XPATH,
        '//button[contains(.,"新增销售")]',
    )

    # ==================================================================
    #  表格 — 列索引常量（1-based, 已通过实际页面验证）
    #
    #  | 1:销售单号 | 2:客户名称 | 3:产品类型 | 4:销售量 |
    #  | 5:车牌号   | 6:销售时间 | 7:关联合同 | 8:操作   |
    # ==================================================================
    COL_ORDER_NO    = 1   # 销售单号（本身是 clickable link）
    COL_CUSTOMER    = 2   # 客户名称
    COL_PRODUCT_TYPE = 3  # 产品类型（el-tag: primary=LNG, warning=焦油）
    COL_QUANTITY    = 4   # 销售量（含单位 t）
    COL_PLATE       = 5   # 车牌号
    COL_SALE_TIME   = 6   # 销售时间
    COL_CONTRACT    = 7   # 关联合同
    COL_OPERATIONS  = 8   # 操作（"详情"按钮）

    # ==================================================================
    #  表格 — 元素定位器（基类已提供 TABLE_ROWS, TABLE_EMPTY, TOTAL_COUNT 等）
    # ==================================================================
    TAG_IN_PRODUCT_COL = (By.CSS_SELECTOR, 'td:nth-child(3) .cell span.el-tag')

    # ==================================================================
    #  构造
    # ==================================================================
    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    # ==================================================================
    #  导航
    # ==================================================================
    def navigate(self):
        """通过侧边栏导航至销售订单页面"""
        logger.info("导航到 → 销售订单 (%s)", self.PAGE_ROUTE)
        self.navigate_to("销售管理", "销售订单")
        self._wait_page_ready()

    def _wait_page_ready(self, timeout=15):
        """等待页面渲染完成：遮罩消失 → Vue 稳定 → 表格就绪"""
        self._wait_loading_gone(timeout)
        self.wait_vue_stable()
        self._wait_loading_gone(timeout=0.5)
        self._wait_table_ready(timeout)

    # ==================================================================
    #  搜索区操作
    # ==================================================================
    def input_search_order_no(self, order_no):
        """输入销售单号搜索条件"""
        logger.info("搜索销售单号: %s", order_no)
        self.input_text(self.SEARCH_ORDER_NO_INPUT, order_no or "")

    def input_search_customer(self, customer):
        """输入客户名称搜索条件"""
        logger.info("搜索客户: %s", customer)
        self.input_text(self.SEARCH_CUSTOMER_INPUT, customer or "")

    def select_product_type(self, option_text):
        """选择产品类型下拉选项

        Args:
            option_text: 产品类型名称，如 "LNG"、"焦油"
        """
        logger.info("选择产品类型: %s", option_text)
        # 点击触发下拉
        trigger = self.find_clickable(self.SELECT_PRODUCT_TYPE)
        self._scroll_into_view(trigger)
        trigger.click()
        self._wait_loading_gone(timeout=0.4)
        self._select_option(option_text)
        self.wait_vue_stable()

    def input_search_date_start(self, date_str):
        """输入开始日期

        Args:
            date_str: 日期字符串，如 "2026-01-01"
        """
        logger.info("搜索开始日期: %s", date_str)
        self.input_text(self.SEARCH_DATE_START, date_str)

    def input_search_date_end(self, date_str):
        """输入结束日期

        Args:
            date_str: 日期字符串，如 "2026-06-30"
        """
        logger.info("搜索结束日期: %s", date_str)
        self.input_text(self.SEARCH_DATE_END, date_str)

    def click_search(self):
        """点击查询按钮（CSS_SELECTOR → XPath 保底）"""
        logger.info("点击查询按钮")
        try:
            self.click(self.BTN_SEARCH_CSS)
        except TimeoutException:
            self.click(self.BTN_SEARCH_XPATH)
        self._wait_table_ready()

    def click_reset(self):
        """点击重置按钮（CSS_SELECTOR → XPath 保底）"""
        logger.info("点击重置按钮")
        try:
            self.click(self.BTN_RESET_CSS)
        except TimeoutException:
            self.click(self.BTN_RESET_XPATH)
        self._wait_table_ready()

    # 向后兼容别名
    click_reset_search = click_reset

    def search(self, *, order_no=None, customer=None, product_type=None,
               date_start=None, date_end=None):
        """多条件组合搜索

        Args:
            order_no: 销售单号（精确匹配）
            customer: 客户名称（模糊匹配）
            product_type: 产品类型（下拉选择）
            date_start: 开始日期
            date_end: 结束日期
        """
        if order_no is not None:
            self.input_search_order_no(order_no)
        if customer is not None:
            self.input_search_customer(customer)
        if product_type is not None:
            self.select_product_type(product_type)
        if date_start is not None:
            self.input_search_date_start(date_start)
        if date_end is not None:
            self.input_search_date_end(date_end)
        self.click_search()

    # ==================================================================
    #  新增订单 弹窗操作
    # ==================================================================
    def click_add(self):
        """点击"新增销售"按钮，等待弹窗打开

        注意：该按钮可能使用 el-button--success 类，且可能因权限问题不可见。
        """
        logger.info("点击新增销售按钮")
        try:
            self.click(self.BTN_ADD_XPATH)
        except TimeoutException:
            try:
                self.click(self.BTN_ADD_XPATH_FALLBACK)
            except TimeoutException:
                try:
                    self.click(self.BTN_ADD_CSS)
                except TimeoutException:
                    # JS 保底：查找任意包含 "新增销售" 的按钮
                    self.driver.execute_script("""
                        var btns = document.querySelectorAll('button.el-button');
                        for (var i = 0; i < btns.length; i++) {
                            if (btns[i].textContent.includes('新增销售')) {
                                btns[i].scrollIntoView({block: 'center'});
                                btns[i].click();
                                return;
                            }
                        }
                    """)
        self.wait_dialog_open()
        self.wait_vue_stable()

    def click_view_by_name(self, identifier):
        """根据订单标识（单号/车牌号）点击"详情"按钮

        实际页面中，第1列销售单号本身也是可点击链接（el-button），
        但操作列的"详情"按钮是最明确的入口。

        Args:
            identifier: 用于定位行的文本（销售单号或车牌号）
        """
        logger.info("查看订单详情: %s", identifier)
        self.click_row_button(identifier, "详情")
        self.wait_dialog_open()

    # — 弹窗表单填充 —
    #  实际弹窗结构（2026-06-03 验证）：
    #    关联合同(Select, filterable)→客户名称/产品类型/单价自动带入
    #    销售量(吨) / 发货时间 / 车牌号 / 司机姓名（手动填写）
    def select_contract_in_dialog(self, contract_identifier=None, search_text=None):
        """在新增弹窗中选择关联合同（filterable Select）

        【关键发现】下拉选项显示格式为 "合同名称 - 客户名称"，不含合同编号。
        因此需要用客户名称（而非合同编号）来搜索过滤。

        用法:
          page.select_contract_in_dialog(search_text="贵州能源")  # 推荐：搜客户名
          page.select_contract_in_dialog(contract_identifier="HT...")  # 向后兼容

        Args:
            contract_identifier: 合同编号（向后兼容）
            search_text: 下拉搜索关键词（优先使用，如客户名称）
        """
        from selenium.webdriver.common.action_chains import ActionChains

        # 优先使用 search_text，否则用 contract_identifier
        filter_text = search_text or contract_identifier
        logger.info("选择关联合同，搜索: %s", filter_text)

        # ── 定位 + 打开下拉 ──
        item = None
        for attempt in range(3):
            try:
                item = self._get_dialog_form_item("关联合同")
                break
            except Exception:
                if attempt < 2:
                    self._wait_loading_gone(timeout=1.0)
        if not item:
            raise Exception("无法定位弹窗表单项: 关联合同")

        select_el = item.find_element(By.CSS_SELECTOR, '.el-select')
        select_input = select_el.find_element(By.CSS_SELECTOR, 'input')
        self._scroll_into_view(select_el)

        # ActionChains 点击 Select
        ActionChains(self.driver).move_to_element(select_el).click().perform()
        self._wait_loading_gone(timeout=0.3)

        # 输入搜索文本（客户名称，匹配 "合同名 - 客户名" 格式）
        select_input.clear()
        ActionChains(self.driver).click(select_input).perform()
        self._wait_loading_gone(timeout=0.1)
        for char in filter_text:
            select_input.send_keys(char)
        self._wait_loading_gone(timeout=1.5)

        # ── 点击第一个可用选项 ──
        try:
            option = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    '//div[contains(@class,"el-select-dropdown") and '
                    'not(contains(@style,"display: none"))]'
                    '//li[not(contains(@class,"is-disabled"))]',
                ))
            )
            ActionChains(self.driver).move_to_element(option).click().perform()
            logger.info("已选中合同选项")
            self._wait_loading_gone(timeout=0.5)
        except Exception:
            # 兜底：键盘确认
            try:
                select_input.send_keys(Keys.ARROW_DOWN)
                self._wait_loading_gone(timeout=0.1)
                select_input.send_keys(Keys.ENTER)
                self._wait_loading_gone(timeout=0.4)
            except Exception:
                pass

        # ── 点击弹窗标题关闭下拉并触发 blur ──
        try:
            dialog = self._get_visible_dialog()
            title_el = dialog.find_element(By.CSS_SELECTOR, '.el-dialog__title')
            ActionChains(self.driver).move_to_element(title_el).click().perform()
            self._wait_loading_gone(timeout=0.3)
        except Exception:
            pass

        self.wait_vue_stable()
        self._wait_loading_gone(timeout=0.3)

    # 向后兼容别名
    def select_customer(self, contract_identifier):
        """向后兼容：选择关联合同等同于原 select_customer 流程"""
        return self.select_contract_in_dialog(contract_identifier)

    def select_contract(self, contract_identifier):
        """向后兼容：选择关联合同"""
        return self.select_contract_in_dialog(contract_identifier)

    def input_order_quantity(self, quantity):
        """输入销售量(吨)"""
        logger.info("输入销售量: %s", quantity)
        self.fill_dialog_input("销售量(吨)", str(quantity))

    def input_vehicle_plate(self, plate):
        """输入车牌号"""
        logger.info("输入车牌号: %s", plate)
        self.fill_dialog_input("车牌号", plate)

    def input_delivery_date(self, date_str):
        """输入销售时间"""
        logger.info("输入销售时间: %s", date_str)
        self.fill_dialog_input("销售时间", date_str)

    def input_driver_name(self, driver_name):
        """输入司机姓名"""
        logger.info("输入司机姓名: %s", driver_name)
        self.fill_dialog_input("司机姓名", driver_name)

    def fill_order_form(self, *,
                        contract=None,
                        quantity=None,
                        plate=None,
                        delivery_date=None,
                        driver_name=None):
        """完整填充订单表单

        选择关联合同后，客户名称/产品类型/单价自动带入！

        Args:
            contract: 合同编号（下拉选择）
            quantity: 销售量(吨)
            plate: 车牌号
            delivery_date: 发货时间
            driver_name: 司机姓名（可选）
        """
        if contract is not None:
            self.select_contract_in_dialog(contract)
        if quantity is not None:
            self.input_order_quantity(quantity)
        if plate is not None:
            self.input_vehicle_plate(plate)
        if delivery_date is not None:
            self.input_delivery_date(delivery_date)
        if driver_name is not None:
            self.input_driver_name(driver_name)

    def click_save(self):
        """点击弹窗保存按钮并获取 Toast 消息

        Returns:
            str: Toast 提示文本
        """
        self.click_dialog_save()
        return self.wait_for_toast_text()

    def click_cancel(self):
        """点击弹窗取消按钮"""
        self.click_dialog_cancel()

    # ==================================================================
    #  业务规则 — 超卖防护
    # ==================================================================
    def try_oversell(self, customer_name, contract_name, oversized_qty):
        """尝试超出剩余数量下单

        预期：保存失败，返回错误提示

        Args:
            customer_name: 客户名称
            contract_name: 合同名称
            oversized_qty: 超过剩余量的销售数量

        Returns:
            tuple: (是否成功被拦截, 错误消息)
        """
        logger.info("超卖测试: 客户=%s, 合同=%s, 数量=%s",
                    customer_name, contract_name, oversized_qty)

        # 用客户名称搜索合同（下拉选项格式为 "合同名 - 客户名"）
        self.select_contract_in_dialog(search_text=customer_name[:6] if customer_name else None)
        self._wait_loading_gone(timeout=0.3)
        self.input_order_quantity(oversized_qty)
        self.input_vehicle_plate("超卖测试")
        self.input_delivery_date("2026-06-15 10:00:00")

        self.click_dialog_save()
        self._wait_loading_gone(timeout=0.5)

        # 检查表单错误
        errors = self.get_form_error()
        if errors:
            return True, str(errors)

        # 检查 Toast 错误
        toast = self.wait_for_toast_text()
        if toast and any(kw in toast for kw in
                         ("超出", "剩余", "不足", "失败", "超过", "不能", "无法")):
            return True, toast
        if toast and "成功" in toast:
            return False, f"超卖未被拦截，保存成功: {toast}"

        # 检查弹窗是否关闭（关闭=保存成功=超卖未被拦截）
        if not self.is_visible(self.DIALOG, timeout=2):
            return False, "弹窗已关闭，超卖可能未被拦截"

        return False, "无法判断超卖拦截结果"

    # ==================================================================
    #  业务规则 — 级联下拉校验
    # ==================================================================
    def get_available_contract_options(self):
        """获取当前合同下拉框中可见的选项列表

        用于验证：选择客户后，合同选项是否已过滤

        Returns:
            list[str]: 可见的合同选项文本列表
        """
        try:
            from base.base_page import BasePage
            options = self.driver.find_elements(
                By.CSS_SELECTOR,
                'body > .el-popper:not([style*="display: none"]) '
                '.el-select-dropdown__item:not(.is-disabled)',
            )
            return [(o.text or "").strip() for o in options if (o.text or "").strip()]
        except Exception:
            return []

    # ==================================================================
    #  表格操作
    # ==================================================================
    def get_table_headers(self):
        """JS提取表格表头（含重试，应对Element Plus异步渲染）"""
        for attempt in range(6):
            try:
                if hasattr(self, '_wait_table_ready'):
                    self._wait_table_ready()
            except Exception:
                pass
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
        """获取当前页可见数据行数"""
        self._wait_table_ready()
        rows = self.find_all(self.TABLE_ROWS)
        return sum(1 for r in rows if r.is_displayed())

    def get_total_count_text(self):
        """获取分页总条数文本

        Returns:
            str: 如 "共 4 条"
        """
        try:
            el = self.find_visible(self.TOTAL_COUNT, timeout=5)
            return (el.text or "").strip()
        except TimeoutException:
            return ""

    def get_total_count(self):
        """获取分页总条数（纯数字）

        Returns:
            int: 总条数，解析失败返回 0
        """
        text = self.get_total_count_text()
        nums = re.findall(r'\d+', text)
        return int(nums[-1]) if nums else 0

    def get_column_data(self, col_index):
        """获取指定列的所有数据（Vue 异步渲染安全）

        使用 JS 一次性提取所有单元格文本，避免 StaleElementReferenceException。

        Args:
            col_index: 列索引（1-based）

        Returns:
            list[str]: 该列所有单元格文本
        """
        self._wait_table_ready()
        try:
            # 方法1: JS 一次性提取（最稳定，避免 DOM 遍历中的 StaleElement）
            texts = self.driver.execute_script(f"""
                var cells = document.querySelectorAll(
                    '.el-table__body-wrapper tbody tr.el-table__row td:nth-child({col_index}) .cell'
                );
                if (cells.length === 0) {{
                    cells = document.querySelectorAll('tbody tr td:nth-child({col_index})');
                }}
                var result = [];
                cells.forEach(function(c) {{
                    var t = (c.textContent || '').trim();
                    if (t) result.push(t);
                }});
                return result;
            """)
            return texts if texts else []
        except Exception:
            # 方法2: Selenium 兜底（捕获 StaleElement 则跳过该行）
            results = []
            rows = self.find_all(self.TABLE_ROWS)
            for row in rows:
                try:
                    cell = row.find_element(
                        By.CSS_SELECTOR, f'td:nth-child({col_index}) .cell'
                    )
                    text = (cell.text or "").strip()
                    if text:
                        results.append(text)
                except Exception:
                    continue
            return results

    def get_product_tag_type(self, row_index):
        """获取指定行产品类型列的 el-tag 类型

        Args:
            row_index: 行索引（1-based）

        Returns:
            str: 'primary' | 'warning' | 'success' | 'info' | 'danger' | 'unknown'
        """
        try:
            rows = self.find_all(self.TABLE_ROWS)
            if row_index > len(rows):
                return 'unknown'
            row = rows[row_index - 1]
            tags = row.find_elements(By.CSS_SELECTOR, 'td:nth-child(3) .cell span.el-tag')
            if tags:
                tag_class = (tags[0].get_attribute("class") or "").split()
                # 优先匹配语义类型（primary/warning/success/info/danger），
                # 因为 Element Plus 可能同时有 el-tag--light, el-tag--plain 等修饰类
                semantic = {'el-tag--primary', 'el-tag--warning', 'el-tag--success',
                           'el-tag--info', 'el-tag--danger'}
                for cls in tag_class:
                    if cls in semantic:
                        return cls.replace('el-tag--', '')
                # 保底：返回第一个 el-tag--* 类
                for cls in tag_class:
                    if cls.startswith('el-tag--'):
                        return cls.replace('el-tag--', '')
            return 'unknown'
        except Exception:
            return 'unknown'

    def get_product_tag_text(self, row_index):
        """获取指定行产品类型列的 el-tag 文本

        Args:
            row_index: 行索引（1-based）

        Returns:
            str: Tag 显示文本，如 "LNG"、"焦油"
        """
        try:
            rows = self.find_all(self.TABLE_ROWS)
            if row_index > len(rows):
                return ''
            row = rows[row_index - 1]
            tags = row.find_elements(By.CSS_SELECTOR, 'td:nth-child(3) .cell span.el-tag')
            return (tags[0].text or "").strip() if tags else ''
        except Exception:
            return ''

    def is_order_present(self, identifier):
        """检查订单是否存在于当前表格

        Args:
            identifier: 销售单号或车牌号

        Returns:
            bool: 是否存在
        """
        self._wait_table_ready()
        try:
            xpath = (
                f'//tr[contains(@class,"el-table__row")]'
                f'//td[contains(normalize-space(.),"{identifier}")]'
            )
            return self.is_present((By.XPATH, xpath), timeout=3)
        except Exception:
            return False

    def click_detail_button(self, order_no):
        """通过销售单号点击行内的"详情"按钮

        注意：表格第一列（销售单号）也是 el-button，会干扰 XPath。
        必须限定到最后一列（操作列）的按钮。

        Args:
            order_no: 销售单号（用于定位行）
        """
        logger.info("查看详情: %s", order_no)
        # 限定：行内 → 最后一个td（操作列） → 按钮
        xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td[contains(normalize-space(.),"{order_no}")]]'
            f'//td[last()]//button[contains(.,"详情")]'
        )
        self.click((By.XPATH, xpath))
        self.wait_dialog_open()

    def get_first_row_data(self):
        """获取第一行数据（全部文本）"""
        self._wait_table_ready()
        rows = self.find_all(self.TABLE_ROWS)
        visible = [r for r in rows if r.is_displayed()]
        if visible:
            return visible[0].text.strip()
        return ""

    def get_detail_info(self):
        """获取详情弹窗中的全部文本内容

        Returns:
            str: 弹窗内所有文本
        """
        try:
            el = self.find_visible(self.DIALOG, timeout=5)
            return (el.text or "").strip()
        except TimeoutException:
            return ""

    # ==================================================================
    #  分页操作
    # ==================================================================
    def click_next_page(self):
        """点击下一页"""
        logger.info("点击下一页")
        self.click((By.CSS_SELECTOR, '.el-pagination .btn-next'))
        self._wait_table_ready()

    def click_prev_page(self):
        """点击上一页"""
        logger.info("点击上一页")
        self.click((By.CSS_SELECTOR, '.el-pagination .btn-prev'))
        self._wait_table_ready()

    def is_next_page_enabled(self):
        """检查下一页按钮是否可用"""
        try:
            self.find(
                (By.CSS_SELECTOR, '.el-pagination .btn-next:not([disabled])'),
                timeout=2,
            )
            return True
        except TimeoutException:
            return False

    def is_prev_page_enabled(self):
        """检查上一页按钮是否可用"""
        try:
            self.find(
                (By.CSS_SELECTOR, '.el-pagination .btn-prev:not([disabled])'),
                timeout=2,
            )
            return True
        except TimeoutException:
            return False

    # ==================================================================
    #  弹窗信息
    # ==================================================================
    def get_dialog_title(self):
        """获取当前可见弹窗标题"""
        try:
            el = self.find_visible(self.DIALOG_TITLE, timeout=5)
            return (el.text or "").strip()
        except TimeoutException:
            return ""

    # ==================================================================
    #  内部工具方法
    # ==================================================================
    def _wait_table_ready(self, timeout=15):
        """等待表格渲染完成 — 轮询检测 thead th 是否可见"""
        import time as _time
        deadline = _time.time() + timeout
        while _time.time() < deadline:
            try:
                th_count = self.driver.execute_script(
                    "return document.querySelectorAll('thead th').length;"
                )
                if th_count > 0:
                    has_visible = self.driver.execute_script(
                        "var ths = document.querySelectorAll('thead th');"
                        "for (var i = 0; i < ths.length; i++) {"
                        "  if (ths[i].offsetHeight > 0 && ths[i].textContent.trim()) return true;"
                        "}"
                        "return false;"
                    )
                    if has_visible:
                        return True
            except Exception as e:
                logger.debug("轮询异常: %s", str(e)[:100])
            self._wait_loading_gone(timeout=0.5)
        logger.warning("表格表头未在 %ds 内变为可见", timeout)
