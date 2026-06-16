"""环保入库页面 Page Object

8列表格，选择危废品（弹窗嵌套）。
审批链：危废出库审批链 (chenqian → admin)
"""
import logging
from selenium.webdriver.common.by import By
from base.base_page import BasePage

logger = logging.getLogger(__name__)


class HazardInOrderPage(BasePage):

    # ── 搜索区 ──────────────────────────────────────────────
    FILTER_STATUS = (
        By.XPATH,
        '(//div[contains(@class,"wh-filter-toolbar")]//div[contains(@class,"el-select__wrapper")])[1]',
    )
    FILTER_HANDLER = (By.XPATH, '//input[@placeholder="请输入经办人"]')
    FILTER_DATE = (By.XPATH, '//input[@placeholder="选择日期"]')
    BTN_QUERY = (By.XPATH, '//button[contains(.,"查询")]')
    BTN_RESET = (By.XPATH, '//button[contains(.,"重置")]')

    # ── 工具栏 ──────────────────────────────────────────────
    BTN_ADD = (By.XPATH, '//button[contains(.,"新增入库")]')

    # ── 行内操作 ────────────────────────────────────────────
    BTN_VIEW = (By.XPATH, '//button[contains(.,"查看")]')
    BTN_EDIT = (By.XPATH, '//button[contains(.,"编辑")]')

    # ── 弹窗A（新增入库） ───────────────────────────────────
    FIELD_IN_TIME = (By.XPATH, '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//input[@placeholder="选择日期"]')
    FIELD_HANDLER = (By.XPATH, '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//input[@placeholder="请输入经办人"]')
    BTN_SELECT_WASTE = (By.XPATH, '//button[contains(.,"选择危废品")]')
    BTN_SUBMIT = (By.XPATH, '//button[contains(.,"提交申请")]')

    # ── 导航 ────────────────────────────────────────────────
    def navigate(self):
        self.navigate_to("库管管理", "环保危废管理", "入库")
        self._wait_page_ready()

    def _wait_page_ready(self):
        self.wait_vue_stable()
        self._wait_loading_gone()

    # ── 新增入库完整流程 ────────────────────────────────────
    def click_add(self):
        self.click(self.BTN_ADD)
        self.wait_dialog_open()

    def fill_in_order(self, handler_name):
        """填写入库单基本信息（弹窗A内）"""
        self.input_text(self.FIELD_HANDLER, handler_name)
        # 日期由用户选择或使用默认值

    def click_select_waste(self):
        """点击选择危废品，打开弹窗B"""
        self.click(self.BTN_SELECT_WASTE)
        # 等待第二个弹窗出现
        self.wait_vue_stable(timeout=5)

    def submit_application(self):
        """点击提交申请"""
        self.click(self.BTN_SUBMIT)
        self.wait_for_toast_text()

    # ── 行内操作 ────────────────────────────────────────────
    def click_view_first(self):
        self.click(self.BTN_VIEW)
        self.wait_dialog_open()

    def search_by_handler(self, name):
        self.input_text(self.FILTER_HANDLER, name)
        self.click(self.BTN_QUERY)
        self.wait_vue_stable()
