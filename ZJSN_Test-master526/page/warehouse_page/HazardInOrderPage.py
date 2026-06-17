"""环保危废入库 Page Object

模块: warehouse
页面: hazard-in-order
审批链: 危废出库审批链 (chenqian → admin)
表格列数: 6~12 列
核心交互: 新增入库（含选择危废品嵌套弹窗）、查看、搜索
"""
import logging
from selenium.webdriver.common.by import By
from base.base_page import BasePage

logger = logging.getLogger(__name__)


class HazardInOrderPage(BasePage):

    # ── 搜索/筛选区 ──────────────────────────────────────────
    # 备选: 增加 data-testid 更稳定
    FILTER_STATUS = (By.CSS_SELECTOR, "[data-testid='filter-status'] .el-select__wrapper")
    FILTER_HANDLER = (By.CSS_SELECTOR, "input[placeholder='请输入经办人']")
    FILTER_DATE = (By.CSS_SELECTOR, "input[placeholder='选择日期']")
    BTN_QUERY = (By.CSS_SELECTOR, "button:has(span:text('查询'))")
    BTN_RESET = (By.CSS_SELECTOR, "button:has(span:text('重置'))")

    # ── 工具栏 ──────────────────────────────────────────────
    BTN_ADD = (By.CSS_SELECTOR, "button:has(span:text('新增入库'))")

    # ── 主数据表格 ───────────────────────────────────────────
    # 表格行和表头使用已由 BasePage 继承的通用定位器
    # TABLE_ROWS = BasePage.TABLE_ROWS
    # TABLe_HEADERS = (By.CSS_SELECTOR, ".el-table__header-wrapper th")

    # ── 行内操作 ────────────────────────────────────────────
    # 使用相对稳定的文本定位
    BTN_VIEW = (By.XPATH, "//button[contains(.,'查看')]")
    BTN_EDIT = (By.XPATH, "//button[contains(.,'编辑')]")

    # ── 弹窗A：新增入库 ─────────────────────────────────────
    # 定位器限定了可见弹窗内的元素
    FIELD_IN_TIME = (
        By.XPATH,
        "//div[contains(@class,'el-dialog') and not(contains(@style,'display: none'))]//input[@placeholder='选择日期']",
    )
    FIELD_HANDLER = (
        By.XPATH,
        "//div[contains(@class,'el-dialog') and not(contains(@style,'display: none'))]//input[@placeholder='请输入经办人']",
    )
    BTN_SELECT_WASTE = (By.XPATH, "//button[contains(.,'选择危废品')]")
    BTN_SUBMIT = (By.XPATH, "//button[contains(.,'提交申请')]")

    # ── 导航 ────────────────────────────────────────────────
    def navigate(self) -> "HazardInOrderPage":
        """导航到环保危废入库页面并等待加载完成。"""
        self.logger.info("导航到 [库管管理] > [环保危废管理] > [入库]")
        self.navigate_to("库管管理", "环保危废管理", "入库")
        self._wait_page_ready()
        self.logger.info("页面加载完成")
        return self

    def _wait_page_ready(self) -> None:
        """等待页面稳定状态。"""
        self.wait_vue_stable()
        self._wait_loading_gone()

    # ── 搜索与筛选 ──────────────────────────────────────────
    def search_by_handler(self, name: str) -> "HazardInOrderPage":
        """按经办人姓名搜索。

        Args:
            name: 经办人姓名
        """
        self.logger.info(f"按经办人搜索: {name}")
        self.clear_and_type(self.FILTER_HANDLER, name)
        self.click(self.BTN_QUERY)
        self.wait_vue_stable()
        return self

    def reset_search(self) -> "HazardInOrderPage":
        """重置所有搜索条件。"""
        self.logger.info("重置搜索条件")
        self.click(self.BTN_RESET)
        self.wait_vue_stable()
        return self

    # ── 新增入库 ────────────────────────────────────────────
    def click_add(self) -> "HazardInOrderPage":
        """点击'新增入库'按钮，并等待弹窗完全打开。"""
        self.logger.info("点击 [新增入库] 按钮")
        self.click(self.BTN_ADD)
        self.wait_dialog_open()
        self.logger.info("新增入库弹窗已打开")
        return self

    def fill_in_order(self, handler_name: str, date: str = None) -> "HazardInOrderPage":
        """在新增弹窗内填写入库单基本信息。

        Args:
            handler_name: 经办人姓名
            date: 入库日期（可选），格式如 '2024-01-15'
        """
        self.logger.info(f"填写入库单: 经办人={handler_name}, 日期={date}")
        self._wait_element_visible(self.FIELD_HANDLER)
        self.clear_and_type(self.FIELD_HANDLER, handler_name)
        if date:
            self._wait_element_visible(self.FIELD_IN_TIME)
            self.clear_and_type(self.FIELD_IN_TIME, date)
        return self

    def click_select_waste(self) -> "HazardInOrderPage":
        """点击'选择危废品'按钮，打开嵌套弹窗B。"""
        self.logger.info("点击 [选择危废品] 按钮")
        self.click(self.BTN_SELECT_WASTE)
        self.wait_vue_stable(timeout=5)
        self.logger.info("危废品选择弹窗已打开")
        return self

    def submit_application(self) -> "HazardInOrderPage":
        """在新增弹窗内点击'提交申请'按钮。"""
        self.logger.info("点击 [提交申请] 按钮")
        self.click(self.BTN_SUBMIT)
        self.wait_for_toast_text()
        self.logger.info("提交申请成功")
        return self

    def cancel_dialog(self) -> "HazardInOrderPage":
        """点击弹窗的取消按钮（从基类继承）。"""
        self.logger.info("点击弹窗取消按钮")
        self.click_dialog_cancel()
        self.wait_dialog_close()
        return self

    # ── 完整业务流程 ────────────────────────────────────────
    def create_and_submit_order(self, handler_name: str, date: str = None) -> "HazardInOrderPage":
        """完整流程: 点击新增 -> 填写表单 -> 选择危废品 -> 提交申请。

        Args:
            handler_name: 经办人姓名
            date: 入库日期（可选）
        """
        self.logger.info(f"开始创建并提交入库单，经办人: {handler_name}")
        self.click_add()
        self.fill_in_order(handler_name, date)
        # 注意: 此方法不自动处理“选择危废品”后的逻辑，只触发该操作
        # 需要后续测试脚本监听弹窗B的关闭或状态
        self.click_select_waste()
        # 模拟在弹窗B中选择了危废品后返回（此处简化，实际需要测试脚本处理）
        # 假设弹窗B会自动关闭或需要手动关闭
        # 场景复杂时，建议由测试脚本控制内嵌弹窗的交互
        self.submit_application()
        return self

    # ── 行内操作 ────────────────────────────────────────────
    def click_view_first(self) -> "HazardInOrderPage":
        """点击第一行的'查看'按钮。"""
        self.logger.info("点击表格第一行的 [查看] 按钮")
        self.click(self.BTN_VIEW)
        self.wait_dialog_open()
        self.logger.info("查看详情弹窗已打开")
        return self

    def click_edit_first(self) -> "HazardInOrderPage":
        """点击第一行的'编辑'按钮。"""
        self.logger.info("点击表格第一行的 [编辑] 按钮")
        self.click(self.BTN_EDIT)
        self.wait_dialog_open()
        self.logger.info("编辑弹窗已打开")
        return self

    # ── 页面数据获取 ────────────────────────────────────────
    def get_table_rows_count(self) -> int:
        """获取当前表格行数。"""
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        count = len(rows)
        self.logger.info(f"当前表格行数: {count}")
        return count

    def get_filter_handler_value(self) -> str:
        """获取经办人筛选输入框的当前值。"""
        value = self.driver.find_element(*self.FILTER_HANDLER).get_attribute("value")
        self.logger.info(f"经办人筛选字段值: '{value}'")
        return value