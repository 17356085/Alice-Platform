"""设备管理页面 Page Object — 基于真实 HTML 结构

==== 页面组件 ====
  1. 统计卡片（4个 .stat-card，BEM命名）
  2. 搜索表单（.search-wrapper 内 el-form inline）
  3. 数据表格（.table-wrapper 内 el-table）
  4. 分页（el-pagination）

==== 定位策略 ====
  CSS_SELECTOR 优先（语义class + Element Plus 标准类）
  文本匹配使用相对 XPath 保底
"""
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class EquipmentPage(BasePage):
    """设备台账管理页面"""

    # ==================================================================
    #  统计卡片 — BEM 命名，CSS_SELECTOR 精准匹配
    #  注意：.stat-card 是 el-card 渲染后的 class，与 el-card 自身 class 合并
    # ==================================================================
    STAT_CARD = (By.CSS_SELECTOR, '.stat-card')
    # 使用 .stat-card__label 文字区分4张卡片（标签文字唯一且稳定）
    STAT_TOTAL = (
        By.XPATH,
        '//div[contains(@class,"stat-card")]'
        '[.//div[contains(@class,"stat-card__label") and normalize-space(.)="设备总数"]]'
        '//div[contains(@class,"stat-card__value")]',
    )
    STAT_RUNNING = (
        By.XPATH,
        '//div[contains(@class,"stat-card")]'
        '[.//div[contains(@class,"stat-card__label") and normalize-space(.)="正常运行"]]'
        '//div[contains(@class,"stat-card__value")]',
    )
    STAT_MAINTENANCE = (
        By.XPATH,
        '//div[contains(@class,"stat-card")]'
        '[.//div[contains(@class,"stat-card__label") and normalize-space(.)="维护中"]]'
        '//div[contains(@class,"stat-card__value")]',
    )
    STAT_STOPPED = (
        By.XPATH,
        '//div[contains(@class,"stat-card")]'
        '[.//div[contains(@class,"stat-card__label") and normalize-space(.)="已停用"]]'
        '//div[contains(@class,"stat-card__value")]',
    )
    STAT_LABELS = (By.CSS_SELECTOR, '.stat-card__label')

    # ==================================================================
    #  搜索区 — .search-wrapper 作用域限定
    # ==================================================================
    SEARCH_WRAPPER = (By.CSS_SELECTOR, '.search-wrapper')
    INPUT_KEYWORD = (
        By.CSS_SELECTOR,
        '.search-wrapper input[placeholder*="设备名称"], '
        '.search-wrapper .el-input__inner',
    )
    # 三个下拉框触发器（按位置区分，Element Plus 将 el-select 渲染为 .el-select）
    SELECT_UNIT_TRIGGER = (
        By.XPATH,
        '//div[contains(@class,"search-wrapper")]'
        '//div[contains(@class,"el-select")][.//input[contains(@placeholder,"装置")]]'
        '//span[contains(@class,"el-select__placeholder")]',
    )
    SELECT_TYPE_TRIGGER = (
        By.XPATH,
        '//div[contains(@class,"search-wrapper")]'
        '//div[contains(@class,"el-select")][.//input[contains(@placeholder,"类型")]]'
        '//span[contains(@class,"el-select__placeholder")]',
    )
    SELECT_STATUS_TRIGGER = (
        By.XPATH,
        '//div[contains(@class,"search-wrapper")]'
        '//div[contains(@class,"el-select")][.//input[contains(@placeholder,"状态")]]'
        '//span[contains(@class,"el-select__placeholder")]',
    )

    # 按钮 — 按 Element Plus type 区分
    BTN_SEARCH = (By.CSS_SELECTOR, '.search-wrapper .el-button--primary')
    BTN_RESET = (
        By.XPATH,
        '//div[contains(@class,"search-wrapper")]'
        '//button[contains(.,"重置")]',
    )
    BTN_ADD = (
        By.XPATH,
        '//div[contains(@class,"search-wrapper")]'
        '//button[contains(.,"新增")]',
    )
    BTN_IMPORT = (
        By.XPATH,
        '//div[contains(@class,"search-wrapper")]'
        '//button[contains(.,"导入")]',
    )
    BTN_EXPORT = (
        By.XPATH,
        '//div[contains(@class,"search-wrapper")]'
        '//button[contains(.,"导出")]',
    )

    # ==================================================================
    #  表格 — .table-wrapper 作用域限定
    # ==================================================================
    TABLE_WRAPPER = (By.CSS_SELECTOR, '.table-wrapper')
    TABLE_ROWS = (
        By.CSS_SELECTOR,
        '.table-wrapper .el-table__body-wrapper tbody tr.el-table__row',
    )
    TABLE_HEADER_CELLS = (
        By.CSS_SELECTOR,
        '.table-wrapper .el-table__header-wrapper th .cell',
    )
    TABLE_EMPTY = (By.CSS_SELECTOR, '.table-wrapper .el-table__empty-text')

    # 操作列按钮（相对 XPath，按文本匹配）
    ROW_BUTTON_VIEW = (
        By.XPATH,
        './/button[contains(.,"查看")]',
    )
    ROW_BUTTON_DATA = (
        By.XPATH,
        './/button[contains(.,"实时数据")]',
    )
    ROW_BUTTON_EDIT = (
        By.XPATH,
        './/button[contains(.,"编辑")]',
    )

    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    # ==================================================================
    #  导航
    # ==================================================================
    def navigate_to_equipment(self):
        """通过侧边栏导航到设备台账页面"""
        logger.info("导航到 → 设备管理 → 设备台账")
        self.navigate_to("设备管理", "设备台账")
        self._wait_page_ready()

    # ==================================================================
    #  页面就绪
    # ==================================================================
    def _wait_page_ready(self, timeout=25):
        """等待页面元素加载完成（统计卡片或表格出现即视为就绪）"""
        self.wait_page_ready(timeout=30)        # document.readyState == 'complete'
        self._wait_loading_gone(timeout)
        try:
            self.wait_stats_loaded(timeout=min(timeout, 12))
        except TimeoutException:
            logger.warning("统计卡片未在时间内加载，尝试等待表格")
        self._wait_table_ready(timeout=min(timeout, 10))

    def wait_stats_loaded(self, timeout=10):
        """等待统计卡片数字出现（DOM中有文本即就绪）"""
        WebDriverWait(self.driver, timeout).until(
            lambda d: any(
                (el.text or '').strip() != ''
                for el in d.find_elements(By.CSS_SELECTOR, '.stat-card__value')
            )
        )

    # ==================================================================
    #  统计卡片
    # ==================================================================
    def get_stat_total(self):
        return self.get_text(self.STAT_TOTAL)

    def get_stat_running(self):
        return self.get_text(self.STAT_RUNNING)

    def get_stat_maintenance(self):
        return self.get_text(self.STAT_MAINTENANCE)

    def get_stat_stopped(self):
        return self.get_text(self.STAT_STOPPED)

    def get_all_stats(self):
        """返回 4 张卡片统计数字"""
        return {
            'total': self.get_stat_total(),
            'running': self.get_stat_running(),
            'maintenance': self.get_stat_maintenance(),
            'stopped': self.get_stat_stopped(),
        }

    def get_stat_card_count(self):
        """返回统计卡片数量"""
        return len(self.find_all(self.STAT_CARD))

    # ==================================================================
    #  搜索区
    # ==================================================================
    def input_keyword(self, keyword):
        """输入设备名称/编号搜索"""
        self.input_text(self.INPUT_KEYWORD, keyword or '')

    def select_unit(self, unit_name):
        """选择所属装置下拉"""
        self._click_select_trigger(self.SELECT_UNIT_TRIGGER)
        self._select_option(unit_name)

    def select_type(self, type_name):
        """选择设备类型下拉"""
        self._click_select_trigger(self.SELECT_TYPE_TRIGGER)
        self._select_option(type_name)

    def select_status(self, status_name):
        """选择设备状态下拉"""
        self._click_select_trigger(self.SELECT_STATUS_TRIGGER)
        self._select_option(status_name)

    def click_search(self):
        """点击查询按钮"""
        self.click(self.BTN_SEARCH)
        self._wait_table_ready()

    def click_reset(self):
        """点击重置按钮"""
        self.click(self.BTN_RESET)
        self._wait_table_ready()

    def click_add(self):
        """点击新增设备按钮"""
        self.click(self.BTN_ADD)
        self.wait_dialog_open()

    def click_import(self):
        """点击导入按钮"""
        self.click(self.BTN_IMPORT)
        self.wait_dialog_open()

    def click_export(self):
        """点击导出按钮并确认"""
        self.click(self.BTN_EXPORT)
        try:
            self.confirm_message_box()
            return True
        except TimeoutException:
            return False

    # ==================================================================
    #  表格
    # ==================================================================
    def _wait_table_ready(self, timeout=10):
        """等待表格渲染完成"""
        self._wait_loading_gone(timeout)
        self.wait_vue_stable()

    def get_table_headers(self):
        """JS提取表格表头（含重试，应对Element Plus异步渲染）"""
        for attempt in range(6):
            try:
                self._wait_table_ready()
            except Exception:
                pass
            self.wait_vue_stable()
            headers = self.driver.execute_script("""
                return Array.from(
                    document.querySelectorAll('.el-table__header-wrapper th .cell')
                ).map(function(el) { return el.textContent.trim(); }).filter(Boolean);
            """)
            if headers and len(headers) >= 3:
                return headers
        return []
    def get_table_row_count(self):
        """获取当前页行数"""
        self._wait_table_ready()
        rows = self.find_all(self.TABLE_ROWS)
        return sum(1 for r in rows if r.is_displayed())

    def get_column_data(self, col_index):
        """获取指定列（1-based）所有数据"""
        self._wait_table_ready()
        cells = self.find_all(
            (By.CSS_SELECTOR,
             f'.table-wrapper .el-table__body-wrapper tbody td:nth-child({col_index}) .cell')
        )
        return [c.text.strip() for c in cells if c.text.strip()]

    def get_column_index_by_header(self, header_text):
        """根据表头文本获取列索引"""
        headers = self.get_table_headers()
        for idx, h in enumerate(headers, start=1):
            if h == header_text:
                return idx
        return None

    def is_row_present(self, text, timeout=10):
        """判断表格中是否存在包含指定文本的行

        轮询重试以处理 Vue 异步数据刷新竞态。
        """
        self._wait_table_ready()
        xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'//td[contains(normalize-space(.),"{text}")]'
        )
        import time as _time
        deadline = _time.time() + timeout
        while _time.time() < deadline:
            if self.is_present((By.XPATH, xpath), timeout=2):
                return True
            _time.sleep(0.5)
        return False

    def click_row_button(self, row_identifier, button_text):
        """点击表格行内的操作按钮（JS click 避免 fixed 列遮挡）"""
        logger.info("对「%s」点击操作: %s", row_identifier, button_text)
        xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td[contains(normalize-space(.),"{row_identifier}")]]'
            f'//button[contains(.,"{button_text}")]'
        )
        self.js_click((By.XPATH, xpath))
        self.wait_vue_stable()

    # ==================================================================
    #  内部：下拉选择
    # ==================================================================
    def _click_select_trigger(self, trigger_locator):
        """点击下拉触发器"""
        self.click(trigger_locator)
        self.wait_vue_stable()

    def _select_option(self, option_text):
        """从已展开的下拉列表中选择选项（BasePage 原有方法）"""
        super()._select_option(option_text)
