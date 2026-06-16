"""储罐日报表页面 Page Object

注意：本页面使用自定义 UI 组件（非 Element Plus），
统计卡片和趋势图为只读展示。
"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class TankReportPage(BasePage):
    """储罐日报表页面"""

    # ══════════════════════════════════════════════════════════════════
    #  导航
    # ══════════════════════════════════════════════════════════════════

    def navigate(self):
        """导航到储罐日报表 — 唯一入口"""
        logger.info("导航到 → 储罐管理 → 储罐日报表")
        self.navigate_to("储罐管理", "储罐日报表")
        self.wait_page_ready(timeout=15)
        self.wait_vue_stable()
        return self

    # ══════════════════════════════════════════════════════════════════
    #  储罐选择
    # ══════════════════════════════════════════════════════════════════

    TANK_SELECT = (By.CSS_SELECTOR, ".el-select, [class*=tank-select]")
    TANK_OPTIONS = (By.CSS_SELECTOR, ".el-select-dropdown__item, [class*=option]")

    def select_tank(self, tank_text):
        """选择储罐"""
        try:
            self.click(self.TANK_SELECT)
            self.wait_vue_stable()
            options = self.find_all(self.TANK_OPTIONS)
            for opt in options:
                if tank_text in (opt.text or ""):
                    self._js_click_el(opt)
                    self.wait_vue_stable()
                    return self
        except Exception:
            logger.warning("下拉选择储罐失败，尝试文本匹配")
            # 兜底：直接点击含文本的元素
            try:
                el = self.driver.find_element(
                    By.XPATH, f'//*[contains(text(),"{tank_text}")]'
                )
                self._js_click_el(el)
            except Exception:
                raise
        return self

    # ══════════════════════════════════════════════════════════════════
    #  日期选择
    # ══════════════════════════════════════════════════════════════════

    DATE_PICKER = (By.CSS_SELECTOR, "input[type='text'][class*='date'], .el-date-editor")

    def select_date(self, date_str):
        """选择日期"""
        try:
            self.input_text(self.DATE_PICKER, date_str)
            self.wait_vue_stable()
        except Exception:
            logger.warning("日期输入失败: %s", date_str)
        return self

    # ══════════════════════════════════════════════════════════════════
    #  统计卡片（只读）
    # ══════════════════════════════════════════════════════════════════

    STAT_CARDS = (By.CSS_SELECTOR, ".stat-item, [class*=stat]")

    def get_stat_intake(self):
        """获取今日进气量"""
        return self._get_stat_by_label("进气量")

    def get_stat_outgas(self):
        """获取今日出气量"""
        return self._get_stat_by_label("出气量")

    def get_stat_inventory(self):
        """获取当前库存量"""
        return self._get_stat_by_label("库存")

    def _get_stat_by_label(self, label):
        """通过文本标签获取统计值（label 在前，value 在后）"""
        try:
            xpath = f'//*[contains(@class,"stat-label") and contains(text(),"{label}")]/following-sibling::*[contains(@class,"stat-value")]'
            return self.get_text((By.XPATH, xpath), timeout=3)
        except Exception:
            return ""

    # ══════════════════════════════════════════════════════════════════
    #  趋势图 Tab
    # ══════════════════════════════════════════════════════════════════

    TAB_7D = (By.XPATH, '//button[contains(.,"近7天")]')
    TAB_15D = (By.XPATH, '//button[contains(.,"近15天")]')
    TAB_30D = (By.XPATH, '//button[contains(.,"近30天")]')
    CHART_CONTAINER = (By.CSS_SELECTOR, "[class*=chart], [class*=trend], canvas, svg")

    def click_tab_7d(self):
        """切换近7天趋势图"""
        self.click(self.TAB_7D)
        self.wait_vue_stable()
        return self

    def click_tab_15d(self):
        """切换近15天趋势图"""
        self.click(self.TAB_15D)
        self.wait_vue_stable()
        return self

    def click_tab_30d(self):
        """切换近30天趋势图"""
        self.click(self.TAB_30D)
        self.wait_vue_stable()
        return self

    CHART_SECTION = (By.CSS_SELECTOR, ".chart-section")

    def is_chart_rendered(self):
        """判断趋势图区域是否渲染（含 canvas/svg 或至少图例可见）"""
        # Step 1: 确认 chart-section 存在
        if not self.is_visible(self.CHART_SECTION, timeout=5):
            return False
        # Step 2: 检查 canvas/svg 是否渲染
        try:
            container = self.find_visible(self.CHART_CONTAINER, timeout=3)
            canvases = container.find_elements(By.TAG_NAME, "canvas")
            svgs = container.find_elements(By.TAG_NAME, "svg")
            if canvases or svgs:
                return True
        except Exception:
            pass
        # Step 3: 兜底——检查图例区域（chart-legend）存在即可
        try:
            legend = self.driver.find_element(By.CSS_SELECTOR, ".chart-legend")
            return legend.is_displayed()
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════
    #  导出
    # ══════════════════════════════════════════════════════════════════

    EXPORT_BTN = (By.XPATH, '//button[contains(.,"导出")]')

    def click_export(self):
        """点击导出按钮"""
        self.click(self.EXPORT_BTN)
        return self
