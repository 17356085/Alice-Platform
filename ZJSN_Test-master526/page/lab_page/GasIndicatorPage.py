"""
气体分析设计指标 Page Object

路由: #/lab/gas/indicator
类型: CRUD 表格 + 弹窗表单（无搜索、无分页）
对称页面: WaterIndicatorPage（水质版）

定位策略:
    - A级: 基于文本内容的 JS 定位（用于按钮、表单标签）
    - B级: 稳定的 CSS 类名（用于表格、弹窗等容器）
"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class GasIndicatorPage(BasePage):
    """气体分析设计指标 CRUD 页面"""

    PAGE_ROUTE = "#/lab/gas/indicator"

    # ══════════════════════════════════════════════════════════════════
    #  容器 & 状态定位器
    # ══════════════════════════════════════════════════════════════════
    LOADING_MASK = (By.CSS_SELECTOR, ".el-loading-mask")
    TABLE_HEADER = (By.CSS_SELECTOR, ".el-table__header-wrapper thead tr")
    TABLE_BODY = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody")
    TABLE_ROWS = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr")
    TABLE_COLUMN = (By.CSS_SELECTOR, "td")
    EMPTY_TEXT = (By.CSS_SELECTOR, ".el-table__empty-text")

    # ══════════════════════════════════════════════════════════════════
    #  弹窗定位器（优先级：Dialog > Drawer）
    # ══════════════════════════════════════════════════════════════════
    DIALOG = (By.CSS_SELECTOR, '.el-dialog:not([style*="display: none"])')
    DIALOG_FALLBACK = (By.CSS_SELECTOR, '.el-drawer:not([style*="display: none"])')

    def __init__(self, driver, timeout=10):
        super().__init__(driver, timeout)

    # ══════════════════════════════════════════════════════════════════
    #  导航
    # ══════════════════════════════════════════════════════════════════
    def navigate(self):
        """
        导航至：化验室取样 -> 气体分析设计指标。

        操作前确保页面DOM和Vue渲染完全稳定。
        """
        logger.info("导航到 → 化验室取样 → 气体分析设计指标")
        self.navigate_to("化验室取样", "气体分析设计指标")
        self.wait_page_ready(timeout=15)
        self._wait_for_page_loaded()
        self.wait_vue_stable()
        return self

    def _wait_for_page_loaded(self):
        """等待表格体出现，标志着页面基础DOM已就绪"""
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located(self.TABLE_BODY)
            )
            logger.info("页面表格体已存在")
        except TimeoutException:
            logger.warning("等待页面表格体超时，继续尝试后续操作")
        return self

    # ══════════════════════════════════════════════════════════════════
    #  表格 & 数据获取（依赖 BasePage 提供的能力）
    # ══════════════════════════════════════════════════════════════════
    def get_table_headers(self):
        """
        获取表格表头列表（通过 JS 采集文本）。

        Returns:
            list: 表头文本列表，例如 ['序号', '指标名称', '分类', ...]
        """
        logger.info("获取表格表头信息")
        script = """
            var headerContainer = document.querySelector('.el-table__header-wrapper');
            if (!headerContainer) return [];
            var headerCells = headerContainer.querySelectorAll('th .cell');
            return Array.from(headerCells).map(function(cell) { return (cell.textContent || '').trim(); });
        """
        headers = self.driver.execute_script(script)
        logger.debug("获取到表头: %s", headers)
        return headers

    def get_table_row_count(self):
        """
        获取表格数据行数（不含表头）。

        Returns:
            int: 表格行数
        """
        rows = self.find_elements(*self.TABLE_ROWS)
        count = len(rows)
        logger.info("表格数据行数: %s", count)
        return count

    def get_column_data(self, column_index):
        """
        获取指定列的所有行数据。

        Args:
            column_index (int): 列索引（从 1 开始）。

        Returns:
            list: 该列所有行单元格的文本列表。
        """
        logger.info("获取第 %d 列的数据", column_index)
        script = f"""
            var rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
            return Array.from(rows).map(function(row) {{
                var cell = row.querySelector('td:nth-child({column_index}) .cell');
                return cell ? (cell.textContent || '').trim() : '';
            }});
        """
        data = self.driver.execute_script(script)
        logger.debug("获取到第 %d 列数据: %s", column_index, data)
        return data

    def get_empty_text(self):
        """
        获取表格空数据提示文本。

        Returns:
            str: 空数据提示文本，若无则返回空字符串。
        """
        try:
            empty_el = self.find_element(*self.EMPTY_TEXT)
            text = empty_el.text
            logger.info("获取空数据提示文本: %s", text)
            return text
        except (NoSuchElementException, TimeoutException):
            logger.info("未找到空数据提示元素，表格可能有数据")
            return ""

    # ══════════════════════════════════════════════════════════════════
    #  私有辅助：基于文本的按钮点击
    # ══════════════════════════════════════════════════════════════════
    def _click_button_by_text(self, button_text):
        """
        通过 JS 根据文本内容点击按钮。

        Args:
            button_text (str): 要匹配的按钮文本（使用 indexOf 匹配）。

        Raises:
            TimeoutException: 未找到匹配的按钮。
        """
        logger.info("尝试点击文本为 '%s' 的按钮", button_text)
        self.wait_vue_stable()
        self.wait_element_gone(*self.LOADING_MASK, timeout=5)
        script = """
            var targetText = arguments[0];
            var buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                var txt = (buttons[i].textContent || '').trim();
                if (txt.indexOf(targetText) !== -1) {
                    buttons[i].click();
                    return true;
                }
            }
            return false;
        """
        clicked = self.driver.execute_script(script, button_text)
        if not clicked:
            raise TimeoutException(f"未能通过文本 '{button_text}' 找到并点击按钮")
        logger.info("成功点击文本为 '%s' 的按钮", button_text)
        return self

    def _wait_for_dialog(self):
        """等待弹窗（Dialog 或 Drawer）出现并返回元素。"""
        for locator in [self.DIALOG, self.DIALOG_FALLBACK]:
            try:
                dialog = WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located(locator)
                )
                logger.info("弹窗已可见: %s", locator)
                return dialog
            except TimeoutException:
                continue
        raise TimeoutException("点击按钮后未检测到任何弹窗出现")

    def _find_field_input_by_label(self, dialog_element, label_keyword):
        """
        在弹窗内根据表单标签文本查找输入框（input 或 textarea）。

        Args:
            dialog_element: 弹窗的 WebElement。
            label_keyword (str): 用于匹配标签文本的关键字。

        Returns:
            WebElement: 找到的输入框元素。

        Raises:
            TimeoutException: 未找到匹配的输入框。
        """
        logger.info("在弹窗内查找标签包含 '%s' 的输入框", label_keyword)
        script = """
            var dialog = arguments[0];
            var keyword = arguments[1];
            var labels = dialog.querySelectorAll('.el-form-item__label');
            for (var i = 0; i < labels.length; i++) {
                var text = (labels[i].textContent || '').trim();
                if (text.indexOf(keyword) !== -1) {
                    var formItem = labels[i].closest('.el-form-item');
                    if (!formItem) continue;
                    var input = formItem.querySelector('input.el-input__inner');
                    if (!input) input = formItem.querySelector('input:not([type="hidden"]):not([readonly])');
                    if (!input) input = formItem.querySelector('textarea');
                    if (input) return input;
                }
            }
            return null;
        """
        input_element = self.driver.execute_script(script, dialog_element, label_keyword)
        if input_element is None:
            raise TimeoutException(f"未能在弹窗中找到标签包含 '{label_keyword}' 的输入框")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_element)
        logger.info("成功找到标签 '%s' 对应的输入框", label_keyword)
        return input_element

    def _type_in_element(self, element, value):
        """
        清空输入框并输入新值。

        通过全选 + 删除来清空，兼容不同浏览器的行为。
        """
        from selenium.webdriver.common.keys import Keys
        element.send_keys(Keys.CONTROL + 'a')
        element.send_keys(Keys.DELETE)
        if value:
            element.send_keys(value)
        logger.debug("输入值: %s", value)

    def _fill_form_field(self, label_keyword, value):
        """封装：在弹窗的某个字段输入值。"""
        dialog = self._wait_for_dialog()
        input_el = self._find_field_input_by_label(dialog, label_keyword)
        self._type_in_element(input_el, value)
        return self

    # ══════════════════════════════════════════════════════════════════
    #  新增操作
    # ══════════════════════════════════════════════════════════════════
    def click_add(self):
        """点击【新增指标】按钮。"""
        self._click_button_by_text("新增指标")
        return self

    def dialog_input_name(self, value):
        """在新增/编辑弹窗中输入【指标名称】。"""
        self._fill_form_field("指标名称", value)
        return self

    def dialog_input_category(self, value):
        """在新增/编辑弹窗中输入【指标分类】。"""
        self._fill_form_field("指标分类", value)
        return self

    def dialog_input_unit(self, value):
        """在新增/编辑弹窗中输入【单位】。"""
        self._fill_form_field("单位", value)
        return self

    def dialog_input_rule(self, value):
        """在新增/编辑弹窗中输入【判断规则】。"""
        self._fill_form_field("判断规则", value)
        return self

    def dialog_input_threshold(self, value):
        """在新增/编辑弹窗中输入【阈值】。"""
        self._fill_form_field("阈值", value)
        return self

    def dialog_input_remark(self, value):
        """在新增/编辑弹窗中输入【备注】。"""
        self._fill_form_field("备注", value)
        return self

    def dialog_confirm(self):
        """
        点击弹窗中的【确认】按钮。

        操作后等待弹窗消失。
        """
        dialog = self._wait_for_dialog()
        logger.info("尝试点击弹窗中的确认按钮")
        script = """
            var dialog = arguments[0];
            var buttons = dialog.querySelectorAll('button.el-button--primary');
            for (var i = 0; i < buttons.length; i++) {
                var txt = (buttons[i].textContent || '').trim();
                if (txt.indexOf('确 定') !== -1 || txt.indexOf('确定') !== -1) {
                    buttons[i].click();
                    return true;
                }
            }
            // Fallback: 点击第一个 primary 按钮
            if (buttons.length > 0) {
                buttons[0].click();
                return true;
            }
            return false;
        """
        clicked = self.driver.execute_script(script, dialog)
        if not clicked:
            raise TimeoutException("未能在弹窗中找到并点击确认按钮")
        logger.info("已点击弹窗确认按钮")
        try:
            WebDriverWait(self.driver, 5).until(
                EC.invisibility_of_element_located(self.DIALOG)
            )
            logger.info("弹窗已关闭")
        except TimeoutException:
            logger.warning("等待弹窗关闭超时，尝试继续后续操作")
        self.wait_vue_stable()
        return self

    def dialog_cancel(self):
        """
        点击弹窗中的【取消】按钮。
        """
        dialog = self._wait_for_dialog()
        logger.info("尝试点击弹窗中的取消按钮")
        script = """
            var dialog = arguments[0];
            var buttons = dialog.querySelectorAll('button.el-button--default');
            for (var i = 0; i < buttons.length; i++) {
                var txt = (buttons[i].textContent || '').trim();
                if (txt.indexOf('取 消') !== -1 || txt.indexOf('取消') !== -1) {
                    buttons[i].click();
                    return true;
                }
            }
            return false;
        """
        clicked = self.driver.execute_script(script, dialog)
        if not clicked:
            # Fallback: 点击右上角关闭按钮
            close_btn = dialog.find_elements(By.CSS_SELECTOR, '.el-dialog__headerbtn, .el-drawer__close-btn')
            if close_btn:
                close_btn[0].click()
                clicked = True

        if not clicked:
            raise TimeoutException("未能在弹窗中找到并点击取消/关闭按钮")
        logger.info("已点击弹窗取消按钮")
        try:
            WebDriverWait(self.driver, 5).until(
                EC.invisibility_of_element_located(self.DIALOG)
            )
            logger.info("弹窗已关闭")
        except TimeoutException:
            logger.warning("等待弹窗关闭超时")
        self.wait_vue_stable()
        return self

    # ══════════════════════════════════════════════════════════════════
    #  编辑操作
    # ══════════════════════════════════════════════════════════════════
    def click_edit(self, row_index=0):
        """
        点击指定行的【编辑】按钮。

        Args:
            row_index (int): 行索引，从 0 开始。
        """
        row = self.find_elements(*self.TABLE_ROWS)
        if not row or row_index >= len(row):
            raise TimeoutException(f"未找到表格行或索引 {row_index} 无效")
        target_row = row[row_index]
        logger.info("点击第 %d 行的编辑按钮", row_index + 1)
        script = """
            var row = arguments[0];
            var buttons = row.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                var txt = (buttons[i].textContent || '').trim();
                if (txt.indexOf('编辑') !== -1) {
                    buttons[i].click();
                    return true;
                }
            }
            return false;
        """
        clicked = self.driver.execute_script(script, target_row)
        if not clicked:
            raise TimeoutException(f"在第 {row_index + 1} 行未找到'编辑'按钮")
        logger.info("成功点击编辑按钮")
        self._wait_for_dialog()
        return self

    # ══════════════════════════════════════════════════════════════════
    #  删除操作
    # ══════════════════════════════════════════════════════════════════
    def click_delete(self, row_index=0):
        """
        点击指定行的【删除】按钮。

        Args:
            row_index (int): 行索引，从 0 开始。
        """
        row = self.find_elements(*self.TABLE_ROWS)
        if not row or row_index >= len(row):
            raise TimeoutException(f"未找到表格行或索引 {row_index} 无效")
        target_row = row[row_index]
        logger.info("点击第 %d 行的删除按钮", row_index + 1)
        script = """
            var row = arguments[0];
            var buttons = row.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                var txt = (buttons[i].textContent || '').trim();
                if (txt.indexOf('删除') !== -1) {
                    buttons[i].click();
                    return true;
                }
            }
            return false;
        """
        clicked = self.driver.execute_script(script, target_row)
        if not clicked:
            raise TimeoutException(f"在第 {row_index + 1} 行未找到'删除'按钮")
        logger.info("成功点击删除按钮")
        return self

    def confirm_delete(self):
        """
        确认删除弹窗，点击【确认】。

        假设删除弹窗也是使用类似 Dialog 的方式。
        """
        dialog = self._wait_for_dialog()
        logger.info("确认删除弹窗")
        script = """
            var dialog = arguments[0];
            var buttons = dialog.querySelectorAll('button.el-button--primary');
            for (var i = 0; i < buttons.length; i++) {
                var txt = (buttons[i].textContent || '').trim();
                if (txt.indexOf('确 定') !== -1 || txt.indexOf('确定') !== -1) {
                    buttons[i].click();
                    return true;
                }
            }
            return false;
        """
        clicked = self.driver.execute_script(script, dialog)
        if not clicked:
            raise TimeoutException("未在删除确认弹窗中找到'确 定'按钮")
        logger.info("已确认删除")
        try:
            WebDriverWait(self.driver, 5).until(
                EC.invisibility_of_element_located(self.DIALOG)
            )
            logger.info("删除确认弹窗已关闭")
        except TimeoutException:
            logger.warning("等待删除确认弹窗关闭超时")
        return self