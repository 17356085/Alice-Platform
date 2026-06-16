"""备品库存盘点调整页面 Page Object

只读查询页面，盘点调整直接生效，无审批流。
"""
import logging
from selenium.webdriver.common.by import By
from base.base_page import BasePage

logger = logging.getLogger(__name__)


class SpareStockAdjustPage(BasePage):

    FILTER_ITEM_CODE = (By.XPATH, '//input[@placeholder="请输入物品编号"]')
    FILTER_DATE = (By.XPATH, '//input[@placeholder="选择日期"]')
    BTN_QUERY = (By.XPATH, '//button[contains(.,"查询")]')
    BTN_RESET = (By.XPATH, '//button[contains(.,"重置")]')

    def navigate(self):
        self.navigate_to("库管管理", "备品备件管理", "盘点调整")
        self._wait_page_ready()

    def _wait_page_ready(self):
        self.wait_vue_stable()
        self._wait_loading_gone()

    def search_by_item_code(self, code):
        self.input_text(self.FILTER_ITEM_CODE, code)
        self.click(self.BTN_QUERY)
        self.wait_vue_stable()

    def reset_search(self):
        self.click(self.BTN_RESET)
        self.wait_vue_stable()
