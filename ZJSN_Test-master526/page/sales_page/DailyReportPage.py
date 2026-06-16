"""销售日报表页面 Page Object — 企业级

==== 页面概述 ====
  路径：销售管理 → 销售日报表  (#/sales/measurement)
  功能：按日统计分析LNG及总体销售数据，监控销售进度与订单频次
  操作：日期范围查询、汇总指标查看、明细下钻

==== 只读页面 ====
  本页面无增删改操作，仅有查询和查看功能。
  核心验证点：统计指标与明细数据的一致性。

==== 定位策略 ====
  1. CSS_SELECTOR：语义属性 > Element Plus 标准类
  2. 相对 XPath：仅用于文本内容匹配
  3. 禁止：绝对 XPath（/html/body/div[n]/...）

==== 风险点 ====
  1. 浮点数精度：报表合计与明细汇总可能差 0.0001
  2. 日期边界：查询无数据日期范围时的表现
"""
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage
from config import BASE_URL

logger = logging.getLogger(__name__)


class DailyReportPage(BasePage):
    """销售日报表页面"""

    # ==================================================================
    #  路由
    # ==================================================================
    PAGE_ROUTE = "#/sales/measurement"

    # ==================================================================
    #  1. LOCATORS — 日期查询区
    # ==================================================================
    START_DATE_INPUT = (
        By.CSS_SELECTOR,
        'input[placeholder*="开始日期"], '
        '.el-date-editor input[placeholder*="开始"]',
    )
    END_DATE_INPUT = (
        By.CSS_SELECTOR,
        'input[placeholder*="结束日期"], '
        '.el-date-editor input[placeholder*="结束"]',
    )
    # 日期范围选择器（Element Plus 双日期选择器）
    DATE_RANGE_PICKER = (
        By.CSS_SELECTOR,
        '.el-date-editor--daterange, '
        '.el-date-range-picker',
    )

    # 查询/重置按钮
    BTN_QUERY_CSS = (
        By.CSS_SELECTOR,
        '.search-form .el-button--primary, '
        '.el-form .el-button--primary',
    )
    BTN_RESET_CSS = (
        By.CSS_SELECTOR,
        '.search-form .el-button--default, '
        '.el-form .el-button:not(.el-button--primary)',
    )
    BTN_QUERY_XPATH = (
        By.XPATH,
        '//button[contains(@class,"el-button--primary")]'
        '//span[contains(normalize-space(.),"查询")]/parent::button',
    )
    BTN_RESET_XPATH = (
        By.XPATH,
        '//button[contains(@class,"el-button")]'
        '//span[contains(normalize-space(.),"重置")]/parent::button',
    )

    # ==================================================================
    #  1. LOCATORS — 汇总指标区
    # ==================================================================
    # 汇总卡片容器
    STAT_CARDS_CONTAINER = (
        By.CSS_SELECTOR,
        '.summary-wrapper, .stat-cards, .el-row.stat-row, '
        '.report-summary, [class*="stat-card"]',
    )
    # 单个指标项（Element Plus el-statistic 或自定义统计卡片）
    STAT_CARD_ITEMS = (
        By.CSS_SELECTOR,
        '.stat-card, .stat-item, .el-statistic, [class*="statistic-item"]',
    )
    # 指标标签和值 — A级定位
    STAT_CARD_LABEL = (
        By.CSS_SELECTOR,
        '.stat-card__label, .stat-item__label, .el-statistic__head',
    )
    STAT_CARD_VALUE = (
        By.CSS_SELECTOR,
        '.stat-card__value, .stat-item__value, .el-statistic__number',
    )
    # 保底：通过文本定位标签（XPath）
    STAT_LABEL_BY_TEXT = (
        By.XPATH,
        '//div[contains(@class,"stat-card")]'
        '//div[contains(@class,"label") and contains(normalize-space(.),"{text}")]',
    )
    # 保底：通过标签文本找兄弟值
    STAT_VALUE_BY_LABEL_TEXT = (
        By.XPATH,
        '//div[contains(@class,"stat-card")]'
        '[.//div[contains(@class,"label") and contains(normalize-space(.),"{text}")]]'
        '//div[contains(@class,"value")]',
    )

    # ==================================================================
    #  1. LOCATORS — 明细表格区
    # ==================================================================
    TABLE_CONTAINER = (
        By.CSS_SELECTOR,
        '.el-table, .el-table__body-wrapper',
    )
    TABLE_HEADER_CELLS = (
        By.CSS_SELECTOR,
        '.el-table__header-wrapper th .cell',
    )
    TABLE_HEADER_CELLS_XPATH = (
        By.XPATH,
        '//div[contains(@class,"el-table__header-wrapper")]//th//div[@class="cell"]',
    )
    TABLE_ROWS_CSS = (
        By.CSS_SELECTOR,
        '.el-table__body-wrapper tbody tr.el-table__row',
    )
    TABLE_EMPTY_TEXT = (
        By.CSS_SELECTOR,
        '.el-table__empty-text, .el-table-empty',
    )
    # 表格 loading 遮罩
    TABLE_LOADING_MASK = (
        By.CSS_SELECTOR,
        '.el-loading-mask, .el-table__body-wrapper .el-loading-mask',
    )
    # 明细按钮（CSS_SELECTOR + XPath 保底）
    DETAIL_BTN_CSS = (
        By.CSS_SELECTOR,
        'button.el-button--small.is-link, '
        'button.el-button.is-link',
    )
    DETAIL_BTN_XPATH = (
        By.XPATH,
        '//button[contains(@class,"el-button") '
        'and contains(normalize-space(.),"明细")]',
    )
    # 通过行内日期文本定位明细按钮
    DETAIL_BTN_BY_DATE = (
        By.XPATH,
        '//tr[contains(@class,"el-table__row")]'
        '[.//td[contains(normalize-space(.),"{date}")]]'
        '//button[contains(normalize-space(.),"明细")]',
    )
    # 展开的内层表格（兼容多种展开内容 DOM 结构）
    INNER_TABLE = (
        By.CSS_SELECTOR,
        '.el-table__expanded-cell, '
        '.el-table__expanded-cell .el-table, '
        'tr.el-table__row--level-1, '
        '.detail-table, '
        '.expanded-content, '
        '.expand-content, '
        '[class*="expanded"]',
    )
    # 日期文本、星期文本（表格内的自定义样式）
    DATE_CELL_FONT = (By.CSS_SELECTOR, 'span.font-medium')
    WEEKDAY_CELL = (By.CSS_SELECTOR, 'span.text-gray-500')

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
    PAGINATION_NEXT_DISABLED = (
        By.CSS_SELECTOR,
        '.el-pagination .btn-next[disabled]',
    )
    PAGINATION_PREV_DISABLED = (
        By.CSS_SELECTOR,
        '.el-pagination .btn-prev[disabled]',
    )
    # 每页条数选择器（Element Plus Select in Pagination）
    PAGE_SIZE_SELECT = (
        By.CSS_SELECTOR,
        '.el-pagination .el-select__wrapper, '
        '.el-pagination .el-select',
    )
    # 每页条数当前值
    PAGE_SIZE_CURRENT = (
        By.CSS_SELECTOR,
        '.el-pagination .el-select .el-select__selected-item, '
        '.el-pagination .el-select__wrapper .el-select__selected-item',
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
        """通过侧边栏导航至销售日报表页面"""
        logger.info("导航到 → 销售日报表 (%s)", self.PAGE_ROUTE)
        self.navigate_to("销售管理", "销售日报表")
        # 侧边栏导航后，Vue Router + 异步组件需要时间加载
        self._wait_loading_gone(timeout=2)
        self._wait_page_ready(timeout=30)  # 首次加载给予更长的等待时间

    def _wait_page_ready(self, timeout=15):
        """等待页面渲染完成

        先确保 document.readyState 为 complete，
        再等待 loading 遮罩消失 + Vue 稳定 + 表格可见。
        """
        # 确保 DOM 完全加载
        try:
            WebDriverWait(self.driver, min(timeout, 10)).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            logger.debug("document.readyState = complete")
        except TimeoutException:
            logger.warning("document.readyState 未在 10s 内变为 complete")

        self._wait_loading_gone(timeout)
        self.wait_vue_stable()
        self._wait_table_ready(timeout)

    # ==================================================================
    #  2. PAGE METHODS — 日期查询
    # ==================================================================
    def input_start_date(self, date_str):
        """输入开始日期

        Element Plus DatePicker 的 input 为 readonly，需使用 JS 设置值
        并派发 input 事件来触发 Vue v-model 更新。

        Args:
            date_str: 日期字符串，如 "2026-01-01"
        """
        logger.info("输入开始日期: %s", date_str)
        self._set_datepicker_value(self.START_DATE_INPUT, date_str)

    def input_end_date(self, date_str):
        """输入结束日期

        Args:
            date_str: 日期字符串，如 "2026-06-01"
        """
        logger.info("输入结束日期: %s", date_str)
        self._set_datepicker_value(self.END_DATE_INPUT, date_str)

    def _set_datepicker_value(self, locator, value, timeout=None):
        """为 Element Plus DatePicker 只读输入框设置值

        使用 JS 原生 value setter + 多事件派发，绕过 readonly 限制。
        同时触发父级 .el-date-editor 的 change 事件确保 Vue 组件模型同步。

        Args:
            locator: 输入框定位器
            value: 日期字符串
            timeout: 超时秒数
        """
        t = timeout or self.timeout
        el = self.find(locator, timeout=t)
        self._scroll_into_view(el)

        # 点击聚焦
        try:
            el.click()
        except Exception:
            self._js_click_el(el)
        self.wait_vue_stable()

        # JS 原生 setter + 完整事件链
        self.driver.execute_script("""
            var input = arguments[0];
            var value = arguments[1];

            // 用原生 setter 设置 value（绕过 readonly）
            var nativeSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            nativeSetter.call(input, value);

            // 派发完整事件链，触发 Vue v-model 和 Element Plus 组件更新
            input.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
            input.dispatchEvent(new Event('change', { bubbles: true, composed: true }));

            // 也触发父级 .el-date-editor 的 change（Element Plus 在父级监听）
            var editor = input.closest('.el-date-editor');
            if (editor) {
                editor.dispatchEvent(new Event('change', { bubbles: true }));
                editor.dispatchEvent(new Event('input', { bubbles: true }));
            }

            // 触发 Element Plus 内部的 focusout
            input.dispatchEvent(new FocusEvent('focusout', { bubbles: true }));
        """, el, value)

        self.wait_vue_stable()
        # 按 ESC 关闭可能弹出的日期面板
        try:
            from selenium.webdriver.common.keys import Keys
            el.send_keys(Keys.ESCAPE)
        except Exception:
            pass
        self.wait_vue_stable()

    def _set_date_range_via_input(self, start_date, end_date):
        """通过 Tab 导航设置日期范围选择器的两个输入值

        这是最可靠的方式：模拟用户通过 Tab 键在开始/结束输入框之间切换，
        完整触发 Element Plus DatePicker range 的 Vue 事件链。

        Args:
            start_date: 开始日期
            end_date: 结束日期
        """
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains

        # 点击开始日期输入框
        start_el = self.find_clickable(self.START_DATE_INPUT)
        self._scroll_into_view(start_el)

        actions = ActionChains(self.driver)
        # 清空并输入开始日期
        actions.click(start_el)
        actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL)
        actions.send_keys(Keys.DELETE)
        actions.send_keys(start_date)
        actions.pause(0.3)
        # Tab 到结束日期
        actions.send_keys(Keys.TAB)
        actions.pause(0.3)
        # 清空并输入结束日期
        actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL)
        actions.send_keys(Keys.DELETE)
        actions.send_keys(end_date)
        actions.pause(0.3)
        # Enter 确认
        actions.send_keys(Keys.ENTER)
        actions.pause(0.3)
        actions.perform()

        # 派发 change 事件确保 Vue 模型同步
        end_el = self.find(self.END_DATE_INPUT, timeout=3)
        self.driver.execute_script("""
            var el = arguments[0];
            el.dispatchEvent(new Event('change', { bubbles: true }));
        """, end_el)

        self.wait_vue_stable()

    def click_query(self):
        """点击查询按钮，等待数据刷新"""
        logger.info("点击查询按钮")
        # 点击前显式等待 loading 遮罩消失，防止 ElementClickInterceptedException
        self._wait_loading_gone(timeout=5)
        try:
            self.click(self.BTN_QUERY_CSS)
        except TimeoutException:
            self.click(self.BTN_QUERY_XPATH)
        self._wait_table_ready()

    def click_reset(self):
        """点击重置按钮，清空所有筛选条件

        注意：重置只清空表单字段，可能不触发表格重载。
        因此在点击前等待 loading 遮罩消失，点击后仅等待 Vue 稳定。
        """
        logger.info("点击重置按钮")
        # 点击前显式等待 loading 遮罩消失，防止被拦截
        self._wait_loading_gone(timeout=5)
        try:
            self.click(self.BTN_RESET_CSS)
        except TimeoutException:
            self.click(self.BTN_RESET_XPATH)
        # 重置可能不触发数据刷新，只等待遮罩消失和Vue稳定
        self._wait_loading_gone(timeout=5)
        self.wait_vue_stable()

    def query_date_range(self, start_date, end_date):
        """按日期范围查询（完整流程）

        使用 JS 原生 setter 设置日期值并派发事件触发 Vue 更新。

        Args:
            start_date: 开始日期
            end_date: 结束日期
        """
        logger.info("设置日期范围并查询: %s ~ %s", start_date, end_date)
        self.input_start_date(start_date)
        self.input_end_date(end_date)
        self.click_query()

    def get_start_date(self):
        """获取开始日期输入框当前值（兼容 readonly DatePicker）"""
        try:
            el = self.find(self.START_DATE_INPUT, timeout=3)
            # JS 读取实际 value 属性（get_attribute 可能返回缓存值）
            val = self.driver.execute_script(
                "return arguments[0].value;", el
            )
            return (val or "").strip()
        except TimeoutException:
            return ""

    def get_end_date(self):
        """获取结束日期输入框当前值（兼容 readonly DatePicker）"""
        try:
            el = self.find(self.END_DATE_INPUT, timeout=3)
            val = self.driver.execute_script(
                "return arguments[0].value;", el
            )
            return (val or "").strip()
        except TimeoutException:
            return ""

    # ==================================================================
    #  3. BUSINESS METHODS — 汇总指标
    # ==================================================================
    def get_summary_metrics(self):
        """获取顶部汇总指标数据

        遍历所有统计卡片，通过 label + value CSS 定位提取。

        Returns:
            dict: {指标名称: 数值文本}，如 {"LNG销售总量": "15 t", "订单数": "4 单"}
        """
        self._wait_table_ready()
        metrics = {}
        try:
            labels = self.find_all(self.STAT_CARD_LABEL)
            values = self.find_all(self.STAT_CARD_VALUE)
            for i, lbl in enumerate(labels):
                if not lbl.is_displayed():
                    continue
                label_text = (lbl.text or "").strip()
                val_text = (values[i].text or "").strip() if i < len(values) else ""
                if label_text:
                    metrics[label_text] = val_text
        except Exception:
            pass

        # 如果 CSS 定位为空，尝试遍历卡片容器
        if not metrics:
            try:
                items = self.find_all(self.STAT_CARD_ITEMS)
                for item in items:
                    if not item.is_displayed():
                        continue
                    text = (item.text or "").strip()
                    if text:
                        lines = text.split('\n')
                        if len(lines) >= 2:
                            metrics[lines[0].strip()] = lines[1].strip()
            except Exception as e:
                logger.warning("获取汇总指标失败: %s", e)
        return metrics

    def get_summary_value(self, metric_name):
        """获取指定汇总指标的值

        Args:
            metric_name: 指标名称（支持部分匹配），如 "LNG销售总量"、"合计销售量"、"订单数"

        Returns:
            str: 指标值文本，未找到返回空字符串
        """
        # 策略1：通过标签文本定位兄弟值（XPath）
        try:
            xpath = self.STAT_VALUE_BY_LABEL_TEXT[1].format(text=metric_name)
            el = self.find_visible((By.XPATH, xpath), timeout=3)
            return (el.text or "").strip()
        except TimeoutException:
            pass

        # 策略2：从 metrics dict 中匹配
        metrics = self.get_summary_metrics()
        for key, val in metrics.items():
            if metric_name in key:
                return val
        return ""

    def get_summary_numeric_value(self, metric_name):
        """获取指定汇总指标的数值（解析为 float）

        Args:
            metric_name: 指标名称

        Returns:
            float | None: 数值，解析失败返回 None
        """
        import re
        val_text = self.get_summary_value(metric_name)
        if not val_text:
            return None
        # 提取数字（支持千分位逗号和可选单位后缀，如 "25.0001 t"）
        nums = re.findall(r'[\d,]+\.?\d*', val_text.replace(',', ''))
        if nums:
            try:
                return float(nums[0].replace(',', ''))
            except ValueError:
                pass
        return None

    def wait_summary_metrics_refresh(self, old_metrics, timeout=10):
        """等待汇总指标刷新（用于查询后断言前）

        Args:
            old_metrics: 旧的指标字典
            timeout: 超时秒数
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            current = self.get_summary_metrics()
            if current and current != old_metrics:
                return current
            self._wait_loading_gone(timeout=1)
        logger.warning("汇总指标未在 %ds 内刷新", timeout)
        return self.get_summary_metrics()

    # ==================================================================
    #  3. BUSINESS METHODS — 明细表格
    # ==================================================================
    def get_table_headers(self):
        """JS提取表格表头（含重试，应对Element Plus异步渲染）"""
        for attempt in range(6):
            try:
                self._wait_table_ready()
            except Exception:
                self._wait_table_ready()
            self.wait_vue_stable()
            headers = self.driver.execute_script("""
                return Array.from(
                    document.querySelectorAll('.el-table__header-wrapper th .cell')
                ).map(function(el) { return el.textContent.trim(); }).filter(Boolean);
            """)
            if headers and len(headers) >= 3:
                return headers
            self._wait_table_ready()
        return []
    def _get_column_index(self, header_text):
        """根据表头文本获取列索引（1-based）

        用于跨方法定位列号，避免硬编码索引。

        Args:
            header_text: 表头文本，支持部分匹配（如 "LNG" 匹配 "LNG销售量(吨)"）

        Returns:
            int | None: 列索引，未找到返回 None
        """
        headers = self.get_table_headers()
        for idx, h in enumerate(headers, start=1):
            if header_text in h:
                return idx
        return None

    def get_table_row_count(self):
        """获取明细表格当前页行数"""
        self._wait_table_ready()
        rows = self.find_all(self.TABLE_ROWS_CSS)
        return sum(1 for r in rows if r.is_displayed())

    def get_table_empty_text(self):
        """获取表格空数据提示文本"""
        self._wait_table_ready()
        try:
            el = self.find_visible(self.TABLE_EMPTY_TEXT, timeout=3)
            return (el.text or "").strip()
        except TimeoutException:
            return ""

    def get_column_data(self, col_index):
        """获取明细表格指定列数据

        Args:
            col_index: 列索引（1-based）

        Returns:
            list[str]: 该列所有可见单元格文本
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

    def get_row_data(self, row_index):
        """获取指定行的所有列数据（1-based）

        Returns:
            list[str]: 该行所有单元格文本
        """
        self._wait_table_ready()
        rows = self.find_all(self.TABLE_ROWS_CSS)
        visible = [r for r in rows if r.is_displayed()]
        if row_index > len(visible):
            return []
        cells = visible[row_index - 1].find_elements(By.TAG_NAME, "td")
        return [c.text.strip() for c in cells]

    def get_row_by_date(self, date_str):
        """通过日期文本定位表格行

        Args:
            date_str: 日期字符串，如 "2026-05-29"

        Returns:
            WebElement | None: 匹配的 tr 元素
        """
        self._wait_table_ready()
        try:
            return self.find(
                (By.XPATH,
                 f'//tr[contains(@class,"el-table__row")]'
                 f'//td[contains(normalize-space(.),"{date_str}")]'
                 f'/parent::tr'),
                timeout=5,
            )
        except TimeoutException:
            return None

    def click_detail_button(self, date_str):
        """点击指定日期行的「明细」按钮

        Args:
            date_str: 日期字符串，如 "2026-05-29"

        Returns:
            bool: 是否成功点击
        """
        logger.info("点击 %s 行的明细按钮", date_str)
        try:
            xpath = self.DETAIL_BTN_BY_DATE[1].format(date=date_str)
            self.click((By.XPATH, xpath))
            self.wait_vue_stable()
            return True
        except TimeoutException:
            logger.warning("未找到 %s 行的明细按钮", date_str)
            return False

    def expand_detail_row(self, row_index=1):
        """展开指定行的明细（下钻至具体订单）

        Args:
            row_index: 行号（1-based），默认展开第一行

        Returns:
            bool: 是否成功展开
        """
        self._wait_table_ready()
        rows = self.find_all(self.TABLE_ROWS_CSS)
        visible = [r for r in rows if r.is_displayed()]
        if row_index > len(visible):
            return False

        row = visible[row_index - 1]
        try:
            # 找行内的展开/详情按钮
            expand_btn = row.find_element(
                By.XPATH,
                './/button[contains(normalize-space(.),"详情") or '
                'contains(normalize-space(.),"查看") or '
                'contains(normalize-space(.),"明细")]'
            )
            self._js_click_el(expand_btn)
            self.wait_vue_stable()
            return True
        except Exception:
            # 可能直接点击行就能展开
            try:
                self._js_click_el(row)
                self.wait_vue_stable()
                return True
            except Exception:
                return False

    def get_expanded_detail_data(self):
        """获取展开后的内层明细数据

        使用轮询等待异步数据加载：点击明细后数据可能通过接口异步返回，
        轮询检测展开区域文本直到非空或超时。
        如果标准展开区域为空，回退到读取整个表格 body 文本（
        某些 Element Plus 版本展开内容直接追加到 tbody 中）。

        Returns:
            str: 展开区域的所有文本，超时或未展开返回空
        """
        deadline = time.time() + 5
        last_text = ""
        while time.time() < deadline:
            try:
                inner = self.find_visible(self.INNER_TABLE, timeout=2)
                text = (inner.text or "").strip()
                if text:
                    return text
                last_text = text
            except TimeoutException:
                pass

            # 回退：检查是否展开了新的行（el-table__row--expanded）
            try:
                expanded_rows = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    'tr.el-table__row--expanded, '
                    'tr[class*="expanded"], '
                    '.el-table__expanded-cell',
                )
                for row in expanded_rows:
                    if row.is_displayed():
                        row_text = (row.text or "").strip()
                        if row_text and len(row_text) > len(last_text):
                            return row_text
            except Exception:
                pass

            self._wait_loading_gone(timeout=1)

        if last_text == "":
            logger.debug("展开区域内容在5s内未变为非空（数据可能为空或异步加载较慢）")
        return last_text

    def verify_dates_in_range(self, start_date, end_date):
        """验证表格中所有日期在查询范围内（用于查询结果断言）

        Args:
            start_date: 开始日期 "YYYY-MM-DD"
            end_date: 结束日期 "YYYY-MM-DD"

        Returns:
            tuple: (all_in_range: bool, out_of_range_dates: list[str])
        """
        import re
        date_col = self.get_column_data(1)
        out_of_range = []
        for cell_text in date_col:
            # 提取 "2026-05-29" 部分
            match = re.search(r'(\d{4}-\d{2}-\d{2})', cell_text)
            if match:
                d = match.group(1)
                if d < start_date or d > end_date:
                    out_of_range.append(d)
        return len(out_of_range) == 0, out_of_range

    # ==================================================================
    #  3. BUSINESS METHODS — 数据一致性校验
    # ==================================================================
    def sum_detail_column(self, col_index):
        """对明细表格指定列求和（用于与汇总指标对比）

        Args:
            col_index: 列索引（1-based）

        Returns:
            float: 列合计值
        """
        data = self.get_column_data(col_index)
        total = 0.0
        import re
        for val in data:
            nums = re.findall(r'[\d,]+\.?\d*', val.replace(',', ''))
            if nums:
                try:
                    total += float(nums[0].replace(',', ''))
                except ValueError:
                    pass
        return total

    def sum_detail_column_by_header(self, header_text):
        """按表头名称对明细列求和

        Args:
            header_text: 表头文本（支持部分匹配），如 "LNG"、"合计"、"订单数"

        Returns:
            float: 列合计值
        """
        idx = self._get_column_index(header_text)
        if idx is None:
            logger.warning("未找到列: %s", header_text)
            return 0.0
        return self.sum_detail_column(idx)

    def verify_stat_vs_table(self, stat_name, column_header, tolerance=0.001):
        """验证统计卡片值与表格列合计一致（核心交叉验证）

        Args:
            stat_name: 统计卡片指标名（如 "LNG销售总量"）
            column_header: 表格列表头关键词（如 "LNG"）
            tolerance: 允许的浮点偏差

        Returns:
            tuple: (is_match: bool, stat_value: float, table_sum: float, diff: float)
        """
        stat_val = self.get_summary_numeric_value(stat_name)
        table_sum = self.sum_detail_column_by_header(column_header)

        if stat_val is None:
            logger.warning("统计指标 [%s] 无值", stat_name)
            return False, 0, table_sum, 0

        diff = abs(stat_val - table_sum)
        is_match = diff <= tolerance
        if not is_match:
            logger.warning(
                "数据不一致: 统计[%s]=%s, 表格[%s]=%s, 偏差=%s",
                stat_name, stat_val, column_header, table_sum, diff,
            )
        return is_match, stat_val, table_sum, diff

    # ==================================================================
    #  2. PAGE METHODS — 分页
    # ==================================================================
    def get_total_count_text(self):
        """获取分页总条数文本（如 "共 2 条"）"""
        try:
            el = self.find_visible(self.PAGINATION_TOTAL, timeout=5)
            return (el.text or "").strip()
        except TimeoutException:
            return ""

    def get_total_count(self):
        """获取分页总条数（数字）"""
        import re
        text = self.get_total_count_text()
        nums = re.findall(r'\d+', text)
        return int(nums[-1]) if nums else 0

    def get_current_page_size(self):
        """获取当前每页条数

        Returns:
            str: 如 "10条/页"
        """
        try:
            el = self.find_visible(self.PAGE_SIZE_CURRENT, timeout=3)
            return (el.text or "").strip()
        except TimeoutException:
            return ""

    def select_page_size(self, size_text, timeout=None):
        """切换每页条数

        处理 Element Plus Select 的 Teleport + 下拉面板。

        Args:
            size_text: 每页条数文本，如 "10条/页"、"20条/页"
            timeout: 超时秒数
        """
        t = timeout or self.timeout
        logger.info("切换每页条数: %s", size_text)

        # 点击分页器中的 Select 触发器
        try:
            trigger = self.find_clickable(self.PAGE_SIZE_SELECT, timeout=t)
            self._scroll_into_view(trigger)
            trigger.click()
        except Exception:
            self.js_click(self.PAGE_SIZE_SELECT, timeout=t)
        self.wait_vue_stable()

        # 等待下拉面板可见（Teleport 到 body 下）
        self._wait_dropdown_visible(t)

        # 点击目标选项
        self._select_option(size_text, timeout=t)
        self.wait_vue_stable()
        self._wait_table_ready()

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
        """翻到下一页，等待数据刷新"""
        logger.info("翻到下一页")
        self.click(self.PAGINATION_NEXT)
        self._wait_table_ready()

    def click_prev_page(self):
        """翻到上一页，等待数据刷新"""
        logger.info("翻到上一页")
        self.click(self.PAGINATION_PREV)
        self._wait_table_ready()

    # ==================================================================
    #  4. WAIT METHODS
    # ==================================================================
    def _wait_table_ready(self, timeout=15):
        """等待表格渲染完成（JS 轮询）

        检测条件（按优先级）：
        0. document.readyState === 'complete'（页面 DOM 完全加载）
        1. thead th 存在且 offsetHeight > 0（Vue 重新渲染后可见）
        2. tbody 存在（数据行/空提示）
        3. loading 遮罩消失
        4. Vue transition 动画完成（offsetHeight 稳定）
        """
        deadline = time.time() + timeout

        # 先确保 document.readyState 为 complete（首次渲染必须）
        ready_checked = False
        while time.time() < deadline:
            try:
                ready_state = self.driver.execute_script("return document.readyState;")
                if ready_state == "complete":
                    if not ready_checked:
                        logger.debug("document.readyState = complete")
                        ready_checked = True
                    break
                logger.debug("document.readyState = %s, 等待...", ready_state)
            except Exception:
                pass
            self._wait_loading_gone(timeout=1)

        while time.time() < deadline:
            try:
                th_count = self.driver.execute_script(
                    "return document.querySelectorAll('.el-table__header-wrapper thead th').length || "
                    "       document.querySelectorAll('thead th').length;"
                )
                body_count = self.driver.execute_script(
                    "return document.querySelectorAll('tbody').length;"
                )
                # 检查 loading 遮罩
                mask_visible = self.driver.execute_script(
                    "var m = document.querySelector('.el-loading-mask');"
                    "return m ? (m.offsetHeight > 0) : false;"
                )
                logger.debug(
                    "_wait_table_ready: thead th=%d, tbody=%d, mask=%s",
                    th_count, body_count, mask_visible,
                )

                if mask_visible:
                    self._wait_loading_gone(timeout=1)
                    continue

                if th_count > 0 and body_count > 0:
                    # 等待 Vue transition 动画结束：连续 2 次 offsetHeight 稳定
                    stable = 0
                    while time.time() < deadline and stable < 2:
                        has_visible = self.driver.execute_script(
                            "var ths = document.querySelectorAll('.el-table__header-wrapper thead th');"
                            "if (!ths.length) ths = document.querySelectorAll('thead th');"
                            "for (var i = 0; i < ths.length; i++) {"
                            "  if (ths[i].offsetHeight > 0 && ths[i].textContent.trim()) return 'visible';"
                            "}"
                            "return 'hidden';"
                        )
                        if has_visible == "visible":
                            stable += 1
                            if stable >= 2:
                                return True
                        else:
                            stable = 0
                            logger.debug("thead th offsetHeight=0（动画中），等待稳定...")
                        self._wait_loading_gone(timeout=1)
                    if stable >= 2:
                        return True
                elif body_count > 0:
                    # 非标准表格（无 thead），直接认为就绪
                    return True
            except Exception as e:
                logger.debug("_wait_table_ready 轮询异常: %s", str(e)[:100])
            self._wait_loading_gone(timeout=1)

        logger.warning("表格未在 %ds 内变为可见", timeout)

    def _wait_date_picker_panel(self, timeout=5):
        """等待 ElementDatePicker 面板在 body 下可见

        Returns:
            WebElement | None: 面板元素
        """
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((
                    By.CSS_SELECTOR,
                    '.el-picker-panel.el-date-range-picker:not([style*="display: none"])',
                ))
            )
        except TimeoutException:
            logger.debug("日期面板未在 %ds 内可见", timeout)
            return None

    def _wait_dropdown_visible(self, timeout=5):
        """等待 Element Plus 下拉面板在 body 下可见（Teleport 渲染）"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                dropdowns = self.driver.find_elements(
                    By.XPATH,
                    '//div[contains(@class,"el-select-dropdown") '
                    'and not(contains(@style,"display: none"))]',
                )
                for dd in dropdowns:
                    if dd.is_displayed():
                        return True
            except Exception:
                pass
            self._wait_loading_gone(timeout=1)
        logger.debug("下拉面板未在 %ds 内可见", timeout)
        return False

    def _wait_loading_gone(self, timeout=15):
        """等待加载遮罩消失"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                mask_count = self.driver.execute_script(
                    "return document.querySelectorAll('.el-loading-mask').length;"
                )
                if mask_count == 0:
                    return True
                logger.debug("_wait_loading_gone: masks=%d", mask_count)
            except Exception:
                pass
            self.wait_vue_stable()
        logger.warning("加载遮罩未在 %ds 内消失", timeout)
        return False

    def _wait_interceptor_gone(self, timeout=5):
        """等待 Element Plus 遮挡元素（loading overlay / v-modal）消失"""
        end = time.time() + timeout
        while time.time() < end:
            interceptors = self.driver.find_elements(
                By.CSS_SELECTOR,
                '.el-loading-mask, .el-loading-spinner, '
                '.el-overlay:not([style*="display: none"]), '
                '.v-modal',
            )
            visible = any(
                (el.is_displayed() if hasattr(el, 'is_displayed') else True)
                for el in interceptors
            )
            if not visible:
                return True
            self.wait_vue_stable()
        return False
