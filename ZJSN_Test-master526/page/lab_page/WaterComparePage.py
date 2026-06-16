"""水质分析对比 Page Object

路由: #/lab/water/compare
类型: 搜索表单 + 自定义对比表格（结构与 GasComparePage 相同）
"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class WaterComparePage(BasePage):
    """水质分析对比 — 双位置选择+日期筛选+对比表格"""

    PAGE_ROUTE = "#/lab/water/compare"

    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    def navigate(self):
        logger.info("导航到 → 化验室取样 → 水质分析 → 水质分析对比")
        self.navigate_to("化验室取样", "水质分析对比")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        return self

    def set_start_date(self, date_str):
        el = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder*="开始日期"]')))
        el.clear()
        el.send_keys(date_str)
        logger.info("已输入开始日期: %s", date_str)

    def set_end_date(self, date_str):
        el = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder*="结束日期"]')))
        el.clear()
        el.send_keys(date_str)
        logger.info("已输入结束日期: %s", date_str)

    def click_query(self):
        self._js_click_search_or_reset("查询")
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        logger.info("已点击查询按钮")

    def click_reset(self):
        self._js_click_search_or_reset("重置")
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        logger.info("已点击重置按钮")

    def _js_click_search_or_reset(self, text):
        self.driver.execute_script(f"""
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {{
                if ((btns[i].textContent || '').trim().indexOf('{text}') !== -1) {{
                    btns[i].scrollIntoView({{block:'center'}});
                    btns[i].click();
                    return;
                }}
            }}
        """)

    def is_page_loaded(self):
        self.wait_vue_stable()
        self._wait_loading_gone(timeout=10)
        has_date = self.driver.execute_script(
            "return !!document.querySelector('input[placeholder*=\"开始日期\"]');")
        has_content = self.driver.execute_script(
            "return !!(document.querySelector('table') || document.querySelector('[class*=\"empty\"]'));")
        return bool(has_date) and bool(has_content)

    def get_table_row_count(self):
        try:
            rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            return sum(1 for r in rows if r.is_displayed())
        except Exception:
            return 0
