"""备品库存盘点页面 Page Object

只读查询+审批链：备件盘点审批链 (chenqian → tjw)
"""
import logging
from selenium.webdriver.common.by import By
from base.base_page import BasePage

logger = logging.getLogger(__name__)


class SpareStocktakePage(BasePage):

    FILTER_HANDLER = (By.XPATH, '//input[@placeholder="请输入盘点人"]')
    FILTER_DATE = (By.XPATH, '//input[@placeholder="选择日期"]')
    BTN_QUERY = (By.XPATH, '//button[contains(.,"查询")]')
    BTN_RESET = (By.XPATH, '//button[contains(.,"重置")]')

    def navigate(self):
        self.navigate_to("库管管理", "备品备件管理", "库存盘点")
        self._wait_page_ready()

    def _wait_page_ready(self):
        self.wait_vue_stable()
        self._wait_loading_gone()

    def search_by_handler(self, name):
        self.input_text(self.FILTER_HANDLER, name)
        self.click(self.BTN_QUERY)
        self.wait_vue_stable()

    def reset_search(self):
        self.click(self.BTN_RESET)
        self.wait_vue_stable()
