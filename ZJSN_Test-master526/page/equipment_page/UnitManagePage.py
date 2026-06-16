"""计量单位（装置）管理页面 Page Object — 基于真实 HTML 结构

==== 页面组件 ====
  1. 统计卡片（4个 .stat-card，BEM命名）：装置总数、运行中、维护中、已停用
  2. 搜索表单（.search-wrapper 内 el-form inline）
  3. 操作按钮栏：新增装置、导入、导出（有 v-permission 权限控制）
  4. 数据表格（.table-wrapper 内 el-table）
  5. 分页（el-pagination）

==== 弹窗组件 ====
  A. 新增/编辑弹窗（title="新增装置"/"编辑装置"，width=650px）
     - 表单字段：装置名称*、装置编号*、装置类型*、所属区域*、状态、装置描述(textarea)
  B. 详情弹窗（title="装置详情"，width=750px）
     - el-descriptions（column=2, border）
  C. 关联设备弹窗（title="关联设备"，width=800px）
     - 设备搜索 + 多选表格 + 已选计数提示
  D. 导入装置弹窗（title="导入装置"，共享组件）
     - 模板下载 → 拖拽上传 → 进度条 → 导入结果

==== 定位策略 ====
  CSS_SELECTOR 优先（语义class + Element Plus 标准类 + placeholder）
  文本匹配使用相对 XPath 保底
  不使用 data-v-* / el-id-* / nth-child 绝对定位
"""

import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class UnitManagePage(BasePage):
    """计量单位（装置）管理页面"""

    # ==================================================================
    #  统计卡片 — BEM 命名，通过 .stat-card__label 文字区分
    # ==================================================================
    STAT_CARD = (By.CSS_SELECTOR, '.stat-card')
    STAT_CARD_VALUE = (By.CSS_SELECTOR, '.stat-card__value')
    STAT_TOTAL = (
        By.XPATH,
        '//div[contains(@class,"stat-card")]'
        '[.//div[contains(@class,"stat-card__label") and normalize-space(.)="装置总数"]]'
        '//div[contains(@class,"stat-card__value")]',
    )
    STAT_RUNNING = (
        By.XPATH,
        '//div[contains(@class,"stat-card")]'
        '[.//div[contains(@class,"stat-card__label") and normalize-space(.)="运行中"]]'
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

    # ==================================================================
    #  搜索区 — .search-wrapper 作用域限定
    # ==================================================================
    SEARCH_WRAPPER = (By.CSS_SELECTOR, '.search-wrapper')
    # 装置名称/编号输入框 — placeholder="装置名称/编号"
    INPUT_UNIT_NAME = (
        By.CSS_SELECTOR,
        '.search-wrapper input[placeholder*="装置名称"]',
    )
    # 装置类型下拉框 — placeholder="装置类型"
    SELECT_TYPE_TRIGGER = (
        By.CSS_SELECTOR,
        '.search-wrapper .el-select',
    )

    # 按钮 — 按文本 + Element Plus type 组合匹配（不限定 .search-wrapper）
    BTN_SEARCH = (
        By.XPATH,
        '//button[contains(@class,"el-button--primary")][contains(.,"查询")]',
    )
    BTN_RESET = (
        By.XPATH,
        '//button[contains(.,"重置")]',
    )
    BTN_ADD = (
        By.XPATH,
        '//button[contains(.,"新增")]',
    )
    BTN_IMPORT = (
        By.XPATH,
        '//button[contains(.,"导入")]',
    )
    BTN_EXPORT = (
        By.XPATH,
        '//button[contains(.,"导出")]',
    )

    # ==================================================================
    #  表格区 — .table-wrapper 作用域限定
    # ==================================================================
    TABLE_WRAPPER = (By.CSS_SELECTOR, '.table-wrapper')
    TABLE_TITLE = (By.CSS_SELECTOR, '.table-title')
    TABLE_ROWS = (
        By.CSS_SELECTOR,
        '.table-wrapper .el-table__body-wrapper tbody tr.el-table__row',
    )
    TABLE_HEADER_CELLS = (
        By.CSS_SELECTOR,
        '.table-wrapper .el-table__header-wrapper th .cell',
    )
    TABLE_EMPTY = (By.CSS_SELECTOR, '.table-wrapper .el-table__empty-text')
    TABLE_LOADING = (
        By.CSS_SELECTOR,
        '.table-wrapper .el-loading-mask',
    )

    # 表格操作列按钮（用于 click_row_button 的 button_text 参数）
    ROW_BTN_TEXT = {
        'view': '查看',
        'edit': '编辑',
        'bind': '关联设备',
    }

    # ==================================================================
    #  分页区
    # ==================================================================
    PAGINATION = (By.CSS_SELECTOR, '.el-pagination')
    PAGE_TOTAL = (By.CSS_SELECTOR, '.el-pagination__total')
    PAGE_NEXT = (By.CSS_SELECTOR, '.el-pagination .btn-next:not([disabled])')
    PAGE_PREV = (By.CSS_SELECTOR, '.el-pagination .btn-prev:not([disabled])')
    PAGE_SIZE_SELECT = (
        By.CSS_SELECTOR,
        '.el-pagination__sizes .el-select',
    )
    PAGE_JUMPER_INPUT = (
        By.CSS_SELECTOR,
        '.el-pagination__jump .el-input__inner',
    )

    # ==================================================================
    #  新增/编辑弹窗（title="新增装置"/"编辑装置"，width=650px）
    #  使用 BasePage._get_dialog_form_item(label_text) 按 label 定位表单字段
    # ==================================================================
    DIALOG_FORM_TITLE = (
        By.XPATH,
        '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
        '//span[contains(@class,"el-dialog__title")]',
    )
    # 表单 label → BasePage.fill_dialog_input / select_dialog_dropdown 的参数
    FORM_LABEL_UNIT_NAME = "装置名称"        # input, required
    FORM_LABEL_UNIT_CODE = "装置编号"        # input, required
    FORM_LABEL_UNIT_TYPE = "装置类型"        # select, required
    FORM_LABEL_AREA = "所属区域"             # select, required
    FORM_LABEL_STATUS = "状态"               # select
    FORM_LABEL_DESCRIPTION = "装置描述"      # textarea, rows=3

    # 保存/取消 — BasePage 已有 DIALOG_SAVE / DIALOG_CANCEL 通用定位器

    # ==================================================================
    #  详情弹窗（title="装置详情"，width=750px）
    # ==================================================================
    DETAIL_DIALOG = (
        By.CSS_SELECTOR,
        '.el-dialog[aria-label="装置详情"]',
    )
    DETAIL_DESCRIPTIONS = (By.CSS_SELECTOR, '.el-descriptions')
    # 详情字段 label
    DETAIL_SECTION_TITLE = (By.CSS_SELECTOR, '.detail-section-title')

    # ==================================================================
    #  关联设备弹窗（title="关联设备"，width=800px）
    # ==================================================================
    BIND_DIALOG = (
        By.CSS_SELECTOR,
        '.el-dialog[aria-label="关联设备"]',
    )
    # 设备搜索（弹窗内）
    BIND_SEARCH_NAME = (
        By.CSS_SELECTOR,
        '.el-dialog[aria-label="关联设备"] input[placeholder="设备名称"]',
    )
    BIND_SEARCH_CODE = (
        By.CSS_SELECTOR,
        '.el-dialog[aria-label="关联设备"] input[placeholder="设备编号"]',
    )
    BIND_SEARCH_TYPE_TRIGGER = (
        By.XPATH,
        '//div[contains(@class,"el-dialog")][@aria-label="关联设备"]'
        '//input[@placeholder="设备类型"]/ancestor::div[contains(@class,"el-select")]',
    )
    BIND_BTN_SEARCH = (
        By.XPATH,
        '//div[contains(@class,"el-dialog")][@aria-label="关联设备"]'
        '//button[contains(.,"查询")]',
    )
    BIND_BTN_RESET = (
        By.XPATH,
        '//div[contains(@class,"el-dialog")][@aria-label="关联设备"]'
        '//button[contains(.,"重置")]',
    )
    # 设备表格（多选）
    BIND_TABLE_ROWS = (
        By.CSS_SELECTOR,
        '.el-dialog[aria-label="关联设备"] .el-table__body-wrapper tbody tr',
    )
    BIND_TABLE_LOADING = (
        By.CSS_SELECTOR,
        '.el-dialog[aria-label="关联设备"] .el-loading-mask',
    )
    # 已选提示
    BIND_HINT = (By.CSS_SELECTOR, '.bind-hint')
    # 确认绑定 / 取消 — 按钮文本唯一
    BIND_BTN_CONFIRM = (
        By.XPATH,
        '//div[contains(@class,"el-dialog")][@aria-label="关联设备"]'
        '//button[contains(.,"确认绑定")]',
    )

    # ==================================================================
    #  导入弹窗（title="导入装置"）
    # ==================================================================
    IMPORT_DIALOG = (
        By.XPATH,
        '//div[contains(@class,"el-dialog")][contains(@aria-label,"导入")]',
    )
    IMPORT_BTN_DOWNLOAD_TEMPLATE = (
        By.XPATH,
        '//div[contains(@class,"el-dialog")][contains(@aria-label,"导入")]'
        '//button[contains(.,"下载模板")]',
    )
    IMPORT_BTN_START = (
        By.XPATH,
        '//div[contains(@class,"el-dialog")][contains(@aria-label,"导入")]'
        '//button[contains(.,"开始导入")]',
    )
    IMPORT_FILE_INPUT = (
        By.CSS_SELECTOR,
        '//div[contains(@class,"el-dialog")][contains(@aria-label,"导入")] input[type="file"]',
    )
    IMPORT_PROGRESS = (
        By.CSS_SELECTOR,
        '//div[contains(@class,"el-dialog")][contains(@aria-label,"导入")] .el-progress',
    )
    IMPORT_RESULT = (
        By.CSS_SELECTOR,
        '//div[contains(@class,"el-dialog")][contains(@aria-label,"导入")] .el-result',
    )
    IMPORT_ERROR_TABLE = (
        By.CSS_SELECTOR,
        '//div[contains(@class,"el-dialog")][contains(@aria-label,"导入")] .import-error-list .el-table',
    )

    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    # ==================================================================
    #  导航
    # ==================================================================
    def navigate_to_unit_management(self):
        """通过侧边栏导航到装置台账页面"""
        logger.info("导航到 → 设备管理 → 装置台账")
        # 等待侧边栏菜单就绪（登录后可能延迟渲染）
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.el-menu,.sidebar-container'))
            )
            self.wait_vue_stable()
            self.wait_vue_stable()
        except TimeoutException:
            logger.warning("侧边栏菜单未在时间内就绪，仍尝试导航")
        self.navigate_to("设备管理", "装置台账")
        self._wait_page_ready()

    # ==================================================================
    #  页面就绪
    # ==================================================================
    def _wait_page_ready(self, timeout=25):
        """等待页面核心元素加载完成"""
        self.wait_page_ready(timeout=30)        # document.readyState == 'complete'
        self._wait_loading_gone(timeout)
        try:
            self.wait_stats_loaded(timeout=min(timeout, 12))
        except TimeoutException:
            logger.warning("统计卡片未在时间内加载，尝试等待表格")
        self._wait_table_ready(timeout=min(timeout, 10))

    def wait_stats_loaded(self, timeout=10):
        """等待统计卡片数字出现 — 至少4张卡片有非空文本"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: (
                    sum(1 for el in d.find_elements(*self.STAT_CARD_VALUE)
                        if (el.text or '').strip() != '') >= 4
                )
            )
        except TimeoutException:
            logger.warning("统计卡片及表格均未在 %ds 内加载", timeout)

    def _wait_table_ready(self, timeout=10):
        """等待表格渲染完成（loading 消失 + Vue 稳定）"""
        self._wait_loading_gone(timeout)
        self.wait_vue_stable()

    # ==================================================================
    #  统计卡片
    # ==================================================================
    def get_stat_total(self):
        """获取装置总数"""
        return self.get_text(self.STAT_TOTAL)

    def get_stat_running(self):
        """获取运行中数量"""
        return self.get_text(self.STAT_RUNNING)

    def get_stat_maintenance(self):
        """获取维护中数量"""
        return self.get_text(self.STAT_MAINTENANCE)

    def get_stat_stopped(self):
        """获取已停用数量"""
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

    def click_stat_card(self, card_label):
        """点击指定统计卡片（用于状态筛选）

        Args:
            card_label: "装置总数" | "运行中" | "维护中" | "已停用"
        """
        xpath = (
            f'//div[contains(@class,"stat-card")]'
            f'[.//div[contains(@class,"stat-card__label") and normalize-space(.)="{card_label}"]]'
        )
        self.click((By.XPATH, xpath))
        self._wait_table_ready()

    # ==================================================================
    #  搜索区
    # ==================================================================
    def input_unit_name(self, keyword):
        """输入装置名称/编号搜索关键词"""
        self.input_text(self.INPUT_UNIT_NAME, keyword or '')

    def get_unit_name_value(self):
        """获取搜索框当前值"""
        return self.get_attribute(self.INPUT_UNIT_NAME, 'value')

    def select_unit_type(self, type_name):
        """选择装置类型下拉"""
        self._click_select_trigger(self.SELECT_TYPE_TRIGGER)
        self._select_option(type_name)

    def click_search(self):
        """点击查询按钮"""
        self.click(self.BTN_SEARCH)
        self._wait_table_ready()

    def click_reset(self):
        """点击重置按钮"""
        self.click(self.BTN_RESET)
        self._wait_table_ready()

    def click_add(self):
        """点击新增装置按钮"""
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
    #  搜索区 — 权限检查
    # ==================================================================
    def is_add_button_visible(self):
        """新增装置按钮是否可见"""
        return self.is_visible(self.BTN_ADD, timeout=2)

    def is_import_button_visible(self):
        """导入按钮是否可见"""
        return self.is_visible(self.BTN_IMPORT, timeout=2)

    def is_export_button_visible(self):
        """导出按钮是否可见"""
        return self.is_visible(self.BTN_EXPORT, timeout=2)

    # ==================================================================
    #  表格 — 通用操作
    # ==================================================================
    def get_table_headers(self):
        """JS提取表格表头（含重试，应对Element Plus异步渲染）"""
        for attempt in range(8):
            try:
                self._wait_table_ready()
            except Exception:
                self._wait_loading_gone(3)
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
        """获取当前页行数（排除不可见行）"""
        self._wait_table_ready()
        rows = self.find_all(self.TABLE_ROWS)
        return sum(1 for r in rows if r.is_displayed())

    def get_column_data(self, col_index):
        """获取指定列（1-based）所有行数据"""
        self._wait_table_ready()
        cells = self.find_all(
            (By.CSS_SELECTOR,
             f'.table-wrapper .el-table__body-wrapper tbody td:nth-child({col_index}) .cell')
        )
        return [c.text.strip() for c in cells if c.text.strip()]

    def get_column_index_by_header(self, header_text):
        """根据表头文本获取列索引（1-based）"""
        headers = self.get_table_headers()
        for idx, h in enumerate(headers, start=1):
            if header_text in h:
                return idx
        return None

    def is_table_empty(self):
        """表格是否为空（显示暂无数据）"""
        self._wait_table_ready()
        return self.is_visible(self.TABLE_EMPTY, timeout=2)

    def is_row_present(self, text, timeout=10):
        """判断表格中是否存在包含指定文本的行

        轮询重试以处理 Vue 异步数据刷新（AJAX 重新拉取表格数据）导致的竞态。

        Args:
            text: 单元格中的任意文本（如装置名称、装置编号）
            timeout: 轮询超时秒数
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
        """在表格中查找包含指定文本的行，点击行内操作按钮

        Args:
            row_identifier: 行标识文本（如装置名称或装置编号）
            button_text: 按钮文本（"查看" | "编辑" | "关联设备"）
        """
        logger.info("对「%s」点击操作: %s", row_identifier, button_text)
        xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td[contains(normalize-space(.),"{row_identifier}")]]'
            f'//button[contains(.,"{button_text}")]'
        )
        self.click((By.XPATH, xpath))
        self.wait_vue_stable()

    def click_view(self, row_identifier):
        """查看装置详情"""
        self.click_row_button(row_identifier, self.ROW_BTN_TEXT['view'])

    def click_edit(self, row_identifier):
        """编辑装置"""
        self.click_row_button(row_identifier, self.ROW_BTN_TEXT['edit'])
        self.wait_dialog_open()

    def click_bind_device(self, row_identifier):
        """打开关联设备弹窗"""
        self.click_row_button(row_identifier, self.ROW_BTN_TEXT['bind'])
        # 等待关联设备弹窗打开 + 设备表格加载
        self._wait_bind_dialog_ready()

    def get_all_unit_names_on_page(self):
        """获取当前页所有装置名称列表"""
        col_idx = self.get_column_index_by_header("装置名称")
        if col_idx is None:
            return []
        return self.get_column_data(col_idx)

    # ==================================================================
    #  表格 — 权限检查
    # ==================================================================
    def is_edit_button_visible(self, row_identifier):
        """指定行的编辑按钮是否可见"""
        xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td[contains(normalize-space(.),"{row_identifier}")]]'
            f'//button[contains(.,"编辑")]'
        )
        return self.is_visible((By.XPATH, xpath), timeout=2)

    def is_bind_button_visible(self, row_identifier):
        """指定行的关联设备按钮是否可见"""
        xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td[contains(normalize-space(.),"{row_identifier}")]]'
            f'//button[contains(.,"关联设备")]'
        )
        return self.is_visible((By.XPATH, xpath), timeout=2)

    # ==================================================================
    #  分页
    # ==================================================================
    def get_total_count(self):
        """获取分页器显示的总条数（数字）"""
        try:
            text = self.get_text(self.PAGE_TOTAL, timeout=3)
            return int(''.join(filter(str.isdigit, text)))
        except (ValueError, TypeError, TimeoutException):
            return 0

    def get_current_page(self):
        """获取当前激活的页码"""
        try:
            active = self.driver.find_element(
                By.CSS_SELECTOR, '.el-pagination .el-pager li.is-active'
            )
            return int(active.text.strip())
        except Exception:
            return 1

    def get_page_size(self):
        """获取当前每页条数"""
        try:
            el = self.driver.find_element(
                By.CSS_SELECTOR, '.el-pagination__sizes .el-select .el-select__selected-item'
            )
            return int((el.text or '').strip())
        except Exception:
            return 10

    def click_next_page(self):
        """点击下一页"""
        self.click(self.PAGE_NEXT)
        self._wait_table_ready()

    def click_prev_page(self):
        """点击上一页"""
        self.click(self.PAGE_PREV)
        self._wait_table_ready()

    def change_page_size(self, size):
        """切换每页条数

        Args:
            size: 10 | 20 | 50 | 100
        """
        self.click(self.PAGE_SIZE_SELECT)
        self.wait_vue_stable()
        self._select_option(str(size))
        self._wait_table_ready()

    def jump_to_page(self, page_num):
        """使用跳转输入框跳转到指定页"""
        el = self.find(self.PAGE_JUMPER_INPUT)
        self._scroll_into_view(el)
        el.clear()
        el.send_keys(str(page_num))
        el.send_keys('\n')   # Enter 触发跳转
        self.wait_vue_stable()
        self._wait_table_ready()

    # ==================================================================
    #  新增/编辑弹窗
    # ==================================================================
    def get_form_dialog_title(self):
        """获取弹窗标题（"新增装置" 或 "编辑装置"）"""
        return self.get_text(self.DIALOG_FORM_TITLE)

    def fill_form_unit_name(self, name):
        """填写装置名称"""
        self.fill_dialog_input(self.FORM_LABEL_UNIT_NAME, name)

    def fill_form_unit_code(self, code):
        """填写装置编号"""
        self.fill_dialog_input(self.FORM_LABEL_UNIT_CODE, code)

    def _dialog_select(self, label_text, option_text):
        """弹窗下拉选择 — 通过点击 wrapper 打开下拉，选择选项"""
        item = self._get_dialog_form_item(label_text)
        # Element Plus 2.x：点击 el-select__wrapper 触发下拉
        wrapper = item.find_element(
            By.XPATH, './/div[contains(@class,"el-select__wrapper")]'
        )
        self._scroll_into_view(wrapper)
        # 使用 Selenium ActionChains 模拟真实点击
        from selenium.webdriver.common.action_chains import ActionChains
        ActionChains(self.driver).move_to_element(wrapper).click().perform()
        self._wait_loading_gone(3)
        # 选择选项
        self._select_option(option_text)

    def select_form_unit_type(self, type_name):
        """选择装置类型"""
        self._dialog_select(self.FORM_LABEL_UNIT_TYPE, type_name)

    def select_form_area(self, area_name):
        """选择所属区域"""
        self._dialog_select(self.FORM_LABEL_AREA, area_name)

    def select_form_status(self, status_name):
        """选择状态"""
        self._dialog_select(self.FORM_LABEL_STATUS, status_name)

    def fill_form_description(self, desc):
        """填写装置描述"""
        self.fill_dialog_input(self.FORM_LABEL_DESCRIPTION, desc)

    def fill_form_all(self, unit_data):
        """一键填写全部表单字段

        Args:
            unit_data: dict，键名为 unitName/unitCode/unitType/area/status/description
                       所有值均为字符串（status 内部是数字但选择时使用文字）
        """
        if unit_data.get('unitName') is not None:
            self.fill_form_unit_name(unit_data['unitName'])
        if unit_data.get('unitCode') is not None:
            self.fill_form_unit_code(unit_data['unitCode'])
        if unit_data.get('unitType') is not None:
            self.select_form_unit_type(unit_data['unitType'])
        if unit_data.get('area') is not None:
            self.select_form_area(unit_data['area'])
        if unit_data.get('status') is not None:
            self.select_form_status(unit_data['status'])
        if unit_data.get('description') is not None:
            self.fill_form_description(unit_data['description'])

    def click_form_save(self):
        """点击弹窗保存按钮，等待 Toast 和列表刷新"""
        self.click_dialog_save()
        # 等待操作结果
        toast = self.wait_for_toast_text(timeout=5)
        logger.info("操作结果 Toast: %s", toast)
        self._wait_table_ready()
        return toast

    def click_form_cancel(self):
        """点击弹窗取消按钮"""
        self.click_dialog_cancel()
        self.wait_dialog_close()

    def get_form_error(self):
        """获取表单校验错误文本"""
        return super().get_form_error()

    def wait_form_dialog_closed(self):
        """等待新增/编辑弹窗关闭"""
        self.wait_dialog_close()

    # ==================================================================
    #  新增/编辑弹窗 — 复合操作
    # ==================================================================
    def add_unit(self, unit_data):
        """新增装置（完整流程）

        Args:
            unit_data: dict，至少包含 unitName, unitCode, unitType

        Returns:
            str: Toast 消息文本（成功/失败）
        """
        logger.info("新增装置: %s", unit_data.get('unitName'))
        self.click_add()
        self.fill_form_all(unit_data)
        return self.click_form_save()

    def edit_unit(self, row_identifier, unit_data):
        """编辑装置（完整流程）

        Args:
            row_identifier: 行标识文本
            unit_data: dict，仅包含需要修改的字段

        Returns:
            str: Toast 消息文本
        """
        logger.info("编辑装置「%s」: %s", row_identifier, unit_data)
        self.click_edit(row_identifier)
        self.fill_form_all(unit_data)
        return self.click_form_save()

    # ==================================================================
    #  详情弹窗
    # ==================================================================
    def wait_detail_dialog_open(self):
        """等待详情弹窗打开"""
        self.wait_dialog_open()
        self.wait_vue_stable()

    def get_detail_value(self, label_text):
        """获取详情弹窗中指定 label 对应的值

        通过 el-descriptions 的 label 查找对应 value 单元格
        """
        xpath = (
            f'//div[contains(@class,"el-dialog")][@aria-label="装置详情"]'
            f'//td[contains(@class,"el-descriptions__label") and '
            f'contains(normalize-space(.),"{label_text}")]'
            f'/following-sibling::td[contains(@class,"el-descriptions__content")]'
        )
        el = self.driver.find_element(By.XPATH, xpath)
        return (el.text or '').strip()

    def get_all_detail_values(self):
        """获取详情弹窗全部字段值"""
        fields = [
            "装置名称", "装置编号", "装置类型", "所属区域",
            "状态", "关联设备数", "装置描述",
        ]
        return {f: self.get_detail_value(f) for f in fields}

    def click_detail_close(self):
        """关闭详情弹窗"""
        # 详情弹窗 footer 只有"关闭"按钮
        self.click_dialog_cancel()
        self.wait_dialog_close()

    # ==================================================================
    #  关联设备弹窗
    # ==================================================================
    def _wait_bind_dialog_ready(self, timeout=15):
        """等待关联设备弹窗及设备表格加载完成"""
        self.wait_dialog_open()
        self._wait_loading_gone(timeout)
        self.wait_vue_stable()

    def search_bind_device_by_name(self, name):
        """在关联弹窗中按设备名称搜索"""
        el = self.find(self.BIND_SEARCH_NAME)
        self._scroll_into_view(el)
        self.input_text(self.BIND_SEARCH_NAME, name)
        self.click(self.BIND_BTN_SEARCH)
        self._wait_loading_gone()

    def search_bind_device_by_code(self, code):
        """在关联弹窗中按设备编号搜索"""
        self.input_text(self.BIND_SEARCH_CODE, code)
        self.click(self.BIND_BTN_SEARCH)
        self._wait_loading_gone()

    def reset_bind_device_search(self):
        """重置关联弹窗搜索条件"""
        self.click(self.BIND_BTN_RESET)
        self._wait_loading_gone()

    def get_bind_device_row_count(self):
        """获取可选设备行数"""
        rows = self.find_all(self.BIND_TABLE_ROWS)
        return sum(1 for r in rows if r.is_displayed())

    def get_selected_device_count(self):
        """获取已选设备数（从 hint 文本解析）"""
        try:
            text = self.get_text(self.BIND_HINT, timeout=3)
            # "已选择 N 台设备"
            return int(''.join(filter(str.isdigit, text)))
        except (ValueError, TimeoutException):
            return 0

    def toggle_bind_device_by_name(self, device_name, select=True):
        """勾选/取消勾选指定设备

        Args:
            device_name: 设备名称（表格中的行标识）
            select: True=勾选, False=取消勾选
        """
        xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td[contains(normalize-space(.),"{device_name}")]]'
            f'//td[contains(@class,"el-table-column--selection")]'
        )
        checkbox = self.find((By.XPATH, xpath))
        is_checked = 'is-checked' in (checkbox.get_attribute('class') or '')
        if select != is_checked:
            self.click((By.XPATH, xpath))

    def click_bind_confirm(self):
        """点击确认绑定按钮"""
        self.click(self.BIND_BTN_CONFIRM)
        toast = self.wait_for_toast_text(timeout=5)
        logger.info("绑定结果 Toast: %s", toast)
        self._wait_table_ready()
        return toast

    def click_bind_cancel(self):
        """取消关联设备"""
        self.click_dialog_cancel()
        self.wait_dialog_close()

    def bind_devices(self, row_identifier, device_names):
        """关联设备 — 完整流程

        Args:
            row_identifier: 装置行标识
            device_names: 要勾选的设备名称列表

        Returns:
            str: Toast 消息文本
        """
        logger.info("为装置「%s」关联设备: %s", row_identifier, device_names)
        self.click_bind_device(row_identifier)
        for name in device_names:
            self.toggle_bind_device_by_name(name, select=True)
        return self.click_bind_confirm()

    # ==================================================================
    #  导入弹窗
    # ==================================================================
    def wait_import_dialog_open(self):
        """等待导入弹窗打开"""
        self.wait_dialog_open()
        self.wait_vue_stable()

    def click_download_template(self):
        """点击下载模板按钮"""
        self.click(self.IMPORT_BTN_DOWNLOAD_TEMPLATE)

    def upload_import_file(self, file_absolute_path):
        """上传导入文件

        Args:
            file_absolute_path: Excel 文件的绝对路径
        """
        file_input = self.driver.find_element(*self.IMPORT_FILE_INPUT)
        file_input.send_keys(file_absolute_path)
        self.wait_vue_stable()
        logger.info("已选择导入文件: %s", file_absolute_path)

    def click_start_import(self):
        """点击开始导入按钮"""
        self.click(self.IMPORT_BTN_START)

    def wait_import_completed(self, timeout=30):
        """等待导入完成（进度条→结果出现）

        Returns:
            bool: 是否导入完成
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: len(d.find_elements(*self.IMPORT_RESULT)) > 0
            )
            return True
        except TimeoutException:
            logger.warning("导入未在 %ds 内完成", timeout)
            return False

    def get_import_result_counts(self):
        """获取导入结果统计

        Returns:
            dict: {'total': int, 'success': int, 'failed': int}
                  如果结果区域不存在则返回 None
        """
        # 通过统计文本解析：成功 N 条，失败 M 条
        try:
            result_el = self.driver.find_element(*self.IMPORT_RESULT)
            title = (result_el.find_element(By.CSS_SELECTOR, '.el-result__title').text or '').strip()
            sub = (result_el.find_element(By.CSS_SELECTOR, '.el-result__subtitle').text or '').strip()
            import re
            success = int(re.search(r'成功[^\d]*(\d+)', sub).group(1)) if re.search(r'成功[^\d]*(\d+)', sub) else 0
            failed = int(re.search(r'失败[^\d]*(\d+)', sub).group(1)) if re.search(r'失败[^\d]*(\d+)', sub) else 0
            return {
                'title': title,
                'success': success,
                'failed': failed,
                'total': success + failed,
            }
        except Exception:
            return None

    def is_import_completed(self):
        """导入是否已完成（结果区域可见）"""
        return self.is_visible(self.IMPORT_RESULT, timeout=2)

    def get_import_progress_percentage(self):
        """获取当前导入进度百分比"""
        try:
            progress_text = self.driver.find_element(
                By.CSS_SELECTOR,
                '//div[contains(@class,"el-dialog")][contains(@aria-label,"导入")] .el-progress__text',
            ).text.strip()
            return int(progress_text.replace('%', ''))
        except Exception:
            return 0

    def close_import_dialog(self):
        """关闭导入弹窗"""
        self.click_dialog_cancel()
        self.wait_dialog_close()
        self._wait_table_ready()

    def import_data(self, file_path):
        """导入装置 — 完整流程

        Args:
            file_path: Excel 文件绝对路径

        Returns:
            dict: 导入结果 {'total', 'success', 'failed'}
        """
        logger.info("导入装置文件: %s", file_path)
        self.click_import()
        self.wait_import_dialog_open()
        self.upload_import_file(file_path)
        self.click_start_import()
        if self.wait_import_completed(timeout=30):
            result = self.get_import_result_counts()
            logger.info("导入完成: %s", result)
            self.close_import_dialog()
            return result
        logger.warning("导入超时")
        return None

    # ==================================================================
    #  内部：下拉选择辅助
    # ==================================================================
    def _click_select_trigger(self, trigger_locator):
        """点击下拉触发器"""
        self.click(trigger_locator)
        self.wait_vue_stable()

    def _select_option(self, option_text):
        """从已展开的下拉列表中选择选项（增强版：额外等待+重试）"""
        # 等待下拉面板渲染
        self.wait_vue_stable()
        try:
            super()._select_option(option_text)
        except Exception:
            # 保底：尝试更宽松的匹配
            logger.debug("精确匹配失败，尝试 contains 匹配: %s", option_text)
            xp = (
                f'(//div[contains(@class,"el-select-dropdown") and '
                f'not(contains(@style,"display: none"))])[last()]'
                f'//li[not(contains(@class,"is-disabled")) and '
                f'contains(normalize-space(.),"{option_text}")]'
            )
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            opt = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, xp))
            )
            self._js_click_el(opt)
            self.wait_vue_stable()
            logger.info("已选择下拉选项 (contains): %s", option_text)
