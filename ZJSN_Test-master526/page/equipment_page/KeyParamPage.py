"""关键参数监控页面 Page Object — 基于实际页面 DOM 结构

==== 页面特征（已验证）====
  - 统计卡片：4张 .stat-card（BEM命名）
  - 搜索区：无 .search-wrapper，无 el-form，无下拉筛选
  - 搜索：裸 input（无placeholder）+ [重置]按钮(danger)
  - 数据表格：el-table，9列，无 fixed="right"，无 .table-wrapper
  - 运行状态：纯文本（非 el-tag）
  - 分页：el-pagination
  - 弹窗：详情弹窗 + 编辑弹窗（有CRUD操作）

==== 与推断的关键差异 ====
  1. 无 .search-wrapper / .table-wrapper → 定位器不加容器前缀
  2. 无[查询]按钮 → 只有关键词输入框 + [重置]
  3. 无下拉筛选框 → 无 select_device / select_param_status
  4. 按钮为"查看"/"编辑"/"删除" → 非"查看详情"/"历史趋势"
  5. 无趋势弹窗 → 无 trend dialog 相关方法
  6. 运行状态为纯文本 → 非 el-tag，验证方式不同
  7. 无固定列克隆 → 不需 TABLE_BODY 隔离
"""
import logging
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class KeyParamPage(BasePage):
    """关键参数监控页面 — Page Object (基于实际页面 DOM)"""

    # ==================================================================
    #  统计卡片 — BEM 命名，按 label 文字区分
    # ==================================================================
    STAT_CARD = (By.CSS_SELECTOR, '.stat-card')
    STAT_TOTAL = (
        By.XPATH,
        '//div[contains(@class,"stat-card")]'
        '[.//div[contains(@class,"stat-card__label") and normalize-space(.)="总监测参数"]]'
        '//div[contains(@class,"stat-card__value")]',
    )
    STAT_NORMAL = (
        By.XPATH,
        '//div[contains(@class,"stat-card")]'
        '[.//div[contains(@class,"stat-card__label") and normalize-space(.)="正常运行"]]'
        '//div[contains(@class,"stat-card__value")]',
    )
    STAT_WARNING = (
        By.XPATH,
        '//div[contains(@class,"stat-card")]'
        '[.//div[contains(@class,"stat-card__label") and normalize-space(.)="预警参数"]]'
        '//div[contains(@class,"stat-card__value")]',
    )
    STAT_ALARM = (
        By.XPATH,
        '//div[contains(@class,"stat-card")]'
        '[.//div[contains(@class,"stat-card__label") and normalize-space(.)="报警参数"]]'
        '//div[contains(@class,"stat-card__value")]',
    )
    STAT_LABELS = (By.CSS_SELECTOR, '.stat-card__label')

    # ==================================================================
    #  搜索区 — 裸 input + [重置]按钮
    #  无 .search-wrapper，无 el-form，无[查询]按钮，无下拉筛选
    # ==================================================================
    # 关键词输入框：使用 JS 定位（页面结构特殊，标准 CSS/XPath 不可靠）
    # 实际为页面上唯一一个接收文本输入但不属于分页/开关的 input
    INPUT_KEYWORD = (
        By.XPATH,
        '//input['
        'not(ancestor::div[contains(@class,"el-pagination")])'
        'and not(ancestor::div[contains(@class,"el-switch")])'
        'and not(ancestor::div[contains(@class,"el-select")])'
        'and not(@type="hidden")'
        'and not(@type="checkbox")'
        'and not(@type="radio")'
        '][1]'
    )
    # 重置按钮：仅用于 is_visible 检测，click 操作使用 JS 避免 Unicode 问题
    BTN_RESET = (
        By.XPATH,
        '//button[contains(.,"重")]',
    )

    # ==================================================================
    #  表格 — 无 .table-wrapper 包装
    # ==================================================================
    TABLE_ROWS = (
        By.CSS_SELECTOR,
        '.el-table__body-wrapper tbody tr.el-table__row',
    )
    TABLE_HEADER_CELLS = (
        By.CSS_SELECTOR,
        '.el-table__header-wrapper th .cell',
    )
    TABLE_EMPTY = (By.CSS_SELECTOR, '.el-table__empty-text')

    # ==================================================================
    #  分页 — Element Plus 标准 class
    # ==================================================================
    PAGE_JUMPER = (By.CSS_SELECTOR, '.el-pagination__jump .el-input__inner')

    # ==================================================================
    #  弹窗定位器
    # ==================================================================
    DIALOG_DETAIL = (
        By.CSS_SELECTOR,
        '.el-dialog[aria-label*="详情"]:not([style*="display: none"]), '
        '.el-dialog[aria-label*="参数"]:not([style*="display: none"])',
    )

    # ==================================================================
    #  行操作按钮文本
    # ==================================================================
    ROW_BUTTON_VIEW = "查看"
    ROW_BUTTON_EDIT = "编辑"
    ROW_BUTTON_DELETE = "删除"

    # ==================================================================
    #  构造 & 导航
    # ==================================================================
    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    def navigate_to_key_param(self):
        """通过 Vue Router hash 导航到关键参数监控页面"""
        logger.info("导航到 → 设备管理 → 关键参数监控 (hash切换)")
        self.driver.execute_script(
            'window.location.hash = "#/equipment/key-param";'
        )
        self._wait_page_ready()

    # ==================================================================
    #  页面就绪
    # ==================================================================
    def _wait_page_ready(self, timeout=25):
        self.wait_page_ready(timeout=30)
        self._wait_loading_gone(timeout)
        try:
            self.wait_stats_loaded(timeout=min(timeout, 12))
        except TimeoutException:
            logger.warning("统计卡片未在时间内加载，尝试等待表格")
        self._wait_table_ready(timeout=min(timeout, 15))

    def wait_stats_loaded(self, timeout=10):
        """等待统计卡片 label 和 value 均渲染完成"""
        WebDriverWait(self.driver, timeout).until(
            lambda d: (
                sum(1 for el in d.find_elements(By.CSS_SELECTOR, '.stat-card__label')
                    if (el.text or '').strip()) >= 2
                and sum(1 for el in d.find_elements(By.CSS_SELECTOR, '.stat-card__value')
                        if (el.text or '').strip()) >= 2
            )
        )

    # ==================================================================
    #  统计卡片
    # ==================================================================
    def get_stat_card_count(self):
        return len(self.find_all(self.STAT_CARD))

    def get_stat_labels(self):
        labels = self.find_all(self.STAT_LABELS)
        result = []
        for l in labels:
            text = (l.text or '').strip()
            if not text:
                text = (l.get_attribute("textContent") or '').strip()
            if text:
                result.append(text)
        return result

    def _get_stat_value(self, label_text):
        xpath = (
            f'//div[contains(@class,"stat-card")]'
            f'[.//div[contains(@class,"stat-card__label") and normalize-space(.)="{label_text}"]]'
            f'//div[contains(@class,"stat-card__value")]'
        )
        try:
            return self.get_text((By.XPATH, xpath), timeout=3)
        except TimeoutException:
            return ''

    def get_all_stats(self):
        stats = {}
        labels = self.get_stat_labels()
        for label in labels:
            stats[label] = self._get_stat_value(label)
        return stats

    # ==================================================================
    #  搜索区
    # ==================================================================
    def input_keyword(self, keyword):
        """输入关键词 — 通过 JS 设置 input 值+触发事件（确保 Vue 响应）"""
        self.driver.execute_script("""
            var inputs = document.querySelectorAll('input');
            var target = null;
            for (var i = 0; i < inputs.length; i++) {
                var el = inputs[i];
                if (el.offsetParent === null) continue;
                var type = (el.type || 'text').toLowerCase();
                if (type === 'hidden' || type === 'checkbox' || type === 'radio') continue;
                var p = el.parentElement;
                if (p && p.closest('.el-pagination')) continue;
                if (p && p.closest('.el-switch')) continue;
                if (p && p.closest('.el-select')) continue;
                target = el; break;
            }
            if (!target) return;
            target.value = arguments[1] || '';
            var evt = new Event('input', {bubbles: true, cancelable: true});
            target.dispatchEvent(evt);
            var evt2 = new Event('change', {bubbles: true, cancelable: true});
            target.dispatchEvent(evt2);
        """, keyword)
        self.wait_vue_stable()

    def click_reset(self):
        """点击重置按钮 — 通过 JS 遍历按钮文本匹配（避免 XPath Unicode 问题）"""
        self.driver.execute_script("""
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                var txt = (btns[i].textContent || '').trim();
                if (txt === '重置' || txt.indexOf('重置') >= 0) {
                    btns[i].click();
                    return;
                }
            }
            // 模糊匹配
            for (var i = 0; i < btns.length; i++) {
                var txt = (btns[i].textContent || '').trim();
                if (txt.indexOf('重') >= 0) {
                    btns[i].click();
                    return;
                }
            }
        """)
        self.wait_vue_stable()
        self._wait_table_ready()

    # ==================================================================
    #  表格
    # ==================================================================
    def _wait_table_ready(self, timeout=10):
        self._wait_loading_gone(timeout)
        self.wait_vue_stable()
        try:
            WebDriverWait(self.driver, 5).until(
                lambda d: d.execute_script(
                    "return document.querySelectorAll("
                    "'.el-table__body-wrapper tbody tr.el-table__row'"
                    ").length > 0;"
                )
            )
        except TimeoutException:
            logger.warning("表格行未在5s内渲染")

    def get_table_headers(self):
        """JS提取表格表头（含重试，应对Element Plus异步渲染）"""
        from selenium.webdriver.support.ui import WebDriverWait
        self._wait_table_ready()
        try:
            headers = WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script("""
                    return Array.from(
                        document.querySelectorAll('.el-table__header-wrapper th .cell')
                    ).map(function(el) { return el.textContent.trim(); }).filter(Boolean);
                """)
            )
            if headers and len(headers) >= 3:
                return headers
        except:
            pass
        return []
    def get_table_row_count(self):
        self._wait_table_ready()
        rows = self.find_all(self.TABLE_ROWS)
        return sum(1 for r in rows if r.is_displayed())

    def get_column_data(self, col_index):
        self._wait_table_ready()
        cells = self.find_all(
            (By.CSS_SELECTOR,
             f'.el-table__body-wrapper tbody td:nth-child({col_index}) .cell')
        )
        return [c.text.strip() for c in cells if c.text.strip()]

    def get_column_index_by_header(self, header_text):
        for idx, h in enumerate(self.get_table_headers(), start=1):
            if h == header_text:
                return idx
        return None

    def find_row_by_name(self, param_name):
        self._wait_table_ready()
        try:
            rows = self.find_all(self.TABLE_ROWS)
        except StaleElementReferenceException:
            self.wait_vue_stable()
            rows = self.find_all(self.TABLE_ROWS)

        for i in range(len(rows)):
            try:
                row = self.find_all(self.TABLE_ROWS)[i]
                first_cell = row.find_element(By.CSS_SELECTOR, 'td:first-child .cell')
                cell_text = (first_cell.text or '').strip()
                if not cell_text:
                    try:
                        btn = first_cell.find_element(By.TAG_NAME, 'button')
                        cell_text = (btn.text or '').strip()
                    except Exception:
                        pass
                if param_name in cell_text:
                    return row
            except (StaleElementReferenceException, Exception):
                continue
        return None

    def click_row_button(self, param_name, button_text):
        """点击指定行的操作按钮（查看/编辑/删除）"""
        logger.info("对监测参数「%s」点击操作: %s", param_name, button_text)
        self._wait_table_ready()

        row = self.find_row_by_name(param_name)
        if not row:
            raise TimeoutException(f"未找到监测参数行: {param_name}")

        try:
            action_cell = row.find_element(By.CSS_SELECTOR, 'td:last-child .cell')
        except Exception:
            raise TimeoutException(f"无法定位操作列: {param_name}")

        # 通过 class 特征匹配按钮
        btn_class_map = {
            "查看": "el-button--primary",
            "编辑": "el-button--small:not(.el-button--primary):not(.el-button--danger)",
            "删除": "el-button--danger",
        }

        for key, css_hint in btn_class_map.items():
            if button_text in key or key in button_text:
                try:
                    cls = css_hint.split(":")[0]
                    btn = action_cell.find_element(By.CSS_SELECTOR, f'button.{cls}')
                    if btn.is_displayed():
                        self._js_click_el(btn)
                        self.wait_vue_stable()
                        return
                except Exception:
                    pass

        # 保底
        all_btns = action_cell.find_elements(By.TAG_NAME, 'button')
        for btn in all_btns:
            txt = (btn.text or '').strip()
            if txt == button_text or button_text in txt:
                self._js_click_el(btn)
                self.wait_vue_stable()
                return

        raise TimeoutException(
            f"未找到监测参数「{param_name}」的操作按钮「{button_text}」"
        )

    def click_view_detail(self, param_name):
        """点击行操作[查看]按钮"""
        self.click_row_button(param_name, self.ROW_BUTTON_VIEW)
        self.wait_dialog_open()

    def is_row_present(self, param_name):
        return self.find_row_by_name(param_name) is not None

    # ==================================================================
    #  核心数据取值
    # ==================================================================

    def _get_row_cell_by_header(self, param_name, header_text):
        col_idx = self.get_column_index_by_header(header_text)
        if col_idx is None:
            logger.warning("未找到列: %s", header_text)
            return ''
        row = self.find_row_by_name(param_name)
        if not row:
            return ''
        try:
            cell = row.find_element(By.XPATH, f'td:nth-child({col_idx}) .cell')
            text = (cell.text or '').strip()
            if not text:
                try:
                    btn = cell.find_element(By.TAG_NAME, 'button')
                    text = (btn.text or '').strip()
                except Exception:
                    pass
            return text
        except Exception:
            return ''

    def get_current_value(self, param_name):
        return self._get_row_cell_by_header(param_name, "当前指标值")

    def get_param_status(self, param_name):
        return self._get_row_cell_by_header(param_name, "运行状态")

    def get_standard_value(self, param_name):
        return self._get_row_cell_by_header(param_name, "标准指标值")

    def get_device_name(self, param_name):
        return self._get_row_cell_by_header(param_name, "设备名称")

    def get_unit_name(self, param_name):
        return self._get_row_cell_by_header(param_name, "所属装置")

    # ==================================================================
    #  数据校验
    # ==================================================================

    def verify_status_vs_threshold(self, param_name):
        """验证运行状态与当前指标值vs标准指标值的逻辑一致性"""
        current_val_str = self.get_current_value(param_name)
        param_status = self.get_param_status(param_name)
        standard_str = self.get_standard_value(param_name)

        def _parse_num(s):
            if not s:
                return None
            try:
                match = re.match(r'[-]?\d+\.?\d*', s.replace(',', '').replace(' ', ''))
                if match:
                    return float(match.group())
            except (ValueError, TypeError):
                pass
            return None

        current_val = _parse_num(current_val_str)

        upper_val = None
        lower_val = None
        if standard_str:
            upper_match = re.search(r'上限\s*[:：]\s*([\d.]+)', standard_str)
            lower_match = re.search(r'下限\s*[:：]\s*([\d.]+)', standard_str)
            if upper_match:
                upper_val = float(upper_match.group(1))
            if lower_match:
                lower_val = float(lower_match.group(1))

        if current_val is None:
            return False, f"当前值无法解析: {current_val_str}"
        if lower_val is None or upper_val is None:
            return False, f"标准指标值无法解析: {standard_str}"

        if lower_val <= current_val <= upper_val:
            is_normal = (param_status == "正常")
        else:
            is_normal = (param_status != "正常")

        detail = (
            f"当前值={current_val}, 标准=[{lower_val}, {upper_val}], "
            f"状态={param_status}"
        )
        return is_normal, detail

    # ==================================================================
    #  分页
    # ==================================================================
    def jump_to_page(self, page_num):
        logger.info("跳转到第 %d 页", page_num)
        self.input_text(self.PAGE_JUMPER, str(page_num))
        jumper = self.find_visible(self.PAGE_JUMPER)
        jumper.send_keys('\n')
        self.wait_vue_stable()
        self._wait_table_ready()

    # ==================================================================
    #  详情弹窗
    # ==================================================================

    def get_detail_field(self, label_text):
        """从详情弹窗的 el-descriptions 中获取字段值"""
        xpath = (
            f'//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
            f'//td[contains(@class,"el-descriptions__label") and '
            f'contains(normalize-space(.),"{label_text}")]'
            f'/following-sibling::td[contains(@class,"el-descriptions__content")]'
        )
        try:
            return self.get_text((By.XPATH, xpath), timeout=5)
        except TimeoutException:
            xpath2 = (
                f'//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
                f'//div[contains(@class,"el-descriptions__label") and '
                f'contains(normalize-space(.),"{label_text}")]'
                f'/following-sibling::div[contains(@class,"el-descriptions__content")]'
            )
            return self.get_text((By.XPATH, xpath2), timeout=3)

    def click_detail_close(self):
        xpath = (
            '//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]'
            '//button[contains(.,"关闭") or contains(.,"取消")]'
        )
        try:
            self.click((By.XPATH, xpath))
            self.wait_dialog_close()
        except TimeoutException:
            logger.debug("未找到关闭按钮，尝试遮罩关闭")
            self.wait_dialog_close()

    # ==================================================================
    #  权限检查
    # ==================================================================

    def is_view_button_visible(self, param_name):
        try:
            row = self.find_row_by_name(param_name)
            if not row:
                return False
            action_cell = row.find_element(By.CSS_SELECTOR, 'td:last-child .cell')
            btn = action_cell.find_element(
                By.XPATH, f'.//button[contains(.,"{self.ROW_BUTTON_VIEW}")]'
            )
            return btn.is_displayed()
        except Exception:
            return False

    def is_edit_button_visible(self, param_name):
        try:
            row = self.find_row_by_name(param_name)
            if not row:
                return False
            action_cell = row.find_element(By.CSS_SELECTOR, 'td:last-child .cell')
            btn = action_cell.find_element(By.XPATH, './/button[not(contains(@class,"el-button--primary"))][not(contains(@class,"el-button--danger"))]')
            return btn.is_displayed()
        except Exception:
            return False
