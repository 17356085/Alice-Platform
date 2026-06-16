"""业务类型配置页面 Page Object

==== 页面概述 ====
  路径：生产管理 → 业务类型配置
  路由：#/production/business-type-config
  功能：CRUD 管理生产业务类型 — 搜索区 + 表格 + 新增/编辑弹窗(17字段)

==== 定位策略 ====
  1. placeholder 定位搜索区输入框
  2. XPath 文本匹配按钮
  3. 弹窗内按 label 文本定位表单项
"""
import logging
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class BusinessTypeConfigPage(BasePage):
    """业务类型配置页面"""

    # ══════════════════════════════════════════════════════════════════
    #  搜索区
    # ══════════════════════════════════════════════════════════════════
    INPUT_PLAN_PARAM = (By.CSS_SELECTOR, 'input[placeholder="请输入计划参数"]')
    INPUT_FACTORY = (By.CSS_SELECTOR, 'input[placeholder="请输入工厂编码"]')
    INPUT_MATERIAL = (By.CSS_SELECTOR, 'input[placeholder="请输入物料编码"]')
    SELECT_BIZ_TYPE = (
        By.XPATH,
        '//label[contains(.,"业务类型")]/following-sibling::div//input',
    )

    BTN_SEARCH = (By.XPATH, '//button[contains(.,"搜索")]')
    BTN_RESET = (By.XPATH, '//button[contains(.,"重置")]')
    BTN_ADD = (By.XPATH, '//button[contains(.,"新增")]')
    BTN_DELETE = (By.XPATH, '//button[contains(.,"删除")]')  # 页面级删除（多选后启用）

    # ══════════════════════════════════════════════════════════════════
    #  表格
    # ══════════════════════════════════════════════════════════════════
    TABLE_ROWS = (By.CSS_SELECTOR, '.el-table__body-wrapper tbody tr.el-table__row')
    TABLE_HEADERS = (By.CSS_SELECTOR, '.el-table__header-wrapper th .cell')
    TABLE_CHECKBOX = (By.CSS_SELECTOR, '.el-table__header-wrapper .el-checkbox')
    PAGINATION_TOTAL = (By.CSS_SELECTOR, '.el-pagination__total')

    # ══════════════════════════════════════════════════════════════════
    #  弹窗（新增 / 编辑共用）
    # ══════════════════════════════════════════════════════════════════
    DIALOG = (By.CSS_SELECTOR, '.el-dialog:not([style*="display: none"])')
    DIALOG_TITLE = (By.CSS_SELECTOR, '.el-dialog:not([style*="display: none"]) .el-dialog__title')
    DIALOG_CONFIRM = (
        By.XPATH,
        '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
        '//button[contains(.,"确")]',
    )
    DIALOG_CANCEL = (
        By.XPATH,
        '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
        '//button[contains(.,"取")]',
    )

    # 弹窗字段 — 按 label 定位 input
    _DIALOG_FIELD_XPATH = (
        '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
        '//label[contains(.,"{label}")]/following-sibling::div//input'
    )

    # ══════════════════════════════════════════════════════════════════
    #  页面身份标记
    # ══════════════════════════════════════════════════════════════════
    _PAGE_IDENTITY_MARKERS = [
        'input[placeholder="请输入计划参数"]',
        'input[placeholder="请输入物料编码"]',
    ]

    def _is_on_page(self):
        """验证当前页面是否为业务类型配置"""
        return self.driver.execute_script("""
            var markers = arguments[0];
            for (var i = 0; i < markers.length; i++) {
                var el = document.querySelector(markers[i]);
                if (el && el.offsetParent !== null) return true;
            }
            return false;
        """, self._PAGE_IDENTITY_MARKERS)

    # ══════════════════════════════════════════════════════════════════
    #  导航
    # ══════════════════════════════════════════════════════════════════
    def navigate_to_page(self):
        """导航到业务类型配置页面"""
        max_retries = 2
        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.warning("身份验证失败（第%d次），重试…", attempt)
                self.driver.refresh()
                self.wait_page_ready()
                self.wait_vue_stable()

            try:
                self.navigate_to("生产管理", "业务类型配置")
            except Exception as exc:
                logger.warning("SidebarNavigator 异常: %s，hash 直跳", exc)
                self.driver.execute_script(
                    "window.location.hash = '#/production/business-type-config';"
                )
                self.wait_page_ready()
                self.wait_vue_stable()

            if self._is_on_page():
                logger.info("业务类型配置页面就绪（第%d次尝试）", attempt + 1)
                self.wait_vue_stable()
                return self

        raise TimeoutException("业务类型配置导航失败")

    # ══════════════════════════════════════════════════════════════════
    #  搜索操作
    # ══════════════════════════════════════════════════════════════════
    def search(self, plan_param=None, factory=None, material=None):
        """执行搜索"""
        if plan_param is not None:
            inp = self.find(self.INPUT_PLAN_PARAM)
            inp.clear()
            inp.send_keys(plan_param)
        if factory is not None:
            inp = self.find(self.INPUT_FACTORY)
            inp.clear()
            inp.send_keys(factory)
        if material is not None:
            inp = self.find(self.INPUT_MATERIAL)
            inp.clear()
            inp.send_keys(material)
        self.click(self.BTN_SEARCH)
        self.wait_vue_stable()
        return self

    def click_reset(self):
        """点击重置"""
        logger.info("点击重置")
        self.click(self.BTN_RESET)
        self.wait_vue_stable()
        return self

    # ══════════════════════════════════════════════════════════════════
    #  表格操作
    # ══════════════════════════════════════════════════════════════════
    def get_table_headers(self):
        """获取表头文本列表"""
        headers = self.find_all(self.TABLE_HEADERS)
        return [h.text.strip() for h in headers if h.text.strip()]

    def get_row_count(self):
        """获取表格行数"""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return len(rows)

    def get_pagination_total(self):
        """获取分页总数"""
        try:
            el = self.find(self.PAGINATION_TOTAL)
            return el.text.strip()
        except Exception:
            return ""

    def get_cell_text(self, row_index, col_index):
        """获取指定单元格文本"""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        if row_index >= len(rows):
            return None
        cells = rows[row_index].find_elements(By.CSS_SELECTOR, 'td .cell')
        if col_index >= len(cells):
            return None
        return cells[col_index].text.strip()

    # ══════════════════════════════════════════════════════════════════
    #  复选框操作
    # ══════════════════════════════════════════════════════════════════
    def select_row(self, row_index=0):
        """勾选指定行"""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        checkbox = rows[row_index].find_element(By.CSS_SELECTOR, '.el-checkbox')
        self.driver.execute_script("arguments[0].click();", checkbox)
        self.wait_vue_stable()
        return self

    def is_batch_delete_enabled(self):
        """页面级删除按钮是否可用"""
        try:
            el = self.find(self.BTN_DELETE, timeout=2)
            return "is-disabled" not in (el.get_attribute("class") or "")
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════
    #  弹窗操作
    # ══════════════════════════════════════════════════════════════════
    def click_add(self):
        """点击新增按钮"""
        logger.info("点击新增")
        self._js_click_by_text("新增")
        self._wait_dialog_open()
        return self

    def _wait_dialog_open(self, timeout=10):
        """等待弹窗出现"""
        self.wait_until_visible(self.DIALOG, timeout=timeout)
        self.wait_vue_stable()
        return self

    def wait_dialog_closed(self, timeout=10):
        """等待弹窗关闭"""
        self.wait_until_gone(self.DIALOG, timeout=timeout)
        return self

    def get_dialog_title(self):
        """获取弹窗标题"""
        el = self.find(self.DIALOG_TITLE)
        return el.text.strip()

    def fill_dialog_field(self, label, value):
        """填写弹窗中指定 label 的字段"""
        xpath = self._DIALOG_FIELD_XPATH.format(label=label)
        inp = self.find((By.XPATH, xpath))
        inp.clear()
        inp.send_keys(value)
        return self

    def click_dialog_confirm(self):
        """点击弹窗确定"""
        logger.info("点击弹窗确定")
        self.click(self.DIALOG_CONFIRM)
        self.wait_dialog_closed()
        return self

    def click_dialog_cancel(self):
        """点击弹窗取消"""
        logger.info("点击弹窗取消")
        self.click(self.DIALOG_CANCEL)
        self.wait_dialog_closed()
        return self

    def close_dialog_by_x(self):
        """通过 × 关闭弹窗"""
        try:
            dialog = self.find(self.DIALOG)
            close_btn = dialog.find_element(By.CSS_SELECTOR, ".el-dialog__headerbtn")
            close_btn.click()
        except Exception:
            pass
        self.wait_dialog_closed()
        return self

    # ══════════════════════════════════════════════════════════════════
    #  行级操作
    # ══════════════════════════════════════════════════════════════════
    def click_row_edit(self, row_index=0):
        """点击指定行的编辑按钮"""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        edit_btns = rows[row_index].find_elements(
            By.XPATH, './/button[contains(.,"编辑")]'
        )
        if edit_btns:
            self.driver.execute_script("arguments[0].click();", edit_btns[0])
        self._wait_dialog_open()
        return self

    def click_row_delete(self, row_index=0):
        """点击指定行的删除按钮"""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        del_btns = rows[row_index].find_elements(
            By.XPATH, './/button[contains(.,"删除")]'
        )
        if del_btns:
            self.driver.execute_script("arguments[0].click();", del_btns[0])
        self.wait_vue_stable()
        return self

    # ══════════════════════════════════════════════════════════════════
    #  内部辅助
    # ══════════════════════════════════════════════════════════════════
    def _js_click_by_text(self, text):
        """用 JS 查找并点击匹配文本的按钮"""
        script = """
            var buttons = document.querySelectorAll('button, .el-button');
            for (var i = 0; i < buttons.length; i++) {
                var b = buttons[i];
                var btnText = (b.innerText || b.textContent || '').trim();
                if (btnText.indexOf(arguments[0]) >= 0) {
                    if (b.offsetParent !== null && !b.classList.contains('is-disabled')) {
                        b.click();
                        return {clicked: true, text: btnText, index: i};
                    }
                }
            }
            return {clicked: false};
        """
        result = self.driver.execute_script(script, text)
        if result and result.get('clicked'):
            logger.info("JS点击成功: '%s'", result['text'])
        else:
            logger.warning("JS点击未找到匹配按钮: '%s'", text)
        self.wait_vue_stable()
        return self
