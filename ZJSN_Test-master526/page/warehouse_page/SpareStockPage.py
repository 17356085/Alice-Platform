"""备品库存查询页面 Page Object

只读页面：查询+重置，无行内操作按钮，无审批流。
"""
import logging
from selenium.webdriver.common.by import By
from base.base_page import BasePage

logger = logging.getLogger(__name__)


class SpareStockPage(BasePage):

    # ── 搜索区 ──────────────────────────────────────────────
    FILTER_ITEM_NAME = (By.XPATH, '//input[@placeholder="请输入物品名称"]')
    BTN_QUERY = (By.XPATH, '//button[contains(.,"查询")]')
    BTN_RESET = (By.XPATH, '//button[contains(.,"重置")]')

    # ── 导航 ────────────────────────────────────────────────
    def navigate(self):
        self.navigate_to("库管管理", "备品备件管理", "库存查询")
        self._wait_page_ready()

    def _wait_page_ready(self):
        self.wait_vue_stable()
        self._wait_loading_gone()

    # ── 搜索操作 ────────────────────────────────────────────
    def search_by_item_name(self, name):
        """按物品名称搜索"""
        self.input_text(self.FILTER_ITEM_NAME, name)
        self.click(self.BTN_QUERY)
        self.wait_vue_stable()

    def reset_search(self):
        """重置搜索条件"""
        self.click(self.BTN_RESET)
        self.wait_vue_stable()
