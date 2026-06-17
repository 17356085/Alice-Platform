"""备品物品管理页面 Page Object

CRUD + 导入导出 + 批量选择(checkbox)，无审批流。
"""
import logging
from selenium.webdriver.common.by import By
from base.base_page import BasePage

logger = logging.getLogger(__name__)


class SpareItemPage(BasePage):

    FILTER_ITEM_NAME = (By.XPATH, '//input[@placeholder="请输入物品名称"]')
    FILTER_FACTORY = (By.XPATH, '//input[@placeholder="请输入厂家名称"]')
    BTN_QUERY = (By.XPATH, '//button[contains(.,"查询")]')
    BTN_RESET = (By.XPATH, '//button[contains(.,"重置")]')
    BTN_ADD = (By.XPATH, '//button[contains(.,"新增")]')
    BTN_VIEW = (By.XPATH, '//button[contains(.,"查看")]')

    def navigate(self):
        self.navigate_to("库管管理", "备品备件管理", "物品管理")
        self._wait_page_ready()

    def _wait_page_ready(self):
        self.wait_vue_stable()
        self._wait_loading_gone()

    def search_by_item_name(self, name):
        self.input_text(self.FILTER_ITEM_NAME, name)
        self.click(self.BTN_QUERY)
        self.wait_vue_stable()

    def reset_search(self):
        self.click(self.BTN_RESET)
        self.wait_vue_stable()

    def click_add(self):
        self.click(self.BTN_ADD)
        self.wait_dialog_open()

    def click_view_first(self):
        self.click(self.BTN_VIEW)
        self.wait_dialog_open()

    # ── 新增弹窗表单操作 ────────────────────────────────────
    def _fill_dialog_by_placeholder(self, placeholder_contains, value):
        """弹窗内按 placeholder 查找输入框并填写（JS方式，避免xpath编码问题）"""
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

    def fill_item_name(self, name):
        """在新增弹窗中填写物品名称"""
        self._fill_dialog_by_placeholder("物品名称", name)

    def fill_item_code(self, code):
        """在新增弹窗中填写物品编码"""
        self._fill_dialog_by_placeholder("物品编码", code)

    def click_search(self):
        """点击查询按钮"""
        self.click(self.BTN_QUERY)
        self.wait_vue_stable()

    def delete_item_by_name(self, name):
        """搜索并删除指定物品"""
        self.search_by_item_name(name)
        self.click_row_button(name, "删除")
        self.confirm_message_box()
