"""
气体分析对比 Page Object

路由: #/lab/gas/compare
模块: lab
类型: 搜索表单 + 自定义对比表格（双位置选择 + 日期范围）
"""
import logging
import time
from selenium.webdriver.common.by import By

from base.base_page import BasePage

logger = logging.getLogger(__name__)


class GasComparePage(BasePage):
    """
    气体分析对比页面

    Element Plus 坑位处理:
    - 输入框 `el-date-picker` 使用 `fill_input` 方法（基类已封装）进行日期设置，避免直接 `send_keys` 可能不触发 `v-model` 的问题。
    - 查询/重置按钮采用 JS Click + 等待加载动画，防止 Element Plus 按钮的点击事件冒泡或动画拦截。
    """

    # ══════════════════════════════════════════════════════════════════
    #  Locators (类属性元组)
    #  来源: PAGE_ELEMENT_POSITION.md
    # ══════════════════════════════════════════════════════════════════
    START_DATE_INPUT = (By.CSS_SELECTOR, "input[placeholder*='开始日期']")  # 稳定性: B
    END_DATE_INPUT = (By.CSS_SELECTOR, "input[placeholder*='结束日期']")    # 稳定性: B
    # 基类通用定位器（可通过 self.XXX 直接使用）:
    #   self.DIALOG = (By.CSS_SELECTOR, '.el-dialog')
    #   self.TOAST = (By.CSS_SELECTOR, '.el-message')
    #   self.LOADING = (By.CSS_SELECTOR, '.el-loading-mask')

    # ══════════════════════════════════════════════════════════════════
    #  页面入口
    # ══════════════════════════════════════════════════════════════════
    def navigate(self):
        """导航到气体分析对比页面（唯一入口）"""
        self.logger.info("导航到: 化验室取样 → 气体分析对比")
        self.navigate_to("化验室取样", "气体分析对比")
        self.wait_page_ready(timeout=15)
        self.wait_loading_disappear(timeout=10)   # 等待通用加载动画消失
        self.wait_vue_stable()
        return self

    # ══════════════════════════════════════════════════════════════════
    #  搜索区操作 (链式调用)
    # ══════════════════════════════════════════════════════════════════
    def set_start_date(self, date_str: str):
        """设置开始日期

        Args:
            date_str: 日期字符串，格式如 '2026-01-01'
        """
        self.logger.info("设置开始日期: %s", date_str)
        # 使用基类封装的 fill_input 方法，适用于 el-date-picker
        self.fill_input(self.START_DATE_INPUT, date_str)
        return self

    def set_end_date(self, date_str: str):
        """设置结束日期"""
        self.logger.info("设置结束日期: %s", date_str)
        self.fill_input(self.END_DATE_INPUT, date_str)
        return self

    def click_query(self):
        """点击查询按钮（JS Click 绕过 Element Plus 可能的拦截）"""
        self.logger.info("点击查询按钮")
        # 使用基类方法进行 JS 点击
        self.js_click_button_by_text("查询")
        self.wait_loading_disappear(timeout=10)
        self.wait_vue_stable()
        return self

    def click_reset(self):
        """点击重置按钮"""
        self.logger.info("点击重置按钮")
        self.js_click_button_by_text("重置")
        self.wait_loading_disappear(timeout=10)
        self.wait_vue_stable()
        return self

    # ══════════════════════════════════════════════════════════════════
    #  页面内容检测 (辅助方法，无 assert)
    # ══════════════════════════════════════════════════════════════════
    def is_page_loaded(self) -> bool:
        """
        检测页面是否正常加载

        判断依据:
        - 开始日期输入框可见
        - 表格或空状态提示存在
        """
        self.wait_vue_stable()
        self.wait_loading_disappear(timeout=10)
        has_start_input = self.is_element_visible(self.START_DATE_INPUT)
        has_table_or_empty = self.driver.execute_script("""
            return !!(document.querySelector('table') ||
                      document.querySelector('.el-table__empty-text') ||
                      document.querySelector('[class*="empty"]'));
        """)
        return bool(has_start_input) and bool(has_table_or_empty)

    def get_table_row_count(self) -> int:
        """
        获取当前表格可见行数

        Returns:
            表格行数（整数），如无表格或异常则返回 0
        """
        try:
            # 使用基类方法等待表格出现
            self.wait_for_element_visible(self.TABLE_ROWS)
            rows = self.driver.find_elements(*self.TABLE_ROWS)
            display_count = sum(1 for r in rows if r.is_displayed())
            self.logger.info("当前表格可见行数: %s", display_count)
            return display_count
        except Exception as e:
            self.logger.warning("获取表格行数失败: %s", e)
            return 0

    # ══════════════════════════════════════════════════════════════════
    #  高级交互 (增强功能)
    # ══════════════════════════════════════════════════════════════════
    def click_row_compare(self, row_index: int = 0):
        """
        点击表格中指定行的“对比”按钮

        Args:
            row_index: 行索引（从 0 开始），默认第一行

        注意:
            - 该操作基于“每行都有一个对比按钮”的假设
            - 使用 JS Click 以确保稳定性
        """
        self.logger.info("点击第 %s 行的对比按钮", row_index + 1)
        js_script = f"""
            var table = document.querySelector('table');
            if (!table) return false;
            var rows = table.querySelectorAll('tbody tr');
            if (rows.length > {row_index}) {{
                var btn = rows[{row_index}].querySelector('button');
                if (btn) {{
                    btn.click();
                    return true;
                }}
            }}
            return false;
        """
        success = self.driver.execute_script(js_script)
        if not success:
            raise RuntimeError(f"第 {row_index + 1} 行的对比按钮不可点击或不存在")
        self.wait_loading_disappear(timeout=10)
        self.wait_vue_stable()
        return self

    def handle_dialog_on_compare(self, action: str = "confirm"):
        """
        处理对比操作后可能弹出的对话框

        Args:
            action: "confirm" 或 "cancel"(取消)

        适用场景:
            - 对比后如果结果异常会弹窗提示
            - 或对比前需确认
        """
        self.logger.info("处理弹窗: %s", action)
        self.wait_for_dialog_visible()
        if action == "confirm":
            self.dialog_confirm()
        elif action == "cancel":
            self.dialog_cancel()
        else:
            raise ValueError(f"不支持的弹窗操作: {action}")
        self.wait_loading_disappear(timeout=5)
        return self

    def verify_system_timestamp_received(self) -> bool:
        """
        校验“系统当前时间”已经回显在页面上

        该方法用于应对服务端返回的“系统当前时间戳”需要与页面时间做对比的场景。

        Returns:
            bool: True 表示页面已展示时间戳相关信息（存在包含当前日期的文本）
        """
        self.logger.info("校验系统时间戳回显...")
        import datetime
        today = datetime.date.today().isoformat()
        # 检查页面中是否存在包含今日日期的文本
        page_text = self.get_page_text()
        if today in page_text:
            self.logger.info("时间戳校验通过: 页面已展示今日日期 %s", today)
            return True
        else:
            self.logger.warning("时间戳校验未通过: 页面未找到日期 %s", today)
            return False

    # ══════════════════════════════════════════════════════════════════
    #  数据提取 (提供给测试脚本断言用)
    # ══════════════════════════════════════════════════════════════════
    def get_table_data_as_text(self) -> list:
        """
        提取表格数据为文本列表

        Returns:
            list: 每行文本组成的列表，例如 ['气体名称: N₂ 标准值: 1.23...']
        """
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        data = []
        for row in rows:
            data.append(row.text)
        self.logger.info("提取到 %s 行表格数据", len(data))
        return data