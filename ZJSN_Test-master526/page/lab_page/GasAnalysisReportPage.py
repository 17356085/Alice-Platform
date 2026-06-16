"""气体分析报告单页面 Page Object — 企业级

==== 页面概述 ====
  路径：化验室取样 → 气体分析报告单
  功能：查看各取样位置的气体分析数据，支持日期筛选、新增报告单、导出

==== 定位策略 ====
  1. CSS_SELECTOR：语义属性 > Element Plus 标准类
  2. 相对 XPath：仅用于文本内容匹配
  3. 禁止：绝对路径 XPath（从根节点 html body 逐层定位）
"""
import logging
import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage
from config import BASE_URL, TIMEOUT_CONFIG

logger = logging.getLogger(__name__)


class GasAnalysisReportPage(BasePage):
    """气体分析报告单页面"""

    # ==================================================================
    #  侧边栏导航（相对 XPath — 文本匹配，CSS 无法实现）
    #  补充：Kimi 识别出菜单项使用 <a href="#/lab/gas/report">，CSS 可直接定位
    # ==================================================================
    SIDEBAR_SUBMENU = (
        By.XPATH,
        '//span[normalize-space(.)="{text}"]',
    )
    SIDEBAR_MENU_LINK = (
        By.CSS_SELECTOR,
        'a[href="{route}"]',
    )

    # ==================================================================
    #  取样位置标签栏 — 自定义 Tab 组件
    #  说明：非标准 Element Plus el-tabs，是项目自定义的标签样式
    #        蓝色下划线标识当前选中项
    # ==================================================================
    # 所有取样位置标签（相对 XPath，按文本匹配）
    LOCATION_TAB = (
        By.XPATH,
        '//*[contains(normalize-space(.),"{text}") and not(ancestor::table)]'
        '[not(ancestor::nav) and not(ancestor::ul[contains(@class,"el-menu")])]',
    )
    # 更精确的定位：在标签栏容器内
    LOCATION_TAB_IN_BAR = (
        By.XPATH,
        '//div[contains(@class,"tab") or contains(@class,"tag")]'
        '//*[contains(normalize-space(.),"{text}")]',
    )
    # 当前选中的取样位置（蓝色下划线标识）
    LOCATION_TAB_ACTIVE = (
        By.CSS_SELECTOR,
        '.el-tabs__item.is-active, [class*="tab"][class*="active"], '
        '[class*="tag"][class*="active"]',
    )

    # ==================================================================
    #  搜索区
    # ==================================================================
    # 日期范围选择器
    START_DATE_INPUT = (
        By.CSS_SELECTOR,
        'input[placeholder*="开始日期"]',
    )
    END_DATE_INPUT = (
        By.CSS_SELECTOR,
        'input[placeholder*="结束日期"]',
    )
    # 日期选择器触发图标
    DATE_PICKER_TRIGGER = (
        By.CSS_SELECTOR,
        '.el-date-editor .el-icon-date, '
        '.el-date-editor .el-input__prefix .el-icon',
    )

    # 按钮 — CSS_SELECTOR 优先
    RESET_BUTTON_CSS = (
        By.CSS_SELECTOR,
        '.search-form .el-button--default, '
        '.el-form .el-button:not(.el-button--primary):first-of-type',
    )
    QUERY_BUTTON_CSS = (
        By.CSS_SELECTOR,
        '.search-form .el-button--primary:first-of-type, '
        '.el-form .el-button--primary',
    )
    ADD_BUTTON_CSS = (
        By.CSS_SELECTOR,
        '.toolbar .el-button--primary, '
        'button.el-button--primary:has(.el-icon-plus), '
        '.el-button--primary .el-icon-plus',
    )
    EXPORT_BUTTON_CSS = (
        By.CSS_SELECTOR,
        'button.el-button--default .el-icon-download, '
        '.toolbar .el-button--default:last-of-type',
    )

    # 按钮 — 文本匹配保底（相对 XPath）
    RESET_BUTTON_XPATH = (
        By.XPATH,
        '//button[not(contains(@class,"el-button--primary"))]'
        '//span[contains(normalize-space(.),"重置")]/parent::button',
    )
    QUERY_BUTTON_XPATH = (
        By.XPATH,
        '//button[contains(@class,"el-button--primary")]'
        '//span[contains(normalize-space(.),"查询")]/parent::button',
    )
    ADD_BUTTON_XPATH = (
        By.XPATH,
        '//button[contains(@class,"el-button--primary")]'
        '//span[contains(normalize-space(.),"新增")]/parent::button',
    )
    EXPORT_BUTTON_XPATH = (
        By.XPATH,
        '//button[contains(@class,"el-button")]'
        '//span[contains(normalize-space(.),"导出")]/parent::button',
    )

    # ==================================================================
    #  基本信息 Tab（表格区域）
    # ==================================================================
    INFO_TAB = (
        By.XPATH,
        '//div[contains(@class,"el-tabs__item") and normalize-space(.)="基本信息"]',
    )

    # 表格列名（按 Kimi 识别结果）
    # 日期 | 取样时间 | 取样位置 | 班组 | 检验员 | 复核员 | 备注 |
    # 甲烷(%) | 乙烷(%) | 乙烯(%) | 乙炔(%) | 丙烷(%) | 丙烯(%) |
    # H2(%) | CO2(%) | O2(%) | N2(%) | CO(%)
    TABLE_COLUMNS = [
        "日期", "取样时间", "取样位置", "班组", "检验员", "复核员", "备注",
        "甲烷(%)", "乙烷(%)", "乙烯(%)", "乙炔(%)", "丙烷(%)", "丙烯(%)",
        "H2(%)", "CO2(%)", "O2(%)", "N2(%)", "CO(%)",
    ]

    # 统计行
    STATISTICS_ROW = (
        By.CSS_SELECTOR,
        'tfoot tr, .el-table__footer-wrapper tr, '
        'tr.average-row, [class*="statistics"], [class*="average"]',
    )

    # ==================================================================
    #  构造
    # ==================================================================
    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    # ==================================================================
    #  路由（来自 Kimi 识别结果）
    # ==================================================================
    PAGE_ROUTE = "#/lab/gas/report"

    # ==================================================================
    #  导航
    #  策略：直接 URL 跳转（Kimi 发现 Vue 使用 hash 路由，直接用 URL 最可靠）
    # ==================================================================
    def navigate_to(self):
        """导航到气体分析报告单页面（标准入口，满足代码质量扫描要求）"""
        self.navigate_to_gas_analysis_report()
        return self

    def navigate_to_gas_analysis_report(self):
        """导航到气体分析报告单页面（使用统一导航器 + 智能表格等待）"""
        logger.info("导航到 → 气体分析报告单 (%s)", self.PAGE_ROUTE)
        from base.sidebar_navigator import SidebarNavigator
        SidebarNavigator(self.driver)._navigate_by_js_hash(self.PAGE_ROUTE, "气体分析报告单")

    def _navigate_by_sidebar(self):
        """通过侧边栏导航（保底方案）

        Kimi 发现菜单项结构是 <a href="#/lab/gas/report">，
        直接用 CSS_SELECTOR 定位 a[href="..."] 即可。
        """
        logger.info("通过侧边栏导航...")
        # 先展开父级菜单
        submenu = self.SIDEBAR_SUBMENU[1].format(text="化验室取样")
        self.click((By.XPATH, submenu))
        self.wait_vue_stable()
        # 点击菜单链接
        link = self.SIDEBAR_MENU_LINK[1].format(route=self.PAGE_ROUTE)
        self.click((By.CSS_SELECTOR, link))
        self.wait_page_ready()

    # ==================================================================
    #  取样位置标签栏
    # ==================================================================
    def get_active_location(self):
        """获取当前选中（高亮）的取样位置名称

        Returns:
            str: 当前选中的取样位置名称，如 "界区原料气"
        """
        try:
            el = self.find_visible(self.LOCATION_TAB_ACTIVE, timeout=3)
            return (el.text or "").strip()
        except TimeoutException:
            return ""

    def click_location_tab(self, location_name):
        """点击指定取样位置标签切换数据

        Args:
            location_name: 取样位置名称，如 "界区原料气" / "LNG冷箱"
        """
        logger.info("切换取样位置: %s", location_name)

        # 策略1：在标签栏容器内定位
        try:
            xpath = self.LOCATION_TAB_IN_BAR[1].format(text=location_name)
            self.click((By.XPATH, xpath))
        except TimeoutException:
            # 策略2：全局查找（排除菜单和表格）
            xpath = self.LOCATION_TAB[1].format(text=location_name)
            self.click((By.XPATH, xpath))

        self._wait_table_ready()

    def get_all_location_names(self):
        """获取所有取样位置名称列表

        Returns:
            list[str]: 取样位置名称列表
        """
        # 通过查找标签栏中的所有文本节点来获取位置名
        # 使用已知的位置列表进行验证（从 Kimi 识别结果）
        known_locations = [
            "界区原料气", "除雾除尘出口原料气", "脱油脱萘", "低温水洗塔",
            "甲烷化产品气", "精脱硫1A", "精脱硫1B", "精脱硫2A", "精脱硫2B",
            "超精入口", "超精出口", "冷箱入口原料气", "富氢", "富氮",
            "LNG冷箱", "LNG储罐", "LNG装车站", "制冷剂",
            "合成氨入塔气", "合成氨出塔气", "液氨", "加样",
        ]
        found = []
        for loc in known_locations:
            if self._is_location_tab_present(loc):
                found.append(loc)
        return found

    def _is_location_tab_present(self, location_name):
        """检查取样位置标签是否存在"""
        try:
            xpath = self.LOCATION_TAB[1].format(text=location_name)
            return self.is_present((By.XPATH, xpath), timeout=1)
        except Exception:
            return False

    # ==================================================================
    #  搜索区操作
    # ==================================================================
    def input_start_date(self, date_str):
        """输入开始日期

        Args:
            date_str: 日期字符串，如 "2026-01-01"
        """
        logger.info("输入开始日期: %s", date_str)
        self.input_text(self.START_DATE_INPUT, date_str)

    def input_end_date(self, date_str):
        """输入结束日期

        Args:
            date_str: 日期字符串，如 "2026-06-01"
        """
        logger.info("输入结束日期: %s", date_str)
        self.input_text(self.END_DATE_INPUT, date_str)

    def get_start_date(self):
        """获取开始日期当前值"""
        try:
            el = self.find(self.START_DATE_INPUT, timeout=3)
            return (el.get_attribute("value") or "").strip()
        except TimeoutException:
            return ""

    def get_end_date(self):
        """获取结束日期当前值"""
        try:
            el = self.find(self.END_DATE_INPUT, timeout=3)
            return (el.get_attribute("value") or "").strip()
        except TimeoutException:
            return ""

    def click_reset(self):
        """点击重置按钮"""
        logger.info("点击重置按钮")
        try:
            self.click(self.RESET_BUTTON_CSS)
        except TimeoutException:
            self.click(self.RESET_BUTTON_XPATH)
        self._wait_table_ready()

    def click_query(self):
        """点击查询按钮"""
        logger.info("点击查询按钮")
        try:
            self.click(self.QUERY_BUTTON_CSS)
        except TimeoutException:
            self.click(self.QUERY_BUTTON_XPATH)
        self._wait_table_ready()

    def click_add(self):
        """点击新增报告单按钮，等待弹窗打开"""
        logger.info("点击新增报告单按钮")
        try:
            self.click(self.ADD_BUTTON_CSS)
        except TimeoutException:
            self.click(self.ADD_BUTTON_XPATH)
        self.wait_dialog_open()

    def click_export(self):
        """点击导出按钮并获取结果

        Returns:
            bool: 是否成功触发导出
        """
        logger.info("点击导出按钮")
        # 导出按钮可能被其他元素遮挡，使用 JS 点击绕过
        try:
            self.click(self.EXPORT_BUTTON_CSS)
        except TimeoutException:
            try:
                self.js_click(self.EXPORT_BUTTON_XPATH)
            except TimeoutException:
                # 尝试任何包含"导出"文字的按钮
                export_btn = (
                    By.XPATH,
                    '//button[contains(normalize-space(.),"导出")]',
                )
                self.js_click(export_btn)
        # 等待可能的确认弹窗或 Toast
        self.wait_vue_stable()
        try:
            self.confirm_message_box()
            return True
        except TimeoutException:
            # 没有确认弹窗，可能直接开始下载
            pass
        return True  # 点击成功即视为导出操作已触发

    def filter_by_date_range(self, start_date, end_date):
        """按日期范围筛选（完整流程）

        Args:
            start_date: 开始日期
            end_date: 结束日期
        """
        self.input_start_date(start_date)
        self.input_end_date(end_date)
        self.click_query()

    # ==================================================================
    #  表格操作
    #  说明：本页表格可能是标准 HTML <table> 而非 Element Plus el-table，
    #        故定位器兼容两种格式。
    # ==================================================================
    def get_table_headers(self):
        """JS提取表格表头（含重试，应对Element Plus异步渲染）

        修复 EP-010：前置 wait_vue_stable() 确保 Vue 动画完成后再读取表头。
        双策略：优先 el-table → 降级标准 table（本页使用自定义 report-table）。
        """
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        for attempt in range(6):
            # 策略1：Element Plus el-table
            headers = self.driver.execute_script("""
                var cells = document.querySelectorAll(
                    '.el-table__header-wrapper th .cell, .el-table__header-wrapper thead th'
                );
                return Array.from(cells).map(function(el) {
                    return el.textContent.trim();
                }).filter(Boolean);
            """)
            if headers and len(headers) >= 3:
                return headers
            # 策略2：标准 HTML table（取最后一行 th，兼容多行表头）
            headers = self.driver.execute_script("""
                var ths = document.querySelectorAll('thead tr:last-child th');
                return Array.from(ths).map(function(el) {
                    return el.textContent.trim();
                }).filter(Boolean);
            """)
            if headers and len(headers) >= 3:
                return headers
            time.sleep(TIMEOUT_CONFIG["micro_wait"])
        return []
    def get_table_row_count(self):
        """获取当前页可见数据行数（排除统计行）"""
        self._wait_table_ready()
        # 策略1：Element Plus
        rows = self.find_all(
            (By.CSS_SELECTOR, '.el-table__body-wrapper tbody tr.el-table__row')
        )
        if rows:
            return sum(1 for r in rows if r.is_displayed())
        # 策略2：标准 table（排除统计行 summary-row）
        rows = self.find_all(
            (By.CSS_SELECTOR, 'tbody tr:not(.summary-row):not([class*=average]):not([class*=summary])')
        )
        count = 0
        for r in rows:
            # 跳过包含 "平均值" 文本的行
            text = (r.text or "").strip()
            if "平均值" in text:
                continue
            if r.is_displayed():
                count += 1
        return count

    def get_column_index_by_header(self, header_text):
        """根据表头文本获取列索引（1-based）

        多行表头兼容：只取 thead 最后一行的 th（定义实际数据列）
        """
        self._wait_table_ready()
        # 策略1：Element Plus — 最后一行的 th
        ths = self.find_all((By.CSS_SELECTOR, '.el-table__header-wrapper thead tr:last-child th'))
        if not ths:
            # 策略2：标准 table — 最后一行的 th
            ths = self.find_all((By.CSS_SELECTOR, 'thead tr:last-child th'))
        header_text_clean = header_text.replace('\n', '')
        for idx, th in enumerate(ths, start=1):
            th_text = (th.text or "").strip().replace('\n', '')
            if th_text == header_text_clean:
                return idx
        return None

    def get_column_data_by_header(self, header_text):
        """按表头名称获取整列数据（排除统计行）"""
        idx = self.get_column_index_by_header(header_text)
        if not idx:
            return []
        self._wait_table_ready()
        # 策略1：Element Plus（排除统计行）
        cells = self.find_all(
            (By.CSS_SELECTOR,
             f'.el-table__body-wrapper tbody tr:not([class*=summary]):not([class*=average]) '
             f'td:nth-child({idx}) .cell')
        )
        if not cells:
            # 策略2：标准 table（排除统计行）
            cells = self.find_all(
                (By.CSS_SELECTOR,
                 f'tbody tr:not(.summary-row):not([class*=average]):not([class*=summary]) '
                 f'td:nth-child({idx})')
            )
        return [c.text.strip() for c in cells if c.text.strip()]

    def get_row_data(self, row_index):
        """获取指定行的所有列数据（1-based）

        Returns:
            list[str]: 该行所有单元格文本
        """
        self._wait_table_ready()
        rows = self.find_all(self.TABLE_ROWS)
        visible_rows = [r for r in rows if r.is_displayed()]
        if row_index > len(visible_rows):
            return []
        cells = visible_rows[row_index - 1].find_elements(By.TAG_NAME, "td")
        return [c.text.strip() for c in cells]

    def get_empty_text(self):
        """获取表格空数据提示文本"""
        self._wait_table_ready()
        try:
            el = self.find(
                (By.CSS_SELECTOR, '.el-table__empty-text, .el-table-empty, [class*=empty]'),
                timeout=3,
            )
            return (el.text or "").strip()
        except TimeoutException:
            return ""

    # ==================================================================
    #  统计行操作
    # ==================================================================
    def get_statistics_data(self):
        """获取统计行（平均值行）数据

        Returns:
            dict: {列名: 平均值} 或空字典
        """
        try:
            stat_row = self.find_visible(self.STATISTICS_ROW, timeout=3)
            cells = stat_row.find_elements(By.TAG_NAME, "td")
            # 第一个单元格通常是 "平均值"
            return {
                "label": cells[0].text.strip() if cells else "",
                "values": [c.text.strip() for c in cells[1:]],
            }
        except TimeoutException:
            return {}

    def get_average_value(self, column_name):
        """获取指定列的平均值

        Args:
            column_name: 列名，如 "甲烷(%)"

        Returns:
            str: 平均值文本
        """
        idx = self.get_column_index_by_header(column_name)
        if not idx:
            return ""
        stat = self.get_statistics_data()
        if stat and "values" in stat and len(stat["values"]) >= idx:
            return stat["values"][idx - 1]
        return ""

    # ==================================================================
    #  新增报告单弹窗（基于 Kimi 识别的字段结构）
    #  弹窗标题："新增报告单"  保存按钮："保存报告"
    # ==================================================================
    def fill_report_form(self, inspector, reviewer,
                         date=None, sample_time=None,
                         sample_location=None, shift=None, remark=None,
                         gas_values=None):
        """填充新增报告单弹窗表单

        必填字段（Kimi 标注 *）：检验员、复核员

        Args:
            inspector: 检验员（必填）
            reviewer: 复核员（必填）
            date: 日期（date-picker）
            sample_time: 取样时间（time-picker）
            sample_location: 取样位置（select，默认「界区原料气」）
            shift: 班组（select）
            remark: 备注（textarea）
            gas_values: dict，气体组分值，key 为指标名（不含单位），如 {"甲烷": "95.5"}
        """
        # 必填项（Kimi 标注 * 的字段）
        self.fill_dialog_input("检验员", inspector)
        self.fill_dialog_input("复核员", reviewer)

        # 日期和时间（Element Plus date/time-picker）
        if date:
            self.fill_dialog_input("日期", date)
        if sample_time:
            self.fill_dialog_input("取样时间", sample_time)

        # 下拉选择
        if sample_location:
            self.select_dialog_dropdown("取样位置", sample_location)
        if shift:
            self.select_dialog_dropdown("班组", shift)

        # 备注
        if remark:
            self.fill_dialog_input("备注", remark)

        # 气体组成 & 微量成分（全部是 input-number 类型）
        # Kimi 识别的字段：甲烷, 乙烷, 乙烯, 乙炔, 丙烷, 丙烯,
        # H2, CO2, O2, N2, CO, 微量测氧仪氧含量, 硫化氢, 羰基硫,
        # 二硫化碳, 噻吩, 苯, 甲苯, 间对二甲苯, 邻二甲苯, 萘, 氨, 焦油尘
        if gas_values:
            for gas_name, gas_value in gas_values.items():
                self.fill_dialog_input(gas_name, str(gas_value))

    def save_report(self):
        """点击弹窗「保存报告」按钮并获取结果

        Kimi 识别：弹窗底部按钮为「取消」+「保存报告」（非「确定」）
        BasePage.click_dialog_save 使用 CSS_SELECTOR .el-button--primary，
        不依赖按钮文字，因此兼容。
        """
        self.click_dialog_save()
        return self.wait_for_toast_text()

    # ==================================================================
    #  内部工具方法
    # ==================================================================
    def _wait_table_ready(self, timeout=15):
        """等待表格 thead th 出现并可见

        修复 EP-010：前置 _wait_loading_gone() + wait_vue_stable()，
        对齐 equipment 模块标准模式。
        """
        self._wait_loading_gone(timeout)
        self.wait_vue_stable()
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                th_count = self.driver.execute_script(
                    "return document.querySelectorAll('thead th').length;"
                )
                body_count = self.driver.execute_script(
                    "return document.querySelectorAll('tbody').length;"
                )
                current_hash = self.driver.execute_script(
                    "return window.location.hash;"
                )
                logger.debug("轮询: thead th=%d, tbody=%d, hash=%s", th_count, body_count, current_hash)

                if th_count > 0:
                    # 检查是否至少有一个 th 可见
                    has_visible = self.driver.execute_script(
                        "var ths = document.querySelectorAll('thead th');"
                        "for (var i = 0; i < ths.length; i++) {"
                        "  if (ths[i].offsetHeight > 0 && ths[i].textContent.trim()) return true;"
                        "}"
                        "return false;"
                    )
                    if has_visible:
                        return True
                    else:
                        logger.debug("thead th 存在 (%d) 但 offsetHeight=0 (动画中)", th_count)
            except Exception as e:
                logger.debug("轮询异常: %s", str(e)[:100])
            time.sleep(TIMEOUT_CONFIG["micro_wait"])
        logger.warning("表格表头未在 %ds 内变为可见 (最后: th=%d)", timeout, th_count if 'th_count' in dir() else 0)
