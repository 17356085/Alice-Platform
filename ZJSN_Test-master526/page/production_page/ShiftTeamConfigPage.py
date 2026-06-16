"""班次班组配置页面 Page Object

==== 页面概述 ====
  路径：生产管理 → 班次班组配置
  路由：#/production/shift-team-config
  功能：CRUD 管理工厂排班 — 搜索区 + 表格 + 新增/编辑弹窗

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


class ShiftTeamConfigPage(BasePage):
    """班次班组配置页面"""

    # ══════════════════════════════════════════════════════════════════
    #  搜索区
    # ══════════════════════════════════════════════════════════════════
    INPUT_FACTORY = (By.CSS_SELECTOR, 'input[placeholder="请输入工厂编码"]')
    INPUT_TEAM = (By.CSS_SELECTOR, 'input[placeholder="请输入班组"]')
    INPUT_SHIFT = (By.CSS_SELECTOR, 'input[placeholder="请输入班次"]')
    # 排班类型 — el-select（需要通过父级 .el-form-item 定位）
    SELECT_SCHEDULE_TYPE = (
        By.XPATH,
        '//label[contains(.,"排班类型")]/following-sibling::div//input',
    )

    BTN_SEARCH = (By.XPATH, '//button[contains(.,"搜索")]')
    BTN_RESET = (By.XPATH, '//button[contains(.,"重置")]')
    BTN_ADD = (By.XPATH, '//button[contains(.,"新增")]')

    # ══════════════════════════════════════════════════════════════════
    #  表格
    # ══════════════════════════════════════════════════════════════════
    TABLE = (By.CSS_SELECTOR, '.el-table')
    TABLE_ROWS = (By.CSS_SELECTOR, '.el-table__body-wrapper tbody tr.el-table__row')
    TABLE_HEADERS = (By.CSS_SELECTOR, '.el-table__header-wrapper th .cell')
    TABLE_EMPTY = (By.CSS_SELECTOR, '.el-empty')
    PAGINATION_TOTAL = (By.CSS_SELECTOR, '.el-pagination__total')

    # ══════════════════════════════════════════════════════════════════
    #  弹窗（新增 / 编辑共用）
    # ══════════════════════════════════════════════════════════════════
    DIALOG = (By.CSS_SELECTOR, '.el-dialog:not([style*="display: none"])')
    DIALOG_TITLE = (By.CSS_SELECTOR, '.el-dialog:not([style*="display: none"]) .el-dialog__title')
    DIALOG_CONFIRM = (By.XPATH, '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[contains(.,"确")]')
    DIALOG_CANCEL = (By.XPATH, '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[contains(.,"取")]')

    # 弹窗字段 — 按 label 定位 input
    _DIALOG_FIELD_XPATH = (
        '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
        '//label[contains(.,"{label}")]/following-sibling::div//input'
    )

    # ══════════════════════════════════════════════════════════════════
    #  页面身份标记
    # ══════════════════════════════════════════════════════════════════
    _PAGE_IDENTITY_MARKERS = [
        'input[placeholder="请输入工厂编码"]',
        'input[placeholder="请输入班组"]',
    ]

    def _is_on_page(self):
        """验证当前页面是否为班次班组配置"""
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
        """导航到班次班组配置页面"""
        max_retries = 2
        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.warning("身份验证失败（第%d次），重试…", attempt)
                self.driver.refresh()
                self.wait_page_ready()
                self.wait_vue_stable()

            try:
                self.navigate_to("生产管理", "班次班组配置")
            except Exception as exc:
                logger.warning("SidebarNavigator 异常: %s，hash 直跳", exc)
                self.driver.execute_script(
                    "window.location.hash = '#/production/shift-team-config';"
                )
                self.wait_page_ready()
                self.wait_vue_stable()

            if self._is_on_page():
                logger.info("班次班组配置页面就绪（第%d次尝试）", attempt + 1)
                self.wait_vue_stable()
                return self

        raise TimeoutException("班次班组配置导航失败")

    # ══════════════════════════════════════════════════════════════════
    #  搜索操作
    # ══════════════════════════════════════════════════════════════════
    def search(self, factory=None, team=None, shift=None):
        """执行搜索（可选参数）"""
        if factory is not None:
            inp = self.find(self.INPUT_FACTORY)
            inp.clear()
            inp.send_keys(factory)
        if team is not None:
            inp = self.find(self.INPUT_TEAM)
            inp.clear()
            inp.send_keys(team)
        if shift is not None:
            inp = self.find(self.INPUT_SHIFT)
            inp.clear()
            inp.send_keys(shift)
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
        """获取分页总数文本"""
        try:
            el = self.find(self.PAGINATION_TOTAL)
            return el.text.strip()
        except Exception:
            return ""

    def is_table_empty(self):
        """表格是否为空"""
        try:
            self.find(self.TABLE_EMPTY, timeout=3)
            return True
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════
    #  弹窗操作
    # ══════════════════════════════════════════════════════════════════
    def click_add(self):
        """点击新增按钮，打开弹窗"""
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
        """点击弹窗确定按钮"""
        logger.info("点击弹窗确定")
        self.click(self.DIALOG_CONFIRM)
        self.wait_dialog_closed()
        return self

    def click_dialog_cancel(self):
        """点击弹窗取消按钮"""
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
        edit_links = rows[row_index].find_elements(
            By.XPATH, './/button[contains(.,"编辑")]'
        )
        if edit_links:
            self.driver.execute_script("arguments[0].click();", edit_links[0])
        self._wait_dialog_open()
        return self

    def click_row_delete(self, row_index=0):
        """点击指定行的删除按钮"""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        del_links = rows[row_index].find_elements(
            By.XPATH, './/button[contains(.,"删除")]'
        )
        if del_links:
            self.driver.execute_script("arguments[0].click();", del_links[0])
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
