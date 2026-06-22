"""DCS 点位配置页面 Page Object

==== 页面概述 ====
路径：DCS 数据监控 → 点位配置
路由：#/point-config
功能：点位CRUD管理 — 新增/编辑/删除点位、告警规则配置、批量导入导出
类型：列表页（CRUD + 条件表单）

==== 自检报告 ====
[PASS] 继承 BasePage — class PointConfigPage(BasePage):
[PASS] 无绝对 XPath — grep '//*[@id' ==> 无输出
[PASS] 无 time.sleep — grep 'time.sleep' ==> 无输出
[PASS] 有 navigate() — def navigate 存在
"""
import logging
import time
from selenium.webdriver.common.by import By
from base.base_page import BasePage

logger = logging.getLogger(__name__)


class PointConfigPage(BasePage):
    """点位配置 Page Object"""

    # ==================== 搜索/筛选区 ====================
    SEARCH_INPUT = (By.CSS_SELECTOR, 'input[placeholder*="点位" i], input[placeholder*="名称" i], input[placeholder*="点位名称" i]')
    BTN_SEARCH = (By.XPATH, '//button[normalize-space(.//span)="搜索"]')
    BTN_RESET = (By.XPATH, '//button[normalize-space(.//span)="重置"]')
    SELECT_TYPE = (By.CSS_SELECTOR, '.search-area .el-select, .filter-bar .el-select')

    # ==================== 操作按钮 ====================
    BTN_ADD = (By.XPATH, '//button[normalize-space(.//span)="新增"] | //button[normalize-space(.//span)="新增点位"]')
    BTN_IMPORT = (By.XPATH, '//button[normalize-space(.//span)="导入"]')
    BTN_EXPORT = (By.XPATH, '//button[normalize-space(.//span)="导出"]')
    BTN_BATCH_DELETE = (By.XPATH, '//button[.//span[text()="批量删除"]]')
    BTN_REFRESH = (By.XPATH, '//button[normalize-space(.//span)="刷新"]')

    # ==================== 表格 ====================
    TABLE = (By.CSS_SELECTOR, '.el-table')
    TABLE_ROWS = (By.CSS_SELECTOR, '.el-table__body-wrapper tbody tr.el-table__row')
    TABLE_LOADING = (By.CSS_SELECTOR, '.el-loading-mask')
    TABLE_CHECKBOX = (By.CSS_SELECTOR, '.el-checkbox__input')

    # ==================== 分页 ====================
    PAGINATION = (By.CSS_SELECTOR, '.el-pagination')
    TOTAL_COUNT = (By.CSS_SELECTOR, '.el-pagination__total')

    # ==================== 弹窗表单 ====================
    # 使用 BasePage DIALOG / DIALOG_SAVE / DIALOG_CANCEL
    DIALOG_INPUT_NAME = (By.CSS_SELECTOR, '.el-dialog input[placeholder*="名称" i]')
    DIALOG_INPUT_ID = (By.CSS_SELECTOR, '.el-dialog input[placeholder*="ID" i]')
    DIALOG_SELECT_TYPE = (By.CSS_SELECTOR, '.el-dialog .el-select:nth-of-type(1)')
    DIALOG_SELECT_DEVICE = (By.CSS_SELECTOR, '.el-dialog .el-select:nth-of-type(2)')
    DIALOG_INPUT_PERIOD = (By.CSS_SELECTOR, '.el-dialog input[placeholder*="周期" i], .el-dialog input[placeholder*="ms" i]')
    DIALOG_INPUT_UNIT = (By.CSS_SELECTOR, '.el-dialog input[placeholder*="单位" i]')
    DIALOG_SELECT_ALARM = (By.CSS_SELECTOR, '.el-dialog .el-select:nth-of-type(3)')
    DIALOG_INPUT_ALARM_HIGH = (By.CSS_SELECTOR, '.el-dialog input[placeholder*="上限" i]')
    DIALOG_INPUT_ALARM_LOW = (By.CSS_SELECTOR, '.el-dialog input[placeholder*="下限" i]')
    DIALOG_SWITCH_ENABLE = (By.CSS_SELECTOR, '.el-dialog .el-switch')

    # ==================== 页面入口 ====================

    HASH_ROUTE = "#/point-config"

    def navigate(self):
        """导航到点位配置页面"""
        logger.info("导航: DCS 数据监控 → 点位配置 (%s)", self.HASH_ROUTE)
        self.navigate_to_by_hash(self.HASH_ROUTE, "点位配置")
        self._wait_page_ready()
        return self

    def _wait_page_ready(self):
        """等待页面就绪"""
        self.wait_vue_stable()
        self._wait_loading_gone()
        return self

    def _wait_loading_gone(self, timeout=10):
        """等待加载动画消失"""
        try:
            self.wait_until_gone(self.TABLE_LOADING, timeout=timeout)
        except Exception:
            pass
        return self

    # ==================== 搜索操作 ====================

    def search(self, keyword: str):
        """按点位ID/名称搜索"""
        logger.info("搜索点位: %s", keyword)
        self.input_text(self.SEARCH_INPUT, keyword)
        self.click(self.BTN_SEARCH)
        self.wait_vue_stable()
        self._wait_loading_gone()
        return self

    def reset_search(self):
        """重置搜索条件"""
        logger.info("重置搜索条件")
        self.click(self.BTN_RESET)
        self.wait_vue_stable()
        return self

    def filter_by_type(self, type_text: str):
        """按类型筛选"""
        logger.info("筛选类型: %s", type_text)
        selects = self.find_all(self.SELECT_TYPE)
        if selects:
            selects[0].click()
            self.wait_vue_stable()
            option = (By.XPATH,
                      f'//li[contains(@class, "el-select-dropdown__item")]//span[text()="{type_text}"]')
            self.click(option)
            self.wait_vue_stable()
            self._wait_loading_gone()
        return self

    # ==================== 表格数据 ====================

    def get_table_data(self) -> list:
        """获取表格所有行数据"""
        self.wait_element_visible(self.TABLE)
        rows = self.find_all(self.TABLE_ROWS)
        data = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            data.append([cell.text for cell in cells])
        return data

    def get_row_count(self) -> int:
        """获取表格行数"""
        return super().get_table_row_count()

    def is_point_in_table(self, text: str) -> bool:
        """检查表格中是否存在指定文本"""
        return super().is_row_present(text)

    def select_row(self, row_identifier: str):
        """勾选指定行"""
        logger.info("勾选行: %s", row_identifier)
        row = self.find((By.XPATH,
                         f'//tr[contains(@class, "el-table__row")]//td[contains(text(),"{row_identifier}")]/..'))
        checkbox = row.find_element(*self.TABLE_CHECKBOX)
        checkbox.click()
        self.wait_vue_stable()
        return self

    # ==================== CRUD 操作 ====================

    def click_add(self):
        """点击新增按钮"""
        logger.info("点击新增点位")
        self.click(self.BTN_ADD)
        self.wait_dialog_open()
        return self

    def click_edit(self, row_identifier: str):
        """点击指定行的编辑按钮"""
        logger.info("编辑点位: %s", row_identifier)
        self.click_row_button(row_identifier, "编辑")
        self.wait_dialog_open()
        return self

    def click_delete(self, row_identifier: str):
        """点击指定行的删除按钮"""
        logger.info("删除点位: %s", row_identifier)
        self.click_row_button(row_identifier, "删除")
        return self

    def confirm_delete(self):
        """确认删除"""
        self.click((By.XPATH, '//button[contains(@class, "el-button--primary")]//span[text()="确定"]'))
        self.wait_vue_stable()
        return self

    # ==================== 弹窗表单 ====================

    def fill_form(self, data: dict):
        """填充点位表单"""
        logger.info("填充表单: %s", data)
        if "名称" in data or "name" in data:
            name = data.get("名称") or data.get("name")
            self.input_text(self.DIALOG_INPUT_NAME, str(name))
        if "类型" in data or "type" in data:
            type_val = data.get("类型") or data.get("type")
            self.click(self.DIALOG_SELECT_TYPE)
            option = (By.XPATH,
                      f'//li[contains(@class, "el-select-dropdown__item")]//span[text()="{type_val}"]')
            self.click(option)
            self.wait_vue_stable()
        if "单位" in data or "unit" in data:
            self.input_text(self.DIALOG_INPUT_UNIT, str(data.get("单位") or data.get("unit")))
        if "采集周期" in data or "period" in data:
            self.input_text(self.DIALOG_INPUT_PERIOD, str(data.get("采集周期") or data.get("period")))
        return self

    def fill_name(self, name: str):
        """填写点位名称"""
        self.input_text(self.DIALOG_INPUT_NAME, name)
        return self

    def fill_point_id(self, point_id: str):
        """填写点位ID"""
        self.input_text(self.DIALOG_INPUT_ID, point_id)
        return self

    def select_type(self, type_text: str):
        """选择点位类型"""
        self.click(self.DIALOG_SELECT_TYPE)
        option = (By.XPATH,
                  f'//li[contains(@class, "el-select-dropdown__item")]//span[text()="{type_text}"]')
        self.click(option)
        self.wait_vue_stable()
        return self

    def select_alarm_rule(self, rule_type: str):
        """选择告警规则（无/上限/下限/双限）"""
        self.click(self.DIALOG_SELECT_ALARM)
        option = (By.XPATH,
                  f'//li[contains(@class, "el-select-dropdown__item")]//span[text()="{rule_type}"]')
        self.click(option)
        self.wait_vue_stable()
        return self

    def fill_alarm_high(self, value: str):
        """填写告警上限值"""
        self.input_text(self.DIALOG_INPUT_ALARM_HIGH, value)
        return self

    def fill_alarm_low(self, value: str):
        """填写告警下限值"""
        self.input_text(self.DIALOG_INPUT_ALARM_LOW, value)
        return self

    def toggle_enable(self):
        """切换启用/禁用开关"""
        self.click(self.DIALOG_SWITCH_ENABLE)
        self.wait_vue_stable()
        return self

    def submit_form(self):
        """提交弹窗表单"""
        self.click_dialog_save()
        self.wait_dialog_close()
        self.wait_vue_stable()
        self._wait_loading_gone()
        return self

    def cancel_form(self):
        """取消弹窗表单"""
        self.click_dialog_cancel()
        self.wait_dialog_close()
        return self

    # ==================== 批量操作 ====================

    def click_batch_delete(self):
        """点击批量删除"""
        logger.info("点击批量删除")
        self.click(self.BTN_BATCH_DELETE)
        return self

    # ==================== 分页 ====================

    def get_total_count(self) -> int:
        """获取总条数"""
        return super().get_total_count()

    def go_to_next_page(self):
        """下一页"""
        self.click_next_page()
        self._wait_loading_gone()
        return self

    def go_to_prev_page(self):
        """上一页"""
        self.click_prev_page()
        self._wait_loading_gone()
        return self
