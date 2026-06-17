# page/warehouse_page/hazard_io_record_page.py
"""环保出入库明细表页面 Page Object

只读审计日志，无审批流。基于页面上下文和测试脚本生成。
"""
import logging
from selenium.webdriver.common.by import By
from base.base_page import BasePage

logger = logging.getLogger(__name__)


class HazardIORecordPage(BasePage):
    """环保出入库明细表页面"""

    # ==================== 定位器 ====================
    # 搜索区
    FILTER_DATE_START = (By.XPATH, '//input[@placeholder="开始日期"]')
    FILTER_DATE_END = (By.XPATH, '//input[@placeholder="结束日期"]')
    BTN_QUERY = (By.XPATH, '//button[contains(.,"查询")]')
    BTN_RESET = (By.XPATH, '//button[contains(.,"重置")]')

    # 表格与分页 (CSS 优先，基于 Element Plus 通用类名)
    TABLE_ROWS = (By.CSS_SELECTOR, '.el-table__body-wrapper tbody tr.el-table__row')
    TOTAL_COUNT = (By.CSS_SELECTOR, '.el-pagination .el-pagination__total')

    # ==================== 导航 ====================

    def navigate(self):
        self.logger.info("导航到环保出入库明细表页面")
        self.navigate_to("库管管理", "环保危废管理", "出入库明细")
        self._wait_page_ready()
        self.logger.info("页面导航完成")
        return self

    def _wait_page_ready(self):
        """等待页面加载核心元素就绪"""
        self.wait_vue_stable()
        self.wait_loading_gone()
        # 等待一个核心元素出现以确保页面完全渲染
        self.wait_visible(self.BTN_QUERY)

    # ==================== 核心操作方法 ====================

    def query(self, start_date: str = None, end_date: str = None):
        """按日期范围查询
        
        Args:
            start_date: 开始日期，格式如 '2024-01-01'
            end_date: 结束日期，格式如 '2024-01-31'
        
        Returns:
            self: 支持链式调用
        """
        if start_date:
            self.logger.info(f"输入开始日期: {start_date}")
            self.clear_and_type(self.FILTER_DATE_START, start_date)
        if end_date:
            self.logger.info(f"输入结束日期: {end_date}")
            self.clear_and_type(self.FILTER_DATE_END, end_date)
        
        self.logger.info("点击查询按钮")
        self.click(self.BTN_QUERY)
        self._wait_page_ready()
        return self

    def reset_search(self):
        """重置搜索条件到默认状态"""
        self.logger.info("点击重置按钮")
        self.click(self.BTN_RESET)
        self._wait_page_ready()
        self.logger.info("搜索条件已重置")
        return self

    # ==================== 数据获取方法 ====================

    def get_table_data(self) -> list:
        """获取当前页表格的所有数据行
        
        Returns:
            包含所有数据行 WebElement 的列表
        """
        self.logger.info("获取表格数据行")
        rows = self.find_elements(self.TABLE_ROWS)
        self.logger.info(f"获取到 {len(rows)} 行数据")
        return rows

    def get_pagination_info(self) -> str:
        """获取分页总记录数文本
        
        Returns:
            str: 分页文本，例如 "共 100 条"
        """
        self.logger.info("获取分页信息")
        total_text = self.wait_visible(self.TOTAL_COUNT).text
        self.logger.info(f"分页信息: {total_text}")
        return total_text

    def wait_for_load(self):
        """等待表格数据加载完成
        
        用于测试脚本中确保数据已更新
        """
        self.logger.info("等待表格数据加载完成")
        self._wait_page_ready()
        return self