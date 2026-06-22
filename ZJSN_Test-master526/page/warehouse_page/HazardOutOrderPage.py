"""环保危废出库 Page Object

模块: warehouse
页面: hazard-out-order
审批链: 危废出库审批链 (chenqian → admin)
表格列数: 6~12 列
核心交互: 新增出库（含选择危废品嵌套弹窗）、查看、搜索、删除
"""
import logging
import time

from selenium.webdriver.common.by import By
from base.base_page import BasePage

logger = logging.getLogger(__name__)


class HazardOutOrderPage(BasePage):
    """环保危废出库 Page Object"""

    # ── 搜索/筛选区 ──────────────────────────────────────────
    FILTER_HANDLER = (By.XPATH, "//input[@placeholder='请输入经办人']")
    FILTER_DATE = (By.XPATH, "//input[@placeholder='选择日期']")
    BTN_QUERY = (By.XPATH, "//button[contains(.,'查询')]")
    BTN_RESET = (By.XPATH, "//button[contains(.,'重置')]")

    # ── 工具栏 ──────────────────────────────────────────────
    BTN_ADD = (By.XPATH, "//button[contains(.,'新增出库')]")
    BTN_VIEW = (By.XPATH, "//button[contains(.,'查看')]")

    # ── 行内操作 ────────────────────────────────────────────
    BTN_DELETE = (By.XPATH, "//button[contains(.,'删除')]")

    # ── 导航 ────────────────────────────────────────────────
    def navigate(self) -> "HazardOutOrderPage":
        """导航到环保危废出库页面并等待加载完成。"""
        self.logger.info("导航到 [库管管理] > [环保危废管理] > [出库]")
        self.navigate_to("库管管理", "环保危废管理", "出库")
        self._wait_page_ready()
        self.logger.info("页面加载完成")
        return self

    def _wait_page_ready(self) -> None:
        """等待页面稳定状态。"""
        self.wait_vue_stable()
        self._wait_loading_gone()

    # ── 搜索与筛选 ──────────────────────────────────────────
    def search_by_handler(self, name: str) -> "HazardOutOrderPage":
        """按经办人姓名搜索。"""
        self.logger.info(f"按经办人搜索: {name}")
        self.clear_and_type(self.FILTER_HANDLER, name)
        self.click(self.BTN_QUERY)
        self.wait_vue_stable()
        return self

    def reset_search(self) -> "HazardOutOrderPage":
        """重置所有搜索条件。"""
        self.logger.info("重置搜索条件")
        self.click(self.BTN_RESET)
        self.wait_vue_stable()
        return self

    def click_search(self) -> "HazardOutOrderPage":
        """点击查询按钮并等待页面稳定。"""
        self.logger.info("点击查询按钮")
        self.click(self.BTN_QUERY)
        self.wait_vue_stable()
        return self

    # ── 新增出库 ────────────────────────────────────────────
    def click_add(self) -> "HazardOutOrderPage":
        """点击'新增出库'按钮，并等待弹窗完全打开。"""
        self.logger.info("点击 [新增出库] 按钮")
        self.click(self.BTN_ADD)
        self.wait_dialog_open()
        self.logger.info("新增出库弹窗已打开")
        return self

    def _fill_dialog_by_placeholder(self, placeholder_contains: str, value: str) -> None:
        """通过 placeholder 子串匹配弹窗内 input 并填充值（JS 事件驱动）。

        Args:
            placeholder_contains: placeholder 属性子串
            value: 要填充的值
        """
        self.logger.info(f"弹窗填充: placeholder含'{placeholder_contains}' = '{value}'")
        script = (
            "var dialogs = document.querySelectorAll('.el-dialog');"
            "for (var i = 0; i < dialogs.length; i++) {"
            "  if (dialogs[i].offsetParent !== null) {"
            "    var inputs = dialogs[i].querySelectorAll('input');"
            "    for (var j = 0; j < inputs.length; j++) {"
            "      var ph = inputs[j].getAttribute('placeholder') || '';"
            "      if (ph.indexOf(arguments[0]) !== -1) {"
            "        inputs[j].value = arguments[1];"
            "        inputs[j].dispatchEvent(new Event('input', {bubbles: true}));"
            "        inputs[j].dispatchEvent(new Event('change', {bubbles: true}));"
            "        return 'found';"
            "      }"
            "    }"
            "  }"
            "}"
            "return 'not_found';"
        )
        result = self.driver.execute_script(script, placeholder_contains, value)
        if result == 'not_found':
            self.logger.warning(f"未找到 placeholder 包含 '{placeholder_contains}' 的弹窗 input")
        time.sleep(0.3)

    def fill_out_order_handler(self, name: str) -> "HazardOutOrderPage":
        """在新增弹窗内填写经办人。"""
        self.logger.info(f"填写经办人: {name}")
        self._fill_dialog_by_placeholder("经办人", name)
        return self

    # ── 行内操作 ────────────────────────────────────────────
    def click_view_first(self) -> "HazardOutOrderPage":
        """点击第一行的'查看'按钮。"""
        self.logger.info("点击表格第一行的 [查看] 按钮")
        self.click(self.BTN_VIEW)
        self.wait_dialog_open()
        self.logger.info("查看详情弹窗已打开")
        return self

    def delete_by_handler(self, name: str) -> "HazardOutOrderPage":
        """按经办人搜索后删除第一条匹配记录。

        Args:
            name: 经办人姓名
        """
        self.logger.info(f"删除经办人为 '{name}' 的出库记录")
        self.search_by_handler(name)
        try:
            self.click_row_button(name, "删除")
            self.confirm_message_box()
            self.logger.info(f"删除成功: {name}")
        except Exception as e:
            self.logger.warning(f"删除操作异常: {e}")
        return self

    # ── 页面数据获取 ────────────────────────────────────────
    def get_table_rows_count(self) -> int:
        """获取当前表格行数。"""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        count = len(rows)
        self.logger.info(f"当前表格行数: {count}")
        return count

    def get_handler_input_value(self) -> str:
        """获取经办人筛选输入框的当前值。"""
        value = self.driver.find_element(*self.FILTER_HANDLER).get_attribute("value")
        self.logger.info(f"经办人筛选字段值: '{value}'")
        return value
