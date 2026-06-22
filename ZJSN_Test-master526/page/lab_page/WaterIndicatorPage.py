"""水质分析设计指标 Page Object

路由: #/lab/water/indicator
类型: 只读展示表格（无搜索、无分页、无CRUD）
对称页面: GasIndicatorPage（气体版）
"""
from base.base_page import BasePage
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


class WaterIndicatorPage(BasePage):
    """水质分析设计指标 — 只读展示页"""

    # 页面唯一入口路由
    PAGE_ROUTE = "#/lab/water/indicator"

    # ---------- Locator (基于 PAGE_CONTEXT.md PAGE_ELEMENT_POSITION) ----------
    # B级 - CSS Selector: 表格加载完成后变为可见
    TABLE_BODY = (By.CSS_SELECTOR, ".el-table__body-wrapper")
    # B级 - CSS Selector: 表格行
    TABLE_ROWS = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr")
    # B级 - CSS Selector: 无数据提示文字
    EMPTY_TEXT = (By.CSS_SELECTOR, ".el-table__empty-text")
    # B级 - CSS Selector: 展示中的弹窗（通用预留）
    DIALOG_VISIBLE = (By.CSS_SELECTOR, '.el-dialog:not([style*="display: none"])')
    # B级 - CSS Selector: 表头单元格文字
    HEADER_CELLS = (By.CSS_SELECTOR, ".el-table__header-wrapper th .cell")
    # C级 -> 优化为B级 - CSS Selector: 第n列数据单元格（备用方案）
    # 定位str: ".el-table__body-wrapper td:nth-child({col_index}) div.cell"

    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    # ==================== 页面入口 ====================
    def navigate(self):
        """导航到页面，并等待加载完成"""
        self.logger.info("导航到 → 化验室取样 → 水质分析设计指标")
        self.navigate_to("化验室取样", "水质分析设计指标")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        self.logger.info("页面加载完成")
        return self

    # ==================== 页面状态查询 ====================
    def get_table_row_count(self):
        """获取表格当前显示的行数（过滤后）"""
        self._wait_loading_gone(timeout=5)
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        count = sum(1 for r in rows if r.is_displayed())
        self.logger.info(f"表格当前显示行数: {count}")
        return count

    def get_empty_text(self):
        """获取表格无数据时的提示文本"""
        try:
            text = (self.driver.find_element(*self.EMPTY_TEXT).text or "").strip()
            self.logger.debug(f"空数据文本: '{text}'")
            return text
        except Exception:
            self.logger.debug("未找到空数据文本元素")
            return ""

    # ==================== 表格数据查询 ====================
    def get_table_headers(self):
        """获取表格所有列标题的文本列表"""
        self.wait_vue_stable()
        self._wait_loading_gone(timeout=5)
        # 使用 JavaScript 获取文本更稳定，避免元素不可见问题
        headers = self.driver.execute_script("""
            return Array.from(
                document.querySelectorAll('.el-table__header-wrapper th .cell')
            ).map(function(el) { return el.textContent.trim(); }).filter(Boolean);
        """)
        self.logger.info(f"获取到表头 ({len(headers)} 列): {headers}")
        return headers

    def get_column_data(self, col_index):
        """获取指定索引列的所有数据（从1开始）"""
        self._wait_loading_gone(timeout=5)
        # 改用更稳定的 CSS Selector 替代 XPath
        css_selector = f".el-table__body-wrapper td:nth-child({col_index}) div.cell"
        try:
            cells = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
            data = [cell.text.strip() for cell in cells if cell.text.strip()]
            self.logger.info(f"获取第 {col_index} 列数据 ({len(data)} 行)")
            return data
        except Exception as e:
            self.logger.error(f"获取第 {col_index} 列数据失败: {e}")
            return []

    def get_table_data(self):
        """获取整个二维数据表（列表套列表）"""
        self._wait_loading_gone(timeout=5)
        headers = self.get_table_headers()
        if not headers:
            self.logger.warning("表头为空，无法获取数据")
            return []

        col_count = len(headers)
        data = []
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        for row in rows:
            row_data = []
            cells = row.find_elements(By.TAG_NAME, "td")
            for i, cell in enumerate(cells[:col_count]):
                text = cell.text.strip()
                row_data.append(text)
            if row_data:
                data.append(row_data)
        self.logger.info(f"获取表格数据 ({len(data)} 行 x {col_count} 列)")
        return data

    # ==================== 等待辅助 ====================
    def _wait_loading_gone(self, timeout=10):
        """等待Element Plus的加载动画消失"""
        try:
            self.wait_element_invisible((By.CSS_SELECTOR, ".el-loading-mask"), timeout=timeout)
        except TimeoutException:
            self.logger.warning(f"等待加载动画消失超时 (timeout={timeout}s)")