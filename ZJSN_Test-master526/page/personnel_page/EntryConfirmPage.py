"""入场确认页面 Page Object

人员管理 > 承包商管理 > 入场确认
路由: #/personnel/contractor/confirm

功能: 安保人员确认承包商人员实际入场（单条/批量）
变更记录:
  2026-06-15: 新建 — 继承 BasePage，遵循 EntryRecordPage 模式
"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class EntryConfirmPage(BasePage):
    """入场确认页面操作 — 继承 BasePage"""

    # ══════════════════════════════════════════════════════════════════
    #  搜索区域
    # ══════════════════════════════════════════════════════════════════
    SEARCH_CONTRACTOR_INPUT = (By.XPATH, '//input[contains(@placeholder,"承包商名称") or contains(@placeholder,"承包商")]')
    SEARCH_PERSONNEL_INPUT = (By.XPATH, '//input[contains(@placeholder,"人员姓名") or contains(@placeholder,"人员")]')

    # ══════════════════════════════════════════════════════════════════
    #  工具栏
    # ══════════════════════════════════════════════════════════════════
    BATCH_CONFIRM_BUTTON = (By.XPATH, '//button[.//span[contains(text(),"批量确认入场")]]')

    # ══════════════════════════════════════════════════════════════════
    #  表格
    # ══════════════════════════════════════════════════════════════════
    TABLE_COLUMN_HEADERS = (By.XPATH, '//div[contains(@class,"el-table__header-wrapper")]//th//div[contains(@class,"cell")]')

    # ══════════════════════════════════════════════════════════════════
    #  表格列索引（1-based）
    # ══════════════════════════════════════════════════════════════════
    COL_CHECKBOX = 1
    COL_REQUEST_NO = 2
    COL_CONTRACTOR = 3
    COL_PERSONNEL = 4
    COL_WORK_TYPE = 5
    COL_WORK_AREA = 6
    COL_PLANNED_ENTRY = 7
    COL_ENTRY_REASON = 8
    COL_OPERATIONS = 9

    # ══════════════════════════════════════════════════════════════════
    #  分页
    # ══════════════════════════════════════════════════════════════════
    PAGE_SIZE_SELECT = (By.CSS_SELECTOR, '.el-pagination .el-select__wrapper')
    NEXT_PAGE_BUTTON = (By.CSS_SELECTOR, '.el-pagination .btn-next')
    PREV_PAGE_BUTTON = (By.CSS_SELECTOR, '.el-pagination .btn-prev')
    CURRENT_PAGE = (By.XPATH, '//div[contains(@class,"el-pagination")]//button[contains(@class,"is-active") or contains(@class,"active")]')
    PAGE_SIZE_OPTION = '//li[contains(@class,"el-select-dropdown__item") and contains(., "{size}")]'

    # ══════════════════════════════════════════════════════════════════
    #  行复选框
    # ══════════════════════════════════════════════════════════════════
    ROW_CHECKBOX = (
        By.XPATH,
        '//tr[contains(@class,"el-table__row")]//td[1]//input[@type="checkbox"]',
    )

    def __init__(self, driver, timeout=None):
        """初始化入场确认页面"""
        super().__init__(driver, timeout)

    # ══════════════════════════════════════════════════════════════════
    #  导航
    # ══════════════════════════════════════════════════════════════════

    def navigate(self):
        """导航到入场确认页面"""
        logger.info("导航到 → 人员管理 → 承包商管理 → 入场确认")
        self.navigate_to("人员管理", "承包商管理", "入场确认")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        if not self.is_page_loaded():
            raise Exception("入场确认页面加载失败")
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

    def input_contractor_name(self, value):
        """输入承包商名称搜索关键词"""
        el = self.wait.until(EC.visibility_of_element_located(self.SEARCH_CONTRACTOR_INPUT))
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        el.send_keys(value)
        logger.info("已输入搜索承包商名称: %s", value)

    def input_personnel_name(self, value):
        """输入人员姓名搜索关键词"""
        el = self.wait.until(EC.visibility_of_element_located(self.SEARCH_PERSONNEL_INPUT))
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        el.send_keys(value)
        logger.info("已输入搜索人员姓名: %s", value)

    def click_search(self):
        """点击查询按钮"""
        self.click_search_button()
        self.wait_vue_stable()

    def click_reset(self):
        """点击重置按钮"""
        self.click_reset_button()
        self.wait_vue_stable()

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
    #  确认入场操作
    # ══════════════════════════════════════════════════════════════════

    def click_confirm_entry_by_name(self, person_name):
        """点击指定人员姓名的「确认入场」按钮（JS 绕过遮挡）"""
        try:
            self._js_click_by_text("确认入场", scope_contains=person_name)
            self.wait_vue_stable()
            logger.info("已点击人员「%s」的确认入场按钮", person_name)
        except Exception as e:
            raise Exception(f"未找到人员「{person_name}」的确认入场按钮: {e}")

    def click_batch_confirm(self):
        """点击批量确认入场按钮"""
        try:
            el = self.wait.until(EC.element_to_be_clickable(self.BATCH_CONFIRM_BUTTON))
            self.driver.execute_script("arguments[0].click();", el)
            self.wait_vue_stable()
            logger.info("已点击批量确认入场按钮")
        except Exception as e:
            raise Exception(f"点击批量确认入场失败: {e}")

    def confirm_dialog(self):
        """在确认弹窗中点击确定"""
        try:
            self.wait_dialog_open(timeout=5)
            self.click_dialog_save()
            self.wait_vue_stable()
            logger.info("已确认弹窗")
        except Exception:
            logger.info("无确认弹窗或已自动处理")

    # ══════════════════════════════════════════════════════════════════
    #  复选框操作
    # ══════════════════════════════════════════════════════════════════

    def select_row_by_name(self, person_name):
        """勾选指定人员姓名的行复选框"""
        try:
            row_checkbox = (
                By.XPATH,
                f'//tr[contains(@class,"el-table__row")]'
                f'[.//td[contains(text(),"{person_name}")]]'
                f'//input[@type="checkbox"]',
            )
            el = self.wait.until(EC.presence_of_element_located(row_checkbox))
            self.driver.execute_script("arguments[0].click();", el)
            self.wait_vue_stable()
            logger.info("已勾选人员「%s」的复选框", person_name)
        except Exception as e:
            raise Exception(f"勾选人员「{person_name}」复选框失败: {e}")

    def select_first_n_rows(self, n):
        """勾选前 N 行的复选框"""
        try:
            checkboxes = self.wait.until(
                EC.presence_of_all_elements_located(self.ROW_CHECKBOX)
            )
            for i in range(min(n, len(checkboxes))):
                self.driver.execute_script("arguments[0].click();", checkboxes[i])
            self.wait_vue_stable()
            logger.info("已勾选前 %d 行", n)
        except Exception as e:
            raise Exception(f"勾选前 {n} 行失败: {e}")

    def get_selected_count(self):
        """获取当前已选中的行数"""
        try:
            return len(self.find_all(
                (By.XPATH, '//tr[contains(@class,"el-table__row")]//td[1]//input[@type="checkbox" and @checked]')
            ))
        except Exception:
            return 0

    # ══════════════════════════════════════════════════════════════════
    #  状态读取
    # ══════════════════════════════════════════════════════════════════

    def get_unread_personnel_names(self):
        """获取所有状态为「未读」的人员姓名"""
        try:
            rows = self.find_all(self.TABLE_ROWS)
            names = []
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, 'td')
                if len(cells) >= self.COL_OPERATIONS:
                    # 检查是否有「未读」tag
                    tags = row.find_elements(
                        By.XPATH, './/span[contains(@class,"el-tag")]'
                    )
                    has_unread = any('未读' in (t.text.strip() or '') for t in tags)
                    if has_unread:
                        names.append(cells[self.COL_PERSONNEL - 1].text.strip())
            return names
        except Exception:
            return []

    def get_toast_text(self, timeout=10):
        """获取操作提示消息"""
        return self.wait_for_toast_text(timeout)


if __name__ == "__main__":
    """测试入场确认页面导航"""
    from base.browser_driver import BaseDriver
    from page.LoginPage import LoginPage

    base = BaseDriver()
    try:
        driver = base.open_browser()
        login_page = LoginPage(driver)
        login_page.login("admin", "admin123")

        confirm_page = EntryConfirmPage(driver)
        confirm_page.navigate()
    finally:
        base.close_browser()
