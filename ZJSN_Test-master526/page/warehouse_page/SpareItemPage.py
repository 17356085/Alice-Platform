"""备品物品管理页面 Page Object

CRUD + 导入导出 + 批量选择(checkbox)，无审批流。
"""
import logging
from selenium.webdriver.common.by import By
from base.base_page import BasePage

logger = logging.getLogger(__name__)


class SpareItemPage(BasePage):

    FILTER_ITEM_NAME = (By.XPATH, '//input[@placeholder="请输入物品名称"]')
    FILTER_FACTORY = (By.XPATH, '//input[@placeholder="请输入厂家名称"]')
    BTN_QUERY = (By.XPATH, '//button[contains(.,"查询")]')
    BTN_RESET = (By.XPATH, '//button[contains(.,"重置")]')
    BTN_ADD = (By.XPATH, '//button[contains(.,"新增")]')
    BTN_VIEW = (By.XPATH, '//button[contains(.,"查看")]')

    def navigate(self):
        self.navigate_to("库管管理", "备品备件管理", "物品管理")
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

    def click_add(self):
        self.click(self.BTN_ADD)
        self.wait_dialog_open()

    def click_view_first(self):
        self.click(self.BTN_VIEW)
        self.wait_dialog_open()
