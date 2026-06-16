"""Element Plus 组件专用操作工具

处理 Vue3 + Element Plus 组件特有的异步渲染、动画延迟、Teleport 挂载等问题。

覆盖组件：
  - ElementSelect: 选项面板挂载在 body，需等待 Teleport 渲染
  - ElementDatePicker (Range): 范围选择器，面板挂载在 body
  - ElementProgress: 进度条有 3s CSS 动画，断言前需等待动画完成
  - ElementTable: 表格异步加载，需等待遮罩消失
  - ElementTag: 状态标签颜色/类型校验
  - ElementPagination: 分页器操作
"""
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

from config import TIMEOUT_CONFIG

logger = logging.getLogger(__name__)


class ElementPlusHelper:
    """Element Plus 组件操作助手

    可直接实例化使用，也可作为 mixin 混入 Page Object。
    """

    # ── 通用定位器 ──────────────────────────────────────────
    SELECT_DROPDOWN = (
        By.XPATH,
        '//div[contains(@class,"el-select-dropdown") '
        'and not(contains(@style,"display: none"))]',
    )
    SELECT_DROPDOWN_LIST = (
        By.CSS_SELECTOR,
        'body > .el-popper:not([style*="display: none"]) '
        'ul.el-select-dropdown__list',
    )
    SELECT_OPTION_TEMPLATE = (
        By.XPATH,
        '//div[contains(@class,"el-select-dropdown") '
        'and not(contains(@style,"display: none"))]'
        '//li[not(contains(@class,"is-disabled")) '
        'and contains(normalize-space(.),"{text}")]',
    )
    DATE_PANEL = (
        By.CSS_SELECTOR,
        '.el-picker-panel.el-date-range-picker:not([style*="display: none"])',
    )
    DATE_PANEL_XPATH = (
        By.XPATH,
        '//div[contains(@class,"el-picker-panel") '
        'and contains(@class,"el-date-range-picker") '
        'and not(contains(@style,"display: none"))]',
    )
    PROGRESS_BAR_INNER = (By.CSS_SELECTOR, '.el-progress-bar__inner')
    PROGRESS_TEXT = (By.CSS_SELECTOR, '.el-progress__text')
    TAG_DANGER = (By.CSS_SELECTOR, 'span.el-tag--danger')
    TAG_SUCCESS = (By.CSS_SELECTOR, 'span.el-tag--success')
    TAG_INFO = (By.CSS_SELECTOR, 'span.el-tag--info')
    TAG_WARNING = (By.CSS_SELECTOR, 'span.el-tag--warning')
    TABLE_LOADING_MASK = (
        By.CSS_SELECTOR,
        '.el-loading-mask, .el-table__body-wrapper .el-loading-mask',
    )
    PAGINATION_PAGE_SIZE_SELECT = (
        By.CSS_SELECTOR,
        '.el-pagination .el-select',
    )
    PAGINATION_NEXT = (By.CSS_SELECTOR, '.el-pagination button.btn-next:not([disabled])')
    PAGINATION_PREV = (By.CSS_SELECTOR, '.el-pagination button.btn-prev:not([disabled])')
    PAGINATION_TOTAL = (By.CSS_SELECTOR, '.el-pagination .el-pagination__total')

    def __init__(self, driver, timeout=None):
        self.driver = driver
        self.timeout = timeout or TIMEOUT_CONFIG.get('explicit_wait', 10)

    # ==================================================================
    #  ElementSelect — 下拉选择器
    # ==================================================================

    def select_option_by_placeholder(self, placeholder_text, option_text, timeout=None):
        """通过 placeholder 定位 Select 并选择选项

        处理 Element Plus Select 的 Teleport 机制：
        1. 通过 placeholder 文本找到 Select 根节点
        2. 点击触发下拉
        3. 等待下拉面板在 body 下渲染
        4. 等待动画完成
        5. 点击目标选项

        Args:
            placeholder_text: Select 的 placeholder 文本（如"产品类型"）
            option_text: 要选择的选项文本
            timeout: 超时时间
        """
        t = timeout or self.timeout
        logger.info("选择下拉选项: placeholder='%s' → '%s'", placeholder_text, option_text)

        # 步骤1: 通过 placeholder 定位 Select wrapper
        select_trigger_xpaths = [
            f'//span[contains(@class,"el-select__placeholder") '
            f'and contains(normalize-space(.),"{placeholder_text}")]'
            f'/ancestor::div[contains(@class,"el-select")]',
            f'//div[contains(@class,"el-select")]'
            f'[.//span[contains(@class,"el-select__placeholder") '
            f'and contains(normalize-space(.),"{placeholder_text}")]]',
        ]

        trigger = None
        for xp in select_trigger_xpaths:
            try:
                trigger = WebDriverWait(self.driver, t).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                break
            except TimeoutException:
                continue

        if not trigger:
            # 保底：直接用文本匹配任意 el-select
            try:
                trigger = WebDriverWait(self.driver, t).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        f'//div[contains(@class,"el-select")]'
                        f'[.//*[contains(normalize-space(.),"{placeholder_text}")]]',
                    ))
                )
            except TimeoutException:
                raise TimeoutException(
                    f"无法定位 placeholder='{placeholder_text}' 的 Select 组件"
                )

        # 步骤2: 滚动到可见区域并点击
        self._safe_click(trigger)
        time.sleep(0.4)  # 等待 Teleport 渲染 + 打开动画

        # 步骤3: 等待下拉面板可见
        self._wait_dropdown_visible(t)

        # 步骤4: 点击选项
        return self._click_dropdown_option(option_text, t)

    def select_option_by_index(self, select_root_locator, index, timeout=None):
        """通过 Select 根节点定位器，选择第 N 个选项（0-based）

        Args:
            select_root_locator: Select 根元素的定位器元组
            index: 选项索引
            timeout: 超时时间
        """
        t = timeout or self.timeout
        trigger = WebDriverWait(self.driver, t).until(
            EC.element_to_be_clickable(select_root_locator)
        )
        self._safe_click(trigger)
        time.sleep(0.4)
        self._wait_dropdown_visible(t)

        options = self.driver.find_elements(
            By.XPATH,
            '//div[contains(@class,"el-select-dropdown") '
            'and not(contains(@style,"display: none"))]'
            '//li[not(contains(@class,"is-disabled"))]',
        )
        if index < len(options):
            self._safe_click(options[index])
            time.sleep(0.3)
            logger.info("已选择第 %d 个选项", index)
        else:
            raise IndexError(f"选项索引 {index} 超出范围 (共 {len(options)} 个)")

    # ==================================================================
    #  ElementDatePicker (Range) — 日期范围选择器
    # ==================================================================

    def input_date_range(self, start_placeholder, end_placeholder,
                         start_date, end_date, timeout=None):
        """填写日期范围选择器

        Element Plus DatePicker Range 有两个输入框，分别通过 placeholder 定位。

        Args:
            start_placeholder: 开始日期输入框的 placeholder（如"有效期起"）
            end_placeholder: 结束日期输入框的 placeholder（如"有效期止"）
            start_date: 开始日期字符串（如 "2026-01-01"）
            end_date: 结束日期字符串（如 "2026-12-31"）
            timeout: 超时时间
        """
        t = timeout or self.timeout
        logger.info("输入日期范围: %s ~ %s", start_date, end_date)

        # 定位开始日期输入框
        start_input_xpaths = [
            f'//input[@placeholder="{start_placeholder}"]',
            f'//input[contains(@placeholder,"{start_placeholder}")]',
        ]
        start_input = None
        for xp in start_input_xpaths:
            try:
                start_input = WebDriverWait(self.driver, t).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                break
            except TimeoutException:
                continue
        if not start_input:
            raise TimeoutException(f"无法定位开始日期输入框: placeholder='{start_placeholder}'")

        self._safe_click(start_input)
        time.sleep(0.3)

        # 等待日期面板出现
        try:
            WebDriverWait(self.driver, t).until(
                EC.visibility_of_element_located(self.DATE_PANEL)
            )
        except TimeoutException:
            try:
                WebDriverWait(self.driver, t).until(
                    EC.visibility_of_element_located(self.DATE_PANEL_XPATH)
                )
            except TimeoutException:
                logger.warning("日期面板未在 %ds 内出现，尝试直接输入", t)

        # 清空并输入开始日期
        start_input.clear()
        start_input.send_keys(start_date)
        time.sleep(0.2)

        # 定位结束日期输入框
        end_input_xpaths = [
            f'//input[@placeholder="{end_placeholder}"]',
            f'//input[contains(@placeholder,"{end_placeholder}")]',
        ]
        end_input = None
        for xp in end_input_xpaths:
            try:
                end_input = self.driver.find_element(By.XPATH, xp)
                if end_input.is_displayed():
                    break
            except Exception:
                continue
        if not end_input:
            raise TimeoutException(f"无法定位结束日期输入框: placeholder='{end_placeholder}'")

        self._safe_click(end_input)
        end_input.clear()
        end_input.send_keys(end_date)
        time.sleep(0.3)

        # 按 ESC 关闭面板
        try:
            from selenium.webdriver.common.keys import Keys
            end_input.send_keys(Keys.ESCAPE)
        except Exception:
            pass

        logger.info("日期范围输入完成")

    def pick_date_from_panel(self, panel_locator, day_cell_text, timeout=None):
        """从日期面板中选择指定日期格子

        Args:
            panel_locator: 日期面板定位器
            day_cell_text: 日期数字文本（如 "15"）
            timeout: 超时时间
        """
        t = timeout or self.timeout
        panel = WebDriverWait(self.driver, t).until(
            EC.visibility_of_element_located(panel_locator)
        )
        # 找到可选的日期格子（排除 disabled 和上一月/下一月的）
        day_cell = panel.find_element(
            By.XPATH,
            f'.//td[not(contains(@class,"disabled")) '
            f'and not(contains(@class,"prev-month")) '
            f'and not(contains(@class,"next-month"))]'
            f'//div[normalize-space(.)="{day_cell_text}"]',
        )
        self._safe_click(day_cell)
        time.sleep(0.2)

    # ==================================================================
    #  ElementProgress — 进度条
    # ==================================================================

    def get_progress_percentage(self, progress_bar_element, timeout=None):
        """获取进度条百分比（等待 CSS 动画完成）

        Element Plus 进度条默认有 3s CSS transition 动画。
        此方法轮询等待 width 值稳定后再返回。

        Args:
            progress_bar_element: 进度条内层元素 (.el-progress-bar__inner) 的 WebElement
            timeout: 超时时间

        Returns:
            float: 进度百分比（0-100）
        """
        t = timeout or self.timeout
        deadline = time.time() + t
        last_width = None
        stable_count = 0

        while time.time() < deadline:
            try:
                style = progress_bar_element.get_attribute("style") or ""
                # 从 style="width: 50%;" 中提取数值
                import re
                match = re.search(r'width:\s*([\d.]+)%', style)
                if match:
                    current_width = float(match.group(1))
                    if last_width is not None and abs(current_width - last_width) < 0.1:
                        stable_count += 1
                        if stable_count >= 3:  # 连续3次稳定
                            return current_width
                    else:
                        stable_count = 0
                    last_width = current_width
            except StaleElementReferenceException:
                break
            time.sleep(0.3)

        # 超时或元素失效，返回最后读取的值
        if last_width is not None:
            logger.warning("进度条动画未完全稳定，返回最后值: %.1f%%", last_width)
            return last_width
        return 0.0

    def wait_progress_stable(self, progress_locator, timeout=None):
        """等待进度条动画完成（便捷方法）

        直接通过定位器等待进度条宽度稳定。

        Args:
            progress_locator: 进度条内层元素的定位器
            timeout: 超时时间
        """
        t = timeout or TIMEOUT_CONFIG.get('vue_stable', 5)
        el = WebDriverWait(self.driver, t).until(
            EC.presence_of_element_located(progress_locator)
        )
        return self.get_progress_percentage(el, timeout)

    # ==================================================================
    #  ElementTable — 表格
    # ==================================================================

    def wait_table_ready(self, timeout=None):
        """等待表格数据加载完成（遮罩消失 + 行渲染）"""
        t = timeout or TIMEOUT_CONFIG.get('table_render', 10)
        deadline = time.time() + t

        # 先等待 loading 遮罩消失
        while time.time() < deadline:
            try:
                masks = self.driver.find_elements(*self.TABLE_LOADING_MASK)
                visible_masks = [m for m in masks if m.is_displayed()]
                if not visible_masks:
                    break
            except Exception:
                pass
            time.sleep(0.3)

        # 再等待至少一行渲染（或空数据提示出现）
        while time.time() < deadline:
            try:
                rows = self.driver.find_elements(
                    By.CSS_SELECTOR, 'tr.el-table__row'
                )
                if rows:
                    return True
                # 也可能是空数据
                empty = self.driver.find_elements(
                    By.CSS_SELECTOR, '.el-table__empty-text'
                )
                if empty:
                    return True
            except Exception:
                pass
            time.sleep(0.3)

        logger.warning("表格未在 %ds 内完成渲染", t)
        return False

    def get_table_row_by_cell_text(self, cell_text, timeout=None):
        """根据单元格文本定位表格行

        Args:
            cell_text: 单元格包含的文本（如合同编号）
            timeout: 超时时间

        Returns:
            WebElement: 匹配的 tr 元素，未找到则 None
        """
        t = timeout or self.timeout
        try:
            return WebDriverWait(self.driver, t).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    f'//tr[contains(@class,"el-table__row")]'
                    f'[.//td[contains(normalize-space(.),"{cell_text}")]]',
                ))
            )
        except TimeoutException:
            return None

    def get_cell_value(self, row_element, col_index):
        """获取表格行中指定列的值

        Args:
            row_element: tr 元素
            col_index: 列索引（1-based）

        Returns:
            str: 单元格文本
        """
        try:
            cell = row_element.find_element(
                By.CSS_SELECTOR, f'td:nth-child({col_index}) .cell'
            )
            return (cell.text or '').strip()
        except Exception:
            try:
                cell = row_element.find_element(
                    By.CSS_SELECTOR, f'td:nth-child({col_index})'
                )
                return (cell.text or '').strip()
            except Exception:
                return ''

    def click_row_button(self, row_identifier, button_text, timeout=None):
        """在表格中定位包含指定文本的行，点击行内按钮

        对 Vue 场景做了优化：先确保行在视口内，等待 Vue 稳定后再点击。

        Args:
            row_identifier: 行标识文本（如合同编号）
            button_text: 按钮文本（如"详情"、"销售订单"）
            timeout: 超时时间
        """
        t = timeout or self.timeout
        xpath = (
            f'//tr[contains(@class,"el-table__row")]'
            f'[.//td[contains(normalize-space(.),"{row_identifier}")]]'
            f'//button[contains(.,"{button_text}")]'
        )
        btn = WebDriverWait(self.driver, t).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        self._safe_click(btn)
        time.sleep(0.3)
        logger.info("已点击行 [%s] 的 [%s] 按钮", row_identifier, button_text)

    # ==================================================================
    #  ElementTag — 状态标签
    # ==================================================================

    def get_tag_type(self, tag_element):
        """获取 ElementTag 的类型

        Args:
            tag_element: span.el-tag 元素

        Returns:
            str: 'danger', 'success', 'info', 'warning', 'primary' 或 'unknown'
        """
        classes = (tag_element.get_attribute("class") or "").split()
        type_map = {
            'el-tag--danger': 'danger',
            'el-tag--success': 'success',
            'el-tag--info': 'info',
            'el-tag--warning': 'warning',
            'el-tag--primary': 'primary',
        }
        for cls in classes:
            if cls in type_map:
                return type_map[cls]
        return 'unknown'

    def get_tag_text(self, tag_element):
        """获取 ElementTag 的文本内容"""
        return (tag_element.text or '').strip()

    # ==================================================================
    #  ElementPagination — 分页器
    # ==================================================================

    def get_pagination_total(self, timeout=5):
        """获取分页总条数文本

        Returns:
            str: 如 "共 4 条"
        """
        try:
            el = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.PAGINATION_TOTAL)
            )
            return (el.text or '').strip()
        except TimeoutException:
            return ''

    def get_pagination_total_number(self, timeout=5):
        """获取分页总条数（纯数字）

        Returns:
            int: 总条数，解析失败返回 0
        """
        import re
        text = self.get_pagination_total(timeout)
        nums = re.findall(r'\d+', text)
        return int(nums[-1]) if nums else 0

    def select_page_size(self, size_text, timeout=None):
        """切换每页条数

        Args:
            size_text: 每页条数文本（如 "10条/页"、"20条/页"）
            timeout: 超时时间
        """
        t = timeout or self.timeout
        logger.info("切换每页条数: %s", size_text)

        # 点击分页器中的 page-size select
        trigger = WebDriverWait(self.driver, t).until(
            EC.element_to_be_clickable(self.PAGINATION_PAGE_SIZE_SELECT)
        )
        self._safe_click(trigger)
        time.sleep(0.4)
        self._wait_dropdown_visible(t)
        self._click_dropdown_option(size_text, t)

    def click_next_page(self, timeout=None):
        """点击下一页"""
        t = timeout or self.timeout
        btn = WebDriverWait(self.driver, t).until(
            EC.element_to_be_clickable(self.PAGINATION_NEXT)
        )
        self._safe_click(btn)
        time.sleep(0.5)
        logger.info("已点击下一页")

    def click_prev_page(self, timeout=None):
        """点击上一页"""
        t = timeout or self.timeout
        btn = WebDriverWait(self.driver, t).until(
            EC.element_to_be_clickable(self.PAGINATION_PREV)
        )
        self._safe_click(btn)
        time.sleep(0.5)
        logger.info("已点击上一页")

    def is_next_page_enabled(self, timeout=3):
        """检查下一页按钮是否可用"""
        try:
            self.driver.find_element(*self.PAGINATION_NEXT)
            return True
        except Exception:
            return False

    def is_prev_page_enabled(self, timeout=3):
        """检查上一页按钮是否可用"""
        try:
            self.driver.find_element(*self.PAGINATION_PREV)
            return True
        except Exception:
            return False

    # ==================================================================
    #  ElementButton
    # ==================================================================

    def click_button_by_text(self, button_text, timeout=None):
        """通过按钮文本点击按钮

        优先 CSS_SELECTOR，XPath 保底。

        Args:
            button_text: 按钮文本（如"查询"、"重置"、"新增合同"）
            timeout: 超时时间
        """
        t = timeout or self.timeout
        logger.info("点击按钮: %s", button_text)

        # 策略1：CSS_SELECTOR + :has() / :contains()（如果浏览器支持）
        css_selectors = [
            f'button.el-button--primary span',
        ]
        for css in css_selectors:
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, css)
                for btn in buttons:
                    if button_text in (btn.text or ''):
                        self._safe_click(btn.find_element(By.XPATH, '..')
                                         if btn.tag_name == 'span' else btn)
                        return
            except Exception:
                continue

        # 策略2：XPath 文本匹配（最可靠）
        xpaths = [
            f'//button[contains(@class,"el-button")]'
            f'//span[contains(normalize-space(.),"{button_text}")]/parent::button',
            f'//button[contains(@class,"el-button") and contains(.,"{button_text}")]',
            f'//button[contains(.,"{button_text}")]',
        ]
        for xp in xpaths:
            try:
                btn = WebDriverWait(self.driver, t).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                self._safe_click(btn)
                time.sleep(0.3)
                return
            except TimeoutException:
                continue

        raise TimeoutException(f"无法定位包含文本 '{button_text}' 的按钮")

    # ==================================================================
    #  内部工具方法
    # ==================================================================

    def _safe_click(self, element):
        """安全点击：先滚动到视图，再点击（JS 保底）"""
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
                element,
            )
        except Exception:
            pass
        time.sleep(0.15)
        try:
            element.click()
        except Exception:
            try:
                self.driver.execute_script("arguments[0].click();", element)
            except Exception as e:
                logger.error("安全点击失败: %s", e)
                raise

    def _wait_dropdown_visible(self, timeout):
        """等待下拉面板在 body 下可见"""
        deadline = time.time() + timeout
        last_error = None
        while time.time() < deadline:
            try:
                dropdowns = self.driver.find_elements(
                    By.XPATH,
                    '//div[contains(@class,"el-select-dropdown") '
                    'and not(contains(@style,"display: none"))]',
                )
                if dropdowns:
                    for dd in dropdowns:
                        if dd.is_displayed():
                            return True
            except Exception as e:
                last_error = e
            time.sleep(0.2)
        if last_error:
            logger.warning("等待下拉面板超时: %s", last_error)
        return False

    def _click_dropdown_option(self, option_text, timeout):
        """点击下拉选项"""
        xpaths = [
            f'//div[contains(@class,"el-select-dropdown") '
            f'and not(contains(@style,"display: none"))]'
            f'//li[not(contains(@class,"is-disabled")) '
            f'and normalize-space(.)="{option_text}"]',
            f'(//div[contains(@class,"el-select-dropdown") '
            f'and not(contains(@style,"display: none"))])[last()]'
            f'//li[not(contains(@class,"is-disabled")) '
            f'and contains(normalize-space(.),"{option_text}")]',
            f'//body//li[@role="option" '
            f'and contains(normalize-space(.),"{option_text}")]',
        ]

        last_error = None
        for xp in xpaths:
            try:
                opt = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                self._safe_click(opt)
                time.sleep(0.4)
                logger.info("已选择下拉选项: %s", option_text)
                return
            except TimeoutException as e:
                last_error = e
                continue

        if last_error:
            raise last_error
        raise TimeoutException(f"无法选择下拉选项: {option_text}")
