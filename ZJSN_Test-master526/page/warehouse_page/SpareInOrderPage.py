"""备品入库页面 Page Object

8列表格，与环保入库结构相似。
审批链：备件入库审批链 (admin 会签)
"""
import logging
from selenium.webdriver.common.by import By
from base.base_page import BasePage

logger = logging.getLogger(__name__)


class SpareInOrderPage(BasePage):

    FILTER_HANDLER = (By.XPATH, '//input[@placeholder="请输入经办人"]')
    FILTER_DATE = (By.XPATH, '//input[@placeholder="选择日期"]')
    BTN_QUERY = (By.XPATH, '//button[contains(.,"查询")]')
    BTN_RESET = (By.XPATH, '//button[contains(.,"重置")]')
    BTN_ADD = (By.XPATH, '//button[contains(.,"新增入库")]')
    BTN_VIEW = (By.XPATH, '//button[contains(.,"查看")]')

    def navigate(self):
        self.navigate_to("库管管理", "备品备件管理", "入库")
        self._wait_page_ready()

    def _wait_page_ready(self):
        self.wait_vue_stable()
        self._wait_loading_gone()

    def click_add(self):
        self.click(self.BTN_ADD)
        self.wait_dialog_open()

    def click_view_first(self):
        self.click(self.BTN_VIEW)
        self.wait_dialog_open()

    def search_by_handler(self, name):
        self.input_text(self.FILTER_HANDLER, name)
        self.click(self.BTN_QUERY)
        self.wait_vue_stable()

    def reset_search(self):
        self.click(self.BTN_RESET)
        self.wait_vue_stable()

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
            // 兜底：未匹配则填第一个可见输入框
            for (var i = 0; i < dlgs.length; i++) {
                if (dlgs[i].offsetParent === null) continue;
                var inputs = dlgs[i].querySelectorAll('input:not([type=\"hidden\"])');
                if (inputs.length > 0) {
                    inputs[0].focus();
                    inputs[0].value = '';
                    inputs[0].value = value;
                    inputs[0].dispatchEvent(new Event('input', {bubbles: true}));
                    inputs[0].dispatchEvent(new Event('change', {bubbles: true}));
                    return '(fallback) ' + (inputs[0].getAttribute('placeholder') || 'first-input');
                }
            }
            return '';
        """
        result = self.driver.execute_script(script, placeholder_contains, value)
        if not result:
            logger.warning("弹窗输入框填写失败: placeholder='%s'", placeholder_contains)
        elif result.startswith('(fallback)'):
            logger.warning("弹窗输入框兜底填写(可能填入错误字段): placeholder='%s', target='%s'",
                           placeholder_contains, result[len('(fallback) '):])
        self.wait_vue_stable()

    def fill_in_order_handler(self, name):
        """在新增弹窗中填写经办人"""
        self._fill_dialog_by_placeholder("经办人", name)

    def click_search(self):
        """点击查询按钮"""
        self.click(self.BTN_QUERY)
        self.wait_vue_stable()

    def delete_by_handler(self, name):
        """搜索并删除指定入库记录"""
        self.search_by_handler(name)
        self.click_row_button(name, "删除")
        self.confirm_message_box()
