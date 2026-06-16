"""备品出入库记录页面 Page Object

只读审计日志页面，无审批流。
"""
import logging
from selenium.webdriver.common.by import By
from base.base_page import BasePage

logger = logging.getLogger(__name__)


class SpareIORecordPage(BasePage):

    FILTER_ITEM_NAME = (By.XPATH, '//input[@placeholder="请输入物品名称"]')
    BTN_QUERY = (By.XPATH, '//button[contains(.,"查询")]')
    BTN_RESET = (By.XPATH, '//button[contains(.,"重置")]')

    def navigate(self):
        self.navigate_to("库管管理", "备品备件管理", "出入库记录")
        self._wait_page_ready()

    def _wait_page_ready(self):
        self.wait_vue_stable()
        self._wait_loading_gone()

    def search_by_item_name(self, name):
        self.input_text(self.FILTER_ITEM_NAME, name)
        self.click(self.BTN_QUERY)
        self.wait_vue_stable()

    def reset_search(self):
        self.click(self.BTN_RESET)
        self.wait_vue_stable()
