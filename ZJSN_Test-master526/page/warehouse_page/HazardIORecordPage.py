"""环保出入库明细表页面 Page Object

只读审计日志，无审批流。搜索区为日期范围选择器。
"""
import logging
from selenium.webdriver.common.by import By
from base.base_page import BasePage

logger = logging.getLogger(__name__)


class HazardIORecordPage(BasePage):

    # 日期范围搜索（非普通 input）
    FILTER_DATE_START = (By.XPATH, '//input[@placeholder="开始日期"]')
    FILTER_DATE_END = (By.XPATH, '//input[@placeholder="结束日期"]')
    BTN_QUERY = (By.XPATH, '//button[contains(.,"查询")]')
    BTN_RESET = (By.XPATH, '//button[contains(.,"重置")]')

    def navigate(self):
        self.navigate_to("库管管理", "环保危废管理", "出入库明细")
        self._wait_page_ready()

    def _wait_page_ready(self):
        self.wait_vue_stable()
        self._wait_loading_gone()

    def reset_search(self):
        self.click(self.BTN_RESET)
        self.wait_vue_stable()
