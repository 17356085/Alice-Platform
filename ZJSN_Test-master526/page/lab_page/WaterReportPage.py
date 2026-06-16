"""水质分析报告单 Page Object

路由: #/lab/water/report
类型: 搜索表单 + 自定义 report-table + 新增弹窗
参考: GasAnalysisReportPage（气体版已有成熟实现）
"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class WaterReportPage(BasePage):
    """水质分析报告单 — 取样位置标签栏 + 日期筛选 + 表格 + 新增弹窗"""

    PAGE_ROUTE = "#/lab/water/report"
    DIALOG = (By.CSS_SELECTOR, '.el-dialog:not([style*="display: none"])')

    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    def navigate(self):
        logger.info("导航到 → 化验室取样 → 水质分析 → 水质分析报告单")
        self.navigate_to("化验室取样", "水质分析报告单")
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
    #  新增
    # ══════════════════════════════════════════════════════════════════
    def click_add(self):
        """点击新增报告单"""
        self._wait_loading_gone(timeout=5)
        self.wait_vue_stable()
        clicked = self.driver.execute_script("""
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                if ((btns[i].textContent || '').trim().indexOf('新增报告单') !== -1) {
                    btns[i].click(); return true;
                }
            }
            return false;
        """)
        if not clicked:
            raise TimeoutException("未找到'新增报告单'按钮")
        logger.info("已点击新增报告单按钮")
        self.wait_vue_stable()
        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(self.DIALOG))
            logger.info("弹窗已打开")
        except TimeoutException:
            raise TimeoutException("点击新增报告单后未检测到弹窗")

    def _get_dialog(self):
        return WebDriverWait(self.driver, 4).until(EC.presence_of_element_located(self.DIALOG))

    def _find_field_in_dialog(self, label_keyword):
        dlg = self._get_dialog()
        el = self.driver.execute_script("""
            var dlg = arguments[0], keyword = arguments[1];
            var labels = dlg.querySelectorAll('.el-form-item__label');
            for (var i = 0; i < labels.length; i++) {
                if ((labels[i].textContent || '').trim().indexOf(keyword) !== -1) {
                    var fi = labels[i].closest('.el-form-item');
                    if (!fi) continue;
                    var inp = fi.querySelector('input.el-input__inner');
                    if (!inp) inp = fi.querySelector('input:not([type="hidden"]):not([readonly])');
                    if (!inp) inp = fi.querySelector('textarea');
                    if (!inp) inp = fi.querySelector('.el-select input');
                    if (inp) return inp;
                }
            }
            return null;
        """, dlg, label_keyword)
        if el is None:
            raise TimeoutException(f"未在弹窗内找到标签含'{label_keyword}'的表单字段")
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        return el

    def _clear_and_type(self, element, value):
        element.send_keys(Keys.CONTROL + "a")
        element.send_keys(Keys.DELETE)
        if value:
            element.send_keys(value)

    # 弹窗表单字段（根据 PAGE_CONTEXT: 检验员/复核员/日期/取样时间/取样位置/水质指标）
    def dialog_input_inspector(self, value):
        el = self._find_field_in_dialog("检验员")
        self._clear_and_type(el, value)
        logger.info("弹窗输入检验员: %s", value)

    def dialog_input_reviewer(self, value):
        el = self._find_field_in_dialog("复核员")
        self._clear_and_type(el, value)
        logger.info("弹窗输入复核员: %s", value)

    def dialog_confirm(self):
        dlg = self._get_dialog()
        self.driver.execute_script("""
            var dlg = arguments[0];
            var btns = dlg.querySelectorAll('button.el-button--primary');
            for (var i = 0; i < btns.length; i++) {
                if ((btns[i].textContent || '').trim().indexOf('取消') === -1) {
                    btns[i].click(); return;
                }
            }
        """, dlg)
        self._wait_loading_gone(timeout=3)
        self.wait_vue_stable()
        logger.info("已点击弹窗确认按钮")

    def dialog_cancel(self):
        dlg = self._get_dialog()
        self.driver.execute_script("""
            var dlg = arguments[0];
            var btns = dlg.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                if ((btns[i].textContent || '').trim().indexOf('取消') !== -1) {
                    btns[i].click(); return;
                }
            }
        """, dlg)
        self.wait_vue_stable()
        logger.info("已点击弹窗取消按钮")

    def is_dialog_open(self):
        try:
            return self.driver.find_element(*self.DIALOG).is_displayed()
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════
    #  页面内容
    # ══════════════════════════════════════════════════════════════════
    def is_page_loaded(self):
        self.wait_vue_stable()
        self._wait_loading_gone(timeout=10)
        has_search = self.driver.execute_script(
            "return !!document.querySelector('input[placeholder*=\"开始日期\"]');")
        return bool(has_search)

    def get_table_row_count(self):
        try:
            rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr, .report-table tbody tr")
            return sum(1 for r in rows if r.is_displayed())
        except Exception:
            return 0

    # ══════════════════════════════════════════════════════════════════
    #  Toast
    # ══════════════════════════════════════════════════════════════════
    def wait_for_toast_text(self, timeout=6):
        import time as _time
        deadline = _time.time() + timeout
        locators = [
            (By.XPATH, '(//*[contains(@class,"el-message__content") and normalize-space(.)!=""])[last()]'),
            (By.CSS_SELECTOR, ".el-message__content"),
        ]
        while _time.time() < deadline:
            for loc in locators:
                try:
                    els = self.driver.find_elements(*loc)
                    for el in els:
                        try:
                            if el.is_displayed():
                                t = (el.text or "").strip()
                                if t:
                                    return t
                        except Exception:
                            continue
                except Exception:
                    continue
            _time.sleep(0.3)
        return ""
