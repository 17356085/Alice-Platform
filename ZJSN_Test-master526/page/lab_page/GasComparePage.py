"""气体分析对比 Page Object

路由: #/lab/gas/compare
类型: 搜索表单 + 自定义对比表格（双位置选择 + 日期范围）
"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class GasComparePage(BasePage):
    """气体分析对比 — 双位置选择+日期筛选+对比表格"""

    PAGE_ROUTE = "#/lab/gas/compare"

    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    def navigate(self):
        logger.info("导航到 → 化验室取样 → 气体分析 → 气体分析对比")
        self.navigate_to("化验室取样", "气体分析对比")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        return self

    # ══════════════════════════════════════════════════════════════════
    #  搜索区
    # ══════════════════════════════════════════════════════════════════
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

    # ══════════════════════════════════════════════════════════════════
    #  页面内容
    # ══════════════════════════════════════════════════════════════════
    def is_page_loaded(self):
        self.wait_vue_stable()
        self._wait_loading_gone(timeout=10)
        # 检测：有搜索表单 + (有表格 或 空状态)
        has_date_inputs = self.driver.execute_script("""
            return !!document.querySelector('input[placeholder*="开始日期"]');
        """)
        has_table_or_msg = self.driver.execute_script("""
            return !!(document.querySelector('table') ||
                      document.querySelector('.el-table__empty-text') ||
                      document.querySelector('[class*="empty"]'));
        """)
        return bool(has_date_inputs) and bool(has_table_or_msg)

    def get_table_row_count(self):
        try:
            rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            return sum(1 for r in rows if r.is_displayed())
        except Exception:
            return 0
