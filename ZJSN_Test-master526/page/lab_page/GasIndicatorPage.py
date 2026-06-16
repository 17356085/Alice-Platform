"""气体分析设计指标 Page Object

路由: #/lab/gas/indicator
类型: CRUD 表格 + 弹窗表单
对称页面: WaterIndicatorPage（水质版）
"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class GasIndicatorPage(BasePage):
    """气体分析设计指标 — 标准 CRUD 表格（无搜索表单，无分页）"""

    PAGE_ROUTE = "#/lab/gas/indicator"

    # ══════════════════════════════════════════════════════════════════
    #  弹窗定位器
    # ══════════════════════════════════════════════════════════════════
    DIALOG = (By.CSS_SELECTOR, '.el-dialog:not([style*="display: none"])')
    DIALOG_FALLBACK = (By.CSS_SELECTOR, '.el-drawer:not([style*="display: none"])')

    # ══════════════════════════════════════════════════════════════════
    #  表格
    # ══════════════════════════════════════════════════════════════════
    EMPTY_TEXT = (By.CSS_SELECTOR, ".el-table__empty-text")
    TABLE_ROWS = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr")

    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    # ══════════════════════════════════════════════════════════════════
    #  导航
    # ══════════════════════════════════════════════════════════════════
    def navigate(self):
        logger.info("导航到 → 化验室取样 → 气体分析设计指标")
        self.navigate_to("化验室取样", "气体分析设计指标")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        return self

    # ══════════════════════════════════════════════════════════════════
    #  新增
    # ══════════════════════════════════════════════════════════════════
    def click_add(self):
        """点击新增指标 — JS 文本搜索"""
        self._wait_loading_gone(timeout=5)
        self.wait_vue_stable()
        clicked = self.driver.execute_script("""
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                var txt = (btns[i].textContent || '').trim();
                if (txt.indexOf('新增指标') !== -1) {
                    btns[i].click(); return true;
                }
            }
            return false;
        """)
        if not clicked:
            raise TimeoutException("未找到'新增指标'按钮")
        logger.info("已点击新增指标按钮")
        self.wait_vue_stable()
        for loc in [self.DIALOG, self.DIALOG_FALLBACK]:
            try:
                WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(loc))
                logger.info("弹窗已打开")
                return
            except TimeoutException:
                continue
        raise TimeoutException("点击新增指标后未检测到弹窗")

    # ══════════════════════════════════════════════════════════════════
    #  弹窗表单（6个字段：指标名称/分类/单位/判断规则/阈值/备注）
    # ══════════════════════════════════════════════════════════════════
    def _get_dialog(self):
        for loc in [self.DIALOG, self.DIALOG_FALLBACK]:
            try:
                return WebDriverWait(self.driver, 4).until(EC.presence_of_element_located(loc))
            except TimeoutException:
                continue
        raise TimeoutException("未找到弹窗")

    def _find_field_in_dialog(self, label_keyword):
        dlg = self._get_dialog()
        el = self.driver.execute_script("""
            var dlg = arguments[0];
            var keyword = arguments[1];
            var labels = dlg.querySelectorAll('.el-form-item__label');
            for (var i = 0; i < labels.length; i++) {
                var text = (labels[i].textContent || '').trim();
                if (text.indexOf(keyword) !== -1) {
                    var formItem = labels[i].closest('.el-form-item');
                    if (!formItem) continue;
                    var input = formItem.querySelector('input.el-input__inner');
                    if (!input) input = formItem.querySelector('input:not([type="hidden"]):not([readonly])');
                    if (!input) input = formItem.querySelector('textarea');
                    if (input) return input;
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

    def dialog_input_name(self, value):
        el = self._find_field_in_dialog("指标名称")
        self._clear_and_type(el, value)
        logger.info("弹窗输入指标名称: %s", value)

    def dialog_input_category(self, value):
        el = self._find_field_in_dialog("指标分类")
        self._clear_and_type(el, value)
        logger.info("弹窗输入指标分类: %s", value)

    def dialog_input_unit(self, value):
        el = self._find_field_in_dialog("单位")
        self._clear_and_type(el, value)
        logger.info("弹窗输入单位: %s", value)

    def dialog_input_rule(self, value):
        el = self._find_field_in_dialog("判断规则")
        self._clear_and_type(el, value)
        logger.info("弹窗输入判断规则: %s", value)

    def dialog_input_threshold(self, value):
        el = self._find_field_in_dialog("阈值")
        self._clear_and_type(el, value)
        logger.info("弹窗输入阈值: %s", value)

    def dialog_input_remark(self, value):
        el = self._find_field_in_dialog("备注")
        self._clear_and_type(el, value)
        logger.info("弹窗输入备注: %s", value)

    def dialog_confirm(self):
        dlg = self._get_dialog()
        btn = self.driver.execute_script("""
            var dlg = arguments[0];
            var btns = dlg.querySelectorAll('button.el-button--primary');
            for (var i = 0; i < btns.length; i++) {
                var txt = (btns[i].textContent || '').trim();
                if (txt && txt.indexOf('取消') === -1) return btns[i];
            }
            if (btns.length > 0) return btns[0];
            return null;
        """, dlg)
        if btn:
            self.driver.execute_script("arguments[0].click();", btn)
        self._wait_loading_gone(timeout=3)
        self.wait_vue_stable()
        logger.info("已点击弹窗确认按钮")

    def dialog_cancel(self):
        dlg = self._get_dialog()
        btn = self.driver.execute_script("""
            var dlg = arguments[0];
            var btns = dlg.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                if ((btns[i].textContent || '').trim().indexOf('取消') !== -1) return btns[i];
            }
            return null;
        """, dlg)
        if btn:
            self.driver.execute_script("arguments[0].click();", btn)
        self.wait_vue_stable()
        logger.info("已点击弹窗取消按钮")

    def is_dialog_open(self):
        try:
            return self.driver.find_element(*self.DIALOG).is_displayed()
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════
    #  表格操作
    # ══════════════════════════════════════════════════════════════════
    def get_table_headers(self):
        self.wait_vue_stable()
        self._wait_loading_gone(timeout=5)
        headers = self.driver.execute_script("""
            return Array.from(
                document.querySelectorAll('.el-table__header-wrapper th .cell')
            ).map(function(el) { return el.textContent.trim(); }).filter(Boolean);
        """)
        return headers

    def get_table_row_count(self):
        self._wait_loading_gone(timeout=5)
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        count = 0
        for r in rows:
            try:
                if r.is_displayed():
                    count += 1
            except Exception:
                continue
        return count

    def get_empty_text(self):
        try:
            return (self.driver.find_element(*self.EMPTY_TEXT).text or "").strip()
        except Exception:
            return ""

    def get_column_data(self, col_index):
        self._wait_loading_gone(timeout=5)
        xpath = f'.//div[contains(@class,"el-table__body-wrapper")]//tbody/tr/td[{col_index}]//div[contains(@class,"cell")]'
        cells = self.driver.find_elements(By.XPATH, xpath)
        return [(c.text or "").strip().replace("\n", " ").strip() for c in cells if (c.text or "").strip()]

    def click_row_edit(self, row_index=1):
        self._wait_loading_gone(timeout=5)
        xpath = (
            f'(//div[contains(@class,"el-table__body-wrapper")]//tbody/tr)[{int(row_index)}]'
            f'//td[last()]//button[contains(.,"编辑")]'
        )
        btn = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.XPATH, xpath)))
        self.driver.execute_script("arguments[0].click();", btn)
        self.wait_vue_stable()
        logger.info("已点击第%s行编辑按钮", row_index)

    def click_row_delete(self, row_index=1):
        self._wait_loading_gone(timeout=5)
        xpath = (
            f'(//div[contains(@class,"el-table__body-wrapper")]//tbody/tr)[{int(row_index)}]'
            f'//td[last()]//button[contains(.,"删除")]'
        )
        btn = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.XPATH, xpath)))
        self.driver.execute_script("arguments[0].click();", btn)
        self.wait_vue_stable()
        logger.info("已点击第%s行删除按钮", row_index)

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
