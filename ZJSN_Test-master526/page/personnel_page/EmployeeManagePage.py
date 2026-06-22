"""员工管理页面操作类

重构记录:
    2025-XX-XX: 继承 BasePage, 替换 time.sleep 为智能等待, 替换绝对 XPath 为 CSS/相对 XPath,
                新增 navigate() 方法, 添加统一日志记录.
"""
import logging
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class EmployeeManagePage(BasePage):
    """员工管理页面操作"""

    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)
        self.logger = logging.getLogger(__name__)

    # ==================== 导航定位 ====================

    def navigate(self):
        """导航到员工管理页面"""
        self.navigate_to("人员管理", "员工管理")

    # ==================== 基础定位 ====================
    TITLE = (By.XPATH, '//h2[contains(normalize-space(.),"员工") or contains(normalize-space(.),"人员")]')
    TABLE_HEADERS = (By.XPATH, '//div[contains(@class,"el-table__header-wrapper")]//th//div[contains(@class,"cell")]')

    # ==================== 搜索区域 ====================
    SEARCH_DEPT_INPUT = (By.XPATH, '//input[contains(@placeholder,"搜索部门")]')
    SEARCH_NAME_INPUT = (By.XPATH, '//input[contains(@placeholder,"请输入姓名") or contains(@placeholder,"姓名或工号") or contains(@placeholder,"姓名/工号")]')
    POSITION_SELECT = (By.XPATH, '//div[contains(@class,"el-select")][.//span[contains(normalize-space(.),"选择岗位")]]')
    STATUS_SELECT = (By.XPATH, '//div[contains(@class,"el-select")][.//span[contains(normalize-space(.),"员工状态") or contains(normalize-space(.),"在职")]]')
    RESET_BUTTON = (By.XPATH, '//button[not(contains(@class,"el-button--primary"))]//span[contains(normalize-space(.),"重置")]/parent::button')
    SEARCH_BUTTON = (By.XPATH, '//button[.//span[contains(normalize-space(.),"搜索") or contains(normalize-space(.),"查询")]]')
    EXPORT_BUTTON = (By.XPATH, '//button[.//span[contains(normalize-space(.),"导出")]]')

    def navigate_to_employee_management(self):
        """导航到员工管理页面（旧接口，保留兼容性）"""
        self.navigate_to("人员管理", "员工管理")
        self._wait_settled()

    def _wait_settled(self, timeout=10):
        """等待页面加载完成（保留旧接口，委托到 BasePage 方法）"""
        self._wait_loading_gone(timeout=timeout)
        self.wait_vue_stable()

    def is_page_loaded(self):
        """判断页面是否加载完成 — 多重检测"""
        indicators = [
            (By.XPATH, '//div[contains(@class,"el-table")]'),
            (By.XPATH, '//div[contains(@class,"el-table__header")]'),
            (By.CSS_SELECTOR, '.el-table, .el-table__header-wrapper'),
            (By.XPATH, '//*[contains(@class,"table")]'),
            (By.XPATH, '//span[contains(text(),"员工")]'),
            (By.XPATH, '//*[contains(text(),"共") and contains(text(),"条")]'),
        ]
        for locator in indicators:
            try:
                self.find_visible(locator, timeout=3)
                return True
            except Exception:
                continue
        # Final check: any non-empty content area
        try:
            text = self.driver.execute_script(
                "return document.querySelector('.el-main, .app-main, main')?.textContent?.trim() || ''"
            )
            return len(text) > 20
        except Exception:
            return False

    def get_table_header_texts(self):
        """获取表格表头文本列表"""
        try:
            headers = self.find_all(self.TABLE_HEADERS)
            return [h.text.strip() for h in headers if h.text.strip()]
        except Exception:
            return []

    def get_table_row_count(self):
        """获取当前页表格行数"""
        return super().get_table_row_count()

    def get_total_count_text(self):
        """获取分页总数文本"""
        try:
            return self.get_text(self.TOTAL_COUNT, timeout=3)
        except Exception:
            return ''

    def get_total_count(self):
        """获取分页总数数值"""
        return super().get_total_count()

    def click_reset(self):
        """点击重置按钮"""
        self.click(self.RESET_BUTTON)
        self.wait_vue_stable()

    def click_search(self):
        """点击搜索按钮"""
        self.click(self.SEARCH_BUTTON)
        self.wait_vue_stable()

    def input_search_name(self, value):
        """输入搜索姓名"""
        el = self.find_visible(self.SEARCH_NAME_INPUT)
        el.send_keys(Keys.CONTROL + 'a')
        el.send_keys(Keys.DELETE)
        el.send_keys(value)

    def input_search_dept(self, value):
        """输入搜索部门"""
        el = self.find_visible(self.SEARCH_DEPT_INPUT)
        el.send_keys(Keys.CONTROL + 'a')
        el.send_keys(Keys.DELETE)
        el.send_keys(value)

    def click_next_page(self):
        """点击下一页"""
        super().click_next_page()

    def click_prev_page(self):
        """点击上一页"""
        super().click_prev_page()

    def select_page_size(self, size):
        """选择每页显示条数"""
        select = self.find_clickable(self.PAGE_SIZE_SELECT)
        select.click()
        self.wait_vue_stable()
        option = self.find_clickable((By.XPATH, f'//li[contains(@class,"el-select-dropdown__item") and contains(.,"{size}")]'))
        option.click()
        self.wait_vue_stable()
