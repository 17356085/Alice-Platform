"""Water Analysis Report Page Object"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from base.base_page import BasePage

logger = logging.getLogger(__name__)

class WaterAnalysisReportPage(BasePage):
    PAGE_ROUTE = '#/lab/water/report'
    DIALOG = (By.CSS_SELECTOR, '.el-dialog:not([style*="display: none"])')
    BTN_ADD = (By.XPATH, '//button[contains(.,"新增报告单")]')

    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    def navigate(self):
        logger.info('navigate to water report')
        self.navigate_to('化验室取样', '水质分析报告单')
        self.wait_page_ready(15)
        self._wait_loading_gone(10)
        self.wait_vue_stable()

    def _wait_page_ready(self):
        self._wait_loading_gone(10)
        self.wait_vue_stable()

    def search_by_date(self, start, end):
        try:
            el = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder*="开始日期"]')))
            el.clear()
            el.send_keys(start)
        except Exception:
            pass
        try:
            el = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder*="结束日期"]')))
            el.clear()
            el.send_keys(end)
        except Exception:
            pass
        self._js_click('查询')
        self._wait_loading_gone(10)
        self.wait_vue_stable()

    def _js_click(self, t):
        self.driver.execute_script("""
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                if ((btns[i].textContent || '').trim().indexOf(arguments[0]) !== -1) {
                    btns[i].click(); return;
                }
            }
        """, t)

    def switch_location(self, name):
        self.driver.execute_script("""
            var tags = document.querySelectorAll('[class*="tab"], [class*="tag"]');
            for (var i = 0; i < tags.length; i++) {
                if ((tags[i].textContent || '').trim().indexOf(arguments[0]) !== -1) {
                    tags[i].click(); return;
                }
            }
        """, name)
        self._wait_loading_gone(5)
        self.wait_vue_stable()

    def click_add(self):
        self._wait_loading_gone(5)
        self.wait_vue_stable()
        self._js_click('新增报告单')
        self.wait_vue_stable()
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(self.DIALOG))

    def is_dialog_visible(self):
        try:
            return self.driver.find_element(*self.DIALOG).is_displayed()
        except Exception:
            return False

    def get_row_count(self):
        try:
            return sum(1 for r in self.driver.find_elements(By.CSS_SELECTOR, 'table tbody tr, .report-table tbody tr') if r.is_displayed())
        except Exception:
            return 0
