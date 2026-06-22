"""DCS 全部点位页面 Page Object

==== 页面概述 ====
路径：DCS 数据监控 → 全部点位
路由：#/all-data
功能：全部点位列表管理 — 搜索、新增、编辑、删除、批量操作
类型：列表页（CRUD + 批量选择）

==== 定位策略 ====
- CSS_SELECTOR 优先（Element Plus 标准类）
- 相对 XPath 仅用于文本内容匹配
- 禁止：绝对 XPath
"""
import logging
from selenium.webdriver.common.by import By
from base.base_page import BasePage

logger = logging.getLogger(__name__)


class AllDataPage(BasePage):
    """全部点位 Page Object"""

    # ==================== 搜索/筛选区 ====================
    SEARCH_INPUT = (By.CSS_SELECTOR, 'input[placeholder*="点位" i], input[placeholder*="点位名称" i]')
    BTN_SEARCH = (By.XPATH, '//button[normalize-space(.//span)="搜索"]')
    BTN_RESET = (By.XPATH, '//button[normalize-space(.//span)="重置"]')

    # 类型/状态筛选下拉
    SELECT_TYPE = (By.CSS_SELECTOR, '.search-area .el-select, .filter-bar .el-select')

    # ==================== 操作按钮 ====================
    BTN_ADD = (By.XPATH, '//button[normalize-space(.//span)="新增"] | //button[normalize-space(.//span)="新增点位"]')
    BTN_IMPORT = (By.XPATH, '//button[normalize-space(.//span)="导入"]')
    BTN_EXPORT = (By.XPATH, '//button[normalize-space(.//span)="导出"]')
    BTN_REFRESH = (By.XPATH, '//button[normalize-space(.//span)="刷新"]')
    BTN_BATCH_DELETE = (By.XPATH, '//button[.//span[text()="批量删除"]]')
    BTN_BATCH_ENABLE = (By.XPATH, '//button[.//span[text()="启用"]]')
    BTN_BATCH_DISABLE = (By.XPATH, '//button[.//span[text()="禁用"]]')

    # ==================== 表格区 ====================
    TABLE = (By.CSS_SELECTOR, '.el-table')
    TABLE_BODY = (By.CSS_SELECTOR, '.el-table__body-wrapper')
    TABLE_ROWS = (By.CSS_SELECTOR, '.el-table__body-wrapper tbody tr.el-table__row')
    TABLE_LOADING = (By.CSS_SELECTOR, '.el-loading-mask')
    TABLE_EMPTY = (By.CSS_SELECTOR, '.el-table__empty-text')
    TABLE_CHECKBOX = (By.CSS_SELECTOR, '.el-checkbox__input')

    # ==================== 表格列定义（按索引） ====================
    # 0: Checkbox | 1: 点位ID | 2: 点位名称 | 3: 类型 | 4: 单位
    # 5: 采集周期 | 6: 状态 | 7: 上报率 | 8: 操作
    CELL_POINT_ID = (By.CSS_SELECTOR, 'td:nth-child(2) .cell')
    CELL_POINT_NAME = (By.CSS_SELECTOR, 'td:nth-child(3) .cell')
    CELL_POINT_TYPE = (By.CSS_SELECTOR, 'td:nth-child(4) .cell')
    CELL_STATUS = (By.CSS_SELECTOR, 'td:nth-child(7) .cell, td:nth-child(6) .cell')

    # ==================== 分页 ====================
    PAGINATION = (By.CSS_SELECTOR, '.el-pagination')
    TOTAL_COUNT = (By.CSS_SELECTOR, '.el-pagination__total')
    BTN_NEXT_PAGE = (By.CSS_SELECTOR, '.el-pagination button.btn-next')
    BTN_PREV_PAGE = (By.CSS_SELECTOR, '.el-pagination button.btn-prev')

    # ==================== 弹窗表单 ====================
    # 使用 BasePage 的 DIALOG / DIALOG_SAVE / DIALOG_CANCEL 通用定位器
    DIALOG_INPUT_NAME = (By.CSS_SELECTOR, '.el-dialog input[placeholder*="名称"]')
    DIALOG_INPUT_ID = (By.CSS_SELECTOR, '.el-dialog input[placeholder*="ID" i]')
    DIALOG_SELECT_TYPE = (By.CSS_SELECTOR, '.el-dialog .el-select')
    DIALOG_SELECT_DEVICE = (By.CSS_SELECTOR, '.el-dialog .el-select:nth-of-type(2)')

    # ==================== 页面入口 ====================

    HASH_ROUTE = "#/all-data"

    def navigate(self):
        """导航到全部点位页面"""
        logger.info("导航: DCS 数据监控 → 全部点位 (%s)", self.HASH_ROUTE)
        self.navigate_to_by_hash(self.HASH_ROUTE, "全部点位")
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
        """按类型筛选（模拟量/开关量/计数）"""
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
        self.wait_element_visible(self.TABLE, timeout=10)
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
        """检查表格中是否存在指定文本的点位"""
        return super().is_row_present(text)

    def get_total_count(self) -> int:
        """获取总条数（从分页）"""
        return super().get_total_count()

    # ==================== 批量选择 ====================

    def select_row(self, row_identifier: str):
        """勾选指定行"""
        logger.info("勾选行: %s", row_identifier)
        row = self._find_row_by_text(row_identifier)
        if row:
            checkbox = row.find_element(*self.TABLE_CHECKBOX)
            checkbox.click()
            self.wait_vue_stable()
        return self

    def select_all_rows(self):
        """全选所有行"""
        logger.info("全选所有行")
        header_checkbox = (By.CSS_SELECTOR, '.el-table__header-wrapper .el-checkbox__input')
        self.click(header_checkbox)
        self.wait_vue_stable()
        return self

    def get_selected_count(self) -> int:
        """获取已选行数"""
        try:
            checked = self.find_all((By.CSS_SELECTOR, '.el-table__row .el-checkbox.is-checked'))
            return len(checked)
        except Exception:
            return 0

    # ==================== CRUD 操作 ====================

    def click_add(self):
        """点击新增按钮"""
        logger.info("点击新增点位")
        self.click(self.BTN_ADD)
        self.wait_dialog_open()
        return self

    def click_import(self):
        """点击导入按钮"""
        logger.info("点击导入")
        self.click(self.BTN_IMPORT)
        self.wait_vue_stable()
        return self

    def click_export(self):
        """点击导出按钮"""
        logger.info("点击导出")
        self.click(self.BTN_EXPORT)
        self.wait_vue_stable()
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

    def click_detail(self, row_identifier: str):
        """查看点位详情"""
        logger.info("查看点位详情: %s", row_identifier)
        self.click_row_button(row_identifier, "详情")
        self.wait_dialog_open()
        return self

    def confirm_delete(self):
        """确认删除（Element Plus message-box）"""
        self.click((By.XPATH, '//button[contains(@class, "el-button--primary")]//span[text()="确定"]'))
        self.wait_vue_stable()
        return self

    # ==================== 弹窗表单 ====================

    def fill_name(self, name: str):
        """填写点位名称"""
        self.input_text(self.DIALOG_INPUT_NAME, name)
        return self

    def fill_form(self, data: dict):
        """填充表单（通过标签匹配）"""
        logger.info("填充表单: %s", data)
        for field, value in data.items():
            locator = (By.XPATH,
                       f'//div[contains(@class, "el-form-item")]'
                       f'//label[contains(text(),"{field}")]/following-sibling::div//input')
            self.input_text(locator, str(value))
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

    # ==================== 辅助方法 ====================

    def _find_row_by_text(self, text: str):
        """根据文本查找表格行"""
        try:
            return self.find((By.XPATH, f'//tr[contains(@class, "el-table__row")]//td[contains(text(),"{text}")]/..'))
        except Exception:
            return None

    def go_to_next_page(self):
        """翻到下一页"""
        self.click_next_page()
        self._wait_loading_gone()
        return self

    def go_to_prev_page(self):
        """翻到上一页"""
        self.click_prev_page()
        self._wait_loading_gone()
        return self
