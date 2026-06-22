"""
气体分析报告单页面 Page Object

==== 页面概述 ====
  路径：化验室取样 → 气体分析报告单
  功能：查看各取样位置的气体分析数据，支持日期筛选、新增报告单、导出

==== 定位策略 ====
  1. CSS_SELECTOR：语义属性 > Element Plus 标准类
  2. 相对 XPath：仅用于文本内容匹配
  3. 禁止：绝对路径 XPath（从根节点 html body 逐层定位）

==== 开发者 ====
  Created by: AI Assistant (page-object-generator)
  Last Updated: 2024-05-24
"""
from selenium.webdriver.common.by import By
from base.base_page import BasePage


class GasAnalysisReportPage(BasePage):
    """气体分析报告单页面"""

    # ==================================================================
    #  侧边栏导航
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
    #  取样位置标签栏 — 自定义 Tab 组件（高风险区域）
    # ==================================================================
    LOCATION_TAB = (
        By.XPATH,
        '//*[contains(normalize-space(.),"{text}") and not(ancestor::table)]'
        '[not(ancestor::nav) and not(ancestor::ul[contains(@class,"el-menu")])]',
    )
    LOCATION_TAB_ACTIVE = (
        By.CSS_SELECTOR,
        '.el-tabs__item.is-active, [class*="tab"][class*="active"], '
        '[class*="tag"][class*="active"]',
    )

    # ==================================================================
    #  搜索区
    # ==================================================================
    START_DATE_INPUT = (
        By.CSS_SELECTOR,
        'input[placeholder*="开始日期"]',
    )
    END_DATE_INPUT = (
        By.CSS_SELECTOR,
        'input[placeholder*="结束日期"]',
    )
    QUERY_BUTTON = (
        By.CSS_SELECTOR,
        '.search-form .el-button--primary:first-of-type, '
        '.el-form .el-button--primary',
    )
    RESET_BUTTON = (
        By.CSS_SELECTOR,
        '.search-form .el-button--default, '
        '.el-form .el-button:not(.el-button--primary):first-of-type',
    )
    ADD_BUTTON = (
        By.CSS_SELECTOR,
        '.toolbar .el-button--primary, '
        'button.el-button--primary:has(.el-icon-plus), '
        '.el-button--primary .el-icon-plus',
    )
    EXPORT_BUTTON = (
        By.CSS_SELECTOR,
        'button.el-button--default .el-icon-download, '
        '.toolbar .el-button--default:last-of-type',
    )

    # ==================================================================
    #  基本信息 Tab（表格区域）
    # ==================================================================
    INFO_TAB = (
        By.XPATH,
        '//div[contains(@class,"el-tabs__item") and normalize-space(.)="基本信息"]',
    )

    # ==================================================================
    #  构造
    # ==================================================================
    def __init__(self, driver):
        super().__init__(driver)

    # ==================================================================
    #  路由
    # ==================================================================
    PAGE_ROUTE = "#/lab/gas/report"

    # ==================================================================
    #  导航（唯一入口）
    # ==================================================================
    def navigate(self):
        """导航到气体分析报告单页面"""
        self.logger.info("导航到 → 气体分析报告单 (%s)", self.PAGE_ROUTE)
        self._navigate_by_url()
        self.wait_vue_stable()
        return self

    def _navigate_by_url(self):
        """通过直接 URL 跳转导航"""
        from base.sidebar_navigator import SidebarNavigator
        SidebarNavigator(self.driver)._navigate_by_js_hash(
            self.PAGE_ROUTE, "气体分析报告单"
        )

    # ==================================================================
    #  取样位置操作
    # ==================================================================
    def select_location(self, location_name):
        """切换到指定取样位置标签

        Args:
            location_name: 取样位置名称文本
        """
        self.logger.info("切换取样位置 → %s", location_name)
        locator = (By.XPATH, self.LOCATION_TAB[1].format(text=location_name))
        self.wait_clickable(locator).click()
        self.wait_vue_stable()
        return self

    # ==================================================================
    #  筛选操作
    # ==================================================================
    def filter_by_date_range(self, start_date, end_date):
        """按日期范围查询数据

        Args:
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
        """
        self.logger.info("按日期范围查询: %s ~ %s", start_date, end_date)
        self.wait_visible(self.START_DATE_INPUT).clear()
        self.wait_visible(self.START_DATE_INPUT).send_keys(start_date)
        self.wait_visible(self.END_DATE_INPUT).clear()
        self.wait_visible(self.END_DATE_INPUT).send_keys(end_date)
        self.click_query()
        return self

    def click_query(self):
        """点击查询按钮"""
        self.logger.info("点击查询按钮")
        self.wait_clickable(self.QUERY_BUTTON).click()
        self.wait_vue_stable()
        return self

    def click_reset(self):
        """点击重置按钮"""
        self.logger.info("点击重置按钮")
        self.wait_clickable(self.RESET_BUTTON).click()
        self.wait_vue_stable()
        return self

    # ==================================================================
    #  工具栏操作
    # ==================================================================
    def click_add(self):
        """点击新增报告单按钮"""
        self.logger.info("点击新增按钮")
        self.wait_clickable(self.ADD_BUTTON).click()
        return self

    def click_export(self):
        """点击导出按钮"""
        self.logger.info("点击导出按钮")
        self.wait_clickable(self.EXPORT_BUTTON).click()
        return self

    # ==================================================================
    #  表格操作
    # ==================================================================
    def get_table_headers(self):
        """获取表格表头文本列表"""
        self.logger.info("获取表格表头")
        return self.get_table_header_texts()

    def get_table_row_count(self):
        """获取表格数据行数"""
        self.logger.info("获取表格行数")
        return len(self.get_table_data_rows())

    def get_empty_text(self):
        """获取表格空状态提示文本"""
        self.logger.info("检查表格空状态")
        return self.get_table_empty_text()

    def get_column_data_by_header(self, column_name):
        """根据列名获取该列所有数据

        Args:
            column_name: 列名
        """
        self.logger.info("获取列数据: %s", column_name)
        return self.get_table_column_data(column_name)

    def click_info_tab(self):
        """切换到基本信息 Tab"""
        self.logger.info("切换到基本信息 Tab")
        self.wait_clickable(self.INFO_TAB).click()
        self.wait_vue_stable()
        return self