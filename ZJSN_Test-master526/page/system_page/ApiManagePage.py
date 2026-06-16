"""接口管理页面 Page Object

变更记录:
  2026-06-12: 新建，继承 BasePage。接口管理页可能为Swagger/API文档查看器
  或自定义API管理界面，定位器覆盖两种场景。
"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class ApiManagePage(BasePage):
    """接口管理页面操作 — 继承 BasePage"""

    # 页面框架定位器（覆盖 Swagger + 自定义API管理两种场景）
    PAGE_CONTAINER = (By.CSS_SELECTOR, ".app-container, .el-main")
    PAGE_TITLE = (By.XPATH, '//*[contains(normalize-space(.),"接口") or contains(normalize-space(.),"API")]')
    # Swagger UI 元素
    API_GROUP = (By.CSS_SELECTOR, ".swagger-ui .opblock, .opblock-tag-section")
    API_ENDPOINT = (By.CSS_SELECTOR, ".opblock-summary, .opblock-summary-description")
    # 自定义API管理界面元素（Element Plus 表格风格）
    API_TABLE = (By.CSS_SELECTOR, ".el-table, .api-table, .interface-table")
    API_TABLE_ROWS = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr, .api-row")
    # 搜索
    SEARCH_INPUT = (By.XPATH, '//input[contains(@placeholder,"搜索") or contains(@placeholder,"filter") or contains(@placeholder,"接口") or contains(@placeholder,"API")]')
    TOAST_TEXT = (By.CSS_SELECTOR, ".el-message__content")

    PAGE_ROUTE = "#/system/api"

    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    def navigate(self):
        """导航到接口管理页面"""
        logger.info("导航到 → 系统管理 → 接口管理")
        self.navigate_to("系统管理", "接口管理")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        return self

    def _wait_settled(self, timeout=10):
        self._wait_loading_gone(timeout=timeout)

    def is_page_loaded(self):
        """检查页面是否加载 — 支持Swagger UI和自定义API管理两种模式"""
        self._wait_settled(timeout=10)
        try:
            if self.driver.find_elements(*self.API_GROUP):
                return True
        except Exception:
            pass
        try:
            table = self.driver.find_element(*self.API_TABLE)
            if table.is_displayed():
                return True
        except Exception:
            pass
        try:
            rows = self.driver.find_elements(*self.TABLE_ROWS)
            if rows:
                return True
        except Exception:
            pass
        try:
            container = self.driver.find_element(*self.PAGE_CONTAINER)
            if container.is_displayed():
                body_text = (container.text or "").strip()
                if len(body_text) > 20:
                    return True
        except Exception:
            pass
        return False

    def get_api_count(self):
        """获取API接口数量 — Swagger端点 或 自定义表格行数"""
        try:
            endpoints = self.driver.find_elements(*self.API_ENDPOINT)
            if endpoints:
                return len(endpoints)
        except Exception:
            pass
        try:
            return self.get_table_row_count()
        except Exception:
            pass
        try:
            rows = self.driver.find_elements(*self.API_TABLE_ROWS)
            return len(rows)
        except Exception:
            pass
        return 0

    def search_api(self, keyword):
        """在API搜索框中输入关键词"""
        from selenium.webdriver.common.keys import Keys
        try:
            el = self.driver.find_element(*self.SEARCH_INPUT)
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.send_keys(Keys.CONTROL + "a")
            el.send_keys(Keys.DELETE)
            el.send_keys(keyword)
            el.send_keys(Keys.ENTER)
            self.wait_vue_stable()
            logger.info("已搜索API: %s", keyword)
            return True
        except Exception:
            logger.warning("未找到API搜索框")
            return False

    def click_first_endpoint(self):
        """展开第一个API端点"""
        try:
            endpoints = self.driver.find_elements(*self.API_ENDPOINT)
            if endpoints:
                self.driver.execute_script("arguments[0].click();", endpoints[0])
                self.wait_vue_stable()
                return True
        except Exception:
            pass
        # 尝试点击表格第一行
        try:
            rows = self.driver.find_elements(*self.API_TABLE_ROWS)
            if rows:
                self.driver.execute_script("arguments[0].click();", rows[0])
                self.wait_vue_stable()
                return True
        except Exception:
            pass
        return False

    def switch_to_api_iframe(self):
        """尝试切换到API文档所在的iframe"""
        try:
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                src = iframe.get_attribute("src") or ""
                if any(k in src.lower() for k in ["swagger", "api", "doc"]):
                    self.driver.switch_to.frame(iframe)
                    logger.info("已切换到API文档iframe: %s", src)
                    return True
        except Exception:
            pass
        return False

    def switch_to_default_content(self):
        """切回主文档"""
        self.driver.switch_to.default_content()
