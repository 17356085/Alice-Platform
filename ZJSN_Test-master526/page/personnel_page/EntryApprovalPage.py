"""入场审批页面 Page Object

人员管理 > 承包商管理 > 入场审批
路由: #/personnel/contractor/approval

功能: 对承包商人员的入场申请进行审批（通过/驳回）
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


class EntryApprovalPage(BasePage):
    """入场审批页面操作 — 继承 BasePage"""

    # ══════════════════════════════════════════════════════════════════
    #  搜索区域
    # ══════════════════════════════════════════════════════════════════
    SEARCH_NAME_INPUT = (By.XPATH, '//input[contains(@placeholder,"姓名") or contains(@placeholder,"申请人") or contains(@placeholder,"人员") or contains(@placeholder,"搜索") or contains(@placeholder,"请输")]')
    SEARCH_UNIT_SELECT = (
        By.XPATH,
        '//div[contains(@class,"el-form") or contains(@class,"search-bar")]'
        '//div[contains(@class,"el-select")][.//span[contains(.,"承包商") or contains(.,"单位")]]',
    )
    SEARCH_STATUS_SELECT = (
        By.XPATH,
        '//div[contains(@class,"el-form") or contains(@class,"search-bar")]'
        '//div[contains(@class,"el-select")][.//span[contains(.,"审批状态") or contains(.,"状态")]]',
    )

    # ══════════════════════════════════════════════════════════════════
    #  表格
    # ══════════════════════════════════════════════════════════════════
    TABLE_COLUMN_HEADERS = (By.XPATH, '//div[contains(@class,"el-table__header-wrapper")]//th//div[contains(@class,"cell")]')

    # ══════════════════════════════════════════════════════════════════
    #  表格列索引（1-based）
    # ══════════════════════════════════════════════════════════════════
    COL_APPLICANT = 1
    COL_UNIT = 2
    COL_ID_CARD = 3
    COL_ENTRY_DATE = 4
    COL_REASON = 5
    COL_STATUS = 6
    COL_OPERATIONS = 7

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
    TABLE_APPROVE_BUTTON = (By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[contains(text(),"通过")]]')
    TABLE_REJECT_BUTTON = (By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[contains(text(),"驳回")]]')
    TABLE_DETAIL_BUTTON = (By.XPATH, '//tr[contains(@class,"el-table__row")]//button[.//span[contains(text(),"详情") or contains(text(),"查看")]]')

    # ══════════════════════════════════════════════════════════════════
    #  审批弹窗
    # ══════════════════════════════════════════════════════════════════
    APPROVAL_COMMENT_INPUT = (By.XPATH, '//textarea[contains(@placeholder,"审批意见") or contains(@placeholder,"备注")]')

    def __init__(self, driver, timeout=None):
        """初始化入场审批页面"""
        super().__init__(driver, timeout)

    # ══════════════════════════════════════════════════════════════════
    #  导航
    # ══════════════════════════════════════════════════════════════════

    def navigate(self):
        """导航到入场审批页面"""
        logger.info("导航到 → 人员管理 → 承包商管理 → 入场审批")
        self.navigate_to("人员管理", "承包商管理", "入场审批")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        if not self.is_page_loaded():
            raise Exception("入场审批页面加载失败")
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
        """输入搜索关键词（申请人姓名），XPATH + JS 双路定位"""
        try:
            el = self.wait.until(EC.visibility_of_element_located(self.SEARCH_NAME_INPUT))
        except Exception:
            # JS fallback: find first visible text input with matching placeholder
            el = self.driver.execute_script("""
                var inputs = document.querySelectorAll('input[placeholder]');
                for (var i = 0; i < inputs.length; i++) {
                    var ph = inputs[i].getAttribute('placeholder') || '';
                    if ((ph.indexOf('申请人') !== -1 || ph.indexOf('姓名') !== -1 || ph.indexOf('人员') !== -1)
                        && inputs[i].offsetParent !== null && inputs[i].type === 'text') {
                        return inputs[i];
                    }
                }
                return document.querySelector('input[placeholder]:not([placeholder=""])');
            """)
            if not el:
                raise Exception("未找到搜索输入框")
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        el.send_keys(value)
        logger.info("已输入搜索申请人: %s", value)

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

    def select_search_status(self, status_text):
        """选择搜索条件中的审批状态"""
        self.click(self.SEARCH_STATUS_SELECT)
        self._select_option(status_text)
        logger.info("已选择搜索审批状态: %s", status_text)

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
    #  审批操作
    # ══════════════════════════════════════════════════════════════════

    def click_approve_by_applicant(self, applicant_name):
        """点击指定申请人的通过按钮"""
        btn_xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td[contains(normalize-space(.),"{applicant_name}")]]'
            f'//button[contains(.,"通过")]'
        )
        try:
            btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, btn_xpath))
            )
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_vue_stable()
            logger.info("已点击申请人「%s」的通过按钮", applicant_name)
        except Exception as e:
            raise Exception(f"未找到申请人「{applicant_name}」的通过按钮: {e}")

    def click_reject_by_applicant(self, applicant_name):
        """点击指定申请人的驳回按钮"""
        btn_xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td[contains(normalize-space(.),"{applicant_name}")]]'
            f'//button[contains(.,"驳回")]'
        )
        try:
            btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, btn_xpath))
            )
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_vue_stable()
            logger.info("已点击申请人「%s」的驳回按钮", applicant_name)
        except Exception as e:
            raise Exception(f"未找到申请人「{applicant_name}」的驳回按钮: {e}")

    def click_detail_by_applicant(self, applicant_name):
        """点击指定申请人的详情按钮"""
        try:
            self.click_row_button(applicant_name, "详情")
            self.wait_vue_stable()
            self.wait_dialog_open(timeout=10)
            logger.info("已点击申请人「%s」的详情按钮", applicant_name)
        except Exception:
            # 尝试"查看"
            try:
                self.click_row_button(applicant_name, "查看")
                self.wait_vue_stable()
                self.wait_dialog_open(timeout=10)
                logger.info("已点击申请人「%s」的查看按钮", applicant_name)
            except Exception as e:
                raise Exception(f"未找到申请人「{applicant_name}」的详情按钮: {e}")

    # ══════════════════════════════════════════════════════════════════
    #  审批弹窗操作
    # ══════════════════════════════════════════════════════════════════

    def fill_approval_comment(self, comment):
        """填写审批意见"""
        try:
            el = self.wait.until(
                EC.visibility_of_element_located(self.APPROVAL_COMMENT_INPUT)
            )
            el.send_keys(Keys.CONTROL + "a")
            el.send_keys(Keys.DELETE)
            el.send_keys(comment)
            logger.info("已填写审批意见: %s", comment)
        except Exception:
            logger.debug("审批意见输入框未找到，跳过")

    def click_dialog_confirm(self):
        """点击弹窗确认按钮"""
        super().click_dialog_save()
        self.wait_vue_stable()
        logger.info("已点击审批确认按钮")

    def click_dialog_cancel(self):
        """点击弹窗取消按钮"""
        super().click_dialog_cancel()
        logger.info("已点击审批取消按钮")

    def get_dialog_title_text(self):
        """获取弹窗标题"""
        return self.get_dialog_title()

    def get_toast_text(self, timeout=10):
        """获取操作提示消息"""
        return self.wait_for_toast_text(timeout)

    def get_message_box_text(self, timeout=5):
        """获取消息框提示文本"""
        return super().get_message_box_text(timeout)

    def confirm_message_box(self):
        """确认消息框（确定按钮）"""
        super().confirm_message_box()
        logger.info("已确认消息框")


if __name__ == "__main__":
    """测试入场审批页面导航"""
    from base.browser_driver import BaseDriver
    from page.LoginPage import LoginPage

    base = BaseDriver()
    try:
        driver = base.open_browser()
        login_page = LoginPage(driver)
        login_page.login("admin", "admin123")

        approval_page = EntryApprovalPage(driver)
        approval_page.navigate()
    finally:
        base.close_browser()
