"""生产月报表页面 Page Object

==== 页面概述 ====
  路径：生产管理 → 生产月报表
  路由：#/production/monthly-report
  功能：按月查看产品/原料/公辅工程/冷剂消耗四区数据，支持月份切换、趋势、导出

==== 定位策略 ====
  1. CSS: month-nav / current-month (自定义组件)
  2. XPath 文本：按钮 / 弹窗标题
  3. 禁止绝对 XPath
"""
import logging
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage
from config import TIMEOUT_CONFIG

logger = logging.getLogger(__name__)


class MonthlyReportPage(BasePage):
    """生产月报表页面"""

    # ══════════════════════════════════════════════════════════════════
    #  月份导航（自定义 month-nav 组件）
    # ══════════════════════════════════════════════════════════════════
    CURRENT_MONTH = (By.CSS_SELECTOR, ".current-month")
    BTN_PREV_MONTH = (By.CSS_SELECTOR, ".month-nav button.el-button.is-circle:first-child")
    BTN_NEXT_MONTH = (By.CSS_SELECTOR, ".month-nav button.el-button.is-circle:last-child")

    # ══════════════════════════════════════════════════════════════════
    #  操作按钮
    # ══════════════════════════════════════════════════════════════════
    BTN_GENERATE = (By.XPATH, '//button[contains(.,"生成报表")]')
    BTN_TREND = (By.XPATH, '//button[contains(.,"趋势")]')
    BTN_EXPORT = (By.XPATH, '//button[contains(.,"导出")]')
    BTN_PRINT = (By.XPATH, '//button[contains(.,"打印")]')

    # ══════════════════════════════════════════════════════════════════
    #  统计卡片
    # ══════════════════════════════════════════════════════════════════
    # 统计卡片：.summary-card 内 .label + .value 结构
    STAT_CARD_LNG_LABEL = (By.XPATH, '//div[contains(@class,"summary-card")]//div[contains(@class,"label") and contains(.,"LNG")]')
    STAT_CARD_LNG_VALUE = (By.XPATH, '//div[contains(@class,"summary-card")]//div[contains(@class,"label") and contains(.,"LNG")]/following-sibling::div[contains(@class,"value")]')
    STAT_CARDS = (By.CSS_SELECTOR, '.summary-card')

    # ══════════════════════════════════════════════════════════════════
    #  分区卡片（复用 daily-report 模式）
    # ══════════════════════════════════════════════════════════════════
    _SECTION_CARD_XPATH = (
        '//*[contains(@class,"section-title") and contains(.,"{section_name}")]'
        '/ancestor::div[contains(@class,"el-card")]'
    )
    _SECTION_TABLE_ROWS = (By.CSS_SELECTOR, '.el-table__body-wrapper tbody tr.el-table__row')
    _SECTION_TABLE_HEADERS = (By.CSS_SELECTOR, '.el-table__header-wrapper th .cell')

    # ══════════════════════════════════════════════════════════════════
    #  弹窗
    # ══════════════════════════════════════════════════════════════════
    _DIALOG_BY_TITLE_XPATH = (
        '//div[contains(@class,"el-dialog") and .//span[contains(@class,"el-dialog__title")'
        ' and contains(.,"{title}")]]'
    )

    # ══════════════════════════════════════════════════════════════════
    #  导航
    # ══════════════════════════════════════════════════════════════════
    # 页面身份标记（dashboard 没有这些元素，用于验证导航是否到达目标页面）
    _PAGE_IDENTITY_MARKERS = [
        ".current-month",      # 月份导航组件
        ".month-nav",          # 月份切换按钮组
        ".summary-card",       # 统计卡片
    ]

    def _is_on_monthly_report(self):
        """验证当前页面是否为月报表（而非 dashboard 或其他页面）"""
        return self.driver.execute_script("""
            var markers = arguments[0];
            for (var i = 0; i < markers.length; i++) {
                var el = document.querySelector(markers[i]);
                if (el && el.offsetParent !== null) return true;
            }
            return false;
        """, self._PAGE_IDENTITY_MARKERS)

    def navigate_to_monthly_report(self):
        """导航到生产月报表页面（SidebarNavigator + 页面身份验证 + 重试）

        策略：
          1. 优先使用 SidebarNavigator（内部 _ensure_on_welcome + 5阶段等待）
          2. 导航后验证页面身份标记（.current-month / .month-nav / .summary-card）
          3. 身份验证失败 → 整页刷新 + hash 直跳重试（最多2次）
        """
        max_retries = 2
        last_error = None

        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.warning("月报表身份验证失败（第%d次），重试导航…", attempt)
                # 重试策略：整页刷新 + hash 直跳（Vue Router 重新初始化）
                self.driver.refresh()
                self.wait_page_ready()
                self.wait_vue_stable()

            # 策略1：SidebarNavigator（侧边栏点击 + JS hash 双策略，含5阶段等待）
            try:
                self.navigate_to("生产管理", "生产月报表")
            except Exception as exc:
                logger.warning("SidebarNavigator 导航异常: %s，回退到 hash 直跳", exc)
                # 策略2：hash 直跳保底
                self.driver.execute_script(
                    "window.location.hash = '#/production/monthly-report';"
                )
                self.wait_page_ready()
                self.wait_vue_stable()

            # 验证页面身份（关键：确保不是 dashboard）
            if self._is_on_monthly_report():
                logger.info("月报表页面身份验证通过（第%d次尝试）", attempt + 1)
                # 再等核心元素稳定
                try:
                    self.wait_until_visible(self.CURRENT_MONTH, timeout=10)
                except TimeoutException:
                    pass
                self.wait_vue_stable()
                return self

            last_error = "页面身份标记未找到（可能渲染为dashboard）"

        raise TimeoutException(
            f"月报表导航失败（{max_retries + 1}次尝试后仍无法到达目标页面）: {last_error}"
        )

    # ══════════════════════════════════════════════════════════════════
    #  月份导航
    # ══════════════════════════════════════════════════════════════════
    def get_current_month(self):
        """获取当前月份文字（如'2026年5月'）"""
        el = self.find(self.CURRENT_MONTH)
        return el.text.strip()

    def click_prev_month(self):
        """点击上一月 ←"""
        logger.info("点击上一月")
        self.click(self.BTN_PREV_MONTH)
        self.wait_vue_stable()
        return self

    def click_next_month(self):
        """点击下一月 →"""
        logger.info("点击下一月")
        self.click(self.BTN_NEXT_MONTH)
        self.wait_vue_stable()
        return self

    # ══════════════════════════════════════════════════════════════════
    #  操作按钮
    # ══════════════════════════════════════════════════════════════════
    def click_generate_report(self):
        """点击生成报表按钮

        ⚠️ 月份切换后 Vue 可能未及时更新按钮 disabled 状态，
        使用 JS 强制清除 disabled 属性后再点击，确保请求发出。
        """
        logger.info("点击生成报表（force-enable + JS click）")
        self.driver.execute_script("""
            var btn = arguments[0];
            btn.classList.remove('is-disabled');
            btn.removeAttribute('disabled');
            btn.click();
        """, self.find(self.BTN_GENERATE))
        self.wait_vue_stable()
        self.wait_overlay_gone(timeout=15)
        return self

    def is_generate_disabled(self):
        """检查生成报表按钮是否 disabled"""
        el = self.find(self.BTN_GENERATE)
        return "is-disabled" in (el.get_attribute("class") or "")

    def click_trend(self):
        """点击趋势按钮"""
        logger.info("点击趋势按钮")
        self._js_click_by_text("趋势")
        self._wait_dialog_open("趋势分析")
        return self

    def click_export(self):
        """点击导出按钮"""
        logger.info("点击导出按钮")
        self._js_click_by_text("导出")
        self._wait_dialog_open("生产日报表")
        return self

    # ══════════════════════════════════════════════════════════════════
    #  统计卡片
    # ══════════════════════════════════════════════════════════════════
    def get_stat_card_count(self):
        """获取统计卡片数量"""
        cards = self.find_all(self.STAT_CARDS)
        return len(cards)

    def get_lng_monthly_output(self):
        """获取LNG月产量数值"""
        el = self.find(self.STAT_CARD_LNG_VALUE)
        return el.text.strip()

    # ══════════════════════════════════════════════════════════════════
    #  分区表格
    # ══════════════════════════════════════════════════════════════════
    def _get_section_locator(self, section_name):
        return (By.XPATH, self._SECTION_CARD_XPATH.format(section_name=section_name))

    def get_section_table_headers(self, section_name):
        card = self.find(self._get_section_locator(section_name))
        headers = card.find_elements(*self._SECTION_TABLE_HEADERS)
        return [h.text.strip() for h in headers if h.text.strip()]

    def get_section_row_count(self, section_name):
        card = self.find(self._get_section_locator(section_name))
        rows = card.find_elements(*self._SECTION_TABLE_ROWS)
        return len(rows)

    def is_section_visible(self, section_name):
        return self.is_visible(self._get_section_locator(section_name), timeout=5)

    # ══════════════════════════════════════════════════════════════════
    #  弹窗操作
    # ══════════════════════════════════════════════════════════════════
    def _get_dialog_locator(self, title):
        return (By.XPATH, self._DIALOG_BY_TITLE_XPATH.format(title=title))

    def _wait_dialog_open(self, title, timeout=None):
        if timeout is None:
            timeout = TIMEOUT_CONFIG.get('dialog_open', 10)
        self.wait_until_visible(self._get_dialog_locator(title), timeout=timeout)
        self.wait_vue_stable()
        return self

    def wait_dialog_close(self, title, timeout=None):
        if timeout is None:
            timeout = TIMEOUT_CONFIG.get('dialog_close', 10)
        self.wait_until_gone(self._get_dialog_locator(title), timeout=timeout)
        return self

    def is_dialog_open(self, title):
        return self.is_visible(self._get_dialog_locator(title), timeout=3)

    def get_dialog_title(self, title):
        dialog = self.find(self._get_dialog_locator(title))
        title_el = dialog.find_element(By.CSS_SELECTOR, ".el-dialog__title")
        return title_el.text.strip()

    def click_dialog_cancel(self, title):
        dialog = self.find(self._get_dialog_locator(title))
        try:
            cancel_btn = dialog.find_element(By.XPATH, './/button[contains(.,"取消")]')
            cancel_btn.click()
        except Exception:
            logger.info("弹窗'%s'无取消按钮，使用 × 关闭", title)
            close_btn = dialog.find_element(By.CSS_SELECTOR, ".el-dialog__headerbtn")
            close_btn.click()
        self.wait_dialog_close(title)
        return self

    # ══════════════════════════════════════════════════════════════════
    #  内部辅助
    # ══════════════════════════════════════════════════════════════════
    def _js_click_by_text(self, text):
        """用 JS 查找并点击匹配文本的按钮（绕过 Selenium 拦截问题）"""
        script = """
            var buttons = document.querySelectorAll('button, .el-button');
            for (var i = 0; i < buttons.length; i++) {
                var b = buttons[i];
                var btnText = (b.innerText || b.textContent || '').trim();
                if (btnText.indexOf(arguments[0]) >= 0) {
                    if (b.offsetParent !== null && !b.classList.contains('is-disabled')) {
                        b.click();
                        return {clicked: true, text: btnText, index: i};
                    }
                }
            }
            return {clicked: false};
        """
        result = self.driver.execute_script(script, text)
        if result and result.get('clicked'):
            logger.info("JS点击成功: '%s' (按钮[%d])", result['text'], result['index'])
        else:
            logger.warning("JS点击未找到匹配按钮: '%s'", text)
        self.wait_vue_stable()
        return self
