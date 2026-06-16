"""Lab Compare Page Object — gas/water 共用"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from base.base_page import BasePage

logger = logging.getLogger(__name__)
ROUTES = {'gas': '#/lab/gas/compare', 'water': '#/lab/water/compare'}
MENUS = {'gas': ['化验室取样', '气体分析对比'], 'water': ['化验室取样', '水质分析对比']}

class LabComparePage(BasePage):
    def __init__(self, driver, sub='gas', timeout=None):
        super().__init__(driver, timeout)
        self.sub = sub
        self.PAGE_ROUTE = ROUTES[sub]

    def navigate(self):
        m = MENUS[self.sub]
        logger.info('navigate to %s', ' -> '.join(m))
        self.navigate_to(*m)
        self.wait_page_ready(15)
        self._wait_loading_gone(10)
        self.wait_vue_stable()

    def set_start_date(self, v):
        el = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder*="开始日期"]')))
        el.clear()
        el.send_keys(v)

    def set_end_date(self, v):
        el = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder*="结束日期"]')))
        el.clear()
        el.send_keys(v)

    def click_query(self):
        self._js('查询')
        self._wait_loading_gone(10)
        self.wait_vue_stable()

    def click_reset(self):
        self._js('重置')
        self._wait_loading_gone(10)
        self.wait_vue_stable()

    def _js(self, t):
        self.driver.execute_script("""
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                if ((btns[i].textContent || '').trim().indexOf(arguments[0]) !== -1) {
                    btns[i].click(); return;
                }
            }
        """, t)

    def is_page_loaded(self):
        self.wait_vue_stable()
        self._wait_loading_gone(10)
        return bool(self.driver.execute_script(
            'return !!document.querySelector("input[placeholder*=\\"开始日期\\"]");'))

    def get_table_row_count(self):
        try:
            return sum(1 for r in self.driver.find_elements(By.CSS_SELECTOR, 'table tbody tr') if r.is_displayed())
        except Exception:
            return 0

    def _wait_page_ready(self):
        self._wait_loading_gone(10)
        self.wait_vue_stable()

    def get_row_count(self):
        return self.get_table_row_count()

    def verify_row_count(self):
        return self.get_table_row_count() > 0

    def search_compare(self, pos1, pos2):
        """选择两个取样位置并查询"""
        # Click first select to open dropdown, then select option
        self.driver.execute_script("""
            var selects = document.querySelectorAll('.el-select');
            if (selects.length >= 2) {
                selects[0].click();
            }
        """)
        self._wait_loading_gone(3)
        # Click second select
        self.driver.execute_script("""
            var selects = document.querySelectorAll('.el-select');
            if (selects.length >= 2) {
                selects[1].click();
            }
        """)
        self._wait_loading_gone(3)
        self.click_query()
        return self.get_table_row_count()
