"""备品入库页面 Page Object

8列表格，与环保入库结构相似。
审批链：备件入库审批链 (admin 会签)
"""
import logging
from selenium.webdriver.common.by import By
from base.base_page import BasePage

logger = logging.getLogger(__name__)


class SpareInOrderPage(BasePage):

    FILTER_HANDLER = (By.XPATH, '//input[@placeholder="请输入经办人"]')
    FILTER_DATE = (By.XPATH, '//input[@placeholder="选择日期"]')
    BTN_QUERY = (By.XPATH, '//button[contains(.,"查询")]')
    BTN_RESET = (By.XPATH, '//button[contains(.,"重置")]')
    BTN_ADD = (By.XPATH, '//button[contains(.,"新增入库")]')
    BTN_VIEW = (By.XPATH, '//button[contains(.,"查看")]')

    def navigate(self):
        self.navigate_to("库管管理", "备品备件管理", "入库")
        self._wait_page_ready()

    def _wait_page_ready(self):
        self.wait_vue_stable()
        self._wait_loading_gone()

    def click_add(self):
        self.click(self.BTN_ADD)
        self.wait_dialog_open()

    def click_view_first(self):
        self.click(self.BTN_VIEW)
        self.wait_dialog_open()

    def search_by_handler(self, name):
        self.input_text(self.FILTER_HANDLER, name)
        self.click(self.BTN_QUERY)
        self.wait_vue_stable()

    def reset_search(self):
        self.click(self.BTN_RESET)
        self.wait_vue_stable()
