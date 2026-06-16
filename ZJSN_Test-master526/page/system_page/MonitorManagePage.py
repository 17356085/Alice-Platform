"""系统监控页面 Page Object

变更记录:
  2026-06-12: 新建，继承 BasePage。系统监控页为Dashboard面板，
  不同于标准CRUD页面，以卡片/图表/指标为主要元素。
"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class MonitorManagePage(BasePage):
    """系统监控页面操作 — 继承 BasePage"""

    # ══════════════════════════════════════════════════════════════════
    #  页面框架定位器
    # ══════════════════════════════════════════════════════════════════
    PAGE_CONTAINER = (By.CSS_SELECTOR, ".app-container, .el-main, .dashboard-container")
    PAGE_TITLE = (By.XPATH, '//*[contains(normalize-space(.),"监控") or contains(normalize-space(.),"Monitor")]')

    # 卡片/指标区域
    METRIC_CARD = (By.CSS_SELECTOR, ".el-card, .metric-card, .stat-card, .dashboard-card")
    METRIC_VALUE = (By.CSS_SELECTOR, ".metric-value, .stat-value, .el-statistic__number")
    METRIC_LABEL = (By.CSS_SELECTOR, ".metric-label, .stat-label, .el-statistic__title")

    # 图表区域
    CHART_CONTAINER = (By.CSS_SELECTOR, ".chart-container, .echarts, [id*='chart']")

    # 服务器信息
    SERVER_INFO = (By.XPATH, '//*[contains(text(),"CPU") or contains(text(),"内存") or contains(text(),"磁盘")]')
    JVM_INFO = (By.XPATH, '//*[contains(text(),"JVM") or contains(text(),"堆内存") or contains(text(),"GC")]')

    # 刷新按钮
    REFRESH_BUTTON = (By.XPATH, '//button[.//span[contains(text(),"刷新")] or contains(text(),"刷新")]')

    # ══════════════════════════════════════════════════════════════════
    #  Toast
    # ══════════════════════════════════════════════════════════════════
    TOAST_TEXT = (By.CSS_SELECTOR, ".el-message__content")

    PAGE_ROUTE = "#/system/monitor"

    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    # ══════════════════════════════════════════════════════════════════════
    #  导航
    # ══════════════════════════════════════════════════════════════════════

    def navigate(self):
        """导航到系统监控页面"""
        logger.info("导航到 → 系统管理 → 系统监控")
        self.navigate_to("系统管理", "系统监控")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        return self

    def _wait_settled(self, timeout=10):
        self._wait_loading_gone(timeout=timeout)

    # ══════════════════════════════════════════════════════════════════════
    #  页面就绪检测
    # ══════════════════════════════════════════════════════════════════════

    def is_page_loaded(self):
        """检查监控页面是否渲染完成（至少有一个卡片或图表可见）"""
        try:
            cards = self.driver.find_elements(*self.METRIC_CARD)
            for card in cards:
                if card.is_displayed():
                    return True
        except Exception:
            pass
        try:
            charts = self.driver.find_elements(*self.CHART_CONTAINER)
            if charts:
                return True
        except Exception:
            pass
        try:
            server = self.driver.find_elements(*self.SERVER_INFO)
            if server:
                return True
        except Exception:
            pass
        return False

    # ══════════════════════════════════════════════════════════════════════
    #  指标读取
    # ══════════════════════════════════════════════════════════════════════

    def get_metric_card_count(self):
        """获取指标卡片数量"""
        try:
            cards = self.driver.find_elements(*self.METRIC_CARD)
            visible = [c for c in cards if c.is_displayed()]
            return len(visible)
        except Exception:
            return 0

    def get_metric_values(self):
        """获取所有可见的指标值"""
        try:
            els = self.driver.find_elements(*self.METRIC_VALUE)
            return [(e.text or "").strip() for e in els if e.is_displayed() and (e.text or "").strip()]
        except Exception:
            return []

    def get_metric_labels(self):
        """获取所有可见的指标标签"""
        try:
            els = self.driver.find_elements(*self.METRIC_LABEL)
            return [(e.text or "").strip() for e in els if e.is_displayed() and (e.text or "").strip()]
        except Exception:
            return []

    def get_server_info_text(self):
        """获取服务器信息区域的文本"""
        try:
            els = self.driver.find_elements(*self.SERVER_INFO)
            texts = [(e.text or "").strip() for e in els if e.is_displayed()]
            return " | ".join(texts) if texts else ""
        except Exception:
            return ""

    # ══════════════════════════════════════════════════════════════════════
    #  交互操作
    # ══════════════════════════════════════════════════════════════════════

    def click_refresh(self):
        """点击刷新按钮"""
        try:
            btn = self.driver.find_element(*self.REFRESH_BUTTON)
            if btn.is_displayed():
                self.driver.execute_script("arguments[0].click();", btn)
                self._wait_settled(timeout=10)
                logger.info("已点击刷新按钮")
                return True
        except Exception:
            pass
        try:
            # 备用：通过btn-refresh class定位
            btn = self.driver.find_element(By.CSS_SELECTOR, ".btn-refresh, [class*='refresh']")
            self.driver.execute_script("arguments[0].click();", btn)
            self._wait_settled(timeout=10)
            return True
        except Exception:
            logger.warning("未找到刷新按钮")
            return False
