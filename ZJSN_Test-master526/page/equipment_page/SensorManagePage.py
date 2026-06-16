"""传感器管理页面 Page Object

==== 页面特征 ====
  - 统计卡片：4张 .stat-card（BEM命名，与设备管理相同模式）
  - 搜索表单：.search-wrapper 内 el-form inline
  - 数据表格：el-table，操作列 fixed="right"（关键：DOM克隆问题）
  - 分页：el-pagination

==== 关键风险：fixed="right" 列 DOM 克隆 ====
  Element Plus 的 fixed="right" 列会克隆一份 DOM 到固定区域，
  导致操作按钮在 DOM 中存在两份。解决方案：
    1. 始终在 .el-table__body-wrapper .el-table__body 内定位行按钮
    2. 不直接使用 el-table__fixed-right 内的按钮

==== 定位策略 ====
  CSS_SELECTOR 优先（语义 class + Element Plus 标准类）
  文本匹配使用相对 XPath 保底
  禁止：Vue 动态 ID (el-id-xxx)、绝对 XPath、nth-child 硬编码
"""
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class SensorManagePage(BasePage):
    """传感器管理页面"""

    # ==================================================================
    #  统计卡片 — BEM 命名，按 label 文字区分
    # ==================================================================
    STAT_CARD = (By.CSS_SELECTOR, '.stat-card')
    STAT_TOTAL = (
        By.XPATH,
        '//div[contains(@class,"stat-card")]'
        '[.//div[contains(@class,"stat-card__label") and normalize-space(.)="传感器总数"]]'
        '//div[contains(@class,"stat-card__value")]',
    )
    STAT_BOUND = (
        By.XPATH,
        '//div[contains(@class,"stat-card")]'
        '[.//div[contains(@class,"stat-card__label") and normalize-space(.)="已绑定"]]'
        '//div[contains(@class,"stat-card__value")]',
    )
    STAT_ALARM = (
        By.XPATH,
        '//div[contains(@class,"stat-card")]'
        '[.//div[contains(@class,"stat-card__label") and normalize-space(.)="故障报警"]]'
        '//div[contains(@class,"stat-card__value")]',
    )
    STAT_UNBOUND = (
        By.XPATH,
        '//div[contains(@class,"stat-card")]'
        '[.//div[contains(@class,"stat-card__label") and normalize-space(.)="未绑定"]]'
        '//div[contains(@class,"stat-card__value")]',
    )
    STAT_LABELS = (By.CSS_SELECTOR, '.stat-card__label')

    # ==================================================================
    #  搜索区 — .search-wrapper 作用域限定
    # ==================================================================
    SEARCH_WRAPPER = (By.CSS_SELECTOR, '.search-wrapper')
    INPUT_KEYWORD = (
        By.CSS_SELECTOR,
        '.search-wrapper input[placeholder*="传感器名称"], '
        '.search-wrapper .el-input__inner',
    )
    # 三个下拉框 — 按 placeholder 文本区分
    SELECT_TYPE_TRIGGER = (
        By.XPATH,
        '//div[contains(@class,"search-wrapper")]'
        '//div[contains(@class,"el-select")][.//input[contains(@placeholder,"类型")]]',
    )
    SELECT_ONLINE_TRIGGER = (
        By.XPATH,
        '//div[contains(@class,"search-wrapper")]'
        '//div[contains(@class,"el-select")][.//input[contains(@placeholder,"在线")]]',
    )
    SELECT_BIND_TRIGGER = (
        By.XPATH,
        '//div[contains(@class,"search-wrapper")]'
        '//div[contains(@class,"el-select")][.//input[contains(@placeholder,"绑定")]]',
    )

    # 按钮 — 按 Element Plus type + 文本组合
    BTN_SEARCH = (
        By.XPATH,
        '//div[contains(@class,"search-wrapper")]'
        '//button[contains(@class,"el-button--primary")][contains(.,"查询")]',
    )
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
    #  重要：操作列有 fixed="right"，只在主表格体内定位，排除 .el-table__fixed-right
    # ==================================================================
    TABLE_WRAPPER = (By.CSS_SELECTOR, '.table-wrapper')
    # 主表格体（不是 fixed 列的克隆副本）
    TABLE_BODY = (
        By.CSS_SELECTOR,
        '.table-wrapper .el-table__body-wrapper .el-table__body',
    )
    TABLE_ROWS = (
        By.CSS_SELECTOR,
        '.table-wrapper .el-table__body-wrapper tbody tr.el-table__row',
    )
    TABLE_HEADER_CELLS = (
        By.CSS_SELECTOR,
        '.table-wrapper .el-table__header-wrapper th .cell',
    )
    TABLE_EMPTY = (By.CSS_SELECTOR, '.table-wrapper .el-table__empty-text')

    # ==================================================================
    #  构造
    # ==================================================================
    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    # ==================================================================
    #  导航
    # ==================================================================
    def navigate_to_sensor(self):
        """通过侧边栏导航到传感器管理页面"""
        logger.info("导航到 → 设备管理 → 传感器管理")
        self.navigate_to("设备管理", "传感器管理")
        self._wait_page_ready()

    # ==================================================================
    #  页面就绪
    # ==================================================================
    def _wait_page_ready(self, timeout=25):
        """等待页面加载完成（统计卡片或表格出现即视为就绪）"""
        self.wait_page_ready(timeout=30)        # document.readyState == 'complete'
        self._wait_loading_gone(timeout)
        # 优先等统计卡片，超时则等表格
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
    def get_all_stats(self):
        """返回 4 张卡片统计数字"""
        return {
            'total': self.get_text(self.STAT_TOTAL),
            'bound': self.get_text(self.STAT_BOUND),
            'alarm': self.get_text(self.STAT_ALARM),
            'unbound': self.get_text(self.STAT_UNBOUND),
        }

    def get_stat_card_count(self):
        return len(self.find_all(self.STAT_CARD))

    # ==================================================================
    #  搜索区
    # ==================================================================
    def input_keyword(self, keyword):
        """输入传感器名称/编号"""
        self.input_text(self.INPUT_KEYWORD, keyword or '')

    def select_type(self, type_name):
        """选择传感器类型下拉"""
        self._open_select(self.SELECT_TYPE_TRIGGER)
        self._select_option(type_name)

    def select_online_status(self, status):
        """选择在线状态下拉"""
        self._open_select(self.SELECT_ONLINE_TRIGGER)
        self._select_option(status)

    def select_bind_status(self, status):
        """选择绑定状态下拉"""
        self._open_select(self.SELECT_BIND_TRIGGER)
        self._select_option(status)

    def click_search(self):
        self.click(self.BTN_SEARCH)
        self._wait_table_ready()

    def click_reset(self):
        self.click(self.BTN_RESET)
        self._wait_table_ready()

    def click_add(self):
        self.click(self.BTN_ADD)
        self.wait_dialog_open()

    def click_import(self):
        self.click(self.BTN_IMPORT)
        self.wait_dialog_open()

    def click_export(self):
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
                self.wait_vue_stable()
            self.wait_vue_stable()
            headers = self.driver.execute_script("""
                return Array.from(
                    document.querySelectorAll('.el-table__header-wrapper th .cell')
                ).map(function(el) { return el.textContent.trim(); }).filter(Boolean);
            """)
            if headers and len(headers) >= 3:
                return headers
            self.wait_vue_stable()
        return []
    def get_table_row_count(self):
        self._wait_table_ready()
        rows = self.find_all(self.TABLE_ROWS)
        return sum(1 for r in rows if r.is_displayed())

    def get_column_data(self, col_index):
        self._wait_table_ready()
        cells = self.find_all(
            (By.CSS_SELECTOR,
             f'.table-wrapper .el-table__body-wrapper tbody td:nth-child({col_index}) .cell')
        )
        return [c.text.strip() for c in cells if c.text.strip()]

    def get_column_index_by_header(self, header_text):
        for idx, h in enumerate(self.get_table_headers(), start=1):
            if h == header_text:
                return idx
        return None

    def find_row_by_name(self, name):
        """通过传感器名称（第1列）查找行 —— 仅在主表格体中查找"""
        self._wait_table_ready()
        rows = self.find_all(self.TABLE_ROWS)
        for row in rows:
            try:
                first_cell = row.find_element(By.CSS_SELECTOR, 'td:first-child .cell')
                if name in (first_cell.text or ''):
                    return row
            except Exception:
                continue
        return None

    def click_row_button(self, sensor_name, button_text):
        """点击指定传感器行的操作按钮

        仅在主表格体（.el-table__body）中查找，排除 fixed 列克隆副本。

        Args:
            sensor_name: 传感器名称（第1列显示文本）
            button_text: 按钮文本（"查看"/"编辑"/"换绑"/"解绑"/"历史数据"）
        """
        logger.info("对传感器「%s」点击操作: %s", sensor_name, button_text)
        row = self.find_row_by_name(sensor_name)
        if not row:
            raise TimeoutException(f"未找到传感器行: {sensor_name}")

        # 在主表格体中查找操作按钮（行内最后一列）
        action_cell = row.find_element(By.CSS_SELECTOR, 'td:last-child .cell')
        xpath = f'.//button[contains(normalize-space(.),"{button_text}")]'
        btn = self.find_in_parent(action_cell, (By.XPATH, xpath))
        self._js_click_el(btn)
        self.wait_vue_stable()

    def get_row_bind_status(self, sensor_name):
        """获取指定传感器的绑定状态（el-tag 文本）"""
        row = self.find_row_by_name(sensor_name)
        if not row:
            return ''
        try:
            tag = row.find_element(By.CSS_SELECTOR, '.el-tag .el-tag__content, .el-tag')
            return (tag.text or '').strip()
        except Exception:
            return ''

    # ==================================================================
    #  内部：下拉选择
    # ==================================================================
    def _open_select(self, trigger_locator):
        """点击下拉触发器展开下拉列表"""
        self.click(trigger_locator)
        self.wait_vue_stable()

    # ==================================================================
    #  弹窗1 & 4：新增/编辑传感器（表单结构一致）
    #  差异：编辑时「传感器编号」disabled
    # ==================================================================
    # 弹窗内表单定位器
    DIALOG_NAME_INPUT = (
        By.CSS_SELECTOR,
        '.el-dialog input[placeholder="请输入传感器名称"]',
    )
    DIALOG_CODE_INPUT = (
        By.CSS_SELECTOR,
        '.el-dialog input[placeholder*="传感器编号"]',
    )
    DIALOG_CODE_DISABLED = (
        By.CSS_SELECTOR,
        '.el-dialog input[disabled][placeholder*="传感器编号"]',
    )
    DIALOG_TYPE_SELECT = None   # 动态获取：通过 _get_dialog_form_item 定位
    DIALOG_BIND_DEVICE_SELECT = None  # 动态获取
    DIALOG_INSTALL_DATE = (
        By.CSS_SELECTOR,
        '.el-dialog input[placeholder="请选择安装日期"]',
    )
    DIALOG_REMARK_TEXTAREA = (
        By.CSS_SELECTOR,
        '.el-dialog textarea[placeholder*="备注"]',
    )
    # 保存按钮：文本为"保存"（不是"确定"！）
    DIALOG_SAVE_BTN = (
        By.XPATH,
        '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
        '//button[contains(@class,"el-button--primary")][contains(.,"保存")]',
    )
    DIALOG_CANCEL_BTN = (
        By.XPATH,
        '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
        '//button[contains(.,"取消")]',
    )
    DIALOG_CLOSE_BTN = (
        By.XPATH,
        '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
        '//button[contains(.,"关闭")]',
    )

    def fill_sensor_form(self, name=None, code=None, sensor_type=None,
                         monitor_param=None, location=None, bind_device=None,
                         range_val=None, precision=None, manufacturer=None,
                         install_date=None, remark=None):
        """填充新增/编辑传感器弹窗表单。只填充非 None 的字段。"""
        if name is not None:
            self.input_text(self.DIALOG_NAME_INPUT, name)
        if code is not None:
            try:
                self.input_text(self.DIALOG_CODE_INPUT, code)
            except Exception:
                logger.debug("传感器编号可能处于禁用状态，跳过")
        if sensor_type is not None:
            self._dialog_select_by_label("传感器类型", sensor_type)
        if monitor_param is not None:
            self._dialog_input_by_placeholder("如：温度、压力", monitor_param)
        if location is not None:
            self._dialog_input_by_placeholder("如：LNG储罐顶部", location)
        if bind_device is not None:
            self._dialog_select_by_label("绑定设备", bind_device)
        if range_val is not None:
            self._dialog_input_by_placeholder("如：-200~100 ℃", range_val)
        if precision is not None:
            self._dialog_input_by_placeholder("如：0.5级", precision)
        if manufacturer is not None:
            self._dialog_input_by_placeholder("请输入生产厂家", manufacturer)
        if install_date is not None:
            self.input_text(self.DIALOG_INSTALL_DATE, install_date)
        if remark is not None:
            self.input_text(self.DIALOG_REMARK_TEXTAREA, remark)

    def _dialog_input_by_placeholder(self, placeholder_keyword, value):
        """在弹窗中通过 placeholder 关键词定位输入框并填充"""
        css = f'.el-dialog:not([style*="display: none"]) input[placeholder*="{placeholder_keyword}"]'
        try:
            self.input_text((By.CSS_SELECTOR, css), value or '')
        except Exception:
            # 回退：在弹窗内直接用 label 匹配
            logger.debug("placeholder 匹配失败: %s，回退到 label", placeholder_keyword)
            if '温度' in placeholder_keyword or '压力' in placeholder_keyword:
                self.fill_dialog_input("监测参数", value)
            elif 'LNG' in placeholder_keyword or '储罐' in placeholder_keyword:
                self.fill_dialog_input("安装位置", value)
            elif '200' in placeholder_keyword or '℃' in placeholder_keyword:
                self.fill_dialog_input("量程范围", value)
            elif '0.5' in placeholder_keyword or '级' in placeholder_keyword:
                self.fill_dialog_input("精度等级", value)
            elif '厂家' in placeholder_keyword:
                self.fill_dialog_input("生产厂家", value)
            else:
                raise

    def _dialog_select_by_label(self, label_text, option_text):
        """在弹窗中通过 label 文本选择下拉选项"""
        item_xpath = (
            f'//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
            f'//div[contains(@class,"el-form-item")]'
            f'[.//label[contains(@class,"el-form-item__label") and contains(normalize-space(.),"{label_text}")]]'
        )
        item = self.wait.until(
            EC.presence_of_element_located((By.XPATH, item_xpath))
        )
        trigger = item.find_element(
            By.XPATH,
            './/div[contains(@class,"el-select__wrapper")] | .//div[contains(@class,"el-select")]',
        )
        self._js_click_el(trigger)
        self.wait_vue_stable()
        # 先尝试 BasePage 通用方法
        try:
            self._select_option(option_text)
            return
        except Exception:
            logger.debug("通用 _select_option 失败，使用 JS 回退")
        # 回退：JS 直接查找所有可见下拉选项并点击匹配项
        clicked = self.driver.execute_script("""
            var opts = document.querySelectorAll(
                '.el-select-dropdown:not([style*=\"display: none\"]) li:not(.is-disabled)'
            );
            for (var i = 0; i < opts.length; i++) {
                if (opts[i].textContent.trim() === arguments[0]) {
                    opts[i].click();
                    return true;
                }
            }
            return false;
        """, option_text)
        if not clicked:
            raise Exception(f"无法选择下拉选项: {option_text}")
        self.wait_vue_stable()

    def click_dialog_save(self):
        """点击弹窗保存按钮（文本为"保存"）"""
        self.click(self.DIALOG_SAVE_BTN)
        self.wait_vue_stable()

    def click_dialog_cancel(self):
        """点击弹窗取消按钮"""
        self.click(self.DIALOG_CANCEL_BTN)

    def click_dialog_close(self):
        """点击弹窗关闭按钮（详情/历史弹窗）"""
        self.click(self.DIALOG_CLOSE_BTN)

    def is_code_disabled_in_edit(self):
        """编辑弹窗中传感器编号是否处于禁用状态"""
        return self.is_present(self.DIALOG_CODE_DISABLED, timeout=3)

    # ══════════════════════════════════════════════════════════════
    #  弹窗2：传感器详情（只读 el-descriptions）
    # ══════════════════════════════════════════════════════════════

    def get_detail_field(self, label_text):
        """从详情弹窗的 el-descriptions 中获取字段值

        Args:
            label_text: 描述项标签文本，如 "传感器名称"

        Returns:
            str: 对应的内容文本
        """
        xpath = (
            f'//div[contains(@class,"el-dialog")]'
            f'//td[contains(@class,"el-descriptions__label") and '
            f'contains(normalize-space(.),"{label_text}")]'
            f'/following-sibling::td[contains(@class,"el-descriptions__content")]'
        )
        return self.get_text((By.XPATH, xpath), timeout=5)

    def get_detail_bind_status(self):
        """获取详情弹窗中的绑定状态标签文本"""
        try:
            xpath = (
                '//div[contains(@class,"el-dialog")]'
                '//td[contains(@class,"el-descriptions__content")]'
                '//span[contains(@class,"el-tag")]'
            )
            return self.get_text((By.XPATH, xpath), timeout=3)
        except TimeoutException:
            return ''

    # ══════════════════════════════════════════════════════════════
    #  弹窗3：历史数据（图表 + 数据列表 + 导出）
    # ══════════════════════════════════════════════════════════════

    HISTORY_TAB_CHART = (
        By.XPATH,
        '//div[contains(@class,"el-dialog")]'
        '//div[contains(@class,"el-tabs__item") and contains(.,"曲线图表")]',
    )
    HISTORY_TAB_TABLE = (
        By.XPATH,
        '//div[contains(@class,"el-dialog")]'
        '//div[contains(@class,"el-tabs__item") and contains(.,"数据列表")]',
    )
    HISTORY_TABLE = (
        By.CSS_SELECTOR,
        '.el-dialog .el-table:not([style*="display: none"])',
    )
    HISTORY_START_INPUT = (
        By.CSS_SELECTOR,
        '.el-dialog .el-range-input:nth-child(1)',
    )
    HISTORY_END_INPUT = (
        By.CSS_SELECTOR,
        '.el-dialog .el-range-input:nth-child(3)',
    )
    HISTORY_SEARCH_BTN = (
        By.XPATH,
        '//div[contains(@class,"el-dialog")]'
        '//button[contains(@class,"el-button--primary")][contains(.,"查询")]',
    )
    HISTORY_EXPORT_BTN = (
        By.XPATH,
        '//div[contains(@class,"el-dialog")]'
        '//button[contains(.,"导出数据")]',
    )

    def switch_to_data_table(self):
        """在历史数据弹窗中切换到「数据列表」tab"""
        self.click(self.HISTORY_TAB_TABLE)
        self.wait_vue_stable()

    def search_history_data(self, start_time, end_time):
        """在历史数据弹窗中设置时间范围并查询"""
        self.input_text(self.HISTORY_START_INPUT, start_time)
        self.input_text(self.HISTORY_END_INPUT, end_time)
        self.click(self.HISTORY_SEARCH_BTN)
        self.wait_vue_stable()

    def get_history_table_rows(self):
        """获取历史数据弹窗中表格的行数"""
        return self.get_table_row_count()

    def click_export_data(self):
        """点击历史数据弹窗中的导出数据按钮"""
        self.click(self.HISTORY_EXPORT_BTN)
        self.wait_vue_stable()
