"""DCS 上传日志页面 Page Object

==== 页面概述 ====
路径：DCS 数据监控 → 上传日志
路由：#/upload-log
功能：数据上传日志查询 — 按时间/设备/状态筛选、查看详情、重试失败上传
类型：日志列表页（筛选 + 统计卡片）

==== 自检报告 ====
[PASS] 继承 BasePage — class UploadLogPage(BasePage):
[PASS] 无绝对 XPath — grep '//*[@id' ==> 无输出
[PASS] 无 time.sleep — grep 'time.sleep' ==> 无输出
[PASS] 有 navigate() — def navigate 存在
"""
import logging
import time
from selenium.webdriver.common.by import By
from base.base_page import BasePage

logger = logging.getLogger(__name__)


class UploadLogPage(BasePage):
    """上传日志 Page Object"""

    # ==================== 时间/筛选区 ====================
    DATE_PICKER_START = (By.CSS_SELECTOR, '.el-date-editor input:first-of-type')
    DATE_PICKER_END = (By.CSS_SELECTOR, '.el-date-editor input:last-of-type')
    SELECT_DEVICE = (By.CSS_SELECTOR, '.el-select')
    SELECT_STATUS = (By.CSS_SELECTOR, '.el-select:nth-of-type(2), .status-filter .el-select')
    SEARCH_INPUT = (By.CSS_SELECTOR, 'input[placeholder*="点位名称" i], input[placeholder*="错误" i]')
    BTN_SEARCH = (By.XPATH, '//button[normalize-space(.//span)="搜索"]')
    BTN_RESET = (By.XPATH, '//button[normalize-space(.//span)="重置"]')

    # ==================== 统计卡片 ====================
    STAT_CARDS = (By.CSS_SELECTOR, '.stat-card, .el-statistic, .summary-card')
    STAT_TOTAL = (By.CSS_SELECTOR, '.stat-total .el-statistic__content, .total-count')
    STAT_SUCCESS = (By.CSS_SELECTOR, '.stat-success .el-statistic__content, .success-count')
    STAT_FAIL = (By.CSS_SELECTOR, '.stat-fail .el-statistic__content, .fail-count')
    STAT_ABNORMAL = (By.CSS_SELECTOR, '.stat-abnormal .el-statistic__content, .abnormal-count')

    # ==================== 操作按钮 ====================
    BTN_EXPORT = (By.XPATH, '//button[normalize-space(.//span)="导出"] | //button[.//span[text()="导出日志"]]')
    BTN_REFRESH = (By.XPATH, '//button[normalize-space(.//span)="刷新"]')
    BTN_CLEAR = (By.XPATH, '//button[.//span[text()="清空"]] | //button[.//span[text()="清空日志"]]')

    # ==================== 表格 ====================
    TABLE = (By.CSS_SELECTOR, '.el-table')
    TABLE_ROWS = (By.CSS_SELECTOR, '.el-table__body-wrapper tbody tr.el-table__row')
    TABLE_LOADING = (By.CSS_SELECTOR, '.el-loading-mask')
    TABLE_EMPTY = (By.CSS_SELECTOR, '.el-table__empty-text')

    # ==================== 分页 ====================
    PAGINATION = (By.CSS_SELECTOR, '.el-pagination')
    TOTAL_COUNT = (By.CSS_SELECTOR, '.el-pagination__total')

    # ==================== 详情弹窗 ====================
    DETAIL_DIALOG = BasePage.DIALOG
    DETAIL_CLOSE_BTN = BasePage.DIALOG_CANCEL

    # ==================== 页面入口 ====================

    HASH_ROUTE = "#/upload-log"

    def navigate(self):
        """导航到上传日志页面"""
        logger.info("导航: DCS 数据监控 → 上传日志 (%s)", self.HASH_ROUTE)
        self.navigate_to_by_hash(self.HASH_ROUTE, "上传日志")
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

    # ==================== 搜索/筛选 ====================

    def search(self, keyword: str):
        """搜索日志（按错误信息/点位ID）"""
        logger.info("搜索日志: %s", keyword)
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

    def set_date_range(self, start_date: str, end_date: str):
        """设置时间范围"""
        logger.info("设置日期: %s ~ %s", start_date, end_date)
        self.input_text(self.DATE_PICKER_START, start_date)
        self.input_text(self.DATE_PICKER_END, end_date)
        self.wait_vue_stable()
        return self

    def filter_by_status(self, status_text: str):
        """按状态筛选（成功/失败/超时/异常）"""
        logger.info("筛选状态: %s", status_text)
        selects = self.find_all(self.SELECT_STATUS)
        if selects:
            selects[-1].click()
            self.wait_vue_stable()
            option = (By.XPATH,
                      f'//li[contains(@class, "el-select-dropdown__item")]//span[text()="{status_text}"]')
            self.click(option)
            self.wait_vue_stable()
            self._wait_loading_gone()
        return self

    def filter_by_device(self, device_name: str):
        """按设备筛选"""
        logger.info("筛选设备: %s", device_name)
        selects = self.find_all(self.SELECT_DEVICE)
        if selects:
            selects[0].click()
            self.wait_vue_stable()
            option = (By.XPATH,
                      f'//li[contains(@class, "el-select-dropdown__item")]//span[text()="{device_name}"]')
            self.click(option)
            self.wait_vue_stable()
            self._wait_loading_gone()
        return self

    def click_query(self):
        """点击查询按钮"""
        self.click(self.BTN_SEARCH)
        self.wait_vue_stable()
        self._wait_loading_gone()
        return self

    # ==================== 统计卡片 ====================

    def get_stat_total(self) -> str:
        """获取上传总数"""
        total = self.find(self.STAT_TOTAL)
        return total.text if total else "0"

    def get_stat_success(self) -> str:
        """获取成功数"""
        el = self.find(self.STAT_SUCCESS)
        return el.text if el else "0"

    def get_stat_fail(self) -> str:
        """获取失败数"""
        el = self.find(self.STAT_FAIL)
        return el.text if el else "0"

    def get_stat_abnormal(self) -> str:
        """获取异常数"""
        el = self.find(self.STAT_ABNORMAL)
        return el.text if el else "0"

    # ==================== 表格数据 ====================

    def get_table_data(self) -> list:
        """获取表格所有行数据"""
        self.wait_until_visible(self.TABLE)
        rows = self.find_all(self.TABLE_ROWS)
        data = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            data.append([cell.text for cell in cells])
        return data

    def get_row_count(self) -> int:
        """获取表格行数"""
        return super().get_table_row_count()

    def is_log_in_table(self, text: str) -> bool:
        """检查表格中是否包含指定文本"""
        return super().is_row_present(text)

    # ==================== 查看详情 ====================

    def click_detail(self, row_identifier: str):
        """查看指定行的日志详情"""
        logger.info("查看详情: %s", row_identifier)
        self.click_row_button(row_identifier, "详情")
        self.wait_dialog_open()
        return self

    def close_detail(self):
        """关闭详情弹窗"""
        self.click(self.DETAIL_CLOSE_BTN)
        self.wait_dialog_close()
        return self

    def get_detail_content(self) -> str:
        """获取详情弹窗内容"""
        body = self.find((By.CSS_SELECTOR, '.el-dialog__body'))
        return body.text if body else ""

    # ==================== 重试操作 ====================

    def retry_upload(self, row_identifier: str):
        """重试失败的上传"""
        logger.info("重试上传: %s", row_identifier)
        self.click_row_button(row_identifier, "重试")
        self.wait_vue_stable()
        return self

    # ==================== 导出 ====================

    def click_export(self):
        """导出日志"""
        logger.info("导出日志")
        self.click(self.BTN_EXPORT)
        self.wait_vue_stable()
        return self

    # ==================== 清空日志 ====================

    def click_clear(self):
        """清空日志"""
        logger.info("清空日志")
        self.click(self.BTN_CLEAR)
        return self

    def confirm_clear(self):
        """确认清空（双重确认）"""
        self.click((By.XPATH, '//button[contains(@class, "el-button--primary")]//span[text()="确定"]'))
        self.wait_vue_stable()
        return self

    # ==================== 分页 ====================

    def get_total_count(self) -> int:
        """获取总条数"""
        return super().get_total_count()

    def go_to_next_page(self):
        self.click_next_page()
        self._wait_loading_gone()
        return self

    def go_to_prev_page(self):
        self.click_prev_page()
        self._wait_loading_gone()
        return self
