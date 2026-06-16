"""储罐监控管理页面 Page Object

注意：本页面使用自定义 UI 组件（非 Element Plus），
BasePage 中的 DIALOG/TOAST/TABLE_ROWS 等通用定位器不适用。
"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class TankMonitorPage(BasePage):
    """储罐监控管理页面 — 自定义 UI 框架"""

    # ══════════════════════════════════════════════════════════════════
    #  导航
    # ══════════════════════════════════════════════════════════════════

    def navigate(self):
        """导航到储罐监控管理 — 唯一入口"""
        logger.info("导航到 → 储罐管理 → 储罐监控管理")
        self.navigate_to("储罐管理", "储罐监控管理")
        self.wait_page_ready(timeout=15)
        self.wait_vue_stable()
        return self

    # ══════════════════════════════════════════════════════════════════
    #  统计卡片
    # ══════════════════════════════════════════════════════════════════

    STAT_CARDS = (By.CSS_SELECTOR, ".stats-cards .stat-card")
    STAT_VALUE = (By.CSS_SELECTOR, ".stat-card .value")

    def get_stat_card_count(self):
        """获取统计卡片总数"""
        cards = self.find_all(self.STAT_CARDS)
        return len(cards)

    def get_stat_values(self):
        """获取所有统计卡片的值
        Returns:
            dict: {总数: N, 正常运行: N, 检修维护: N, 报警储罐: N}
        """
        labels_text = ["储罐总数", "正常运行", "检修维护", "报警储罐"]
        values = {}
        for label in labels_text:
            try:
                xpath = f'//div[contains(@class,"stat-card")][.//*[contains(text(),"{label}")]]//*[contains(@class,"value")]'
                val = self.get_text((By.XPATH, xpath), timeout=3)
                values[label] = val
            except Exception:
                values[label] = ""
        return values

    # ══════════════════════════════════════════════════════════════════
    #  搜索区
    # ══════════════════════════════════════════════════════════════════

    SEARCH_INPUT = (By.CSS_SELECTOR, "input.filter-input")
    SEARCH_BTN = (By.CSS_SELECTOR, "button.btn.btn-primary")
    RESET_BTN = (By.XPATH, '//button[contains(.,"重置")]')
    ADD_BTN = (By.XPATH, '//button[contains(.,"新增储罐")]')
    IMPORT_BTN = (By.XPATH, '//button[contains(.,"导入")]')
    EXPORT_BTN = (By.XPATH, '//button[contains(.,"导出")]')

    def search(self, keyword):
        """输入搜索关键词并点击查询"""
        self.input_text(self.SEARCH_INPUT, keyword)
        self.click(self.SEARCH_BTN)
        self.wait_vue_stable()
        return self

    def reset_search(self):
        """点击重置按钮"""
        self.click(self.RESET_BTN)
        self.wait_vue_stable()
        return self

    # ══════════════════════════════════════════════════════════════════
    #  表格
    # ══════════════════════════════════════════════════════════════════

    TABLE = (By.CSS_SELECTOR, "table.data-table")
    TABLE_HEADERS = (By.CSS_SELECTOR, "table.data-table thead tr th")
    TABLE_ROWS = (By.CSS_SELECTOR, "table.data-table tbody tr")
    TABLE_BODY = (By.CSS_SELECTOR, "table.data-table tbody")
    TABLE_BODY_TEXT = (By.CSS_SELECTOR, "table.data-table tbody")
    TABLE_EMPTY = (By.CSS_SELECTOR, "table.data-table .empty-cell")

    def get_table_headers_text(self):
        """获取表格所有列标题"""
        headers = self.find_all(self.TABLE_HEADERS)
        return [h.text.strip() for h in headers if h.text.strip()]

    def get_table_row_count(self):
        """获取表格行数"""
        return len(self.find_all(self.TABLE_ROWS))

    def get_cell(self, row_index, col_index):
        """获取指定单元格文本（1-based索引）"""
        try:
            rows = self.find_all(self.TABLE_ROWS)
            if row_index <= len(rows):
                cells = rows[row_index - 1].find_elements(By.TAG_NAME, "td")
                if col_index <= len(cells):
                    return cells[col_index - 1].text.strip()
            return ""
        except Exception:
            return ""

    def is_table_empty(self):
        """判断表格是否为空"""
        try:
            if self.is_visible(self.TABLE_EMPTY, timeout=2):
                return True
        except Exception:
            pass
        # 兜底：检查 tbody 中是否包含"暂无数据"
        try:
            body_text = self.get_text(self.TABLE_BODY_TEXT, timeout=1)
            if "暂无数据" in body_text:
                return True
        except Exception:
            pass
        return self.get_table_row_count() == 0

    def click_view(self, row_index=1):
        """点击某行的查看按钮"""
        self.click_row_button_by_index(row_index, "查看")
        return self

    def click_history(self, row_index=1):
        """点击某行的历史数据按钮"""
        self.click_row_button_by_index(row_index, "历史数据")
        return self

    def click_edit(self, row_index=1):
        """点击某行的编辑按钮"""
        self.click_row_button_by_index(row_index, "编辑")
        return self

    def click_row_button_by_index(self, row_index, button_text):
        """点击指定行的操作按钮"""
        rows = self.find_all(self.TABLE_ROWS)
        if row_index <= len(rows):
            btns = rows[row_index - 1].find_elements(By.TAG_NAME, "button")
            for btn in btns:
                if button_text in (btn.text or "").strip():
                    self._js_click_el(btn)
                    self.wait_vue_stable()
                    return
        raise Exception(f"未在行{row_index}找到按钮[{button_text}]")

    # ══════════════════════════════════════════════════════════════════
    #  分页
    # ══════════════════════════════════════════════════════════════════

    PAGE_BTNS = (By.CSS_SELECTOR, "button.page-btn")

    def get_current_page(self):
        """获取当前页码"""
        active = self.driver.find_elements(By.CSS_SELECTOR, "button.page-btn.active")
        return int(active[0].text.strip()) if active else 1

    def click_page(self, page_num):
        """点击指定页码"""
        btns = self.find_all(self.PAGE_BTNS)
        for btn in btns:
            if btn.text.strip() == str(page_num):
                self._js_click_el(btn)
                self.wait_vue_stable()
                return self
        return self

    # ══════════════════════════════════════════════════════════════════
    #  弹窗（新增储罐 / 编辑 / 查看详情）
    #  ✅ DOM 捕获确认: el-dialog tank-monitor-dialog (Element Plus)
    #  2026-06-14 实地验证: 9 个 el-form-item, el-button 保存/取消
    # ══════════════════════════════════════════════════════════════════

    DIALOG = (By.CSS_SELECTOR, ".el-dialog.tank-monitor-dialog:not([style*='display: none'])")
    DIALOG_TITLE = (By.CSS_SELECTOR, ".el-dialog.tank-monitor-dialog .el-dialog__title")
    DIALOG_CLOSE = (By.CSS_SELECTOR, ".el-dialog.tank-monitor-dialog .el-dialog__headerbtn")

    DIALOG_CONFIRM = (By.XPATH, '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[contains(@class,"el-button--primary")]')
    DIALOG_CANCEL = (By.XPATH, '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[contains(@class,"el-button")][not(contains(@class,"el-button--primary"))]')

    # 弹窗表单字段 label 常量（DOM 捕获确认，按 label 文本定位）
    FIELD_LABEL_TANK_NUMBER = "储罐编号"       # required, el-input, placeholder="如：V-101"
    FIELD_LABEL_TANK_NAME = "储罐名称"         # required, el-input, placeholder="请输入储罐名称"
    FIELD_LABEL_TANK_TYPE = "储罐类型"         # required, el-select
    FIELD_LABEL_MEDIUM_TYPE = "介质类型"       # required, el-select
    FIELD_LABEL_CAPACITY = "设计容量"          # required, el-input, placeholder="如：5000"
    FIELD_LABEL_AREA = "所属区域"              # optional, el-select
    FIELD_LABEL_COMMISSION_DATE = "投用日期"   # optional, el-input (date)
    FIELD_LABEL_CHECK_DATE = "检验日期"        # optional, el-input (date)
    FIELD_LABEL_REMARK = "备注"                # optional, el-textarea

    REQUIRED_FIELDS = [
        FIELD_LABEL_TANK_NUMBER, FIELD_LABEL_TANK_NAME, FIELD_LABEL_TANK_TYPE,
        FIELD_LABEL_MEDIUM_TYPE, FIELD_LABEL_CAPACITY,
    ]
    ALL_DIALOG_FIELDS = REQUIRED_FIELDS + [
        FIELD_LABEL_AREA, FIELD_LABEL_COMMISSION_DATE, FIELD_LABEL_CHECK_DATE, FIELD_LABEL_REMARK,
    ]

    def wait_dialog_visible(self, timeout=10):
        """等待弹窗出现"""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.DIALOG)
            )
        except TimeoutException:
            return None

    def is_dialog_open(self):
        """判断弹窗是否打开"""
        return self.is_visible(self.DIALOG, timeout=2)

    def close_dialog(self):
        """关闭弹窗（优先 X 按钮，兜底点取消）"""
        try:
            self.click(self.DIALOG_CLOSE)
            self.wait_vue_stable()
        except Exception:
            try:
                self.click(self.DIALOG_CANCEL)
                self.wait_vue_stable()
            except Exception:
                pass
        return self

    # ── 使用 BasePage 标签定位方法（el-form-item label 匹配）──

    def fill_dialog_input_by_label(self, label_text, value):
        """按 label 文本填充弹窗输入框（复用 BasePage._get_dialog_form_item + fill_dialog_input）"""
        self.fill_dialog_input(label_text, value)
        return self

    def select_dialog_dropdown_by_label(self, label_text, option_text):
        """按 label 文本选择弹窗下拉选项"""
        self.select_dialog_dropdown(label_text, option_text)
        return self

    def fill_add_dialog(self, tank_number, tank_name, tank_type, medium_type, capacity,
                        area=None, commission_date=None, check_date=None, remark=None):
        """一次性填写新增弹窗的所有字段"""
        self.fill_dialog_input(self.FIELD_LABEL_TANK_NUMBER, tank_number)
        self.fill_dialog_input(self.FIELD_LABEL_TANK_NAME, tank_name)
        self.select_dialog_dropdown(self.FIELD_LABEL_TANK_TYPE, tank_type)
        self.select_dialog_dropdown(self.FIELD_LABEL_MEDIUM_TYPE, medium_type)
        self.fill_dialog_input(self.FIELD_LABEL_CAPACITY, capacity)
        if area:
            self.select_dialog_dropdown(self.FIELD_LABEL_AREA, area)
        if commission_date:
            self.fill_dialog_input(self.FIELD_LABEL_COMMISSION_DATE, commission_date)
        if check_date:
            self.fill_dialog_input(self.FIELD_LABEL_CHECK_DATE, check_date)
        if remark:
            self.fill_dialog_input(self.FIELD_LABEL_REMARK, remark)
        return self

    def click_dialog_confirm(self):
        """点击弹窗确定/保存按钮（JS 直点，绕过遮挡）"""
        result = self.driver.execute_script("""
            var dialogs = document.querySelectorAll(
                '.el-dialog:not([style*="display: none"]), .dialog:not([style*="display: none"])'
            );
            for (var i = dialogs.length - 1; i >= 0; i--) {
                var btns = dialogs[i].querySelectorAll('button');
                for (var j = 0; j < btns.length; j++) {
                    var t = btns[j].textContent.trim();
                    if (t === '确定' || t === '保存' || t === '保 存' || t === '确 定' ||
                        btns[j].className.indexOf('el-button--primary') >= 0 ||
                        btns[j].className.indexOf('btn-success') >= 0 ||
                        btns[j].className.indexOf('btn-primary') >= 0) {
                        btns[j].click();
                        return 'clicked:' + t;
                    }
                }
            }
            return 'not_found';
        """)
        if result and not result.startswith('clicked'):
            # JS 兜底失败，回退到 Selenium click
            self.click(self.DIALOG_CONFIRM)
        self.wait_vue_stable()
        return self

    def click_dialog_cancel(self):
        """点击弹窗取消按钮"""
        self.click(self.DIALOG_CANCEL)
        self.wait_vue_stable()
        return self

    def get_toast_text(self, timeout=5):
        """获取操作提示消息（Element Plus el-message）"""
        try:
            return self.get_toast(timeout=timeout)
        except Exception:
            return ""

    # ══════════════════════════════════════════════════════════════════
    #  导入弹窗（Element Plus el-upload 组件）
    # ══════════════════════════════════════════════════════════════════

    IMPORT_FILE_INPUT = (By.CSS_SELECTOR, ".el-upload input[type='file']")
    IMPORT_START_BTN = (By.XPATH, '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[contains(@class,"el-button--primary") and contains(.,"导入")]')
    IMPORT_RESULT_AREA = (By.CSS_SELECTOR, ".el-dialog .import-result, .el-dialog [class*='result']")

    def click_import_open(self):
        """点击导入按钮并等待弹窗出现"""
        self.click(self.IMPORT_BTN)
        return self.wait_dialog_visible(timeout=10)

    def upload_import_file(self, file_path):
        """上传导入文件（通过 el-upload input[type=file]）"""
        file_input = self.driver.find_element(*self.IMPORT_FILE_INPUT)
        file_input.send_keys(file_path)
        self.wait_vue_stable()
        return self

    def click_start_import(self):
        """点击导入弹窗中的'开始导入'按钮"""
        self.click(self.IMPORT_START_BTN)
        self.wait_vue_stable()
        return self

    def wait_import_result(self, timeout=30):
        """等待导入结果显示"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.IMPORT_RESULT_AREA)
            )
            return self.get_text(self.IMPORT_RESULT_AREA, timeout=3)
        except TimeoutException:
            return ""

    def import_data(self, file_path):
        """完整导入流程: 打开弹窗 → 上传 → 开始导入 → 等待结果"""
        self.click_import_open()
        self.upload_import_file(file_path)
        self.click_start_import()
        result = self.wait_import_result()
        return result
