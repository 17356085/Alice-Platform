"""环保物品管理页面 Page Object — CRUD + 批量选择

==== 页面概述 ====
路径：库管管理 → 环保危废管理 → 物品管理
功能：查看、搜索、新增、删除、批量选择危废品
类型：列表页（CRUD），无审批流

==== 定位策略 ====
- CSS_SELECTOR 优先（语义属性 / Element Plus 标准类）
- 相对 XPath 仅用于文本内容匹配
- 禁止：绝对 XPath（/html/body/div[n]/...）

==== 风险点 ====
1. 新增后列表刷新需等待 Vue 稳定 + 加载动画消失
2. 删除二次确认弹窗为 Element Plus message-box，等待其出现再点击确认
3. 搜索框 placeholder 可能因语言/版本变化，测试前确认
"""
import logging

from selenium.webdriver.common.by import By

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class HazardItemPage(BasePage):
    """环保物品管理 Page Object"""

    # ==================== 通用定位器（子类定义） ====================
    # 搜索/筛选区
    FILTER_ITEM_NAME = (By.CSS_SELECTOR, 'input[placeholder="请输入危废品名称"]')
    BTN_QUERY = (By.XPATH, '//button[.//span[text()="查询"]]')
    BTN_RESET = (By.XPATH, '//button[.//span[text()="重置"]]')
    BTN_ADD = (By.XPATH, '//button[.//span[text()="新增"]]')

    # 表格区
    TABLE = (By.CSS_SELECTOR, '.el-table')
    TABLE_ROWS = (By.CSS_SELECTOR, '.el-table__row')
    COL_CHECKBOX = (By.CSS_SELECTOR, '.el-checkbox__input')

    # 分页区
    TOTAL_COUNT = (By.CSS_SELECTOR, '.el-pagination__total')

    # 操作列按钮（备用，实际使用动态 XPath）
    BTN_DELETE = (By.XPATH, '//button[.//span[text()="删除"]]')

    # ==================== 页面入口 ====================

    def navigate(self):
        """导航到本页面"""
        self.navigate_to("库管管理", "环保危废管理", "物品管理")
        self._wait_page_ready()
        return self

    def _wait_page_ready(self):
        """等待页面完全就绪：Vue 稳定 + 加载动画消失"""
        self.wait_vue_stable()
        self._wait_loading_gone()
        return self

    # ==================== 搜索操作 ====================

    def search_by_item_name(self, name):
        """按危废品名称搜索"""
        self.logger.info("搜索危废品名称：%s", name)
        self.input_text(self.FILTER_ITEM_NAME, name)
        self.click(self.BTN_QUERY)
        self.wait_vue_stable()
        self._wait_loading_gone()
        return self

    def reset_search(self):
        """重置搜索条件"""
        self.logger.info("重置搜索条件")
        self.click(self.BTN_RESET)
        self.wait_vue_stable()
        return self

    def click_search(self):
        """点击查询按钮（同 search_by_item_name，无输入）"""
        self.click(self.BTN_QUERY)
        self.wait_vue_stable()
        self._wait_loading_gone()
        return self

    # ==================== 表格数据查询 ====================

    def get_total_count(self) -> int:
        """获取分页总条数"""
        text = self.get_text(self.TOTAL_COUNT)
        # 例如："共 42 条"
        import re
        match = re.search(r'(\d+)', text)
        count = int(match.group(1)) if match else 0
        self.logger.info("分页总条数：%d", count)
        return count

    def is_row_present(self, name_or_text) -> bool:
        """判断表格中是否存在包含指定文本的行"""
        xpath = f'//tr[.//td[contains(.,"{name_or_text}")]]'
        try:
            self.driver.find_element(By.XPATH, xpath)
            return True
        except Exception:
            return False

    # ==================== 行操作（编辑、删除等） ====================

    def click_row_button(self, row_text, button_text):
        """点击某行中的操作按钮（如「编辑」「删除」）"""
        self.logger.info("点击行「%s」中的按钮「%s」", row_text, button_text)
        # 定位包含 row_text 的行中的按钮
        xpath = (
            f'//tr[.//td[contains(.,"{row_text}")]]'
            f'//button[.//span[text()="{button_text}"]]'
        )
        btn = (By.XPATH, xpath)
        self.click(btn)
        self.wait_vue_stable()
        return self

    def delete_item_by_name(self, name):
        """按名称搜索并删除指定物品（包含二次确认）"""
        self.logger.info("删除危废品：%s", name)
        self.search_by_item_name(name)
        self.click_row_button(name, "删除")
        self.confirm_message_box()
        self.wait_vue_stable()
        self._wait_loading_gone()
        return self

    # ==================== 新增弹窗操作 ====================

    def click_add(self):
        """点击新增按钮，等待弹窗打开"""
        self.logger.info("点击新增按钮")
        self.click(self.BTN_ADD)
        self.wait_dialog_open()
        return self

    def _fill_dialog_by_placeholder(self, placeholder_contains, value):
        """弹窗内按 placeholder 查找输入框并填写（JS 方式，避免 XPath 编码问题）"""
        self.logger.info(
            "弹窗内填写 placeholder 包含「%s」的输入框，值为：%s",
            placeholder_contains, value
        )
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
            self.logger.warning("未找到 placeholder 包含「%s」的弹窗输入框", placeholder_contains)
        self.wait_vue_stable()
        return self

    def fill_item_name(self, name):
        """在新增弹窗中填写危废品名称"""
        self.logger.info("填写危废品名称：%s", name)
        self._fill_dialog_by_placeholder("危废品名称", name)
        return self

    # ==================== 弹窗通用快捷操作 ====================

    def confirm_message_box(self):
        """确认 Element Plus message-box 弹窗（删除等二次确认）"""
        self.logger.info("确认消息弹窗")
        # 等待弹窗出现
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[role="alertdialog"]'))
        )
        # 点击确认按钮（primary 类）
        confirm_btn = (By.XPATH, '//div[@role="alertdialog"]//button[contains(@class,"el-button--primary")]')
        self.click(confirm_btn)
        self.wait_vue_stable()
        return self

    # ==================== 其他（沿用通用方法） ====================
    # is_dialog_visible, click_dialog_save, click_dialog_cancel 继承自 BasePage


# ====== 代码自检报告 ======
# [PASS] 继承 BasePage
# [PASS] 无绝对 XPath（grep -n '//\*\[@id="app"\]' 应为空）
# [PASS] 无 time.sleep（grep -n "time.sleep" 应为空，仅配置文件除外）
# [PASS] 无 print()（grep -n "print(" 应为空）
# [PASS] 有 navigate() 方法
# ============================