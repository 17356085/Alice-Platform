"""设备维保计划管理页面 Page Object — 基于实际 HTML 结构

==== 页面组件 ====
  1. 搜索表单（.search-wrapper 内 el-form inline）
     - 维保类型下拉、状态下拉、[搜索]/[重置]/[新增计划] 按钮
  2. 数据表格（.table-wrapper 内 el-table，无操作列 fixed）
     - 列：计划编码、计划名称、设备名称、维保类型、周期(天)、上次维保、下次维保、状态、操作
     - 行按钮：[编辑]、[生成任务]
  3. 分页（el-pagination）
  4. 新增/编辑计划弹窗（role="dialog"）

==== 定位策略 ====
  CSS_SELECTOR 优先（Element Plus 标准类 + placeholder）
  文本匹配使用相对 XPath 保底
  无 fixed 列克隆问题（操作列未设置 fixed="right"）
"""
import logging
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


# 不同维保计划状态对应的操作按钮
STATUS_BUTTON_MAP = {
    "待执行": ["编辑", "生成任务"],
    "已完成": ["查看"],
}


class MaintenancePage(BasePage):
    """设备维保计划管理页面"""

    # ══════════════════════════════════════════════════════════════════
    #  弹窗定位器（覆盖 BasePage — 本页面使用 role="dialog" 而非 el-dialog class）
    # ══════════════════════════════════════════════════════════════════
    DIALOG = (
        By.CSS_SELECTOR,
        '.el-overlay-dialog[role="dialog"]',
    )
    DIALOG_TITLE = (
        By.CSS_SELECTOR,
        '.el-overlay-dialog[role="dialog"] .el-dialog__title',
    )
    DIALOG_SAVE = (
        By.CSS_SELECTOR,
        '.el-overlay-dialog[role="dialog"] .el-button--primary',
    )
    DIALOG_CANCEL = (
        By.CSS_SELECTOR,
        '.el-overlay-dialog[role="dialog"] .el-button:not(.el-button--primary)',
    )
    DIALOG_SAVE_XPATH = (
        By.XPATH,
        '//div[contains(@class,"el-overlay-dialog")][@role="dialog"]'
        '//button[contains(@class,"el-button--primary")]',
    )
    DIALOG_CANCEL_XPATH = (
        By.XPATH,
        '//div[contains(@class,"el-overlay-dialog")][@role="dialog"]'
        '//button[not(contains(@class,"el-button--primary"))]//span[contains(.,"取消")]',
    )

    # ==================================================================
    #  搜索区 — .search-wrapper 作用域限定
    # ==================================================================
    SEARCH_WRAPPER = (By.CSS_SELECTOR, '.search-wrapper')
    # 搜索区 el-select 容器（通过 Python 索引区分类型/状态）
    SELECT_TRIGGERS = (
        By.CSS_SELECTOR,
        '.search-wrapper .el-select__wrapper',
    )

    # 按钮
    BTN_SEARCH = (
        By.XPATH,
        '//div[contains(@class,"search-wrapper")]//button[contains(@class,"el-button--primary")][contains(.,"搜索")]',
    )
    BTN_RESET = (
        By.XPATH,
        '//div[contains(@class,"search-wrapper")]//button[contains(.,"重置")]',
    )
    BTN_ADD = (
        By.XPATH,
        '//button[contains(.,"新增计划")]',
    )

    # ==================================================================
    #  表格区 — 无特定容器 class，el-table 直接可见
    #  操作列 fixed="right"（第9列存在 DOM 克隆）
    #  注意：页面有3个 el-table（维护计划 / 登录日志 / 设备状态），
    #        我们操作的是第一个（维护计划表格）
    # ==================================================================
    TABLE_BODY = (
        By.CSS_SELECTOR,
        '.el-table__body-wrapper .el-table__body',
    )
    TABLE_ROWS = (
        By.CSS_SELECTOR,
        '.el-table__body-wrapper tbody tr.el-table__row',
    )
    TABLE_HEADER_CELLS = (
        By.CSS_SELECTOR,
        '.el-table__header-wrapper th .cell',
    )
    TABLE_EMPTY = (By.CSS_SELECTOR, '.el-table__empty-text')
    TABLE_LOADING = (
        By.CSS_SELECTOR,
        '.el-loading-mask',
    )

    # 表格操作列按钮文本映射
    ROW_BTN_TEXT = {
        'edit': '编辑',
        'generate_task': '生成任务',
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
    #  新增/编辑弹窗
    #  实际页面使用 role="dialog" 而非 class="el-dialog"
    # ==================================================================
    DIALOG_FORM_TITLE = (
        By.XPATH,
        '//div[@role="dialog" and not(contains(@style,"display: none"))]'
        '//span[contains(@class,"el-dialog__title")]',
    )

    # ==================================================================
    #  初始化与导航
    # ==================================================================

    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    def navigate_to_maintenance(self):
        """导航到设备维保页面（Vue Router 编程式导航 + 侧边栏兜底）"""
        # 优先使用 Vue Router API（最快最可靠）
        self.driver.execute_script(
            "var app = document.querySelector('#app').__vue_app__;"
            "if(app && app.config.globalProperties.$router) {"
            "  app.config.globalProperties.$router.push('/equipment/maintenance');"
            "}"
        )
        self.wait_vue_stable()

        # 若路由未变，用侧边栏兜底
        if '#/equipment/maintenance' not in self.driver.current_url:
            logger.info("Vue Router 未生效，回退侧边栏")
            try:
                self.navigate_to("设备管理", "设备维保")
                self.wait_vue_stable()
            except Exception:
                pass

        self._wait_page_ready()

    def _wait_page_ready(self, timeout=30):
        """等待设备维保页面完全加载"""
        self.wait_page_ready(timeout=60)          # document.readyState
        self._wait_loading_gone(timeout=5)         # 给 Vue 渲染时间
        self._wait_loading_gone(timeout=timeout)  # 等待 loading 消失
        self.wait_vue_stable()
        # 确认页面确实加载了（轮询表头）
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: len(d.find_elements(
                    By.CSS_SELECTOR, '.el-table__header-wrapper th .cell'
                )) > 3
            )
        except TimeoutException:
            logger.warning("表头未在 %ds 内出现", timeout)

    def _wait_table_ready(self, timeout=10):
        """等待表格渲染完成（loading 消失 + Vue 稳定）"""
        self._wait_loading_gone(timeout)
        self.wait_vue_stable()

    # ==================================================================
    #  搜索区
    # ==================================================================

    def _click_search_select(self, index):
        """点击搜索区第 index 个下拉（0=维保类型, 1=状态）"""
        triggers = self.find_all(self.SELECT_TRIGGERS)
        if index >= len(triggers):
            raise IndexError(f"搜索区只有 {len(triggers)} 个下拉，请求第 {index} 个")
        self._scroll_into_view(triggers[index])
        triggers[index].click()
        self.wait_vue_stable()

    def select_type(self, type_name):
        """选择维保类型下拉（第一个）"""
        self._click_search_select(0)
        self._select_option(type_name)

    def select_status(self, status_name):
        """选择维保状态下拉（第二个）"""
        self._click_search_select(1)
        self._select_option(status_name)

    def click_search(self):
        """点击搜索按钮"""
        self.click(self.BTN_SEARCH)
        self._wait_table_ready()

    def click_reset(self):
        """点击重置按钮"""
        self.click(self.BTN_RESET)
        self._wait_table_ready()

    def _get_visible_dialog(self, timeout=None):
        """获取当前可见弹窗（el-overlay-dialog 可能有多个，返回可见的）"""
        deadline = time.time() + (timeout or self.timeout)
        while time.time() < deadline:
            dialogs = self.driver.find_elements(*self.DIALOG)
            for dlg in dialogs:
                try:
                    if dlg.is_displayed():
                        return dlg
                except Exception:
                    continue
            self.wait_vue_stable()
        raise TimeoutException("未找到可见的 el-overlay-dialog")

    def wait_dialog_open(self, timeout=None):
        """等待弹窗出现"""
        self.wait_vue_stable()
        self._get_visible_dialog(timeout)

    def click_add(self):
        """点击新增计划按钮"""
        # 关闭可能残留的弹窗
        try:
            dlg = self.driver.find_element(By.CSS_SELECTOR, '.el-overlay-dialog[role="dialog"]')
            if dlg.is_displayed():
                logger.info("检测到残留弹窗，先关闭")
                self.click_dialog_cancel()
                self.wait_vue_stable()
        except Exception:
            pass

        self.js_click(self.BTN_ADD)
        self.wait_vue_stable()
        self.wait_dialog_open()

    def wait_dialog_close(self, timeout=None):
        """等待弹窗关闭（覆盖 BasePage — 本页面使用 el-overlay-dialog）"""
        t = timeout or self.timeout
        self.wait_until_gone(
            (By.CSS_SELECTOR, '.el-overlay-dialog[role="dialog"]'),
            timeout=t,
        )
        self.wait_overlay_gone(timeout=10)

    # ==================================================================
    #  搜索区 — 权限检查
    # ==================================================================

    def is_add_button_visible(self):
        """新增计划按钮是否可见"""
        return self.is_visible(self.BTN_ADD, timeout=2)

    # ==================================================================
    #  表格 — 通用操作
    # ==================================================================

    def get_table_headers(self):
        """JS提取表格表头（含重试，应对Element Plus异步渲染）"""
        for attempt in range(6):
            try:
                self._wait_table_ready() if hasattr(self, '_wait_table_ready') else self._wait_loading_gone(timeout=2)
            except:
                self._wait_loading_gone(timeout=2)
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
        """获取当前页行数 (仅第一个 el-table = 维保计划, 排除登录日志/设备状态干扰)"""
        self._wait_table_ready()
        count = self.driver.execute_script("""
            var tables = document.querySelectorAll('.el-table');
            if (!tables.length) return 0;
            var rows = tables[0].querySelectorAll('tbody tr.el-table__row');
            return rows.length;
        """)
        return count

    def get_column_data(self, col_index):
        """获取指定列（1-based）所有行数据"""
        self._wait_table_ready()
        cells = self.find_all(
            (By.CSS_SELECTOR,
             f'.el-table__body-wrapper tbody td:nth-child({col_index}) .cell')
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
        """在指定行点击操作按钮（JS click 避免 fixed 列遮挡）"""
        logger.info("对「%s」点击操作: %s", row_identifier, button_text)
        xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td[contains(normalize-space(.),"{row_identifier}")]]'
            f'//button[contains(.,"{button_text}")]'
        )
        self.js_click((By.XPATH, xpath))
        self.wait_vue_stable()

    def click_edit(self, row_identifier):
        """编辑维保计划"""
        self.click_row_button(row_identifier, self.ROW_BTN_TEXT['edit'])
        self.wait_dialog_open()

    def click_generate_task(self, row_identifier):
        """生成维保任务"""
        self.click_row_button(row_identifier, self.ROW_BTN_TEXT['generate_task'])

    def get_row_status(self, row_identifier):
        """获取指定行的计划状态

        Args:
            row_identifier: 行标识文本

        Returns:
            str: 状态文本，未找到返回空字符串
        """
        status_idx = self.get_column_index_by_header("状态")
        if not status_idx:
            return ''
        col_data = self.get_column_data(status_idx)
        # 通过行内其他列定位 — 简化：直接检查行文本
        xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td[contains(normalize-space(.),"{row_identifier}")]]'
            f'//td[{status_idx}]//span[contains(@class,"el-tag")]'
        )
        try:
            el = self.driver.find_element(By.XPATH, xpath)
            return (el.text or '').strip()
        except Exception:
            return ''

    # ==================================================================
    #  分页
    # ==================================================================

    # get_total_count() 继承自 BasePage (含 JS 兜底)

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
                By.CSS_SELECTOR,
                '.el-pagination__sizes .el-select .el-select__selected-item',
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
        """切换每页条数（size 为数字如 10/20/50/100）"""
        self.click(self.PAGE_SIZE_SELECT)
        self.wait_vue_stable()
        # 尝试多种格式匹配选项文本
        self._select_option(str(size) + "条/页")
        self._wait_table_ready()

    def jump_to_page(self, page_num):
        """使用跳转输入框跳转到指定页"""
        el = self.find(self.PAGE_JUMPER_INPUT)
        self._scroll_into_view(el)
        el.clear()
        el.send_keys(str(page_num))
        el.send_keys('\n')
        self.wait_vue_stable()
        self._wait_table_ready()

    # ==================================================================
    #  新增/编辑弹窗 — 表单填充
    # ==================================================================

    def get_form_dialog_title(self):
        """获取弹窗标题"""
        return self.get_text(self.DIALOG_FORM_TITLE)

    def fill_form_plan_name(self, name):
        """填写计划名称"""
        self.fill_dialog_input("计划名称", name)

    def fill_form_equipment(self, device_name):
        """选择关联设备（下拉）"""
        self._dialog_select("关联设备", device_name)

    def fill_form_type(self, type_name):
        """选择维保类型（下拉）"""
        self._dialog_select("维保类型", type_name)

    def fill_form_cycle(self, days):
        """填写周期（天）"""
        self.fill_dialog_input("周期(天)", str(days))

    def fill_form_remark(self, remark):
        """填写备注"""
        self.fill_dialog_input("备注", remark)

    def fill_form_all(self, data):
        """一键填写全部表单字段

        Args:
            data: dict，支持 planName/deviceName/maintenanceType/cycle/remark
        """
        if data.get('planName') is not None:
            self.fill_form_plan_name(data['planName'])
        if data.get('deviceName') is not None:
            self.fill_form_equipment(data['deviceName'])
        if data.get('maintenanceType') is not None:
            self.fill_form_type(data['maintenanceType'])
        if data.get('cycle') is not None:
            self.fill_form_cycle(data['cycle'])
        if data.get('remark') is not None:
            self.fill_form_remark(data['remark'])

    def click_form_save(self):
        """点击弹窗保存按钮（scope 到可见弹窗）

        Returns:
            str: Toast 消息文本
        """
        # 获取当前可见弹窗，在其内部找 primary 按钮
        dlg = self._get_visible_dialog()
        btn = dlg.find_element(By.CSS_SELECTOR, '.el-button--primary')
        self._js_click_el(btn)
        self.wait_overlay_gone(timeout=5)
        self.wait_vue_stable()
        toast = self.wait_for_toast_text(timeout=5)
        logger.info("操作结果 Toast: %s", toast)
        self._wait_table_ready()
        return toast

    def click_form_cancel(self):
        """点击弹窗取消按钮（scope 到可见弹窗）"""
        dlg = self._get_visible_dialog()
        btn = dlg.find_element(By.CSS_SELECTOR, '.el-button:not(.el-button--primary)')
        self._js_click_el(btn)
        self.wait_dialog_close()

    def get_form_error(self):
        """获取表单校验错误文本"""
        return super().get_form_error()

    # ==================================================================
    #  内部方法
    # ==================================================================

    def _click_select_trigger(self, trigger_locator):
        """点击下拉触发器展开下拉列表"""
        self.click(trigger_locator)
        self.wait_vue_stable()

    def _select_option(self, option_text):
        """选择下拉选项"""
        super()._select_option(option_text)

    def _dialog_select(self, label_text, option_text):
        """弹窗下拉选择（支持 filterable 和普通 el-select）"""
        item = self._get_dialog_form_item(label_text)
        wrapper = item.find_element(
            By.XPATH, './/div[contains(@class,"el-select__wrapper")]'
        )
        self._scroll_into_view(wrapper)

        # 判断是否为 filterable（可搜索）下拉
        select_el = item.find_element(By.CSS_SELECTOR, '.el-select')
        select_classes = select_el.get_attribute('class') or ''
        is_filterable = 'is-filterable' in select_classes

        # 点击打开下拉
        from selenium.webdriver.common.action_chains import ActionChains
        ActionChains(self.driver).move_to_element(wrapper).click().perform()
        self.wait_vue_stable()

        if is_filterable:
            # filterable 下拉：输入框在 .el-select__wrapper 内部（input.el-select__input）
            self.wait_vue_stable()
            try:
                # 找到 el-select__wrapper 内部的 input
                filter_input = wrapper.find_element(
                    By.CSS_SELECTOR, 'input.el-select__input'
                )
                filter_input.clear()
                filter_input.send_keys(option_text)
                self._wait_loading_gone(timeout=3)  # 等待异步 API 搜索返回
                filter_input.send_keys('\n')   # Enter 选择第一项
                self.wait_vue_stable()
                return
            except Exception:
                logger.debug("filterable 搜索框操作失败，回退到常规选择")

        # 常规下拉（非 filterable）
        # 等待下拉面板选项出现
        try:
            WebDriverWait(self.driver, 6).until(
                lambda d: len(d.find_elements(
                    By.CSS_SELECTOR,
                    '.el-select-dropdown:not([style*=\"display: none\"]) .el-select-dropdown__item, '
                    '.el-popper:not([style*=\"display: none\"]) li[role=\"option\"]'
                )) > 0
            )
        except TimeoutException:
            logger.warning("下拉选项未在 %ds 内出现", 6)

        # 选择选项
        self.wait_vue_stable()
        self._select_option(option_text)
