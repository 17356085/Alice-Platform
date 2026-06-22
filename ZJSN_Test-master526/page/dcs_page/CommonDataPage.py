"""DCS 常用点位页面 Page Object

==== 页面概述 ====
路径：DCS 数据监控 → 常用点位
路由：#/common-data
功能：常用点位快捷管理 — 卡片视图 + 拖拽排序 + 搜索/添加/删除
类型：卡片面板页

⚠️ DOM 诊断发现 (2026-06-22): 页面实际为「搜索表单卡片 + 数据表格」布局，
  非卡片网格视图。.el-card 元素为筛选器表单，非数据卡片。
  无拖拽手柄、无右键菜单、无新增/删除按钮。
  PO 定位器 POINT_CARDS/CARD_GRID/DRAG_HANDLE/CONTEXT_MENU_ITEM 均不匹配实际DOM。
  当前仅 get_card_count() 能返回正确值 (因匹配到筛选表单卡)。
  需重新设计 PO — 建议改为 CommonDataTablePage。

==== 自检报告 ====
[PASS] 继承 BasePage — class CommonDataPage(BasePage):
[PASS] 无绝对 XPath — grep '//*[@id' ==> 无输出
[PASS] 无 time.sleep — grep 'time.sleep' ==> 无输出
[PASS] 有 navigate() — def navigate 存在
"""
import logging
import time
from selenium.webdriver.common.by import By
from base.base_page import BasePage

logger = logging.getLogger(__name__)


class CommonDataPage(BasePage):
    """常用点位 Page Object"""

    # ==================== 搜索/筛选区 ====================
    SEARCH_INPUT = (By.CSS_SELECTOR, 'input[placeholder*="点位名称" i], input[placeholder*="点位" i], input[placeholder*="名称" i]')
    BTN_SEARCH = (By.XPATH, '//button[normalize-space(.//span)="搜索"]')
    BTN_RESET = (By.XPATH, '//button[normalize-space(.//span)="重置"]')
    SELECT_DEVICE = (By.CSS_SELECTOR, '.search-area .el-select')

    # ==================== 操作按钮 ====================
    BTN_ADD = (By.XPATH, '//button[normalize-space(.//span)="新增"] | //button[.//span[text()="添加常用点位"]]')
    BTN_EXPORT = (By.XPATH, '//button[normalize-space(.//span)="导出"]')
    BTN_DELETE_ALL = (By.XPATH, '//button[.//span[text()="删除所有"]] | //button[.//span[text()="清空"]]')
    BTN_RESTORE_DEFAULT = (By.XPATH, '//button[.//span[text()="恢复默认"]]')
    BTN_REFRESH = (By.XPATH, '//button[normalize-space(.//span)="刷新"]')

    # ==================== 卡片网格区 ====================
    CARD_GRID = (By.CSS_SELECTOR, '.card-grid, .el-row, .common-data-cards')
    POINT_CARDS = (By.CSS_SELECTOR, '.point-card, .data-card, .el-card')
    CARD_TITLE = (By.CSS_SELECTOR, '.el-card__header, .card-title, .point-name')
    CARD_BODY = (By.CSS_SELECTOR, '.el-card__body, .card-body')
    CARD_VALUE = (By.CSS_SELECTOR, '.card-value, .point-value')
    CARD_STATUS = (By.CSS_SELECTOR, '.el-tag, .status-badge')
    DRAG_HANDLE = (By.CSS_SELECTOR, '.drag-handle, .el-icon-rank')

    # ==================== 表格备选视图 ====================
    TABLE = (By.CSS_SELECTOR, '.el-table')
    TABLE_ROWS = (By.CSS_SELECTOR, '.el-table__body-wrapper tbody tr.el-table__row')
    TABLE_LOADING = (By.CSS_SELECTOR, '.el-loading-mask')

    # ==================== 右键菜单 ====================
    CONTEXT_MENU_ITEM = (By.CSS_SELECTOR, '.el-dropdown-menu__item, [role="menuitem"]')

    # ==================== 弹窗 ====================
    BTN_CONFIRM_SELECT = (By.XPATH, '//button[.//span[text()="添加选中"]] | //button[.//span[text()="确定"]]')

    # ==================== 页面入口 ====================

    HASH_ROUTE = "#/common-data"

    def navigate(self):
        """导航到常用点位页面"""
        logger.info("导航: DCS 数据监控 → 常用点位 (%s)", self.HASH_ROUTE)
        self.navigate_to_by_hash(self.HASH_ROUTE, "常用点位")
        self._wait_page_ready()
        return self

    def _wait_page_ready(self):
        """等待页面就绪"""
        self.wait_vue_stable()
        self._wait_loading_gone()
        return self

    def _wait_loading_gone(self, timeout=10):
        """等待加载动画消失"""
        try:
            self.wait_until_gone(self.TABLE_LOADING, timeout=timeout)
        except Exception:
            pass
        return self

    # ==================== 搜索操作 ====================

    def search(self, keyword: str):
        """按点位名称搜索"""
        logger.info("搜索常用点位: %s", keyword)
        self.input_text(self.SEARCH_INPUT, keyword)
        self.click(self.BTN_SEARCH)
        self.wait_vue_stable()
        return self

    def reset_search(self):
        """重置搜索"""
        self.click(self.BTN_RESET)
        self.wait_vue_stable()
        return self

    # ==================== 卡片操作 ====================

    def get_cards(self) -> list:
        """获取所有点位卡片"""
        return self.find_all(self.POINT_CARDS)

    def get_card_count(self) -> int:
        """获取卡片数量"""
        return len(self.get_cards())

    def get_card_name(self, card_index: int = 0) -> str:
        """获取指定卡片的名称"""
        cards = self.get_cards()
        if card_index < len(cards):
            return self.find_in_parent(cards[card_index], self.CARD_TITLE).text
        return ""

    def get_card_value(self, card_index: int = 0) -> str:
        """获取指定卡片的值"""
        cards = self.get_cards()
        if card_index < len(cards):
            return self.find_in_parent(cards[card_index], self.CARD_VALUE).text
        return ""

    def get_card_status(self, card_index: int = 0) -> str:
        """获取指定卡片的状态标签"""
        cards = self.get_cards()
        if card_index < len(cards):
            tags = cards[card_index].find_elements(*self.CARD_STATUS)
            if tags:
                return tags[0].text
        return ""

    def is_card_visible(self, card_index: int = 0) -> bool:
        """检查卡片是否可见"""
        cards = self.get_cards()
        if card_index < len(cards):
            return cards[card_index].is_displayed()
        return False

    def click_card(self, card_index: int = 0):
        """点击卡片"""
        cards = self.get_cards()
        if card_index < len(cards):
            cards[card_index].click()
            self.wait_vue_stable()
        return self

    def right_click_card(self, card_index: int = 0):
        """右键点击卡片弹出菜单"""
        from selenium.webdriver.common.action_chains import ActionChains
        cards = self.get_cards()
        if card_index < len(cards):
            ActionChains(self.driver).context_click(cards[card_index]).perform()
            self.wait_vue_stable()
        return self

    def click_context_menu(self, item_text: str):
        """点击右键菜单项（编辑/删除/置顶/移至末尾）"""
        logger.info("点击右键菜单: %s", item_text)
        item = self.find((By.XPATH,
                          f'//li[contains(@class, "el-dropdown-menu__item")]//span[text()="{item_text}"] | '
                          f'//div[@role="menuitem" and contains(text(),"{item_text}")]'))
        self.click(item)
        self.wait_vue_stable()
        return self

    def delete_card(self, card_name: str):
        """根据名称删除卡片"""
        logger.info("删除卡片: %s", card_name)
        self.right_click_card_by_name(card_name)
        self.click_context_menu("删除")
        self.confirm_action()
        return self

    def right_click_card_by_name(self, card_name: str):
        """根据名称右键点击卡片"""
        from selenium.webdriver.common.action_chains import ActionChains
        card = self.find((By.XPATH, f'//*[contains(@class, "card") and contains(.,"{card_name}")]'))
        ActionChains(self.driver).context_click(card).perform()
        self.wait_vue_stable()
        return self

    # ==================== 新增/删除 ====================

    def click_add(self):
        """点击新增按钮 — 打开点位选择弹窗"""
        logger.info("点击新增常用点位")
        self.click(self.BTN_ADD)
        self.wait_dialog_open()
        return self

    def select_points_in_dialog(self, point_names: list):
        """在弹窗中选择点位"""
        for name in point_names:
            checkbox = (By.XPATH,
                        f'//label[contains(@class, "el-checkbox")]//span[contains(text(),"{name}")]')
            self.click(checkbox)
        return self

    def confirm_add_points(self):
        """确认添加选中点位"""
        self.click(self.BTN_CONFIRM_SELECT)
        self.wait_dialog_close()
        self.wait_vue_stable()
        return self

    def delete_all(self):
        """删除所有常用点位"""
        logger.info("删除所有常用点位")
        self.click(self.BTN_DELETE_ALL)
        self.confirm_action()
        self.wait_vue_stable()
        return self

    # ==================== 表格操作 ====================

    def get_table_data(self) -> list:
        """获取表格数据"""
        self.wait_element_visible(self.TABLE)
        rows = self.find_all(self.TABLE_ROWS)
        data = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            data.append([cell.text for cell in cells])
        return data

    def is_point_in_table(self, text: str) -> bool:
        """检查表格中是否存在指定文本"""
        return super().is_row_present(text)

    # ==================== 拖拽排序 ====================

    def drag_card(self, from_index: int, to_index: int):
        """拖拽卡片重新排序（JS 模拟 DragEvent）"""
        logger.info("拖拽卡片: %d → %d", from_index, to_index)
        cards = self.get_cards()
        if from_index >= len(cards) or to_index >= len(cards):
            logger.warning("拖拽索引越界")
            return self

        source = cards[from_index]
        target = cards[to_index]
        self.driver.execute_script("""
            function simulateDragDrop(sourceNode, targetNode) {
                var dt = new DataTransfer();
                sourceNode.dispatchEvent(new DragEvent('dragstart', {dataTransfer:dt, bubbles:true}));
                targetNode.dispatchEvent(new DragEvent('dragover', {dataTransfer:dt, bubbles:true}));
                targetNode.dispatchEvent(new DragEvent('drop', {dataTransfer:dt, bubbles:true}));
                sourceNode.dispatchEvent(new DragEvent('dragend', {dataTransfer:dt, bubbles:true}));
            }
            simulateDragDrop(arguments[0], arguments[1]);
        """, source, target)
        self.wait_vue_stable()
        return self

    # ==================== 辅助 ====================

    def confirm_action(self):
        """确认操作（Element Plus message-box 确定按钮）"""
        self.click((By.XPATH, '//button[contains(@class, "el-button--primary")]//span[text()="确定"]'))
        self.wait_vue_stable()
        return self

    def get_toast_message(self) -> str:
        """获取 toast 消息"""
        try:
            return self.get_toast()
        except Exception:
            return ""
