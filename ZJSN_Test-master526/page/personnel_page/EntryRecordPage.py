"""入场记录页面 Page Object

人员管理 > 承包商管理 > 入场记录
路由: #/personnel/contractor/record

功能: 查看所有承包商人员的入场历史记录（只读/导出为主）
变更记录:
  2026-06-15: 新建 — 继承 BasePage，遵循 PostManagePage 重构模式
"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class EntryRecordPage(BasePage):
    """入场记录页面操作 — 继承 BasePage"""

    # ══════════════════════════════════════════════════════════════════
    #  搜索区域
    # ══════════════════════════════════════════════════════════════════
    SEARCH_NAME_INPUT = (By.XPATH, '//input[contains(@placeholder,"姓名") or contains(@placeholder,"人员") or contains(@placeholder,"搜索") or contains(@placeholder,"申请人")]')
    SEARCH_UNIT_SELECT = (
        By.XPATH,
        '//div[contains(@class,"el-form") or contains(@class,"search-bar")]'
        '//div[contains(@class,"el-select")][.//span[contains(.,"承包商") or contains(.,"单位")]]',
    )
    SEARCH_DATE_RANGE_START = (By.XPATH, '//input[contains(@placeholder,"开始") or contains(@placeholder,"入场时间")][1]')
    SEARCH_DATE_RANGE_END = (By.XPATH, '//input[contains(@placeholder,"结束") or contains(@placeholder,"离场时间")]')

    # ══════════════════════════════════════════════════════════════════
    #  工具栏
    # ══════════════════════════════════════════════════════════════════
    EXPORT_BUTTON = (By.XPATH, '//button[.//span[contains(.,"导出")]]')

    # ══════════════════════════════════════════════════════════════════
    #  表格
    # ══════════════════════════════════════════════════════════════════
    TABLE_COLUMN_HEADERS = (By.XPATH, '//div[contains(@class,"el-table__header-wrapper")]//th//div[contains(@class,"cell")]')

    # ══════════════════════════════════════════════════════════════════
    #  表格列索引（1-based）
    # ══════════════════════════════════════════════════════════════════
    COL_NAME = 1
    COL_UNIT = 2
    COL_ID_CARD = 3
    COL_ENTRY_TIME = 4
    COL_EXIT_TIME = 5
    COL_APPROVAL_STATUS = 6
    COL_APPROVER = 7
    COL_OPERATIONS = 8

    # ══════════════════════════════════════════════════════════════════
    #  分页
    # ══════════════════════════════════════════════════════════════════
    PAGE_SIZE_SELECT = (By.CSS_SELECTOR, '.el-pagination .el-select__wrapper')
    NEXT_PAGE_BUTTON = (By.CSS_SELECTOR, '.el-pagination .btn-next')
    PREV_PAGE_BUTTON = (By.CSS_SELECTOR, '.el-pagination .btn-prev')
    CURRENT_PAGE = (By.XPATH, '//div[contains(@class,"el-pagination")]//button[contains(@class,"is-active") or contains(@class,"active")]')
    PAGE_SIZE_OPTION = '//li[contains(@class,"el-select-dropdown__item") and contains(., "{size}")]'

    # ══════════════════════════════════════════════════════════════════
    #  行内操作按钮
    # ══════════════════════════════════════════════════════════════════
    TABLE_DETAIL_BUTTON = (By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[contains(text(),"详情") or contains(text(),"查看")]]')

    def __init__(self, driver, timeout=None):
        """初始化入场记录页面"""
        super().__init__(driver, timeout)

    # ══════════════════════════════════════════════════════════════════
    #  导航
    # ══════════════════════════════════════════════════════════════════

    def navigate(self):
        """导航到入场记录页面"""
        logger.info("导航到 → 人员管理 → 承包商管理 → 入场记录")
        self.navigate_to("人员管理", "承包商管理", "入场记录")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        if not self.is_page_loaded():
            raise Exception("入场记录页面加载失败")
        return self

    # ══════════════════════════════════════════════════════════════════
    #  页面状态验证
    # ══════════════════════════════════════════════════════════════════

    def is_page_loaded(self):
        """判断页面是否加载完成"""
        try:
            self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[contains(@class,"el-table")]')
                )
            )
            return True
        except Exception:
            return False

    def get_table_header_texts(self):
        """获取表格所有列头文本"""
        try:
            headers = self.wait.until(
                EC.presence_of_all_elements_located(self.TABLE_COLUMN_HEADERS)
            )
            return [h.text.strip() for h in headers if h.text.strip()]
        except Exception:
            return []

    def get_table_row_count(self):
        """获取当前页表格行数"""
        try:
            return len(self.find_all(self.TABLE_ROWS))
        except Exception:
            return 0

    def get_column_data(self, col_index):
        """获取指定列（1-based）的所有行数据"""
        try:
            rows = self.find_all(self.TABLE_ROWS)
            data = []
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, 'td')
                if col_index <= len(cells):
                    data.append(cells[col_index - 1].text.strip())
            return data
        except Exception:
            return []

    def get_first_row_data(self):
        """获取第一行所有列的数据"""
        try:
            row = self.wait.until(EC.presence_of_element_located(self.TABLE_ROWS))
            cells = row.find_elements(By.TAG_NAME, 'td')
            return [cell.text.strip() for cell in cells]
        except Exception:
            return []

    def get_total_count_text(self):
        """获取总条数文本"""
        try:
            el = self.wait.until(EC.visibility_of_element_located(self.TOTAL_COUNT))
            return el.text.strip()
        except Exception:
            return ''

    def get_total_count(self):
        """解析总条数数字"""
        return super().get_total_count()

    def get_current_page_number(self):
        """获取当前页码"""
        try:
            el = self.wait.until(EC.presence_of_element_located(self.CURRENT_PAGE))
            text = el.text.strip()
            return int(text) if text.isdigit() else 1
        except Exception:
            return 1

    # ══════════════════════════════════════════════════════════════════
    #  搜索
    # ══════════════════════════════════════════════════════════════════

    def input_search_name(self, value):
        """输入搜索关键词（人员姓名）"""
        el = self.wait.until(EC.visibility_of_element_located(self.SEARCH_NAME_INPUT))
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        el.send_keys(value)
        logger.info("已输入搜索人员姓名: %s", value)

    def input_date_start(self, value):
        """输入入场开始日期"""
        el = self.wait.until(EC.visibility_of_element_located(self.SEARCH_DATE_RANGE_START))
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        el.send_keys(value)
        logger.info("已输入开始日期: %s", value)

    def input_date_end(self, value):
        """输入入场结束日期"""
        el = self.wait.until(EC.visibility_of_element_located(self.SEARCH_DATE_RANGE_END))
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        el.send_keys(value)
        logger.info("已输入结束日期: %s", value)

    def click_search(self):
        """点击查询按钮"""
        self.click_search_button()
        self.wait_vue_stable()

    def click_reset(self):
        """点击重置按钮"""
        self.click_reset_button()
        self.wait_vue_stable()

    def select_search_unit(self, unit_text):
        """选择搜索条件中的承包商单位"""
        self.click(self.SEARCH_UNIT_SELECT)
        self._select_option(unit_text)
        logger.info("已选择搜索单位: %s", unit_text)

    # ══════════════════════════════════════════════════════════════════
    #  分页
    # ══════════════════════════════════════════════════════════════════

    def is_next_page_enabled(self):
        """下一页按钮是否可用"""
        try:
            btn = self.driver.find_element(*self.NEXT_PAGE_BUTTON)
            return btn.is_enabled()
        except Exception:
            return False

    def is_prev_page_enabled(self):
        """上一页按钮是否可用"""
        try:
            btn = self.driver.find_element(*self.PREV_PAGE_BUTTON)
            return btn.is_enabled()
        except Exception:
            return False

    def click_next_page(self):
        """点击下一页"""
        super().click_next_page()

    def click_prev_page(self):
        """点击上一页"""
        super().click_prev_page()

    def select_page_size(self, size):
        """切换每页条数"""
        try:
            select = self.wait.until(EC.element_to_be_clickable(self.PAGE_SIZE_SELECT))
            self.driver.execute_script("arguments[0].click();", select)
            self.wait_vue_stable()
            option_xpath = self.PAGE_SIZE_OPTION.format(size=size)
            option = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, option_xpath))
            )
            self.driver.execute_script("arguments[0].click();", option)
            self.wait_vue_stable()
            logger.info("已切换每页条数为: %s", size)
        except Exception as e:
            raise Exception(f"切换每页条数失败: {e}")

    # ══════════════════════════════════════════════════════════════════
    #  导出
    # ══════════════════════════════════════════════════════════════════

    def click_export(self):
        """点击导出按钮"""
        self.click(self.EXPORT_BUTTON)
        self.wait_vue_stable()
        logger.info("已点击导出按钮")

    # ══════════════════════════════════════════════════════════════════
    #  详情查看
    # ══════════════════════════════════════════════════════════════════

    def click_detail_by_name(self, person_name):
        """点击指定人员姓名的详情按钮"""
        try:
            self.click_row_button(person_name, "详情")
            self.wait_vue_stable()
            self.wait_dialog_open(timeout=10)
            logger.info("已点击人员「%s」的详情按钮", person_name)
        except Exception:
            try:
                self.click_row_button(person_name, "查看")
                self.wait_vue_stable()
                self.wait_dialog_open(timeout=10)
                logger.info("已点击人员「%s」的查看按钮", person_name)
            except Exception as e:
                raise Exception(f"未找到人员「{person_name}」的详情按钮: {e}")

    def get_dialog_title_text(self):
        """获取弹窗标题"""
        return self.get_dialog_title()

    def wait_dialog_closed(self, timeout=5):
        """等待弹窗关闭"""
        return self.wait_dialog_close(timeout)

    def click_dialog_close(self):
        """关闭详情弹窗"""
        super().click_dialog_cancel()
        logger.info("已关闭详情弹窗")

    def get_toast_text(self, timeout=10):
        """获取操作提示消息"""
        return self.wait_for_toast_text(timeout)


if __name__ == "__main__":
    """测试入场记录页面导航"""
    from base.browser_driver import BaseDriver
    from page.LoginPage import LoginPage

    base = BaseDriver()
    try:
        driver = base.open_browser()
        login_page = LoginPage(driver)
        login_page.login("admin", "admin123")

        record_page = EntryRecordPage(driver)
        record_page.navigate()
    finally:
        base.close_browser()
