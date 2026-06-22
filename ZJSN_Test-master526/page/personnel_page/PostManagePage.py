"""岗位管理页面 Page Object — 重构版

变更记录:
  2026-06-11: 继承 BasePage，清理绝对 XPath，替换 time.sleep → BasePage 等待方法
"""
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class PostManagePage(BasePage):
    """岗位管理页面操作 — 继承 BasePage"""

    # ══════════════════════════════════════════════════════════════════
    #  搜索区域
    # ══════════════════════════════════════════════════════════════════
    SEARCH_NAME_INPUT = (By.XPATH, '//input[@placeholder="请输入岗位编码或名称"]')
    SEARCH_DEPT_SELECT = (
        By.XPATH,
        '//div[contains(@class,"el-form") or contains(@class,"search-bar")]'
        '//div[contains(@class,"el-select")][1]',
    )
    SEARCH_CATEGORY_SELECT = (
        By.XPATH,
        '//div[contains(@class,"el-form") or contains(@class,"search-bar")]'
        '//div[contains(@class,"el-select")][2]',
    )
    SEARCH_STATUS_SELECT = (
        By.XPATH,
        '//div[contains(@class,"el-form") or contains(@class,"search-bar")]'
        '//div[contains(@class,"el-select")][3]',
    )

    # ══════════════════════════════════════════════════════════════════
    #  工具栏
    # ══════════════════════════════════════════════════════════════════
    ADD_BUTTON = (By.XPATH, '//button[contains(.,"新增")]')

    # ══════════════════════════════════════════════════════════════════
    #  表格
    # ══════════════════════════════════════════════════════════════════
    TABLE_COLUMN_HEADERS = (By.XPATH, '//div[contains(@class,"el-table__header-wrapper")]//th//div[contains(@class,"cell")]')

    # ══════════════════════════════════════════════════════════════════
    #  表格列索引（1-based，与表格显示顺序一致）
    # ══════════════════════════════════════════════════════════════════
    COL_POST_CODE = 1
    COL_POST_NAME = 2
    COL_DEPT = 3
    COL_CATEGORY = 4
    COL_LEVEL = 5
    COL_HEADCOUNT = 6
    COL_STATUS = 7
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
    #  新增 / 编辑弹窗
    # ══════════════════════════════════════════════════════════════════

    # ══════════════════════════════════════════════════════════════════
    #  行内操作按钮
    # ══════════════════════════════════════════════════════════════════
    TABLE_EDIT_BUTTON = (By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[contains(text(),"编辑")]]')
    TABLE_TOGGLE_STATUS_BUTTON = (By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[contains(text(),"停用") or contains(text(),"启用")]]')
    TABLE_DELETE_BUTTON = (By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[contains(text(),"删除")]]')

    def __init__(self, driver, timeout=None):
        """初始化岗位管理页面 — 继承 BasePage"""
        super().__init__(driver, timeout)

    # ══════════════════════════════════════════════════════════════════
    #  导航
    # ══════════════════════════════════════════════════════════════════

    def navigate(self):
        """导航到岗位管理页面 — 唯一入口"""
        logger.info("导航到 → 人员管理 → 岗位管理")
        self.navigate_to("人员管理", "岗位管理")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        if not self.is_page_loaded():
            raise Exception("岗位管理页面加载失败")
        return self

    # 向后兼容别名
    def navigate_to_position_management(self):
        """@deprecated: 使用 navigate() 替代"""
        return self.navigate()

    # ══════════════════════════════════════════════════════════════════
    #  页面状态验证
    # ══════════════════════════════════════════════════════════════════

    def is_page_loaded(self):
        """判断页面是否加载完成（表格或关键元素存在）"""
        try:
            self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[contains(@class,"el-table")]')
                )
            )
            return True
        except Exception:
            return False

    def get_page_title_text(self):
        """获取页面主标题"""
        candidates = [
            (By.XPATH, '//header//h2'),
            (By.XPATH, '//h2[not(ancestor::div[contains(@style,"display: none")])]'),
            (By.XPATH, '//div[contains(@class,"page-header") or contains(@class,"page-title")]//h2'),
        ]
        for locator in candidates:
            try:
                el = self.wait.until(EC.presence_of_element_located(locator))
                text = el.text.strip()
                if text:
                    return text
            except Exception:
                continue
        return ''

    def get_table_header_texts(self):
        """获取表格所有列头的文本"""
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

    def is_post_name_present(self, post_name):
        """判断指定岗位名称是否在表格中存在"""
        return self.is_row_present(post_name)

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
        """输入搜索关键词"""
        el = self.wait.until(EC.visibility_of_element_located(self.SEARCH_NAME_INPUT))
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        el.send_keys(value)
        logger.info("已输入搜索关键词: %s", value)

    def click_search(self):
        """点击查询按钮"""
        self.click_search_button()
        self.wait_vue_stable()

    def click_reset(self):
        """点击重置按钮"""
        self.click_reset_button()
        self.wait_vue_stable()

    def select_search_category(self, category_text):
        """选择搜索条件中的岗位类别"""
        self.click(self.SEARCH_CATEGORY_SELECT)
        self._select_option(category_text)
        logger.info("已选择搜索岗位类别: %s", category_text)

    def select_search_status(self, status_text):
        """选择搜索条件中的状态"""
        self.click(self.SEARCH_STATUS_SELECT)
        self._select_option(status_text)
        logger.info("已选择搜索状态: %s", status_text)

    def select_search_dept(self, dept_text):
        """选择搜索条件中的部门"""
        self.click(self.SEARCH_DEPT_SELECT)
        self._select_option(dept_text)
        logger.info("已选择搜索部门: %s", dept_text)

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
    #  弹窗操作
    # ══════════════════════════════════════════════════════════════════

    def click_add_button(self):
        """点击新增岗位按钮"""
        self.click(self.ADD_BUTTON)
        self.wait_dialog_open(timeout=15)
        self.wait_vue_stable()
        logger.info("已点击新增岗位按钮")

    def get_dialog_title_text(self):
        """获取弹窗标题"""
        return self.get_dialog_title()

    def wait_dialog_closed(self, timeout=5):
        """等待弹窗关闭"""
        return self.wait_dialog_close(timeout)

    # ══════════════════════════════════════════════════════════════════
    #  表单填充
    # ══════════════════════════════════════════════════════════════════

    def fill_dialog_input(self, label_text, value):
        """按 label 文本找到弹窗输入框并输入"""
        super().fill_dialog_input(label_text, value)

    def clear_dialog_input(self, label_text):
        """清空弹窗输入框"""
        super().clear_dialog_input(label_text)

    def select_dialog_option(self, label_text, option_text):
        """在弹窗中点击下拉框并选择选项"""
        super().select_dialog_dropdown(label_text, option_text)
        logger.info("弹窗已选择 [%s] = %s", label_text, option_text)

    def click_dialog_save(self):
        """点击弹窗保存按钮，等待弹窗关闭"""
        super().click_dialog_save()
        self.wait_vue_stable()
        logger.info("已点击弹窗保存按钮")

    def click_dialog_cancel(self):
        """点击弹窗取消按钮"""
        super().click_dialog_cancel()
        logger.info("已点击弹窗取消按钮")

    def get_toast_text(self, timeout=10):
        """获取操作提示消息"""
        return self.wait_for_toast_text(timeout)

    def get_form_error_text(self, timeout=3):
        """获取表单校验错误提示"""
        return self.get_form_error(timeout)

    # ══════════════════════════════════════════════════════════════════
    #  行内操作
    # ══════════════════════════════════════════════════════════════════

    def click_edit_by_name(self, post_name):
        """点击指定岗位名称所在行的编辑按钮"""
        try:
            self.click_row_button(post_name, "编辑")
            self.wait_vue_stable()
            self.wait_dialog_open(timeout=10)
            logger.info("已点击岗位「%s」的编辑按钮", post_name)
        except Exception as e:
            raise Exception(f"未找到岗位「{post_name}」的编辑按钮: {e}")

    def click_toggle_status_by_name(self, post_name):
        """点击指定岗位名称所在行的启用/停用按钮"""
        btn_xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td[contains(normalize-space(.),"{post_name}")]]'
            f'//button[contains(.,"停用") or contains(.,"启用")]'
        )
        try:
            btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, btn_xpath))
            )
            btn_text = btn.text.strip()
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_vue_stable()
            logger.info("已点击岗位「%s」的状态切换按钮: %s", post_name, btn_text)
            return btn_text
        except Exception as e:
            raise Exception(f"未找到岗位「{post_name}」的状态切换按钮: {e}")

    def click_delete_by_name(self, post_name):
        """点击指定岗位名称所在行的删除按钮"""
        try:
            self.click_row_button(post_name, "删除")
            self.wait_vue_stable()
            logger.info("已点击岗位「%s」的删除按钮", post_name)
        except Exception as e:
            raise Exception(f"未找到岗位「{post_name}」的删除按钮: {e}")

    def confirm_message_box(self):
        """确认消息框（确定按钮）"""
        super().confirm_message_box()
        logger.info("已确认消息框")

    def get_message_box_text(self, timeout=5):
        """获取消息框提示文本"""
        return super().get_message_box_text(timeout)


if __name__ == "__main__":
    """测试岗位管理页面导航"""
    from base.browser_driver import BaseDriver
    from page.LoginPage import LoginPage

    base = BaseDriver()
    try:
        driver = base.open_browser()
        login_page = LoginPage(driver)
        login_page.login("admin", "admin123")

        post_page = PostManagePage(driver)
        post_page.navigate()
    finally:
        base.close_browser()
