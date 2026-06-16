"""审批链配置页面 Page Object

变更记录:
  2026-06-12: 新建，继承 BasePage，遵循代码红线规范
"""
import logging
import time as _time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class ApprovalChainPage(BasePage):
    """审批链配置页面操作 — 继承 BasePage"""

    # ══════════════════════════════════════════════════════════════════
    #  搜索区域定位器
    # ══════════════════════════════════════════════════════════════════
    NAME_INPUT = (By.XPATH, '//div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"名称")]]//input[contains(@class,"el-input")] | //input[contains(@placeholder,"审批链名称")]')
    SEARCH_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="搜索"] or normalize-space(.)="搜索"]')
    RESET_BUTTON = (By.XPATH, '//button[.//span[normalize-space(.)="重置"] or normalize-space(.)="重置"]')

    # ══════════════════════════════════════════════════════════════════
    #  工具栏
    # ══════════════════════════════════════════════════════════════════
    TOOLBAR_ADD_TEXT = ["新增", "添加", "新建"]

    # ══════════════════════════════════════════════════════════════════
    #  弹窗定位器（CSS Selector，比 XPath [last()] 更可靠）
    # ══════════════════════════════════════════════════════════════════
    DIALOG = (By.CSS_SELECTOR, '.el-dialog:not([style*="display: none"])')
    DIALOG_FALLBACK = (By.CSS_SELECTOR, '.el-drawer:not([style*="display: none"])')
    DIALOG_CONFIRM = (
        By.XPATH,
        '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]'
        '//div[contains(@class,"el-dialog")])[last()]'
        '//footer//button[contains(@class,"el-button--primary")]',
    )
    DIALOG_CANCEL = (
        By.XPATH,
        '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]'
        '//div[contains(@class,"el-dialog")])[last()]'
        '//footer//button[not(contains(@class,"el-button--primary"))]',
    )

    # 删除确认
    DELETE_CONFIRM = (
        By.XPATH,
        '(//div[contains(@class,"el-overlay") and not(contains(@style,"display: none"))]'
        '//div[contains(@class,"el-message-box")])[last()]'
        '//button[contains(@class,"el-button--primary")]',
    )

    # ══════════════════════════════════════════════════════════════════
    #  表格定位器
    # ══════════════════════════════════════════════════════════════════
    EMPTY_TEXT = (By.CSS_SELECTOR, ".el-table__empty-text")
    TABLE_HEADERS = (By.XPATH, '//div[contains(@class,"el-table__header-wrapper")]//th//div')
    CURRENT_PAGE = (By.CSS_SELECTOR, ".el-pagination .el-pager li.active, .el-pagination .el-pager li.is-active")

    # ══════════════════════════════════════════════════════════════════
    #  Toast
    # ══════════════════════════════════════════════════════════════════
    TOAST_TEXT = (By.CSS_SELECTOR, ".el-message__content")
    TOAST_FALLBACK = (By.CSS_SELECTOR, 'div[id^="message_"] p, div[id^="message_"] .el-message__content')
    TOAST_ENHANCED = (By.XPATH, '(//*[contains(@class,"el-message__content") and normalize-space(.)!=""])[last()]')

    PAGE_ROUTE = "#/system/workflow/approval-chain"

    def __init__(self, driver, timeout=None):
        super().__init__(driver, timeout)

    # ══════════════════════════════════════════════════════════════════════
    #  导航
    # ══════════════════════════════════════════════════════════════════════

    def navigate(self):
        """导航到审批链配置页面"""
        logger.info("导航到 → 系统管理 → 工作流管理 → 审批链配置")
        self.navigate_to("系统管理", "工作流管理", "审批链配置")
        self.wait_page_ready(timeout=15)
        self._wait_loading_gone(timeout=10)
        self.wait_vue_stable()
        return self

    def _wait_settled(self, timeout=10):
        self._wait_loading_gone(timeout=timeout)

    # ══════════════════════════════════════════════════════════════════════
    #  搜索操作
    # ══════════════════════════════════════════════════════════════════════

    def input_name(self, value):
        """输入审批链名称 — JS 遍历标签定位 el-input → XPath 降级"""
        el = self.driver.execute_script("""
            var labels = document.querySelectorAll('.el-form-item__label');
            for (var i = 0; i < labels.length; i++) {
                var text = (labels[i].textContent || '').trim();
                if (text.indexOf('名称') !== -1) {
                    var formItem = labels[i].closest('.el-form-item');
                    if (!formItem) continue;
                    var input = formItem.querySelector('input.el-input__inner');
                    if (!input) input = formItem.querySelector('input:not([type=\"hidden\"]):not([readonly])');
                    if (input) return input;
                }
            }
            return null;
        """)
        if el:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.send_keys(Keys.CONTROL + "a")
            el.send_keys(Keys.DELETE)
            if value:
                el.send_keys(value)
            logger.info("已输入名称: %s", value)
            return
        # XPath 降级
        try:
            el = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(self.NAME_INPUT))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.send_keys(Keys.CONTROL + "a")
            el.send_keys(Keys.DELETE)
            if value:
                el.send_keys(value)
            logger.info("已输入名称(XPath): %s", value)
        except Exception:
            raise TimeoutException(f"未找到名称输入框: {value}")

    def input_code(self, value):
        """输入审批链编码 — 搜索区"审批链编码"字段"""
        el = self.driver.execute_script("""
            var labels = document.querySelectorAll('.el-form-item__label');
            for (var i = 0; i < labels.length; i++) {
                var text = (labels[i].textContent || '').trim();
                if (text.indexOf('编码') !== -1 && text.indexOf('审批链') !== -1) {
                    var formItem = labels[i].closest('.el-form-item');
                    if (!formItem) continue;
                    var input = formItem.querySelector('input.el-input__inner');
                    if (!input) input = formItem.querySelector('input:not([type="hidden"]):not([readonly])');
                    if (input) return input;
                }
            }
            return null;
        """)
        if el:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.send_keys(Keys.CONTROL + "a")
            el.send_keys(Keys.DELETE)
            if value:
                el.send_keys(value)
            logger.info("已输入编码: %s", value)
        else:
            logger.warning("未找到编码输入框")

    def click_search(self):
        self._wait_settled(timeout=6)
        self._js_click_search_or_reset("搜索")
        self._wait_settled(timeout=10)
        logger.info("已点击搜索按钮")

    def click_reset(self):
        self._wait_settled(timeout=6)
        self._js_click_search_or_reset("重置")
        self._wait_settled(timeout=10)
        logger.info("已点击重置按钮")

    def _js_click_search_or_reset(self, text):
        """JS 点击搜索/重置按钮（绕过 element click intercepted）"""
        self.driver.execute_script(f"""
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {{
                if ((btns[i].textContent || '').trim().indexOf('{text}') !== -1) {{
                    btns[i].scrollIntoView({{block:'center'}});
                    btns[i].click();
                    return;
                }}
            }}
            // Fallback: click primary button for search
            if ('{text}' === '搜索') {{
                var primary = document.querySelector('.search-form button.el-button--primary, .search-row button.el-button--primary');
                if (primary) {{ primary.scrollIntoView({{block:'center'}}); primary.click(); }}
            }}
        """)

    # ══════════════════════════════════════════════════════════════════════
    #  新增操作
    # ══════════════════════════════════════════════════════════════════════

    def click_add(self):
        """点击新增按钮 — JS 文本匹配优先（XPath span 嵌套不可靠）"""
        self._wait_settled(timeout=6)
        # JS 文本搜索 — 遍历所有 button，匹配"新增"/"添加"/"新建"
        clicked = self.driver.execute_script("""
            var texts = ['新增', '添加', '新建'];
            var btns = document.querySelectorAll('button');
            for (var t = 0; t < texts.length; t++) {
                for (var i = 0; i < btns.length; i++) {
                    var txt = (btns[i].textContent || '').trim();
                    if (txt.indexOf(texts[t]) !== -1) {
                        btns[i].scrollIntoView({block:'center'});
                        btns[i].click();
                        return txt;
                    }
                }
            }
            return null;
        """)
        if not clicked:
            # XPath 降级：按钮内可能含 span
            for loc in [
                (By.XPATH, '//button[.//span[contains(text(),"新增")] or contains(text(),"新增")]'),
                (By.XPATH, '//button[contains(@class,"el-button--primary")][1]'),
            ]:
                try:
                    btn = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(loc))
                    if btn and btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        clicked = "fallback"
                        break
                except Exception:
                    continue
        logger.info("已点击新增按钮 (方式=%s)", clicked or "unknown")
        self.wait_vue_stable()
        # 等待弹窗/抽屉出现
        for loc in [self.DIALOG, self.DIALOG_FALLBACK]:
            try:
                WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(loc))
                logger.info("弹窗已打开")
                return
            except TimeoutException:
                continue
        raise TimeoutException("点击新增按钮后未检测到弹窗/抽屉，请检查页面行为")

    def _get_dialog(self):
        """获取当前可见的弹窗/抽屉容器（CSS 优先）"""
        for loc in [self.DIALOG, self.DIALOG_FALLBACK]:
            try:
                return WebDriverWait(self.driver, 4).until(EC.presence_of_element_located(loc))
            except TimeoutException:
                continue
        raise TimeoutException("未找到弹窗/抽屉")

    def is_dialog_open(self):
        try:
            el = self.driver.find_element(*self.DIALOG)
            return el.is_displayed()
        except Exception:
            return False

    def _find_field_in_dialog(self, label_keyword):
        """在弹窗内通过标签文本查找表单元素（JS label遍历，不受placeholder/type影响）"""
        dlg = self._get_dialog()
        el = self.driver.execute_script("""
            var dlg = arguments[0];
            var keyword = arguments[1];
            var labels = dlg.querySelectorAll('.el-form-item__label');
            for (var i = 0; i < labels.length; i++) {
                var text = (labels[i].textContent || '').trim();
                if (text.indexOf(keyword) !== -1) {
                    var formItem = labels[i].closest('.el-form-item');
                    if (!formItem) continue;
                    var input = formItem.querySelector('input.el-input__inner');
                    if (!input) input = formItem.querySelector('input:not([type="hidden"]):not([readonly])');
                    if (!input) input = formItem.querySelector('textarea');
                    if (!input) input = formItem.querySelector('.el-select input');
                    if (input) return input;
                }
            }
            // Fallback: placeholder 模糊匹配
            var inputs = dlg.querySelectorAll('input:not([type="hidden"]), textarea');
            for (var j = 0; j < inputs.length; j++) {
                var ph = (inputs[j].placeholder || '').trim();
                if (ph.indexOf(keyword) !== -1) return inputs[j];
            }
            return null;
        """, dlg, label_keyword)
        if el is None:
            raise TimeoutException(f"未在弹窗内找到标签含'{label_keyword}'的表单字段")
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        return el

    def _clear_and_type(self, element, value):
        """清空输入框并输入新值"""
        element.send_keys(Keys.CONTROL + "a")
        element.send_keys(Keys.DELETE)
        if value:
            element.send_keys(value)

    def dialog_input_name(self, value):
        """弹窗 — 输入审批链名称 (label='审批链名称')"""
        el = self._find_field_in_dialog("审批链名称")
        self._clear_and_type(el, value)
        logger.info("弹窗输入名称: %s", value)

    def dialog_input_code(self, value):
        """弹窗 — 输入审批链编码 (label='审批链编码')"""
        el = self._find_field_in_dialog("审批链编码")
        self._clear_and_type(el, value)
        logger.info("弹窗输入编码: %s", value)

    def dialog_input_desc(self, value):
        """弹窗 — 输入备注 (label='备注')"""
        el = self._find_field_in_dialog("备注")
        self._clear_and_type(el, value)
        logger.info("弹窗输入备注: %s", value)

    def dialog_confirm(self):
        """点击弹窗确认按钮 — 先在 dialog 内找，再全局降级"""
        dlg = self._get_dialog()
        btn = self.driver.execute_script("""
            var dlg = arguments[0];
            var btns = dlg.querySelectorAll('button.el-button--primary');
            for (var i = 0; i < btns.length; i++) {
                var txt = (btns[i].textContent || '').trim();
                if (txt && txt.indexOf('取消') === -1) return btns[i];
            }
            if (btns.length > 0) return btns[0];
            var footer = dlg.querySelector('.el-dialog__footer');
            if (footer) {
                var fb = footer.querySelector('button.el-button--primary');
                if (fb) return fb;
            }
            return null;
        """, dlg)
        if btn:
            self.driver.execute_script("arguments[0].click();", btn)
        else:
            btn = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(self.DIALOG_CONFIRM))
            self.driver.execute_script("arguments[0].click();", btn)
        self._wait_settled(timeout=3)
        self.wait_vue_stable()
        logger.info("已点击弹窗确认按钮")

    def dialog_cancel(self):
        """点击弹窗取消按钮"""
        dlg = self._get_dialog()
        btn = self.driver.execute_script("""
            var dlg = arguments[0];
            var btns = dlg.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                var txt = (btns[i].textContent || '').trim();
                if (txt.indexOf('取消') !== -1) return btns[i];
            }
            return null;
        """, dlg)
        if btn:
            self.driver.execute_script("arguments[0].click();", btn)
        else:
            btn = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(self.DIALOG_CANCEL))
            self.driver.execute_script("arguments[0].click();", btn)
        self.wait_vue_stable()
        logger.info("已点击弹窗取消按钮")

    def delete_confirm(self):
        btn = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(self.DELETE_CONFIRM))
        self.driver.execute_script("arguments[0].click();", btn)
        self._wait_settled(timeout=3)
        self.wait_vue_stable()
        logger.info("已点击删除确认按钮")

    # ══════════════════════════════════════════════════════════════════════
    #  表格操作
    # ══════════════════════════════════════════════════════════════════════

    def get_table_headers(self):
        for _ in range(6):
            try:
                self._wait_settled(timeout=5)
            except Exception:
                pass
            self.wait_vue_stable()
            headers = self.driver.execute_script("""
                return Array.from(
                    document.querySelectorAll('.el-table__header-wrapper th .cell')
                ).map(function(el) { return el.textContent.trim(); }).filter(Boolean);
            """)
            if headers and len(headers) >= 2:
                return headers
            self._wait_loading_gone(timeout=2)
        return []

    def get_table_row_count(self):
        self._wait_settled(timeout=10)
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        count = 0
        for r in rows:
            try:
                if r.is_displayed():
                    count += 1
            except Exception:
                continue
        return count

    def get_column_index_by_header(self, header_text):
        self._wait_settled(timeout=10)
        ths = self.driver.find_elements(By.XPATH, '//div[contains(@class,"el-table__header-wrapper")]//table//th')
        for idx, th in enumerate(ths, start=1):
            try:
                if (th.text or "").strip() == header_text:
                    return idx
            except Exception:
                continue
        return None

    def get_column_data(self, col_index):
        self._wait_settled(timeout=10)
        xpath = f'//div[contains(@class,"el-table__body-wrapper")]//tbody/tr/td[{col_index}]//div[contains(@class,"cell")]'
        cells = self.driver.find_elements(By.XPATH, xpath)
        return [(c.text or "").strip().replace("\n", " ").strip() for c in cells if (c.text or "").strip()]

    def get_column_data_by_header(self, header_text):
        idx = self.get_column_index_by_header(header_text)
        return self.get_column_data(idx) if idx else []

    def get_empty_text(self):
        try:
            self._wait_settled(timeout=10)
        except Exception:
            pass
        try:
            return (self.driver.find_element(*self.EMPTY_TEXT).text or "").strip()
        except Exception:
            return ""

    def get_current_page_number(self):
        try:
            return (WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(self.CURRENT_PAGE)
            ).text or "").strip()
        except Exception:
            return ""

    def click_next_page(self):
        try:
            super().click_next_page()
            self._wait_settled(timeout=10)
            return True
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════════
    #  行操作
    # ══════════════════════════════════════════════════════════════════════

    def click_row_action(self, row_index, action_text):
        """点击指定行的操作按钮（编辑/删除）"""
        self._wait_settled(timeout=10)
        locators = [
            (
                By.XPATH,
                f'(//div[contains(@class,"el-table__body-wrapper")]//tbody/tr)[{int(row_index)}]'
                f'//td[last()]//button[.//*[normalize-space(.)="{action_text}"]]',
            ),
            (
                By.XPATH,
                f'(//div[contains(@class,"el-table__body-wrapper")]//tbody/tr)[{int(row_index)}]'
                f'//td[last()]//*[normalize-space(.)="{action_text}"]',
            ),
        ]
        for loc in locators:
            try:
                btn = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(loc))
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_vue_stable()
                    logger.info("已点击第%s行%s按钮", row_index, action_text)
                    return
            except Exception:
                continue
        raise TimeoutException(f"未找到第{row_index}行{action_text}按钮")

    def click_first_row_edit(self):
        self.click_row_action(1, "编辑")

    def click_first_row_delete(self):
        self.click_row_action(1, "删除")

    # ══════════════════════════════════════════════════════════════════════
    #  Toast
    # ══════════════════════════════════════════════════════════════════════

    def wait_for_toast_text(self, timeout=6):
        import time as _time
        deadline = _time.time() + timeout
        last = ""
        while _time.time() < deadline:
            for loc in [self.TOAST_ENHANCED, self.TOAST_TEXT, self.TOAST_FALLBACK]:
                try:
                    els = self.driver.find_elements(*loc)
                    for el in els:
                        try:
                            if el.is_displayed():
                                t = (el.text or el.get_attribute("textContent") or "").strip()
                                if t:
                                    return t
                        except Exception:
                            continue
                except Exception:
                    continue
            if last:
                return last
            _time.sleep(0.3)
        return last

    # ══════════════════════════════════════════════════════════════════════
    #  步骤配置面板 (inline .step-editor, CDP click required)
    # ══════════════════════════════════════════════════════════════════════

    def _cdp_click_at(self, x, y):
        """CDP native click — 步骤配置按钮只响应此方式。

        JS click / Selenium click / ActionChains 全部无效。
        """
        self.driver.execute_cdp_cmd('Input.dispatchMouseEvent', {
            'type': 'mousePressed', 'x': x, 'y': y,
            'button': 'left', 'clickCount': 1
        })
        _time.sleep(0.08)
        self.driver.execute_cdp_cmd('Input.dispatchMouseEvent', {
            'type': 'mouseReleased', 'x': x, 'y': y,
            'button': 'left', 'clickCount': 1
        })

    def _get_step_btn_rect(self, row_index):
        """获取指定行 '步骤配置' 按钮的中心坐标 (1-indexed)。无按钮返回 None。"""
        return self.driver.execute_script("""
            var rows = document.querySelectorAll('.el-table__body-wrapper tbody tr');
            if (arguments[0] > rows.length) return null;
            var cells = rows[arguments[0]-1].querySelectorAll('td .cell');
            var lastCell = cells[cells.length-1];
            var btns = lastCell.querySelectorAll('button');
            for (var i=0; i<btns.length; i++) {
                if (btns[i].textContent.indexOf('步骤配置') !== -1) {
                    var r = btns[i].getBoundingClientRect();
                    return {x: r.left + r.width/2, y: r.top + r.height/2};
                }
            }
            return null;
        """, row_index)

    def click_step_config(self, row_index=1):
        """CDP点击第 row_index 行的'步骤配置'按钮，等待面板出现。

        Returns:
            bool: 是否成功点击
        """
        rect = self._get_step_btn_rect(row_index)
        if not rect:
            logger.warning("步骤配置按钮未找到: row=%s", row_index)
            return False
        self._cdp_click_at(rect['x'], rect['y'])
        _time.sleep(3)
        return True

    def get_step_editor_data(self):
        """读取步骤配置面板 (.step-editor) 的步骤数据。

        Returns:
            dict: {found: bool, steps: [{审批人: [str], 审批模式: str, 步骤名称: str}]}
                   found=False 时面板不存在或不可见。
            审批人为 approver-tag 列表，不是 input/select。
        """
        return self.driver.execute_script("""
            var editor = document.querySelector('.step-editor');
            if (!editor || editor.offsetParent === null) return {found: false};

            var result = {found: true, steps: []};
            var cards = editor.querySelectorAll('.step-card');
            cards.forEach(function(card) {
                var step = {};
                card.querySelectorAll('.el-form-item').forEach(function(fi) {
                    var label = fi.querySelector('.el-form-item__label');
                    var name = label ? label.textContent.trim() : '';
                    if (!name) return;

                    // 审批人特殊处理: 读取 .approver-tag__content 列表
                    if (name === '审批人') {
                        var tags = fi.querySelectorAll('.approver-tag .el-tag__content');
                        var approvers = [];
                        tags.forEach(function(t) {
                            var txt = t.textContent.trim();
                            if (txt) approvers.push(txt);
                        });
                        step[name] = approvers;
                        return;
                    }

                    var input = fi.querySelector('input');
                    var textarea = fi.querySelector('textarea');
                    var select = fi.querySelector('.el-select');

                    var v = '';
                    if (input) v = input.value;
                    else if (textarea) v = textarea.value;
                    else if (select) {
                        var s = select.querySelector('.el-select__selected-item, input');
                        v = s ? (s.value || s.textContent || s.placeholder || '').trim() : '';
                    }
                    step[name] = v || '';
                });
                result.steps.push(step);
            });
            return result;
        """)

    def is_step_editor_visible(self):
        """步骤配置面板是否可见"""
        return self.driver.execute_script("""
            var editor = document.querySelector('.step-editor');
            return !!(editor && editor.offsetParent !== null);
        """)

    def get_step_cards_count(self):
        """获取步骤卡片数量"""
        return self.driver.execute_script("""
            var editor = document.querySelector('.step-editor');
            if (!editor || editor.offsetParent === null) return 0;
            return editor.querySelectorAll('.step-card').length;
        """)

    def has_add_step_button(self):
        """是否显示'添加步骤'按钮"""
        return self.driver.execute_script("""
            var bar = document.querySelector('.add-step-bar');
            return !!(bar && bar.offsetParent !== null);
        """)

    def close_step_editor(self):
        """尝试关闭步骤配置面板（点击返回/取消按钮或关闭图标）"""
        return self.driver.execute_script("""
            var editor = document.querySelector('.step-editor');
            if (!editor || editor.offsetParent === null) return 'not_open';

            // 尝试找关闭按钮
            var btns = editor.querySelectorAll('button');
            for (var i=0; i<btns.length; i++) {
                var txt = btns[i].textContent.trim();
                if (txt === '返回' || txt === '取消' || txt === '关闭') {
                    btns[i].click();
                    return 'clicked_' + txt;
                }
            }
            // 尝试找 X 图标
            var closeIcon = editor.querySelector('[class*="close"], .el-icon-close');
            if (closeIcon) { closeIcon.click(); return 'clicked_close_icon'; }
            return 'no_close_found';
        """)
