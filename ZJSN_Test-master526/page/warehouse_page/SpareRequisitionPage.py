"""备品领用申请页面 Page Object

4 个行内按钮：查看(blue) / 编辑(blue) / 提交(green) / 删除(red)
审批链：备件领用申请审批链 (admin+chenqian → tjw)
"""
import logging
from selenium.webdriver.common.by import By
from base.base_page import BasePage

logger = logging.getLogger(__name__)


class SpareRequisitionPage(BasePage):

    # ══════════════════════════════════════════════════════════
    #  搜索区（自定义 wh-filter-toolbar，placeholder 定位）
    # ══════════════════════════════════════════════════════════
    FILTER_APPLICANT = (By.XPATH, '//input[@placeholder="请输入申请人"]')
    FILTER_DATE = (By.XPATH, '//input[@placeholder="选择日期"]')
    # 第一个 el-select（流程状态）
    FILTER_STATUS = (
        By.XPATH,
        '(//div[contains(@class,"wh-filter-toolbar")]//div[contains(@class,"el-select__wrapper")])[1]',
    )
    BTN_QUERY = (By.XPATH, '//button[contains(.,"查询")]')
    BTN_RESET = (By.XPATH, '//button[contains(.,"重置")]')

    # ══════════════════════════════════════════════════════════
    #  工具栏
    # ══════════════════════════════════════════════════════════
    BTN_ADD = (By.XPATH, '//button[contains(.,"新增")]')

    # ══════════════════════════════════════════════════════════
    #  行内操作按钮（按状态动态显隐）
    # ══════════════════════════════════════════════════════════
    BTN_VIEW = (By.XPATH, '//button[contains(.,"查看")]')
    BTN_EDIT = (By.XPATH, '//button[contains(.,"编辑")]')
    BTN_SUBMIT = (By.XPATH, '//button[contains(.,"提交")]')
    BTN_DELETE = (By.XPATH, '//button[contains(.,"删除")]')

    # ══════════════════════════════════════════════════════════
    #  弹窗 — 新增/编辑（继承 BasePage DIALOG/DIALOG_SAVE）
    # ══════════════════════════════════════════════════════════

    # ── 导航 ────────────────────────────────────────────────
    def navigate(self):
        """导航到备品领用申请页面"""
        self.navigate_to("库管管理", "备品备件管理", "领用申请")
        self._wait_page_ready()

    def _wait_page_ready(self):
        self.wait_vue_stable()
        self._wait_loading_gone()

    # ── 搜索操作 ────────────────────────────────────────────
    def search_by_applicant(self, name):
        """按申请人搜索"""
        self.input_text(self.FILTER_APPLICANT, name)
        self.click(self.BTN_QUERY)
        self.wait_vue_stable()

    def reset_search(self):
        """重置搜索条件"""
        self.click(self.BTN_RESET)
        self.wait_vue_stable()

    # ── 新增 ────────────────────────────────────────────────
    def click_add(self):
        """点击新增按钮，等待弹窗出现"""
        self.click(self.BTN_ADD)
        self.wait_dialog_open()

    # ── 行内按钮操作（操作第一行） ──────────────────────────
    def click_view_first(self):
        self.click(self.BTN_VIEW)
        self.wait_dialog_open()

    def click_edit_first(self):
        self.click(self.BTN_EDIT)

    def click_submit_first(self):
        self.click(self.BTN_SUBMIT)
        self.wait_for_toast_text()

    def click_delete_first(self):
        self.click(self.BTN_DELETE)
        self.confirm_message_box()
        self.wait_for_toast_text()

    # ── 断言辅助（test 层调用） ─────────────────────────────
    def has_edit_button(self):
        """检查当前页面是否有编辑按钮"""
        return len(self.driver.find_elements(*self.BTN_EDIT)) > 0

    def has_submit_button(self):
        return len(self.driver.find_elements(*self.BTN_SUBMIT)) > 0

    def has_delete_button(self):
        return len(self.driver.find_elements(*self.BTN_DELETE)) > 0

    def get_first_row_status(self):
        """获取第一行流程状态文本"""
        el = self.driver.find_element(*self.TABLE_ROWS)
        tags = el.find_elements(By.CSS_SELECTOR, '.el-tag')
        return tags[0].text if tags else ""

    # ── 新增弹窗表单操作 ────────────────────────────────────
    def _fill_dialog_by_placeholder(self, placeholder_contains, value):
        """弹窗内按 placeholder 查找输入框并填写（JS方式）"""
        script = """
            var placeholder = arguments[0];
            var value = arguments[1];
            var dlgs = document.querySelectorAll('.el-dialog');
            for (var i = 0; i < dlgs.length; i++) {
                if (dlgs[i].offsetParent === null) continue;
                var inputs = dlgs[i].querySelectorAll('input:not([type="hidden"])');
                for (var j = 0; j < inputs.length; j++) {
                    var ph = inputs[j].getAttribute('placeholder') || '';
                    if (ph.indexOf(placeholder) >= 0) {
                        inputs[j].focus();
                        inputs[j].value = '';
                        inputs[j].value = value;
                        inputs[j].dispatchEvent(new Event('input', {bubbles: true}));
                        inputs[j].dispatchEvent(new Event('change', {bubbles: true}));
                        return ph;
                    }
                }
            }
            return '';
        """
        result = self.driver.execute_script(script, placeholder_contains, value)
        if not result:
            logger.warning("未找到 placeholder 包含 '%s' 的弹窗输入框", placeholder_contains)
        self.wait_vue_stable()

    def fill_requisition_applicant(self, name):
        """在新增弹窗中填写申请人"""
        self._fill_dialog_by_placeholder("申请人", name)

    def click_search(self):
        """点击查询按钮"""
        self.click(self.BTN_QUERY)
        self.wait_vue_stable()

    def delete_by_name(self, name):
        """搜索并删除指定领用申请"""
        self.search_by_applicant(name)
        try:
            self.click_row_button(name, "删除")
            self.confirm_message_box()
        except Exception:
            logger.warning("无法删除领用申请: %s（可能已审批不允许删除）", name)
