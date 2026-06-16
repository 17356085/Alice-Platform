from base.base_page import BasePage
from selenium.webdriver.common.by import By
import logging
logger = logging.getLogger(__name__)
ROUTES = {'gas': '#/lab/gas/indicator', 'water': '#/lab/water/indicator'}
MENUS = {'gas': ['化验室取样', '气体分析设计指标'], 'water': ['化验室取样', '水质分析设计指标']}

class LabIndicatorPage(BasePage):
    EMPTY_TEXT = (By.CSS_SELECTOR, '.el-table__empty-text')
    TABLE_ROWS = (By.CSS_SELECTOR, '.el-table__body-wrapper tbody tr')
    def __init__(self, driver, sub='gas', timeout=None):
        super().__init__(driver, timeout)
        self.sub = sub
        self.PAGE_ROUTE = ROUTES[sub]
    def navigate(self):
        menu = MENUS[self.sub]
        logger.info('导航到 → %s', ' → '.join(menu))
        self.navigate_to(*menu)
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        return self
    def get_table_headers(self):
        self.wait_vue_stable(); self._wait_loading_gone(timeout=5)
        return self.driver.execute_script("return Array.from(document.querySelectorAll('.el-table__header-wrapper th .cell')).map(function(el){return el.textContent.trim()}).filter(Boolean);")
    def get_table_row_count(self):
        self._wait_loading_gone(timeout=5)
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return sum(1 for r in rows if r.is_displayed())
    def get_empty_text(self):
        try: return (self.driver.find_element(*self.EMPTY_TEXT).text or '').strip()
        except: return ''
    def get_column_data(self, col_index):
        self._wait_loading_gone(timeout=5)
        xpath = f'.//div[contains(@class,"el-table__body-wrapper")]//tbody/tr/td[{col_index}]//div[contains(@class,"cell")]'
        return [(c.text or '').strip() for c in self.driver.find_elements(By.XPATH, xpath) if (c.text or '').strip()]

    def _wait_page_ready(self):
        """test_indicator.py 调用 — 等待页面就绪"""
        self._wait_loading_gone(10); self.wait_vue_stable()

    def get_row_count(self):
        """test_indicator.py / test_compare.py 调用 — 行数别名"""
        return self.get_table_row_count()

    def verify_row_count(self):
        """test_indicator.py 调用 — 验证有数据"""
        return self.get_table_row_count() > 0