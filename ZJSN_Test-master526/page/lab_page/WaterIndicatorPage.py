"""水质分析设计指标 Page Object

路由: #/lab/water/indicator
类型: 只读展示表格（无搜索、无分页、无CRUD）
对称页面: GasIndicatorPage（气体版）
"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class WaterIndicatorPage(BasePage):
    """水质分析设计指标 — 只读展示页"""

    PAGE_ROUTE = "#/lab/water/indicator"
    EMPTY_TEXT = (By.CSS_SELECTOR, ".el-table__empty-text")
    TABLE_ROWS = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr")
    DIALOG = (By.CSS_SELECTOR, '.el-dialog:not([style*="display: none"])')

    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    def navigate(self):
        logger.info("导航到 → 化验室取样 → 水质分析设计指标")
        self.navigate_to("化验室取样", "水质分析设计指标")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        return self

    def get_table_headers(self):
        self.wait_vue_stable()
        self._wait_loading_gone(timeout=5)
        return self.driver.execute_script("""
            return Array.from(
                document.querySelectorAll('.el-table__header-wrapper th .cell')
            ).map(function(el) { return el.textContent.trim(); }).filter(Boolean);
        """)

    def get_table_row_count(self):
        self._wait_loading_gone(timeout=5)
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return sum(1 for r in rows if r.is_displayed())

    def get_empty_text(self):
        try:
            return (self.driver.find_element(*self.EMPTY_TEXT).text or "").strip()
        except Exception:
            return ""

    def get_column_data(self, col_index):
        self._wait_loading_gone(timeout=5)
        xpath = f'.//div[contains(@class,"el-table__body-wrapper")]//tbody/tr/td[{col_index}]//div[contains(@class,"cell")]'
        return [(c.text or "").strip() for c in self.driver.find_elements(By.XPATH, xpath) if (c.text or "").strip()]
