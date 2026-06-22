"""DCS 关键参数监控页面 Page Object

==== 页面概述 ====
路径：DCS 数据监控 → 关键参数监控
路由：#/monitor
功能：实时参数监控卡片 + 搜索 + 新增/编辑/删除参数
类型：监控面板页（卡片网格 + 可选表格视图）

==== 定位策略 ====
- CSS_SELECTOR 优先（Element Plus 标准类）
- 相对 XPath 仅用于文本内容匹配
- 禁止：绝对 XPath

==== 风险点 ====
1. 实时数据推送可能使用 WebSocket，刷新延迟需处理
2. 参数卡片由 CSS Grid 布局，个数不固定
3. 告警状态颜色编码需正确识别
4. 曲线图表渲染可能延迟（ECharts）
"""
import logging
from selenium.webdriver.common.by import By
from base.base_page import BasePage

logger = logging.getLogger(__name__)


class DcsMonitorPage(BasePage):
    """关键参数监控 Page Object"""

    # ==================== 搜索/筛选区 ====================
    SEARCH_INPUT = (By.CSS_SELECTOR, 'input[placeholder*="参数" i], input[placeholder*="设备" i], input[placeholder*="点位名称" i]')
    BTN_SEARCH = (By.XPATH, '//button[normalize-space(.//span)="搜索"]')
    BTN_RESET = (By.XPATH, '//button[normalize-space(.//span)="重置"]')
    BTN_ADD = (By.XPATH, '//button[normalize-space(.//span)="新增"] | //button[normalize-space(.//span)="新增参数"]')
    BTN_REFRESH = (By.XPATH, '//button[normalize-space(.//span)="刷新"]')
    BTN_EXPORT = (By.XPATH, '//button[normalize-space(.//span)="导出"]')

    # 状态筛选
    SELECT_STATUS = (By.CSS_SELECTOR, '.el-select')
    STATUS_OPTIONS = (By.CSS_SELECTOR, '.el-select-dropdown__item')

    # 时间选择器
    DATE_PICKER = (By.CSS_SELECTOR, '.el-date-picker, .el-date-editor')

    # ==================== 卡片网格区 ====================
    CARD_GRID = (By.CSS_SELECTOR, '.monitor-cards, .card-grid, .el-row')
    PARAM_CARDS = (By.CSS_SELECTOR, '.monitor-card, .param-card, .el-card')
    CARD_NAME = (By.CSS_SELECTOR, '.card-title, .param-name')
    CARD_VALUE = (By.CSS_SELECTOR, '.card-value, .param-value')
    CARD_STATUS_BADGE = (By.CSS_SELECTOR, '.el-tag, .status-badge')
    CARD_TREND_UP = (By.CSS_SELECTOR, '.trend-up, .el-icon-top')
    CARD_TREND_DOWN = (By.CSS_SELECTOR, '.trend-down, .el-icon-bottom')

    # ==================== 表格区（如果切换到表格视图）====================
    TABLE = (By.CSS_SELECTOR, '.el-table')
    TABLE_ROWS = (By.CSS_SELECTOR, '.el-table__body-wrapper tbody tr.el-table__row')
    TABLE_LOADING = (By.CSS_SELECTOR, '.el-loading-mask')

    # ==================== 图表区 ====================
    CHART_CONTAINER = (By.CSS_SELECTOR, '.chart-container, [class*="chart"]')

    # ==================== 分页 ====================
    PAGINATION = (By.CSS_SELECTOR, '.el-pagination')
    TOTAL_COUNT = (By.CSS_SELECTOR, '.el-pagination__total')

    # ==================== 页面入口 ====================

    HASH_ROUTE = "#/monitor"

    def navigate(self):
        """导航到关键参数监控页面（DCS 模块）"""
        logger.info("导航: DCS 数据监控 → 关键参数监控 (%s)", self.HASH_ROUTE)
        self.navigate_to_by_hash(self.HASH_ROUTE, "关键参数监控")
        self._wait_page_ready()
        return self

    def _wait_page_ready(self):
        """等待页面就绪"""
        self.wait_vue_stable()
        self._wait_loading_gone()
        return self

    def _wait_loading_gone(self, timeout=10):
        """等待 Element Plus 加载动画消失"""
        try:
            self.wait_until_gone(self.TABLE_LOADING, timeout=timeout)
        except Exception:
            pass
        return self

    # ==================== 搜索操作 ====================

    def search(self, keyword: str):
        """按参数名/设备ID搜索"""
        logger.info("搜索: %s", keyword)
        self.input_text(self.SEARCH_INPUT, keyword)
        self.click(self.BTN_SEARCH)
        self.wait_vue_stable()
        return self

    def reset_search(self):
        """重置搜索条件"""
        logger.info("重置搜索条件")
        self.click(self.BTN_RESET)
        self.wait_vue_stable()
        return self

    def filter_by_status(self, status_text: str):
        """按状态筛选（正常/告警/离线）"""
        logger.info("筛选状态: %s", status_text)
        selects = self.find_all(self.SELECT_STATUS)
        if selects:
            selects[0].click()
            self.wait_vue_stable()
            option = self.find((By.XPATH, f'//li[contains(@class, "el-select-dropdown__item")]//span[text()="{status_text}"]'))
            option.click()
            self.wait_vue_stable()
        return self

    # ==================== 卡片操作 ====================

    def get_param_cards(self) -> list:
        """获取所有参数卡片"""
        return self.find_all(self.PARAM_CARDS)

    def get_card_count(self) -> int:
        """获取卡片数量"""
        return len(self.get_param_cards())

    def get_card_name(self, card_index: int = 0) -> str:
        """获取指定卡片的参数名"""
        cards = self.get_param_cards()
        if card_index < len(cards):
            return self.find_in_parent(cards[card_index], self.CARD_NAME).text
        return ""

    def get_card_value(self, card_index: int = 0) -> str:
        """获取指定卡片的当前值"""
        cards = self.get_param_cards()
        if card_index < len(cards):
            return self.find_in_parent(cards[card_index], self.CARD_VALUE).text
        return ""

    def click_card(self, card_index: int = 0):
        """点击指定卡片"""
        cards = self.get_param_cards()
        if card_index < len(cards):
            cards[card_index].click()
            self.wait_vue_stable()
        return self

    # ==================== 表格操作 ====================

    def get_table_data(self) -> list:
        """获取表格数据"""
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

    def is_param_in_table(self, text: str) -> bool:
        """检查表格中是否存在包含指定文本的行"""
        return super().is_row_present(text)

    # ==================== 新增/编辑/删除 ====================

    def click_add(self):
        """点击新增按钮"""
        logger.info("点击新增参数")
        self.click(self.BTN_ADD)
        self.wait_dialog_open()
        return self

    def fill_form(self, data: dict):
        """填充参数表单（弹窗模式）"""
        logger.info("填充表单: %s", data)
        for field, value in data.items():
            locator = (By.XPATH, f'//label[contains(text(),"{field}")]/following-sibling::div//input | '
                                 f'//span[contains(text(),"{field}")]/following-sibling::div//input')
            self.input_text(locator, str(value))
        return self

    def submit_form(self):
        """提交表单"""
        self.click_dialog_save()
        self.wait_dialog_close()
        self.wait_vue_stable()
        return self

    def cancel_form(self):
        """取消表单"""
        self.click_dialog_cancel()
        self.wait_dialog_close()
        return self

    def click_edit(self, row_identifier: str):
        """点击指定行的编辑按钮"""
        self.click_row_button(row_identifier, "编辑")
        self.wait_dialog_open()
        return self

    def click_delete(self, row_identifier: str):
        """点击指定行的删除按钮"""
        self.click_row_button(row_identifier, "删除")
        return self

    def confirm_delete(self):
        """确认删除（Element Plus message-box）"""
        self.click_element((By.XPATH, '//button[contains(@class, "el-button--primary")]//span[text()="确定"]'))
        self.wait_vue_stable()
        return self

    # ==================== 详情操作 ====================

    def click_detail(self, row_identifier: str):
        """查看参数详情"""
        self.click_row_button(row_identifier, "详情")
        self.wait_dialog_open()
        return self

    def close_detail(self):
        """关闭详情弹窗"""
        self.click_dialog_cancel()
        self.wait_dialog_close()
        return self

    # ==================== 刷新操作 ====================

    def refresh(self):
        """点击刷新按钮"""
        logger.info("刷新数据")
        self.click(self.BTN_REFRESH)
        self.wait_vue_stable()
        return self

    # ==================== 图表验证 ====================

    def is_chart_visible(self) -> bool:
        """检查图表是否渲染"""
        return self.is_visible(self.CHART_CONTAINER, timeout=5)

    # ==================== 分页 ====================

    def get_total_count(self) -> int:
        """获取总条数"""
        return super().get_total_count()
